# -*- coding: utf-8 -*-
"""Tests for the render pipeline version compatibility helpers."""
import unittest

from src.core.render_optimizer.pipeline import (  # pylint: disable=import-error
    EEVEE_ENGINE_ID,
    EEVEE_ENGINE_ID_NEXT,
    resolve_compositor_node_ids,
    resolve_eevee_engine_id,
)


class EeveeEngineIdTests(unittest.TestCase):
    """EEVEE engine identifier resolution across versions."""

    def test_eevee_next_id_for_4_x(self):
        """4.2-4.5 use the transitional BLENDER_EEVEE_NEXT identifier."""
        for version in ((4, 2, 0), (4, 3, 1), (4, 5, 0)):
            self.assertEqual(resolve_eevee_engine_id(version), EEVEE_ENGINE_ID_NEXT)

    def test_eevee_id_for_5_x(self):
        """5.0+ renamed the engine back to BLENDER_EEVEE."""
        for version in ((5, 0, 0), (5, 1, 0), (5, 2, 3)):
            self.assertEqual(resolve_eevee_engine_id(version), EEVEE_ENGINE_ID)


class CompositorNodeIdsTests(unittest.TestCase):
    """Compositor node bl_idname resolution across versions."""

    def test_legacy_ids_before_5_0(self):
        """4.x keeps the classic compositor node types."""
        mix_id, ramp_id, output_id = resolve_compositor_node_ids((4, 5, 0))
        self.assertEqual(mix_id, 'CompositorNodeMixRGB')
        self.assertEqual(ramp_id, 'CompositorNodeValToRGB')
        self.assertEqual(output_id, 'CompositorNodeComposite')

    def test_modern_ids_from_5_0(self):
        """5.0 removed those nodes; shader counterparts replace them."""
        mix_id, ramp_id, output_id = resolve_compositor_node_ids((5, 0, 0))
        self.assertEqual(mix_id, 'ShaderNodeMixRGB')
        self.assertEqual(ramp_id, 'ShaderNodeValToRGB')
        self.assertEqual(output_id, 'NodeGroupOutput')


if __name__ == "__main__":
    unittest.main()
