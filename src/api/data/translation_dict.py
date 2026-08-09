# -*- coding: utf-8 -*-
# Copyright (c) 2024, https://github.com/skys-mission and Half-Bottled Reverie
"""
翻译相关
"""


def get_translation_zh_dict(local):
    """
    获取翻译字典

    本函数用于根据指定的本地化参数，返回一个包含翻译映射的字典

    参数:
    local (str): 本地化参数，用于指定需要的翻译语言

    返回:
    dict: 包含翻译映射的字典
    """
    translation_dict = {
        local: translation_zh_map
    }

    return translation_dict


translation_zh_map = {
    ("*", "MMD Lip Gen"): "MMD口型生成",
    ("*", "Audio Path"): "音频文件",
    ("*", "Audio Source"): "音频来源",
    ("*", "File"): "文件",
    ("*", "Timeline"): "时间线",
    ("*", "Where to get the audio for lip sync generation"): "选择口型生成所使用的音频来源",
    ("*", "Use an audio file from disk"): "从磁盘选择音频文件",
    ("*", "Use audio from the Video Sequence Editor timeline"): "使用视频序列编辑器时间线中的音频",
    ("*", "No audio in timeline"): "时间线中没有音频",
    ("*", "Audio Strip"): "音频片段",
    ("*", "Select an audio strip from the timeline"): "从时间线中选择一个音频片段",
    ("*", "No audio strip selected"): "未选择音频片段",
    ("*", "No audio strips found"): "时间线中没有音频片段",
    ("*", "Audio starts at frame"): "音频起始帧",
    ("*", "Bilibili cover image"): "必剪封面",
    ("*", "382:239 Bilibili cover image"): "382:239 B站封面",
    ("*", "Other"): "其它",
    ("*", "Old Film Standards"): "旧电影标准",
    ("*", "Film Standards"): "电影标准",
    ("*", "2.39:1 Film Standards"): "2.39:1 电影标准",
    ("*", "Standard"): "标准",
    ("*", "Old Standard"): "旧标准",
    ("*", "Landscape"): "横屏",
    ("*", "Portrait"): "竖屏",
    ("*", "Resolution"): "分辨率",
    ("*", "Aspect Ratio"): "宽高比",
    ("*", "Rotate"): "旋转",
    ("*", "Render Preset"): "渲染预设",
    ("*", "Set Camera"): "设置相机",
    ("*", "Focal Length"): "焦距",
    ("*", "F-Stop"): "光圈",
    ("*", "Depth of Field"): "景深",
    ("*", "Focus on Object"): "聚焦到物体",
    ("*", "Select focus object"): "选择聚焦物体",
    ("*", "Apply settings to the selected camera"): "将设置应用到选定的相机",
    ("*", "14mm ultra-wide field"): "14mm 超广角镜头",
    ("*", "Highlight background"): "突出背景",
    ("*", "24mm wide angle"): "24mm 广角镜头",
    ("*", "scenery, street snap"): "风景摄影，街头抓拍",
    ("*", "50mm human eye perspective"): "50mm 人眼视角镜头",
    ("*", "human eye perspective"): "人眼视角",
    ("*", "85mm classic portrait"): "85mm 经典肖像镜头",
    ("*", "classic portrait, background blur"): "经典肖像，背景虚化",
    ("*", "135mm long-focus"): "135mm 长焦镜头",
    ("*", "long-focus, strong background blur"): "长焦，强烈的背景虚化",
    ("*", "f/1.4 low light env"): "f/1.4 低光环境",
    ("*", "Background blur, portrait/night scene photography"): "背景虚化，适用于人像/夜景摄影",
    ("*", "f/2.8 default"): "f/2.8 默认光圈",
    ("*", "f/4 medium aperture"): "f/4 中等光圈",
    ("*", "Suitable for average lighting conditions"): "适合一般光照条件",
    ("*", "f/8 small aperture"): "f/8 小光圈",
    ("*", "Requires strong lighting"): "需要强光",
    ("*", "f/22 minimum aperture"): "f/22 最小光圈",
    ("*", "Requires a strong light environment"): "需要强光环境",
    ("*", "Slightly Blurred. Suitable for average lighting conditions"): "轻微虚化，适合一般光照条件",
    ("*", "HBR MMD Tools"): "HBR MMD工具",
    ("*", "default"): "默认",
    ("*", "Start Frame"): "起始帧",
    ("*", "Preset"): "预设",
    ("*", "Natural"): "自然",
    ("*", "Clear Speech"): "清晰发音",
    ("*", "Soft Motion"): "柔和动作",
    ("*", "Choose the overall lip sync style"): "选择整体口型风格",
    ("*", "Smooth and balanced motion for most dialogue"): "适用于大多数对白的平滑均衡口型",
    ("*", "Sharper mouth motion for clearer articulation"): "更清晰的咬字与更明显的口型动作",
    ("*", "Smaller and softer mouth motion"): "较小且更柔和的口型动作",
    ("*", "Advanced"): "高级",
    ("*", "Custom Tuning"): "自定义调参",
    ("*", "Use manual advanced tuning instead of the preset"): "使用手动高级参数而不是预设",
    ("*", "Using preset tuning"): "当前使用预设调参",
    ("*", "Delayed Opening"): "延时张嘴",
    ("*", "Speed Up Opening"): "加速张嘴",
    ("*", "DB Threshold"): "分贝阈值",
    ("*", "RMS Threshold"): "均方根阈值",
    ("*", "Max Morph Value"): "最大阈值",
    ("*", "Threshold for the maximum value of the morphological key"): "形态键最大值的阈值",
    ("*", "Minimum threshold for audio root mean square identification"): "识别音频均方根的最小阈值",
    ("*", "Minimum threshold for audio volume detection"): "识别音频音量的最小阈值",
    ("*", "The mouth does not open immediately upon recognition;"
          " the unit is in milliseconds,"
          " and the buffer value is calculated"
          " based on the acceleration parameters for opening the mouth"): "不是识别开始就张嘴的，"
                                                                          "单位毫秒，"
                                                                          "根据加速张嘴参数计算缓冲值",
    ("*", "The larger this parameter is, "
          "the greater the value of the morph key "
          "for delayed mouth opening will be."): "这个参数越大，延时张嘴的形态键数值就会越大",
    ("*", "Timeline"): "时间线",
    ("*", "MMD Random Blink"): "MMD 随机眨眼",
    ("*", "start"): "起始",
    ("*", "end"): "结束",
    ("*", "blink interval"): "眨眼间隔",
    ("*", "The interval in seconds between blinks."): "眨眼的间隔时间，单位秒",
    ("*", "blinking wave ratio"): "波动比例",
    ("*", "half blink ratio"): "半眨眼比例",
    ("*", "Probability of a half-blink (0=never, 1=always). "
          "Double blinks use twice this chance."): "半眨眼概率（0=从不，1=总是）。双眨眼时使用两倍此概率。",
    ("*","Blink interval = "
         "blink interval + "
         "rand(-fluctuation ratio, "
         "fluctuation ratio)"):"眨眼间隔=眨眼间隔+rand(-波动比例,波动比例)",
    ("Operator", "Gen random blink"): "生成随机眨眼",
    ("Operator", "apply camera settings"): "应用相机设置",
    ("Operator", "Generate Lip Sync"): "生成口型",
    ("Operator", "user doc"): "用户文档",
    ("Operator", "open source"): "开源地址",
    ("*", "author: Half-Bottled Reverie"): "作者：半瓶入梦",
    ("*", "MMD Smart Toon Render (Experimental)"): "MMD智能3渲2渲染（试验性）",
    ("*", "Toon Style"): "卡通风格",
    ("*", "Cel shading style preset"): "卡通着色风格预设",
    ("*", "Classic two-tone anime shading"): "经典二阶动画着色",
    ("*", "Softer three-tone shading with gentle shadows"): "柔和三阶着色，阴影更软",
    ("*", "Hard two-tone shading with deep shadows"): "硬边二阶着色，阴影更深",
    ("*", "Brightness"): "亮度倾向",
    ("*", "Auto"): "自动",
    ("*", "Light"): "浅色",
    ("*", "Medium"): "标准",
    ("*", "Dark"): "深色",
    ("*", "Compositor Post"): "合成后期",
    ("*", "Enable light bloom and contrast post-processing"): "启用轻量泛光与对比度后期",
    ("*", "Outline"): "描边",
    ("*", "Outline strategy"): "描边策略",
    ("*", "Solidify (Fast)"): "Solidify（快速）",
    ("*", "Inverted hull outline, real-time in EEVEE"): "反向壳描边，EEVEE 实时渲染",
    ("*", "Freestyle (Quality)"): "Freestyle（高质量）",
    ("*", "Topology-aware line art, slower render"): "拓扑感知线条，渲染较慢",
    ("*", "None"): "无",
    ("*", "No outline"): "无描边",
    ("*", "Outline Width"): "描边宽度",
    ("*", "Outline thickness multiplier (Solidify mode only)"): "描边厚度系数（仅 Solidify 模式）",
    ("Operator", "Apply Toon Render"): "应用3渲2渲染",
    ("*", "One-click smart cel shading: converts materials, adds outline, "
          "lights and post-processing (EEVEE only)"): "一键智能3渲2：转换卡通材质、添加描边、"
                                                     "灯光与后期（仅 EEVEE）",
    ("Operator", "Reset"): "重置",
    ("*", "Delete auto-created lights and outlines, reset World, disable Compositor "
          "(toon-shaded materials can be restored with Undo)"): (
        "删除自动创建的灯光与描边，重置World，关闭合成器（卡通化材质可用撤销恢复）"
    ),
    ("*", "Select model, then apply (EEVEE only)"): "选择模型后应用（仅 EEVEE）",
    ("*", "Soft"): "柔和",
    ("*", "Contrast"): "强对比",
}
