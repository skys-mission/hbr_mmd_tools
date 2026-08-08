# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Smart Toon Render — 纯常量与纯逻辑预设。

本模块不导入 bpy，所有函数均为纯函数，可在 Blender 外进行单元测试。
包含：卡通色阶(ramp)规则、模型类型识别、材质语义分类、灯光/描边/合成器常量。
"""

import re

# ==========================================================
# 卡通风格预设
# ==========================================================
TOON_STYLE_STANDARD = 'STANDARD'
TOON_STYLE_SOFT = 'SOFT'
TOON_STYLE_CONTRAST = 'CONTRAST'

TOON_STYLES = (TOON_STYLE_STANDARD, TOON_STYLE_SOFT, TOON_STYLE_CONTRAST)

# 阴影染色（乘算在基础色上，轻微偏冷是常见日式动画阴影色）
SHADOW_TINT = (0.92, 0.92, 1.05)

# 各风格的基础阴影阶调：
#   shadow   — 阴影面亮度系数
#   mid      — 中间调亮度系数（仅 SOFT 使用）
#   threshold — 阴影/受光分界（0~1，对应受光响应）
#   soft_threshold — SOFT 风格中间调分界
_STYLE_PARAMS = {
    TOON_STYLE_STANDARD: {
        'shadow': 0.55, 'mid': 0.82, 'threshold': 0.50, 'soft_threshold': 0.72,
    },
    TOON_STYLE_SOFT: {
        'shadow': 0.62, 'mid': 0.85, 'threshold': 0.45, 'soft_threshold': 0.70,
    },
    TOON_STYLE_CONTRAST: {
        'shadow': 0.42, 'mid': 0.75, 'threshold': 0.55, 'soft_threshold': 0.78,
    },
}

# 分类微调：delta 加在风格参数上；flat 表示近乎自发光（眼睛/发光件）
_CATEGORY_TWEAKS = {
    'face': {'shadow': 0.08, 'threshold': -0.05},
    'skin': {'shadow': 0.06, 'threshold': -0.03},
    'cheek': {'shadow': 0.08, 'threshold': -0.05},
    'hair': {'highlight': 1.12, 'highlight_pos': 0.85},
    'metal': {'shadow': -0.12, 'threshold': 0.05},
    'jewelry': {'shadow': -0.10, 'threshold': 0.05},
    'eye_highlight': {'flat': 1.0},
    'eye_iris': {'flat': 0.95},
    'eye_pupil': {'flat': 0.92},
    'emissive_deco': {'flat': 1.0},
}


def _clamp(value, low=0.0, high=1.2):
    return max(low, min(high, value))


def _flat_stops(value):
    """近乎自发光的分类（眼睛/发光件）：整段常亮，只保留极暗部一点层次。"""
    v = _clamp(value)
    return [(0.0, (v * 0.92, v * 0.92, v * 0.92)), (0.25, (v, v, v))]


def _insert_soft_midtone(stops, params, threshold):
    """SOFT 风格在阴影与受光之间插入中间调，形成柔和三段。"""
    mid = _clamp(params['mid'])
    # 中间调必须落在受光分界之下：face/cheek/skin 等负向 threshold
    # 微调后 soft_threshold*0.6 可能不低于 threshold，排序后中间调会
    # 跑到受光档之后，造成受光面反而变暗的亮度反转
    mid_pos = min(
        _clamp(params['soft_threshold'], threshold + 0.01, 0.98) * 0.6,
        threshold - 0.02,
    )
    mid_rgb = tuple(_clamp(mid * t) for t in SHADOW_TINT)
    stops.insert(1, (mid_pos, mid_rgb))


def resolve_ramp_stops(category, style):
    """
    解析指定材质分类与卡通风格的色阶停靠点。

    返回 [(position, (r, g, b)), ...]，按 position 升序，供 ColorRamp(CONSTANT) 使用。
    颜色为乘算系数：1.0 表示保持基础色，小于 1.0 为压暗的阴影。
    """
    params = _STYLE_PARAMS.get(style, _STYLE_PARAMS[TOON_STYLE_STANDARD])
    tweak = _CATEGORY_TWEAKS.get(category, {})

    if tweak.get('flat') is not None:
        return _flat_stops(tweak['flat'])

    shadow = _clamp(params['shadow'] + tweak.get('shadow', 0.0))
    threshold = _clamp(params['threshold'] + tweak.get('threshold', 0.0), 0.05, 0.95)
    shadow_rgb = tuple(_clamp(shadow * t) for t in SHADOW_TINT)

    stops = [(0.0, shadow_rgb), (threshold, (1.0, 1.0, 1.0))]

    highlight = tweak.get('highlight')
    if highlight is not None:
        hpos = _clamp(tweak.get('highlight_pos', 0.85), threshold + 0.01, 0.98)
        hv = _clamp(highlight)
        stops.append((hpos, (hv, hv, hv)))
    elif style == TOON_STYLE_SOFT:
        _insert_soft_midtone(stops, params, threshold)

    stops.sort(key=lambda s: s[0])
    return stops


def detect_model_type(has_mmd_shader, has_mtoon_group, has_vrm_props=False):
    """
    根据收集到的特征标志识别模型来源类型。

    返回 'MMD' / 'VRM' / 'GENERIC'。
    """
    if has_mmd_shader:
        return 'MMD'
    if has_mtoon_group or has_vrm_props:
        return 'VRM'
    return 'GENERIC'


def resolve_outline_thickness(height, width_factor):
    """
    根据角色高度与用户宽度系数计算 Solidify 描边厚度（米）。

    基准：1.6m 高的角色在 width_factor=1.0 时约 5.6mm。
    """
    if height <= 0:
        height = 1.6
    factor = max(0.05, min(float(width_factor), 5.0))
    return height * 0.0035 * factor


def is_rigid_body_object_name(name):
    """识别 MMD 刚体伪 mesh 的命名格式（如 000_xxx / 012_下半身）。"""
    return len(name) > 3 and name[:3].isdigit() and name[3] == '_'


# ==========================================================
# 透明材质的渲染路径判定（纯函数，可单测）
# ==========================================================
# EEVEE 约束：任何含透明（恒定 alpha<1，或贴图存在 alpha<1 的 texel）的
# 材质都不能包含 Shader to RGB —— 透明 texel 会清零其身后 S2RGB 表面的
# 光照求值（4.5 实测：全身薄纱壳材质让身后的皮肤渲染成纯黑）。
# 因此透明材质一律走无 S2RGB 的结构。
RENDER_PATH_LIT_OPAQUE = 'lit_opaque'
RENDER_PATH_LIT_ALPHA = 'lit_alpha'
RENDER_PATH_DECAL = 'decal'

# 转换后的渲染路径写入材质的这个自定义属性，供描边识别贴花面
# （贴花与局部透明材质同为 BLENDED，混合模式本身无法区分）
RENDER_PATH_PROP = 'hbr_toon_path'

# 透明 texel 占比阈值：低于视为不透明（忽略微小 alpha 杂点），
# 高于视为整体/大面积透明叠层（贴花）。
_ALPHA_OPAQUE_TOLERANCE = 0.005
_ALPHA_DECAL_THRESHOLD = 0.5


def resolve_render_path(alpha, has_alpha, transparent_fraction):
    """
    判定材质的卡通化渲染路径。

    参数:
        alpha: 材质恒定不透明度（如 MMD 材质 alpha）
        has_alpha: 基础色贴图是否带 Alpha 通道
        transparent_fraction: 贴图 alpha < 0.995 的采样占比（无通道时传 0）

    返回:
        'lit_opaque' — 受光卡通（Shader to RGB 色阶），不透明
        'lit_alpha'  — 扁平 Principled + 贴图透明（BLENDED，无 S2RGB）
        'decal'      — 平涂贴花（BLENDED，无 S2RGB）
    """
    if alpha < 0.999:
        return RENDER_PATH_DECAL
    if not has_alpha:
        return RENDER_PATH_LIT_OPAQUE
    if transparent_fraction < _ALPHA_OPAQUE_TOLERANCE:
        return RENDER_PATH_LIT_OPAQUE
    if transparent_fraction > _ALPHA_DECAL_THRESHOLD:
        return RENDER_PATH_DECAL
    return RENDER_PATH_LIT_ALPHA


# ==========================================================
# 灯光（3点卡通布光，仅主光投影以保持性能）
# ==========================================================
LIGHT_KEY_ENERGY = 3.0          # SUN，能量与角色尺寸无关
LIGHT_FILL_ENERGY = 240         # AREA，需乘 (H/1.7)^2
LIGHT_RIM_ENERGY = 130

LIGHT_KEY_COLOR = (1.0, 0.96, 0.90)
LIGHT_FILL_COLOR = (0.72, 0.80, 0.95)
LIGHT_RIM_COLOR = (1.0, 0.82, 0.62)

LIGHT_KEY_SUN_ANGLE = 0.35      # 太阳角越大阴影边缘越柔

# ==========================================================
# World 背景（与模型明暗互补，突出主体）
# ==========================================================
WORLD_COLORS = {
    'light': (0.20, 0.21, 0.26, 1.0),
    'medium': (0.40, 0.43, 0.48, 1.0),
    'dark': (0.60, 0.62, 0.66, 1.0),
}
WORLD_STRENGTH = 1.0

# ==========================================================
# Compositor 参数（轻量后期，注意性能）
# ==========================================================
BLOOM_THRESHOLD = 1.2
BLOOM_MIX = 0.06
BLOOM_SIZE_LEGACY = 6           # 4.x：0-9 的 2 的幂指数
BLOOM_SIZE_MODERN = 0.5         # 5.0+：0-1 比例
BRIGHT_CONTRAST = (0.0, 0.08)

# ==========================================================
# 渲染参数（EEVEE 专用，保守采样保证性能）
# ==========================================================
EEVEE_RENDER_SAMPLES = 32

# ==========================================================
# 自动创建对象命名（Reset 依赖这些名字做清理）
# ==========================================================
AUTO_LIGHT_PREFIX = 'HBRToon'
LIGHT_KEY_NAME = 'HBRToonKey'
LIGHT_FILL_NAME = 'HBRToonFill'
LIGHT_RIM_NAME = 'HBRToonRim'
OUTLINE_MATERIAL_NAME = 'HBRToonOutline'
OUTLINE_MODIFIER_NAME = 'HBRToonOutline'
OUTLINE_MASK_GROUP_NAME = 'hbr_outline_mask'
OUTLINE_COLOR = (0.012, 0.008, 0.016, 1.0)

# 旧版一键渲染创建的对象，Reset 时一并清理
LEGACY_AUTO_NAMES = (
    'AutoKey', 'AutoFill', 'AutoRim', 'AutoHair', 'AutoBack',
    'AutoFront', 'AutoGround', 'AutoBounce', 'AutoBackdrop', 'AutoDome',
    'AutoBackdropMat', 'AutoDomeMat', 'AutoGroundMat',
)

# ==========================================================
# 材质语义分类规则（简 / 繁 / 日 / 英 / 拼音）
# ==========================================================
HEAD_BONE_NAMES = {'頭', '头', 'Head', 'head', '頭部', '头部'}

SEMANTIC_RULES = [
    ('eye_highlight', ['目光', '瞳光', '眼神光', 'highlight', 'eyelight', 'hilight']),
    ('eye_pupil', ['瞳孔', 'pupil']),
    ('eye_white', ['白目', '眼白', 'sclera', 'shirome', 'bai3']),
    ('eye_shadow', ['目影', '眼影', 'eyeshadow']),
    ('eye_iris', ['星目', '目鏡', '目镜', '眼睛', '眼球', '瞳', 'iris', 'hitomi']),
    ('eyebrow_lash', ['眉睫', '眉毛', '睫毛', 'eyebrow', 'eyelash']),
    ('cheek', ['頰', '腮', '红晕', 'cheek', 'blush']),
    ('mouth', ['口舌', '嘴', '唇', 'mouth', 'lip']),
    ('tongue', ['舌', 'tongue']),
    ('teeth', ['齒', '齿', '牙', 'teeth', 'tooth']),
    ('face', ['顏', '颜', '顔', '脸', 'face', '面']),
    ('accessory', [
        '头饰', '頭飾', '髮飾', '发饰', '飾品', '饰品', '吊飾', '吊饰', '装饰', '裝飾', '服饰',
        '蝴蝶結', '蝴蝶结', '蝴蝶', '流苏', '流蘇', '腰帶', '腰带',
        '鏡片', '鏡框', '镜片', '镜框', '眼镜', '眼鏡', 'glasses', 'lens',
        'accessory', 'ornament', 'decor', 'headpiece', 'belt',
    ]),
    ('hair', [
        '髪', '髮', '头发', '頭髪', '前髪', '後髪', '后髪', '后髮', '前髮', '刘海',
        'bangs', 'hair',
    ]),
    ('metal', [
        '金属', '金屬', '金扣', '金链', '金鏈', '金醣', '金墜', '金子', '足金',
        '链子', '链条', '链', '鎖', '锁', '扣', '醣', '铆', '釆', '螺丝', '螺絲',
        '齿轮', '機械', '机械', '钢', '鋼', '银', '銀', '铜', '銄', '铁', '鉄',
        'metal', 'gold', 'silver', 'iron', 'metallic', 'chain', 'buckle',
        'rivet', 'screw', 'gear', 'mech', 'steel', 'copper',
    ]),
    ('jewelry', [
        '珍珠', '寶石', '宝石', '水晶', '钻石', '鑽石', '貝殼', '贝壳', '神之眼',
        'pearl', 'gem', 'jewel', 'crystal', 'diamond',
    ]),
    ('emissive_deco', [
        '灯条', '燈條', '光翼', '光羽', 'glow', 'emit', 'neon', 'star', 'heart',
    ]),
    ('shoes', ['鞋', '靴', 'shoe', 'boot']),
    ('bag', ['包包', '背包', '挎包', '包带', '包帶', 'bag', 'pouch']),
    ('wing_tail', ['翼', '羽', '尾巴', '尾', 'wing', 'tail', 'feather']),
    ('ear', ['耳', 'ear']),
    ('cloth', [
        '披風', '披风', '袖', '裙', '上衣', '内衣', '内裤', '上半身', '下半身',
        '上身', '下身', '上body', '下body', '大衣', '外套', '夹克', '马甲', '马夢',
        '长袍', '袍', '军装', '袜', '襪', '褲', '裤', '下擺', '下著', '腰結', '后結',
        '後結', '布', '花边', '蕴絲', '蕴丝',
        'mi_up', 'mi_down', 'mi_body', 'cloth', 'dress', 'skirt', 'sleeve',
        'shirt', 'cape', 'jacket', 'pants', 'top', 'bottom',
        '帽', '衣', '服',
    ]),
    ('skin', [
        '肌', '皮膚', '皮肤', '手足', '手套', '腕套', '腿', '臂', '腕',
        '軂體', '軂体', '驱体', 'skin', 'body', 'hada', '軂', '体',
    ]),
    ('eyebrow_lash', ['眉', '睫']),
    ('mouth', ['口']),
    ('eye_iris', ['目']),
]

PINYIN_RULES = [
    ('eye_iris', ['eye']),
    ('eye_white', ['bai']),
    ('tongue', ['she']),
    ('eyebrow_lash', ['mei', 'jie']),
    ('teeth', ['hi']),
    ('face', ['kao']),
]

# 冷暖色调关键词
_COOL_KEYWORDS = {
    '蓝', '藍', '青', '紫', '碧', '冰', '水', '海', '天', '苍', '沧',
    ' cold', 'cool', 'cyan', 'blue', 'purple', 'aqua', 'indigo', 'violet',
    'ice', 'azure', 'navy', 'sapphire',
}
_WARM_KEYWORDS = {
    '红', '紅', '橙', '黄', '黃', '金', '赤', '暖', '火', '阳', '棕', '粉',
    '橘', '杏', ' warm', 'red', 'orange', 'yellow', 'gold', 'fire', 'warm',
    'brown', 'pink', 'rose', 'amber', 'coral', 'peach',
}


def classify_material(mat_name):
    """多语言材质语义分类，返回 (category, is_overlay)。"""
    is_overlay = (
        mat_name.endswith('+')
        or mat_name.endswith('+.001')
        or mat_name.endswith('++')
    )
    name_lower = mat_name.lower()

    for cat, kws in SEMANTIC_RULES:
        for kw in kws:
            if kw.lower() in name_lower:
                return cat, is_overlay

    tokens = [t for t in re.split(r'[._\-+\s]+|\d+', name_lower) if t]
    for cat, kws in PINYIN_RULES:
        for kw in kws:
            if kw in tokens:
                return cat, is_overlay

    return 'fallback', is_overlay
