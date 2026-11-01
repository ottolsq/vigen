#!/usr/bin/env python
"""vigen check.py — 项目文件机械校验（薄校验层，裁定 R1）。

只 enforce 机械可判定的门（K1-K10），不查审美。宁松勿滥：
误拦的门比没有门更糟——只收零歧义条款。

纪律（SKILL.md 硬规则 15）：本脚本只 enforce 文档已写的门；
改门必同步改本脚本。enforce 的文档条款清单：

- K1 台词逐字        → SKILL.md 硬规则4 / prompt-rules A11
- K2 时长            → prompt-rules A2/A3
- K3 锚定逐字        → prompt-rules A1
- K4 稳定镜号        → SKILL.md 稳定镜号规则
- K5 强调手段配额    → prompt-rules B3 / cinematography「峰值与强调手段」
- K6 运镜条件门      → prompt-rules A12 / cinematography 决策表+五类词表
- K7 环境动态层      → prompt-rules B13
- K8 骨架槽位        → prompt-rules 硬规则1/10
- K9 情节点覆盖      → SKILL.md 硬规则7
- K10 PLAN/REF 闭环  → SKILL.md E2 / prompt-rules CT5

用法（CT6）：
    python scripts/check.py <项目目录> [--partial] [--gate K5]
exit: 0=全过 1=有findings 2=用法/IO错
输出行格式：[K1] 04_视频提示词.md:123: <具体缺什么>
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

MINIMUM_PYTHON = (3, 9)

DOC_FILES = {
    "00": "00_剧情状态.md",
    "01": "01_方案与剧本.md",
    "02": "02_锚定表.md",
    "03": "03_图片提示词.md",
    "04": "04_视频提示词.md",
    "05": "05_语音台词表.md",
    "06": "06_剪辑清单.md",
}


@dataclass(frozen=True)
class Finding:
    gate: str    # "K1".."K10"
    file: str    # "01_方案与剧本.md" 等
    line: int    # 1-based；0=文件级
    message: str  # 具体到"缺什么"


class Project:
    """项目目录加载与解析缓存。"""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._cache: dict = {}

    def path(self, key: str) -> Path:
        return self.root / DOC_FILES[key]

    def doc(self, key: str) -> Optional[List[str]]:
        """key ∈ {"00".."06"}；文件不存在返回 None（--partial 容忍）。"""
        if key in self._cache:
            return self._cache[key]
        p = self.path(key)
        if not p.is_file():
            self._cache[key] = None
            return None
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            self._cache[key] = None
            return None
        lines = text.splitlines()
        self._cache[key] = lines
        return lines

    def section(self, key: str, heading: str) -> List[Tuple[int, str]]:
        """返回 '## heading'（前缀匹配）到下一个 '## ' 之间的行，
        元素为 (1-based 行号, 行文本)。heading 不带 '## ' 前缀。"""
        lines = self.doc(key)
        if lines is None:
            return []
        out: List[Tuple[int, str]] = []
        inside = False
        for i, ln in enumerate(lines, start=1):
            if ln.startswith("## "):
                if inside:
                    break
                inside = ln[3:].strip().startswith(heading)
                continue
            if inside:
                out.append((i, ln))
        return out


# ---------------------------------------------------------------- K1 台词逐字

# 01 分场剧本节的说话人行：名字（≤12 非空白字符）+ 全角冒号 + 内容
_DIALOGUE_LINE_RE = re.compile(r"^(\S{1,12})：(.+)$")
# SCR-18 防误判：以这些词开头的"名字"是动作段/结构行，不是说话人
_ACTION_PREFIXES = ("第", "格", "镜", "段", "场景状态", "场景", "镜头")
# 04 台词：三种引号内的文本
_QUOTED_RE = re.compile(r'"([^"]+)"|“([^”]+)”|「([^」]+)」')


def _is_dialogue_line(line: str) -> bool:
    """判断一行是否为 01 的说话人台词行（SCR-18：排除全角冒号开头的动作段）。"""
    m = _DIALOGUE_LINE_RE.match(line.strip())
    if not m:
        return False
    speaker = m.group(1)
    for pre in _ACTION_PREFIXES:
        if speaker.startswith(pre):
            return False
    return True


def _clean_dialogue(text: str) -> str:
    """去首尾空白与句末标点差异前的规范化：只去首尾空白（逐字=字符级一致）。"""
    return text.strip()


def _dialogue_set_01(project: Project) -> set:
    """01 分场剧本节的台词集合（去首尾空白）。"""
    out = set()
    for _, ln in project.section("01", "分场剧本"):
        if _is_dialogue_line(ln):
            content = _DIALOGUE_LINE_RE.match(ln.strip()).group(2)
            out.add(_clean_dialogue(content))
    return out


def _quoted_lines(key: str, project: Project) -> List[Tuple[int, str, str]]:
    """返回 (行号, 引号内文本, 所属文件名) 列表——跳过表格行/声明行。"""
    out = []
    lines = project.doc(key)
    if lines is None:
        return out
    fname = DOC_FILES[key]
    for i, ln in enumerate(lines, start=1):
        if ln.startswith(">") or ln.startswith("|"):
            continue
        for m in _QUOTED_RE.finditer(ln):
            text = next(g for g in m.groups() if g is not None)
            out.append((i, text, fname))
    return out


def _dialogue_rows_05(project: Project) -> List[Tuple[int, str]]:
    """05 台词清单表：返回 (行号, 台词原文列)。表头含'台词原文'才解析。"""
    out = []
    lines = project.doc("05")
    if lines is None:
        return out
    col = -1
    for i, ln in enumerate(lines, start=1):
        if not ln.startswith("|"):
            col = -1
            continue
        cells = [c.strip() for c in ln.split("|")[1:-1]]
        if "台词原文" in cells:
            col = cells.index("台词原文")
            continue
        if col >= 0 and len(cells) > col and not set(cells[0]) <= {"-", " ", ":"}:
            v = cells[col]
            if v and not v.startswith("{"):
                out.append((i, v))
    return out


def gate_k1(project: Project, partial: bool) -> List[Finding]:
    """K1 台词逐字：04/05 每句台词必须逐字存在于 01 定稿台词集合。"""
    if project.doc("01") is None:
        return []
    base = _dialogue_set_01(project)
    findings: List[Finding] = []

    if project.doc("04") is not None:
        for line_no, text, fname in _quoted_lines("04", project):
            t = _clean_dialogue(text)
            if not t:
                continue
            if t in base:
                continue
            # 引号内容不一定是台词（可能是提示词短语）——只有整行含
            # 说话/语气语境词才算台词候选，宁松勿滥
            row = project.doc("04")[line_no - 1]
            if not re.search(r"：\"|：\"|说|语气|情绪|画外音|（", row):
                continue
            findings.append(Finding(
                "K1", fname, line_no,
                "台词与01定稿不一致：「%s」（01 定稿中无此句——改写/修订后须从 01 逐字搬运）" % t))

    if project.doc("05") is not None:
        for line_no, text in _dialogue_rows_05(project):
            t = _clean_dialogue(text)
            if not t or t in base:
                continue
            findings.append(Finding(
                "K1", DOC_FILES["05"], line_no,
                "台词与01定稿不一致：「%s」（05 台词总账须与 01 逐字一致）" % t))
    return findings


GATES: List[Tuple[str, Callable[[Project, bool], List[Finding]]]] = [
    ("K1", gate_k1),
]


def main(argv: List[str]) -> int:
    # Windows GBK 控制台兼容：强制 UTF-8 输出（reconfigure 仅 3.7+，3.9 下限内安全）
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    if sys.version_info < MINIMUM_PYTHON:
        print("check.py requires Python %d.%d+, running %d.%d" % (
            MINIMUM_PYTHON[0], MINIMUM_PYTHON[1],
            sys.version_info[0], sys.version_info[1]))
        return 2
    ap = argparse.ArgumentParser(description="vigen 项目文件机械校验（K1-K10）")
    ap.add_argument("project_dir", help="项目目录（含 01-06 Markdown）")
    ap.add_argument("--partial", action="store_true",
                    help="只核对已有文档；依赖文件缺失的门静默跳过")
    ap.add_argument("--gate", default=None, help="只跑指定门（如 K5）")
    args = ap.parse_args(argv[1:])

    root = Path(args.project_dir)
    if not root.is_dir():
        print("项目目录不存在或未按 01-06 契约组织：%s" % root)
        return 2
    project = Project(root)
    if project.doc("01") is None and project.doc("04") is None:
        print("项目目录内无 01/04 文件——未按 vigen 01-06 契约组织，跳过")
        return 2

    findings: List[Finding] = []
    for gate_id, gate_fn in GATES:
        if args.gate and gate_id != args.gate:
            continue
        findings.extend(gate_fn(project, args.partial))

    for f in findings:
        loc = "%s:%d" % (f.file, f.line) if f.line else f.file
        print("[%s] %s: %s" % (f.gate, loc, f.message))
    if findings:
        print("check: %d 项未通过（不过不进下一阶段——SKILL.md 硬规则 15）" % len(findings))
        return 1
    print("check: 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
