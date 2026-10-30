import importlib.util
import os
import unittest

from PIL import Image


MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layouts", "自由设计.py")


def load_layout_module():
    spec = importlib.util.spec_from_file_location("free_designer_layout", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeContext:
    fonts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fonts")

    def download_img(self, url):
        if url == "backdrop":
            return Image.new("RGBA", (640, 360), (20, 80, 130, 255))
        if url == "poster":
            return Image.new("RGBA", (400, 600), (180, 45, 60, 255))
        if url == "poster-red":
            return Image.new("RGBA", (400, 600), (210, 35, 45, 255))
        if url == "poster-blue":
            return Image.new("RGBA", (400, 600), (20, 80, 210, 255))
        if url == "backdrop-red":
            return Image.new("RGBA", (640, 360), (170, 45, 30, 255))
        if url == "backdrop-blue":
            return Image.new("RGBA", (640, 360), (15, 110, 170, 255))
        return None


class FreeDesignerLayoutTests(unittest.TestCase):
    def test_renders_saved_layers_on_full_hd_canvas(self):
        layout = load_layout_module()
        config = {
            "canvas_bg_color": "#101820",
            "title": "电影库",
            "designer_elements": [
                {"type": "backdrop", "x": 0, "y": 0, "w": 1920, "h": 1080, "opacity": 100},
                {"type": "shape", "x": 80, "y": 90, "w": 500, "h": 200, "fill": "#1479d7", "radius": 20, "opacity": 80},
                {"type": "poster", "x": 1200, "y": 180, "w": 400, "h": 600, "assetIndex": 0, "radius": 24, "opacity": 100},
                {"type": "text", "x": 120, "y": 350, "w": 800, "h": 180, "textSource": "title", "fontSize": 120, "color": "#ffffff", "opacity": 100},
            ],
        }
        result = layout.render(FakeContext(), Image.new("RGBA", (1920, 1080)), config, {"bg_url": "backdrop", "posters": ["poster"], "count": 12}, {})

        self.assertEqual(result.size, (1920, 1080))
        self.assertNotEqual(result.getpixel((10, 10)), result.getpixel((100, 100)))

    def test_hidden_layers_are_not_rendered(self):
        layout = load_layout_module()
        base = {"canvas_bg_color": "#112233", "designer_elements": [{"type": "shape", "hidden": True, "x": 0, "y": 0, "w": 1920, "h": 1080, "fill": "#ffffff"}]}
        result = layout.render(FakeContext(), Image.new("RGBA", (1920, 1080)), base, {}, {})

        self.assertEqual(result.getpixel((100, 100)), (17, 34, 51, 255))

    def test_poster_can_extend_beyond_canvas_and_is_cropped(self):
        layout = load_layout_module()
        config = {
            "canvas_bg_color": "#101820",
            "designer_elements": [
                {
                    "type": "poster",
                    "x": -100,
                    "y": 100,
                    "w": 200,
                    "h": 300,
                    "assetIndex": 0,
                    "fit": "cover",
                    "opacity": 100,
                }
            ],
        }
        result = layout.render(FakeContext(), Image.new("RGBA", (1920, 1080)), config, {"posters": ["poster"]}, {})

        self.assertEqual(result.getpixel((0, 200))[:3], (180, 45, 60))
        self.assertEqual(result.getpixel((99, 200))[:3], (180, 45, 60))
        self.assertEqual(result.getpixel((100, 200))[:3], (16, 24, 32))

    def test_chinese_text_falls_back_when_selected_font_has_no_glyphs(self):
        layout = load_layout_module()
        font = layout._load_font(FakeContext(), "Bodoni MT Black.TTF", 96, "国产剧")
        missing = layout._glyph_signature(font, chr(0x10FFFF))

        self.assertTrue(all(layout._glyph_signature(font, char) != missing for char in "国产剧"))

    def test_text_layer_supports_gradient_color_and_opacity(self):
        layout = load_layout_module()
        element = {
            "type": "text",
            "w": 720,
            "h": 220,
            "textSource": "custom",
            "text": "FRAMEBASE",
            "fontSize": 140,
            "align": "center",
            "verticalAlign": "center",
            "colorMode": "gradient",
            "gradientStart": "#ff0000",
            "gradientMiddle": "#00ff00",
            "gradientEnd": "#0000ff",
            "gradientDirection": "horizontal",
            "opacity": 60,
        }

        layer = layout._element_image(FakeContext(), element, {}, {})
        visible = [pixel for pixel in layer.get_flattened_data() if pixel[3] > 0]

        self.assertTrue(visible)
        self.assertLessEqual(max(pixel[3] for pixel in visible), 153)
        self.assertGreater(len({pixel[:3] for pixel in visible}), 20)

    def test_backdrop_uses_the_topmost_visible_poster(self):
        layout = load_layout_module()
        config = {
            "designer_elements": [
                {"type": "backdrop", "x": 0, "y": 0, "w": 1920, "h": 1080, "opacity": 100},
                {"type": "poster", "x": 100, "y": 100, "w": 200, "h": 300, "assetIndex": 0, "opacity": 100},
                {"type": "poster", "x": 1500, "y": 700, "w": 200, "h": 300, "assetIndex": 1, "opacity": 100},
            ]
        }

        result = layout.render(
            FakeContext(),
            Image.new("RGBA", (1920, 1080)),
            config,
            {
                "bg_url": "backdrop",
                "posters": ["poster-red", "poster-blue"],
                "poster_backdrops": ["backdrop-red", "backdrop-blue"],
            },
            {},
        )

        self.assertEqual(result.getpixel((900, 400))[:3], (15, 110, 170))

    def test_backdrop_skips_topmost_poster_without_a_matching_backdrop(self):
        layout = load_layout_module()
        config = {
            "designer_elements": [
                {"type": "backdrop", "x": 0, "y": 0, "w": 1920, "h": 1080, "opacity": 100},
                {"type": "poster", "x": 100, "y": 100, "w": 200, "h": 300, "assetIndex": 0, "opacity": 100},
                {"type": "poster", "x": 1500, "y": 700, "w": 200, "h": 300, "assetIndex": 1, "opacity": 100},
            ]
        }

        result = layout.render(
            FakeContext(),
            Image.new("RGBA", (1920, 1080)),
            config,
            {
                "bg_url": "backdrop",
                "posters": ["poster-red", "poster-blue"],
                "poster_backdrops": ["backdrop-red", None],
            },
            {},
        )

        self.assertEqual(result.getpixel((900, 400))[:3], (170, 45, 30))

    def test_backdrop_uses_default_only_when_no_poster_has_a_backdrop(self):
        layout = load_layout_module()
        config = {
            "designer_elements": [
                {"type": "backdrop", "x": 0, "y": 0, "w": 1920, "h": 1080, "opacity": 100},
                {"type": "poster", "x": 100, "y": 100, "w": 200, "h": 300, "assetIndex": 0, "opacity": 100},
                {"type": "poster", "x": 1500, "y": 700, "w": 200, "h": 300, "assetIndex": 1, "opacity": 100},
            ]
        }

        result = layout.render(
            FakeContext(),
            Image.new("RGBA", (1920, 1080)),
            config,
            {
                "bg_url": "backdrop",
                "posters": ["poster-red", "poster-blue"],
                "poster_backdrops": [None, None],
            },
            {},
        )

        self.assertEqual(result.getpixel((900, 400))[:3], (20, 80, 130))


if __name__ == "__main__":
    unittest.main()
