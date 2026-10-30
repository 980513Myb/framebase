import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from app.routers import webhook
from app.services import task_service


class FakeRequest:
    headers = {"content-type": "application/json"}

    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


class FakeEmbyClient:
    def __init__(self, host, key, public_host=None, user_name=None):
        self.host = host

    def get_libraries(self):
        return [{"id": "library-1", "name": "电影", "paths": ["/media/movies"]}]

    def get_item_info(self, item_id):
        return {
            "name": "测试电影",
            "type": "Movie",
            "year": 2026,
            "poster_url": "https://example.test/poster.jpg",
            "overview": "简介",
            "community_rating": 8.4,
            "genres": "剧情",
            "tagline": "标语",
        }

    def get_image_data(self, image_url):
        return b"poster-bytes", "image/jpeg"


class WebhookNotificationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.webhook_config = os.path.join(self.tempdir.name, "webhook.json")
        self.app_config = os.path.join(self.tempdir.name, "settings.json")
        with open(self.app_config, "w", encoding="utf-8") as f:
            json.dump({"servers": [{"name": "Emby", "host": "http://emby", "key": "key"}]}, f)

    def tearDown(self):
        self.tempdir.cleanup()

    def write_webhook_config(self, enabled):
        with open(self.webhook_config, "w", encoding="utf-8") as f:
            json.dump({"enabled": enabled, "engine": "classic", "preset": "preset.json", "mode": "latest"}, f)

    def patches(self):
        return (
            patch.object(webhook, "WEBHOOK_CONFIG_FILE", self.webhook_config),
            patch.object(webhook, "CONFIG_FILE", self.app_config),
            patch.object(webhook, "EmbyClient", FakeEmbyClient),
            patch.object(webhook, "wechat_notify_service", Mock()),
            patch.object(webhook, "webhook_debouncer", Mock()),
        )

    async def test_media_notification_runs_when_cover_automation_is_off(self):
        self.write_webhook_config(False)
        payload = {
            "Event": "item.added",
            "Item": {"Id": "movie-1", "Name": "测试电影", "Type": "Movie", "Path": "/media/movies/test.mkv"},
        }
        contexts = self.patches()
        with contexts[0], contexts[1], contexts[2], contexts[3] as notify, contexts[4] as debouncer:
            notify.notify_media_added.return_value = True
            result = await webhook.emby_webhook_trigger(FakeRequest(payload))

        self.assertEqual(result["action"], "notification_only")
        self.assertFalse(result["cover_automation"])
        notify.notify_media_added.assert_called_once()
        debouncer.schedule.assert_not_called()

    async def test_playback_notification_is_independent_from_cover_automation(self):
        self.write_webhook_config(False)
        payload = {
            "Event": "playback.start",
            "Item": {"Id": "movie-1", "Name": "测试电影", "Type": "Movie"},
            "User": {"Name": "admin"},
            "Session": {
                "Client": "Emby Web",
                "DeviceName": "Browser",
                "RemoteEndPoint": "192.0.2.10",
            },
            "Server": {"Name": "家庭影院"},
        }
        contexts = self.patches()
        with contexts[0], contexts[1], contexts[2], contexts[3] as notify, contexts[4]:
            notify.notify_playback.return_value = True
            result = await webhook.emby_webhook_trigger(FakeRequest(payload))

        self.assertEqual(result["action"], "playback_notification")
        self.assertTrue(result["notified"])
        kwargs = notify.notify_playback.call_args.kwargs
        self.assertEqual(kwargs["user_name"], "admin")
        self.assertEqual(kwargs["client_info"], "Emby Web / Browser")
        self.assertEqual(kwargs["client_name"], "Emby Web")
        self.assertEqual(kwargs["device_name"], "Browser")
        self.assertEqual(kwargs["device_ip"], "192.0.2.10")
        self.assertEqual(kwargs["poster_data"], b"poster-bytes")

    async def test_legacy_media_play_payload_is_normalized(self):
        self.write_webhook_config(False)
        payload = {
            "Event": "media.play",
            "ItemID": "movie-1",
            "ItemName": "Legacy Movie",
            "ItemType": "movies",
            "UserName": "admin",
            "AppName": "Emby Theater",
            "DeviceName": "Living Room",
            "DeviceIP": "198.51.100.20",
            "ServerName": "Home Emby",
        }
        contexts = self.patches()
        with contexts[0], contexts[1], contexts[2], contexts[3] as notify, contexts[4]:
            notify.notify_playback.return_value = True
            result = await webhook.emby_webhook_trigger(FakeRequest(payload))

        self.assertEqual(result["action"], "playback_notification")
        kwargs = notify.notify_playback.call_args.kwargs
        self.assertEqual(kwargs["user_name"], "admin")
        self.assertEqual(kwargs["client_info"], "Emby Theater / Living Room")
        self.assertEqual(kwargs["device_ip"], "198.51.100.20")

    async def test_emby_webhook_test_event_sends_notification(self):
        self.write_webhook_config(False)
        contexts = self.patches()
        with contexts[0], contexts[1], contexts[2], contexts[3] as notify, contexts[4]:
            notify.send_message.return_value = True
            result = await webhook.emby_webhook_trigger(FakeRequest({"Event": "system.notificationtest"}))

        self.assertEqual(result["action"], "webhook_test")
        self.assertTrue(result["notified"])
        notify.send_message.assert_called_once()

    async def test_cover_task_is_scheduled_only_when_enabled(self):
        self.write_webhook_config(True)
        payload = {
            "Event": "item.added",
            "Item": {"Id": "movie-1", "Name": "测试电影", "Type": "Movie", "Path": "/media/movies/test.mkv"},
        }
        contexts = self.patches()
        with contexts[0], contexts[1], contexts[2], contexts[3] as notify, contexts[4] as debouncer:
            notify.notify_media_added.return_value = True
            result = await webhook.emby_webhook_trigger(FakeRequest(payload))

        self.assertEqual(result["status"], "queued")
        self.assertTrue(result["cover_automation"])
        debouncer.schedule.assert_called_once()


class PosterTaskNotificationTests(unittest.TestCase):
    def test_missing_preset_sends_failed_poster_notification(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with patch.object(task_service, "TEMPLATES_DIR", tempdir), patch.object(task_service, "wechat_notify_service", Mock()) as notify:
                result = task_service.execute_task_logic("missing.json", [], task_name="每日封面")

        self.assertEqual(result["status"], "error")
        notify.notify_task_complete.assert_called_once_with("每日封面", status="failed", detail="预设不存在", posters_count=0)


if __name__ == "__main__":
    unittest.main()
