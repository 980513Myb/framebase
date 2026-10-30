import base64
import importlib.util
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops

from core.asset_limits import resolve_asset_limits
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


class ColorContext:
    def __init__(self, count=9):
        self.poster_colors = [
            ((index * 31 + 30) % 240 + 10, (index * 53 + 40) % 240 + 10, (index * 71 + 50) % 240 + 10)
            for index in range(count)
        ]
        self.backdrop_colors = [
            ((index * 47 + 20) % 220 + 10, (index * 29 + 60) % 220 + 10, (index * 83 + 80) % 220 + 10)
            for index in range(count)
        ]
        self.images = {}
        for index in range(count):
            self.images[f"poster-{index}"] = Image.new("RGBA", (400, 600), (*self.poster_colors[index], 255))
            self.images[f"backdrop-{index}"] = Image.new("RGBA", (1920, 1080), (*self.backdrop_colors[index], 255))

    def download_img(self, url):
        image = self.images.get(url)
        return image.copy() if image else None

    def resolve_text_fill(self, config, prefix, fallback, opacity=255):
        return fallback

    def draw_text_wrapper(self, draw, text, x, y, font, max_width, fill, align="left"):
        return y


class DynamicLayoutCountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tile = load_layout("经典平铺(动态).py", "count_dynamic_tile")
        cls.stack = load_layout("经典堆叠(动态).py", "count_dynamic_stack")
        cls.focus = load_layout("聚焦(动态).py", "count_dynamic_focus")
        cls.fan = load_layout("扇形展开(动态).py", "count_dynamic_fan")
        cls.rotation = load_layout("旋转(动态).py", "count_dynamic_rotation")
        cls.grid = load_layout("经典九宫格(动态).py", "count_dynamic_grid")

    def test_dynamic_defaults_and_backdrops_follow_poster_count(self):
        expected = {
            self.tile: 8,
            self.stack: 6,
            self.focus: 9,
            self.fan: 9,
            self.rotation: 3,
            self.grid: 9,
        }
        for layout, poster_count in expected.items():
            with self.subTest(layout=layout.__name__):
                items = [item for group in layout.get_schema() for item in group["items"]]
                values = {item["key"]: item.get("default") for item in items}
                self.assertEqual(values["poster_count"], poster_count)
                self.assertNotIn("backdrop_count", values)
                self.assertNotIn("anim_output_width", values)
                self.assertNotIn("anim_format", values)
                self.assertEqual(
                    resolve_asset_limits({"engine": "任意(动态)", "poster_count": poster_count, "backdrop_count": 1}),
                    (poster_count, poster_count),
                )

    def test_static_and_nine_grid_asset_limits(self):
        self.assertEqual(resolve_asset_limits({"engine": "经典平铺", "poster_count": 5, "backdrop_count": 1}), (5, 1))
        self.assertEqual(resolve_asset_limits({"engine": "旋转堆叠", "backdrop_count": 1}), (9, 1))
        self.assertEqual(resolve_asset_limits({"engine": "经典九宫格(动态)"}), (9, 9))

    def test_tile_five_posters_are_unique_and_centered(self):
        ctx = ColorContext(6)
        pairs = [(f"poster-{index}", f"backdrop-{index}") for index in range(5)]
        canvas = Image.new("RGBA", (1000, 600), (1, 2, 3, 255))
        config = {
            "poster_count": 5,
            "poster_height_percent": 40,
            "poster_ratio": 0.6667,
            "poster_spacing": 10,
            "active_x_percent": 50,
            "poster_baseline_percent": 90,
            "active_scale": 1.0,
            "poster_corner_radius": 0,
            "side_poster_brightness": 1.0,
            "active_border_width": 0,
            "poster_shadow_opacity": 0,
            "shadow_blur": 0,
        }
        result = self.tile._draw_carousel(ctx, canvas, config, pairs, current=0, slide=0.0)
        pixels = list(result.convert("RGB").getdata())
        for color in ctx.poster_colors[:5]:
            self.assertIn(color, pixels)
        self.assertNotIn(ctx.poster_colors[5], pixels)
        self.assertEqual(result.getpixel((500, 420))[:3], ctx.poster_colors[0])

    def test_rotation_honors_six_real_layers(self):
        ctx = ColorContext(6)
        posters = [ctx.download_img(f"poster-{index}") for index in range(6)]
        canvas = Image.new("RGBA", (1200, 800), (2, 3, 4, 255))
        config = {
            "card_scale": 0.62,
            "card_x_percent": 55,
            "card_y_percent": 50,
            "card_radius": 0,
            "angle_top": 0,
            "angle_mid": 12,
            "angle_bot": 42,
            "layer_scale_step": 1.0,
            "shadow_opacity": 0,
            "shadow_blur": 0,
        }
        result = self.rotation._draw_cards(ctx, canvas, config, posters, progress=0.0)
        pixels = list(result.convert("RGB").getdata())
        for color in ctx.poster_colors:
            self.assertIn(color, pixels)

    def test_nine_grid_background_and_center_advance_together(self):
        ctx = ColorContext(9)
        fallback = Image.new("RGBA", (1920, 1080), (5, 6, 7, 255))
        assets = {
            "posters": [f"poster-{index}" for index in range(9)],
            "poster_backdrops": [f"backdrop-{index}" for index in range(9)],
        }
        config = {
            "poster_count": 9,
            "switch_interval": 2500,
            "transition_ms": 900,
            "background_brightness": 1.0,
            "background_overlay": 0,
            "bg_blur": 0,
            "shadow_opacity": 0,
            "title": "",
            "subtitle": "",
        }
        first = self.grid.render(ctx, fallback, config, assets, {}, step=0.0)
        second = self.grid.render(ctx, fallback, config, assets, {}, step=1 / 9)
        self.assertEqual(first.getpixel((10, 10))[:3], ctx.backdrop_colors[4])
        self.assertEqual(second.getpixel((10, 10))[:3], ctx.backdrop_colors[3])
        early = self.grid.render(ctx, fallback, config, assets, {}, step=0.05 / 9)
        late = self.grid.render(ctx, fallback, config, assets, {}, step=0.9 / 9)
        self.assertEqual(early.getpixel((10, 10))[:3], ctx.backdrop_colors[4])
        self.assertNotEqual(late.getpixel((10, 10))[:3], ctx.backdrop_colors[4])
        self.assertNotEqual(late.getpixel((10, 10))[:3], ctx.backdrop_colors[3])
        halfway = self.grid.render(ctx, fallback, config, assets, {}, step=0.1)
        flat = Image.blend(first, second, 0.5)
        self.assertIsNotNone(ImageChops.difference(halfway.convert("RGB"), flat.convert("RGB")).getbbox())

    def test_nine_grid_slides_continuously_without_a_hold_phase(self):
        current, upcoming, progress = self.grid._timeline_state(0.02, 9)
        self.assertEqual((current, upcoming), (4, 3))
        self.assertAlmostEqual(progress, 0.18)
        items = [item for group in self.grid.get_schema() for item in group["items"]]
        values = {item["key"]: item for item in items}
        self.assertNotIn("transition_ms", values)
        self.assertNotIn("slide_x", values)
        self.assertNotIn("slide_y", values)
        self.assertIn("连续滑动", values["switch_interval"]["label"])
        self.assertEqual(values["background_transition_ms"]["default"], 700)

    def test_nine_grid_outputs_animated_gif(self):
        assets = {
            "bg_url": data_url((10, 20, 30), (1920, 1080)),
            "posters": [data_url((60 + index * 30, 80, 120), (400, 600)) for index in range(3)],
            "poster_backdrops": [data_url((30, 60 + index * 30, 100), (1920, 1080)) for index in range(3)],
            "count": 3,
        }
        engine = PosterEngine(fonts_dir=str(ROOT / "fonts"), layouts_dir=str(ROOT / "layouts"))
        config = {
            "engine": "经典九宫格(动态)",
            "enable_animation": True,
            "switch_interval": 500,
            "transition_ms": 200,
            "anim_duration": 100,
            "anim_format": "apng",
            "anim_output_width": 1280,
            "poster_count": 3,
            "shadow_opacity": 0,
            "badge_style": "none",
            "title": "",
            "subtitle": "",
        }
        animation = Image.open(BytesIO(base64.b64decode(engine.draw(config, assets))))
        self.assertTrue(animation.is_animated)
        self.assertEqual(animation.format, "GIF")
        self.assertEqual(animation.size, (533, 300))


if __name__ == "__main__":
    unittest.main()
