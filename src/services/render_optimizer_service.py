# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD 智能3渲2渲染服务层。

一键卡通渲染编排：模型类型识别 → 材质卡通化 → 描边 → 布光 →
World → 轻量后期。仅使用 EEVEE，性能优先。
"""

from ..core.render_optimizer.presets import detect_model_type
from ..core.render_optimizer.utils import (
    collect_objects_from_selection,
    find_primary_mesh,
    find_armature_for_meshes,
    calc_character_metrics,
    analyze_model_tone,
    scan_model_features,
    cleanup_auto_objects,
)
from ..core.render_optimizer.toon_material import (
    convert_meshes_to_toon,
    ensure_fallback_material,
)
from ..core.render_optimizer.lighting import setup_lights
from ..core.render_optimizer.world_env import setup_world, reset_world_default
from ..core.render_optimizer.compositor import setup_compositor, setup_render
from ..core.render_optimizer.outline import setup_outline, disable_freestyle
from ..core.render_optimizer import pipeline
from ..util.logger import Log


def _resolve_brightness(scene, meshes):
    """分析模型明暗并应用用户覆盖。"""
    tone, brightness = analyze_model_tone(meshes)
    if scene.render_opt_brightness_override != 'AUTO':
        brightness = scene.render_opt_brightness_override.lower()
    return tone, brightness


def apply_render_optimizer(context):
    """
    执行一键智能3渲2渲染配置。

    根据选中的模型自动完成：卡通材质转换、描边、3点布光、
    World 背景与轻量合成器后期。仅使用 EEVEE 渲染器。
    """
    scene = context.scene

    meshes, armatures = collect_objects_from_selection(context)
    if not meshes:
        raise ValueError("No valid mesh found in the selected object tree.")

    features = scan_model_features(meshes)
    model_type = detect_model_type(
        features['has_mmd_shader'],
        features['has_mtoon_group'],
        features['has_vrm_props'],
    )

    primary_mesh = find_primary_mesh(meshes)
    arm = find_armature_for_meshes(meshes, armatures)
    metrics = calc_character_metrics(
        context.active_object or meshes[0], arm, primary_mesh,
    )

    tone, brightness = _resolve_brightness(scene, meshes)

    # 幂等：先清理上一次的自动对象与描边
    cleanup_auto_objects()

    # 材质卡通化（含无材质 mesh 的兜底）
    fallback_mats = ensure_fallback_material(meshes)
    mat_stats = convert_meshes_to_toon(meshes, scene.render_opt_style)
    mat_stats['fallback_meshes'] = len(fallback_mats)

    # 描边
    outline_info = setup_outline(
        meshes,
        strategy=scene.render_opt_outline.lower(),
        width_factor=scene.render_opt_outline_width,
        height=metrics[0],
    )

    # 灯光 / World / 后期 / 渲染参数
    light_info = setup_lights(metrics, tone=tone, brightness=brightness)
    setup_world(brightness=brightness)
    setup_compositor(enabled=scene.render_opt_use_compositor)
    setup_render()

    Log.info(
        f"Toon render applied: type={model_type}, style={scene.render_opt_style}, "
        f"materials={mat_stats['total']}, textured={mat_stats['textured']}, "
        f"fallback={mat_stats['fallback_color']}, outline={outline_info}, "
        f"tone={tone}, brightness={brightness}"
    )

    return {
        'model_type': model_type,
        'style': scene.render_opt_style,
        'mat_stats': mat_stats,
        'light_info': light_info,
        'outline_info': outline_info,
        'tone': tone,
        'brightness': brightness,
    }


def reset_render_optimizer():
    """
    重置渲染优化创建的所有自动对象和设置。

    注意：已卡通化的材质不会还原（可通过撤销 Ctrl+Z 恢复）。
    """
    import bpy  # pylint: disable=import-outside-toplevel,import-error

    scene = bpy.context.scene

    cleanup_auto_objects()
    disable_freestyle(scene)

    # 关闭 Compositor
    pipeline.disable_compositor(scene)

    reset_world_default(scene)

    # 恢复默认色彩管理
    scene.view_settings.exposure = 0.0
    try:
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except (TypeError, ValueError):
        pass

    Log.info("Toon render reset completed.")
