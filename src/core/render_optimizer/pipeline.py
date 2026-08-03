# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
渲染管线版本兼容层。

抹平 Blender 4.2 - 5.2 之间的渲染 API 差异：
- EEVEE 引擎 ID（4.2-4.5 为 ``BLENDER_EEVEE_NEXT``，5.0+ 改回 ``BLENDER_EEVEE``）
- 合成器节点树（4.x 为 ``scene.node_tree``，5.0+ 为独立数据块
  ``scene.compositing_node_group``，且 ``scene.use_nodes`` 被移除）
- 5.0 中被删除的合成器节点（MixRGB / ColorRamp / Composite，
  官方建议改用对应的 Shader 节点与 Group Output）
- 节点选项在 4.5+ 从属性迁移为输入插槽
"""

from ...util.logger import Log

BLENDER_5_0 = (5, 0, 0)

EEVEE_ENGINE_ID = 'BLENDER_EEVEE'
EEVEE_ENGINE_ID_NEXT = 'BLENDER_EEVEE_NEXT'
CYCLES_ENGINE_ID = 'CYCLES'

LEGACY_COMPOSITOR_NODE_IDS = (
    'CompositorNodeMixRGB',
    'CompositorNodeValToRGB',
    'CompositorNodeComposite',
)
MODERN_COMPOSITOR_NODE_IDS = (
    'ShaderNodeMixRGB',
    'ShaderNodeValToRGB',
    'NodeGroupOutput',
)


def resolve_eevee_engine_id(blender_version):
    """返回指定 Blender 版本对应的 EEVEE 引擎 ID。"""
    if tuple(blender_version) < BLENDER_5_0:
        return EEVEE_ENGINE_ID_NEXT
    return EEVEE_ENGINE_ID


def resolve_compositor_node_ids(blender_version):
    """返回指定版本下（混合节点, 色阶节点, 输出节点）的 bl_idname 三元组。"""
    if tuple(blender_version) >= BLENDER_5_0:
        return MODERN_COMPOSITOR_NODE_IDS
    return LEGACY_COMPOSITOR_NODE_IDS


def get_eevee_engine_id():
    """返回当前 Blender 版本对应的 EEVEE 引擎 ID。"""
    # pylint: disable=import-outside-toplevel
    from ..compat import get_blender_version
    return resolve_eevee_engine_id(get_blender_version())


def is_modern_compositor():
    """判断当前 Blender 是否使用 5.0+ 的新合成器管线。"""
    # pylint: disable=import-outside-toplevel
    from ..compat import is_blender_version_at_least
    return is_blender_version_at_least(BLENDER_5_0)


def ensure_compositor_tree(scene):
    """启用场景合成器并返回其节点树。"""
    import bpy  # pylint: disable=import-outside-toplevel,import-error

    if not is_modern_compositor():
        scene.use_nodes = True
        return scene.node_tree

    node_tree = scene.compositing_node_group
    if node_tree is None or node_tree.users > 1:
        # 5.0+ 合成器树是独立数据块，可能被其他场景共享，避免误改
        node_tree = bpy.data.node_groups.new("HBR Compositing", "CompositorNodeTree")
        scene.compositing_node_group = node_tree
    scene.render.use_compositing = True
    return node_tree


def disable_compositor(scene):
    """关闭场景合成器。"""
    if is_modern_compositor():
        scene.render.use_compositing = False
        return

    scene.use_nodes = False
    if scene.node_tree:
        scene.node_tree.nodes.clear()


def new_node(node_tree, legacy_idname, modern_idname=None):
    """按版本创建节点；5.0+ 提供 modern_idname 以替代被删除的旧节点。"""
    bl_idname = legacy_idname
    if modern_idname is not None and is_modern_compositor():
        bl_idname = modern_idname
    return node_tree.nodes.new(bl_idname)


def append_output_socket(node_tree):
    """创建合成器输出节点，返回接收最终图像的输入插槽。"""
    if not is_modern_compositor():
        output = node_tree.nodes.new('CompositorNodeComposite')
        return output.inputs['Image']

    _ensure_output_interface(node_tree)
    output = node_tree.nodes.new('NodeGroupOutput')
    socket = output.inputs.get('Image')
    if socket is None:
        socket = output.inputs[0]
    return socket


def _ensure_output_interface(node_tree):
    """确保合成器树接口中存在输出插槽（5.0+ 由 Group Output 消费）。"""
    for item in node_tree.interface.items_tree:
        if getattr(item, 'in_out', '') == 'OUTPUT':
            return
    node_tree.interface.new_socket(
        name="Image", in_out="OUTPUT", socket_type="NodeSocketColor",
    )


def image_output(node):
    """返回节点的图像输出插槽（兼容合成器 Image 与 Shader 节点 Color 标识符）。"""
    for name in ('Image', 'Color'):
        socket = node.outputs.get(name)
        if socket is not None:
            return socket
    return node.outputs[0]


def set_node_option(node, prop_name, input_names, value):
    """
    设置节点选项，兼容 4.2-4.4 的属性形式与 4.5+ 的输入插槽形式。

    优先尝试 input_names 中的输入插槽，失败时回退到 prop_name 属性。
    返回是否设置成功。
    """
    for name in input_names:
        socket = node.inputs.get(name)
        if socket is None or socket.is_linked:
            continue
        try:
            socket.default_value = value
            return True
        except (TypeError, ValueError):
            continue

    if hasattr(node, prop_name):
        try:
            setattr(node, prop_name, value)
            return True
        except (AttributeError, TypeError, ValueError):
            pass
    Log.warning(
        f"Failed to set node option {prop_name}={value!r} on {node.bl_idname}, "
        f"tried input sockets {tuple(input_names)}"
    )
    return False
