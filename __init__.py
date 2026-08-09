# -*- coding: utf-8 -*-
# Copyright (c) 2025, https://github.com/skys-mission and Half-Bottled Reverie
"""
Blender Addon 入口
"""
from .src.core.addon import AddonManager
from .src.core.compat import ensure_supported_blender_version

# 注册插件信息
bl_info = {
    "name": "HBR MMD Tools",
    "author": "Half-Bottled Reverie, github.com/skys-mission",
    "version": (0, 5, 5),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > HBR MMD Tools",
    "description": "Blender add-on for MMD lip sync, random blinking, and related workflow tools.",
    "category": "3D View",
    "doc_url": "https://github.com/skys-mission/hbr_mmd_tools#readme",
    "tracker_url": "https://github.com/skys-mission/hbr_mmd_tools/issues"
}


def register():
    """
    注册插件。

    本函数在插件加载时被调用，用于设置插件名称并初始化插件。
    """
    ensure_supported_blender_version()
    AddonManager.set_addon_name(__name__)
    AddonManager.init_addon()


def unregister():
    """
    注销插件。

    本函数在插件卸载时被调用，用于卸载插件。
    """
    AddonManager.unload_addon()


if __name__ == "__main__":
    pass
