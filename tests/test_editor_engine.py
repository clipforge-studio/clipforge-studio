import unittest

from editor_engine import FILTER_CATEGORIES, build_filter_chain, filter_names, build_audio_mix_graph


class FilterCatalogTests(unittest.TestCase):
    def test_catalog_has_named_categories_and_presets(self):
        names = filter_names()
        self.assertGreaterEqual(len(names), 12)
        self.assertGreaterEqual(sum(len(items) for items in names.values()), 70)
        for category, presets in names.items():
            self.assertTrue(category)
            self.assertTrue(presets)

    def test_every_preset_builds_landscape_filter(self):
        for category, presets in FILTER_CATEGORIES.items():
            for preset in presets:
                with self.subTest(category=category, preset=preset):
                    result = build_filter_chain("Landscape", preset)
                    self.assertTrue(result)
                    self.assertIn("setsar=1", result)

    def test_vertical_filter_has_output_label(self):
        result = build_filter_chain("Vertical 9:16", "Teal & Orange")
        self.assertTrue(result.startswith("[0:v]"))
        self.assertTrue(result.endswith("[vout]"))

    def test_adjustments_and_overlay_are_applied(self):
        result = build_filter_chain(
            "Original",
            "Original",
            {"brightness": 0.2, "contrast": 1.4, "saturation": 1.2,
             "temperature": 0.3, "sharpen": 0.8, "vignette": 0.5},
            {"text": "Hello: ClipForge", "text_size": 54, "color": "yellow",
             "position": "Center", "background": True, "font": "Sans"},
        )
        self.assertIn("brightness=0.2000", result)
        self.assertIn("drawtext=", result)
        self.assertIn("box=1", result)

    def test_image_overlay_builds_second_input_graph(self):
        graph = build_filter_chain("Landscape", "Original",
            {"overlay_opacity": 0.7, "overlay_scale": 0.3},
            {"image_position": "Top Right"}, overlay_image="logo.png")
        self.assertIn("[1:v]", graph)
        self.assertIn("overlay=x=W-w-30:y=30", graph)
        self.assertIn("aa=0.700", graph)
        self.assertTrue(graph.endswith("[vout]"))

    def test_canvas_fit_modes(self):
        fit = build_filter_chain("Landscape", "Original", {"canvas_mode": "Fit"})
        fill = build_filter_chain("Landscape", "Original", {"canvas_mode": "Fill"})
        stretch = build_filter_chain("Landscape", "Original", {"canvas_mode": "Stretch"})
        self.assertIn("force_original_aspect_ratio=decrease", fit)
        self.assertIn("crop=1920:1080", fill)
        self.assertIn("scale=1920:1080", stretch)

    def test_rotation_and_flip_are_included(self):
        graph = build_filter_chain("Landscape", "Original",
            {"rotation": "90° CW", "flip_h": True, "flip_v": False})
        self.assertIn("transpose=clock", graph)
        self.assertIn("hflip", graph)

    def test_speed_changes_video_timestamps(self):
        graph = build_filter_chain("Original", "Original", {"speed": 1.5})
        self.assertIn("setpts=PTS/1.5000", graph)

    def test_video_fade_in_and_out_are_applied(self):
        graph = build_filter_chain("Original", "Original",
            {"video_fade_in": 1.5, "video_fade_out": 2, "duration": 10})
        self.assertIn("fade=t=in:st=0:d=1.500", graph)
        self.assertIn("fade=t=out:st=8.000:d=2.000", graph)

    def test_subtitle_style_is_applied(self):
        graph = build_filter_chain("Original", "Original",
            {"subtitle_size": 36, "subtitle_outline": 4},
            {"subtitle_color": "yellow", "subtitle_position": "Top"},
            subtitle="captions.srt")
        self.assertIn("FontSize=36", graph)
        self.assertIn("PrimaryColour=&H0000FFFF", graph)
        self.assertIn("Alignment=8", graph)

    def test_audio_mix_graph_includes_original_and_music(self):
        graph = build_audio_mix_graph(True, 0.8, 0.35, 1.5, 2, 30)
        self.assertIn("[0:a]volume=0.800", graph)
        self.assertIn("[1:a]volume=0.350", graph)
        self.assertIn("amix=inputs=2", graph)
        self.assertIn("afade=t=in", graph)
        self.assertIn("afade=t=out:st=28.000:d=2.000", graph)

    def test_music_only_graph_works_without_source_audio(self):
        graph = build_audio_mix_graph(False, 1, 0.5)
        self.assertEqual(graph, "[1:a]volume=0.500[aout]")

    def test_unknown_preset_is_rejected(self):
        with self.assertRaises(ValueError):
            build_filter_chain("Original", "Not A Real Filter")

    def test_adjustments_are_clamped(self):
        result = build_filter_chain("Original", "Original",
                                    {"brightness": 20, "contrast": -4})
        self.assertIn("brightness=1.0000", result)
        self.assertIn("contrast=0.0000", result)


if __name__ == "__main__":
    unittest.main()
