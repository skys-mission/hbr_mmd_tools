# HBR MMD Tools

[![Release](https://img.shields.io/github/v/release/skys-mission/hbr_mmd_tools?style=flat-square)](https://github.com/skys-mission/hbr_mmd_tools/releases)
[![License](https://img.shields.io/github/license/skys-mission/hbr_mmd_tools?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.13-blue?style=flat-square)]()
[![Pylint](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml)
[![CodeQL Advanced](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml)
[![Bandit](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml/badge.svg)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml)

**A Blender add-on for MikuMikuDance (MMD) workflows.**
Generate lip-sync keyframes from audio, create natural random blinking, render anime-style cel shading with one-click smart toon setup, and manage shape keys for MMD-style characters.

Other languages: [简体中文](README_zh.md), [日本語](README_ja.md)

---

## Feature Overview

| Feature | Description | Since |
|---|---|---|
| **MMD Lip-Sync** | Audio-driven mouth shape keyframe generation (あいうえおん) via formant and energy analysis; supports file or VSE timeline audio input | v0.3 |
| **Random Blinking** | Gaussian-distributed natural blinking with half-blink and double-blink support | v0.5 |
| **Smart Toon Render** *(Experimental)* | One-click EEVEE cel shading: model detection, toon materials, outline, lighting & light post | v0.6 |
| **Render Presets** | Quick resolution, aspect ratio and orientation presets | v0.5 |
| **Camera Settings** | Focal length, aperture and depth-of-field presets | v0.5 |

## Screenshots

### Lip-Sync Generation
![Lip Sync](.img/lip_sync.webp)
*Model: KissshotSusu*

### Random Blinking
![Blink Settings](.img/blink_args.webp)

### Render Optimizer *(Experimental)*
> One-click EEVEE cel shading: auto-detects MMD / VRM / generic models, posterized toon materials, real-time Solidify outline.

---

## Installation

1. Download the latest release from [Releases](https://github.com/skys-mission/hbr_mmd_tools/releases).
2. In Blender: `Edit → Preferences → Add-ons → Install from Disk`.
3. Select the downloaded `.zip` and enable **HBR MMD Tools**.

> **Version Requirement:** Blender **4.2 LTS to 5.2 LTS** (Python 3.11 / 3.13).

> **Note:** The current version is **0.5.1-preview**. If you need a stable build, please use **0.5.0**. There will be no official 0.5.1 release — the next official release will be **0.5.5**.

---

## Usage

### MMD Lip-Sync Generation

Generates mouth shape keyframes (あ, い, う, え, お, ん) by analyzing audio formants.

![Lip Sync UI](.img/lips_gen2.0f.webp)

**Steps:**
1. Select an audio file or use the active VSE audio strip.
2. Select an MMD model (or any parent object in its hierarchy).
3. Open **System Console** to monitor progress (`Window → Toggle System Console`).
4. Adjust parameters and click **Generate**.
5. Wait for the cursor to return to normal.

**Parameters:**

![Parameters](.img/lips3.0.webp)

| Parameter | Description |
|---|---|
| **Start Frame** | Frame where the audio begins |
| **DB Threshold** | Noise floor in dB; raise if inaccurate, lower if nothing is detected |
| **RMS Threshold** | RMS noise gate; raise if inaccurate, lower if nothing is detected |
| **Delayed Opening** | Delay ratio before mouth fully opens |
| **Speed Up Opening** | Curve speed from recognition start to delayed opening |
| **Max Morph Value** | Maximum morph key value cap |

**Adapting to Non-MMD Models**

The VRM standard defines expression *preset* names only — shape key names are not standardized, and an imported model keeps its original morph names. Check the model's actual shape keys first:

- Keys named after VRM 1.0 presets (`aa` `ih` `ou` `ee` `oh`, blink `blink`): select the bundled `vrm.json`
- Keys named after VRM 0.x presets (`A` `I` `U` `E` `O`, blink `Blink`): select the bundled `vrm0.json`
- Any other naming (e.g. VRoid exports use `..._Fcl_MTH_A`): copy/rename the shape keys, or import a custom config

> **At least one lip shape key must exist.** See [copy_shape_key.md](docs/copy_shape_key.md) for how to copy shape keys.

---

### Random Blinking

Generates natural blinking keyframes for the `まばたき` shape key.

**Steps:**
1. Select an MMD model (or any parent object).
2. Open **System Console** to monitor progress.
3. Adjust parameters and click **Generate**.
4. Wait for the cursor to return to normal.

| Parameter | Description |
|---|---|
| **Blink Interval** | Average seconds between blinks |
| **Wave Ratio** | Randomness factor (0.01–1.0) |

> **Warning:** This overwrites existing `まばたき` keyframes in the selected range.

---

### Smart Toon Render *(Experimental)*

One-click cel shading for MMD-style characters (EEVEE only, performance-first).

**Style presets:**
- **Standard** — Classic two-tone anime shading.
- **Soft** — Softer three-tone shading with gentle shadows.
- **Contrast** — Hard two-tone shading with deep shadows.

**Features:**
- **Model Type Detection** — Distinguishes MMD (mmd_tools imports), VRM and generic models, each with its own base-color extraction strategy.
- **Smart Toon Materials** — Keeps original textures and applies semantic per-category ramp tuning: brighter faces, highlight band on hair, nearly self-lit eyes.
- **Missing-Asset Fallbacks** — Broken or missing textures fall back to diffuse colors; meshes without materials get a default toon material; alpha channels are preserved automatically.
- **Solidify Inverted-Hull Outline** — Real-time EEVEE outline (default), reusing the per-vertex `mmd_edge_scale` weights from MMD imports; optional Freestyle for higher quality.
- **3-Point Toon Lighting** — Only the key sun casts shadows; area lights aim at the character automatically.
- **Light Post** — Slight contrast and low-quality bloom; conservative samples, ray tracing off.

> **Warning:** Material conversion rebuilds node trees (restore with Undo / Ctrl+Z). The **Reset** button removes auto-created lights, outlines, world and compositor setup.

---

## Compatibility

### Blender Versions

| Version | Python | Status |
|---|---|---|
| 4.2 LTS – 4.5 LTS | 3.11 | Supported |
| 5.0 – 5.2 LTS | 3.11 / 3.13 | Supported (pending on-device verification) |
| < 4.2 | — | Not Supported |

### Operating Systems

| OS | Status |
|---|---|
| Windows x64 | Supported |
| macOS ARM64 | Experimental |
| Linux | Not Planned |

---

## Development

### Build & Lint

```bash
pip install pylint
pylint src/ --fail-under=9.9
```

### Notes

- Audio analysis runs on the Python standard library alone; the only bundled binary is FFmpeg (used to decode arbitrary audio formats).

### AI-Assisted Development

This project is developed with a heavy **vibe-coding** workflow (\>70% of code contributions).  
The primary IDE/tool used is **Claude Code**; however, **Claude models are not used** as the generation backend.  
LLM inference is mainly provided by **Kimi** and **DeepSeek**.

---

## License

[GPL-3.0](LICENSE)

## Credits

| Project | Link | License |
|---|---|---|
| FFmpeg | https://github.com/FFmpeg/FFmpeg | GPLv3 (tools embedded in Releases) |
