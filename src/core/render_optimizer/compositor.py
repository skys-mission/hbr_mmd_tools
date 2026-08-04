# -*- coding: utf-8 -*-
# Copyright (c) 2025, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Render Optimizer — 合成器后期。
bloom + 暗角 + 对比度（激进模式 + 饱和度 + 锐化）。
"""

import bpy  # pylint: disable=import-error

from . import pipeline
from .presets import (
    BLOOM_STRENGTH, BLOOM_THRESHOLD, VIGNETTE_EDGE,
    TAA_SAMPLES, TAA_SAMPLES_AGGRESSIVE,
    CYCLES_SAMPLES, CYCLES_SAMPLES_AGGRESSIVE,
)


def _build_glare(nt, aggressive):
    """创建 Bloom Glare 节点并按版本设置其选项。"""
    glare = nt.nodes.new('CompositorNodeGlare')
    glare.location = (-300, 0)
    pipeline.set_node_option(glare, 'glare_type', ('Type',), 'BLOOM')
    pipeline.set_node_option(glare, 'quality', ('Quality',), 'HIGH')
    pipeline.set_node_option(
        glare, 'threshold', ('Threshold',),
        2.2 if aggressive else BLOOM_THRESHOLD,
    )
    # 5.0+ Size 改为 0-1 比例，之前为 0-9 的 2 的幂指数
    if pipeline.is_modern_compositor():
        size_value = 0.6 if aggressive else 0.5
    else:
        size_value = 7 if aggressive else 6
    pipeline.set_node_option(glare, 'size', ('Size',), size_value)
    pipeline.set_node_option(
        glare, 'mix', ('Strength', 'Mix'),
        0.10 if aggressive else BLOOM_STRENGTH,
    )
    return glare


def _build_vignette(nt, aggressive):
    """Create vignette mask and return the mask_ramp node."""
    mask = nt.nodes.new('CompositorNodeEllipseMask')
    mask.location = (-600, -300)
    size_socket = mask.inputs.get('Size')
    if size_socket is not None:
        size_socket.default_value = (0.58, 0.58)
    else:
        mask.mask_width = 0.58
        mask.mask_height = 0.58
    value_socket = mask.inputs.get('Value')
    if value_socket is not None:
        value_socket.default_value = 0.30

    vignette_val = 0.15 if aggressive else VIGNETTE_EDGE
    mask_ramp = pipeline.new_node(nt, 'CompositorNodeValToRGB', 'ShaderNodeValToRGB')
    mask_ramp.location = (-400, -300)
    mask_ramp.color_ramp.elements[0].position = 0.0
    mask_ramp.color_ramp.elements[0].color = (vignette_val, vignette_val, vignette_val, 1.0)
    mask_ramp.color_ramp.elements[1].position = 1.0
    mask_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    nt.links.new(mask.outputs['Mask'], mask_ramp.inputs['Fac'])
    return mask_ramp


def _mix_color_inputs(mix_node):
    """返回混合节点的两个颜色输入插槽（新旧节点标识符不同）。"""
    inputs = mix_node.inputs
    first = inputs.get('Image1') or inputs.get('Color1')
    second = inputs.get('Image2') or inputs.get('Color2')
    if first is None or second is None:
        return inputs[1], inputs[2]
    return first, second


def setup_compositor(aggressive=False, enabled=True):
    """
    设置 Compositor 后期节点树。

    参数:
        aggressive: 激进模式（更强效果）
        enabled: False 时关闭 Compositor
    """
    scene = bpy.context.scene

    if not enabled:
        pipeline.disable_compositor(scene)
        return

    nt = pipeline.ensure_compositor_tree(scene)
    nt.nodes.clear()

    rl = nt.nodes.new('CompositorNodeRLayers')
    rl.location = (-900, 0)

    # 基础对比度调整
    bright = nt.nodes.new('CompositorNodeBrightContrast')
    bright.location = (-600, 200)
    bright.inputs['Bright'].default_value = 0.02 if aggressive else 0.03
    bright.inputs['Contrast'].default_value = 0.38 if aggressive else 0.20

    # Bloom
    glare = _build_glare(nt, aggressive)

    # 饱和度与锐化（仅激进模式）
    last = glare
    if aggressive:
        sat = nt.nodes.new('CompositorNodeHueSat')
        sat.location = (0, 0)
        sat.inputs['Saturation'].default_value = 1.12
        nt.links.new(pipeline.image_output(last), sat.inputs['Image'])
        last = sat

        sharp = nt.nodes.new('CompositorNodeFilter')
        sharp.location = (200, 0)
        pipeline.set_node_option(sharp, 'filter_type', ('Type',), 'SHARPEN')
        nt.links.new(pipeline.image_output(last), sharp.inputs['Image'])
        last = sharp

    # 暗角
    mask_ramp = _build_vignette(nt, aggressive)

    # 混合暗角
    mix_v = pipeline.new_node(nt, 'CompositorNodeMixRGB', 'ShaderNodeMixRGB')
    mix_v.location = (600 if aggressive else 400, 0)
    mix_v.blend_type = 'MULTIPLY'
    mix_v.inputs[0].default_value = 1.0
    first_color, second_color = _mix_color_inputs(mix_v)

    # 节点连接
    nt.links.new(rl.outputs['Image'], bright.inputs['Image'])
    nt.links.new(pipeline.image_output(bright), glare.inputs['Image'])
    nt.links.new(pipeline.image_output(last), first_color)
    nt.links.new(pipeline.image_output(mask_ramp), second_color)
    nt.links.new(pipeline.image_output(mix_v), pipeline.append_output_socket(nt))


def setup_render(engine=None, aggressive=False):
    """
    设置渲染参数（不含相机）。

    参数:
        engine: 渲染引擎 ID，默认取当前版本对应的 EEVEE ID
        aggressive: 激进模式提升采样
    """
    scene = bpy.context.scene
    r = scene.render
    if engine is None:
        engine = pipeline.get_eevee_engine_id()
    r.engine = engine
    r.film_transparent = False

    if engine == pipeline.CYCLES_ENGINE_ID:
        scene.cycles.samples = (
            CYCLES_SAMPLES_AGGRESSIVE if aggressive else CYCLES_SAMPLES
        )
        scene.cycles.use_denoising = True
    else:
        e = scene.eevee
        e.taa_render_samples = (
            TAA_SAMPLES_AGGRESSIVE if aggressive else TAA_SAMPLES
        )
        e.use_raytracing = True
        e.use_shadows = True
        e.shadow_resolution_scale = 1.0
        # GTAO 选项在部分版本中不存在，仅在其可用时启用
        if hasattr(e, 'use_gtao'):
            e.use_gtao = True
            e.gtao_distance = 0.4
            e.gtao_quality = 0.5
        e.use_fast_gi = True

    v = scene.view_settings
    v.view_transform = 'AgX'
    v.look = 'AgX - Medium High Contrast'
    v.gamma = 1.0
