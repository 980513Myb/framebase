import base64
import importlib.util
import shutil
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

from core.engine import PosterEngine


ROOT = Path(__file__).resolve().parents[1]


def load_layout(filename, module_name):
    path = ROOT / "layouts" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def data_url(color, size):
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")


class FakeContext:
    def __init__(self):
        self.images = {
            "poster-1": Image.new("RGBA", (400, 600), (235, 235, 235, 255)),
            "poster-2": Image.new("RGBA", (400, 600), (210, 180, 80, 255)),
            "poster-3": Image.new("RGBA", (400, 600), (100, 210, 180, 255)),
            "backdrop-1": Image.new("RGBA", (1920, 1080), (20, 80, 180, 255)),
            "backdrop-2": Image.new("RGBA", (1920, 1080), (180, 40, 30, 255)),
            "backdrop-3": Image.new("RGBA", (1920, 1080), (45, 150, 80, 255)),
        }

    def download_img(self, url):
        image = self.images.get(url)
        return image.copy() if image else None

    def create_smart_mask(self, width, height, opacity, coverage, direction):
        return Image.new("L", (width, height), 0)

    def resolve_text_fill(self, config, prefix, fallback, opacity=255):
        return fallback

    def draw_text_wrapper(self, draw, text, x, y, font, max_width, fill, align="left"):
        return y


class DynamicCarouselTests(unittest.TestCase):
    def setUp(self):
        self.tile = load_layout("经典平铺(动态).py", "dynamic_tile_layout")
        self.focus = load_layout("聚焦(动态).py", "dynamic_focus_layout")
        self.ctx = FakeContext()
        self.fallback = Image.new("RGBA", (1920, 1080), (15, 120, 50, 255))
        self.assets = {
            "posters": ["poster-1", "poster-2", "poster-3"],
            "poster_backdrops": ["backdrop-1", "backdrop-2", "backdrop-3"],
        }

    def test_dynamic_tile_keeps_center_poster_and_background_matched(self):
        config = {
            "poster_count": 3,
            "switch_interval": 2500,
            "transition_ms": 500,
            "background_brightness": 1.0,
            "blur_radius": 0,
            "poster_height_percent": 40,
            "poster_baseline_percent": 98,
            "poster_ratio": 0.67,
            "poster_spacing": 18,
            "active_scale": 1.08,
            "active_border_width": 0,
            "poster_shadow_opacity": 0,
            "mask_opacity": 0,
            "title": "",
            "subtitle": "",
        }

        first = self.tile.render(self.ctx, self.fallback, config, self.assets, {}, step=0.0)
        second = self.tile.render(self.ctx, self.fallback, config, self.assets, {}, step=1 / 3)

        self.assertEqual(first.getpixel((100, 100))[:3], (20, 80, 180))
        self.assertEqual(second.getpixel((100, 100))[:3], (180, 40, 30))
        self.assertEqual(first.getpixel((960, 760))[:3], (235, 235, 235))
        self.assertEqual(second.getpixel((960, 760))[:3], (210, 180, 80))

    def test_dynamic_focus_keeps_center_poster_and_background_matched(self):
        config = {
            "poster_count": 3,
            "switch_interval": 2500,
            "transition_ms": 500,
            "background_brightness": 1.0,
            "bg_blur": 0,
            "bg_overlay_opacity": 0,
            "spotlight_intensity": 0,
            "bg_vignette": 0,
            "hero_height_percent": 50,
            "baseline_percent": 94,
            "poster_ratio": 0.66,
            "side_scale_step": 0.9,
            "overlap_percent": 40,
            "reflection_opacity": 0,
            "hero_shadow_opacity": 0,
            "title": "",
            "subtitle": "",
        }

        first = self.focus.render(self.ctx, self.fallback, config, self.assets, {}, step=0.0)
        second = self.focus.render(self.ctx, self.fallback, config, self.assets, {}, step=1 / 3)

        self.assertEqual(first.getpixel((100, 100))[:3], (20, 80, 180))
        self.assertEqual(second.getpixel((100, 100))[:3], (180, 40, 30))
        self.assertEqual(first.getpixel((960, 700))[:3], (235, 235, 235))
        self.assertEqual(second.getpixel((960, 700))[:3], (210, 180, 80))

    def test_both_layouts_skip_posters_without_backdrops(self):
        assets = {
            "posters": ["poster-1", "poster-2", "poster-3"],
            "poster_backdrops": [None, "backdrop-2", "backdrop-3"],
        }
        self.assertEqual(self.tile._poster_pairs(assets, 3)[0], ("poster-2", "backdrop-2"))
        self.assertEqual(self.focus._poster_pairs(assets, 3)[0], ("poster-2", "backdrop-2"))

    def test_dynamic_layout_schemas_hide_fixed_emby_output(self):
        for layout in (self.tile, self.focus):
            items = [item for group in layout.get_schema() for item in group["items"]]
            keys = {item["key"] for item in items}
            self.assertNotIn("anim_output_width", keys)
            self.assertNotIn("anim_format", keys)

    def test_engine_falls_back_when_configured_font_cannot_render_chinese(self):
        engine = PosterEngine.__new__(PosterEngine)
        engine.fonts_dir = str(ROOT / "fonts")
        font = engine._load_text_font("字魂白鸽天行体(商用需授权).ttf", 80, "欧美剧")
        missing = engine._glyph_signature(font, chr(0x10FFFF))
        self.assertTrue(all(engine._glyph_signature(font, char) != missing for char in "欧美剧"))

    def test_engine_outputs_animated_gif_for_tile_and_focus(self):
        sources = [
            ROOT / "layouts" / "经典平铺(动态).py",
            ROOT / "layouts" / "聚焦(动态).py",
        ]
        previous_layouts = PosterEngine._shared_layouts
        previous_loaded = PosterEngine._layouts_loaded
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                for source in sources:
                    shutil.copyfile(source, Path(temp_dir) / source.name)
                PosterEngine._shared_layouts = None
                PosterEngine._layouts_loaded = False
                engine = PosterEngine(fonts_dir=temp_dir, layouts_dir=temp_dir)
                assets = {
                    "bg_url": data_url((15, 120, 50), (1920, 1080)),
                    "posters": [
                        data_url((235, 235, 235), (400, 600)),
                        data_url((210, 180, 80), (400, 600)),
                    ],
                    "poster_backdrops": [
                        data_url((20, 80, 180), (1920, 1080)),
                        data_url((180, 40, 30), (1920, 1080)),
                    ],
                    "count": 2,
                }
                base_config = {
                    "enable_animation": True,
                    "switch_interval": 1000,
                    "transition_ms": 400,
                    "anim_duration": 100,
                    "anim_format": "gif",
                    "poster_count": 2,
                    "badge_style": "none",
                    "title": "",
                    "subtitle": "",
                    "blur_radius": 0,
                    "bg_blur": 0,
                }

                for engine_name in ("经典平铺(动态)", "聚焦(动态)"):
                    raw = base64.b64decode(engine.draw({**base_config, "engine": engine_name}, assets))
                    animation = Image.open(BytesIO(raw))
                    self.assertTrue(animation.is_animated)
                    self.assertEqual(animation.format, "GIF")
                    self.assertEqual(animation.size, (533, 300))
                    self.assertGreater(animation.n_frames, 2)
        finally:
            PosterEngine._shared_layouts = previous_layouts
            PosterEngine._layouts_loaded = previous_loaded


if __name__ == "__main__":
    unittest.main()
