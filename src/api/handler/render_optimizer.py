# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — Operators
"""
from bpy.types import Operator  # pylint: disable=import-error

from ...services.render_optimizer_service import (
    apply_render_optimizer,
    reset_render_optimizer,
)
from ...util.logger import Log


class RenderOptimizerApplyOperator(Operator):  # pylint: disable=too-few-public-methods
    """Apply smart toon render (one-click cel shading)"""
    bl_idname = "hbr_mmd.render_optimizer_apply"
    bl_label = "Apply Toon Render"
    bl_description = (
        "One-click smart cel shading: converts materials, adds outline, "
        "lights and post-processing (EEVEE only)"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        """Require at least one selected object."""
        return len(context.selected_objects) > 0

    def execute(self, context):
        """Apply toon render setup and report results."""
        context.window_manager.progress_begin(0, 100)
        context.window.cursor_modal_set('WAIT')
        context.window_manager.progress_update(50)

        try:
            result = apply_render_optimizer(context)
            mat_stats = result['mat_stats']
            outline_info = result['outline_info']

            report = (
                f"[{result['model_type']}] Toon-shaded {mat_stats['total']} materials "
                f"(textured: {mat_stats['textured']}, "
                f"color-fallback: {mat_stats['fallback_color']}, "
                f"alpha: {mat_stats['alpha']})"
            )
            if mat_stats.get('skipped'):
                report += f" | Skipped: {mat_stats['skipped']}"
            if mat_stats.get('fallback_meshes'):
                report += f" | No-material meshes: {mat_stats['fallback_meshes']}"
            if outline_info.get('enabled'):
                report += f" | Outline: {outline_info['strategy']}"
            report += f" | Tone: {result['tone']}, Brightness: {result['brightness']}"

            self.report({'INFO'}, report)
        except Exception as e:  # pylint: disable=broad-exception-caught
            context.window_manager.progress_end()
            context.window.cursor_modal_restore()
            Log.raise_error(str(e), type(e))

        context.window_manager.progress_end()
        context.window.cursor_modal_restore()
        return {'FINISHED'}


class RenderOptimizerResetOperator(Operator):  # pylint: disable=too-few-public-methods
    """Reset toon render changes"""
    bl_idname = "hbr_mmd.render_optimizer_reset"
    bl_label = "Reset"
    bl_description = (
        "Delete auto-created lights and outlines, reset World, disable Compositor "
        "(toon-shaded materials can be restored with Undo)"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, _context):
        """Reset all auto-created render objects."""
        try:
            reset_render_optimizer()
            self.report({'INFO'}, "Scene reset completed")
        except Exception as e:  # pylint: disable=broad-exception-caught
            Log.raise_error(str(e), type(e))
        return {'FINISHED'}
