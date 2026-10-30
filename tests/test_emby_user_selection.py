import unittest

from core.emby_client import EmbyClient


class EmbyUserSelectionTests(unittest.TestCase):
    USERS = [
        {"Id": "admin-id", "Name": "Admin", "Policy": {"IsAdministrator": True}},
        {"Id": "media-id", "Name": "MediaUser", "Policy": {"IsAdministrator": False}},
    ]

    def test_configured_username_resolves_exact_user(self):
        client = EmbyClient("http://emby.local", "key", user_name="MediaUser")
        client._request = lambda _method, endpoint, **_kwargs: self.USERS if endpoint == "emby/Users" else {}

        self.assertEqual(client._get_user_id(), "media-id")

    def test_configured_username_is_case_sensitive(self):
        client = EmbyClient("http://emby.local", "key", user_name="mediauser")
        client._request = lambda _method, endpoint, **_kwargs: self.USERS if endpoint == "emby/Users" else {}

        with self.assertRaisesRegex(ValueError, "未找到 Emby 用户: mediauser"):
            client._get_user_id()

    def test_blank_username_keeps_administrator_fallback(self):
        client = EmbyClient("http://emby.local", "key")
        client._request = lambda _method, endpoint, **_kwargs: self.USERS if endpoint == "emby/Users" else {}

        self.assertEqual(client._get_user_id(), "admin-id")

    def test_empty_user_views_do_not_fall_back_to_global_libraries(self):
        client = EmbyClient("http://emby.local", "key", user_name="MediaUser")

        def fake_request(_method, endpoint, **_kwargs):
            if endpoint == "emby/Library/VirtualFolders":
                return [{"ItemId": "hidden-id", "Name": "管理员媒体库", "Locations": ["/media/admin"]}]
            if endpoint == "emby/Users":
                return self.USERS
            if endpoint == "emby/Users/media-id/Views":
                return {"Items": []}
            raise AssertionError(f"unexpected endpoint: {endpoint}")

        client._request = fake_request

        self.assertEqual(client.get_libraries(), [])

    def test_user_views_return_only_shared_libraries(self):
        client = EmbyClient("http://emby.local", "key", user_name="MediaUser")

        def fake_request(_method, endpoint, **_kwargs):
            if endpoint == "emby/Library/VirtualFolders":
                return [
                    {"ItemId": "shared-id", "Name": "共享媒体库", "Locations": ["/media/shared"]},
                    {"ItemId": "hidden-id", "Name": "管理员媒体库", "Locations": ["/media/admin"]},
                ]
            if endpoint == "emby/Users":
                return self.USERS
            if endpoint == "emby/Users/media-id/Views":
                return {"Items": [{"Id": "shared-id", "Name": "共享媒体库", "CollectionType": "movies"}]}
            raise AssertionError(f"unexpected endpoint: {endpoint}")

        client._request = fake_request

        self.assertEqual(
            client.get_libraries(),
            [{"name": "共享媒体库", "id": "shared-id", "type": "movies", "paths": ["/media/shared"]}],
        )


if __name__ == "__main__":
    unittest.main()
