#!/usr/bin/env python
"""vigen pack.py — 批次生产效率工具（V3.23）。

子命令：
  freeze   <项目目录> [--out FILE]
      从 02/01/05 生成「冻结字段速查卡」（每项带源行号；禁止手改）。
  segment  <项目目录> --segment 段号 [--shots S1-S3] [--skeleton A|B] [--out FILE]
      生成自包含「段任务包」，供并行子代理直接使用（不读项目其他文件）。

只读项目文件，不写项目目录；输出到 stdout 或 --out 指定文件。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vigen_md import (
    DOC_FILES,
    Project,
    blocks,
    block_text,
    cell,
    iter_tables,
    round_ids,
    shot_blocks,
    sub_blocks,
    table_rows,
)

SKILL_ROOT = Path(__file__).resolve().parent.parent
PROMPT_RULES = SKILL_ROOT / "references" / "prompt-rules.md"
_ID_RE = re.compile(r"^((?:S|A)?)(\d+)([a-z]?)(?:v(\d+))?$")


def _has_id(text: str, sid: str) -> bool:
    """整词匹配镜号，避免 S1 命中 S1a/S10。"""
    return re.search(r"(?<![0-9A-Za-z])" + re.escape(sid) + r"(?![0-9A-Za-z])", text or "") is not None


def _seg_match(cell_text: str, segment: str) -> bool:
    def norm(value: str) -> str:
        value = value.strip()
        value = re.sub(r"^#+\s*", "", value)
        value = re.split(r"[（(]", value, maxsplit=1)[0].strip()
        if value.startswith("段落"):
            value = "段" + value[len("段落"):]
        return value

    return norm(cell_text) == norm(segment)


def _err(msg: str) -> int:
    print(msg, file=sys.stderr)
    return 2


def _find_table(doc: List[str], *names: str):
    for head_no, header, body in iter_tables(doc):
        if all(any(n in h for h in header) for n in names):
            return head_no, header, body
    return None


def _section_range(project: Project, key: str, heading: str) -> Tuple[int, int, List[str]]:
    rows = project.section(key, heading)
    if not rows:
        return 0, 0, []
    return rows[0][0], rows[-1][0], [t for _n, t in rows]


def _clean_section(lines: List[str], keep_tables: bool = True) -> List[str]:
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith(">") or s.startswith("#"):
            continue
        if not keep_tables and s.startswith("|"):
            continue
        out.append(ln)
    return out


def _value_row(doc: List[str], *keys: str) -> Tuple[int, str]:
    for head_no, header, body in iter_tables(doc):
        if len(header) < 2 or "项" not in header[0] or "值" not in header[1]:
            continue
        for no, cells in body:
            if len(cells) >= 2 and any(k in cells[0] for k in keys):
                return no, cells[1].strip()
    return 0, ""


def _subsections(project: Project, key: str, heading: str) -> List[Tuple[int, str, List[str]]]:
    """返回 [(起始行, 名称, 该节内容行)]。"""
    start, end, lines = _section_range(project, key, heading)
    if not lines:
        return []
    out = []
    cur_name = ""
    cur_line = start
    cur: List[str] = []
    for i, ln in enumerate(lines):
        if ln.startswith("### "):
            if cur_name:
                out.append((cur_line, cur_name, cur))
            cur_name = ln[4:].strip()
            cur_line = start + i
            cur = []
        elif cur_name:
            cur.append(ln)
    if cur_name:
        out.append((cur_line, cur_name, cur))
    return out


def _field(lines: List[str], *names: str) -> str:
    for ln in lines:
        s = ln.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) >= 2 and any(n in cells[0] for n in names):
            return cells[1]
    return ""


def _value_in_sections(project: Project, headings: Tuple[str, ...], *keys: str) -> Tuple[int, str]:
    """在指定节的「项|值」表里取值（不读项目状态卡快照）。"""
    for heading in headings:
        start, _end, lines = _section_range(project, "01", heading)
        for _head_no, header, body in iter_tables(lines):
            if len(header) < 2 or "项" not in header[0] or "值" not in header[1]:
                continue
            for no, cells in body:
                if len(cells) >= 2 and any(k in cells[0] for k in keys):
                    return start + no - 1, cells[1].strip()
    return 0, ""


def build_freeze_card(project: Project) -> str:
    doc02 = project.doc("02")
    if doc02 is None:
        raise ValueError("02 缺失，无法生成冻结字段速查卡")
    out: List[str] = ["# 冻结字段速查卡（pack.py freeze 生成；禁止手改；02/01/05 变更后重新生成）", ""]

    out.append("## 目标模型")
    for no, cells in _find_table(doc02, "用途", "模型")[2] if _find_table(doc02, "用途", "模型") else []:
        out.append("- %s：%s（02:%d）" % (cells[0] if cells else "", cells[1] if len(cells) > 1 else "", no))

    doc01 = project.doc("01")
    if doc01 is not None:
        lines_out = []
        for label in ("画幅", "时长模式", "时长上限", "成片时长", "总时长"):
            no, value = _value_in_sections(project, ("整体方案", "时长预算"), label)
            if value:
                lines_out.append("- %s：%s（01:%d）" % (label, value, no))
        if lines_out:
            out.append("\n## 项目口径")
            out.extend(lines_out)

    start, end, lines = _section_range(project, "02", "风格圣经")
    text = " ".join(x.strip() for x in _clean_section(lines, keep_tables=False))
    if text:
        out.append("\n## 风格圣经")
        out.append("- %s（02:%d-%d）" % (text, start, end))

    tbl = _find_table(doc02, "色号")
    if not tbl:
        start, end, lines = _section_range(project, "02", "色彩基调")
        rows = [ln.strip() for ln in lines if ln.strip().startswith("|")]
        if rows:
            out.append("\n## 色彩基调（02:%d-%d）" % (start, end))
            out.extend(rows)
    if tbl:
        out.append("\n## 色彩基调")
        for no, cells in tbl[2]:
            out.append("- %s（02:%d）" % (" / ".join(c for c in cells if c), no))

    for heading, label in (("角色锚定表", "角色锚定"), ("服装锚定表", "服装锚定"),
                           ("道具锚定表", "道具锚定"), ("群像锚定表", "群像锚定")):
        subs = _subsections(project, "02", heading)
        if not subs:
            continue
        out.append("\n## %s" % label)
        for no, name, lines in subs:
            phrase = _field(lines, "锚定短语") or _field(lines, "服装锚定短语") or _field(lines, "道具锚定短语")
            if phrase:
                out.append("- %s：%s（02:%d）" % (name, phrase, no))
            if heading == "道具锚定表":
                for fname in ("唯一实例定义", "开场状态", "状态转换点", "终态", "携带位置账"):
                    value = _field(lines, fname)
                    if value:
                        out.append("  - %s：%s" % (fname, value))

    start, end, lines = _section_range(project, "02", "全片负面清单")
    neg = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith(">") and not ln.strip().startswith("#")]
    if neg:
        out.append("\n## 全片负面清单（02:%d-%d）" % (start, end))
        out.append("\n".join(neg))

    doc05 = project.doc("05")
    if doc05 is not None:
        tbl = _find_table(doc05, "角色", "台词原文")
        if tbl:
            out.append("\n## 台词（05 逐句）")
            for no, cells in tbl[2]:
                out.append("- %s（05:%d）" % ("｜".join(c for c in cells if c), no))
    return "\n".join(out) + "\n"


def _expand_shots(spec: str) -> List[str]:
    out: List[str] = []
    for part in spec.replace("，", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = [x.strip() for x in part.split("-", 1)]
            ma, mb = _ID_RE.match(a), _ID_RE.match(b)
            if (ma and mb and ma.group(1) == mb.group(1)
                    and not ma.group(3) and not mb.group(3)
                    and ma.group(4) is None and mb.group(4) is None):
                for i in range(int(ma.group(2)), int(mb.group(2)) + 1):
                    out.append(ma.group(1) + str(i))
                continue
        out.append(part)
    return out


def _extract_skeleton(which: str) -> str:
    try:
        lines = PROMPT_RULES.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "（骨架全文缺失：找不到 references/prompt-rules.md）"
    marker = "### 骨架 %s" % which
    start = -1
    for i, ln in enumerate(lines):
        if ln.startswith(marker):
            start = i
            break
    if start < 0:
        return "（骨架 %s 未找到）" % which
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("### ") or lines[j].startswith("## "):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


def _previous_ending_frame(doc04: List[str], segment: str, shots: List[str]) -> str:
    """取本段之前一段的结尾帧；未定位到本段时不冒充。"""
    units = blocks(doc04, only_segments=True)
    if not units:
        units = [[(1, text)] for text in ["\n".join(doc04)]]
    texts = [block_text(b) for b in units]
    idx = -1
    for i, text in enumerate(texts):
        heading = text.splitlines()[0] if text.splitlines() else ""
        if (segment and _seg_match(heading, segment)) or any(_has_id(text, s) for s in shots):
            idx = i
            break
    if idx > 0:
        lines = [ln.strip() for ln in texts[idx - 1].splitlines()
                 if "结尾帧" in ln or "ENDING FRAME" in ln]
        return lines[-1] if lines else "（上一段未写结尾帧——人工确认）"
    if idx == 0:
        return "（本段为首段，无上一段尾帧）"
    return "（未能定位本段在 04 中的位置——不取未来段尾帧，人工确认）"


def build_segment_packet(project: Project, segment: str, shots_spec: Optional[str], skeleton: str) -> str:
    doc01 = project.doc("01")
    if doc01 is None:
        raise ValueError("01 缺失，无法生成段任务包")
    card_rows = table_rows(doc01, ("段号", "镜号"))
    cards = []
    if card_rows:
        for r in card_rows:
            if segment and not _seg_match(cell(r, "段号"), segment):
                continue
            cards.append(r)
    shots: List[str] = []
    if shots_spec:
        shots = _expand_shots(shots_spec)
    if segment:
        for r in cards:
            for s in _expand_shots(cell(r, "镜号")):
                if s not in shots:
                    shots.append(s)
    else:
        cards = [r for r in cards if any(_has_id(cell(r, "镜号"), s) for s in shots)]
    if not shots:
        raise ValueError("未找到段「%s」的镜号；请提供 --shots" % segment)

    storyboard = table_rows(doc01, ("镜号", "运镜"))
    story_rows = []
    if storyboard:
        for r in storyboard:
            if any(_has_id(cell(r, "镜号"), s) for s in shots):
                story_rows.append(r)
    beat_rows = table_rows(doc01, ("节拍号", "认领镜号"))
    beats = []
    if beat_rows:
        for r in beat_rows:
            if any(_has_id(cell(r, "认领镜号"), s) for s in shots):
                beats.append(r)
    plot_rows = table_rows(doc01, ("情节点", "覆盖镜号"))
    plots = []
    if plot_rows:
        for r in plot_rows:
            if any(_has_id(cell(r, "覆盖镜号"), s) for s in shots):
                plots.append(r)

    out: List[str] = []
    out.append("# 段任务包：%s（镜号：%s）" % (segment or "(按镜号)", "、".join(shots)))
    out.append("")
    out.append("## 0. 任务声明")
    out.append("只按本文件生产，不读其他项目文件、不读全库；产出原文返回。冻结字段一律从本文件复制，禁止手打。")
    out.append("")
    state_start, state_end, state_lines = _section_range(project, "01", "项目状态卡")
    out.append("## 1. 项目状态卡摘要（01:%d-%d）" % (state_start, state_end))
    if state_lines:
        out.extend([ln for ln in state_lines if ln.strip()])
    else:
        out.append("（未找到项目状态卡；按 3a/3e 的 01 记录执行）")
    out.append("")
    start, end, lines = _section_range(project, "02", "目标模型")
    if lines:
        out.append("## 2a. 目标模型（02:%d-%d）" % (start, end))
        out.extend([ln for ln in lines if ln.strip() and not ln.strip().startswith(">")])
        out.append("")
    doc02 = project.doc("02")
    if doc02 is not None:
        out.append("## 2. 02 锚定表全文（逐字；行号即源文件行号）")
        out.append("")
        out.append("```markdown")
        out.extend(doc02)
        out.append("```")
        out.append("")
    else:
        out.append("## 2. 02 锚定表")
        out.append("（02 缺失：轻量模式或未建锚定表；冻结字段以 01/03 为准）")
        out.append("")
    gate_start, gate_end, gate_lines = _section_range(project, "01", "GATE0 对齐记录")
    if gate_lines:
        out.append("## 3a. GATE0 对齐记录（01:%d-%d）" % (gate_start, gate_end))
        out.extend(gate_lines)
        out.append("")
    if story_rows:
        out.append("## 3b. 本段分镜行（01）")
        for r in story_rows:
            out.append("- 01:%d：%s" % (r.line, "｜".join("%s=%s" % (k, v) for k, v in r.cells.items() if v)))
        out.append("")
    if beats:
        out.append("## 3c. 本段节拍行（01）")
        for r in beats:
            out.append("- 01:%d：%s" % (r.line, "｜".join("%s=%s" % (k, v) for k, v in r.cells.items() if v)))
        out.append("")
    if plots:
        out.append("## 3d. 覆盖情节点（01）")
        for r in plots:
            out.append("- 01:%d：%s" % (r.line, "｜".join("%s=%s" % (k, v) for k, v in r.cells.items() if v)))
        out.append("")
    card_start = cards[0].line if cards else 0
    if cards:
        out.append("## 3e. 批次生产卡（01:%d）" % card_start)
        for r in cards:
            out.append("- 01:%d：%s" % (r.line, "｜".join("%s=%s" % (k, v) for k, v in r.cells.items() if v)))
        out.append("")
    combat_rounds: set[int] = set()
    for card in cards:
        decision = cell(card, "打斗判定")
        if decision.startswith("是"):
            combat_rounds.update(round_ids(decision))
    if combat_rounds:
        out.append("## 3f. 交手账回合（01）")
        ledger = project.section("01", "打斗交手账")
        if ledger:
            for _, header, rows in iter_tables([line for _, line in ledger]):
                if "回合" not in header:
                    continue
                round_column = header.index("回合")
                for row_no, cells in rows:
                    if len(cells) > round_column and round_ids(cells[round_column]) & combat_rounds:
                        out.append("- 01:%d：%s" % (ledger[row_no - 1][0], "｜".join(cells)))
        out.append("")
    doc05 = project.doc("05")
    if doc05 is not None:
        tbl = _find_table(doc05, "角色", "台词原文")
        if tbl:
            out.append("## 4. 05 台词摘录")
            for no, cells in tbl[2]:
                if any(_has_id(" ".join(cells), s) for s in shots):
                    out.append("- 05:%d：%s" % (no, "｜".join(c for c in cells if c)))
            out.append("")
    else:
        out.append("## 4. 05 台词")
        out.append("（无 05：无台词项目；本段按无台词、无旁白、无人声处理）")
        out.append("")
    doc04 = project.doc("04")
    if doc04 is not None:
        ending = _previous_ending_frame(doc04, segment, shots)
        out.append("## 5. 上一段结尾帧（ENDING FRAME）")
        out.append(ending)
        out.append("")
    out.append("## 6. 骨架 %s 全文" % skeleton)
    out.append(_extract_skeleton(skeleton))
    out.append("")
    out.append("## 7. 生产要求")
    out.append("- 填段生产卡/锁定清单九项/时间账/状态三问/走位总谱/动作桥/负面清单（按模型能力）")
    out.append("- 动作描述密度按 prompt-rules 0.13：默认意图级；峰值才展开秒级微操")
    out.append("- 不确定的字段回看本文件行号；禁止凭记忆手打冻结字段")
    out.append("")
    out.append("## 8. 源文件指纹")
    for key in ("01", "02", "05"):
        p = project.root / DOC_FILES[key]
        if p.is_file():
            st = p.stat()
            out.append("- %s：%d 行；mtime %s" % (
                DOC_FILES[key],
                len((project.doc(key) or [])),
                datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")))
        else:
            out.append("- %s：缺失" % DOC_FILES[key])
    return "\n".join(out) + "\n"


def main(argv: List[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    ap = argparse.ArgumentParser(description="vigen 批次生产效率工具（V3.23：段任务包/冻结字段速查卡）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_freeze = sub.add_parser("freeze", help="生成冻结字段速查卡")
    ap_freeze.add_argument("project_dir")
    ap_freeze.add_argument("--out", default=None)

    ap_seg = sub.add_parser("segment", help="生成段任务包")
    ap_seg.add_argument("project_dir")
    ap_seg.add_argument("--segment", default="", help="批次生产卡段号（如 段1）")
    ap_seg.add_argument("--shots", default=None, help="镜号范围/列表（S1-S3 / S1,S2 / A1v3）")
    ap_seg.add_argument("--skeleton", default="A", choices=["A", "B"])
    ap_seg.add_argument("--out", default=None)

    args = ap.parse_args(argv[1:])
    root = Path(args.project_dir)
    if not root.is_dir():
        return _err("项目目录不存在：%s" % root)
    project = Project(root)
    try:
        if args.cmd == "freeze":
            text = build_freeze_card(project)
        else:
            if not args.segment and not args.shots:
                return _err("segment 需要 --segment 或 --shots")
            text = build_segment_packet(project, args.segment, args.shots, args.skeleton)
    except ValueError as exc:
        return _err(str(exc))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print("written: %s" % args.out)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
