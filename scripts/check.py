#!/usr/bin/env python
"""vigen check.py — 项目文件机械校验（薄校验层，裁定 R1）。

只 enforce 机械可判定的门，不查审美。宁松勿滥：误拦的门比没有门更糟。
**「门没跑」与「门跑过且通过」必须是两种不同输出**——每个门在①文档存在②却找不到
任何可检查单位时，报一条「警告：…未执行」而不是静默通过。

纪律（SKILL.md 硬规则 15）：只 enforce 文档已写的门；改门必同步改脚本。

enforce 的条款（与 vigen_md 解析层配套）：
  K1  台词逐字            → 硬规则4 / prompt-rules A11
  K2  时长（模型上限/朗读≤镜头/4字每秒估算/段级14s）→ A2 / A3
  K3  锚定逐字（色号全量 + 角色锚定短语，无 REF 绑定时）
                          → A1（色号、角色锚定；风格圣经/03/场景道具锚定见台账 V3.1 延后）
  K4  稳定镜号（唯一性/引用解析/作废行）→ SKILL 稳定镜号规则
  K5  强调手段（慢镜配额/峰值标注可解析）→ B3 / cinematography「峰值与强调手段」
  K6  运镜条件门（剧情特征→族 + CT1 动机格式 + 固定须 R7）→ A12
  K7  环境动态层 + 固定机位微振来源 → B13
  K8  骨架槽位（11 节精确匹配 + 骨架 B 理由）→ prompt-rules 第二节（「槽位单值」见台账 V3.1 延后）
  K9  情节点覆盖（双向）  → 硬规则7
  K10 PLAN/REF 闭环（禁模糊占位；REF 须在 03 登记）→ E2 / CT5（挂图清单一致性见台账 V3.1 延后）
  K11 设定间算术冲突（段内时长合计 vs 标题生成；平均镜长 vs 模型原生下限）→ 各设定单看合法的组合矛盾
  K12 指代与部位（人物禁代词/部位带主人与左右）→ prompt-rules「指代与部位纪律」/ A13
  K13 节拍认领（每拍恰好一镜/双向一致/顺序/有台词镜不得 —）→ A14
  K14 钩子位置与时长预算（前3拍/末拍/±15%≥2.5s）→ A15

用法（CT6）：
    python check.py <项目目录> [--partial] [--gate K5[,K6]]
exit: 0=全过 1=有findings 2=用法/IO错（含门内部错误）
输出： `[K1] 04_视频提示词.md:123: <具体缺什么>`
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from vigen_md import (  # noqa: F401 — Project/Finding 供测试与外部使用
    ACTION_PREFIXES,
    CHASE_RE,
    CT1_RE,
    DOC_FILES,
    DURATION_RE,
    EMPHASIS_OTHER,
    EMPHASIS_SLOW,
    EMPHASIS_WORDS,
    ENV_MOTION_WORDS,
    FOLLOW_FAMILY,
    HEX_RE,
    MINIMUM_PYTHON,
    MODEL_CAP,
    PEAK_RE,
    PLANREF_RE,
    QUOTE_RE,
    REF_SHOT_RE,
    REVEAL_FAMILY,
    REVEAL_RE,
    SHOT_ID_RE,
    SKELETON_A_SECTIONS,
    SKIP_SECTIONS,
    VOIDED_RE,
    Finding,
    Project,
    Row,
    block_text,
    blocks,
    beat_ids,
    cell,
    sub_blocks,
    character_names,
    col_index,
    dialogue_quotes,
    dialogue_set_01,
    extract_dialogue_cell,
    model_native_min,
    time_range_seconds,
    is_dialogue_line,
    is_segment_heading,
    iter_tables,
    shot_blocks,
    split_cells,
    table_rows,
)

GateFn = Callable[[Project, bool], List[Finding]]

# 兼容旧测试名（V3.0 内部 API：_is_dialogue_line）
_is_dialogue_line = is_dialogue_line

# 01 分镜表列别名（模板与真实历史项目表头不同）
STORY_ALIASES: Dict[str, Tuple[str, ...]] = {
    "镜号": ("镜号", "镜头"),
    "运镜": ("运镜",),
    "运镜动机": ("运镜动机", "动机"),
    "生成时长": ("生成时长",),
}


def _warn(gate: str, key: str, msg: str) -> Finding:
    return Finding(gate, DOC_FILES[key], 0, "警告：" + msg)


def _plot_rows(project: Project) -> Optional[List[Row]]:
    return table_rows(project.doc("01"), ("情节点", "覆盖镜号"),
                      aliases={"覆盖镜号": ("覆盖镜号", "覆盖")})


def _story_rows(project: Project) -> Optional[List[Row]]:
    rows = table_rows(project.doc("01"), ("镜号", "运镜"),
                      aliases=STORY_ALIASES)
    if rows is not None:
        return rows
    return table_rows(project.doc("01"), ("镜号",), aliases=STORY_ALIASES)


def _kv_lookup(block: List[Tuple[int, str]], key: str) -> Optional[str]:
    """竖排键值表取值：首列（去粗体/空格）== key 时返回第二列。"""
    for _no, header, body in iter_tables([t for _, t in block]):
        if len(header) < 2 and not body:
            continue
        for _ln, cells in body:
            if len(cells) >= 2 and cells[0].strip("* ").strip() == key:
                return cells[1].strip()
    return None


def _heading_seconds(block: List[Tuple[int, str]]) -> Tuple[int, Optional[float]]:
    """04 段落/镜头标题里的「生成 Xs」。"""
    head_no, head = block[0]
    m = re.search(r"生成\s*(\d+(?:\.\d+)?)\s*s", head)
    return head_no, (float(m.group(1)) if m else None)


# ------------------------------------------------------------------ K1 台词

def gate_k1(project: Project, partial: bool) -> List[Finding]:
    if project.doc("01") is None:
        return []
    findings: List[Finding] = []
    base = dialogue_set_01(project)
    if not base:
        findings.append(_warn("K1", "01", "01 未解析到台词（缺「分场剧本」节或说话人行格式不同），K1 无法核对"))

    if project.doc("04") is not None:
        quotes = dialogue_quotes(project.doc("04"))
        if not quotes:
            findings.append(_warn("K1", "04", "未找到任何台词引号，K1 未执行"))
        for line_no, text in quotes:
            t = text.strip()
            if t and t not in base:
                findings.append(Finding(
                    "K1", DOC_FILES["04"], line_no,
                    "台词与01定稿不一致：「%s」（01 定稿中无此句——改写/修订后须从 01 逐字搬运）" % t))

    if project.doc("05") is not None:
        rows = table_rows(project.doc("05"), ("台词原文",))
        if rows is None:
            findings.append(_warn("K1", "05", "未找到含「台词原文」列的台词清单，K1 未核对 05"))
        else:
            for row in rows:
                t = extract_dialogue_cell(row.cells["台词原文"])
                if t and t not in base:
                    findings.append(Finding(
                        "K1", DOC_FILES["05"], row.line,
                        "台词与01定稿不一致：「%s」（05 台词总账须与 01 逐字一致）" % t))
    return findings


# ------------------------------------------------------------------ K2 时长

def _video_cap(project: Project) -> Optional[float]:
    rows = table_rows(project.doc("02"), ("用途", "模型"),
                      aliases={"用途": ("用途",), "模型": ("模型",)})
    if not rows:
        return None
    for row in rows:
        if "视频" in row.cells.get("用途", ""):
            cell = " ".join(row.cells.values())
            nums = [float(m) for m in DURATION_RE.findall(cell)]
            if nums:
                return max(nums)          # 区间 3s-15s → 取上限
            low = cell.lower()
            for key, cap in MODEL_CAP.items():
                if key in low:
                    return cap
            return None
    return None


def gate_k2(project: Project, partial: bool) -> List[Finding]:
    findings: List[Finding] = []
    cap = _video_cap(project)

    # ① 04 标题里的生成时长 ≤ 模型上限
    if project.doc("04") is not None and cap is not None:
        checked = 0
        for block in blocks(project.doc("04"), only_segments=True):
            head_no, secs = _heading_seconds(block)
            if secs is None:
                continue
            checked += 1
            if secs > cap:
                findings.append(Finding(
                    "K2", DOC_FILES["04"], head_no,
                    "生成时长 %gs 超模型上限 %gs（超限须拆条+尾帧续接——A2）" % (secs, cap)))
        if checked == 0:
            findings.append(_warn("K2", "04", "段落标题未写「生成 Xs」，K2 未核对生成时长"))

    # ② 01 分镜表若写了生成时长列，一并核对
    if project.doc("01") is not None and cap is not None:
        rows = table_rows(project.doc("01"), ("镜号", "生成时长"), aliases=STORY_ALIASES)
        for row in rows or []:
            m = DURATION_RE.search(row.cells.get("生成时长", ""))
            if m and float(m.group(1)) > cap:
                findings.append(Finding(
                    "K2", DOC_FILES["01"], row.line,
                    "生成时长 %ss 超模型上限 %gs（超限须拆条+尾帧续接——A2）"
                    % (m.group(1), cap)))

    # ③ 05 朗读时长 ≤ 所在镜头时长；4字/秒估算；段级 14s
    if project.doc("05") is not None:
        rows = table_rows(project.doc("05"), ("台词原文", "朗读时长", "所在镜头时长"))
        if rows is None:
            findings.append(_warn("K2", "05", "台词清单缺「朗读时长/所在镜头时长」列，K2 未核对台词时长"))
        else:
            seg_sum: Dict[str, float] = {}
            for row in rows:
                txt = extract_dialogue_cell(row.cells["台词原文"])
                try:
                    read = float(DURATION_RE.search(row.cells["朗读时长"]).group(1))
                    shot = float(DURATION_RE.search(row.cells["所在镜头时长"]).group(1))
                except (AttributeError, ValueError):
                    continue
                if read > shot:
                    findings.append(Finding(
                        "K2", DOC_FILES["05"], row.line,
                        "台词朗读超镜头时长：朗读 %gs > 镜头 %gs（延长时间码或拆多镜——A3）" % (read, shot)))
                if txt:
                    est = math.ceil(len(txt) / 4.0)
                    if est > shot:
                        findings.append(Finding(
                            "K2", DOC_FILES["05"], row.line,
                            "台词估算朗读 %ds（%d字÷4字/秒）> 镜头 %gs（A3 含标点估算）"
                            % (est, len(txt), shot)))
                m = re.search(r"段\s*(\d+)", cell(row, "镜号/段落", "镜号"))
                key = m.group(1) if m else "?"
                seg_sum[key] = seg_sum.get(key, 0.0) + read
            for seg, total in seg_sum.items():
                if total > 14.0:
                    findings.append(Finding(
                        "K2", DOC_FILES["05"], 0,
                        "段%s 台词朗读合计 %.1fs > 14s 必拆段（A3 段级预算）" % (seg, total)))
    return findings


# ------------------------------------------------------------------ K3 锚定

def _palette(project: Project) -> List[str]:
    """02 色彩基调里要求「每段都出现」的色号：环境底色/中间调/暗部色。

    装饰色（点缀色）与肤色基准按模板语义是「只给特定物体/人物皮肤」，
    空镜或无关段落不出现是合法的——不纳入逐段校验（宁松勿滥）。
    """
    out: List[str] = []
    for _no, header, body in iter_tables(project.doc("02") or []):
        if not any("色号" in h for h in header):
            continue
        role_i = 0
        hex_i = next((i for i, h in enumerate(header) if "色号" in h), -1)
        for _ln, cells in body:
            role = cells[role_i] if cells else ""
            # 白名单：只有「环境底色/中间调/暗部色」要求每段出现；
            # 点缀色、肤色基准、瞬时光效（如火星橙）按模板语义可缺（宁松勿滥）
            if not any(k in role for k in ("环境", "中间调", "暗部")):
                continue
            cell = cells[hex_i] if 0 <= hex_i < len(cells) else ""
            for m in HEX_RE.finditer(cell):
                if m.group(0) not in out:
                    out.append(m.group(0))
    return out


def _character_anchors(project: Project) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for block in sub_blocks(project.doc("02")):
        name = block[0][1][4:].strip()
        phrase = _kv_lookup(block, "锚定短语（中文）")
        if phrase:
            out.append((name, phrase))
    return out


def gate_k3(project: Project, partial: bool) -> List[Finding]:
    if project.doc("02") is None or project.doc("04") is None:
        return []
    findings: List[Finding] = []
    lines04 = project.doc("04")

    # ① 色号：每个 段落/段/镜头 块的「色调」行须含 02 登记的全部色号
    hexes = _palette(project)
    if hexes:
        checked = 0
        for block in blocks(lines04, only_segments=True):
            tone = [(no, t) for no, t in block if t.strip().startswith("色调")]
            if not tone:
                findings.append(Finding(
                    "K3", DOC_FILES["04"], block[0][0],
                    "段落缺「色调：」行，K3 无法核对色号（FORMAT 须写色号+落点——A1）"))
                continue
            checked += 1
            body = "\n".join(t for _, t in tone)
            for hx in hexes:
                if hx not in body:
                    findings.append(Finding(
                        "K3", DOC_FILES["04"], tone[0][0],
                        "色彩基调色号缺失：%s 未逐字出现（02 色板登记项——A1）" % hx))
        if checked == 0:
            findings.append(_warn("K3", "04", "未找到段落块，K3 色号检查未执行"))

    # ② 角色锚定：04 出现角色名且无 @REF 绑定 → 锚定短语须逐字出现
    anchors = _character_anchors(project)
    if not anchors:
        findings.append(_warn("K3", "02", "未解析到「锚定短语（中文）」，K3 角色锚定未核对"))
    doc_text = "\n".join(lines04)
    for name, phrase in anchors:
        if re.search(r"@\s*REF-[A-Z0-9-]+[^\n]*%s" % re.escape(name), doc_text):
            continue                      # REF 图承载外观 → 豁免
        if name not in doc_text or phrase in doc_text:
            continue
        line_no = next((i for i, ln in enumerate(lines04, start=1) if name in ln), 0)
        findings.append(Finding(
            "K3", DOC_FILES["04"], line_no,
            "角色「%s」锚定短语缺失：无 REF 图绑定，锚定短语须逐字出现（02 登记：%s…——A1）"
            % (name, phrase[:24])))
    return findings


# ------------------------------------------------------------------ K4 镜号

def _shot_ids(project: Project) -> Tuple[Dict[str, int], Dict[str, int]]:
    live: Dict[str, int] = {}
    voided: Dict[str, int] = {}
    rows = _story_rows(project)
    for row in rows or []:
        raw = row.cells.get("镜号", "").strip()
        vm = VOIDED_RE.match(raw)
        if vm:
            voided.setdefault(vm.group(1), row.line)
            continue
        m = SHOT_ID_RE.match(raw)
        if m:
            live.setdefault(m.group(1), row.line)
    return live, voided


def _shot_header_lines(lines: Optional[List[str]]) -> List[Tuple[int, str]]:
    """只取镜头块首行/标题行（K4 引用扫描范围）。"""
    if lines is None:
        return []
    out = []
    for i, ln in enumerate(lines, start=1):
        s = ln.strip()
        if re.match(r"^#{1,4}\s*镜头", s) or re.match(r"^\d+(?:\.\d+)?\s*s?\s*[–\-—~～至]", s):
            out.append((i, s))
    return out


def gate_k4(project: Project, partial: bool) -> List[Finding]:
    if project.doc("01") is None:
        return []
    findings: List[Finding] = []
    live, voided = _shot_ids(project)
    if not live:
        findings.append(_warn("K4", "01", "未解析到分镜表镜号，K4 未执行"))

    seen: set = set()
    rows = _story_rows(project) or []
    for row in rows:
        raw = row.cells.get("镜号", "").strip()
        if VOIDED_RE.match(raw):
            continue
        m = SHOT_ID_RE.match(raw)
        if not m:
            continue
        sid = m.group(1)
        if sid in seen:
            findings.append(Finding(
                "K4", DOC_FILES["01"], row.line,
                "镜号重复：%s 已分配（插入用后缀式 S3a，不重排已有镜号）" % sid))
        seen.add(sid)

    for key in ("03", "04"):
        for line_no, text in _shot_header_lines(project.doc(key)):
            for m in REF_SHOT_RE.finditer(text):
                ref = m.group(1)
                if ref in live:
                    continue
                if ref in voided:
                    findings.append(Finding(
                        "K4", DOC_FILES[key], line_no,
                        "引用了已作废镜号：镜%s（作废镜号仅供追溯，禁止再引用）" % ref))
                else:
                    findings.append(Finding(
                        "K4", DOC_FILES[key], line_no,
                        "引用了01分镜表不存在的镜号：镜%s" % ref))
    return findings


# ------------------------------------------------------------------ K5 强调手段

_SECTION_LABELS = frozenset(SKELETON_A_SECTIONS)
_TECH_LINE = re.compile(r"fps|快门|帧率|镜头运动|运镜库")
_NEG_LINE = re.compile(r"^\s*[*\-—·]?\s*(禁止|不要|不得|避免|无|没有|不)")


def _emphasis_spots(block: List[Tuple[int, str]]) -> List[Tuple[int, bool, str]]:
    """块内的强调手段处：[(行号, 是否慢镜族, 该行命中的词)]，每行最多 1 处。"""
    out: List[Tuple[int, bool, str]] = []
    section = ""
    for no, text in block:
        s = text.strip()
        if s in _SECTION_LABELS:
            section = s
            continue
        if section in ("FORMAT", "NO"):
            continue
        if not s or s.startswith("```"):
            continue
        if _TECH_LINE.search(s) or _NEG_LINE.search(s):
            continue
        hit_slow = next((w for w in EMPHASIS_SLOW if w in s), None)
        hit_other = next((w for w in EMPHASIS_OTHER if w in s), None)
        hit = hit_slow or hit_other
        if hit:
            out.append((no, bool(hit_slow), hit))
    return out


def _plot_peak_ids(project: Project) -> set:
    ids = set()
    for row in _plot_rows(project) or []:
        if "【峰】" in row.cells.get("情节点", ""):
            num = cell(row, "#").strip()
            if num.isdigit():
                ids.add(num)
    return ids


def _combat_star_rounds(project: Project) -> set:
    rounds = set()
    for _no, ln in project.section("01", "打斗交手账"):
        m = re.match(r"^\|\s*R(\d+)", ln)
        if m and "★" in ln:
            rounds.add(m.group(1))
    return rounds


def gate_k5(project: Project, partial: bool) -> List[Finding]:
    if project.doc("04") is None:
        return []
    findings: List[Finding] = []
    peak_ids = _plot_peak_ids(project)
    star_rounds = _combat_star_rounds(project)
    segs = blocks(project.doc("04"), only_segments=True)
    if not segs:
        return [_warn("K5", "04", "未找到段落块，K5 未执行")]
    units = 0
    for block in segs:
        slow = 0
        for line_no, is_slow, word in _emphasis_spots(block):
            units += 1
            if is_slow:
                slow += 1
            pm = PEAK_RE.search(next(t for n, t in block if n == line_no))
            if not pm:
                findings.append(Finding(
                    "K5", DOC_FILES["04"], line_no,
                    "强调手段无峰值标注：「%s」须标注 ←峰值：情节点N/交手账RN" % word))
                continue
            src = pm.group(1)
            if src.startswith("交手账R"):
                r = src[len("交手账R"):]
                if r not in star_rounds:
                    findings.append(Finding(
                        "K5", DOC_FILES["04"], line_no,
                        "峰值来源无法解析：%s（01 交手账该回合不存在或未标 ★ 胜负手）" % src))
            else:
                n = src[len("情节点"):]
                if n not in peak_ids:
                    findings.append(Finding(
                        "K5", DOC_FILES["04"], line_no,
                        "峰值来源无法解析：%s（01 情节点清单该编号不存在或未标【峰】）" % src))
        if slow > 2:
            findings.append(Finding(
                "K5", DOC_FILES["04"], block[0][0],
                "慢镜超配额：本段 %d 处慢镜 > 2（配额是上限不是任务）" % slow))
    if units == 0:
        findings.append(_warn("K5", "04", "全片未出现强调手段，K5 未核对（如是纯文戏可忽略）"))
    return findings


# ------------------------------------------------------------------ K6 运镜条件

def gate_k6(project: Project, partial: bool) -> List[Finding]:
    if project.doc("01") is None:
        return []
    findings: List[Finding] = []
    plot_rows = _plot_rows(project) or []
    story = _story_rows(project) or []
    if not story:
        return [_warn("K6", "01", "未解析到分镜表，K6 未执行")]

    plot_text = "\n".join(r.cells.get("情节点", "") for r in plot_rows)
    cam_text = "\n".join(r.cells.get("运镜", "") for r in story)

    if plot_rows and CHASE_RE.search(plot_text) and not FOLLOW_FAMILY.search(cam_text):
        hit = next((r for r in plot_rows if CHASE_RE.search(r.cells.get("情节点", ""))), None)
        findings.append(Finding(
            "K6", DOC_FILES["01"], hit.line if hit else 0,
            "剧情含奔跑/追逐/逃（%s）但分镜运镜列无跟拍族（跟拍/横移/跟随 ≥1 且指认镜号——A12）"
            % (hit.cells.get("情节点", "")[:24] if hit else "")))
    if plot_rows and REVEAL_RE.search(plot_text) and not REVEAL_FAMILY.search(cam_text):
        hit = next((r for r in plot_rows if REVEAL_RE.search(r.cells.get("情节点", ""))), None)
        findings.append(Finding(
            "K6", DOC_FILES["01"], hit.line if hit else 0,
            "剧情含信息揭示（%s）但分镜运镜列无摇/后拉/俯仰族（揭示须停在新信息上——A12）"
            % (hit.cells.get("情节点", "")[:24] if hit else "")))
    if "【峰】" in plot_text and project.doc("04") is not None:
        doc04 = "\n".join(project.doc("04") or [])
        if not any(w in doc04 for w in EMPHASIS_WORDS):
            findings.append(Finding(
                "K6", DOC_FILES["01"], 0,
                "情节点含【峰】但 04 无任何强调手段（峰值须配手段）"))

    for row in story:
        cam = cell(row, "运镜").strip()
        motive = cell(row, "运镜动机", "动机").strip()
        if motive and not CT1_RE.match(motive):
            findings.append(Finding(
                "K6", DOC_FILES["01"], row.line,
                "运镜动机列不合CT1（需 五类词(R行号)：一句展开，如 pressure(R3)：台词正压到她身上）：%s"
                % motive[:30]))
        if "固定" in cam and "(R7)" not in motive:
            findings.append(Finding(
                "K6", DOC_FILES["01"], row.line,
                "运镜列写固定，但动机列未报 (R7)（固定=决策表最后一行，必须带 R7+理由）：%s"
                % (motive[:30] or "空")))
    return findings


# ------------------------------------------------------------------ K7 环境动态

def gate_k7(project: Project, partial: bool) -> List[Finding]:
    if project.doc("04") is None:
        return []
    blocks_ = shot_blocks(project.doc("04"))
    if not blocks_:
        return [_warn("K7", "04", "未找到任何镜头块，K7 未执行")]
    findings: List[Finding] = []
    for block in blocks_:
        text = block_text(block)
        m = re.search(r"镜头\s*(S?\d+[a-z]?)", block[0][1])
        sid = m.group(1) if m else "?"
        if not any(w in text for w in ENV_MOTION_WORDS):
            findings.append(Finding(
                "K7", DOC_FILES["04"], block[0][0],
                "镜头%s 无环境动态层元素（每镜 ≥1：风吹/衣摆/涟漪/雾/尘埃/微振——固定≠静止）" % sid))
        if "固定" in text and not any(w in text for w in ("微振", "风吹", "风在吹", "机体振动")):
            findings.append(Finding(
                "K7", DOC_FILES["04"], block[0][0],
                "镜头%s 写固定机位但未注明微振来源（机体振动/风吹——B13）" % sid))
    return findings


# ------------------------------------------------------------------ K8 骨架槽位

def _code_blocks(lines: List[str]) -> List[Tuple[int, List[str]]]:
    out: List[Tuple[int, List[str]]] = []
    cur: Optional[List[str]] = None
    start = 0
    for i, ln in enumerate(lines, start=1):
        if ln.strip() == "```":
            if cur is None:
                cur, start = [], i
            else:
                out.append((start, cur))
                cur = None
            continue
        if cur is not None:
            cur.append(ln)
    return out


def gate_k8(project: Project, partial: bool) -> List[Finding]:
    lines = project.doc("04")
    if lines is None:
        return []
    findings: List[Finding] = []
    seen_a = 0
    for start, block in _code_blocks(lines):
        texts = [t.strip() for t in block]
        if "SCENE CONTEXT" not in texts:
            continue
        seen_a += 1
        for sec in SKELETON_A_SECTIONS:
            if not any(t == sec for t in texts):
                findings.append(Finding(
                    "K8", DOC_FILES["04"], start,
                    "骨架A缺节：%s（须单独成行——prompt-rules 骨架槽位清单）" % sec))
    if seen_a == 0:
        findings.append(_warn("K8", "04", "未找到骨架 A code block，K8 未执行"))

    if re.search(r"^##\s*镜头\s*S?\d", "\n".join(lines), re.M):
        note = "\n".join(t for _, t in project.section("01", "分镜总览表"))
        ok = re.search(r"骨架\s*B[^\n]{0,40}(理由|：|—|-)", note) or re.search(
            r"骨架\s*B[^\n]{0,40}(理由|：|—|-)", "\n".join(project.doc("01") or []))
        negated = re.search(r"(不使用|不用|非|不需要)\s*骨架\s*B", "\n".join(project.doc("01") or []))
        if not ok or negated:
            findings.append(Finding(
                "K8", DOC_FILES["04"], 0,
                "04 含骨架 B 单镜块但 01 未正面标注骨架 B 理由（fl2va/一镜到底张力——特例须写明）"))
    return findings


# ------------------------------------------------------------------ K9 情节点覆盖

def gate_k9(project: Project, partial: bool) -> List[Finding]:
    if project.doc("01") is None:
        return []
    rows = _plot_rows(project)
    if not rows:
        return [_warn("K9", "01", "未解析到情节点清单，K9 未执行")]
    findings: List[Finding] = []
    live, _voided = _shot_ids(project)
    has_status = "状态" in (rows[0].cells if rows else {})
    if not has_status:
        findings.append(Finding(
            "K9", DOC_FILES["01"], rows[0].line if rows else 0,
            "情节点清单缺「状态」列——K9 无法核对覆盖状态"))
    for row in rows:
        label = cell(row, "情节点")[:20]
        cov = cell(row, "覆盖镜号", "覆盖").strip()
        status = cell(row, "状态")
        if not cov:
            findings.append(Finding(
                "K9", DOC_FILES["01"], row.line,
                "情节点%s未覆盖：覆盖镜号列为空（分镜必须 100%% 覆盖情节点——硬规则7）" % label))
            continue
        if has_status and "✓" not in status:
            findings.append(Finding(
                "K9", DOC_FILES["01"], row.line,
                "情节点%s状态未勾：状态列须 ✓" % label))
        for m in REF_SHOT_RE.finditer(cov):
            if m.group(1) not in live:
                findings.append(Finding(
                    "K9", DOC_FILES["01"], row.line,
                    "情节点%s覆盖镜号镜%s在01分镜表不存在" % (label, m.group(1))))
    return findings


# ------------------------------------------------------------------ K10 PLAN/REF

def gate_k10(project: Project, partial: bool) -> List[Finding]:
    lines = project.doc("04")
    if lines is None:
        return []
    findings: List[Finding] = []
    doc03 = project.doc("03")
    ref_ids = {m.group(0) for m in PLANREF_RE.finditer("\n".join(doc03 or []))}
    for i, ln in enumerate(lines, start=1):
        if "待补参考图" in ln:
            findings.append(Finding(
                "K10", DOC_FILES["04"], i,
                "模糊占位「待补参考图」：缺图须写 PLAN-<ID> 占位（CT5）"))
        for m in PLANREF_RE.finditer(ln):
            kind, oid = m.group(1), m.group(2)
            if kind == "REF" and doc03 is not None and m.group(0) not in ref_ids:
                findings.append(Finding(
                    "K10", DOC_FILES["04"], i,
                    "REF-%s 在03中无法解析（03 资产引用矩阵须登记同一 REF-id）" % oid))
    return findings



# ------------------------------------------------------------------ K11 算术冲突

def gate_k11(project: Project, partial: bool) -> List[Finding]:
    """K11 设定间算术冲突（profile_notes 式）：各自合法、合起来做不到的设定。

    ① 段内镜头时长合计 vs 标题生成时长（容差 1s：头尾各裁 0.5s 的成片/生成差）
    ② 平均生成时长 vs 模型原生下限（低于下限时多数镜头必须靠多镜容器承载）
    """
    findings: List[Finding] = []
    lines = project.doc("04")
    if lines is None:
        return []
    segs = blocks(lines, only_segments=True)
    if not segs:
        return [_warn("K11", "04", "未找到段落块，K11 未执行")]
    for block in segs:
        head_no, _first = _heading_seconds(block)
        # 标题可能一行声明多段（如「段1a（生成 8s）与 段1b（生成 7s）」）→ 取合计
        secs_list = [float(x) for x in re.findall(r"生成\s*(\d+(?:\.\d+)?)\s*s", block[0][1])]
        secs = sum(secs_list) if secs_list else None
        if secs is None:
            continue
        total, found = 0.0, 0
        for _no, text in block:
            rng = time_range_seconds(text)
            if rng:
                total += rng[1] - rng[0]
                found += 1
        if found and abs(total - secs) > 1.0:
            findings.append(Finding(
                "K11", DOC_FILES["04"], head_no,
                "段内镜头时长合计 %.1fs 与标题「生成 %gs」不符（容差 1s——改时长须同步标题与 01 分镜表）"
                % (total, secs)))

    minv = model_native_min(project)
    rows = table_rows(project.doc("01"), ("镜号", "生成时长"), aliases=STORY_ALIASES)
    if minv and rows:
        durs = []
        for row in rows:
            m = DURATION_RE.search(cell(row, "生成时长"))
            if m:
                durs.append(float(m.group(1)))
        if durs and sum(durs) / len(durs) < minv:
            findings.append(Finding(
                "K11", DOC_FILES["01"], 0,
                "平均生成时长 %.1fs 低于模型原生下限 %gs：多数镜头须由多镜容器（骨架 A）承载，"
                "否则模型会把每镜自行拉长到下限" % (sum(durs) / len(durs), minv)))
    return findings



# ------------------------------------------------------------------ K12 指代与部位

# 人物代词（"其他/其它/他人" 由 lookbehind/lookahead 排掉）
_PRONOUN_RE = re.compile(r"(?<!其)(对方|那个人|两人|二人|双方|他|她|它)(?!人)")
_HUMAN_ACTION = set("说看走站坐抬转拿握伸退冲停笑低靠盯望递接推拉蹲跪扑抓挥砍刺劈跳跑")
_BODY_RE = re.compile(r"(左手|右手|左臂|右臂|左肩|右肩|左腿|右腿|左脚|右脚|左腰侧|右腰侧|左脸颊|右脸颊)(?!边)")
_BODY_SPATIAL = ("左手", "右手", "左臂", "右臂", "左肩", "右肩", "左腿", "右腿", "左脚", "右脚")
# 「哪里」模糊：命中动词 + 身上/某处/要害（没写具体部位）
_VAGUE_HIT_RE = re.compile(r"(打在|踢在|砍在|刺在|击中|砸在|撞在|落在)[^。；\n]{0,8}(身上|某处|要害)")


def _prompt_lines(project: Project, key: str) -> List[Tuple[int, str]]:
    """03/04 的 code block 正文行（跳过围栏、空行与骨架小节标签）。"""
    lines = project.doc(key)
    if lines is None:
        return []
    out: List[Tuple[int, str]] = []
    in_block = False
    for i, ln in enumerate(lines, start=1):
        if ln.strip() == "```":
            in_block = not in_block
            continue
        if not in_block:
            continue
        s = ln.strip()
        if not s or s in SKELETON_A_SECTIONS:
            continue
        out.append((i, ln))
    return out


def gate_k12(project: Project, partial: bool) -> List[Finding]:
    """K12 指代与部位：人物写角色名（禁代词）；身体部位带主人与左右。"""
    findings: List[Finding] = []
    names = character_names(project)
    total_units = 0
    for key in ("03", "04"):
        if project.doc(key) is None:
            continue
        units = 0
        for line_no, ln in _prompt_lines(project, key):
            units += 1
            text = QUOTE_RE.sub("", ln)          # 台词引号内的人称代词不受限
            line_names = sorted(n for n in names if n in text)
            for m in _PRONOUN_RE.finditer(text):
                tok = m.group(1)
                if tok == "它":
                    nxt = text[m.end():m.end() + 1]
                    if not (nxt and nxt in _HUMAN_ACTION):
                        continue                 # 「它」指物（它映着/它连接）不判
                findings.append(Finding(
                    "K12", DOC_FILES[key], line_no,
                    "人物指代用了「%s」——改为角色名（本行角色：%s；台词引号内不受限）"
                    % (tok, "/".join(line_names) or "见 02 锚定表")))
            for m in _VAGUE_HIT_RE.finditer(text):
                findings.append(Finding(
                    "K12", DOC_FILES[key], line_no,
                    "命中位置模糊「%s%s」——写具体部位（<角色名>的<左/右><部位>，如「林枫的右侧肋下」）"
                    % (m.group(1), m.group(2))))
            for m in _BODY_RE.finditer(text):
                part = m.group(1)
                back = text[max(0, m.start() - 14):m.start()]
                owned = any(back.endswith(n) or back.endswith(n + "的") for n in names)
                if not owned and "自己的" in back:
                    owned = len(line_names) <= 1     # 「自己的」需本行只有一个角色
                if not owned:
                    findings.append(Finding(
                        "K12", DOC_FILES[key], line_no,
                        "部位「%s」未带主人与左右归属——写「<角色名>的%s」并写明位置/朝向/持握"
                        % (part, part)))
        total_units += units
    if total_units == 0 and (project.doc("03") is not None or project.doc("04") is not None):
        findings.append(_warn("K12", "04", "未找到可检查的提示词正文（03/04 无 code block），K12 未执行"))
    return findings


# ------------------------------------------------------------------ K13 节拍认领

_BEAT_ID_RE = re.compile(r"^B([1-9]\d*)([a-z]?)$")


def _kv_value(project: Project, *keys: str) -> str:
    """在 01 的「项 | 值」类表格里按首列关键字取值（整体方案/GATE0/时长预算）。"""
    for _no, header, body in iter_tables(project.doc("01") or []):
        if len(header) < 2 or "项" not in header[0] or "值" not in header[1]:
            continue
        for _ln, cells in body:
            if len(cells) < 2:
                continue
            if any(k in cells[0] for k in keys):
                return cells[1].strip()
    return ""


def _beat_enabled(project: Project) -> bool:
    """旧项目没有该字段 / off → 静默跳过；on → 启用。"""
    return _kv_value(project, "节拍制").lower().startswith("on")


def _beat_rows(project: Project) -> Optional[List[Row]]:
    return table_rows(project.doc("01"), ("节拍号", "认领镜号"))


def _shot_beat_rows(project: Project) -> Optional[List[Row]]:
    return table_rows(project.doc("01"), ("镜号", "认领节拍"))


def _norm_shot_id(raw: str) -> Optional[str]:
    m = REF_SHOT_RE.search(raw or "")
    if m:
        return m.group(1)
    m = SHOT_ID_RE.match((raw or "").strip())
    return m.group(1) if m else None


def _shot_beat_claims(project: Project) -> Optional[Dict[str, List[str]]]:
    rows = _shot_beat_rows(project)
    if rows is None:
        return None
    out: Dict[str, List[str]] = {}
    for row in rows:
        raw = row.cells.get("镜号", "").strip()
        if VOIDED_RE.match(raw):
            continue
        sid = _norm_shot_id(raw)
        if sid:
            out[sid] = beat_ids(row.cells.get("认领节拍", ""))
    return out


def _shot_order(project: Project) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for row in _story_rows(project) or []:
        raw = row.cells.get("镜号", "").strip()
        if VOIDED_RE.match(raw):
            continue
        m = SHOT_ID_RE.match(raw)
        if m and m.group(1) not in out:
            out[m.group(1)] = len(out)
    return out


def _shot_seconds(project: Project) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for row in _story_rows(project) or []:
        raw = row.cells.get("镜号", "").strip()
        if VOIDED_RE.match(raw):
            continue
        m = SHOT_ID_RE.match(raw)
        d = DURATION_RE.search(row.cells.get("生成时长", ""))
        if m and d:
            out.setdefault(m.group(1), float(d.group(1)))
    return out


def _parse_seconds(text: str) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(s|秒|min|分钟)", text or "", re.I)
    if not m:
        return None
    value = float(m.group(1))
    return value * 60.0 if m.group(2).lower() in ("min", "分钟") else value


def _parse_float(text: str) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)", text or "")
    return float(m.group(1)) if m else None


def gate_k13(project: Project, partial: bool) -> List[Finding]:
    if not _beat_enabled(project):
        return []
    rows = _beat_rows(project)
    if rows is None:
        return [Finding(
            "K13", DOC_FILES["01"], 0,
            "节拍制已启用但未建场次节拍表（表头须含「节拍号」「认领镜号」）")]
    findings: List[Finding] = []
    required = ("类型", "内容摘要", "台词字数", "估算秒", "标记")
    missing = [c for c in required
               if not any(c in key for key in (rows[0].cells if rows else {}))]
    if missing:
        findings.append(Finding(
            "K13", DOC_FILES["01"], rows[0].line if rows else 0,
            "节拍表缺列：%s" % "、".join(missing)))
    live, _voided = _shot_ids(project)
    order = _shot_order(project)
    claims = _shot_beat_claims(project)
    if claims is None:
        findings.append(Finding(
            "K13", DOC_FILES["01"], rows[0].line if rows else 0,
            "分镜总览表缺「认领节拍」列——K13 无法双向核对"))
        claims = {}
    beat_to_shot: Dict[str, str] = {}
    seen = set()
    scene_bases: Dict[str, set] = {}
    prev_order = -1
    for row in rows:
        scene = cell(row, "场次").strip() or "?"
        bid = cell(row, "节拍号").strip()
        label = "%s/%s" % (scene, bid)
        m = _BEAT_ID_RE.match(bid)
        if not m:
            findings.append(Finding(
                "K13", DOC_FILES["01"], row.line,
                "节拍号「%s」格式非法（须 B1 / B2a）" % (bid or "空")))
            continue
        if bid in seen:
            findings.append(Finding(
                "K13", DOC_FILES["01"], row.line,
                "节拍号 %s 重复（每场节拍号须唯一）" % bid))
        seen.add(bid)
        scene_bases.setdefault(scene, set()).add(int(m.group(1)))
        claim = cell(row, "认领镜号").strip()
        ids = REF_SHOT_RE.findall(claim)
        if len(ids) != 1:
            findings.append(Finding(
                "K13", DOC_FILES["01"], row.line,
                "节拍%s 须恰好一个认领镜号（当前：%s）" % (label, claim or "空")))
            continue
        sid = ids[0]
        if sid not in live:
            findings.append(Finding(
                "K13", DOC_FILES["01"], row.line,
                "节拍%s 认领镜号镜%s在01分镜表不存在" % (label, sid)))
            continue
        beat_to_shot[bid] = sid
        if claims and bid not in claims.get(sid, []):
            findings.append(Finding(
                "K13", DOC_FILES["01"], row.line,
                "镜%s 的认领节拍未包含 %s（双向不一致：节拍表写镜%s）"
                % (sid, bid, sid)))
        pos = order.get(sid)
        if pos is not None:
            if pos < prev_order:
                findings.append(Finding(
                    "K13", DOC_FILES["01"], row.line,
                    "节拍%s 认领镜%s早于上一拍，节拍顺序与镜号顺序不一致"
                    % (label, sid)))
            prev_order = max(prev_order, pos)
    for scene, bases in scene_bases.items():
        if not bases:
            continue
        missing = [i for i in range(1, max(bases) + 1) if i not in bases]
        if missing:
            findings.append(Finding(
                "K13", DOC_FILES["01"], 0,
                "场%s 节拍号不连续，缺 %s"
                % (scene, "、".join("B%d" % i for i in missing))))
    for sid, bids in claims.items():
        for bid in bids:
            if bid not in beat_to_shot:
                findings.append(Finding(
                    "K13", DOC_FILES["01"], 0,
                    "镜%s 认领的 %s 不在场次节拍表" % (sid, bid)))
            elif beat_to_shot[bid] != sid:
                findings.append(Finding(
                    "K13", DOC_FILES["01"], 0,
                    "镜%s 认领 %s，但节拍表登记为镜%s（双向不一致）"
                    % (sid, bid, beat_to_shot[bid])))
    for row in _story_rows(project) or []:
        raw = row.cells.get("镜号", "").strip()
        if VOIDED_RE.match(raw):
            continue
        m = SHOT_ID_RE.match(raw)
        if not m:
            continue
        line = cell(row, "台词/字幕", "台词").strip()
        if line and line not in ("—", "-", "–") and not claims.get(m.group(1)):
            findings.append(Finding(
                "K13", DOC_FILES["01"], row.line,
                "镜%s 有台词但未认领节拍（认领节拍须写 B 编号，不能是 —）"
                % m.group(1)))
    return findings


# ------------------------------------------------------------------ K14 钩子 + 预算

def gate_k14(project: Project, partial: bool) -> List[Finding]:
    if not _beat_enabled(project):
        return []
    rows = _beat_rows(project)
    if rows is None:
        return []
    findings: List[Finding] = []
    hooks: List[Tuple[int, str]] = []
    suspense: List[Tuple[int, str]] = []
    for i, row in enumerate(rows):
        mark = cell(row, "标记")
        bid = cell(row, "节拍号").strip()
        if "钩子" in mark:
            hooks.append((i, bid))
        if "悬念" in mark:
            suspense.append((i, bid))
    if len(hooks) != 1:
        findings.append(Finding(
            "K14", DOC_FILES["01"], 0,
            "须恰好一个【钩子】标记（当前 %d 个）" % len(hooks)))
    elif hooks[0][0] >= 3:
        findings.append(Finding(
            "K14", DOC_FILES["01"], 0,
            "钩子在第 %d 拍（%s），须落在前 3 拍"
            % (hooks[0][0] + 1, hooks[0][1])))
    if len(suspense) != 1:
        findings.append(Finding(
            "K14", DOC_FILES["01"], 0,
            "须恰好一个【悬念】标记（当前 %d 个）" % len(suspense)))
    elif suspense[0][0] != len(rows) - 1:
        findings.append(Finding(
            "K14", DOC_FILES["01"], 0,
            "【悬念】在第 %d 拍（%s），须在末拍（第 %d 拍）"
            % (suspense[0][0] + 1, suspense[0][1], len(rows))))

    target = _parse_seconds(_kv_value(project, "总时长", "目标时长"))
    if target is None:
        findings.append(Finding(
            "K14", DOC_FILES["01"], 0,
            "未找到「总时长/目标时长」——K14 无法核对时长预算"))
        return findings

    chars = 0
    action = 0
    beat_secs: Dict[str, float] = {}
    for row in rows:
        raw_chars = cell(row, "台词字数").strip()
        try:
            chars += int(float(raw_chars or 0))
        except ValueError:
            findings.append(Finding(
                "K14", DOC_FILES["01"], row.line,
                "节拍%s 的台词字数不是数字（%s）"
                % (cell(row, "节拍号").strip(), raw_chars)))
        if "动作" in cell(row, "类型"):
            action += 1
        sec = _parse_float(cell(row, "估算秒"))
        if sec is not None:
            sid = " ".join(REF_SHOT_RE.findall(cell(row, "认领镜号")))
            beat_secs[sid] = beat_secs.get(sid, 0.0) + sec
    dialogue_sec = float(math.ceil(chars / 4.0))
    action_sec = action * 2.5
    estimated = dialogue_sec + action_sec
    raw_tol = _kv_value(project, "时长容差")
    pct_m = re.search(r"(\d+(?:\.\d+)?)\s*%", raw_tol)
    pct = float(pct_m.group(1)) if pct_m else 15.0
    tolerance = max(target * pct / 100.0, 2.5)
    if abs(estimated - target) > tolerance:
        findings.append(Finding(
            "K14", DOC_FILES["01"], 0,
            "时长预算不通过：台词 %.0fs + 动作 %.1fs = %.1fs，目标 %.1fs，"
            "差 %.1fs > 容差 %.1fs"
            % (dialogue_sec, action_sec, estimated, target,
               abs(estimated - target), tolerance)))
    declared = {
        "台词秒数": _parse_float(_kv_value(project, "台词秒数")),
        "动作秒数": _parse_float(_kv_value(project, "动作秒数")),
        "预计总时长": _parse_float(_kv_value(project, "预计总时长")),
    }
    actual = {"台词秒数": dialogue_sec, "动作秒数": action_sec, "预计总时长": estimated}
    for key, value in declared.items():
        if value is not None and abs(value - actual[key]) > 1.0:
            findings.append(Finding(
                "K14", DOC_FILES["01"], 0,
                "时长预算表「%s」写 %.1fs，按节拍表重算 %.1fs（差 >1s）"
                % (key, value, actual[key])))

    shot_secs = _shot_seconds(project)
    for sid, total in beat_secs.items():
        cap = shot_secs.get(sid)
        if cap is not None and total > cap + 2.5:
            findings.append(Finding(
                "K14", DOC_FILES["01"], 0,
                "镜%s 认领的节拍合计 %.1fs > 生成时长 %.1fs + 2.5s（须拆镜或减拍）"
                % (sid, total, cap)))
    return findings


GATES: List[Tuple[str, GateFn]] = [
    ("K1", gate_k1), ("K2", gate_k2), ("K3", gate_k3), ("K4", gate_k4),
    ("K5", gate_k5), ("K6", gate_k6), ("K7", gate_k7), ("K8", gate_k8),
    ("K9", gate_k9), ("K10", gate_k10), ("K11", gate_k11), ("K12", gate_k12),
    ("K13", gate_k13), ("K14", gate_k14),
]

REQUIRED_FOR_FULL = ("01", "02", "03", "04", "05")


def main(argv: List[str]) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass
    if sys.version_info < MINIMUM_PYTHON:
        print("check.py requires Python %d.%d+, running %d.%d"
              % (MINIMUM_PYTHON[0], MINIMUM_PYTHON[1], sys.version_info[0], sys.version_info[1]))
        return 2

    ap = argparse.ArgumentParser(description="vigen 项目文件机械校验（K1-K14）")
    ap.add_argument("project_dir", help="项目目录（含 01-06 Markdown）")
    ap.add_argument("--partial", action="store_true",
                    help="只核对已有文档；缺文档的门静默跳过（全量要求 01-05 齐备）")
    ap.add_argument("--gate", default=None, help="只跑指定门，可用逗号分隔，如 K1,K5")
    args = ap.parse_args(argv[1:])

    root = Path(args.project_dir)
    if not root.is_dir():
        print("项目目录不存在：%s" % root)
        return 2
    project = Project(root)
    if project.doc("01") is None and project.doc("04") is None:
        print("项目目录内无 01/04 文件——未按 vigen 01-06 契约组织，跳过")
        return 2

    valid = {g for g, _ in GATES}
    selected: Optional[set] = None
    if args.gate:
        wanted = {g.strip().upper() for g in args.gate.split(",") if g.strip()}
        bad = wanted - valid
        if bad:
            print("未知门：%s（合法取值：%s）" % (", ".join(sorted(bad)), ", ".join(g for g, _ in GATES)))
            return 2
        selected = wanted

    findings: List[Finding] = []
    rc_extra = 0
    if not args.partial:
        for key in REQUIRED_FOR_FULL:
            if project.doc(key) is None:
                findings.append(Finding("PRE", DOC_FILES[key], 0,
                                        "全量校验缺文件 %s（只跑部分文档请用 --partial）" % DOC_FILES[key]))
    for gate_id, gate_fn in GATES:
        if selected is not None and gate_id not in selected:
            continue
        try:
            findings.extend(gate_fn(project, args.partial))
        except Exception as exc:      # 单门崩溃不吞掉其他门的 findings
            findings.append(Finding(gate_id, "-", 0, "内部错误：%s: %s" % (type(exc).__name__, exc)))
            rc_extra = 2

    for f in findings:
        loc = "%s:%d" % (f.file, f.line) if f.line else f.file
        print("[%s] %s: %s" % (f.gate, loc, f.message))
    if findings:
        print("check: %d 项未通过（不过不进下一阶段——SKILL.md 硬规则 15）" % len(findings))
        return rc_extra or 1
    print("check: 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
