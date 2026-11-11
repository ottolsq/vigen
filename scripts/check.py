#!/usr/bin/env python
"""vigen check.py — 项目文件机械校验（薄校验层，裁定 R1）。

只 enforce 机械可判定的门，不查审美。宁松勿滥：误拦的门比没有门更糟。
**「门没跑」与「门跑过且通过」必须是两种不同输出**——每个门在①文档存在②却找不到
任何可检查单位时，报一条「警告：…未执行」而不是静默通过。

纪律（SKILL.md 硬规则 15）：只 enforce 文档已写的门；改门必同步改脚本。

enforce 的条款（与 vigen_md 解析层配套）：
  K1  台词逐字            → 硬规则4 / prompt-rules A11
  K2  时长（模型上限/朗读≤镜头/4字每秒估算/段级14s/H3整数秒）→ A2 / A3
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
  K15 短剧立项单一致性（必填字段/档位集数/单元划分/付费墙落位）→ short-drama-market
  K16 短剧集结构（本集结算/断章/长档中段小钩 + 独白旁白配额与位置）
      → screenwriting-craft 一·九 / short-drama-market.md
      「叙事形态」缺失或为电影化时 K15/K16 静默跳过（旧项目零影响）；
      模板占位（含花括号/`第N集`）不算已填，K15/K16 报「未填」
  A16 先锁后写（opt-in）：风格圣经逐字/入画 REF/持续在场
  A17 执行契约留痕（opt-in）：批次生产卡 + 批次校验记录 A1-A16 逐项证据
      → SKILL 执行契约（V3.16）

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

def _video_row(project: Project) -> Optional[Row]:
    """02 目标模型表里的「视频」行。"""
    rows = table_rows(project.doc("02"), ("用途", "模型"),
                      aliases={"用途": ("用途",), "模型": ("模型",)})
    if not rows:
        return None
    for row in rows:
        # 用 cell() 的子串匹配，兼容「用途（必填）」「模型（供应商）」等带后缀表头
        if "视频" in cell(row, "用途"):
            return row
    return None


def _video_model(project: Project) -> Optional[str]:
    """「视频」行的模型名单元格（只看模型名，不看备注，防备注里的 H3 误判）。"""
    row = _video_row(project)
    return cell(row, "模型").strip() if row else None


def _is_h3(project: Project) -> bool:
    """当前视频模型是否为 MiniMax-H3 系（网关 seconds 只收整数）。"""
    low = (_video_model(project) or "").lower()
    return "h3" in low or "minimax" in low


def _video_cap(project: Project) -> Optional[float]:
    row = _video_row(project)
    if row is None:
        return None
    cell = " ".join(row.cells.values())
    nums = [float(m) for m in DURATION_RE.findall(cell)]
    if nums:
        return max(nums)          # 区间 3s-15s → 取上限
    low = cell.lower()
    for key, cap in MODEL_CAP.items():
        if key in low:
            return cap
    return None


def gate_k2(project: Project, partial: bool) -> List[Finding]:
    findings: List[Finding] = []
    cap = _video_cap(project)
    h3 = _is_h3(project)

    # ① 04 标题里的生成时长 ≤ 模型上限；H3 还须为整数秒
    #    一行标题可能声明多段（「段1a（生成 8s）与 段1b（生成 7.5s）」）→ 逐个检查
    if project.doc("04") is not None and cap is not None:
        checked = 0
        for block in blocks(project.doc("04"), only_segments=True):
            head_no = block[0][0]
            secs_list = [float(x) for x in
                         re.findall(r"生成\s*(\d+(?:\.\d+)?)\s*s", block[0][1])]
            if not secs_list:
                continue
            checked += 1
            for secs in secs_list:
                if secs > cap:
                    findings.append(Finding(
                        "K2", DOC_FILES["04"], head_no,
                        "生成时长 %gs 超模型上限 %gs（超限须拆条+尾帧续接——A2）" % (secs, cap)))
                if h3 and abs(secs - round(secs)) > 1e-9:
                    findings.append(Finding(
                        "K2", DOC_FILES["04"], head_no,
                        "生成时长 %gs 不是整数秒（H3 网关 seconds 只收整数，9.5→10——A2）" % secs))
        if checked == 0:
            findings.append(_warn("K2", "04", "段落标题未写「生成 Xs」，K2 未核对生成时长"))

    # ② 01 分镜表若写了生成时长列，一并核对
    if project.doc("01") is not None and cap is not None:
        rows = table_rows(project.doc("01"), ("镜号", "生成时长"), aliases=STORY_ALIASES)
        for row in rows or []:
            m = DURATION_RE.search(cell(row, "生成时长"))
            if m and float(m.group(1)) > cap:
                findings.append(Finding(
                    "K2", DOC_FILES["01"], row.line,
                    "生成时长 %ss 超模型上限 %gs（超限须拆条+尾帧续接——A2）"
                    % (m.group(1), cap)))
            # 注：01 的「生成时长」在骨架 A 下是段内镜头的时间分配，不是网关 seconds；
            # 整数秒门只查 04 的段落生成时长，避免把 4.5s/5.5s 的镜头分配误报。

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
    # 分镜总览表的签名列是「运镜」——节拍表只有「认领镜号」，不能拿它冒充分镜表
    has_storyboard = table_rows(
        project.doc("01"), ("镜号", "运镜"), aliases=STORY_ALIASES) is not None
    claims = _shot_beat_claims(project)
    claim_checks = has_storyboard and claims is not None
    if not has_storyboard:
        # 阶段1a：剧本+节拍表已产出、分镜尚未建——--partial 下这是正常状态。
        # 只查节拍号格式/唯一/连续；认领镜号是阶段1b 的产物，此处不查。
        if not partial:
            findings.append(Finding(
                "K13", DOC_FILES["01"], 0,
                "未建分镜总览表——K13 无法核对「认领镜号」"
                "（阶段1b 后必须存在；阶段1a 用 --partial）"))
        claims = {}
    elif claims is None:
        findings.append(Finding(
            "K13", DOC_FILES["01"], rows[0].line if rows else 0,
            "分镜总览表缺「认领节拍」列——K13 无法双向核对"))
        claims = {}
    live, _voided = _shot_ids(project)
    order = _shot_order(project)
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
        if not claim_checks:
            continue
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
    mode = _kv_value(project, "时长模式") or ""
    upper_only = ("上限" in mode) or ("范围" in mode)
    if upper_only:
        # 上限档（V3.16）：只要求不超上限，不强制卡到目标值——防为凑时长删情节
        if estimated > target + 1.0:
            findings.append(Finding(
                "K14", DOC_FILES["01"], 0,
                "时长超上限：台词 %.0fs + 动作 %.1fs = %.1fs > 上限 %.1fs（上限档只查不超，不要求凑满）"
                % (dialogue_sec, action_sec, estimated, target)))
    elif abs(estimated - target) > tolerance:
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


# ------------------------------------------------------------------ K15/K16 竖屏短剧

SHORT_FORM = "竖屏"

# 付费墙落位区间（与 short-drama-market.md 一致；自定义集数不做区间校验）
WALL_RANGES: Dict[int, List[Tuple[int, int]]] = {
    60: [(8, 11), (21, 24), (41, 44)],
    80: [(10, 15), (28, 32), (55, 58)],
    100: [(13, 19), (35, 40), (68, 73)],
    30: [(4, 6), (10, 12), (20, 22)],
    40: [(5, 8), (14, 16), (27, 29)],
    50: [(7, 10), (17, 20), (34, 37)],
}
FORMAT_TOTALS: Dict[str, set] = {
    "standard": {60, 80, 100},
    "long": {30, 40, 50},
    "manju": {60, 80, 100},
}
UNIT_CAP: Dict[str, int] = {"standard": 30, "long": 15, "manju": 30}
OS_CAP: Dict[str, int] = {"standard": 1, "long": 2, "manju": 1}
OS_LEN: Dict[str, int] = {"standard": 25, "long": 30, "manju": 20}
VO_CAP = 1
VO_LEN = 12

_UNIT_RE = re.compile(
    r"([A-Za-z])\s*[（(]\s*(\d+)\s*[-–—~至]\s*(\d+)\s*[)）]")
_SPAN_RE = re.compile(r"(\d+)\s*[-–—~至]\s*(\d+)")
_VO_LINE_RE = re.compile(
    r"^(内心独白|独白|心声|旁白|画外音|画面字幕|字幕)"
    r"(（[^）]*）|\([^)]*\))?\s*[:：]\s*(.+)$")
# vigen 既有 [VO] 记法：不区分独白/旁白，按内心独白口径计（更宽松，防误伤）
_VO_BRACKET_RE = re.compile(r"^\[VO\]\s*[:：]?\s*(.+)$", re.I)


def _parent_series_doc(project: Project) -> Optional[List[str]]:
    """系列项目：ep01/ 的上一级是 00_剧情状态.md（check 在单集目录跑）。"""
    p = project.root.resolve().parent / DOC_FILES["00"]
    if not p.is_file():
        return None
    try:
        return p.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def _meta_value(project: Project, *keys: str) -> str:
    """在 00/01 的「项 | 值」表里按首列关键字取值。

    查找顺序：本目录 00 → 上一级系列 00（单集目录跑 check）→ 本目录 01。
    """
    docs = [project.doc("00"), _parent_series_doc(project), project.doc("01")]
    for lines in docs:
        for _no, header, body in iter_tables(lines or []):
            if len(header) < 2 or "项" not in header[0] or "值" not in header[1]:
                continue
            for _ln, cells in body:
                if len(cells) < 2:
                    continue
                name = cells[0].strip("* ").strip()
                if any(k in name for k in keys):
                    value = cells[1].strip()
                    if value:
                        return value
    return ""


def _has_series_meta(project: Project) -> bool:
    return (project.doc("00") is not None
            or _parent_series_doc(project) is not None)


_PLACEHOLDER_RE = re.compile(r"[{}]")
_MENU_FIELDS = ("平台", "档位", "流派", "备案类别")


def _is_placeholder(value: str) -> bool:
    """模板占位（含花括号）不算已填；`—` 也不算。"""
    v = (value or "").strip()
    return bool(_PLACEHOLDER_RE.search(v)) or v in ("—", "-", "–")


def _filled(value: Optional[str]) -> bool:
    return bool(value) and not _is_placeholder(value)


def _form_state(project: Project) -> str:
    """叙事形态三态：short / film / ambiguous / auto。

    - 未填 / — → auto（旧项目与电影化项目静默跳过）
    - 「非竖屏短剧（电影化）」→ film（否定写法不误判）
    - 同时含「竖屏短剧」与「电影化」→ ambiguous（模板菜单未选定，K15 报错）
    """
    raw = _meta_value(project, "叙事形态").strip()
    if not raw:
        return "auto"
    if _is_placeholder(raw):
        if "竖屏" in raw and "电影化" in raw:
            return "ambiguous"
        if "竖屏" in raw:
            return "short"
        if "电影化" in raw:
            return "film"
        return "auto"
    if re.search(r"(非|不是|不用|不要)\s*竖屏", raw):
        return "film"
    has_short = "竖屏" in raw
    has_film = "电影化" in raw
    if has_short and has_film:
        return "ambiguous"
    if has_short:
        return "short"
    if has_film:
        return "film"
    return "auto"


def _short_form(project: Project) -> bool:
    return _form_state(project) == "short"


def _format_state(project: Project) -> str:
    """档位三态：standard / long / manju / ambiguous / bad / 空。"""
    raw = _meta_value(project, "档位").strip()
    if not raw:
        return ""
    hits = [k for k in ("标准档", "长档", "漫剧档") if k in raw]
    if len(hits) > 1:
        return "ambiguous"
    if _is_placeholder(raw):
        return ""
    if not hits:
        return "bad"
    return {"标准档": "standard", "长档": "long", "漫剧档": "manju"}[hits[0]]


def _short_format(project: Project) -> str:
    state = _format_state(project)
    return state if state in ("standard", "long", "manju") else ""


def _parse_int(text: str) -> Optional[int]:
    m = re.search(r"(\d+)", text or "")
    return int(m.group(1)) if m else None


def _parse_units(text: str) -> List[Tuple[str, int, int]]:
    """'A(1-25) / B(26-52)' → [('A',1,25),('B',26,52)]；无字母标签时按出现顺序编号。"""
    out = [(m.group(1), int(m.group(2)), int(m.group(3)))
           for m in _UNIT_RE.finditer(text or "")]
    if out:
        return out
    return [("单元%d" % (i + 1), int(m.group(1)), int(m.group(2)))
            for i, m in enumerate(_SPAN_RE.finditer(text or ""))]


_WALL_SPLIT = re.compile(r"(一级|二级|三级)")


def _parse_walls(text: str) -> Dict[int, int]:
    """'一级墙 第12集 / 二级墙 第30集' → {1:12, 2:30}。

    按层级词切段逐段取首个数字——禁止跨层吞数（「一级墙 无 / 二级墙 第10集」
    不能把 10 算成一级墙）。
    """
    level = {"一级": 1, "二级": 2, "三级": 3}
    parts = _WALL_SPLIT.split(text or "")
    out: Dict[int, int] = {}
    for i in range(1, len(parts) - 1, 2):
        m = re.search(r"(\d+)", parts[i + 1])
        if m:
            out[level[parts[i]]] = int(m.group(1))
    return out


def _is_no_wall(text: str) -> bool:
    """「无」「无付费墙」「无（广告分账）」→ 无墙；含墙位数字或「一级…」不算。"""
    v = (text or "").strip()
    return v.startswith("无") and not re.search(r"\d", v) and "第" not in v


def _wall_bounds(total: int, variant: str) -> Optional[List[Tuple[int, int]]]:
    """按变体放宽付费墙区间：投流前置只放宽一级墙；治愈系后置整体 +3 集。"""
    base = WALL_RANGES.get(total)
    if not base:
        return None
    out = list(base)
    if variant == "投流前置":
        out[0] = (3, 8)
    elif variant == "治愈系后置":
        out = [(lo + 2, hi + 3) for lo, hi in out]
    return out


def _vo_kind_body(line: str) -> Optional[Tuple[str, str]]:
    """独白/旁白行 → ('os'|'vo', 内容)；兼容 [VO] 记法（按 os 计）。"""
    s = line.strip()
    m = _VO_LINE_RE.match(s)
    if m:
        return ("os" if m.group(1) in ("内心独白", "独白", "心声") else "vo",
                m.group(3))
    m = _VO_BRACKET_RE.match(s)
    if m:
        return ("os", m.group(1))
    return None


def _field_body(lines: List[str], *names: str) -> Optional[str]:
    """【字段】同行的值；值在下一行时取首个非空行。字段不存在返回 None。"""
    for i, ln in enumerate(lines):
        s = ln.strip()
        for name in names:
            marker = "【%s】" % name
            if marker not in s:
                continue
            body = s.split(marker, 1)[1].lstrip("：: ").strip()
            if body:
                return body
            for nxt in lines[i + 1:]:
                t = nxt.strip()
                if not t:
                    continue
                return "" if t.startswith("【") else t
            return ""
    return None


def gate_k15(project: Project, partial: bool) -> List[Finding]:
    """短剧立项单一致性：必填字段 / 档位集数 / 单元划分 / 付费墙落位。"""
    state = _form_state(project)
    if state in ("auto", "film"):
        return []
    key = "00" if _has_series_meta(project) else "01"
    file_name = DOC_FILES[key]
    findings: List[Finding] = []

    if state == "ambiguous":
        findings.append(Finding(
            "K15", file_name, 0,
            "叙事形态未选定：值同时含「竖屏短剧」与「电影化」（不要保留模板菜单）"))

    base_fields = ("平台", "档位", "总集数", "赛道", "流派", "情绪契约", "备案类别")
    for name in base_fields:
        value = _meta_value(project, name)
        if not value or _is_placeholder(value):
            findings.append(Finding(
                "K15", file_name, 0,
                "短剧立项单缺「%s」或仍是模板占位" % name))
        elif name in _MENU_FIELDS and " / " in value:
            findings.append(Finding(
                "K15", file_name, 0,
                "「%s」未选定（值含多个选项：%s）" % (name, value)))

    fmt_state = _format_state(project)
    if fmt_state == "ambiguous":
        findings.append(Finding(
            "K15", file_name, 0,
            "档位未选定：值同时含多个档位（%s）"
            % _meta_value(project, "档位")))
    elif fmt_state == "bad":
        findings.append(Finding(
            "K15", file_name, 0,
            "档位「%s」无法识别（须含 标准档/长档/漫剧档）"
            % _meta_value(project, "档位")))

    raw_total = _meta_value(project, "总集数")
    total = None if _is_placeholder(raw_total) else _parse_int(raw_total)
    if total is None or total <= 0:
        findings.append(Finding(
            "K15", file_name, 0, "总集数不是正整数或仍是模板占位"))
        return findings

    fmt = _short_format(project)
    if fmt:
        known = FORMAT_TOTALS[fmt]
        all_known = set().union(*FORMAT_TOTALS.values())
        if total in all_known and total not in known:
            findings.append(Finding(
                "K15", file_name, 0,
                "总集数 %d 不属于「%s」的集数档（%s）"
                % (total, {"standard": "标准档", "long": "长档",
                           "manju": "漫剧档"}[fmt],
                   "/".join(str(x) for x in sorted(known)))))

    if total <= 1:
        return findings

    emotion_flow = "情绪流" in _meta_value(project, "流派")
    raw_units = _meta_value(project, "单元划分")
    if not raw_units or _is_placeholder(raw_units):
        if emotion_flow:
            findings.append(Finding(
                "K15", file_name, 0,
                "情绪流项目缺「单元划分」（剧情流可写「—」）"))
    else:
        units = _parse_units(raw_units)
        if not units:
            findings.append(Finding(
                "K15", file_name, 0,
                "单元划分无法解析（写法：A(1-25) / B(26-52)）"))
        else:
            cap = UNIT_CAP.get(fmt, 30)
            prev_end = 0
            for label, start, end in units:
                if start != prev_end + 1:
                    findings.append(Finding(
                        "K15", file_name, 0,
                        "单元划分不连续：单元%s 起点第%d集，上一单元终点第%d集"
                        % (label, start, prev_end)))
                if end < start:
                    findings.append(Finding(
                        "K15", file_name, 0,
                        "单元%s 区间 %d-%d 非法" % (label, start, end)))
                if end - start + 1 > cap:
                    findings.append(Finding(
                        "K15", file_name, 0,
                        "单元%s 跨 %d 集 > 上限 %d（单矛盾硬帽）"
                        % (label, end - start + 1, cap)))
                prev_end = max(prev_end, end)
            if prev_end != total:
                findings.append(Finding(
                    "K15", file_name, 0,
                    "单元划分止于第%d集，与总集数 %d 不一致"
                    % (prev_end, total)))

    raw_variant = _meta_value(project, "付费墙变体")
    variant = "标准"
    if _is_placeholder(raw_variant):
        findings.append(Finding(
            "K15", file_name, 0,
            "付费墙变体未选定（仍是模板占位）"))
    elif "投流" in raw_variant:
        variant = "投流前置"
    elif "后置" in raw_variant or "治愈" in raw_variant:
        variant = "治愈系后置"
    elif "无墙" in raw_variant or "广告" in raw_variant:
        variant = "无墙"

    raw_walls = _meta_value(project, "付费墙落位")
    if not raw_walls or _is_placeholder(raw_walls):
        findings.append(Finding(
            "K15", file_name, 0,
            "短剧立项单缺「付费墙落位」或仍是模板占位"))
    elif variant == "无墙":
        if not _is_no_wall(raw_walls):
            findings.append(Finding(
                "K15", file_name, 0,
                "付费墙变体=无墙，但「付费墙落位」填了具体墙位"))
    elif _is_no_wall(raw_walls):
        pass  # 广告分账无付费墙
    else:
        walls = _parse_walls(raw_walls)
        ranges = _wall_bounds(total, variant)
        for level, label in ((1, "一级"), (2, "二级"), (3, "三级")):
            if level not in walls:
                findings.append(Finding(
                    "K15", file_name, 0,
                    "付费墙落位缺「%s墙 第N集」" % label))
                continue
            if not (1 <= walls[level] <= total):
                findings.append(Finding(
                    "K15", file_name, 0,
                    "%s墙 第%d集 超出总集数 %d"
                    % (label, walls[level], total)))
                continue
            if ranges and not (ranges[level - 1][0] <= walls[level]
                               <= ranges[level - 1][1]):
                findings.append(Finding(
                    "K15", file_name, 0,
                    "%s墙 第%d集 不在总集数 %d 的允许区间 %d~%d（变体：%s）"
                    % (label, walls[level], total,
                       ranges[level - 1][0], ranges[level - 1][1], variant)))
    return findings


def gate_k16(project: Project, partial: bool) -> List[Finding]:
    """短剧集结构：结算/断章/长档中段小钩 + 独白旁白配额与位置。"""
    if not _short_form(project):
        return []
    lines = project.doc("01")
    if lines is None:
        # --partial：缺文档静默跳过（与 K1/K13 同口径）；全量校验才报缺文件
        if partial:
            return []
        return [Finding(
            "K16", DOC_FILES["01"], 0,
            "叙事形态=竖屏短剧但缺 01 文件，无法核对本集结构")]
    fmt = _short_format(project) or "standard"
    findings: List[Finding] = []

    settlement = _field_body(lines, "本集结算")
    if not _filled(settlement):
        findings.append(Finding(
            "K16", DOC_FILES["01"], 0,
            "【本集结算】缺失或未填（空/模板占位）——须写主角可见反将 + 反派为本次施压付代价"))

    break_body = _field_body(lines, "本集断章卡点", "本集断章")
    if not _filled(break_body):
        findings.append(Finding(
            "K16", DOC_FILES["01"], 0,
            "【本集断章卡点】缺失或未填（空/模板占位）——每集末拍必须是断章公式之一"))

    if fmt == "long":
        mid = _field_body(lines, "本集中段小钩", "中段小钩")
        if not _filled(mid):
            findings.append(Finding(
                "K16", DOC_FILES["01"], 0,
                "【本集中段小钩】缺失或未填（空/模板占位）——长档 ≈90 秒处必设新信息/新威胁"))

    os_cap = OS_CAP.get(fmt, 1)
    os_len = OS_LEN.get(fmt, 25)
    os_count = 0
    vo_count = 0
    prev_vo = False
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        entry = _vo_kind_body(s)
        if entry is None:
            prev_vo = False
            continue
        kind, body = entry
        clean = re.sub(r"[\s，。！？；：、…—\-·“”\"'‘’（）()《》!?.,]", "", body)
        if kind == "os":
            os_count += 1
            if len(clean) > os_len:
                findings.append(Finding(
                    "K16", DOC_FILES["01"], 0,
                    "内心独白单处 %d 字 >%d（只写具体的账）"
                    % (len(clean), os_len)))
        else:
            vo_count += 1
            if len(clean) > VO_LEN:
                findings.append(Finding(
                    "K16", DOC_FILES["01"], 0,
                    "旁白/字幕单处 %d 字 >%d" % (len(clean), VO_LEN)))
        if prev_vo:
            findings.append(Finding(
                "K16", DOC_FILES["01"], 0,
                "连续两条独白/旁白（禁连排）"))
        prev_vo = True

    if os_count > os_cap:
        findings.append(Finding(
            "K16", DOC_FILES["01"], 0,
            "内心独白 %d 处 > %d（%s配额）"
            % (os_count, os_cap, fmt)))
    if vo_count > VO_CAP:
        findings.append(Finding(
            "K16", DOC_FILES["01"], 0,
            "旁白/字幕 %d 处 > %d" % (vo_count, VO_CAP)))

    break_idx = next((i for i, ln in enumerate(lines)
                      if "【本集断章" in ln), None)
    if break_idx is not None:
        for j in range(break_idx - 1, -1, -1):
            s = lines[j].strip()
            if not s:
                continue
            if _vo_kind_body(s):
                findings.append(Finding(
                    "K16", DOC_FILES["01"], 0,
                    "独白/旁白紧贴断章收尾（断章必须落在画面/事件上）"))
            break
    return findings


# ------------------------------------------------------------------ A16 先锁后写（opt-in 审计）
def _style_bible(project: Project) -> str:
    parts = []
    for _no, ln in project.section("02", "风格圣经"):
        s = ln.strip()
        if not s or s.startswith((">", "|", "#")):
            continue
        parts.append(s)
    text = " ".join(parts).strip()
    return "" if "{" in text or "}" in text else text


def _norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _scene_persistent(project: Project) -> str:
    for _no, _header, body in iter_tables(project.doc("02") or []):
        for _ln, cells in body:
            if len(cells) >= 2 and "持续在场要素" in cells[0]:
                value = cells[1].strip()
                if value and not _is_placeholder(value):
                    return value
    return ""


def gate_a16(project: Project, partial: bool) -> List[Finding]:
    """A16 先锁后写（opt-in 审计）：只做机械可判定的子集。

    ① 04 每个段落须含 02 风格圣经逐字（风格三件套之一）
    ② 01「入画道具」列的 REF-id 须在 03/02 登记
    ③ 02 有持续在场要素时，04 须出现「始终在场」或「全程不出现」
    技术动作/朝向三要素仍为人工核对。
    """
    findings: List[Finding] = []
    bible = _style_bible(project)
    if bible and project.doc("04") is not None:
        target = _norm_ws(bible)
        for block in blocks(project.doc("04"), only_segments=True):
            body = _norm_ws("\n".join(t for _, t in block))
            if target not in body:
                findings.append(Finding(
                    "A16", DOC_FILES["04"], block[0][0],
                    "段落缺风格圣经逐字句（A16 风格三件套——02 已登记：%s…）"
                    % bible[:30]))

    if project.doc("01") is not None:
        rows = table_rows(project.doc("01"), ("镜号",), aliases=STORY_ALIASES)
        if rows and any("入画道具" in key for key in rows[0].cells):
            doc03 = "\n".join(project.doc("03") or [])
            doc02 = "\n".join(project.doc("02") or [])
            for row in rows:
                raw = cell(row, "入画道具").strip()
                if not raw or raw in ("—", "-", "–"):
                    continue
                ids = re.findall(r"REF-[A-Z0-9-]+", raw)
                if not ids:
                    findings.append(Finding(
                        "A16", DOC_FILES["01"], row.line,
                        "入画道具列有内容但未写 REF-id（A16 入画即登记）：%s"
                        % raw[:20]))
                    continue
                for rid in ids:
                    if rid not in doc03 and rid not in doc02:
                        findings.append(Finding(
                            "A16", DOC_FILES["01"], row.line,
                            "入画道具 %s 未在 03 资产矩阵登记（A16 入画即登记）" % rid))

    persistent = _scene_persistent(project)
    if persistent and project.doc("04") is not None:
        doc04 = "\n".join(project.doc("04") or [])
        if "始终在场" not in doc04 and "全程不出现" not in doc04:
            findings.append(Finding(
                "A16", DOC_FILES["04"], 0,
                "02 已登记持续在场要素，但 04 未复述「始终在场/全程不出现」（A16）"))
    return findings


# ------------------------------------------------------------------ A17 执行契约留痕（opt-in 审计）

def _header_index(header: List[str], *names: str) -> int:
    for name in names:
        for i, h in enumerate(header):
            if name in h:
                return i
    return -1


def gate_a17(project: Project, partial: bool) -> List[Finding]:
    """A17 执行契约留痕（opt-in）：只查留痕完整性，不查内容质量。

    - 01 必须有「批次生产卡」表（表头含 段号/镜号/生成时长）且至少一行数据
    - 01 必须有「批次校验记录」表（表头含 门/结果/证据），A1-A16 逐项出现，
      每行结果非空、证据非空（OPEN 也必须有回填时点说明）
    """
    findings: List[Finding] = []
    doc = project.doc("01")
    if doc is None:
        return [_warn("A17", "01", "01 缺失，A17 未执行")]

    audit_head: Optional[int] = None
    card_head: Optional[int] = None
    for head_no, header, body in iter_tables(doc):
        gate_i = _header_index(header, "门")
        res_i = _header_index(header, "结果")
        ev_i = _header_index(header, "证据")
        if gate_i >= 0 and res_i >= 0 and ev_i >= 0:
            audit_head = head_no
            seen = set()
            for no, cells in body:
                if gate_i >= len(cells):
                    continue
                m = re.search(r"A\s*(\d+)", cells[gate_i])
                if not m:
                    continue
                n = int(m.group(1))
                if n < 1 or n > 16:
                    continue
                seen.add(n)
                res = cells[res_i].strip() if res_i < len(cells) else ""
                ev = cells[ev_i].strip() if ev_i < len(cells) else ""
                if "{" in res or "}" in res:
                    findings.append(Finding(
                        "A17", DOC_FILES["01"], no,
                        "A%d 结果仍是模板占位（填 PASS/OPEN/NA）" % n))
                elif res.upper() not in ("PASS", "OPEN", "NA"):
                    findings.append(Finding(
                        "A17", DOC_FILES["01"], no,
                        "A%d 结果须为 PASS/OPEN/NA（当前：%s）" % (n, res)))
                if not ev or ev in ("—", "-", "–"):
                    findings.append(Finding(
                        "A17", DOC_FILES["01"], no, "A%d 证据为空（写文件:行/镜号）" % n))
                elif "{" in ev or "}" in ev:
                    findings.append(Finding(
                        "A17", DOC_FILES["01"], no,
                        "A%d 证据仍是模板占位（填文件:行/镜号）" % n))
            missing = [n for n in range(1, 17) if n not in seen]
            if missing:
                findings.append(Finding(
                    "A17", DOC_FILES["01"], audit_head,
                    "批次校验记录缺 A%d（A1-A16 必须逐项留痕）" % missing[0]
                    if len(missing) == 1 else
                    "批次校验记录缺 %d 项（首个 A%d；A1-A16 必须逐项留痕）"
                    % (len(missing), missing[0])))
        card_i = _header_index(header, "段号")
        shot_i = _header_index(header, "镜号")
        dur_i = _header_index(header, "生成时长")
        if card_i >= 0 and shot_i >= 0 and dur_i >= 0:
            card_head = head_no
            if not body:
                findings.append(Finding(
                    "A17", DOC_FILES["01"], head_no, "批次生产卡没有数据行（每段一行）"))
            else:
                for no, cells in body:
                    if any("{" in c or "}" in c for c in cells):
                        findings.append(Finding(
                            "A17", DOC_FILES["01"], no,
                            "批次生产卡仍是模板占位（从 02/01/05 复制填写）"))
                        break

    if audit_head is None:
        findings.append(_warn("A17", "01", "未找到批次校验记录（表头含 门/结果/证据），A17 未执行"))
    if card_head is None:
        findings.append(_warn("A17", "01", "未找到批次生产卡（表头含 段号/镜号/生成时长），A17 未执行"))

    # 04 每段段首必须有「本段锁定清单」九项（硬规则 19）
    lock_keys = ("身份锁", "表情锁", "表演锁", "说话人锁", "道具锁",
                 "空间锁", "风格锁", "声音锁", "动作锁")
    if project.doc("04") is not None:
        segs = blocks(project.doc("04"), only_segments=True)
        if not segs:
            findings.append(_warn("A17", "04", "未找到段落块，A17 锁定清单未核对"))
        for block in segs:
            head_no = block[0][0]
            text = "\n".join(t for _no, t in block)
            if "本段锁定清单" not in text:
                findings.append(Finding(
                    "A17", DOC_FILES["04"], head_no,
                    "段落缺「本段锁定清单」（硬规则 19：九项锁定缺一不可）"))
                continue
            missing = [k for k in lock_keys if k not in text]
            if missing:
                findings.append(Finding(
                    "A17", DOC_FILES["04"], head_no,
                    "锁定清单缺 %s（九项缺一不可——硬规则 19）" % "、".join(missing)))
    return findings


OPTIONAL_GATES: List[Tuple[str, GateFn]] = [("A16", gate_a16), ("A17", gate_a17)]


GATES: List[Tuple[str, GateFn]] = [
    ("K1", gate_k1), ("K2", gate_k2), ("K3", gate_k3), ("K4", gate_k4),
    ("K5", gate_k5), ("K6", gate_k6), ("K7", gate_k7), ("K8", gate_k8),
    ("K9", gate_k9), ("K10", gate_k10), ("K11", gate_k11), ("K12", gate_k12),
    ("K13", gate_k13), ("K14", gate_k14), ("K15", gate_k15), ("K16", gate_k16),
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

    ap = argparse.ArgumentParser(description="vigen 项目文件机械校验（K1-K16）")
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

    all_gates = GATES + OPTIONAL_GATES
    valid = {g for g, _ in all_gates}
    selected: Optional[set] = None
    if args.gate:
        wanted = {g.strip().upper() for g in args.gate.split(",") if g.strip()}
        bad = wanted - valid
        if bad:
            print("未知门：%s（合法取值：%s）" % (", ".join(sorted(bad)), ", ".join(g for g, _ in all_gates)))
            return 2
        selected = wanted

    findings: List[Finding] = []
    rc_extra = 0
    if not args.partial:
        for key in REQUIRED_FOR_FULL:
            if project.doc(key) is None:
                findings.append(Finding("PRE", DOC_FILES[key], 0,
                                        "全量校验缺文件 %s（只跑部分文档请用 --partial）" % DOC_FILES[key]))
    for gate_id, gate_fn in (all_gates if selected is not None else GATES):
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
