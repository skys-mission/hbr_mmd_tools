# HBR MMD Tools

[![Release](https://img.shields.io/github/v/release/skys-mission/hbr_mmd_tools?style=flat-square)](https://github.com/skys-mission/hbr_mmd_tools/releases)
[![License](https://img.shields.io/github/license/skys-mission/hbr_mmd_tools?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.13-blue?style=flat-square)]()
[![Pylint](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/pylint.yml)
[![CodeQL Advanced](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/codeql.yml)
[![Bandit](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml/badge.svg)](https://github.com/skys-mission/hbr_mmd_tools/actions/workflows/bandit.yml)

**MikuMikuDance（MMD）ワークフロー向けの Blender アドオン。**
音声からリップシンクキーフレームを生成したり、自然なランダムまばたきを作成したり、ワンクリックで PBR/NPR レンダリングを最適化したり、MMD スタイルのキャラクター向けにシェイプキーを管理できます。

他の言語：[English](README.md), [简体中文](README_zh.md)

---

## 機能一覧

| 機能 | 説明 | 対応バージョン |
|---|---|---|
| **MMD リップシンク** | 音声のフォルマント・エネルギー分析により口形状キー（あいうえおん）を生成；ファイルまたは VSE タイムライン音声に対応 | v0.3 |
| **ランダムまばたき** | ガウス分布に基づく自然なまばたき。半まばたき・二重まばたき対応 | v0.5 |
| **レンダリング最適化**（実験的） | ワンクリックで適応的ライティング、PBR/NPR マテリアル強化、ワールド＆コンポジター設定 | v0.5 |
| **レンダープリセット** | 解像度、アスペクト比、画面方向のクイック設定 | v0.5 |
| **カメラ設定** | 焦点距離、絞り、被写界深度のプリセット | v0.5 |

## スクリーンショット

### リップシンク生成
![Lip Sync](.img/lip_sync.webp)
*モデル出典：KissshotSusu*

### ランダムまばたき
![Blink Settings](.img/blink_args.webp)

### レンダリング最適化（実験的）
> EEVEE / Cycles のワンクリック設定、適応的 6 点ライティングとスマートマテリアル分類。

---

## ダウンロードとインストール

**GitHub Releases：** https://github.com/skys-mission/hbr_mmd_tools/releases

**インストール手順：**
1. 最新 Release の `.zip` ファイルをダウンロードします。
2. Blender で：`編集 → プリファレンス → アドオン → ディスクからインストール`。
3. ダウンロードした `.zip` を選択し、**HBR MMD Tools** を有効化します。

> **バージョン要件：** Blender **4.2 LTS ～ 5.2 LTS**（Python 3.11 / 3.13）。

> **注意：** 現在のバージョンは **0.5.1-preview** です。安定版が必要な場合は **0.5.0** をご利用ください。0.5.1 の正式版はリリースせず、次の正式版は **0.5.5** として直接リリースされます。

---

## 使い方

### MMD リップシンク生成

音声のフォルマント分析により、口形状モーフキーフレーム（あ、い、う、え、お、ん）を生成します。

![リップシンク UI](.img/lips_gen2.0f.webp)

**操作手順：**
1. 音声ファイルを選択するか、ビデオシーケンスエディターの音声ストリップを使用します。
2. MMD モデル（またはその階層内の親オブジェクト）を選択します。
3. **システムコンソール**を開いて進捗を確認します（`ウィンドウ → システムコンソールの切り替え`）。
4. パラメータを調整して**生成**をクリックします。
5. カーソルが通常に戻るまで待ちます。

**パラメータ説明：**

![パラメータパネル](.img/lips3.0.webp)

| パラメータ | 説明 |
|---|---|
| **開始フレーム** | 音声が始まるフレーム位置 |
| **DB しきい値** | dB ノイズゲート。認識が不正確なら上げ、認識できないなら下げます |
| **RMS しきい値** | RMS ノイズゲート。認識が不正確なら上げ、認識できないなら下げます |
| **遅延開口比率** | 口が完全に開くまでの遅延比率 |
| **開口速度** | 認識開始から遅延開口までのカーブ速度 |
| **モーフキー最大値** | モーフキーの数値上限 |

**非 MMD モデルへの適応**

VRM などのモデルでは、以下のモーフキーが存在することを確認してください（既存のモーフキーをコピーして改名も可能です）：

| MMD 名称 | 対応 |
|---|---|
| あ | A |
| い | I |
| う | U |
| え | E |
| お | O |
| ん | N |

> **「あ」が最低 1 つ必要です。** コピー方法は [copy_shape_key.md](docs/copy_shape_key.md) を参照してください。

---

### ランダムまばたき

`まばたき` モーフキーに自然なまばたきキーフレームを生成します。

**操作手順：**
1. MMD モデル（またはその階層内の親オブジェクト）を選択します。
2. **システムコンソール**を開いて進捗を確認します。
3. パラメータを調整して**生成**をクリックします。
4. カーソルが通常に戻るまで待ちます。

| パラメータ | 説明 |
|---|---|
| **まばたき間隔** | 平均まばたき間隔（秒） |
| **波動比率** | ランダム性係数（0.01–1.0） |

> **警告：** この機能は選択したフレーム範囲内の `まばたき` キーフレームを上書きします。

---

### レンダリング最適化（実験的）

MMD スタイルのキャラクター向けワンクリックレンダリング設定です。

**プリセット：**
- **PBR** — リアルなレンダリング。肌、髪、金属、布などのマテリアル質感を強化します。
- **PBR Aggressive** — より強いマテリアル差異。ドラマチックな照明向けです。
- **NPR** — トゥーンシェーディング。Freestyle のアウトラインに対応しています。

**特徴：**
- **適応的 6 点ライティング** — キャラクターの身長に基づいてキー、フィル、リム、ヘア、バック、フロントライトを自動配置します。
- **スマートマテリアル分類** — 肌、髪、金属、宝石、目、布などを自動検出し、調整済みの Principled BSDF パラメータを適用します。
- **トーン感知ワールド** — モデルの色彩分析に基づいて、クール/ウォーム/ニュートラルのワールド環境を自動設定します。
- **コンポジター設定** — ビネットとカラーグレーディングノードを自動追加します。
- **レンダーエンジン選択** — EEVEE または Cycles。

> **警告：** この機能は自動命名のライトとワールドノードを作成します。**リセット**ボタンで削除できます。

---

## 互換性

### Blender バージョン

| バージョン | Python | 状態 |
|---|---|---|
| 4.2 LTS – 4.5 LTS | 3.11 | 対応済み |
| 5.0 – 5.2 LTS | 3.11 / 3.13 | 対応済み（実機検証待ち） |
| < 4.2 | — | 非対応 |

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
pip install pylint
pylint src/ --fail-under=9.9
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
