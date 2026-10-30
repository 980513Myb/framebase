import unittest

from app.services.title_mapping import apply_title_mapping, normalize_title_mapping


class TitleMappingTest(unittest.TestCase):
    def test_old_string_mapping_keeps_library_name_as_title(self):
        mapping = normalize_title_mapping({"欧美电影": "Western Movies"})

        config = apply_title_mapping({}, "欧美电影", mapping)

        self.assertEqual(config["title"], "欧美电影")
        self.assertEqual(config["subtitle"], "Western Movies")

    def test_object_mapping_can_override_title_and_subtitle(self):
        mapping = normalize_title_mapping({
            "TMDB高分电影": {
                "title": "高分电影",
                "subtitle": "TMDb Top Rated Movies",
            }
        })

        config = apply_title_mapping({}, "TMDB高分电影", mapping)

        self.assertEqual(config["title"], "高分电影")
        self.assertEqual(config["subtitle"], "TMDb Top Rated Movies")

    def test_missing_mapping_leaves_subtitle_empty(self):
        config = apply_title_mapping({}, "日韩动漫", {})

        self.assertEqual(config["title"], "日韩动漫")
        self.assertEqual(config["subtitle"], "")

    def test_mapping_without_subtitle_leaves_subtitle_empty(self):
        config = apply_title_mapping({}, "国产剧集", {"国产剧集": {"title": "国剧"}})

        self.assertEqual(config["title"], "国剧")
        self.assertEqual(config["subtitle"], "")


if __name__ == "__main__":
    unittest.main()
