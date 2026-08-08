# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — 核心工具函数（bpy 层）。
对象收集、模型检测、语义分类、拓扑检查、色调分析、自动对象清理。
"""

import bpy  # pylint: disable=import-error
import bmesh  # pylint: disable=import-error
from mathutils import Vector  # pylint: disable=import-error

from .presets import (
    HEAD_BONE_NAMES, _COOL_KEYWORDS, _WARM_KEYWORDS,
    AUTO_LIGHT_PREFIX, OUTLINE_MATERIAL_NAME, OUTLINE_MODIFIER_NAME,
    OUTLINE_MASK_GROUP_NAME,
    LEGACY_AUTO_NAMES, classify_material, is_rigid_body_object_name,
)

__all__ = [
    'collect_objects_from_selection',
    'find_primary_mesh',
    'find_armature_for_meshes',
    'head_bone_world_loc',
    'calc_character_metrics',
    'classify_material',
    'iter_mesh_materials',
    'iter_unique_materials',
    'analyze_model_tone',
    'check_mesh_topology',
    'scan_model_features',
    'is_rigid_body_object',
    'cleanup_auto_objects',
]


# ------------------------------------------------------------------
# 模型检测（基于选择对象递归查找）
# ------------------------------------------------------------------

def is_rigid_body_object(obj):
    """
    识别 MMD 刚体/关节伪对象（mmd_tools 导入的物理辅助体）。

    依次检查：mmd_tools ID 属性（插件启用或禁用均可）、
    对象名数字前缀、父级分组名。
    """
    if 'mmd_rigid' in obj.keys() or 'mmd_joint' in obj.keys():
        return True
    if str(getattr(obj, 'mmd_type', '')) in ('RIGID_BODY', 'JOINT'):
        return True
    if obj.type == 'MESH' and is_rigid_body_object_name(obj.name):
        return True
    parent = obj.parent
    if parent is not None and parent.name.lower() in ('rigidbodies', 'joints'):
        return True
    return False


def collect_objects_from_selection(context):
    """
    从当前选中的对象出发，递归收集子树中的所有 MESH 和 ARMATURE 对象。
    自动排除 MMD 刚体伪 mesh。返回 (meshes, armatures) 两个列表。
    """
    selected = list(context.selected_objects)
    if not selected:
        return [], []

    meshes = []
    armatures = []
    seen = set()

    for obj in selected:
        _collect_recursive(obj, meshes, armatures, seen)

    return meshes, armatures


def _collect_recursive(obj, meshes, armatures, seen):
    """递归收集对象及其子对象。"""
    obj_id = obj.as_pointer()
    if obj_id in seen:
        return
    seen.add(obj_id)

    if is_rigid_body_object(obj):
        return
    if obj.type == 'MESH':
        meshes.append(obj)
    elif obj.type == 'ARMATURE':
        armatures.append(obj)

    for child in obj.children:
        _collect_recursive(child, meshes, armatures, seen)


def find_primary_mesh(meshes):
    """从 mesh 列表中返回顶点数最多的主 mesh。"""
    if not meshes:
        return None
    return max(meshes, key=lambda m: len(m.data.vertices))


def find_armature_for_meshes(meshes, armatures):
    """
    尝试为 mesh 列表找到对应的 armature。
    优先返回与主 mesh 同父级或同层的 armature。
    """
    if not armatures:
        return None
    if len(armatures) == 1:
        return armatures[0]

    primary = find_primary_mesh(meshes)
    if not primary:
        return armatures[0]

    # 尝试找到与主 mesh 同父级的 armature
    parent = primary.parent
    for arm in armatures:
        if parent in (arm.parent, arm):
            return arm
    return armatures[0]


def scan_model_features(meshes):
    """
    扫描 mesh 材质，收集模型来源特征标志。

    返回 dict(has_mmd_shader=..., has_mtoon_group=..., has_vrm_props=...)，
    供 presets.detect_model_type 判定 MMD / VRM / GENERIC。
    """
    has_mmd_shader = False
    has_mtoon_group = False
    has_vrm_props = False

    for mat in iter_unique_materials(meshes):
        if not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.name == 'mmd_shader':
                has_mmd_shader = True
            elif node.bl_idname == 'ShaderNodeGroup' and node.node_tree:
                group_name = node.node_tree.name.lower()
                if 'mtoon' in group_name:
                    has_mtoon_group = True

    for mesh in meshes:
        obj = mesh
        while obj is not None:
            keys = obj.keys()
            # 5.0+ bpy.props 定义的属性不再出现在 keys() 中：
            # mmd_tools 启用时改走 RNA 属性判定；keys() 检查保留，
            # 覆盖插件禁用或 4.x 保存的 blend 文件（5.0 会复制旧 ID 属性）。
            # VRM 侧无等效 RNA 判定，但 MToon 节点组检查已是可靠信号。
            if 'mmd_root' in keys or str(getattr(obj, 'mmd_type', '')) == 'ROOT':
                has_mmd_shader = True
            if any('vrm' in str(k).lower() for k in keys):
                has_vrm_props = True
            obj = obj.parent

    return {
        'has_mmd_shader': has_mmd_shader,
        'has_mtoon_group': has_mtoon_group,
        'has_vrm_props': has_vrm_props,
    }


# ------------------------------------------------------------------
# 角色尺寸计算
# ------------------------------------------------------------------

def head_bone_world_loc(arm):
    """从 armature 找头部骨骼世界坐标。"""
    if not arm or not arm.data:
        return None
    for b in arm.pose.bones:
        if b.name in HEAD_BONE_NAMES:
            return arm.matrix_world @ b.head
    for b in arm.pose.bones:
        n = b.name.lower()
        if 'head' in n or '頭' in b.name or '头' in b.name:
            return arm.matrix_world @ b.head
    return None


def calc_character_metrics(_root_obj, arm, mesh):
    """
    计算角色的参考高度和焦点位置。
    返回 (height, fx, fy, fz, cz, es)。
    """
    hl = head_bone_world_loc(arm)
    if hl:
        height = hl.z * 1.08
        fx, fy, fz = hl.x, hl.y, hl.z + height * 0.04
    else:
        coords = [mesh.matrix_world @ Vector(c) for c in mesh.bound_box]
        zs = [c.z for c in coords]
        height = max(zs) - min(zs)
        fx = (max(c.x for c in coords) + min(c.x for c in coords)) / 2
        fy = (max(c.y for c in coords) + min(c.y for c in coords)) / 2
        fz = min(zs) + height * 0.92

    if height <= 0:
        height = 1.6
    es = (height / 1.7) ** 2
    cz = fz - height * 0.92
    return height, fx, fy, fz, cz, es


# ------------------------------------------------------------------
# 材质遍历
# ------------------------------------------------------------------

def iter_mesh_materials(meshes):
    """遍历所有 mesh 的有效材质（跳过空槽位与 mmd_tools 内部材质）。"""
    for mesh in meshes:
        for slot in mesh.material_slots:
            mat = slot.material
            if not mat:
                continue
            if mat.name.startswith(('mmd_tools_rigid', 'mmd_edge.')):
                continue
            yield mat


def iter_unique_materials(meshes):
    """按材质去重遍历（同名材质只处理一次）。"""
    seen = set()
    for mat in iter_mesh_materials(meshes):
        if mat.name in seen:
            continue
        seen.add(mat.name)
        yield mat


# ------------------------------------------------------------------
# 色调分析
# ------------------------------------------------------------------

def _classify_name_tone(mat_name):
    """根据材质名称关键词判断冷暖倾向。返回 1(cool), -1(warm), 0(neutral)。"""
    name_lower = mat_name.lower()
    has_cool = any(kw.lower() in name_lower for kw in _COOL_KEYWORDS)
    has_warm = any(kw.lower() in name_lower for kw in _WARM_KEYWORDS)
    if has_cool and not has_warm:
        return 1
    if has_warm and not has_cool:
        return -1
    return 0


def _extract_base_color_rgb(mat):
    """从材质提取基础色 RGB（Principled 或 mmd_shader Diffuse Color），无效时返回 None。"""
    if not mat.use_nodes:
        return None
    for n in mat.node_tree.nodes:
        col = None
        if n.bl_idname == 'ShaderNodeBsdfPrincipled':
            col = n.inputs.get('Base Color')
        elif n.name == 'mmd_shader':
            col = n.inputs.get('Diffuse Color')
        if col is None:
            continue
        rgb = col.default_value[:3]
        s = sum(rgb)
        if 0.1 <= s <= 2.9:
            return rgb
    return None


def _collect_tone_data(meshes):
    """遍历 mesh 材质，返回 (total_rgb, color_count, name_cool, name_warm, name_count)。"""
    total_rgb = [0.0, 0.0, 0.0]
    color_count = 0
    name_cool = 0
    name_warm = 0
    name_count = 0

    for mat in iter_mesh_materials(meshes):
        name_tone = _classify_name_tone(mat.name)
        if name_tone == 1:
            name_cool += 1
            name_count += 1
        elif name_tone == -1:
            name_warm += 1
            name_count += 1

        rgb = _extract_base_color_rgb(mat)
        if rgb is not None:
            total_rgb[0] += rgb[0]
            total_rgb[1] += rgb[1]
            total_rgb[2] += rgb[2]
            color_count += 1

    return total_rgb, color_count, name_cool, name_warm, name_count


def _compute_tone(total_rgb, color_count, name_cool, name_warm, name_count):
    """基于颜色和名称数据计算 tone。"""
    color_weight = min(1.0, color_count / 5.0)
    name_weight = 1.0 - color_weight if name_count > 0 else 0.0

    color_score = 0.0
    if color_count > 0:
        avg = [c / color_count for c in total_rgb]
        if avg[2] > avg[0] * 1.15:
            color_score = 1.0
        elif avg[0] > avg[2] * 1.15:
            color_score = -1.0

    name_score = 0.0
    if name_count > 0:
        name_score = (name_cool - name_warm) / name_count

    final_score = color_score * color_weight + name_score * name_weight

    if final_score > 0.25:
        return 'cool'
    if final_score < -0.25:
        return 'warm'
    return 'neutral'


def _compute_brightness(total_rgb, color_count):
    """基于颜色数据计算 brightness。"""
    if color_count > 0:
        avg = [c / color_count for c in total_rgb]
        v = max(avg)
    else:
        v = 0.45

    if v > 0.55:
        return 'light'
    if v < 0.35:
        return 'dark'
    return 'medium'


def analyze_model_tone(meshes):
    """
    分析模型整体色调和明暗。
    返回 (tone, brightness)：
        tone: 'cool' / 'warm' / 'neutral'
        brightness: 'light' / 'medium' / 'dark'
    """
    total_rgb, color_count, name_cool, name_warm, name_count = _collect_tone_data(meshes)
    tone = _compute_tone(total_rgb, color_count, name_cool, name_warm, name_count)
    brightness = _compute_brightness(total_rgb, color_count)
    return tone, brightness


# ------------------------------------------------------------------
# 拓扑检查
# ------------------------------------------------------------------

def check_mesh_topology(mesh):
    """
    检查网格拓扑质量，返回 (quality, info_dict)。
    quality: 'clean', 'degraded', 'bad'
    """
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.edges.ensure_lookup_table()

    total = len(bm.edges)
    if total == 0:
        bm.free()
        return 'clean', {'total_edges': 0, 'border_edges': 0, 'border_ratio': 0.0}

    border = sum(1 for e in bm.edges if e.is_boundary)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)

    bm.free()

    border_ratio = border / total

    if border_ratio < 0.01 and non_manifold < 10:
        quality = 'clean'
    elif border_ratio < 0.05:
        quality = 'degraded'
    else:
        quality = 'bad'

    return quality, {
        'total_edges': total,
        'border_edges': border,
        'non_manifold_edges': non_manifold,
        'border_ratio': round(border_ratio, 4),
    }


# ------------------------------------------------------------------
# 清理自动对象
# ------------------------------------------------------------------

def cleanup_auto_objects():
    """
    删除自动生成的灯光、描边与辅助对象（含旧版一键渲染遗留）。
    同时移除所有 mesh 上的描边修改器与描边材质槽位。
    """
    # 灯光与旧版辅助对象
    for obj in list(bpy.data.objects):
        if obj.name.startswith(AUTO_LIGHT_PREFIX) or obj.name in LEGACY_AUTO_NAMES:
            bpy.data.objects.remove(obj, do_unlink=True)

    # 描边修改器与槽位
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for mod in [m for m in obj.modifiers if m.name == OUTLINE_MODIFIER_NAME]:
            obj.modifiers.remove(mod)
        # 描边权重顶点组（贴花排除掩码）
        mask_group = obj.vertex_groups.get(OUTLINE_MASK_GROUP_NAME)
        if mask_group is not None:
            obj.vertex_groups.remove(mask_group)
        # 逆序弹出描边材质槽，避免索引错位
        for i in range(len(obj.data.materials) - 1, -1, -1):
            mat = obj.data.materials[i]
            if mat is not None and mat.name == OUTLINE_MATERIAL_NAME:
                obj.data.materials.pop(index=i)

    # 材质数据块
    for name in (OUTLINE_MATERIAL_NAME, *LEGACY_AUTO_NAMES):
        mat = bpy.data.materials.get(name)
        if mat:
            bpy.data.materials.remove(mat)
