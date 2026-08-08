# -*- coding: utf-8 -*-
"""Tests for the smart toon render pure presets/logic."""
import unittest

from src.core.render_optimizer.presets import (  # pylint: disable=import-error
    TOON_STYLE_STANDARD,
    TOON_STYLE_SOFT,
    TOON_STYLE_CONTRAST,
    TOON_STYLES,
    classify_material,
    detect_model_type,
    is_rigid_body_object_name,
    resolve_outline_thickness,
    resolve_ramp_stops,
    resolve_render_path,
)


class ResolveRampStopsTests(unittest.TestCase):
    """Toon ramp stop resolution per style and category."""

    def _assert_valid_stops(self, stops):
        self.assertGreaterEqual(len(stops), 2)
        positions = [s[0] for s in stops]
        self.assertEqual(positions, sorted(positions))
        for pos, color in stops:
            self.assertGreaterEqual(pos, 0.0)
            self.assertLessEqual(pos, 1.0)
            self.assertEqual(len(color), 3)
            for channel in color:
                self.assertGreaterEqual(channel, 0.0)
                self.assertLessEqual(channel, 1.2)

    def test_all_styles_and_categories_valid(self):
        """Every style x category combination yields well-formed stops."""
        categories = ('face', 'skin', 'hair', 'metal', 'eye_iris', 'fallback',
                      'emissive_deco', 'cloth')
        for style in TOON_STYLES:
            for category in categories:
                with self.subTest(style=style, category=category):
                    self._assert_valid_stops(resolve_ramp_stops(category, style))

    def test_standard_is_two_tone(self):
        """Standard style keeps the classic two-tone look."""
        stops = resolve_ramp_stops('cloth', TOON_STYLE_STANDARD)
        self.assertEqual(len(stops), 2)

    def test_soft_adds_midtone(self):
        """Soft style inserts a mid tone between shadow and lit."""
        stops = resolve_ramp_stops('cloth', TOON_STYLE_SOFT)
        self.assertEqual(len(stops), 3)

    def test_stops_brightness_monotonic(self):
        """Brightness must be non-decreasing across stops (no inverted bands)."""
        categories = ('face', 'skin', 'cheek', 'hair', 'metal', 'jewelry',
                      'eye_iris', 'fallback', 'emissive_deco', 'cloth')
        for style in TOON_STYLES:
            for category in categories:
                stops = resolve_ramp_stops(category, style)
                brightness = [sum(color) for _, color in stops]
                with self.subTest(style=style, category=category):
                    self.assertEqual(brightness, sorted(brightness))

    def test_soft_midtone_stays_below_lit(self):
        """Regression: face/cheek/skin threshold tweaks must not push the
        SOFT mid tone at or past the lit threshold (inverted banding)."""
        for category in ('face', 'skin', 'cheek'):
            stops = resolve_ramp_stops(category, TOON_STYLE_SOFT)
            with self.subTest(category=category):
                self.assertEqual(len(stops), 3)
                positions = [s[0] for s in stops]
                self.assertLess(positions[1], positions[2])

    def test_contrast_shadow_darker_than_standard(self):
        """Contrast style darkens shadows relative to Standard."""
        std = resolve_ramp_stops('cloth', TOON_STYLE_STANDARD)[0][1]
        con = resolve_ramp_stops('cloth', TOON_STYLE_CONTRAST)[0][1]
        self.assertLess(sum(con), sum(std))

    def test_face_brighter_than_metal(self):
        """Faces stay brighter in shadow than metal parts."""
        face = resolve_ramp_stops('face', TOON_STYLE_STANDARD)[0][1]
        metal = resolve_ramp_stops('metal', TOON_STYLE_STANDARD)[0][1]
        self.assertGreater(sum(face), sum(metal))

    def test_hair_has_highlight_stop(self):
        """Hair gets an extra highlight band for the anime shine."""
        stops = resolve_ramp_stops('hair', TOON_STYLE_STANDARD)
        self.assertGreaterEqual(len(stops), 3)
        top = stops[-1][1]
        self.assertGreater(top[0], 1.0)

    def test_eye_iris_nearly_flat(self):
        """Eyes are nearly self-lit (flat) in every style."""
        for style in TOON_STYLES:
            stops = resolve_ramp_stops('eye_iris', style)
            self.assertEqual(len(stops), 2)
            self.assertGreaterEqual(stops[-1][1][0], 0.9)

    def test_unknown_style_falls_back_to_standard(self):
        """Unknown style identifiers degrade to Standard gracefully."""
        self.assertEqual(
            resolve_ramp_stops('cloth', 'NONEXISTENT'),
            resolve_ramp_stops('cloth', TOON_STYLE_STANDARD),
        )


class DetectModelTypeTests(unittest.TestCase):
    """Model source type detection from feature flags."""

    def test_mmd_shader_wins(self):
        self.assertEqual(detect_model_type(True, True), 'MMD')

    def test_mtoon_group(self):
        self.assertEqual(detect_model_type(False, True), 'VRM')

    def test_vrm_props(self):
        self.assertEqual(detect_model_type(False, False, True), 'VRM')

    def test_generic_default(self):
        self.assertEqual(detect_model_type(False, False), 'GENERIC')


class OutlineThicknessTests(unittest.TestCase):
    """Outline thickness resolution."""

    def test_scales_with_height(self):
        thin = resolve_outline_thickness(1.0, 1.0)
        thick = resolve_outline_thickness(2.0, 1.0)
        self.assertAlmostEqual(thick / thin, 2.0)

    def test_scales_with_width_factor(self):
        base = resolve_outline_thickness(1.6, 1.0)
        wide = resolve_outline_thickness(1.6, 2.0)
        self.assertAlmostEqual(wide / base, 2.0)

    def test_reasonable_absolute_value(self):
        # 1.6m 角色、系数 1.0 时约 5.6mm
        self.assertAlmostEqual(resolve_outline_thickness(1.6, 1.0), 0.0056, places=3)

    def test_zero_height_safe(self):
        self.assertGreater(resolve_outline_thickness(0.0, 1.0), 0.0)

    def test_width_factor_clamped(self):
        self.assertEqual(
            resolve_outline_thickness(1.6, 100.0),
            resolve_outline_thickness(1.6, 5.0),
        )


class RigidBodyNameTests(unittest.TestCase):
    """MMD rigid-body dummy mesh name pattern."""

    def test_rigid_names(self):
        self.assertTrue(is_rigid_body_object_name('000_上半身'))
        self.assertTrue(is_rigid_body_object_name('075_+EarB CF AF01'))

    def test_normal_names(self):
        self.assertFalse(is_rigid_body_object_name('派蒙_mesh'))
        self.assertFalse(is_rigid_body_object_name('Cube'))
        self.assertFalse(is_rigid_body_object_name('12_'))


class ClassifyMaterialTests(unittest.TestCase):
    """Multilingual material semantic classification."""

    def test_japanese_mmd_names(self):
        cases = {
            '髪': 'hair',
            '顔': 'face',
            '肌': 'skin',
            '白目': 'eye_white',
            '服': 'cloth',
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(classify_material(name)[0], expected)

    def test_chinese_names(self):
        cases = {
            '头发': 'hair',
            '脸': 'face',
            '皮肤': 'skin',
            '眼白': 'eye_white',
            '披风': 'cloth',
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(classify_material(name)[0], expected)

    def test_overlay_suffix(self):
        self.assertTrue(classify_material('表情+')[1])
        self.assertTrue(classify_material('頬++')[1])
        self.assertFalse(classify_material('髪')[1])

    def test_unknown_is_fallback(self):
        self.assertEqual(classify_material('qwerty')[0], 'fallback')


class ResolveRenderPathTests(unittest.TestCase):
    """Transparent material render-path resolution (no S2RGB with alpha)."""

    def test_constant_alpha_forces_decal(self):
        # MMD 叠层常用的 alpha=0 默认隐藏，以及半透明薄纱
        self.assertEqual(resolve_render_path(0.0, False, 0.0), 'decal')
        self.assertEqual(resolve_render_path(0.2, True, 0.1), 'decal')
        self.assertEqual(resolve_render_path(0.998, False, 0.0), 'decal')

    def test_opaque_without_alpha_channel(self):
        self.assertEqual(resolve_render_path(1.0, False, 0.0), 'lit_opaque')

    def test_negligible_alpha_noise_is_opaque(self):
        self.assertEqual(resolve_render_path(1.0, True, 0.004), 'lit_opaque')

    def test_partial_alpha_keeps_lit_without_s2rgb(self):
        """Partial texture alpha stays lit via the no-S2RGB Principled path."""
        # 局部透明（蕾丝/发梢/全身薄纱壳）：扁平 Principled 路径
        self.assertEqual(resolve_render_path(1.0, True, 0.19), 'lit_alpha')
        self.assertEqual(resolve_render_path(1.0, True, 0.5), 'lit_alpha')

    def test_large_alpha_area_is_decal(self):
        """Mostly-transparent textures become flat decal overlays."""
        self.assertEqual(resolve_render_path(1.0, True, 0.72), 'decal')
        self.assertEqual(resolve_render_path(1.0, True, 1.0), 'decal')


if __name__ == "__main__":
    unittest.main()
