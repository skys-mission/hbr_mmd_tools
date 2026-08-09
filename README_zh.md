# HBR MMD Tools

[![Release](https://img.shields.io/github/v/release/skys-mission/hbr_mmd_tools?style=flat-square)](https://github.com/skys-mission/hbr_mmd_tools/releases)
[![License](https://img.shields.io/github/license/skys-mission/hbr_mmd_tools?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.13-blue?style=flat-square)]()
[![Pylint](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml)
[![CodeQL Advanced](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml)
[![Bandit](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml/badge.svg)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml)

**面向 MikuMikuDance (MMD) 工作流的 Blender 插件。**
从音频生成口型关键帧、创建自然随机眨眼、一键智能3渲2渲染，以及 MMD 风格角色的形态键管理工具。

其它语言：[English](README.md), [日本語](README_ja.md)

---

## 功能一览

| 功能 | 说明 | 起始版本 |
|---|---|---|
| **MMD 口型生成** | 基于音频共振峰与能量分析生成口型关键帧（あいうえおん）；支持文件或 VSE 时间线音频输入 | v0.3 |
| **随机眨眼** | 高斯分布自然眨眼，支持半眨眼与双眨眼 | v0.5 |
| **智能3渲2渲染**（实验性） | 一键 EEVEE 卡通渲染：模型识别、材质卡通化、描边、布光与轻量后期 | v0.5.5 |
| **渲染预设** | 快速设置分辨率、纵横比与画面方向 | v0.5 |
| **相机设置** | 焦距、光圈与景深预设 | v0.5 |

## 截图

### 口型生成
![Lip Sync](.img/lip_sync.webp)
*模型来源：KissshotSusu*

### 随机眨眼
![Blink Settings](.img/blink_args.webp)

### 渲染优化器（实验性）
> 一键 EEVEE 卡通渲染：自动识别 MMD / VRM / 通用模型，材质二/三阶卡通化，Solidify 实时描边。

---

## 下载与安装

**GitHub Releases：** https://github.com/skys-mission/hbr_mmd_tools/releases

**中国大陆用户：**  
链接: https://pan.baidu.com/s/17ubgxZvXVs6goKBjtBFzXA?pwd=gmuv 提取码: gmuv

**安装步骤：**
1. 下载最新 Release 的 `.zip` 文件。
2. Blender 中：`编辑 → 偏好设置 → 插件 → 从磁盘安装`。
3. 选择下载的 `.zip`，勾选启用 **HBR MMD Tools**。

> **版本要求：** Blender **4.2 – 5.2**（Python 3.11 / 3.13）；人工测试仅覆盖 LTS 版本（见[兼容性](#兼容性)）。

> **版本说明：** 当前版本为 **0.5.5**。历史版本（如 0.5.0）可在 [Releases](https://github.com/skys-mission/hbr_mmd_tools/releases) 页面下载。

---

## 使用说明

### MMD 口型生成

通过分析音频共振峰生成口型形态键关键帧（あ、い、う、え、お、ん）。

![口型生成界面](.img/lips_gen2.0_zh.webp)

**操作步骤：**
1. 选择**音频来源**：**文件**（磁盘上的音频）或**时间线**（视频序列编辑器中的音频片段）。
2. 选中 MMD 模型（或其任意父级对象）。
3. 打开**系统控制台**观察进度（`窗口 → 切换系统控制台`）。
4. 调整参数后点击**生成口型**。
5. 等待鼠标指针恢复常态。

**参数说明：**

![参数面板](.img/lips3.0.webp)

| 参数 | 说明 |
|---|---|
| **音频来源** | **文件**：浏览选择磁盘音频；**时间线**：使用 VSE 时间线中的音频片段 |
| **音频片段** | 仅时间线来源：按名称选择片段，生成时起始帧自动锁定为片段的起始帧 |
| **起始帧** | 音频开始的帧位置（时间线来源下由所选片段决定） |
| **预设** | 整体口型风格：**自然**（平滑均衡，适合多数对白）、**清晰发音**（嘴型动作更锐利）、**柔和动作**（幅度更小更柔和） |

**高级（自定义调参）：** 默认跟随所选预设；勾选**自定义调参**后可手动微调——

| 参数 | 说明 |
|---|---|
| **分贝阈值** | dB 降噪门限；识别不准则调高，识别不到则调低 |
| **均方根阈值** | RMS 降噪门限；识别不准则调高，识别不到则调低 |
| **延时张嘴** | 嘴完全张开前的延迟缓冲 |
| **加速张嘴** | 从识别开始到延时张嘴的曲线速度 |
| **最大阈值** | 形态键数值上限 |

**配置（Config）：** 选择形态键映射配置（内置 `mmd` / `vrm` / `vrm0`），或导入自定义 JSON 配置；**打开配置目录**可直接管理用户配置文件。

**适配非 MMD 模型**

VRM 标准只定义了表情预设名，并未规定形态键名——模型导入后保留原始 morph 名称，请先在形态键列表中确认模型实际的键名：

- 键名为 VRM 1.0 预设名（`aa` `ih` `ou` `ee` `oh`，眨眼 `blink`）：选择内置 `vrm.json`
- 键名为 VRM 0.x 预设名（`A` `I` `U` `E` `O`，眨眼 `Blink`）：选择内置 `vrm0.json`
- 其它命名（如 VRoid 导出的 `..._Fcl_MTH_A`）：复制/重命名形态键，或导入自定义配置

> **口型形态键至少存在一个才能使用本功能。** 复制方法请参考：[copy_shape_key.md](docs/copy_shape_key.md)

---

### 随机眨眼

为 `まばたき` 形态键生成自然眨眼关键帧。

**操作步骤：**
1. 选中 MMD 模型（或其任意父级对象）。
2. 打开**系统控制台**观察进度。
3. 调整参数后点击**生成随机眨眼**。
4. 等待鼠标指针恢复常态。

| 参数 | 说明 |
|---|---|
| **起始 / 结束** | 生成眨眼动画的帧范围 |
| **眨眼间隔** | 平均眨眼间隔秒数 |
| **波动比例** | 随机性系数（0–1） |
| **半眨眼比例** | 半眨眼概率（0=从不，1=总是）；双眨眼概率为其两倍 |

> **警告：** 该功能会覆盖所选帧范围内的 `まばたき` 关键帧。

---

### 智能3渲2渲染（实验性）

面向 MMD 风格角色的一键卡通渲染（仅 EEVEE，性能优先）。

**参数说明：**

| 参数 | 说明 |
|---|---|
| **卡通风格** | **标准**（经典二阶）、**柔和**（三阶软阴影）、**强对比**（硬边二阶深阴影） |
| **描边** | **Solidify（快速）**：实时反向壳描边（默认）；**Freestyle（高质量）**：拓扑感知线条，渲染较慢；**无** |
| **描边宽度** | 厚度系数（0.05–5.0，默认 0.15），按角色身高自动缩放，仅 Solidify 模式 |
| **亮度倾向** | 高级：覆盖自动亮度检测（自动 / 浅色 / 标准 / 深色） |
| **合成后期** | 高级：轻量 Bloom 与对比度后期 |

**特性：**
- **模型类型识别** — 自动区分 MMD（mmd_tools 导入）/ VRM / 通用模型并采用对应的基础色提取策略。
- **智能材质卡通化** — 保留原贴图，按语义分类（脸、发、眼、金属等）应用不同阶调；脸部更亮、头发带高光带、眼睛近乎自发光。
- **缺失规避** — 贴图丢失时自动回退到漫射纯色；无材质 mesh 自动补默认卡通材质；Alpha 通道自动保留。
- **Solidify 反向壳描边** — EEVEE 实时描边（默认），复用 MMD 逐顶点 `mmd_edge_scale` 权重；可选 Freestyle 高质量描边。
- **3 点卡通布光** — 仅主光（太阳光）投影，面积光自动对准角色，保证渲染性能。
- **轻量后期** — 轻微对比度与低质量 Bloom；渲染采样保守、关闭光线追踪。

> **警告：** 材质转换会重建节点树（可用撤销 Ctrl+Z 恢复）。**重置**按钮清理自动创建的灯光、描边、World 与合成器。

---

## 兼容性

### Blender 版本

当前版本计划支持 Blender **4.2 – 5.2**。人工测试仅覆盖 LTS 版本（4.2 LTS / 4.5 LTS / 5.2 LTS）；非 LTS 版本按 API 变更适配，未经逐一实机验证。

| 版本 | Python | 状态 |
|---|---|---|
| 4.2 LTS / 4.5 LTS | 3.11 | 已支持（人工测试） |
| 5.2 LTS | 3.13 | 已支持（人工测试） |
| 4.3 – 5.1（非 LTS） | 3.11 / 3.13 | 计划支持（未经人工测试） |
| < 4.2 / ≥ 5.3 | — | 不支持（运行时拦截） |

### 操作系统

| 系统 | 状态 |
|---|---|
| Windows x64 | 已支持 |
| macOS ARM64 | 实验性支持 |
| Linux | 不计划支持 |

---

## 开发

### 构建与检查

```bash
# 代码检查（CI 要求 ≥ 9.9 分）
pip install pylint
pylint src/ --fail-under=9.9

# 单元测试（纯 Python 模块，无需 Blender）
python3 -m unittest discover -s tests

# 打包 Release（内嵌固定版本 FFmpeg，产物输出到 dist/）
python3 tools/build_release.py
```

### 注意事项

- 音频分析仅使用 Python 标准库实现；唯一内嵌的二进制是 FFmpeg（用于解码任意音频格式）。

### AI 辅助开发

本项目采用重度 **vibe-coding** 工作流（代码贡献占比 \>70%）。  
主要使用的开发工具是 **Claude Code**；但**未使用 Claude 模型**作为代码生成后端。  
大模型推理主要由 **Kimi** 与 **DeepSeek** 提供。

---

## 开源协议

[GPL-3.0](LICENSE)

## 致谢

| 项目 | 链接 | 协议 |
|---|---|---|
| FFmpeg | https://github.com/FFmpeg/FFmpeg | GPLv3（Release 中内嵌工具采用此协议） |
