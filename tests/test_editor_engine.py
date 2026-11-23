import unittest

from editor_engine import FILTER_CATEGORIES, build_filter_chain, filter_names


class FilterCatalogTests(unittest.TestCase):
    def test_catalog_has_named_categories_and_presets(self):
        names = filter_names()
        self.assertEqual(len(names), 7)
        self.assertGreaterEqual(sum(len(items) for items in names.values()), 40)
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
