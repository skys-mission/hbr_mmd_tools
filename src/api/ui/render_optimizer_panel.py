# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — UI Panels
"""
import bpy  # pylint: disable=import-error


class RenderOptimizerPanel(bpy.types.Panel):  # pylint: disable=too-few-public-methods
    """主面板"""
    bl_label = "MMD Smart Toon Render (Experimental)"
    bl_idname = "OBJECT_PT_RENDER_OPTIMIZER"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HBR MMD Tools'
    bl_order = 4

    def draw(self, context):
        """Draw the main toon render panel."""
        layout = self.layout
        scene = context.scene

        layout.label(text="Select model, then apply (EEVEE only)", icon='INFO')

        layout.separator()

        # 卡通风格
        layout.prop(scene, "render_opt_style")

        # 描边
        layout.prop(scene, "render_opt_outline")
        if scene.render_opt_outline == 'SOLIDIFY':
            layout.prop(scene, "render_opt_outline_width")

        layout.separator()

        # 执行按钮
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator(
            "hbr_mmd.render_optimizer_apply",
            text="Apply Toon Render",
            icon="RENDER_STILL",
        )

        row = layout.row(align=True)
        row.operator("hbr_mmd.render_optimizer_reset", text="Reset", icon="TRASH")


class RenderOptimizerAdvancedPanel(bpy.types.Panel):  # pylint: disable=too-few-public-methods
    """高级参数面板"""
    bl_label = "Advanced"
    bl_idname = "OBJECT_PT_RENDER_OPTIMIZER_ADVANCED"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HBR MMD Tools'
    bl_parent_id = "OBJECT_PT_RENDER_OPTIMIZER"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """Draw the advanced toon render panel."""
        layout = self.layout
        scene = context.scene

        # 亮度倾向
        layout.prop(scene, "render_opt_brightness_override")

        layout.separator()

        # 合成器后期
        layout.prop(scene, "render_opt_use_compositor")
