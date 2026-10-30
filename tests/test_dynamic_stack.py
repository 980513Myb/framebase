import base64
import importlib.util
import shutil
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

from core.engine import PosterEngine


def load_layout():
    path = Path(__file__).resolve().parents[1] / "layouts" / "经典堆叠(动态).py"
    spec = importlib.util.spec_from_file_location("dynamic_stack_layout", path)
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

    def draw_text_wrapper(self, draw, text, x, y, font, max_width, fill):
        return y


class DynamicStackTests(unittest.TestCase):
    def setUp(self):
        self.layout = load_layout()
        self.ctx = FakeContext()
        self.fallback = Image.new("RGBA", (1920, 1080), (15, 120, 50, 255))
        self.assets = {
            "posters": ["poster-1", "poster-2", "poster-3"],
            "poster_backdrops": ["backdrop-1", "backdrop-2", "backdrop-3"],
        }
        self.config = {
            "poster_count": 3,
            "switch_interval": 2500,
            "transition_ms": 500,
            "background_brightness": 1.0,
            "blur_radius": 0,
            "poster_scale": 0.5,
            "poster_x_percent": 55,
            "poster_y_percent": 50,
            "poster_gap": 80,
            "poster_radius": 0,
            "poster_brightness": 1.0,
            "poster_shadow_opacity": 0,
            "shadow_blur": 0,
            "shadow_offset": 0,
            "mask_opacity": 0,
            "title": "",
            "subtitle": "",
        }

    def test_top_poster_and_backdrop_advance_together(self):
        first = self.layout.render(self.ctx, self.fallback, self.config, self.assets, {}, step=0.0)
        second = self.layout.render(self.ctx, self.fallback, self.config, self.assets, {}, step=0.34)
        self.assertEqual(first.getpixel((100, 100))[:3], (20, 80, 180))
        self.assertEqual(second.getpixel((100, 100))[:3], (180, 40, 30))
        self.assertEqual(first.getpixel((1100, 590))[:3], (235, 235, 235))
        self.assertEqual(second.getpixel((1100, 590))[:3], (210, 180, 80))

    def test_transition_blends_complete_matched_states(self):
        transition = self.layout.render(self.ctx, self.fallback, self.config, self.assets, {}, step=0.85 / 3)
        color = transition.getpixel((100, 100))[:3]
        self.assertNotEqual(color, (20, 80, 180))
        self.assertNotEqual(color, (180, 40, 30))

    def test_posters_without_backdrops_are_skipped_when_matches_exist(self):
        pairs = self.layout._poster_pairs({
            "posters": ["poster-1", "poster-2", "poster-3"],
            "poster_backdrops": ["backdrop-1", None, "backdrop-3"],
        }, 3)
        self.assertEqual(pairs, [("poster-1", "backdrop-1"), ("poster-3", "backdrop-3")])

    def test_engine_outputs_emby_compatible_gif(self):
        source = Path(__file__).resolve().parents[1] / "layouts" / "经典堆叠(动态).py"
        previous_layouts = PosterEngine._shared_layouts
        previous_loaded = PosterEngine._layouts_loaded
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
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
                config = {
                    **self.config,
                    "engine": "经典堆叠(动态)",
                    "enable_animation": True,
                    "anim_output_width": 533,
                    "anim_duration": 100,
                    "anim_format": "gif",
                    "poster_count": 2,
                    "badge_style": "none",
                }
                raw = base64.b64decode(engine.draw(config, assets))
                animation = Image.open(BytesIO(raw))
                self.assertTrue(animation.is_animated)
                self.assertEqual(animation.format, "GIF")
                self.assertEqual(animation.size, (533, 300))
                self.assertGreaterEqual(animation.n_frames, 10)
                animation.seek(0)
                first_color = animation.convert("RGB").getpixel((20, 20))
                animation.seek(animation.n_frames // 2)
                later_color = animation.convert("RGB").getpixel((20, 20))
                self.assertNotEqual(first_color, later_color)
        finally:
            PosterEngine._shared_layouts = previous_layouts
            PosterEngine._layouts_loaded = previous_loaded


if __name__ == "__main__":
    unittest.main()
