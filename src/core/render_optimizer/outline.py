# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — 描边。

默认使用 Solidify 反向壳描边（EEVEE 实时，性能远优于 Freestyle）；
Freestyle 作为备选策略保留。
"""

import bpy  # pylint: disable=import-error

from .presets import (
    OUTLINE_MATERIAL_NAME, OUTLINE_MODIFIER_NAME, OUTLINE_MASK_GROUP_NAME,
    OUTLINE_COLOR, RENDER_PATH_DECAL, RENDER_PATH_PROP,
    resolve_outline_thickness,
)
from .utils import check_mesh_topology

OUTLINE_STRATEGIES = {
    'none': 'No outline',
    'solidify': 'Solidify (Fast)',
    'freestyle': 'Freestyle (Quality)',
}

# MMD 导入时写入的逐顶点描边权重顶点组
MMD_EDGE_SCALE_GROUP = 'mmd_edge_scale'

# 标记过的 Freestyle 面所属的 mesh 自定义属性（清理时只碰我们标记过的）
_FS_MARK_PROP = 'hbr_fs_marked'

# Freestyle 面标记的存储在 5.x 从 MeshPolygon.use_freestyle_mark RNA 属性
# 迁移为名为 freestyle_face 的布尔 FACE 域 mesh 属性；4.x 仍走 RNA 属性
_HAS_FS_FACE_MARK_PROP = hasattr(bpy.types.MeshPolygon, 'use_freestyle_mark')
_FS_FACE_ATTR = 'freestyle_face'


def _get_face_mark(mesh, poly):
    """读取单面的 Freestyle 面标记（4.x RNA 属性 / 5.x 命名属性）。"""
    if _HAS_FS_FACE_MARK_PROP:
        return poly.use_freestyle_mark
    attr = mesh.attributes.get(_FS_FACE_ATTR)
    return bool(attr.data[poly.index].value) if attr is not None else False


def _set_face_mark(mesh, poly, value):
    """写入单面的 Freestyle 面标记，5.x 下按需创建 freestyle_face 属性。"""
    if _HAS_FS_FACE_MARK_PROP:
        poly.use_freestyle_mark = value
        return
    attr = mesh.attributes.get(_FS_FACE_ATTR)
    if attr is None:
        if not value:
            return
        attr = mesh.attributes.new(name=_FS_FACE_ATTR, type='BOOLEAN', domain='FACE')
    attr.data[poly.index].value = value


def _is_decal_material(mat):
    """判断材质是否为贴花（平涂叠层）。

    优先读转换时写入的路径属性；未转换过的材质（理论上不会出现，
    描边总在材质转换后执行）回退按混合模式判断。
    """
    path = mat.get(RENDER_PATH_PROP)
    if path is not None:
        return path == RENDER_PATH_DECAL
    render_method = getattr(mat, 'surface_render_method', None)
    if render_method is None:
        render_method = getattr(mat, 'blend_method', 'OPAQUE')
    return render_method in ('BLENDED', 'BLEND')


def _decal_slot_indices(mesh_obj):
    """返回贴花材质槽位索引集合。"""
    indices = set()
    for i, slot in enumerate(mesh_obj.material_slots):
        mat = slot.material
        if mat is not None and _is_decal_material(mat):
            indices.add(i)
    return indices


def _exclusive_decal_verts(mesh_obj, decal_slots):
    """返回仅被贴花面使用的顶点集合（与受光面共享的顶点不在内）。"""
    lit_verts = set()
    decal_verts = set()
    for poly in mesh_obj.data.polygons:
        target = decal_verts if poly.material_index in decal_slots else lit_verts
        target.update(poly.vertices)
    return decal_verts - lit_verts


def _get_or_create_outline_material():
    """创建（或复用）共享的黑色描边材质。"""
    mat = bpy.data.materials.get(OUTLINE_MATERIAL_NAME)
    if mat is None:
        mat = bpy.data.materials.new(OUTLINE_MATERIAL_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emission = nt.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = OUTLINE_COLOR
    emission.inputs['Strength'].default_value = 1.0
    nt.links.new(emission.outputs[0], out.inputs['Surface'])
    # 反向壳正面剔除：只渲染朝内的背面，形成轮廓线
    mat.use_backface_culling = True
    return mat


def _build_outline_mask(mesh_obj, only_decal):
    """
    构建描边权重顶点组：纯贴花几何（目影/表情贴片等浮空卡片）独占的
    顶点权重为 0，避免透明卡片被反向壳描出黑框；其余顶点沿用
    MMD 逐顶点描边权重（存在时相乘），让粗细跟随原模型意图。
    """
    mesh = mesh_obj.data
    group = mesh_obj.vertex_groups.get(OUTLINE_MASK_GROUP_NAME)
    if group is None:
        group = mesh_obj.vertex_groups.new(name=OUTLINE_MASK_GROUP_NAME)

    edge_scale = mesh_obj.vertex_groups.get(MMD_EDGE_SCALE_GROUP)
    if edge_scale is None:
        others = [v.index for v in mesh.vertices if v.index not in only_decal]
        if others:
            group.add(others, 1.0, 'REPLACE')
        group.add(sorted(only_decal), 0.0, 'REPLACE')
        return

    # 与 mmd_edge_scale 权重相乘；按权重值分桶后批量写入，
    # 逐顶点 add() 会因内部数组重分配退化成 O(n²)
    buckets = {}
    for v in mesh.vertices:
        idx = v.index
        if idx in only_decal:
            continue
        try:
            weight = edge_scale.weight(idx)
        except RuntimeError:  # 顶点不在组中时 Blender 抛 RuntimeError
            weight = 1.0
        buckets.setdefault(round(weight, 4), []).append(idx)
    for weight, indices in buckets.items():
        group.add(indices, weight, 'REPLACE')
    if only_decal:
        group.add(sorted(only_decal), 0.0, 'REPLACE')


def _apply_solidify_outline(mesh_obj, outline_mat, thickness):
    """为单个 mesh 添加 Solidify 反向壳描边。"""
    # 已有同名修改器则先移除，保证幂等
    for mod in [m for m in mesh_obj.modifiers if m.name == OUTLINE_MODIFIER_NAME]:
        mesh_obj.modifiers.remove(mod)

    # 贴花面（目影/表情贴片等浮空透明卡片）不参与描边，避免黑框
    decal_slots = _decal_slot_indices(mesh_obj)
    only_decal = _exclusive_decal_verts(mesh_obj, decal_slots) if decal_slots else set()

    mesh_obj.data.materials.append(outline_mat)
    slot_index = len(mesh_obj.data.materials) - 1

    mod = mesh_obj.modifiers.new(OUTLINE_MODIFIER_NAME, 'SOLIDIFY')
    mod.thickness = thickness
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = slot_index

    if only_decal:
        _build_outline_mask(mesh_obj, only_decal)
        mod.shell_vertex_group = OUTLINE_MASK_GROUP_NAME
    elif MMD_EDGE_SCALE_GROUP in mesh_obj.vertex_groups:
        # 复用 MMD 逐顶点描边权重（存在时让描边粗细跟随原模型意图）
        mod.shell_vertex_group = MMD_EDGE_SCALE_GROUP


def _is_decal_only_mesh(mesh_obj):
    """mesh 的全部材质都是贴花时视为纯叠层 mesh（腮红/目影等）。"""
    mats = [s.material for s in mesh_obj.material_slots if s.material]
    if not mats:
        return False
    return all(_is_decal_material(mat) for mat in mats)


def setup_outline(meshes, strategy='solidify', width_factor=1.0, height=1.6):
    """
    根据策略为 mesh 列表设置描边。

    参数:
        meshes: 目标 mesh 对象列表
        strategy: 'none' / 'solidify' / 'freestyle'
        width_factor: 描边宽度系数（仅 solidify）
        height: 角色高度（用于推算描边厚度）

    返回:
        dict 包含 enabled, strategy, count 等信息
    """
    scene = bpy.context.scene

    if strategy == 'freestyle':
        primary = max(meshes, key=lambda m: len(m.data.vertices)) if meshes else None
        if primary is None:
            return {'enabled': False, 'strategy': 'none'}
        return _setup_freestyle(scene, primary, meshes)

    disable_freestyle(scene)

    if strategy != 'solidify' or not meshes:
        return {'enabled': False, 'strategy': 'none'}

    outline_mat = _get_or_create_outline_material()
    thickness = resolve_outline_thickness(height, width_factor)

    count = 0
    for mesh_obj in meshes:
        if len(mesh_obj.data.vertices) < 4:
            continue
        # 纯贴花 mesh（腮红/目影等叠层）不描边，避免透明卡片出现黑框
        if _is_decal_only_mesh(mesh_obj):
            continue
        _apply_solidify_outline(mesh_obj, outline_mat, thickness)
        count += 1

    return {
        'enabled': count > 0,
        'strategy': 'solidify',
        'count': count,
        'thickness': round(thickness, 5),
    }


def _clear_freestyle_marks():
    """清除上次 Apply 打下的 Freestyle 面标记（只清我们标记过的 mesh）。"""
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        if _FS_MARK_PROP not in mesh:
            continue
        for poly in mesh.polygons:
            if _get_face_mark(mesh, poly):
                _set_face_mark(mesh, poly, False)
        del mesh[_FS_MARK_PROP]


def _mark_decal_faces(meshes):
    """
    为 Freestyle 过滤标记贴花面：仅标记顶点全部独占于贴花面的面
    （目影/表情贴片等浮空透明卡片）。与受光面共享顶点的叠层面
    （如 顏+ 红晕复制层）不标记，避免误伤受光面自身的轮廓线。
    返回是否有任何标记。
    """
    marked_any = False
    for mesh_obj in meshes:
        if mesh_obj.type != 'MESH':
            continue
        decal_slots = _decal_slot_indices(mesh_obj)
        if not decal_slots:
            continue
        only_decal = _exclusive_decal_verts(mesh_obj, decal_slots)
        if not only_decal:
            continue
        mesh = mesh_obj.data
        marked = False
        for poly in mesh.polygons:
            if (poly.material_index in decal_slots
                    and not _get_face_mark(mesh, poly)
                    and all(v in only_decal for v in poly.vertices)):
                _set_face_mark(mesh, poly, True)
                marked = True
        if marked:
            mesh[_FS_MARK_PROP] = True
            marked_any = True
    return marked_any


def disable_freestyle(scene):
    """关闭 Freestyle，并清理我们打下的面标记。"""
    scene.render.use_freestyle = False
    _clear_freestyle_marks()
    if not scene.view_layers:
        return
    fs = scene.view_layers[0].freestyle_settings
    while fs.linesets:
        fs.linesets.remove(fs.linesets[0])


def _setup_freestyle(scene, mesh, meshes):
    """设置 Freestyle 描边（拓扑感知，质量高但渲染慢）。"""
    quality, topo_info = check_mesh_topology(mesh)
    use_material_boundary = quality == 'clean'

    scene.render.use_freestyle = True
    vl = scene.view_layers[0]
    fs = vl.freestyle_settings
    fs.use_smoothness = True

    while fs.linesets:
        fs.linesets.remove(fs.linesets[0])

    ls = fs.linesets.new("Outline")
    ls.select_silhouette = True
    ls.select_crease = False
    ls.select_border = False
    ls.select_edge_mark = False
    ls.select_material_boundary = use_material_boundary

    # 贴花浮空卡片（目影/表情贴片）不描边：面标记 + 反向过滤
    _clear_freestyle_marks()
    if _mark_decal_faces(meshes):
        ls.select_by_face_marks = True
        ls.face_mark_condition = 'ONE'
        ls.face_mark_negation = 'EXCLUSIVE'

    linestyle = bpy.data.linestyles.get("NPR_Outline")
    if not linestyle:
        linestyle = bpy.data.linestyles.new("NPR_Outline")
    linestyle.thickness = 1.5
    linestyle.color = (0.0, 0.0, 0.0)
    ls.linestyle = linestyle

    return {
        'enabled': True,
        'quality': quality,
        'topo_info': topo_info,
        'strategy': 'freestyle+material_boundary'
        if use_material_boundary else 'freestyle_silhouette',
    }
