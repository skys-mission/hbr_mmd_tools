# HBR MMD Tools

[![Release](https://img.shields.io/github/v/release/skys-mission/hbr_mmd_tools?style=flat-square)](https://github.com/skys-mission/hbr_mmd_tools/releases)
[![License](https://img.shields.io/github/license/skys-mission/hbr_mmd_tools?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.13-blue?style=flat-square)]()
[![Pylint](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml)
[![CodeQL Advanced](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml)
[![Bandit](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml/badge.svg)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml)

**面向 MikuMikuDance (MMD) 工作流的 Blender 插件。**
从音频生成口型关键帧、创建自然随机眨眼、一键 PBR/NPR 渲染优化，以及 MMD 风格角色的形态键管理工具。

其它语言：[English](README.md), [日本語](README_ja.md)

---

## 功能一览

| 功能 | 说明 | 起始版本 |
|---|---|---|
| **MMD 口型生成** | 基于音频共振峰与能量分析生成口型关键帧（あいうえおん）；支持文件或 VSE 时间轴音频输入 | v0.3 |
| **随机眨眼** | 高斯分布自然眨眼，支持半眨眼与双眨眼 | v0.5 |
| **渲染优化器**（实验性） | 一键自适应布光、PBR/NPR 材质增强、环境与合成器配置 | v0.5 |
| **渲染预设** | 快速设置分辨率、纵横比与画面方向 | v0.5 |
| **相机设置** | 焦距、光圈与景深预设 | v0.5 |

## 截图

### 口型生成
![Lip Sync](.img/lip_sync.webp)
*模型来源：KissshotSusu*

### 随机眨眼
![Blink Settings](.img/blink_args.webp)

### 渲染优化器（实验性）
> 一键配置 EEVEE / Cycles 渲染，自适应 6 点布光与智能材质分类。

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

VRM 或其它模型需确保存在以下形态键（可复制已有形态键改名）：

| MMD 名称 | 对应 |
|---|---|
| あ | A |
| い | I |
| う | U |
| え | E |
| お | O |
| ん | N |

> **至少要拥有「あ」才能使用本功能。** 复制方法请参考：[copy_shape_key.md](docs/copy_shape_key.md)

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

### 渲染优化器（实验性）

面向 MMD 风格角色的一键渲染配置。

**预设：**
- **PBR** — 写实渲染，增强皮肤、头发、金属、布料等材质质感。
- **PBR 激进** — 更强的材质差异，适合戏剧性光照。
- **NPR** — 卡通风格渲染，支持 Freestyle 描边。

**特性：**
- **自适应 6 点布光** — 根据角色身高自动定位主光、补光、轮廓光、头发光、背景光、正面光。
- **智能材质分类** — 自动识别皮肤、头发、金属、珠宝、眼睛、布料等并应用调优的 Principled BSDF 参数。
- **色调感知环境** — 基于模型色彩分析自动配置冷/暖/中性世界环境。
- **合成器配置** — 自动添加暗角与色彩分级节点。
- **渲染引擎切换** — EEVEE 或 Cycles。

> **警告：** 此功能会创建自动命名的灯光和世界节点。点击**重置**按钮可清理。

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
