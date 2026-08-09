# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — 灯光系统。

3点卡通布光：主光(SUN, 唯一投影) + 补光(AREA) + 轮廓光(AREA)。
卡通渲染以平色为主，灯光只负责产生分明的明暗分界，
因此面积光关闭阴影以保持 EEVEE 渲染性能。
"""

import bpy  # pylint: disable=import-error
from mathutils import Vector  # pylint: disable=import-error

from .presets import (
    LIGHT_KEY_NAME, LIGHT_FILL_NAME, LIGHT_RIM_NAME,
    LIGHT_KEY_ENERGY, LIGHT_FILL_ENERGY, LIGHT_RIM_ENERGY,
    LIGHT_KEY_COLOR, LIGHT_FILL_COLOR, LIGHT_RIM_COLOR,
    LIGHT_KEY_SUN_ANGLE,
)


def _resolve_key_color(tone):
    """根据色调解析主光颜色。"""
    if tone == 'cool':
        return (0.90, 0.94, 1.0)
    if tone == 'warm':
        return (1.0, 0.93, 0.84)
    return LIGHT_KEY_COLOR


def _create_sun(scene, name, energy, color):
    """创建太阳主光（唯一投影光源）。"""
    ld = bpy.data.lights.new(name, 'SUN')
    ld.energy = energy
    ld.color = color
    ld.angle = LIGHT_KEY_SUN_ANGLE
    obj = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(obj)
    return obj


def _create_area_light(scene, name, spec, target):
    """创建 AREA 灯光并使其 -Z 轴对准目标点。默认不投影以保证性能。

    spec: (loc, energy, color, size)
    """
    loc, energy, color, size = spec
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'DISK'
    ld.size = size
    ld.energy = energy
    ld.color = color
    if hasattr(ld, 'use_shadow'):
        ld.use_shadow = False
    obj = bpy.data.objects.new(name, ld)
    obj.location = loc
    scene.collection.objects.link(obj)

    direction = Vector(target) - obj.location
    if direction.length > 1e-6:
        obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return obj

def setup_lights(metrics, *, tone='neutral', brightness='medium'):
    """
    创建3点卡通布光。

    参数:
        metrics: (height, fx, fy, fz, cz, es)
        tone: 'cool' / 'warm' / 'neutral'
        brightness: 'light' / 'medium' / 'dark'，微调补光强度

    返回:
        dict 包含创建的灯光名
    """
    height, fx, fy, _fz, cz, es = metrics
    scene = bpy.context.scene
    target = (fx, fy, cz + height * 0.55)

    fill_mul = {'light': 0.8, 'medium': 1.0, 'dark': 1.25}.get(brightness, 1.0)

    key = _create_sun(scene, LIGHT_KEY_NAME, LIGHT_KEY_ENERGY, _resolve_key_color(tone))
    key.location = (fx + height * 1.2, fy - height * 1.0, cz + height * 1.6)
    key.rotation_euler = (0.9, 0.15, 0.55)

    _create_area_light(
        scene, LIGHT_FILL_NAME,
        ((fx - height * 1.4, fy - height * 0.9, cz + height * 0.9),
         LIGHT_FILL_ENERGY * fill_mul * es,
         LIGHT_FILL_COLOR,
         height * 1.8),
        target,
    )

    _create_area_light(
        scene, LIGHT_RIM_NAME,
        ((fx + height * 0.6, fy + height * 1.5, cz + height * 1.1),
         LIGHT_RIM_ENERGY * es,
         LIGHT_RIM_COLOR,
         height * 1.2),
        target,
    )

    return {
        'lights': [LIGHT_KEY_NAME, LIGHT_FILL_NAME, LIGHT_RIM_NAME],
        'tone': tone,
        'brightness': brightness,
    }
