import unittest
from unittest.mock import patch

from core.emby_client import EmbyClient


class FakeResponse:
    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content


class EmbyCoverUploadTest(unittest.TestCase):
    def make_client(self, state):
        client = EmbyClient("http://emby.local", "test-key")
        client.cover_verify_delays = []
        client._get_user_id = lambda: "user-1"

        def fake_request(method, endpoint, **kwargs):
            tag = state.get("tag")
            return {"ImageTags": {"Primary": tag} if tag else {}}

        client._request = fake_request
        return client

    def make_get(self, state):
        def fake_get(url, **kwargs):
            data = state.get("data")
            if data:
                return FakeResponse(200, data)
            return FakeResponse(404, b"")

        return fake_get

    def test_upload_prefers_base64_and_returns_true_after_primary_tag_changes(self):
        state = {"tag": "old-tag", "data": b"old-cover"}
        client = self.make_client(state)
        calls = []

        def fake_post(url, **kwargs):
            calls.append(kwargs.get("data"))
            state["tag"] = "new-tag"
            state["data"] = b"new-cover"
            return FakeResponse(204)

        with patch("core.emby_client.requests.get", self.make_get(state)), \
                patch("core.emby_client.requests.post", fake_post), \
                patch("core.emby_client.requests.delete") as fake_delete:
            self.assertTrue(client.upload_cover("library-1", b"new-cover"))
            self.assertEqual(calls[0], b"bmV3LWNvdmVy")
            fake_delete.assert_not_called()

    def test_success_response_without_image_change_tries_binary_fallback_without_delete(self):
        state = {"tag": "old-tag", "data": b"old-cover"}
        client = self.make_client(state)
        calls = []

        def fake_post(url, **kwargs):
            calls.append(kwargs.get("data"))
            return FakeResponse(204)

        with patch("core.emby_client.requests.get", self.make_get(state)), \
                patch("core.emby_client.requests.post", fake_post), \
                patch("core.emby_client.requests.delete") as fake_delete, \
                patch("core.emby_client.time.sleep"):
            self.assertFalse(client.upload_cover("library-1", b"new-cover"))
            self.assertEqual(calls, [b"bmV3LWNvdmVy", b"new-cover"])
            fake_delete.assert_not_called()

    def test_rejected_upload_does_not_delete_existing_cover(self):
        state = {"tag": "old-tag", "data": b"old-cover"}
        client = self.make_client(state)

        def fake_post(url, **kwargs):
            return FakeResponse(500)

        with patch("core.emby_client.requests.get", self.make_get(state)), \
                patch("core.emby_client.requests.post", fake_post), \
                patch("core.emby_client.requests.delete") as fake_delete:
            self.assertFalse(client.upload_cover("library-1", b"new-cover"))
            fake_delete.assert_not_called()

    def test_random_posters_keep_their_matching_backdrops(self):
        client = EmbyClient("http://emby.local", "test-key")
        client._get_user_id = lambda: "user-1"
        client.get_library_count = lambda _library_id: 3
        items = [
            {
                "Id": f"item-{index}",
                "ImageTags": {"Primary": f"primary-{index}"},
                "BackdropImageTags": [f"backdrop-{index}"],
            }
            for index in range(1, 4)
        ]

        client._request = lambda _method, _endpoint, **kwargs: {"Items": items}
        with patch("core.emby_client.random.sample", side_effect=lambda values, limit: list(reversed(values))[:limit]):
            assets = client.get_assets("library-1", mode="random", poster_limit=2, backdrop_limit=0)

        self.assertIn("item-3/Images/Primary", assets["posters"][0])
        self.assertIn("item-3/Images/Backdrop", assets["poster_backdrops"][0])
        self.assertIn("item-2/Images/Primary", assets["posters"][1])
        self.assertIn("item-2/Images/Backdrop", assets["poster_backdrops"][1])

    def test_latest_mode_finds_next_poster_with_backdrop(self):
        client = EmbyClient("http://emby.local", "test-key")
        client._get_user_id = lambda: "user-1"
        client.get_library_count = lambda _library_id: 6
        items = [
            {
                "Id": "newest-without-backdrop",
                "ImageTags": {"Primary": "primary-newest"},
                "BackdropImageTags": [],
            }
        ]
        items.extend(
            {
                "Id": f"item-{index}",
                "ImageTags": {"Primary": f"primary-{index}"},
                "BackdropImageTags": [f"backdrop-{index}"],
            }
            for index in range(2, 7)
        )
        client._request = lambda _method, _endpoint, **kwargs: {"Items": items}

        assets = client.get_assets(
            "library-1",
            mode="latest",
            poster_limit=5,
            backdrop_limit=5,
            fallback_to_next_backdrop=True,
        )

        self.assertEqual(len(assets["posters"]), 5)
        self.assertEqual(len(assets["poster_backdrops"]), 5)
        for offset, item_index in enumerate(range(2, 7)):
            self.assertIn(f"item-{item_index}/Images/Primary", assets["posters"][offset])
            self.assertIn(f"item-{item_index}/Images/Backdrop", assets["poster_backdrops"][offset])
        self.assertIn("item-2/Images/Backdrop", assets["bg_url"])

    def test_latest_mode_pages_forward_until_requested_pairs_are_full(self):
        client = EmbyClient("http://emby.local", "test-key")
        client._get_user_id = lambda: "user-1"
        client.get_library_count = lambda _library_id: 9
        missing_backdrops = [
            {
                "Id": f"item-{index}",
                "ImageTags": {"Primary": f"primary-{index}"},
                "BackdropImageTags": [],
            }
            for index in range(1, 4)
        ]
        complete_pairs = [
            {
                "Id": f"item-{index}",
                "ImageTags": {"Primary": f"primary-{index}"},
                "BackdropImageTags": [f"backdrop-{index}"],
            }
            for index in range(4, 10)
        ]
        all_items = missing_backdrops + complete_pairs
        backdrop_page_starts = []
        enabled_image_types = []

        def fake_request(_method, _endpoint, **kwargs):
            params = kwargs.get("params", {})
            if "EnableImageTypes" not in params:
                return {"Items": all_items, "TotalRecordCount": len(all_items)}
            start = int(params.get("StartIndex", 0))
            backdrop_page_starts.append(start)
            enabled_image_types.append(params["EnableImageTypes"])
            page = missing_backdrops if start == 0 else complete_pairs
            return {"Items": page, "TotalRecordCount": len(all_items)}

        client._request = fake_request
        assets = client.get_assets(
            "library-1",
            mode="latest",
            poster_limit=6,
            backdrop_limit=1,
            fallback_to_next_backdrop=True,
        )

        self.assertEqual(backdrop_page_starts, [0, 3])
        self.assertTrue(all("Primary" in image_types for image_types in enabled_image_types))
        self.assertEqual(len(assets["posters"]), 6)
        self.assertEqual(len(assets["poster_backdrops"]), 6)
        for offset, item_index in enumerate(range(4, 10)):
            self.assertIn(f"item-{item_index}/Images/Primary", assets["posters"][offset])
            self.assertIn(f"item-{item_index}/Images/Backdrop", assets["poster_backdrops"][offset])

    def test_latest_mode_can_disable_backdrop_fallback(self):
        client = EmbyClient("http://emby.local", "test-key")
        client._get_user_id = lambda: "user-1"
        client.get_library_count = lambda _library_id: 2
        items = [
            {
                "Id": "newest-without-backdrop",
                "ImageTags": {"Primary": "primary-newest"},
                "BackdropImageTags": [],
            },
            {
                "Id": "next-with-backdrop",
                "ImageTags": {"Primary": "primary-next"},
                "BackdropImageTags": ["backdrop-next"],
            },
        ]
        client._request = lambda _method, _endpoint, **kwargs: {"Items": items}

        assets = client.get_assets(
            "library-1",
            mode="latest",
            poster_limit=2,
            backdrop_limit=1,
            fallback_to_next_backdrop=False,
        )

        self.assertIsNone(assets["bg_url"])
        self.assertEqual(assets["backdrops"], [])

    def test_premiere_mode_uses_release_date_and_falls_back_to_year(self):
        client = EmbyClient("http://emby.local", "test-key")
        client._get_user_id = lambda: "user-1"
        client.get_library_count = lambda _library_id: 3
        requested_params = []
        items = [
            {
                "Id": "older-release",
                "PremiereDate": "2024-04-01T00:00:00.0000000Z",
                "ProductionYear": 2024,
                "ImageTags": {"Primary": "primary-older"},
                "BackdropImageTags": ["backdrop-older"],
            },
            {
                "Id": "year-fallback",
                "ProductionYear": 2025,
                "DateCreated": "2025-01-02T00:00:00.0000000Z",
                "ImageTags": {"Primary": "primary-year"},
                "BackdropImageTags": ["backdrop-year"],
            },
            {
                "Id": "newest-release",
                "PremiereDate": "2025-06-01T00:00:00.0000000Z",
                "ProductionYear": 2025,
                "ImageTags": {"Primary": "primary-newest"},
                "BackdropImageTags": ["backdrop-newest"],
            },
        ]

        def fake_request(_method, _endpoint, **kwargs):
            requested_params.append(kwargs.get("params", {}))
            return {"Items": items, "TotalRecordCount": len(items)}

        client._request = fake_request
        assets = client.get_assets(
            "library-1",
            mode="premiere",
            poster_limit=3,
            backdrop_limit=3,
            fallback_to_next_backdrop=True,
        )

        self.assertTrue(all(params["SortBy"] == "PremiereDate" for params in requested_params))
        self.assertTrue(all("PremiereDate" in params["Fields"] for params in requested_params))
        self.assertIn("newest-release/Images/Primary", assets["posters"][0])
        self.assertIn("year-fallback/Images/Primary", assets["posters"][1])
        self.assertIn("older-release/Images/Primary", assets["posters"][2])


if __name__ == "__main__":
    unittest.main()
