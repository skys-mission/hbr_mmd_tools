# -*- coding: utf-8 -*-
# Copyright (c) 2024, https://github.com/skys-mission and Half-Bottled Reverie
# pylint: disable=R0801
"""
MMD面板
"""
import bpy  # pylint: disable=import-error

from ...services.lip_sync_service import generate_lip_sync, _find_timeline_audio_strip
from ...util.logger import Log
from .config_ops import import_user_config, open_user_config_folder


# 定义一个Blender的面板类，用于在UI中显示渲染预设选项
class MMDHelperPanel(bpy.types.Panel):  # pylint: disable=too-few-public-methods
    """
    渲染预设面板
    """
    # 面板的标题
    bl_label = "MMD Lip Gen"
    # 面板的唯一标识符
    bl_idname = "OBJECT_PT_MMD_Helper"
    # 面板显示的空间类型
    bl_space_type = 'VIEW_3D'
    # 面板显示的区域类型
    bl_region_type = 'UI'
    # 面板显示的类别，用于在UI中分组面板
    bl_category = 'HBR MMD Tools'
    # 面板的显示顺序
    bl_order = 3

    # 绘制面板中的UI元素
    def draw(self, context):
        """
         在给定的上下文中绘制UI元素。

         参数:
         - context: 当前的上下文对象，包含了关于当前Blender环境的信息。

         此函数负责在UI中添加与场景相关的属性控件，以允许用户编辑场景的属性。
         """
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "lips_audio_source")

        if scene.lips_audio_source == 'file':
            layout.prop(scene, "lips_audio_path")
            layout.prop(scene, "lips_start_frame")
        else:
            layout.prop(scene, "lips_timeline_audio_strip")
            try:
                strip = _find_timeline_audio_strip(scene)
            except Exception as e:  # pylint: disable=broad-exception-caught
                # 枚举读取等异常不能中断面板绘制，否则预设和生成按钮会一起消失
                Log.warning(f"Failed to resolve timeline audio strip: {e}")
                strip = None
            if strip is not None:
                layout.label(
                    text=f"Audio starts at frame {int(strip.frame_final_start)}",
                    icon='INFO',
                )
            else:
                layout.label(text="No audio strip selected", icon='ERROR')
            start_row = layout.row()
            # 时间线模式下生成时会锁定为音频片段的起始帧，仅在无片段时可编辑
            start_row.enabled = strip is None
            start_row.prop(scene, "lips_start_frame")

        layout.prop(scene, "lips_generation_preset")

        layout.operator("mmd.gen_lips", text="Generate Lip Sync")


class MMDLipAdvancedPanel(bpy.types.Panel):  # pylint: disable=too-few-public-methods
    """口型高级调参面板"""
    bl_label = "Advanced"
    bl_idname = "OBJECT_PT_MMD_Lip_Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HBR MMD Tools'
    bl_parent_id = "OBJECT_PT_MMD_Helper"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """绘制高级口型参数。"""
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "lips_use_custom_tuning")
        if not scene.lips_use_custom_tuning:
            layout.label(text="Using preset tuning", icon='INFO')
            return

        layout.prop(scene, "db_threshold")
        layout.prop(scene, "rms_threshold")
        layout.prop(scene, "buffer_frame")
        layout.prop(scene, "approach_speed")
        layout.prop(scene, "max_morph_value")


class MMDLipConfigPanel(bpy.types.Panel):  # pylint: disable=too-few-public-methods
    """
    口型配置面板
    """
    bl_label = "Config"
    bl_idname = "OBJECT_PT_MMD_Lip_Config"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HBR MMD Tools'
    bl_parent_id = "OBJECT_PT_MMD_Helper"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """
        ...
        """
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.prop(scene, "lips_config_selection", text="Config")

        row = layout.row()
        row.prop(scene, "lips_custom_config_path", text="Custom Config")
        row.operator("mmd.import_lips_config", text="Apply", icon='CHECKMARK')

        row = layout.row()
        row.operator("mmd.open_lips_config_folder", text="Open Config Folder", icon='FILE_FOLDER')


class ImportLipsConfigOperator(bpy.types.Operator):  # pylint: disable=too-few-public-methods
    """导入口型配置操作器"""
    bl_idname = "mmd.import_lips_config"
    bl_label = "Import Lip Sync Config"
    bl_description = "Import custom lip sync configuration"

    def execute(self, context):
        """执行导入配置"""
        return import_user_config(
            self,
            context,
            config_type='lip_sync',
            source_path_attr='lips_custom_config_path',
            selection_attr='lips_config_selection',
        )


class OpenLipsConfigFolderOperator(bpy.types.Operator):  # pylint: disable=too-few-public-methods
    """打开口型配置文件夹操作器"""
    bl_idname = "mmd.open_lips_config_folder"
    bl_label = "Open Lip Sync Config Folder"
    bl_description = "Open the lip sync configuration folder"

    def execute(self, _context):
        """执行打开文件夹"""
        return open_user_config_folder(
            self,
            config_type='lip_sync',
            success_message_prefix="Opened lip sync config folder",
        )


class GenLipsOperator(bpy.types.Operator):  # pylint: disable=too-few-public-methods
    """
    ...
    """
    bl_idname = "mmd.gen_lips"
    bl_label = "Generate Lip Sync"
    bl_description = "Generate lip sync keyframes for the selected meshes"

    def execute(self, context):
        """
        ...
        :param context:
        :return:
        """
        context.window_manager.progress_begin(0, 100)
        context.window.cursor_modal_set('WAIT')
        context.window_manager.progress_update(98)

        try:
            generate_lip_sync(context)
        except Exception as e:  # pylint: disable=broad-exception-caught
            context.window_manager.progress_end()
            context.window.cursor_modal_restore()
            Log.raise_error(e, Exception)

        context.window_manager.progress_end()
        context.window.cursor_modal_restore()
        return {'FINISHED'}
