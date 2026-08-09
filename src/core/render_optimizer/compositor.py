# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — 合成器后期与渲染参数。

轻量后期：轻微对比度 + 低质量 Bloom。
EEVEE 渲染参数以性能为先：保守采样、关闭光线追踪。
"""

import bpy  # pylint: disable=import-error

from . import pipeline
from .presets import (
    BLOOM_THRESHOLD, BLOOM_MIX, BLOOM_SIZE_LEGACY, BLOOM_SIZE_MODERN,
    BRIGHT_CONTRAST, EEVEE_RENDER_SAMPLES,
)


def _build_glare(nt):
    """创建低质量 Bloom Glare 节点并按版本设置其选项。"""
    glare = nt.nodes.new('CompositorNodeGlare')
    glare.location = (-200, 0)
    pipeline.set_node_option(glare, 'glare_type', ('Type',), 'BLOOM')
    # 低质量：卡通画面只需要轻微泛光，避免性能损耗
    pipeline.set_node_option(glare, 'quality', ('Quality',), 'LOW')
    pipeline.set_node_option(glare, 'threshold', ('Threshold',), BLOOM_THRESHOLD)
    # Glare 选项在 4.5+ 迁移为输入插槽（Size 为 0-1 比例），
    # 4.2-4.4 为节点属性（Size 是 2 的幂指数）；按插槽存在与否做特征检测，
    # 比版本号判定更准（4.5 是旧合成器节点树，但已是新 Glare 节点）
    size_value = (BLOOM_SIZE_MODERN if glare.inputs.get('Size') is not None
                  else BLOOM_SIZE_LEGACY)
    pipeline.set_node_option(glare, 'size', ('Size',), size_value)
    pipeline.set_node_option(glare, 'mix', ('Strength', 'Mix'), BLOOM_MIX)
    return glare


def setup_compositor(enabled=True):
    """
    设置轻量 Compositor 后期节点树。

    参数:
        enabled: False 时关闭 Compositor
    """
    scene = bpy.context.scene

    if not enabled:
        pipeline.disable_compositor(scene)
        return

    nt = pipeline.ensure_compositor_tree(scene)
    nt.nodes.clear()

    rl = nt.nodes.new('CompositorNodeRLayers')
    rl.location = (-500, 0)

    bright = nt.nodes.new('CompositorNodeBrightContrast')
    bright.location = (-300, 0)
    bright.inputs['Bright'].default_value = BRIGHT_CONTRAST[0]
    bright.inputs['Contrast'].default_value = BRIGHT_CONTRAST[1]

    glare = _build_glare(nt)

    nt.links.new(rl.outputs['Image'], bright.inputs['Image'])
    nt.links.new(pipeline.image_output(bright), glare.inputs['Image'])
    nt.links.new(pipeline.image_output(glare), pipeline.append_output_socket(nt))


def setup_render():
    """
    设置 EEVEE 渲染参数（性能优先）与色彩管理。

    - 引擎按版本解析 EEVEE ID
    - 保守采样，关闭光线追踪（卡通渲染不需要）
    - Standard 视图变换保持贴图原色（经典日式动画观感）
    """
    scene = bpy.context.scene
    scene.render.engine = pipeline.get_eevee_engine_id()
    scene.render.film_transparent = False

    eevee = getattr(scene, 'eevee', None)
    if eevee is not None:
        if hasattr(eevee, 'taa_render_samples'):
            eevee.taa_render_samples = EEVEE_RENDER_SAMPLES
        if hasattr(eevee, 'use_raytracing'):
            eevee.use_raytracing = False
        if hasattr(eevee, 'use_shadows'):
            eevee.use_shadows = True

    view = scene.view_settings
    try:
        view.view_transform = 'Standard'
        view.look = 'None'
    except (TypeError, ValueError):
        # OCIO 配置差异时保持现状，不影响主流程
        pass
    view.gamma = 1.0
