import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw, ImageFont

from core.engine import PosterEngine


class BadgePositionTests(unittest.TestCase):
    def test_box_badge_can_move_across_canvas(self):
        with tempfile.TemporaryDirectory() as fonts_dir:
            engine = object.__new__(PosterEngine)
            engine.fonts_dir = fonts_dir
            base = Image.new("RGBA", (640, 360), (0, 0, 0, 255))
            base_config = {
                "badge_style": "box",
                "badge_size": 42,
                "badge_bg_color": "#ffffff",
                "badge_text_color": "#000000",
            }
            upper_left = engine._draw_badge(base.copy(), {**base_config, "badge_x_percent": 0, "badge_y_percent": 0}, 128, {})
            lower_right = engine._draw_badge(base.copy(), {**base_config, "badge_x_percent": 100, "badge_y_percent": 100}, 128, {})

        upper_box = ImageChops.difference(base.convert("RGB"), upper_left.convert("RGB")).getbbox()
        lower_box = ImageChops.difference(base.convert("RGB"), lower_right.convert("RGB")).getbbox()
        self.assertIsNotNone(upper_box)
        self.assertIsNotNone(lower_box)
        self.assertLess(upper_box[0], lower_box[0])
        self.assertLess(upper_box[1], lower_box[1])
        self.assertGreaterEqual(upper_box[0], 1)
        self.assertGreaterEqual(upper_box[1], 1)
        self.assertLessEqual(lower_box[2], base.width - 1)
        self.assertLessEqual(lower_box[3], base.height - 1)

    def test_ribbon_badge_stays_inside_canvas_at_extreme_positions(self):
        with tempfile.TemporaryDirectory() as fonts_dir:
            engine = object.__new__(PosterEngine)
            engine.fonts_dir = fonts_dir
            base = Image.new("RGBA", (640, 360), (0, 0, 0, 255))
            config = {
                "badge_style": "ribbon",
                "badge_size": 50,
                "badge_bg_color": "#ffffff",
                "badge_text_color": "#ffffff",
                "badge_x_percent": 100,
                "badge_y_percent": 100,
            }
            rendered = engine._draw_badge(base.copy(), config, 128, {})

        badge_box = ImageChops.difference(base.convert("RGB"), rendered.convert("RGB")).getbbox()
        self.assertIsNotNone(badge_box)
        self.assertGreaterEqual(badge_box[0], 1)
        self.assertGreaterEqual(badge_box[1], 1)
        self.assertLessEqual(badge_box[2], base.width - 1)
        self.assertLessEqual(badge_box[3], base.height - 1)

    def test_personalized_badge_styles_render_inside_canvas(self):
        with tempfile.TemporaryDirectory() as fonts_dir:
            engine = object.__new__(PosterEngine)
            engine.fonts_dir = fonts_dir
            base = Image.new("RGBA", (640, 360), (0, 0, 0, 255))
            signatures = set()
            styles = ("circle", "outline", "hexagon", "ticket", "stamp", "glitch", "wave", "burst", "tape", "split")
            for style in styles:
                with self.subTest(style=style):
                    config = {
                        "badge_style": style,
                        "badge_size": 50,
                        "badge_bg_color": "#d7265e",
                        "badge_text_color": "#ffffff",
                        "badge_opacity": 220,
                        "badge_border_opacity": 180,
                        "badge_effect_strength": 82,
                        "badge_x_percent": 100,
                        "badge_y_percent": 100,
                    }
                    rendered = engine._draw_badge(base.copy(), config, 128, {})
                    badge_box = ImageChops.difference(base.convert("RGB"), rendered.convert("RGB")).getbbox()
                    self.assertIsNotNone(badge_box)
                    self.assertGreaterEqual(badge_box[0], 1)
                    self.assertGreaterEqual(badge_box[1], 1)
                    self.assertLessEqual(badge_box[2], base.width - 1)
                    self.assertLessEqual(badge_box[3], base.height - 1)
                    signatures.add(rendered.tobytes())

        self.assertEqual(len(signatures), len(styles))

    def test_effect_strength_changes_personalized_badge_rendering(self):
        with tempfile.TemporaryDirectory() as fonts_dir:
            engine = object.__new__(PosterEngine)
            engine.fonts_dir = fonts_dir
            base = Image.new("RGBA", (640, 360), (8, 12, 18, 255))
            base_config = {
                "badge_style": "glitch",
                "badge_size": 54,
                "badge_bg_color": "#22d3ee",
                "badge_text_color": "#ffffff",
                "badge_x_percent": 50,
                "badge_y_percent": 50,
            }
            subtle = engine._draw_badge(base.copy(), {**base_config, "badge_effect_strength": 10}, 2509, {})
            intense = engine._draw_badge(base.copy(), {**base_config, "badge_effect_strength": 100}, 2509, {})

        self.assertNotEqual(subtle.tobytes(), intense.tobytes())

    def test_badge_and_title_support_three_color_gradients(self):
        with tempfile.TemporaryDirectory() as fonts_dir:
            engine = object.__new__(PosterEngine)
            engine.fonts_dir = fonts_dir
            base = Image.new("RGBA", (640, 360), (8, 12, 18, 255))
            gradient = {
                "badge_style": "outline",
                "badge_size": 56,
                "badge_bg_color_mode": "gradient",
                "badge_bg_gradient_start": "#00e5ff",
                "badge_bg_gradient_middle": "#7c3aed",
                "badge_bg_gradient_end": "#ff2da6",
                "badge_bg_gradient_direction": "horizontal",
                "badge_text_color_mode": "gradient",
                "badge_text_gradient_start": "#fff7ad",
                "badge_text_gradient_middle": "#7dd3fc",
                "badge_text_gradient_end": "#f9a8d4",
                "badge_text_gradient_direction": "diagonal_down",
                "badge_opacity": 230,
                "badge_border_opacity": 220,
                "badge_x_percent": 50,
                "badge_y_percent": 50,
            }
            rendered = engine._draw_badge(base.copy(), gradient, 2509, {})

            title = Image.new("RGBA", (360, 90), (8, 12, 18, 255))
            title_fill = engine.resolve_text_fill({
                "title_color_mode": "gradient",
                "title_gradient_start": "#22d3ee",
                "title_gradient_middle": "#a78bfa",
                "title_gradient_end": "#fb7185",
                "title_gradient_direction": "horizontal",
            }, "title", "#ffffff")
            engine.draw_text_wrapper(ImageDraw.Draw(title), "FRAMEBASE", 12, 18, ImageFont.load_default(), 320, title_fill)

        badge_box = ImageChops.difference(base.convert("RGB"), rendered.convert("RGB")).getbbox()
        self.assertIsNotNone(badge_box)
        badge_colors = rendered.convert("RGB").crop(badge_box).getcolors(maxcolors=640 * 360) or []
        title_colors = title.convert("RGB").getcolors(maxcolors=360 * 90) or []
        self.assertGreater(len(badge_colors), 20)
        self.assertGreater(len(title_colors), 4)


if __name__ == "__main__":
    unittest.main()
