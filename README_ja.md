# HBR MMD Tools

[![Release](https://img.shields.io/github/v/release/skys-mission/hbr_mmd_tools?style=flat-square)](https://github.com/skys-mission/hbr_mmd_tools/releases)
[![License](https://img.shields.io/github/license/skys-mission/hbr_mmd_tools?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.13-blue?style=flat-square)]()
[![Pylint](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml)
[![CodeQL Advanced](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml)
[![Bandit](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml/badge.svg)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml)

**MikuMikuDance（MMD）ワークフロー向けの Blender アドオン。**
音声からリップシンクキーフレームを生成したり、自然なランダムまばたきを作成したり、ワンクリックでスマートなセルルックレンダリングを行ったり、MMD スタイルのキャラクター向けにシェイプキーを管理できます。

他の言語：[English](README.md), [简体中文](README_zh.md)

---

## 機能一覧

| 機能 | 説明 | 対応バージョン |
|---|---|---|
| **MMD リップシンク** | 音声のフォルマント・エネルギー分析により口形状キー（あいうえおん）を生成；ファイルまたは VSE タイムライン音声に対応 | v0.3 |
| **ランダムまばたき** | ガウス分布に基づく自然なまばたき。半まばたき・二重まばたき対応 | v0.5 |
| **スマートトゥーンレンダリング**（実験的） | ワンクリック EEVEE セルシェーディング：モデル検出、トゥーンマテリアル、アウトライン、ライティング＆軽量ポスト | v0.5.5 |
| **レンダープリセット** | 解像度、アスペクト比、画面方向のクイック設定 | v0.5 |
| **カメラ設定** | 焦点距離、絞り、被写界深度のプリセット | v0.5 |

## スクリーンショット

### リップシンク生成
![Lip Sync](.img/lip_sync.webp)
*モデル出典：KissshotSusu*

### ランダムまばたき
![Blink Settings](.img/blink_args.webp)

### レンダリング最適化（実験的）
> ワンクリック EEVEE セルシェーディング：MMD / VRM / 汎用モデルを自動検出、ポスタライズされたトゥーンマテリアル、リアルタイム Solidify アウトライン。

---

## ダウンロードとインストール

**GitHub Releases：** https://github.com/skys-mission/hbr_mmd_tools/releases

**インストール手順：**
1. 最新 Release の `.zip` ファイルをダウンロードします。
2. Blender で：`編集 → プリファレンス → アドオン → ディスクからインストール`。
3. ダウンロードした `.zip` を選択し、**HBR MMD Tools** を有効化します。

> **バージョン要件：** Blender **4.2 ～ 5.2**（Python 3.11 / 3.13）。手動テストは LTS 版のみ実施しています（[互換性](#互換性)参照）。

> **注意：** 現在のバージョンは **0.5.5** です。過去のバージョン（0.5.0 など）は [Releases](https://github.com/skys-mission/hbr_mmd_tools/releases) ページから入手できます。

---

## 使い方

### MMD リップシンク生成

音声のフォルマント分析により、口形状モーフキーフレーム（あ、い、う、え、お、ん）を生成します。

![リップシンク UI](.img/lips_gen2.0f.webp)

**操作手順：**
1. **Audio Source**（音声ソース）を選択：**File**（ディスク上の音声ファイル）または **Timeline**（ビデオシーケンスエディターの音声ストリップ）。
2. MMD モデル（またはその階層内の親オブジェクト）を選択します。
3. **システムコンソール**を開いて進捗を確認します（`ウィンドウ → システムコンソールの切り替え`）。
4. パラメータを調整して **Generate Lip Sync** をクリックします。
5. カーソルが通常に戻るまで待ちます。

**パラメータ説明：**

![パラメータパネル](.img/lips3.0.webp)

| パラメータ | 説明 |
|---|---|
| **Audio Source** | **File**：ディスクから音声を選択；**Timeline**：VSE タイムラインの音声ストリップを使用 |
| **Audio Strip** | Timeline 選択時のみ：名前でストリップを指定。生成時の開始フレームはストリップの開始位置に固定されます |
| **Start Frame** | 音声が始まるフレーム（Timeline 選択時はストリップによって決定） |
| **Preset** | 全体の口パクスタイル：**Natural**（滑らかでバランス良い）、**Clear Speech**（シャープな口の動き）、**Soft Motion**（小さく柔らかな動き） |

**Advanced（Custom Tuning）：** 既定ではプリセットに従います。**Custom Tuning** を有効にすると手動で微調整できます——

| パラメータ | 説明 |
|---|---|
| **DB Threshold** | dB ノイズゲート。認識が不正確なら上げ、認識できないなら下げます |
| **RMS Threshold** | RMS ノイズゲート。認識が不正確なら上げ、認識できないなら下げます |
| **Delayed Opening** | 口が完全に開くまでの遅延バッファ |
| **Speed Up Opening** | 認識開始から遅延開口までのカーブ速度 |
| **Max Morph Value** | モーフキーの数値上限 |

**Config：** シェイプキーのマッピング設定（同梱の `mmd` / `vrm` / `vrm0`）を選択するか、カスタム JSON をインポート。**Open Config Folder** でユーザー設定ファイルを直接管理できます。

**非 MMD モデルへの適応**

VRM 標準が定めるのは表情プリセット名のみで、シェイプキー名は規定されていません。インポートされたモデルは元のモーフ名をそのまま保持するため、まずモデル実際のシェイプキー名を確認してください：

- VRM 1.0 プリセット名（`aa` `ih` `ou` `ee` `oh`、まばたき `blink`）：同梱の `vrm.json` を選択
- VRM 0.x プリセット名（`A` `I` `U` `E` `O`、まばたき `Blink`）：同梱の `vrm0.json` を選択
- それ以外の命名（VRoid 出力の `..._Fcl_MTH_A` など）：シェイプキーをコピー/改名するか、カスタム設定をインポート

> **口型モーフキーが最低 1 つ必要です。** コピー方法は [copy_shape_key.md](docs/copy_shape_key.md) を参照してください。

---

### ランダムまばたき

`まばたき` モーフキーに自然なまばたきキーフレームを生成します。

**操作手順：**
1. MMD モデル（またはその階層内の親オブジェクト）を選択します。
2. **システムコンソール**を開いて進捗を確認します。
3. パラメータを調整して **Gen random blink** をクリックします。
4. カーソルが通常に戻るまで待ちます。

| パラメータ | 説明 |
|---|---|
| **start / end** | まばたきを生成するフレーム範囲 |
| **blink interval** | 平均まばたき間隔（秒） |
| **blinking wave ratio** | ランダム性係数（0–1） |
| **half blink ratio** | 半まばたきの確率（0=なし、1=常時）。二重まばたきはこの 2 倍の確率 |

> **警告：** この機能は選択したフレーム範囲内の `まばたき` キーフレームを上書きします。

---

### スマートトゥーンレンダリング（実験的）

MMD スタイルのキャラクター向けワンクリックセルシェーディング（EEVEE 専用、パフォーマンス優先）。

**パラメータ説明：**

| パラメータ | 説明 |
|---|---|
| **Toon Style** | **Standard**（定番の 2 トーン）、**Soft**（3 トーン、柔らかな影）、**Contrast**（ハードな 2 トーン、深い影） |
| **Outline** | **Solidify (Fast)**：リアルタイム反転ハルアウトライン（既定）；**Freestyle (Quality)**：トポロジ認識の線画、低速；**None** |
| **Outline Width** | 太さ係数（0.05–5.0、既定 0.15）。キャラクターの身長に応じて自動スケール。Solidify のみ |
| **Brightness** | 高度：明るさの自動検出を上書き（Auto / Light / Medium / Dark） |
| **Compositor Post** | 高度：軽量 Bloom とコントラストのポスト処理 |

**特徴：**
- **モデルタイプ検出** — MMD（mmd_tools インポート）/ VRM / 汎用モデルを自動判別し、それぞれに合ったベースカラー抽出を行います。
- **スマートトゥーンマテリアル** — 元のテクスチャを保持し、セマンティック分類（顔・髪・目・金属など）ごとに異なる階調を適用。顔は明るく、髪にはハイライト帯、目はほぼ自発光。
- **欠損回避** — テクスチャ欠損時はディフューズ色へ自動フォールバック。マテリアル無しメッシュには既定トゥーン材質を補完。アルファチャンネルは自動保持。
- **Solidify 反転ハルアウトライン** — EEVEE リアルタイムアウトライン（既定）。MMD の頂点ウェイト `mmd_edge_scale` を再利用。高品質 Freestyle も選択可能。
- **3 点トゥーンライティング** — キーの太陽光のみ影を投影。エリアライトは自動でキャラクターに照射。
- **軽量ポスト** — わずかなコントラストと低品質 Bloom。サンプル数は控えめ、レイトレーシングはオフ。

> **警告：** マテリアル変換はノードツリーを再構築します（Ctrl+Z で元に戻せます）。**Reset** ボタンは自動生成されたライト、アウトライン、ワールド、コンポジターを削除します。

---

## 互換性

### Blender バージョン

現バージョンは Blender **4.2 ～ 5.2** をサポート対象としています。手動テストは LTS 版（4.2 LTS / 4.5 LTS / 5.2 LTS）のみで実施しており、非 LTS 版は API 変更に対応済みですが、個別の実機検証は行っていません。

| バージョン | Python | 状態 |
|---|---|---|
| 4.2 LTS / 4.5 LTS | 3.11 | 対応済み（手動テスト済） |
| 5.2 LTS | 3.13 | 対応済み（手動テスト済） |
| 4.3 ～ 5.1（非 LTS） | 3.11 / 3.13 | サポート予定（手動テスト未実施） |
| < 4.2 / ≥ 5.3 | — | 非対応（実行時にブロック） |

### オペレーティングシステム

| OS | 状態 |
|---|---|
| Windows x64 | 対応済み |
| macOS ARM64 | 実験的対応 |
| Linux | 非対応（予定なし） |

---

## 開発

### ビルドと検査

```bash
# 静的解析（CI は 9.9 点以上を要求）
pip install pylint
pylint src/ --fail-under=9.9

# 単体テスト（純 Python モジュール、Blender 不要）
python3 -m unittest discover -s tests

# リリースパッケージのビルド（固定バージョンの FFmpeg を同梱、dist/ に出力）
python3 tools/build_release.py
```

### 注意事項

- 音声解析は Python 標準ライブラリのみで実装されています。バンドルされるバイナリは FFmpeg（任意の音声形式のデコード用）のみです。

### AI 支援開発

本プロジェクトは**vibe-coding**を多用したワークフロー（コード貢献率 70% 超）で開発されています。  
主な開発ツールは **Claude Code** ですが、コード生成バックエンドとして **Claude モデルは使用していません**。  
LLM 推論は主に **Kimi** と **DeepSeek** によって提供されています。

---

## ライセンス

[GPL-3.0](LICENSE)

## クレジット

| プロジェクト | リンク | ライセンス |
|---|---|---|
| FFmpeg | https://github.com/FFmpeg/FFmpeg | GPLv3（Releases に同梱のツールがこのライセンスを使用） |
