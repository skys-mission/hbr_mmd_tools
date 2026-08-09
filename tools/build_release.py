# -*- coding: utf-8 -*-
# Copyright (c) 2026, https://github.com/skys-mission and Half-Bottled Reverie
"""构建 release 压缩包（内嵌固定版本的 FFmpeg 二进制）。

用法 / Usage:
    python3 tools/build_release.py [--tag vX.Y.Z] [--platform win-x64|mac-arm64]

流程 / Pipeline:
    1. 从 blender_manifest.toml 读取版本号，生成 zip 文件名。
    2. 按 tools/ffmpeg_sources.json 下载并校验（sha256）两个平台的 FFmpeg。
    3. git archive HEAD 导出干净源码（只含 git 跟踪文件），
       注入 src/audio/lib/ffmpeg[.exe] 后打成 zip 到 dist/。
    4. 输出各 zip 的 sha256，并生成 dist/release_notes.md。

只依赖 Python 标准库（兼容 Python 3.9+）与 git 命令。
"""

import argparse
import contextlib
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "blender_manifest.toml"
SOURCES_PATH = Path(__file__).resolve().parent / "ffmpeg_sources.json"
DIST_DIR = REPO_ROOT / "dist"
CACHE_DIR = DIST_DIR / ".cache"

ADDON_DIR_NAME = "hbr_mmd_tools"
FFMPEG_LIB_PREFIX = ADDON_DIR_NAME + "/src/audio/lib"
REPO_URL = "https://github.com/skys-mission/hbr_mmd_tools"

DOWNLOAD_TIMEOUT = 600
USER_AGENT = "hbr-mmd-tools-release-build"


def read_manifest():
    """从 blender_manifest.toml 读取 id/version/blender 版本范围。

    只需几个顶层字段，为避免依赖 Python 3.11 的 tomllib 而使用行解析。
    """
    keys = ("id", "version", "blender_version_min", "blender_version_max")
    values = {}
    for line in MANIFEST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        match = re.match(r'^(\w+)\s*=\s*"([^"]+)"', line)
        if match and match.group(1) in keys:
            values[match.group(1)] = match.group(2)
    missing = [key for key in keys if key not in values]
    if missing:
        raise RuntimeError(f"blender_manifest.toml 缺少字段: {', '.join(missing)}")
    return values


def load_sources():
    """读取 FFmpeg 下载源清单。"""
    with SOURCES_PATH.open(encoding="utf-8") as file_obj:
        return json.load(file_obj)


def sha256_file(path):
    """计算文件的 sha256。"""
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def short_version(version):
    """'4.2.0' -> '4.2'，用于 zip 文件名里的 Blender 版本范围。"""
    parts = version.split(".")
    return ".".join(parts[:2])


def warn_dirty_worktree():
    """工作区有未提交改动时告警（git archive 只包含已提交内容）。"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    if result.stdout.strip():
        print("警告: 工作区存在未提交改动，zip 只包含 HEAD 中已提交的内容。")


def check_tag(tag, manifest_version):
    """校验 tag 与 manifest 版本一致（tag 允许带 -preview 之类后缀）。"""
    tag_core = tag.lstrip("v").split("-")[0]
    if tag_core != manifest_version:
        raise RuntimeError(
            f"tag {tag} 与 blender_manifest.toml 版本 {manifest_version} 不一致"
        )


def download(url, dest, expected_sha256):
    """下载 url 到 dest（已存在且校验通过则跳过），强制校验 sha256。"""
    if dest.is_file() and sha256_file(dest) == expected_sha256:
        print(f"使用缓存: {dest.name}")
        return
    print(f"下载: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response, \
            dest.open("wb") as file_obj:
        shutil.copyfileobj(response, file_obj)
    actual = sha256_file(dest)
    if actual != expected_sha256:
        dest.unlink()
        raise RuntimeError(
            f"sha256 校验失败: {url}\n  期望: {expected_sha256}\n  实际: {actual}"
        )


def prepare_binary(platform_key, source):
    """下载源压缩包并解出其中的 ffmpeg 二进制，返回二进制路径。"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = CACHE_DIR / f"{platform_key}-{source['sha256'][:12]}.zip"
    download(source["url"], archive_path, source["sha256"])

    binary_path = CACHE_DIR / f"{platform_key}-{source['binary_name']}"
    with zipfile.ZipFile(archive_path) as archive:
        try:
            member = archive.getinfo(source["archive_member"])
        except KeyError as exc:
            raise RuntimeError(
                f"压缩包内未找到 {source['archive_member']}: {archive_path}"
            ) from exc
        with archive.open(member) as src, binary_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    binary_path.chmod(0o755)
    return binary_path


@contextlib.contextmanager
def open_git_archive():
    """以 tar 形式导出 git HEAD（带顶层目录前缀），产出只读 tarfile 对象。"""
    result = subprocess.run(
        ["git", "archive", "--format=tar", f"--prefix={ADDON_DIR_NAME}/", "HEAD"],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )
    archive = tarfile.open(fileobj=io.BytesIO(result.stdout))
    try:
        yield archive
    finally:
        archive.close()


def build_platform_zip(platform_key, source, zip_path):
    """打出单个平台的 zip：git 跟踪文件 + 注入的 ffmpeg 二进制。"""
    binary_path = prepare_binary(platform_key, source)
    binary_arcname = f"{FFMPEG_LIB_PREFIX}/{source['binary_name']}"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_obj:
        with open_git_archive() as archive:
            for member in archive:
                # zip 不需要显式目录条目（git 也不跟踪空目录）
                if member.isdir():
                    continue
                zip_info = zipfile.ZipInfo(
                    member.name, date_time=time.gmtime(member.mtime)[:6]
                )
                zip_info.external_attr = member.mode << 16
                src = archive.extractfile(member)
                with zip_obj.open(zip_info, "w") as dst:
                    shutil.copyfileobj(src, dst)

        zip_info = zipfile.ZipInfo(binary_arcname)
        zip_info.external_attr = 0o755 << 16
        with binary_path.open("rb") as src, zip_obj.open(zip_info, "w") as dst:
            shutil.copyfileobj(src, dst)


def find_previous_tag(current_tag):
    """取当前 tag 之前的最近一个 tag，用于生成 Full Changelog 链接。"""
    result = subprocess.run(
        ["git", "tag", "--sort=-v:refname"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    tags = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    for tag in tags:
        if tag != current_tag:
            return tag
    return None


def write_release_notes(manifest, built, tag):
    """生成 dist/release_notes.md（Full Changelog 链接 + SHA256 表格）。"""
    version = manifest["version"]
    lines = [f"# HBR MMD Tools v{version}", ""]
    if tag:
        previous = find_previous_tag(tag)
        if previous:
            compare = f"{REPO_URL}/compare/{previous}...{tag}"
            lines += [f"**Full Changelog**: `{previous}...{tag}` ({compare})", ""]
    lines += [
        "<!-- 在此补充更新说明 / What's New / 新機能 -->",
        "",
        "---",
        "",
        "| SHA256 | FileName |",
        "|---|---|",
    ]
    for zip_path, digest in built:
        lines.append(f"| {digest} | {zip_path.name} |")
    lines.append("")

    notes_path = DIST_DIR / "release_notes.md"
    notes_path.write_text("\n".join(lines), encoding="utf-8")
    return notes_path


def main(argv=None):
    """入口：解析参数并构建所有目标平台的 zip。"""
    parser = argparse.ArgumentParser(description="构建 HBR MMD Tools release 压缩包")
    parser.add_argument(
        "--tag", help="发布 tag（如 v0.5.1），用于版本校验与更新日志链接"
    )
    parser.add_argument(
        "--platform", choices=("win-x64", "mac-arm64"),
        help="只构建指定平台（默认两个都构建）",
    )
    args = parser.parse_args(argv)

    manifest = read_manifest()
    if manifest["id"] != ADDON_DIR_NAME:
        raise RuntimeError(f"manifest id 与目录名不一致: {manifest['id']}")
    if args.tag:
        check_tag(args.tag, manifest["version"])
    warn_dirty_worktree()

    sources = load_sources()
    platforms = [args.platform] if args.platform else list(sources["platforms"])
    bl_suffix = (
        f"bl{short_version(manifest['blender_version_min'])}"
        f"_{short_version(manifest['blender_version_max'])}"
    )

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    built = []
    for platform_key in platforms:
        source = sources["platforms"][platform_key]
        zip_name = (
            f"{ADDON_DIR_NAME}-v{manifest['version']}-{platform_key}-{bl_suffix}.zip"
        )
        zip_path = DIST_DIR / zip_name
        print(f"构建: {zip_name}")
        build_platform_zip(platform_key, source, zip_path)
        digest = sha256_file(zip_path)
        built.append((zip_path, digest))
        print(f"  sha256: {digest}")

    notes_path = write_release_notes(manifest, built, args.tag)
    print(f"release notes 模板: {notes_path}")
    print("完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
