#!/usr/bin/env python
"""vigen lint_docs.py — 文档归属与门名一致性检查（V3.24）。

检查项：
  1. SKILL 规则归属表 / Module Map 提到的 references/、assets/ 文件都存在；
  2. references/ 与 assets/ 下每个 .md 都在 SKILL 里被提到（孤儿文件）；
  3. 文档中 `--gate <ID>` 的门名在 check.py 注册表内（K18 作为 A20 旧名放行）；
  4. 跨文件重复的二级/三级标题（疑似规则重复；警告，可用 --strict 升级为错误）。
只读；exit 0=通过（可有警告），1=有错误，2=用法错误。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "SKILL.md"
RUNTIME_DIRS = ["references", "assets"]
GATE_RE = re.compile(r"--gate\s+([A-Za-z]\d+)")
HEADING_RE = re.compile(r"^(##|###)\s+(.+)$")
# 已知跨文件重复且合理的标题（模板与规则各自视角）
HEADING_ALLOW = {
    "目标模型",
    "场景锚定表",
    "道具锚定表",
    "角色锚定表",
    "服装锚定表",
    "群像锚定表",
    "色彩基调",
    "风格圣经",
}


def registry_gates() -> Tuple[set, set]:
    sys.path.insert(0, str(ROOT / "scripts"))
    import check  # noqa: WPS433 — 只为读取注册表

    default = {gid for gid, _fn in check.GATES}
    optional = {gid for gid, _fn in check.OPTIONAL_GATES}
    return default, optional


def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8").splitlines()


def mentioned_paths(skill_text: str) -> set:
    out = set()
    for m in re.finditer(r"(references/[A-Za-z0-9_\-]+\.md|assets/[A-Za-z0-9_\-]+\.md)", skill_text):
        out.add(m.group(1))
    return out


def main(argv: List[str]) -> int:
    strict = "--strict" in argv[1:]
    errors: List[str] = []
    warnings: List[str] = []

    if not SKILL.is_file():
        print("SKILL.md 不存在")
        return 2
    skill_text = SKILL.read_text(encoding="utf-8")
    mentioned = mentioned_paths(skill_text)
    # 扩展库由 knowledge-index 路由，不直接列在 SKILL Module Map
    index_path = ROOT / "references" / "knowledge-index.md"
    if index_path.is_file():
        mentioned |= mentioned_paths(index_path.read_text(encoding="utf-8"))

    # 1. SKILL 提到的文件必须存在
    for rel in sorted(mentioned):
        if not (ROOT / rel).is_file():
            errors.append("SKILL 提到的文件不存在：%s" % rel)

    # 2. 运行时目录下每个 md 都应被 SKILL 提到（归档/学习类除外）
    skip = {"_archive-suspended-claims.md", "learning-guide.md"}
    for dirname in RUNTIME_DIRS:
        for path in sorted((ROOT / dirname).glob("*.md")):
            rel = "%s/%s" % (dirname, path.name)
            if path.name in skip:
                continue
            if rel not in mentioned:
                errors.append("孤儿文件（SKILL 未提到）：%s" % rel)

    # 3. 门名一致性
    default, optional = registry_gates()
    known = default | optional
    for path in [SKILL] + [p for d in RUNTIME_DIRS for p in sorted((ROOT / d).glob("*.md"))]:
        for no, line in enumerate(read_lines(path), start=1):
            for gid in GATE_RE.findall(line):
                gid = gid.upper()
                if gid == "K18":  # A20 旧名，兼容
                    continue
                if gid not in known:
                    errors.append("%s:%d 引用了未注册的门 %s" % (path.relative_to(ROOT), no, gid))

    # 4. 跨文件重复标题（警告）
    titles: Dict[str, List[str]] = {}
    for dirname in RUNTIME_DIRS:
        for path in sorted((ROOT / dirname).glob("*.md")):
            if path.name in skip:
                continue
            for no, line in enumerate(read_lines(path), start=1):
                m = HEADING_RE.match(line)
                if not m:
                    continue
                title = m.group(2).strip()
                if len(title) < 6 or title in HEADING_ALLOW:
                    continue
                titles.setdefault(title, []).append("%s:%d" % (path.relative_to(ROOT), no))
    for title, locations in sorted(titles.items()):
        if len(locations) > 1:
            warnings.append("重复标题「%s」：%s" % (title, "、".join(locations)))

    for w in warnings:
        print("警告：" + w)
    for e in errors:
        print("错误：" + e)
    if errors or (strict and warnings):
        print("lint: %d 错误 / %d 警告" % (len(errors), len(warnings)))
        return 1
    print("lint: 通过（%d 警告）" % len(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
