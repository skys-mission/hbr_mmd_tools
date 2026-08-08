# -*- coding: utf-8 -*-
# Copyright (c) 2025, https://github.com/skys-mission and Half-Bottled Reverie
"""
初始化代码
"""
from ..api.bridge import Bridge
from ..api.handler.camera import CameraApplySettingsOperator
from ..api.handler.render_optimizer import (
    RenderOptimizerApplyOperator,
    RenderOptimizerResetOperator,
)
from ..api.scene.camera_set_scene import CameraSettingsProperties
from ..api.scene.mmd_set import (lips_audio_path, lips_audio_source, lips_timeline_audio_strip,
                                 lips_start_frame, lips_generation_preset,
                                 lips_use_custom_tuning, buffer_frame,
                                 approach_speed, db_threshold, \
                                 rms_threshold, max_morph_value,
                                 blink_start_frame, blink_end_frame,
                                 blinking_frequency, blinking_wave_ratio,
                                 blinking_half_ratio,
                                 lips_config_selection, lips_custom_config_path,
                                 blink_config_selection, blink_custom_config_path)
from ..api.scene.render_preset_scene import (
    resolution_preset, aspect_ratio_preset, orientation_preset)
from ..api.scene.render_optimizer_scene import (
    render_opt_style,
    render_opt_outline,
    render_opt_outline_width,
    render_opt_use_compositor,
    render_opt_brightness_override,
)
from ..api.ui.about import AboutPanel
from ..api.ui.camera_set_panel import CameraSetPanel
from ..api.ui.mmd_blink_panel import (
    RandomBlinkConfigPanel,
    RandomBlinkOperator,
    RandomBlinkPanel,
    ImportBlinkConfigOperator,
    OpenBlinkConfigFolderOperator,
)
from ..api.ui.mmd_set_panel import (
    MMDHelperPanel,
    MMDLipConfigPanel,
    MMDLipAdvancedPanel,
    GenLipsOperator,
    ImportLipsConfigOperator,
    OpenLipsConfigFolderOperator,
)
from ..api.ui.render_preset_panel import RenderPresetPanel
from ..api.ui.render_optimizer_panel import (
    RenderOptimizerPanel,
    RenderOptimizerAdvancedPanel,
)


class AddonManager:
    """
    插件管理器类。
    负责插件的初始化和卸载。
    """
    _addon_name = "hbr_mmd_tools"
    # 定义bl_classes元组，包含所有需要注册的类
    _bl_classes = (
        # 1.Properties(属性定义)
        # 2.Operator(操作器)
        # 3.Menu(菜单)
        # 4.Panel(面板)
        CameraSettingsProperties,
        CameraApplySettingsOperator,
        GenLipsOperator,
        RandomBlinkOperator,
        ImportBlinkConfigOperator,
        OpenBlinkConfigFolderOperator,
        ImportLipsConfigOperator,
        OpenLipsConfigFolderOperator,
        RenderPresetPanel,
        CameraSetPanel,
        MMDHelperPanel,
        MMDLipConfigPanel,
        MMDLipAdvancedPanel,
        RandomBlinkPanel,
        RandomBlinkConfigPanel,
        AboutPanel,
        RenderOptimizerApplyOperator,
        RenderOptimizerResetOperator,
        RenderOptimizerPanel,
        RenderOptimizerAdvancedPanel,
    )

    _scene_property_names = (
        "resolution_preset",
        "aspect_ratio_preset",
        "orientation_preset",
        "camera_settings",
        "lips_audio_path",
        "lips_audio_source",
        "lips_timeline_audio_strip",
        "lips_config_selection",
        "lips_custom_config_path",
        "lips_start_frame",
        "lips_generation_preset",
        "lips_use_custom_tuning",
        "buffer_frame",
        "approach_speed",
        "db_threshold",
        "rms_threshold",
        "max_morph_value",
        "blink_config_selection",
        "blink_custom_config_path",
        "blink_start_frame",
        "blink_end_frame",
        "blinking_frequency",
        "blinking_wave_ratio",
        "blinking_half_ratio",
        "render_opt_style",
        "render_opt_outline",
        "render_opt_outline_width",
        "render_opt_use_compositor",
        "render_opt_brightness_override",
    )

    @staticmethod
    def init_addon():
        """
        初始化插件时调用此函数。
        它负责注册翻译、类和场景属性。
        """

        # 翻译
        Bridge.App.register_translations(
            AddonManager._addon_name
        )

        # Classes
        AddonManager.register_classes()
        # Scene
        AddonManager.register_scene()

    @staticmethod
    def unload_addon():
        """
        卸载插件时调用此函数。
        它负责注销场景属性、类和翻译。
        """

        # Scene
        AddonManager.unregister_scene()
        # Classes
        AddonManager.unregister_classes()
        # 翻译
        Bridge.App.unregister_translations(AddonManager._addon_name)

    @staticmethod
    def register_scene():
        """
        注册场景属性。
        这些属性包括渲染预设、摄像机设置等。
        """
        scene = Bridge.Types.get_scene()
        pp = Bridge.Props.get_pointer_property()

        # Render Preset 相关
        scene.resolution_preset = resolution_preset
        scene.aspect_ratio_preset = aspect_ratio_preset
        scene.orientation_preset = orientation_preset

        # 摄像机预设相关
        scene.camera_settings = pp(type=CameraSettingsProperties)

        # MMD
        scene.lips_audio_path = lips_audio_path
        scene.lips_audio_source = lips_audio_source
        scene.lips_timeline_audio_strip = lips_timeline_audio_strip
        scene.lips_config_selection = lips_config_selection
        scene.lips_custom_config_path = lips_custom_config_path
        scene.lips_start_frame = lips_start_frame
        scene.lips_generation_preset = lips_generation_preset
        scene.lips_use_custom_tuning = lips_use_custom_tuning
        scene.buffer_frame = buffer_frame
        scene.approach_speed = approach_speed
        scene.db_threshold = db_threshold
        scene.rms_threshold = rms_threshold
        scene.max_morph_value = max_morph_value

        # MMD wink
        scene.blink_config_selection = blink_config_selection
        scene.blink_custom_config_path = blink_custom_config_path
        scene.blink_start_frame = blink_start_frame
        scene.blink_end_frame = blink_end_frame
        scene.blinking_frequency = blinking_frequency
        scene.blinking_wave_ratio = blinking_wave_ratio
        scene.blinking_half_ratio = blinking_half_ratio

        # Render Optimizer (Smart Toon)
        scene.render_opt_style = render_opt_style
        scene.render_opt_outline = render_opt_outline
        scene.render_opt_outline_width = render_opt_outline_width
        scene.render_opt_use_compositor = render_opt_use_compositor
        scene.render_opt_brightness_override = render_opt_brightness_override

    @staticmethod
    def unregister_scene():
        """
        注销场景属性。
        这些属性包括渲染预设、摄像机设置等。
        """
        scene = Bridge.Types.get_scene()
        for prop_name in AddonManager._scene_property_names:
            if hasattr(scene, prop_name):
                delattr(scene, prop_name)

    @staticmethod
    def register_classes():
        """
        注册所有bl_classes中的类。
        """
        for cls in AddonManager._bl_classes:
            Bridge.Utils.register_class(cls)

    @staticmethod
    def unregister_classes():
        """
        注销所有bl_classes中的类。
        逆序注销以避免潜在的依赖问题。
        """
        for cls in reversed(AddonManager._bl_classes):
            Bridge.Utils.unregister_class(cls)

    @staticmethod
    def set_addon_name(name):
        """
        ...
        """
        AddonManager._addon_name = name
