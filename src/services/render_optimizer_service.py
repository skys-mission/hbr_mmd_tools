# -*- coding: utf-8 -*-
# Copyright (c) 2025, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD 渲染优化服务层。
组合调用各核心模块完成一键渲染优化。
"""

from ..core.render_optimizer.utils import (
    collect_objects_from_selection,
    find_primary_mesh,
    find_armature_for_meshes,
    calc_character_metrics,
    analyze_model_tone,
    cleanup_auto_objects,
)
from ..core.render_optimizer import pipeline
from ..core.render_optimizer.material import enhance_materials
from ..core.render_optimizer.lighting import setup_lights
from ..core.render_optimizer.world_env import setup_world, reset_world_default
from ..core.render_optimizer.compositor import setup_compositor, setup_render
from ..core.render_optimizer.outline import setup_outline, disable_freestyle
from ..util.logger import Log


def _resolve_preset(preset):
    """解析渲染预设返回配置字典。"""
    return {
        'is_pbr': preset in ('PBR', 'PBR_AGGRESSIVE'),
        'aggressive': preset == 'PBR_AGGRESSIVE',
        'is_npr': preset == 'NPR',
    }


def _resolve_tone_brightness(scene, meshes):
    """分析模型色调并应用用户覆盖。"""
    tone, brightness = analyze_model_tone(meshes)
    if scene.render_opt_brightness_override != 'AUTO':
        brightness = scene.render_opt_brightness_override.lower()
    return tone, brightness


def _resolve_outline_strategy(scene, is_npr):
    """根据 NPR/PBR 模式解析描边策略。"""
    strategy = scene.render_opt_outline_strategy
    if is_npr and strategy == 'freestyle_auto':
        return strategy
    if not is_npr and strategy != 'none':
        return 'none'
    return strategy


def _resolve_engine(scene):
    """根据场景设置解析渲染引擎。"""
    if scene.render_opt_engine == 'EEVEE':
        return pipeline.get_eevee_engine_id()
    return pipeline.CYCLES_ENGINE_ID


def _apply_exposure(scene, brightness, aggressive):
    """根据亮度自适应调整曝光。"""
    if brightness == 'light':
        scene.view_settings.exposure = -0.30 if aggressive else -0.25
    elif brightness == 'dark':
        scene.view_settings.exposure = 0.10 if aggressive else 0.15
    else:
        scene.view_settings.exposure = -0.05 if aggressive else 0.0


def apply_render_optimizer(context):
    """
    执行 MMD 渲染优化。
    根据当前场景属性自动配置材质、灯光、World、合成器和渲染参数。
    """
    scene = context.scene

    meshes, armatures = collect_objects_from_selection(context)
    if not meshes:
        raise ValueError("No valid mesh found in the selected object tree.")

    primary_mesh = find_primary_mesh(meshes)
    arm = find_armature_for_meshes(meshes, armatures)
    metrics = calc_character_metrics(
        context.active_object or meshes[0], arm, primary_mesh,
    )

    tone, brightness = _resolve_tone_brightness(scene, meshes)
    cfg = _resolve_preset(scene.render_opt_preset)

    cleanup_auto_objects()

    mat_stats = (
        enhance_materials([primary_mesh], aggressive=cfg['aggressive'])
        if cfg['is_pbr'] and primary_mesh else
        {'total': 0, 'classified': 0, 'fallback': 0}
    )

    light_info = setup_lights(
        metrics, aggressive=cfg['aggressive'], tone=tone,
    )

    setup_world(brightness=brightness, tone=tone)
    setup_compositor(
        aggressive=cfg['aggressive'], enabled=scene.render_opt_use_compositor,
    )

    outline_strategy = _resolve_outline_strategy(scene, cfg['is_npr'])
    outline_info = setup_outline(primary_mesh, strategy=outline_strategy)

    setup_render(engine=_resolve_engine(scene), aggressive=cfg['aggressive'])
    _apply_exposure(scene, brightness, cfg['aggressive'])

    Log.info(
        f"Render optimizer applied: preset={scene.render_opt_preset}, "
        f"materials={mat_stats['total']}, "
        f"classified={mat_stats['classified']}, "
        f"tone={tone}, brightness={brightness}"
    )

    return {
        'preset': scene.render_opt_preset,
        'mat_stats': mat_stats,
        'light_info': light_info,
        'outline_info': outline_info,
        'tone': tone,
        'brightness': brightness,
    }


def reset_render_optimizer():
    """
    重置渲染优化器创建的所有自动对象和设置。
    """
    import bpy  # pylint: disable=import-outside-toplevel,import-error

    scene = bpy.context.scene

    cleanup_auto_objects()
    disable_freestyle(scene)

    # 关闭 Compositor
    pipeline.disable_compositor(scene)

    reset_world_default(scene)

    # 恢复默认渲染设置
    scene.view_settings.exposure = 0.0
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'

    Log.info("Render optimizer reset completed.")
