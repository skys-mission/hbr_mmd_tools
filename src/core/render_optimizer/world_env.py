# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — World 环境。

卡通渲染不使用世界光照（EEVEE 无 GI 时世界只作为背景可见），
因此仅设置按模型明暗自适应的纯色背景，开销为零。
"""

import bpy  # pylint: disable=import-error

from .presets import WORLD_COLORS, WORLD_STRENGTH


def setup_world(brightness='medium'):
    """
    设置纯色 World 背景。

    参数:
        brightness: 'light' / 'medium' / 'dark'
    """
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()

    out = wnt.nodes.new('ShaderNodeOutputWorld')
    out.location = (200, 0)
    bg = wnt.nodes.new('ShaderNodeBackground')
    bg.location = (0, 0)
    bg.inputs['Color'].default_value = WORLD_COLORS.get(
        brightness, WORLD_COLORS['medium'],
    )
    bg.inputs['Strength'].default_value = WORLD_STRENGTH
    wnt.links.new(bg.outputs['Background'], out.inputs['Surface'])


def reset_world_default(scene):
    """恢复 World 为简单的深色默认背景。"""
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    wnt = world.node_tree
    wnt.nodes.clear()
    out = wnt.nodes.new('ShaderNodeOutputWorld')
    out.location = (200, 0)
    bg = wnt.nodes.new('ShaderNodeBackground')
    bg.location = (0, 0)
    bg.inputs['Color'].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs['Strength'].default_value = 0.3
    wnt.links.new(bg.outputs['Background'], out.inputs['Surface'])
