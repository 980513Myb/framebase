import base64
import importlib.util
import shutil
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops

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

    def resolve_text_fill(self, config, prefix, fallback, opacity=255):
        return fallback

    def draw_text_wrapper(self, draw, text, x, y, font, max_width, fill, align="left"):
        return y


class DynamicFanRotationTests(unittest.TestCase):
    def setUp(self):
        self.fan = load_layout("扇形展开(动态).py", "dynamic_fan_layout")
        self.rotation = load_layout("旋转(动态).py", "dynamic_rotation_layout")
        self.ctx = FakeContext()
        self.fallback = Image.new("RGBA", (1920, 1080), (15, 120, 50, 255))
        self.assets = {
            "posters": ["poster-1", "poster-2", "poster-3"],
            "poster_backdrops": ["backdrop-1", "backdrop-2", "backdrop-3"],
        }

    def test_fan_center_and_background_advance_together(self):
        config = {
            "poster_count": 3,
            "switch_interval": 2500,
            "transition_ms": 500,
            "background_brightness": 1.0,
            "bg_blur": 0,
            "bg_darkness": 0,
            "fan_radius": 900,
            "fan_spread": 30,
            "center_scale": 0.4,
            "side_scale_shrink": 0.9,
            "layout_y_offset": 0,
            "reflection_opacity": 0,
            "shadow_blur": 0,
            "title": "",
            "subtitle": "",
        }
        first = self.fan.render(self.ctx, self.fallback, config, self.assets, {}, step=0.0)
        second = self.fan.render(self.ctx, self.fallback, config, self.assets, {}, step=1 / 3)
        self.assertEqual(first.getpixel((100, 100))[:3], (20, 80, 180))
        self.assertEqual(second.getpixel((100, 100))[:3], (180, 40, 30))
        self.assertEqual(first.getpixel((960, 500))[:3], (235, 235, 235))
        self.assertEqual(second.getpixel((960, 500))[:3], (210, 180, 80))

    def test_rotation_top_card_and_background_advance_together(self):
        config = {
            "poster_count": 3,
            "switch_interval": 2500,
            "transition_ms": 500,
            "background_brightness": 1.0,
            "bg_blur": 0,
            "color_ratio": 0,
            "grain_intensity": 0,
            "card_scale": 0.5,
            "card_x_percent": 68,
            "card_y_percent": 50,
            "card_radius": 0,
            "angle_top": 0,
            "angle_mid": 12,
            "angle_bot": 24,
            "shadow_opacity": 0,
            "shadow_blur": 0,
            "title": "",
            "subtitle": "",
        }
        first = self.rotation.render(self.ctx, self.fallback, config, self.assets, {}, step=0.0)
        second = self.rotation.render(self.ctx, self.fallback, config, self.assets, {}, step=1 / 3)
        self.assertEqual(first.getpixel((100, 100))[:3], (20, 80, 180))
        self.assertEqual(second.getpixel((100, 100))[:3], (180, 40, 30))
        card_center = (round(1920 * 0.68), 540)
        self.assertEqual(first.getpixel(card_center)[:3], (235, 235, 235))
        self.assertEqual(second.getpixel(card_center)[:3], (210, 180, 80))

    def test_transitions_move_cards_instead_of_crossfading_complete_frames(self):
        shared = {
            "poster_count": 3,
            "switch_interval": 2500,
            "transition_ms": 500,
            "background_brightness": 1.0,
            "bg_blur": 0,
            "bg_darkness": 0,
            "color_ratio": 0,
            "grain_intensity": 0,
            "reflection_opacity": 0,
            "shadow_opacity": 0,
            "shadow_blur": 0,
            "title": "",
            "subtitle": "",
        }
        fan_config = {
            **shared,
            "fan_radius": 900,
            "fan_spread": 30,
            "center_scale": 0.4,
            "side_scale_shrink": 0.85,
            "layout_y_offset": 0,
        }
        rotation_config = {
            **shared,
            "card_scale": 0.5,
            "card_x_percent": 68,
            "card_y_percent": 50,
            "card_radius": 0,
            "angle_top": 0,
            "angle_mid": 12,
            "angle_bot": 24,
        }
        for layout, config in ((self.fan, fan_config), (self.rotation, rotation_config)):
            with self.subTest(layout=layout.__name__):
                first = layout.render(self.ctx, self.fallback, config, self.assets, {}, step=0.0)
                second = layout.render(self.ctx, self.fallback, config, self.assets, {}, step=1 / 3)
                halfway = layout.render(self.ctx, self.fallback, config, self.assets, {}, step=0.3)
                flat_crossfade = Image.blend(first, second, 0.5)
                difference = ImageChops.difference(halfway.convert("RGB"), flat_crossfade.convert("RGB"))
                self.assertIsNotNone(difference.getbbox())

    def test_both_layouts_skip_posters_without_backdrops(self):
        assets = {
            "posters": ["poster-1", "poster-2", "poster-3"],
            "poster_backdrops": [None, "backdrop-2", "backdrop-3"],
        }
        self.assertEqual(self.fan._poster_pairs(assets, 3)[0], ("poster-2", "backdrop-2"))
        self.assertEqual(self.rotation._poster_pairs(assets, 3)[0], ("poster-2", "backdrop-2"))

    def test_dynamic_schemas_use_shared_animation_defaults(self):
        for layout in (self.fan, self.rotation):
            items = [item for group in layout.get_schema() for item in group["items"]]
            values = {item["key"]: item.get("default") for item in items}
            self.assertEqual(values["switch_interval"], 2500)
            self.assertEqual(values["transition_ms"], 900)
            self.assertNotIn("anim_output_width", values)
            self.assertNotIn("anim_format", values)

    def test_engine_outputs_animated_gif_for_fan_and_rotation(self):
        sources = [
            ROOT / "layouts" / "扇形展开(动态).py",
            ROOT / "layouts" / "旋转(动态).py",
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
                    "switch_interval": 500,
                    "transition_ms": 200,
                    "anim_duration": 100,
                    "anim_format": "gif",
                    "poster_count": 2,
                    "badge_style": "none",
                    "title": "",
                    "subtitle": "",
                    "bg_blur": 0,
                    "bg_darkness": 0,
                    "color_ratio": 0,
                    "grain_intensity": 0,
                    "reflection_opacity": 0,
                    "shadow_blur": 0,
                }
                for engine_name in ("扇形展开(动态)", "旋转(动态)"):
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
