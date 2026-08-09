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
| **Smart Toon Render** *(Experimental)* | One-click EEVEE cel shading: model detection, toon materials, outline, lighting & light post | v0.5.5 |
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

> **Version Requirement:** Blender **4.2 – 5.2** (Python 3.11 / 3.13); manual testing covers LTS releases only (see [Compatibility](#compatibility)).

> **Note:** The current version is **0.5.5**. Older builds (e.g. 0.5.0) remain available on the [Releases](https://github.com/skys-mission/hbr_mmd_tools/releases) page.

---

## Usage

### MMD Lip-Sync Generation

Generates mouth shape keyframes (あ, い, う, え, お, ん) by analyzing audio formants.

![Lip Sync UI](.img/lips_gen2.0f.webp)

**Steps:**
1. Choose the **Audio Source**: **File** (an audio file on disk) or **Timeline** (an audio strip in the Video Sequence Editor).
2. Select an MMD model (or any parent object in its hierarchy).
3. Open **System Console** to monitor progress (`Window → Toggle System Console`).
4. Adjust parameters and click **Generate Lip Sync**.
5. Wait for the cursor to return to normal.

**Parameters:**

![Parameters](.img/lips3.0.webp)

| Parameter | Description |
|---|---|
| **Audio Source** | **File**: browse for an audio file; **Timeline**: use an audio strip from the VSE timeline |
| **Audio Strip** | Timeline source only: pick a strip by name; generation locks the start frame to the strip's start |
| **Start Frame** | Frame where the audio begins (decided by the selected strip when using the timeline source) |
| **Preset** | Overall lip sync style: **Natural** (smooth and balanced), **Clear Speech** (sharper mouth motion), **Soft Motion** (smaller and softer motion) |

**Advanced (Custom Tuning):** parameters follow the selected preset unless **Custom Tuning** is enabled —

| Parameter | Description |
|---|---|
| **DB Threshold** | Noise floor in dB; raise if inaccurate, lower if nothing is detected |
| **RMS Threshold** | RMS noise gate; raise if inaccurate, lower if nothing is detected |
| **Delayed Opening** | Buffer before the mouth fully opens |
| **Speed Up Opening** | Curve speed from recognition start to delayed opening |
| **Max Morph Value** | Maximum shape key value cap |

**Config:** choose a shape-key mapping (bundled `mmd` / `vrm` / `vrm0`) or import a custom JSON config; **Open Config Folder** gives direct access to user config files.

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
3. Adjust parameters and click **Gen random blink**.
4. Wait for the cursor to return to normal.

| Parameter | Description |
|---|---|
| **Start / End** | Frame range to generate blinks in |
| **Blink Interval** | Average seconds between blinks |
| **Wave Ratio** | Randomness factor (0–1) |
| **Half Blink Ratio** | Probability of a half-blink (0=never, 1=always); double blinks use twice this chance |

> **Warning:** This overwrites existing `まばたき` keyframes in the selected range.

---

### Smart Toon Render *(Experimental)*

One-click cel shading for MMD-style characters (EEVEE only, performance-first).

**Parameters:**

| Parameter | Description |
|---|---|
| **Toon Style** | **Standard** (classic two-tone), **Soft** (three-tone, gentle shadows), **Contrast** (hard two-tone, deep shadows) |
| **Outline** | **Solidify (Fast)**: real-time inverted-hull outline (default); **Freestyle (Quality)**: topology-aware line art, slower; **None** |
| **Outline Width** | Thickness multiplier (0.05–5.0, default 0.15), auto-scaled by character height; Solidify mode only |
| **Brightness** | Advanced: override the automatic brightness detection (Auto / Light / Medium / Dark) |
| **Compositor Post** | Advanced: light bloom and contrast post-processing |

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

This version targets Blender **4.2 – 5.2**. Manual testing covers LTS releases only (4.2 LTS / 4.5 LTS / 5.2 LTS); non-LTS releases are adapted per API changes but not individually verified on-device.

| Version | Python | Status |
|---|---|---|
| 4.2 LTS / 4.5 LTS | 3.11 | Supported (manually tested) |
| 5.2 LTS | 3.13 | Supported (manually tested) |
| 4.3 – 5.1 (non-LTS) | 3.11 / 3.13 | Planned support (not manually tested) |
| < 4.2 / ≥ 5.3 | — | Not supported (blocked at runtime) |

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
# Lint (CI requires a score of at least 9.9)
pip install pylint
pylint src/ --fail-under=9.9

# Unit tests (pure-Python modules, no Blender needed)
python3 -m unittest discover -s tests

# Build release zips (bundles a pinned FFmpeg, outputs to dist/)
python3 tools/build_release.py
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
