import unittest
from unittest.mock import Mock, patch

from app.services.wechat_service import WechatNotifyService


class WechatMediaTests(unittest.TestCase):
    def make_service(self):
        service = WechatNotifyService.__new__(WechatNotifyService)
        service.config = {"enabled": True, "agent_id": "1000001"}
        service._access_token = "token"
        service._token_expires = 7200
        service._token_acquired_time = 0
        service._get_access_token = Mock(return_value="token")
        service._get_api_base_url = Mock(return_value="https://qyapi.weixin.qq.com")
        return service

    def test_upload_image_media_returns_media_id(self):
        service = self.make_service()
        response = Mock()
        response.json.return_value = {"errcode": 0, "media_id": "poster-media-id"}

        with patch("app.services.wechat_service.requests.post", return_value=response) as post:
            media_id = service._upload_image_media(b"poster", "image/jpeg")

        self.assertEqual(media_id, "poster-media-id")
        self.assertIn("type=image", post.call_args.args[0])
        self.assertEqual(post.call_args.kwargs["files"]["media"][1], b"poster")

    def test_private_poster_uses_mpnews_message(self):
        service = self.make_service()
        service._upload_image_media = Mock(return_value="poster-media-id")
        service._send_request = Mock(return_value=True)

        sent = service.send_news_message(
            title="正在播放",
            description="用户：shiwu\n设备：Apple TV",
            image_data=b"poster",
            image_content_type="image/jpeg",
        )

        self.assertTrue(sent)
        payload = service._send_request.call_args.args[1]
        self.assertEqual(payload["msgtype"], "mpnews")
        article = payload["mpnews"]["articles"][0]
        self.assertEqual(article["thumb_media_id"], "poster-media-id")
        self.assertIn("用户：shiwu", article["content"])
        self.assertIn("Apple TV", article["content"])
        self.assertEqual(article["digest"], "用户：shiwu\n设备：Apple TV")


if __name__ == "__main__":
    unittest.main()
