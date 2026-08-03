# -*- coding: utf-8 -*-
# Copyright (c) 2025, https://github.com/skys-mission and Half-Bottled Reverie
"""
MMD Render Optimizer 常量预设配置。
"""

# ==========================================================
# 灯光基础能量（相对于 H_char=1.7m 的参考值）
# 实际能量 = BASE_ENERGY * (H_char / 1.7) ^ 2
# ==========================================================
LIGHT_KEY_ENERGY = 300
LIGHT_FILL_ENERGY = 90
LIGHT_RIM_ENERGY = 100
LIGHT_HAIR_ENERGY = 90
LIGHT_BACK_ENERGY = 80
LIGHT_FRONT_ENERGY = 80

# 灯光色温
LIGHT_KEY_COLOR = (1.0, 0.95, 0.88)
LIGHT_FILL_COLOR = (0.68, 0.78, 0.95)
LIGHT_RIM_COLOR = (1.0, 0.78, 0.55)
LIGHT_HAIR_COLOR = (1.0, 1.0, 1.0)
LIGHT_BACK_COLOR = (1.0, 0.68, 0.42)
LIGHT_FRONT_COLOR = (1.0, 0.98, 0.95)

# ==========================================================
# 材质参数表（Principled BSDF 输入名 -> 值）
# ==========================================================
MATERIAL_PRESETS = {
    'eye_highlight': {
        'Roughness': 0.08, 'Specular IOR Level': 0.80, 'Coat Weight': 0.5,
        'Coat Roughness': 0.06, 'Emission Strength': 0.0,
    },
    'eye_pupil': {
        'Roughness': 0.15, 'Specular IOR Level': 0.70, 'Coat Weight': 0.4,
        'Coat Roughness': 0.08, 'IOR': 1.45,
    },
    'eye_iris': {
        'Roughness': 0.18, 'Specular IOR Level': 0.70, 'Coat Weight': 0.4,
        'Coat Roughness': 0.08, 'IOR': 1.45,
    },
    'eye_white': {
        'Roughness': 0.30, 'Specular IOR Level': 0.45,
    },
    'eye_shadow': {
        'Roughness': 0.65,
    },
    'eyebrow_lash': {
        'Roughness': 0.60,
    },
    'cheek': {
        'Roughness': 0.50, 'Subsurface Weight': 0.18, 'Subsurface Scale': 0.004,
        'Subsurface Radius': (0.55, 0.28, 0.12),
    },
    'mouth': {
        'Roughness': 0.38, 'Subsurface Weight': 0.18, 'Subsurface Scale': 0.004,
        'Subsurface Radius': (0.55, 0.28, 0.12), 'Specular IOR Level': 0.50,
    },
    'tongue': {
        'Roughness': 0.30, 'Subsurface Weight': 0.25, 'Subsurface Scale': 0.006,
        'Subsurface Radius': (0.55, 0.28, 0.12), 'Specular IOR Level': 0.55,
    },
    'teeth': {
        'Roughness': 0.20, 'Specular IOR Level': 0.60,
    },
    'face': {
        'Roughness': 0.38, 'Subsurface Weight': 0.30, 'Subsurface Scale': 0.04,
        'Subsurface Radius': (0.60, 0.30, 0.12), 'Specular IOR Level': 0.45,
        'Coat Weight': 0.15, 'Coat Roughness': 0.15,
    },
    'skin': {
        'Roughness': 0.42, 'Subsurface Weight': 0.25, 'Subsurface Scale': 0.04,
        'Subsurface Radius': (0.60, 0.30, 0.12), 'Specular IOR Level': 0.45,
        'Coat Weight': 0.12, 'Coat Roughness': 0.20,
    },
    'hair': {
        'Roughness': 0.38, 'Anisotropic': 0.35, 'Coat Weight': 0.08,
        'Coat Roughness': 0.30, 'Specular IOR Level': 0.45,
    },
    'metal': {
        'Metallic': 1.0, 'Roughness': 0.30, 'Anisotropic': 0.1,
        'Specular IOR Level': 0.5,
    },
    'jewelry': {
        'Roughness': 0.25, 'Coat Weight': 0.7, 'Coat Roughness': 0.08,
        'IOR': 1.50, 'Specular IOR Level': 0.55,
    },
    'accessory': {
        'Metallic': 0.25, 'Roughness': 0.45, 'Coat Weight': 0.0,
        'Specular IOR Level': 0.35,
    },
    'emissive_deco': {
        'Roughness': 0.25, 'Emission Strength': 1.5,
        'Emission Color': (1, 0.9, 0.7, 1),
    },
    'shoes': {
        'Roughness': 0.50, 'Coat Weight': 0.1, 'Coat Roughness': 0.20,
        'Specular IOR Level': 0.4,
    },
    'bag': {
        'Roughness': 0.60, 'Sheen Weight': 0.1, 'Specular IOR Level': 0.35,
    },
    'wing_tail': {
        'Roughness': 0.45, 'Sheen Weight': 0.15, 'Specular IOR Level': 0.4,
    },
    'ear': {
        'Roughness': 0.35, 'Coat Weight': 0.15, 'Coat Roughness': 0.15,
        'Specular IOR Level': 0.5,
    },
    'cloth': {
        'Roughness': 0.60, 'Sheen Weight': 0.05, 'Sheen Roughness': 0.5,
        'Specular IOR Level': 0.35,
    },
    'fallback': {
        'Roughness': 0.55, 'Specular IOR Level': 0.35,
    },
}

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
    ('face', ['顏', '颜', '脸', 'face', '面']),
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

# ==========================================================
# Compositor 参数
# ==========================================================
BLOOM_STRENGTH = 0.03
BLOOM_THRESHOLD = 3.5
VIGNETTE_EDGE = 0.45

# ==========================================================
# 渲染参数
# ==========================================================
TAA_SAMPLES = 64
TAA_SAMPLES_AGGRESSIVE = 128
CYCLES_SAMPLES = 64
CYCLES_SAMPLES_AGGRESSIVE = 128
