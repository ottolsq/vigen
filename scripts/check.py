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
_DIALOGUE_LINE_RE = re.compile(r"^(\S{1,30})：(.*)$")
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
    if speaker.startswith("（"):   # 舞台指示/画外说明（（空间：…）等，试跑实测）
        return False
    for pre in _ACTION_PREFIXES:
        if speaker.startswith(pre):
            return False
    return True


def _clean_dialogue(text: str) -> str:
    """去首尾空白与句末标点差异前的规范化：只去首尾空白（逐字=字符级一致）。"""
    return text.strip()


def _dialogue_set_01(project: Project) -> set:
    """01 分场剧本节的台词集合（去首尾空白）。
    支持两种格式：单行式「名字：台词」；两行式「名字（描述）：」换行「"台词"」（试跑实测变体）。"""
    out = set()
    prev_is_speaker = False
    for _, ln in project.section("01", "分场剧本"):
        s = ln.strip()
        if _is_dialogue_line(ln):
            content = _DIALOGUE_LINE_RE.match(s).group(2)
            # 单行式：冒号后有内容；两行式：冒号后为空，台词在下一（若干）行
            if content.strip():
                out.add(_clean_dialogue(content))
                prev_is_speaker = False
            else:
                prev_is_speaker = True
            continue
        if not s:          # 空行不重置两行式状态（说话人行与台词行间常隔空行）
            continue
        if prev_is_speaker and s[0] in "\"“「" and s[-1] in "\"”」":
            out.add(_clean_dialogue(s[1:-1]))
            prev_is_speaker = False
            continue
        prev_is_speaker = False
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


# 04 行级排除：这些技术上下文里的引号是说明文本不是台词（试跑实测误拦模式）
_NON_DIALOGUE_CTX = re.compile(
    r"镜头语言|动机[：:]|自检|改为|约束|删掉|删去|新增|落点[：:]|骨架|参考图|"
    r"V[0-9]+ ?：|原版|实测|换算|写法|槽位|画面文字|标题|声音补充|语气词|"
    r"口型|→|表演[：:]|情绪从|演法[：:]|PERFORMANCE LOCK|张力|象征|"
    r"落地后|声景|AUDIO|\[x\]|勾选|尾注|拆条理由|@\{\{ref|出场人物|"
    r"从.+到.|收着演|不接话|全程收")


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
            if _NON_DIALOGUE_CTX.search(row):
                continue
            if not re.search(r"：\"|：\"|说|语气|情绪|画外音|（", row):
                continue
            findings.append(Finding(
                "K1", fname, line_no,
                "台词与01定稿不一致：「%s」（01 定稿中无此句——改写/修订后须从 01 逐字搬运）" % t))

    if project.doc("05") is not None:
        for line_no, text in _dialogue_rows_05(project):
            t = _clean_dialogue(text)
            if len(t) >= 2 and t[0] in '"“【' and t[-1] in '"”】':
                t = _clean_dialogue(t[1:-1])
            if not t or t in base:
                continue
            findings.append(Finding(
                "K1", DOC_FILES["05"], line_no,
                "台词与01定稿不一致：「%s」（05 台词总账须与 01 逐字一致）" % t))
    return findings


# ---------------------------------------------------------------- K2 时长

_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)s")

# 02 目标模型 → 视频上限（秒）；未识别模型跳过上限检查（宁松勿滥）
_MODEL_CAP = {
    "happyhorse": 15.0,
    "h3": 15.0,
    "minimax": 15.0,
    "seedance": 15.0,
}


def _video_cap(project: Project) -> Optional[float]:
    """从 02 目标模型表的'视频'行解析时长上限；解析不出返回 None。"""
    lines = project.doc("02")
    if lines is None:
        return None
    for ln in lines:
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.split("|")[1:-1]]
        if len(cells) >= 2 and cells[0] == "视频":
            m = _DURATION_RE.search(cells[2] if len(cells) > 2 else cells[1])
            if m:
                return float(m.group(1))
            low = (cells[1] + (cells[2] if len(cells) > 2 else "")).lower()
            for key, cap in _MODEL_CAP.items():
                if key in low:
                    return cap
            return None
    return None


def _storyboard_rows(project: Project) -> List[Tuple[int, List[str]]]:
    """01 分镜总览表数据行：(行号, 单元格)。表头含'镜号'才解析。"""
    out = []
    for i, ln in project.section("01", "分镜总览表"):
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.split("|")[1:-1]
                 if c.strip() not in ("", "---")]
        if not cells:
            continue
        if cells[0] == "镜号":
            continue
        if set(cells[0]) <= {"-", " ", ":"}:
            continue
        out.append((i, cells))
    return out


def gate_k2(project: Project, partial: bool) -> List[Finding]:
    """K2 时长：每镜生成时长 ≤ 模型上限；05 朗读时长 ≤ 所在镜头时长。"""
    findings: List[Finding] = []
    cap = _video_cap(project)

    if project.doc("01") is not None and cap is not None:
        for line_no, cells in _storyboard_rows(project):
            if len(cells) < 3:
                continue
            m = _DURATION_RE.search(cells[2])  # 生成时长列
            if not m:
                continue
            dur = float(m.group(1))
            if dur > cap:
                findings.append(Finding(
                    "K2", DOC_FILES["01"], line_no,
                    "生成时长 %gs 超模型上限 %gs（happyhorse 3-15s / H3 4-15s——超限须拆条+尾帧续接）"
                    % (dur, cap)))

    if project.doc("05") is not None and project.doc("01") is not None:
        for line_no, text in _dialogue_rows_05(project):
            pass  # 朗读时长校验在下方按列做
    # 05 逐行按表解析（朗读时长列 vs 所在镜头时长列）
    if project.doc("05") is not None:
        lines = project.doc("05")
        col_read = col_shot = -1
        for i, ln in enumerate(lines, start=1):
            if not ln.startswith("|"):
                col_read = col_shot = -1
                continue
            cells = [c.strip() for c in ln.split("|")[1:-1]]
            if "朗读时长" in cells and "所在镜头时长" in cells:
                col_read = cells.index("朗读时长")
                col_shot = cells.index("所在镜头时长")
                continue
            if col_read >= 0 and len(cells) > max(col_read, col_shot):
                if set(cells[0]) <= {"-", " ", ":"} or cells[0].startswith("{"):
                    continue
                try:
                    rd = float(_DURATION_RE.search(cells[col_read]).group(1))
                    sh = float(_DURATION_RE.search(cells[col_shot]).group(1))
                except (AttributeError, ValueError):
                    continue
                if rd > sh:
                    findings.append(Finding(
                        "K2", DOC_FILES["05"], i,
                        "台词朗读超镜头时长：朗读 %gs > 镜头 %gs（台词时长 ≥ 镜头时长须延长时间码或拆多镜——A3）"
                        % (rd, sh)))
    return findings


# ---------------------------------------------------------------- K3 锚定逐字

_ANCHOR_PHRASE_RE = re.compile(r"^\| 锚定短语（中文） \| (.+?) \|$")


def _character_anchors(project: Project) -> List[Tuple[str, str]]:
    """02 角色锚定表：返回 (角色名, 中文锚定短语)。"""
    out = []
    lines = project.doc("02")
    if lines is None:
        return out
    current = None
    for ln in lines:
        if ln.startswith("### ") and not ln.startswith("### "):
            pass
        if ln.startswith("### ") and len(ln.strip()) > 4:
            name = ln.strip()[4:].strip()
            if name and "锚定表" not in name:
                current = name
        m = _ANCHOR_PHRASE_RE.match(ln.strip())
        if m and current:
            out.append((current, m.group(1).strip()))
            current = None
    return out


def _palette_hexes(project: Project) -> List[str]:
    """02 色彩基调表登记的全部色号。"""
    out = []
    for _, ln in project.section("02", "色彩基调"):
        for m in _HEX_RE.finditer(ln):
            if m.group(0) not in out:
                out.append(m.group(0))
    return out


def gate_k3(project: Project, partial: bool) -> List[Finding]:
    """K3 锚定逐字：02 色号在 04 每段 FORMAT 节逐字出现；
    04 出现的角色若无 REF 图绑定则须逐字含其锚定短语（A1 豁免：视频端有 REF 承载时由图锁定）。"""
    if project.doc("02") is None or project.doc("04") is None:
        return []
    findings: List[Finding] = []
    lines = project.doc("04")

    # 色号：每个段落的 FORMAT 行须含全部 02 登记色号（段落级，非每行）
    hexes = _palette_hexes(project)
    if hexes:
        seg_start = None
        seg_format: List[int] = []
        for i, ln in enumerate(lines, start=1):
            if ln.startswith("## 段落"):
                if seg_start is not None and seg_format:
                    seg_text = "\n".join(lines[n - 1] for n in seg_format)
                    for hx in hexes:
                        if hx not in seg_text:
                            findings.append(Finding(
                                "K3", DOC_FILES["04"], seg_format[0],
                                "色彩基调色号缺失：%s 未逐字出现（02 色板登记项，FORMAT 色调行须逐字含全部色号——A1）" % hx))
                seg_start = i
                seg_format = []
            elif seg_start is not None and ln.lstrip().startswith("色调："):
                seg_format.append(i)
        if seg_start is not None and seg_format:
            seg_text = "\n".join(lines[n - 1] for n in seg_format)
            for hx in hexes:
                if hx not in seg_text:
                    findings.append(Finding(
                        "K3", DOC_FILES["04"], seg_format[0],
                        "色彩基调色号缺失：%s 未逐字出现（02 色板登记项，FORMAT 色调行须逐字含全部色号——A1）" % hx))

    # 角色锚定：04 全文出现角色名但该角色无 @REF 绑定 → 锚定短语须逐字出现
    anchors = _character_anchors(project)
    doc_text = "\n".join(lines)
    bound_names = set()
    for name, _ in anchors:
        # 绑定=ACTIVE REFERENCES 的 "@ REF-..." 行提及该角色（参考素材汇总行不算绑定）
        if re.search(r"@\s*REF-[A-Z0-9-]+[^\n]*%s" % re.escape(name), doc_text):
            bound_names.add(name)
    for name, phrase in anchors:
        if name in bound_names:
            continue
        if name not in doc_text:
            continue
        if phrase not in doc_text:
            line_no = next((i for i, ln in enumerate(lines, start=1)
                            if name in ln), 0)
            findings.append(Finding(
                "K3", DOC_FILES["04"], line_no,
                "角色「%s」锚定短语缺失：该角色无 REF 图绑定，锚定短语须逐字出现（02 登记：%s…——A1，无图承载时文字必须锁）"
                % (name, phrase[:24])))
    return findings


# ---------------------------------------------------------------- K4 稳定镜号

# 合法镜号：1 / 2 / S3 / S3a（后缀式插入）
_SHOTID_RE = re.compile(r"^(S?\d+[a-z]?)(?:（[^）]*）)?$")
# 作废行：~~S3b~~（v3 作废）
_VOIDED_RE = re.compile(r"^~~(S?\d+[a-z]?)~~")
# 03/04 引用的镜号形态：镜1 / 镜头1 / S3a
_REF_RE = re.compile(r"(?:镜|镜头)(S?\d+[a-z]?)")
# 04 镜头块标题行：0.0s–4.0s｜镜头1｜标题
_BLOCK_RE = re.compile(r"(?:镜|镜头)(S?\d+[a-z]?)[｜|]")


def _storyboard_ids(project: Project) -> Tuple[dict, dict]:
    """返回 (活动镜号→行号, 作废镜号→行号)。"""
    live: dict = {}
    voided: dict = {}
    for line_no, cells in _storyboard_rows(project):
        raw = cells[0]
        vm = _VOIDED_RE.match(raw)
        if vm:
            voided.setdefault(vm.group(1), line_no)
            continue
        m = _SHOTID_RE.match(raw)
        if m:
            live.setdefault(m.group(1), line_no)
    return live, voided


def gate_k4(project: Project, partial: bool) -> List[Finding]:
    """K4 稳定镜号：01 镜号唯一（作废行除外）；03/04 引用的镜号必须存在于 01
    且不引用已作废镜号。"""
    if project.doc("01") is None:
        return []
    findings: List[Finding] = []
    live, voided = _storyboard_ids(project)

    # 唯一性：同镜号出现两行（后一行重复）
    seen: set = set()
    for line_no, cells in _storyboard_rows(project):
        raw = cells[0]
        if _VOIDED_RE.match(raw):
            continue
        m = _SHOTID_RE.match(raw)
        if not m:
            continue
        sid = m.group(1)
        if sid in seen:
            findings.append(Finding(
                "K4", DOC_FILES["01"], line_no,
                "镜号重复：%s 已分配（稳定镜号规则：插入用后缀式 S3a，不重排已有镜号）" % sid))
        seen.add(sid)

    # 引用解析（03/04）
    for key in ("03", "04"):
        lines = project.doc(key)
        if lines is None:
            continue
        for i, ln in enumerate(lines, start=1):
            for m in _REF_RE.finditer(ln):
                ref = m.group(1)
                # 跳过表格里的"镜1-2"区间中段？01 覆盖列写"镜1-2"合法——
                # 引用检查只对 03/04 的镜头块/情景图标题行生效
                if ref in live:
                    continue
                if ref in voided:
                    findings.append(Finding(
                        "K4", DOC_FILES[key], i,
                        "引用了已作废镜号：镜%s（作废镜号保留行号仅供追溯，禁止再引用）" % ref))
                else:
                    findings.append(Finding(
                        "K4", DOC_FILES[key], i,
                        "引用了01分镜表不存在的镜号：镜%s（03 资产矩阵/04 段落须与 01 镜号对齐）" % ref))
    return findings


# ---------------------------------------------------------------- K9 情节点覆盖

_PLOT_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|")


def _plot_rows(project: Project) -> List[Tuple[int, str, str, str]]:
    """01 情节点清单：(行号, 情节点文本, 覆盖镜号列, 状态列)。表头含'情节点'才解析。"""
    out = []
    lines = project.doc("01")
    if lines is None:
        return out
    col_cov = col_st = -1
    for i, ln in enumerate(lines, start=1):
        if not ln.startswith("|"):
            col_cov = col_st = -1
            continue
        cells = [c.strip() for c in ln.split("|")[1:-1]]
        if "情节点" in cells and "覆盖镜号" in cells:
            col_cov = cells.index("覆盖镜号")
            col_st = cells.index("状态")
            continue
        if col_cov >= 0 and len(cells) > max(col_cov, col_st):
            if set(cells[0]) <= {"-", " ", ":"} or not cells[0].isdigit():
                continue
            out.append((i, cells[1], cells[col_cov], cells[col_st]))
    return out


def gate_k9(project: Project, partial: bool) -> List[Finding]:
    """K9 情节点覆盖：双向核对——无擅自删减（行存在），无漏拍（覆盖镜号非空+状态✓+
    引用镜号存在于 01 分镜表）。"""
    if project.doc("01") is None:
        return []
    findings: List[Finding] = []
    live, _voided = _storyboard_ids(project)

    for line_no, text, cov, status in _plot_rows(project):
        label = text[:20]
        if not cov:
            findings.append(Finding(
                "K9", DOC_FILES["01"], line_no,
                "情节点%s未覆盖：覆盖镜号列为空（分镜必须 100%% 覆盖情节点——硬规则7；"
                "不拍需在分镜表写弃拍理由）" % label))
            continue
        if "✓" not in status:
            findings.append(Finding(
                "K9", DOC_FILES["01"], line_no,
                "情节点%s状态未勾：状态列须 ✓（未拍/改派须写明处置）" % label))
        for m in _REF_RE.finditer(cov):
            ref = m.group(1)
            if ref not in live:
                findings.append(Finding(
                    "K9", DOC_FILES["01"], line_no,
                    "情节点%s覆盖镜号镜%s在01分镜表不存在" % (label, ref)))
    return findings


# ---------------------------------------------------------------- K5 强调手段配额

EMPHASIS_WORDS = ("慢动作", "慢镜", "Time Ramp", "定格", "闪白", "短促推近", "冲击重复")
# 峰值来源（CT2）
_PEAK_RE = re.compile(r"←峰值：(情节点\d+|交手账R\d+)")


def _segments_04(project: Project) -> List[Tuple[int, List[str]]]:
    """04 按 '## 段落' 分块：返回 (段落起始行号, 块内行列表)。"""
    lines = project.doc("04")
    if lines is None:
        return []
    out: List[Tuple[int, List[str]]] = []
    start = None
    buf: List[str] = []
    for i, ln in enumerate(lines, start=1):
        if ln.startswith("## 段落"):
            if start is not None:
                out.append((start, buf))
            start = i
            buf = []
        elif start is not None:
            buf.append(ln)
    if start is not None:
        out.append((start, buf))
    return out


def _combat_rounds(project: Project) -> set:
    """01 打斗交手账小节登记的回合号集合（纯数字：'1'、'2'…）。"""
    return {m.group(1)
            for _, ln in project.section("01", "打斗交手账")
            for m in re.finditer(r"R(\d+)", ln)}


def gate_k5(project: Project, partial: bool) -> List[Finding]:
    """K5 强调手段配额：每段慢镜类 ≤2 处；每处强调手段须有 CT2 峰值标注
    且来源可解析（情节点N 含【峰】/ 交手账RN 存在）。"""
    if project.doc("04") is None:
        return []
    findings: List[Finding] = []
    rounds = _combat_rounds(project)
    # 情节点【峰】编号集合（表内 # 列序号）
    plot_peak_ids = set()
    rows = _plot_rows(project)
    for idx, (line_no, text, _, _) in enumerate(rows, start=1):
        if "【峰】" in text:
            plot_peak_ids.add(str(idx))

    for seg_line, seg in _segments_04(project):
        # 配额（慢镜类计数）
        slow_hits = 0
        for off, ln in enumerate(seg):
            for w in EMPHASIS_WORDS:
                if w in ln:
                    slow_hits += 1
                    # 标注检查：同行须有 ←峰值：
                    pm = _PEAK_RE.search(ln)
                    if not pm:
                        findings.append(Finding(
                            "K5", DOC_FILES["04"], seg_line + off,
                            "强调手段无峰值标注：「%s」处须标注 ←峰值：情节点N/交手账RN"
                            "（强调手段只花在已点名峰值上——峰值稀缺品）" % w))
                    else:
                        src = pm.group(1)
                        if src.startswith("交手账R"):
                            if src[len("交手账R"):] not in rounds:
                                findings.append(Finding(
                                    "K5", DOC_FILES["04"], seg_line + off,
                                    "峰值来源无法解析：%s（01 打斗交手账无此回合号）" % src))
                        elif src.startswith("情节点"):
                            if src[len("情节点"):] not in plot_peak_ids:
                                findings.append(Finding(
                                    "K5", DOC_FILES["04"], seg_line + off,
                                    "峰值来源无法解析：%s（01 情节点清单该行无【峰】标记）" % src))
        if slow_hits > 2:
            findings.append(Finding(
                "K5", DOC_FILES["04"], seg_line,
                "慢镜超配额：本段 %d 处 > 2（配额是上限不是任务；处处慢镜就没有哪一下是冲击）" % slow_hits))
    return findings


# ---------------------------------------------------------------- K6 运镜条件门

CT1_RE = re.compile(
    r"^(reveal|pressure|alignment|relationship|transition)\(R[1-7]\)：\S")
# 剧情特征 → 必现运镜族（A12）
_CHASE_WORDS = re.compile(r"奔跑|追逐|追|逃")
_REVEAL_WORDS = re.compile(r"揭示|发现|看见|真相|认出")
_FOLLOW_FAMILY = re.compile(r"跟拍|横移|跟随")
_REVEAL_FAMILY = re.compile(r"摇|后拉|拉远|俯仰")


def _motive_cells(project: Project) -> List[Tuple[int, str]]:
    """01 分镜表运镜动机列：(行号, 单元格文本)。"""
    out = []
    lines = project.doc("01")
    if lines is None:
        return out
    col = -1
    for i, ln in enumerate(lines, start=1):
        if not ln.startswith("|"):
            col = -1
            continue
        cells = [c.strip() for c in ln.split("|")[1:-1]]
        if "运镜动机" in " ".join(cells):
            for idx, c in enumerate(cells):
                if "运镜动机" in c:
                    col = idx
                    break
            continue
        if col >= 0 and len(cells) > col:
            if set(cells[0]) <= {"-", " ", ":"} or cells[0].startswith("{"):
                continue
            out.append((i, cells[col] if len(cells) > col else ""))
    return out


def gate_k6(project: Project, partial: bool) -> List[Finding]:
    """K6 运镜条件门：剧情特征→必现运镜族；动机列 CT1 格式。"""
    if project.doc("01") is None:
        return []
    findings: List[Finding] = []
    plot_text = "\n".join(ln for _, ln in project.section("01", "情节点清单"))
    rows = _storyboard_rows(project)
    cam_text = "\n".join(cells[4] if len(cells) > 4 else ""
                         for _, cells in rows)  # 运镜列

    if _CHASE_WORDS.search(plot_text) and not _FOLLOW_FAMILY.search(cam_text):
        hitline = next((ln for _, ln in project.section("01", "情节点清单")
                        if _CHASE_WORDS.search(ln)), "")
        findings.append(Finding(
            "K6", DOC_FILES["01"], 0,
            "剧情含奔跑/追逐/逃（%s）但分镜运镜列无跟拍族（跟拍/横移/跟随 ≥1 且指认镜号——A12）"
            % hitline.strip()[:24]))
    if _REVEAL_WORDS.search(plot_text) and not _REVEAL_FAMILY.search(cam_text):
        hitline = next((ln for _, ln in project.section("01", "情节点清单")
                        if _REVEAL_WORDS.search(ln)), "")
        findings.append(Finding(
            "K6", DOC_FILES["01"], 0,
            "剧情含信息揭示/发现/真相（%s）但分镜运镜列无摇/后拉/俯仰族（信息揭示须停在新信息上——A12）"
            % hitline.strip()[:24]))
    if "【峰】" in plot_text and project.doc("04") is not None:
        doc04 = "\n".join(project.doc("04") or [])
        if not any(w in doc04 for w in EMPHASIS_WORDS):
            findings.append(Finding(
                "K6", DOC_FILES["01"], 0,
                "情节点含【峰】但 04 无任何强调手段（峰值须配手段——慢镜/冲击重复/短促推近等）"))

    for line_no, motive in _motive_cells(project):
        if not motive:
            continue
        if not CT1_RE.match(motive):
            findings.append(Finding(
                "K6", DOC_FILES["01"], line_no,
                "运镜动机列不合CT1（需 五类词(R行号)：一句展开，如 pressure(R3)：台词正压到她身上）：%s" % motive[:30]))
        elif "固定" in motive and "(R7)" not in motive:
            findings.append(Finding(
                "K6", DOC_FILES["01"], line_no,
                "固定机位未报决策表行号（固定=最后一行，必须带 (R7)+理由）：%s" % motive[:30]))
    return findings


# ---------------------------------------------------------------- K7 环境动态层

ENV_MOTION_WORDS = ("风", "尘", "雾", "光斑", "涟漪", "火焰", "衣摆", "树叶",
                    "微振", "机体振动", "水面", "烟", "雪", "雨", "飘", "摇")
_SHOT_BLOCK_RE = re.compile(r"\d+(?:\.\d+)?s[–-]\d+(?:\.\d+)?s[｜|]镜头")


def _shot_blocks_04(project: Project) -> List[Tuple[int, str]]:
    """04 的镜头块：以 '0.0s–4.0s｜镜头N' 行为界，返回 (块首行号, 块文本)。"""
    lines = project.doc("04")
    if lines is None:
        return []
    out: List[Tuple[int, str]] = []
    start = None
    buf: List[str] = []
    for i, ln in enumerate(lines, start=1):
        if _SHOT_BLOCK_RE.search(ln):
            if start is not None:
                out.append((start, "\n".join(buf)))
            start = i
            buf = [ln]
        elif start is not None:
            if ln.strip() == "```" or ln.startswith("ENDING FRAME"):
                out.append((start, "\n".join(buf)))
                start = None
                buf = []
            else:
                buf.append(ln)
    if start is not None:
        out.append((start, "\n".join(buf)))
    return out


def gate_k7(project: Project, partial: bool) -> List[Finding]:
    """K7 环境动态层：04 每个镜头块须含 ≥1 环境运动元素（B13）。"""
    if project.doc("04") is None:
        return []
    findings: List[Finding] = []
    for line_no, block in _shot_blocks_04(project):
        if not any(w in block for w in ENV_MOTION_WORDS):
            m = re.search(r"镜头(S?\d+[a-z]?)", block.splitlines()[0])
            sid = m.group(1) if m else "?"
            findings.append(Finding(
                "K7", DOC_FILES["04"], line_no,
                "镜头%s 无环境动态层元素（每镜 ≥1 环境运动：风/雨/尘/雾/衣摆/微振——固定≠静止，"
                "画面不能像影棚照片）" % sid))
    return findings


# ---------------------------------------------------------------- K8 骨架槽位

SKELETON_A_SECTIONS = ("SCENE CONTEXT", "ACTIVE REFERENCES", "CONTINUITY RULE",
                       "FORMAT", "CAMERA / EDITING", "ENDING FRAME",
                       "PERFORMANCE LOCK", "FACE LOCK", "AUDIO", "LIGHTING", "NO")


def gate_k8(project: Project, partial: bool) -> List[Finding]:
    """K8 骨架槽位：04 每个骨架 A code block 须含全部必备节；骨架 B 须在 01 有理由标注。"""
    lines = project.doc("04")
    if lines is None:
        return []
    findings: List[Finding] = []
    # 找 code block（``` 围栏），块内含 SCENE CONTEXT 即视为骨架 A
    in_block = False
    block_start = 0
    block: List[str] = []
    for i, ln in enumerate(lines, start=1):
        if ln.strip() == "```" and not in_block:
            in_block = True
            block_start = i
            block = []
            continue
        if ln.strip() == "```" and in_block:
            in_block = False
            if any(s in b for b in block for s in ("SCENE CONTEXT",)):
                text = "\n".join(block)
                for sec in SKELETON_A_SECTIONS:
                    if sec not in text:
                        findings.append(Finding(
                            "K8", DOC_FILES["04"], block_start,
                            "骨架A缺节：%s（骨架 A 必备 11 节——prompt-rules 骨架槽位清单）" % sec))
            continue
        if in_block:
            block.append(ln)

    # 骨架 B 须在 01 标注理由
    if re.search(r"## 镜头\d+", "\n".join(lines)):
        note01 = "\n".join(ln for _, ln in project.section("01", "分镜总览表"))
        if "骨架 B" not in note01 and "骨架B" not in note01:
            findings.append(Finding(
                "K8", DOC_FILES["04"], 0,
                "04 含骨架 B 单镜块但 01 分镜表未标注骨架 B 理由（fl2va/一镜到底张力——特例须写明）"))
    return findings


# ---------------------------------------------------------------- K10 PLAN/REF 闭环

_PLANREF_RE = re.compile(r"\b(PLAN|REF)-([A-Z0-9-]+)")


def gate_k10(project: Project, partial: bool) -> List[Finding]:
    """K10 PLAN/REF 闭环：04 无"待补参考图"式模糊字样；REF-id 须在 03 可解析；
    PLAN-id 唯一。"""
    lines = project.doc("04")
    if lines is None:
        return []
    findings: List[Finding] = []
    doc03 = "\n".join(project.doc("03") or [])

    seen_plans: set = set()
    for i, ln in enumerate(lines, start=1):
        if "待补参考图" in ln:
            findings.append(Finding(
                "K10", DOC_FILES["04"], i,
                "模糊占位字样「待补参考图」：缺图须写 PLAN-<ID> 占位（CT5），禁止模糊字样"))
        for m in _PLANREF_RE.finditer(ln):
            kind, oid = m.group(1), m.group(2)
            full = "%s-%s" % (kind, oid)
            if kind == "REF":
                if full not in doc03:
                    findings.append(Finding(
                        "K10", DOC_FILES["04"], i,
                        "REF-%s 在03中无法解析（03 资产引用矩阵须登记同一 REF-id——K10 闭环）" % oid))
            else:  # PLAN
                if full in seen_plans:
                    findings.append(Finding(
                        "K10", DOC_FILES["04"], i,
                        "PLAN-%s 重复登记（挂图占位 ID 须唯一）" % oid))
                seen_plans.add(full)
    return findings


GATES: List[Tuple[str, Callable[[Project, bool], List[Finding]]]] = [
    ("K1", gate_k1),
    ("K2", gate_k2),
    ("K3", gate_k3),
    ("K4", gate_k4),
    ("K5", gate_k5),
    ("K6", gate_k6),
    ("K7", gate_k7),
    ("K8", gate_k8),
    ("K9", gate_k9),
    ("K10", gate_k10),
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
