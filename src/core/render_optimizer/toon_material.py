# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — 材质卡通化转换。

将任意来源（mmd_tools PMX / VRM MToon / 通用 Principled）的材质重建为 EEVEE 卡通着色。

受光材质（不透明）：
    基础色(贴图或纯色) → Principled(纯漫射) → Shader to RGB
    → ColorRamp(常量阶调) → 与基础色相乘 → Emission 输出

局部透明材质（蕾丝/发梢/薄纱等，贴图小面积透明）：
    基础色 → Principled(纯漫射，Alpha=贴图Alpha×材质Alpha) 直接输出，
    BLENDED 前向透明。保留光照层次但不含 Shader to RGB。
    （4.5 实测：DITHERED 哈希透明在部分模型上会整体失效按不透明渲染，
    BLENDED 可靠且不破坏身后 S2RGB 表面的光照。）

叠层/贴花材质（恒定 alpha<1 或大面积透明，如腮红、目影、表情贴片）：
    基础色 → Emission 直接输出（平涂贴花，不参与光照），
    Alpha = 贴图 Alpha × 材质 Alpha，与 Transparent 混合（BLENDED）。

注意：EEVEE 中含 Shader to RGB 的透明材质会清零其身后 S2RGB 表面的
光照求值（4.5 实测：全身薄纱壳材质让身后皮肤渲染成纯黑），因此
任何含透明的材质都不得使用 S2RGB 结构（presets.resolve_render_path）。
转换路径记录在材质自定义属性 hbr_toon_path 中，供描边排除贴花面。

鲁棒性：贴图缺失时回退到漫射纯色；自动识别并保留有效的 Alpha 通道。
"""

import os

import bpy  # pylint: disable=import-error

from .presets import (
    RENDER_PATH_DECAL, RENDER_PATH_LIT_ALPHA, RENDER_PATH_PROP,
    classify_material, resolve_ramp_stops, resolve_render_path,
)
from .utils import iter_unique_materials


def is_image_usable(img):
    """
    判断图像数据块是否可用。

    mmd_tools 对缺失贴图会创建 1x1 占位图（has_data=False），
    因此同时检查像素尺寸与磁盘文件是否存在。
    """
    if img is None:
        return False
    if img.size[0] > 1 and img.size[1] > 1:
        return True
    if img.has_data:
        return True
    if img.source == 'FILE' and img.filepath:
        return os.path.exists(bpy.path.abspath(img.filepath))
    return False


def _image_has_alpha(img):
    """图像是否带 Alpha 通道。"""
    return img is not None and getattr(img, 'depth', 0) in (32, 64, 128)


# 同一张贴图常被多个材质引用（如 MMD 的衣/颜整图），采样结果按图缓存，
# 每次 convert_meshes_to_toon 调用前清空
_ALPHA_SAMPLE_CACHE = {}


def _sample_image_alpha(img):
    """
    稀疏采样贴图 Alpha 通道，返回 alpha < 0.995 的采样点占比。

    部分模型的贴图（如 4K 细节图）虽带 Alpha 通道但内容全为 1，
    不应触发透明混合；采样失败时保守按全透明处理（返回 1.0）。

    性能注意：pixels 逐点 RNA 访问极慢（实测约 17ms/次），全量
    foreach_get 对 4K/8K 贴图又会产生数百 MB~GB 级临时数组；
    切片读取是 C 速度，因此按「均匀分布的整行扫描线」采样——
    对 UV 整图集（透明区域空间集中）比连续块采样可靠。
    """
    try:
        width, height = img.size
        total = width * height
        if total <= 0:
            return 1.0
        key = (img.name_full, width, height)
        if key in _ALPHA_SAMPLE_CACHE:
            return _ALPHA_SAMPLE_CACHE[key]

        pixels = img.pixels
        row_floats = width * 4
        rows = min(height, 32)
        hits = 0
        count = 0
        for r in range(rows):
            y = (r * height) // rows
            start = y * row_floats
            buf = pixels[start:start + row_floats]
            for a in buf[3::4]:
                if a < 0.995:
                    hits += 1
                count += 1
        fraction = hits / count if count else 1.0
        _ALPHA_SAMPLE_CACHE[key] = fraction
        return fraction
    except Exception:  # pylint: disable=broad-exception-caught
        return 1.0


def _find_upstream_image(socket, _depth=0):
    """沿链接向上游查找第一个图像纹理节点（限两层，避免误入复杂节点组）。"""
    if socket is None or not socket.is_linked or _depth > 2:
        return None
    for link in socket.links:
        node = link.from_node
        if node.bl_idname == 'ShaderNodeTexImage':
            return node
        for inp in node.inputs:
            found = _find_upstream_image(inp, _depth + 1)
            if found is not None:
                return found
    return None


def _extract_mmd_source(mat):
    """从 mmd_tools 材质提取基础色来源。找不到 mmd_shader 时返回 None。"""
    shader = None
    base_tex = None
    for node in mat.node_tree.nodes:
        if node.name == 'mmd_shader':
            shader = node
        elif node.name == 'mmd_base_tex':
            base_tex = node

    if shader is None and base_tex is None:
        return None

    image = None
    if base_tex is not None and is_image_usable(base_tex.image):
        image = base_tex.image

    fallback = (0.8, 0.8, 0.8, 1.0)
    alpha = 1.0
    if shader is not None:
        diffuse = shader.inputs.get('Diffuse Color')
        if diffuse is not None:
            fallback = tuple(diffuse.default_value)
        alpha_socket = shader.inputs.get('Alpha')
        if alpha_socket is not None and not alpha_socket.is_linked:
            alpha = float(alpha_socket.default_value)

    mmd_props = getattr(mat, 'mmd_material', None)
    if mmd_props is not None:
        try:
            alpha = min(alpha, float(mmd_props.alpha))
            if image is None and mmd_props.diffuse_color:
                fallback = (*tuple(mmd_props.diffuse_color), fallback[3])
        except (AttributeError, TypeError):
            pass

    return image, fallback, alpha


def _extract_principled_source(mat):
    """从 Principled BSDF 材质提取基础色来源。"""
    principled = None
    for node in mat.node_tree.nodes:
        if node.bl_idname == 'ShaderNodeBsdfPrincipled':
            principled = node
            break
    if principled is None:
        return None

    base = principled.inputs.get('Base Color')
    image = None
    if base is not None and base.is_linked:
        tex_node = _find_upstream_image(base)
        if tex_node is not None and is_image_usable(tex_node.image):
            image = tex_node.image

    fallback = (0.8, 0.8, 0.8, 1.0)
    if base is not None:
        fallback = tuple(base.default_value)

    alpha = 1.0
    alpha_socket = principled.inputs.get('Alpha')
    if alpha_socket is not None and not alpha_socket.is_linked:
        alpha = float(alpha_socket.default_value)

    return image, fallback, alpha


# 首次转换时把原始基础色来源存入材质自定义属性，重复 Apply
# （如切换风格后再次应用）时据此重建，保证贴花贴图与隐藏 alpha 不丢失
_SRC_IMAGE_PROP = 'hbr_toon_src_image'
_SRC_ALPHA_PROP = 'hbr_toon_src_alpha'
_SRC_FALLBACK_PROP = 'hbr_toon_src_fallback'


def extract_base_source(mat):
    """
    提取材质的基础色来源。

    返回 (image, fallback_rgba, alpha)：
        image: 可用的基础色贴图（bpy.types.Image）或 None
        fallback_rgba: 贴图缺失时使用的纯色
        alpha: 材质整体不透明度
    """
    if _SRC_IMAGE_PROP in mat:
        # 已转换过的材质：从自定义属性恢复原始来源（幂等）
        image_name = mat[_SRC_IMAGE_PROP]
        image = bpy.data.images.get(image_name) if image_name else None
        if image is not None and not is_image_usable(image):
            image = None
        fallback = tuple(mat.get(_SRC_FALLBACK_PROP, (0.8, 0.8, 0.8, 1.0)))
        alpha = float(mat.get(_SRC_ALPHA_PROP, 1.0))
        return image, fallback, alpha

    if mat.use_nodes:
        source = _extract_mmd_source(mat)
        if source is None:
            source = _extract_principled_source(mat)
        if source is not None:
            return source

    color = tuple(mat.diffuse_color) if hasattr(mat, 'diffuse_color') else (0.8, 0.8, 0.8, 1.0)
    return None, color, color[3] if len(color) > 3 else 1.0


def _set_principled_flat(bsdf):
    """将 Principled 设为纯漫射（无高光/透射/次表面），供 Shader to RGB 采样。"""
    flat_inputs = {
        'Roughness': 1.0,
        'Metallic': 0.0,
        'Specular IOR Level': 0.0,
        'Subsurface Weight': 0.0,
        'Transmission Weight': 0.0,
        'Coat Weight': 0.0,
        'Sheen Weight': 0.0,
        'Emission Strength': 0.0,
    }
    for name, value in flat_inputs.items():
        socket = bsdf.inputs.get(name)
        if socket is not None and not socket.is_linked:
            socket.default_value = value


def _apply_ramp_stops(ramp_node, stops):
    """按停靠点配置 ColorRamp（常量插值）。"""
    cr = ramp_node.color_ramp
    cr.interpolation = 'CONSTANT'
    while len(cr.elements) > 2:
        cr.elements.remove(cr.elements[-1])
    cr.elements[0].position = stops[0][0]
    cr.elements[0].color = (*stops[0][1], 1.0)
    cr.elements[1].position = stops[-1][0]
    cr.elements[1].color = (*stops[-1][1], 1.0)
    for pos, value in stops[1:-1]:
        element = cr.elements.new(pos)
        element.color = (*value, 1.0)


def _new_base_source_node(nt, image, fallback):
    """创建基础色来源节点：可用贴图或纯色 RGB。"""
    if image is not None:
        src = nt.nodes.new('ShaderNodeTexImage')
        src.image = image
    else:
        src = nt.nodes.new('ShaderNodeRGB')
        src.outputs[0].default_value = fallback
    return src


def _build_toon_tree(mat, image, fallback, category, style):
    """重建为受光卡通着色结构（仅用于不透明材质，绝不可引入透明）。"""
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    emission = nt.nodes.new('ShaderNodeEmission')
    emission.location = (380, 0)
    emission.inputs['Strength'].default_value = 1.0

    mult = nt.nodes.new('ShaderNodeMixRGB')
    mult.blend_type = 'MULTIPLY'
    mult.inputs['Fac'].default_value = 1.0
    mult.location = (160, 0)

    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.location = (-80, 120)
    _apply_ramp_stops(ramp, resolve_ramp_stops(category, style))

    shader_to_rgb = nt.nodes.new('ShaderNodeShaderToRGB')
    shader_to_rgb.location = (-280, 120)

    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (-500, 120)
    _set_principled_flat(bsdf)

    src = _new_base_source_node(nt, image, fallback)
    src.location = (-500, 400)

    nt.links.new(src.outputs[0], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs['BSDF'], shader_to_rgb.inputs['Shader'])
    nt.links.new(shader_to_rgb.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(src.outputs[0], mult.inputs[1])
    nt.links.new(ramp.outputs['Color'], mult.inputs[2])
    nt.links.new(mult.outputs['Color'], emission.inputs['Color'])
    nt.links.new(emission.outputs[0], out.inputs['Surface'])


def _build_principled_flat_tree(mat, image, fallback, alpha):
    """
    重建为扁平 Principled 结构（局部透明材质：蕾丝/发梢/薄纱等）。

    透明材质含 Shader to RGB 会破坏其身后 S2RGB 表面的光照求值，
    因此局部透明材质不能用卡通色阶结构；改用纯漫射 Principled
    保留光照层次，贴图 Alpha × 材质 Alpha 驱动 BLENDED 前向透明
    （DITHERED 哈希透明在部分模型上实测会失效按不透明渲染，BLENDED 可靠）。
    """
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (400, 0)

    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (120, 0)
    _set_principled_flat(bsdf)

    src = _new_base_source_node(nt, image, fallback)
    src.location = (-200, 120)
    nt.links.new(src.outputs[0], bsdf.inputs['Base Color'])

    if image is not None and _image_has_alpha(image):
        if alpha < 0.999:
            alpha_mult = nt.nodes.new('ShaderNodeMath')
            alpha_mult.operation = 'MULTIPLY'
            alpha_mult.location = (-200, -120)
            alpha_mult.inputs[1].default_value = alpha
            nt.links.new(src.outputs['Alpha'], alpha_mult.inputs[0])
            nt.links.new(alpha_mult.outputs[0], bsdf.inputs['Alpha'])
        else:
            nt.links.new(src.outputs['Alpha'], bsdf.inputs['Alpha'])
    elif alpha < 0.999:
        bsdf.inputs['Alpha'].default_value = alpha

    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])


def _build_decal_tree(mat, image, fallback, alpha):
    """
    重建为平涂贴花结构（半透明叠层：腮红/目影/表情贴片等）。

    不参与光照（贴花本就该平涂），且避免在透明材质中使用
    Shader to RGB —— 那会破坏其身后 S2RGB 表面的光照求值。
    """
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)

    emission = nt.nodes.new('ShaderNodeEmission')
    emission.location = (200, 0)
    emission.inputs['Strength'].default_value = 1.0

    src = _new_base_source_node(nt, image, fallback)
    src.location = (-200, 200)
    nt.links.new(src.outputs[0], emission.inputs['Color'])

    transparent = nt.nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (200, -160)
    mix_shader = nt.nodes.new('ShaderNodeMixShader')
    mix_shader.location = (420, -60)

    if image is not None and _image_has_alpha(image):
        # 贴图 Alpha × 材质 Alpha：MMD 叠层（如腮红 颜+）常由
        # 材质形态键控制，静态 alpha=0 时必须保持不可见
        alpha_mult = nt.nodes.new('ShaderNodeMath')
        alpha_mult.operation = 'MULTIPLY'
        alpha_mult.location = (0, -160)
        alpha_mult.inputs[1].default_value = alpha
        nt.links.new(src.outputs['Alpha'], alpha_mult.inputs[0])
        nt.links.new(alpha_mult.outputs[0], mix_shader.inputs[0])
    else:
        mix_shader.inputs[0].default_value = alpha

    nt.links.new(transparent.outputs[0], mix_shader.inputs[1])
    nt.links.new(emission.outputs[0], mix_shader.inputs[2])
    nt.links.new(mix_shader.outputs[0], out.inputs['Surface'])


def _set_render_method(mat, blend):
    """
    设置材质的渲染混合模式。

    透明材质（贴花/局部透明）一律 BLENDED（前向）：
    DITHERED 哈希透明在部分模型上会整体失效、按不透明渲染
    （4.5 实测：全身薄纱壳材质让躯干四肢渲染成纯黑），且全透明的
    哈希材质会破坏其身后 S2RGB 表面的光照求值，BLENDED 都安全。
    受光不透明材质用 DITHERED 保持延迟路径（S2RGB 在 BLENDED
    前向模式下无法正常求值光照）。
    """
    if hasattr(mat, 'surface_render_method'):
        mat.surface_render_method = 'BLENDED' if blend else 'DITHERED'
    elif hasattr(mat, 'blend_method'):
        mat.blend_method = 'BLEND' if blend else 'HASHED'


def _resolve_render_path(image, alpha):
    """
    bpy 包装：采样贴图 Alpha 后委托 presets.resolve_render_path 判定路径。

        'lit_opaque' — 受光卡通，不透明（DITHERED）
        'lit_alpha'  — 扁平 Principled + 局部透明（蕾丝/镂空等，BLENDED）
        'decal'      — 平涂贴花，整体/大面积透明叠层（BLENDED，无 S2RGB）

    注意：任何含透明的材质若含 Shader to RGB 会破坏其身后 S2RGB 表面的
    光照求值，因此透明路径一律无 S2RGB。
    """
    has_alpha = _image_has_alpha(image)
    transparent_fraction = 0.0
    if has_alpha:
        transparent_fraction = _sample_image_alpha(image)
    return resolve_render_path(alpha, has_alpha, transparent_fraction)


def convert_material_to_toon(mat, style):
    """
    将单个材质转换为卡通着色（不透明受光）或平涂贴花（半透明叠层）。

    返回统计 dict(category, textured, fallback_color, alpha)。
    """
    category, _ = classify_material(mat.name)
    stats = {
        'category': category,
        'textured': False,
        'fallback_color': False,
        'alpha': False,
    }

    if not mat.use_nodes:
        mat.use_nodes = True

    image, fallback, alpha = extract_base_source(mat)

    # 记录原始来源，保证重复 Apply 时仍可恢复贴图与 alpha（幂等）
    if _SRC_IMAGE_PROP not in mat:
        mat[_SRC_IMAGE_PROP] = image.name if image is not None else ''
        mat[_SRC_ALPHA_PROP] = float(alpha)
        mat[_SRC_FALLBACK_PROP] = [float(c) for c in fallback]

    path = _resolve_render_path(image, alpha)
    mat[RENDER_PATH_PROP] = path
    if path == RENDER_PATH_DECAL:
        _build_decal_tree(mat, image, fallback, alpha)
        stats['alpha'] = True
        _set_render_method(mat, blend=True)
    elif path == RENDER_PATH_LIT_ALPHA:
        _build_principled_flat_tree(mat, image, fallback, alpha)
        stats['alpha'] = True
        # 无 S2RGB 的 BLENDED 前向透明不破坏身后受光面的光照
        _set_render_method(mat, blend=True)
    else:
        _build_toon_tree(mat, image, fallback, category, style)
        # S2RGB 材质若处于 BLENDED（前向）模式会破坏光照求值，统一哈希
        _set_render_method(mat, blend=False)

    if image is not None:
        stats['textured'] = True
    else:
        stats['fallback_color'] = True
        if hasattr(mat, 'diffuse_color'):
            mat.diffuse_color = fallback

    return stats


def convert_meshes_to_toon(meshes, style):
    """
    批量转换所有 mesh 的材质为卡通着色。

    返回聚合统计 dict(total, textured, fallback_color, alpha, per_category)。
    """
    _ALPHA_SAMPLE_CACHE.clear()
    stats = {
        'total': 0,
        'textured': 0,
        'fallback_color': 0,
        'alpha': 0,
        'skipped': 0,
        'per_category': {},
    }
    for mat in iter_unique_materials(meshes):
        try:
            result = convert_material_to_toon(mat, style)
        except Exception:  # pylint: disable=broad-exception-caught
            stats['skipped'] += 1
            continue
        stats['total'] += 1
        stats['textured'] += int(result['textured'])
        stats['fallback_color'] += int(result['fallback_color'])
        stats['alpha'] += int(result['alpha'])
        cat = result['category']
        stats['per_category'][cat] = stats['per_category'].get(cat, 0) + 1
    return stats


def ensure_fallback_material(meshes):
    """
    为没有任何材质槽的 mesh 补一个默认材质（缺失规避）。

    补建的材质带默认 Principled 节点，随后在 convert_meshes_to_toon
    中与其他材质一起按当前风格统一转换，无需在此提前转换。
    返回补建的材质列表。
    """
    created = []
    for mesh in meshes:
        if len(mesh.data.materials) > 0:
            continue
        mat = bpy.data.materials.new(f'HBRToonFallback_{mesh.name}')
        mat.use_nodes = True
        mesh.data.materials.append(mat)
        created.append(mat)
    return created
