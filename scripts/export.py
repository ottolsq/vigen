#!/usr/bin/env python
"""vigen export.py — 项目交付打包（当前状态快照）。

把项目里「可交付的创作文档 + 成品」复制到项目之外的目录，并附
`manifest.json`（逐文件 sha256/大小）与 `checksums.sha256`（sha256sum 格式）。

明确**不**做：
  - 不打包私有输入（`输入/`）、交付目录（`交付/`）、隐藏运行状态（`.short-drama/`）
  - 不声称任何审批（manifest 里 `asserts_approval` 恒为 false）
  - 不改动项目内任何文件（纯只读 + 复制）

用法：
    python export.py <项目目录> --out <项目外目录>
                      [--episode EP001 ...] [--no-media] [--overwrite]
exit: 0=成功 2=用法/IO错
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MINIMUM_PYTHON = (3, 9)

# 项目根下按 01-06 契约命名的可交付文档
DOC_PREFIXES = ("00_", "01_", "02_", "03_", "04_", "05_", "06_")
# 每集目录（系列项目）里额外可交付的文档
EPISODE_DOC_NAMES = ("剧本.md", "视觉设定.md", "分镜.md", "图片提示词.md",
                     "视频提示词.md", "剪辑单.md")
# 永不打包的目录/文件
EXCLUDED_DIRS = {"输入", "交付", ".short-drama", ".superpowers", "__pycache__",
                 "node_modules", ".git"}
MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov",
                  ".mkv", ".webm", ".wav", ".mp3", ".m4a", ".flac", ".aac"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_media(path: Path) -> bool:
    return path.suffix.lower() in MEDIA_SUFFIXES


def collect(project: Path, episodes: Optional[List[str]], include_media: bool) -> List[Path]:
    """收集要交付的文件（相对项目根）。"""
    picked: List[Path] = []
    for entry in sorted(project.iterdir()):
        name = entry.name
        if entry.is_dir():
            if name in EXCLUDED_DIRS:
                continue
            # 系列项目：剧集/<EP>/ 或 epNN/ 每集目录
            is_ep_dir = episodes is not None and name in episodes
            in_series = entry.name in ("剧集", "episodes") or name.lower().startswith("ep")
            if in_series or is_ep_dir:
                for sub in sorted(entry.rglob("*")):
                    if sub.is_file() and not any(part in EXCLUDED_DIRS for part in sub.relative_to(project).parts):
                        if not include_media and is_media(sub):
                            continue
                        picked.append(sub.relative_to(project))
            continue
        if not entry.is_file():
            continue
        if name.startswith(DOC_PREFIXES) and entry.suffix.lower() == ".md":
            picked.append(entry.relative_to(project))
        elif name in EPISODE_DOC_NAMES:
            picked.append(entry.relative_to(project))
    if episodes:
        picked = [p for p in picked
                  if not p.parts[0].lower().startswith("ep") or p.parts[0] in episodes
                  or p.parts[0] in ("剧集", "episodes")]
    return picked


def main(argv: List[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    if sys.version_info < MINIMUM_PYTHON:
        print("export.py requires Python %d.%d+" % MINIMUM_PYTHON)
        return 2

    ap = argparse.ArgumentParser(description="vigen 项目交付打包（当前状态快照）")
    ap.add_argument("project_dir")
    ap.add_argument("--out", required=True, help="输出目录（必须在项目之外）")
    ap.add_argument("--episode", action="append", default=None, help="只导出指定集，可重复")
    ap.add_argument("--no-media", action="store_true", help="只导出文字，不含图片/视频/音频")
    ap.add_argument("--overwrite", action="store_true", help="覆盖已存在的输出目录")
    args = ap.parse_args(argv[1:])

    project = Path(args.project_dir).resolve()
    out = Path(args.out).resolve()
    if not project.is_dir():
        print("项目目录不存在：%s" % project)
        return 2
    if out == project or project in out.parents:
        print("--out 必须在项目之外（当前：%s）" % out)
        return 2
    if out.exists() and any(out.iterdir()) and not args.overwrite:
        print("输出目录非空：%s（加 --overwrite 覆盖）" % out)
        return 2

    files = collect(project, args.episode, not args.no_media)
    if not files:
        print("没有可导出的文件——项目未按 01-06 契约组织？")
        return 2

    if out.exists() and args.overwrite:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    entries: List[Dict[str, object]] = []
    checksums: List[Tuple[str, str]] = []
    for rel in files:
        src = project / rel
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        digest = sha256_of(dst)
        entries.append({"path": rel.as_posix(), "sha256": digest, "size": dst.stat().st_size})
        checksums.append((digest, rel.as_posix()))

    manifest = {
        "tool": "vigen export",
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": project.name,
        "episodes": args.episode,
        "media_included": not args.no_media,
        "asserts_approval": False,
        "note": "当前状态快照：不代表任何审查通过或创作者接受。",
        "files": entries,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "checksums.sha256").write_text(
        "".join("%s  %s\n" % (h, p) for h, p in sorted(checksums, key=lambda x: x[1])),
        encoding="utf-8")

    print("已导出 %d 个文件 → %s" % (len(entries), out))
    print("清单：manifest.json / checksums.sha256（asserts_approval=false）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
