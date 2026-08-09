# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
VSE（视频序列编辑器）跨版本兼容工具。

Blender 4.4 将 ``bpy.types.Sequence`` 改名为 ``bpy.types.Strip``，
``SequenceEditor.sequences`` 改名为 ``SequenceEditor.strips``，
旧属性在 4.4/4.5 中保留但已废弃，并在 5.0 中移除。
本模块不导入 bpy，仅通过属性探测工作，因此可以脱离 Blender 直接单元测试。
"""


def get_top_level_strips(sequence_editor):
    """获取 VSE 顶层 strip 列表，无序列编辑器或取不到集合时返回空列表。"""
    if sequence_editor is None:
        return []
    strips = getattr(sequence_editor, "strips", None)  # Blender 4.4+
    if strips is None:
        strips = getattr(sequence_editor, "sequences", None)  # Blender < 4.4
    if strips is None:
        return []
    return list(strips)


def get_scene_strips(scene):
    """获取场景 VSE 顶层 strip 列表。"""
    return get_top_level_strips(getattr(scene, "sequence_editor", None))


def get_strip_audio_filepath(strip):
    """返回 SOUND/MOVIE strip 的音频文件路径，非音频 strip 或无路径时返回 None。"""
    if getattr(strip, "type", None) not in ('SOUND', 'MOVIE'):
        return None
    return getattr(getattr(strip, "sound", None), "filepath", None)


def find_strip_by_name(strips, name):
    """按名称在 strip 列表中查找。

    兼容 v0.5.1 及更早版本保存的 ``channel:name`` 形式：
    仅在去掉通道前缀后能唯一匹配时才回退，避免同名 strip 被误选。
    """
    if not name:
        return None
    for strip in strips:
        if getattr(strip, "name", None) == name:
            return strip
    if ":" in name:
        legacy_name = name.split(":", 1)[1]
        matches = [s for s in strips if getattr(s, "name", None) == legacy_name]
        if len(matches) == 1:
            return matches[0]
    return None
