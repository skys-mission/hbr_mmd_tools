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
| **MMD 口型生成** | 基于音频共振峰与能量分析生成口型关键帧（あいうえおん）；支持文件或 VSE 时间轴音频输入 | v0.3 |
| **随机眨眼** | 高斯分布自然眨眼，支持半眨眼与双眨眼 | v0.5 |
| **智能3渲2渲染**（实验性） | 一键 EEVEE 卡通渲染：模型识别、材质卡通化、描边、布光与轻量后期 | v0.6 |
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

> **版本要求：** Blender **4.2 LTS 至 5.2 LTS**（Python 3.11 / 3.13）。

> **注意：** 当前版本为 **0.5.1-preview**，如需稳定版本请使用 **0.5.0**。我们不会发布 0.5.1 正式版，下一个正式版将直接发布 **0.5.5**。

---

## 使用说明

### MMD 口型生成

通过分析音频共振峰生成口型形态键关键帧（あ、い、う、え、お、ん）。

![口型生成界面](.img/lips_gen2.0_zh.webp)

**操作步骤：**
1. 选择音频文件，或使用视频序列编辑器中的音频条。
2. 选中 MMD 模型（或其任意父级对象）。
3. 打开**系统控制台**观察进度（`窗口 → 切换系统控制台`）。
4. 调整参数后点击**生成**。
5. 等待鼠标指针恢复常态。

**参数说明：**

![参数面板](.img/lips3.0.webp)

| 参数 | 说明 |
|---|---|
| **起始帧** | 音频开始的帧位置 |
| **DB 阈值** | dB 降噪门限；识别不准则调高，识别不到则调低 |
| **RMS 阈值** | RMS 降噪门限；识别不准则调高，识别不到则调低 |
| **延时张嘴比例** | 嘴完全张开前的延迟比例 |
| **张嘴速度** | 从识别开始到延时张嘴的曲线速度 |
| **形态键最大值** | 形态键数值上限 |

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
3. 调整参数后点击**生成**。
4. 等待鼠标指针恢复常态。

| 参数 | 说明 |
|---|---|
| **眨眼间隔** | 平均眨眼间隔秒数 |
| **波动比例** | 随机性系数（0.01–1.0） |

> **警告：** 该功能会覆盖所选帧范围内的 `まばたき` 关键帧。

---

### 智能3渲2渲染（实验性）

面向 MMD 风格角色的一键卡通渲染（仅 EEVEE，性能优先）。

**风格预设：**
- **标准** — 经典二阶动画着色。
- **柔和** — 柔和三阶着色，阴影更软。
- **强对比** — 硬边二阶着色，阴影更深。

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

| 版本 | Python | 状态 |
|---|---|---|
| 4.2 LTS – 4.5 LTS | 3.11 | 已支持 |
| 5.0 – 5.2 LTS | 3.11 / 3.13 | 已支持（待实机验证） |
| < 4.2 | — | 不支持 |

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
pip install pylint
pylint src/ --fail-under=9.9
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
