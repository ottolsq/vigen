#!/usr/bin/env python
"""vigen 项目文档解析层（check.py 的依赖模块）。

职责：把 01-06 Markdown 解析成结构（表格=按表头名取列、段落=按任意二级标题切块、
镜头块=时间码或 `## 镜头N` 标题），所有 gate 共用同一套解析器——避免同一文件里
存在多套互不一致的表格解析（V3.0 评审 I5）。

只读：本模块不写任何文件。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    gate: str    # "K1".."K10" / "PRE"
    file: str
    line: int    # 1-based；0=文件级
    message: str


@dataclass(frozen=True)
class Row:
    line: int
    cells: Dict[str, str]


class Project:
    """项目目录加载与解析缓存。"""

    def __init__(self, root: Path):
        self.root = Path(root)
        self._cache: Dict[str, Optional[List[str]]] = {}

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
        """'## heading'（前缀匹配）到下一个 '## ' 之间的行，元素 (1-based 行号, 文本)。"""
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


# ------------------------------------------------------------------ 表格

_SEP_CELL = re.compile(r"^:?-{3,}:?$")


def split_cells(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_separator(line: str) -> bool:
    cells = [c.replace(" ", "") for c in split_cells(line)]
    cells = [c for c in cells if c]
    return bool(cells) and all(_SEP_CELL.match(c) for c in cells)


def iter_tables(lines: List[str]):
    """产出 (表头行号, 表头单元格, [(行号, 单元格列表)])。保留空单元格。"""
    i, n = 0, len(lines)
    while i < n:
        if lines[i].lstrip().startswith("|"):
            head_no = i + 1
            block: List[Tuple[int, str]] = []
            while i < n and lines[i].lstrip().startswith("|"):
                block.append((i + 1, lines[i]))
                i += 1
            header = split_cells(block[0][1])
            body = block[2:] if len(block) > 1 and _is_separator(block[1][1]) else block[1:]
            yield head_no, header, [(no, split_cells(t)) for no, t in body]
        else:
            i += 1


def col_index(header: List[str], *names: str) -> int:
    """按表头名找列下标，支持别名（含子串匹配）。找不到返回 -1。"""
    for name in names:
        for i, h in enumerate(header):
            if name in h:
                return i
    return -1


def cell(row: Row, *names: str) -> str:
    """按列名（支持子串/别名）取单元格值；表头可能带后缀，如「运镜动机（CT1：…）」。"""
    for name in names:
        for key, value in row.cells.items():
            if name in key:
                return value
    return ""


def table_rows(lines: Optional[List[str]], required: Tuple[str, ...],
               aliases: Optional[Dict[str, Tuple[str, ...]]] = None) -> Optional[List[Row]]:
    """返回所有满足 required 列的表行（按表头名取值）。

    required 用别名映射后的列名也计入判断。找不到这样的表返回 None。
    """
    if lines is None:
        return None
    alias_map = aliases or {}
    for _head_no, header, body in iter_tables(lines):
        idx: Dict[str, int] = {}
        ok = True
        for name in required:
            i = col_index(header, *alias_map.get(name, (name,)))
            if i < 0:
                ok = False
                break
            idx[name] = i
        if not ok:
            continue
        rows = []
        for no, cells in body:
            d: Dict[str, str] = {}
            for ci, name in enumerate(header):
                if name and name not in d:
                    d[name] = cells[ci] if ci < len(cells) else ""
            rows.append(Row(no, d))
        return rows
    return None


# ------------------------------------------------------------------ 块

_SEGMENT_HEAD = re.compile(r"^##\s*(段落|段\d|段\s|镜头\s*S?\d)")
_TIME_RANGE = re.compile(
    r"^\s*\d+(?:\.\d+)?\s*s?\s*[–\-—~～至]\s*\d+(?:\.\d+)?\s*s?\s*[｜|]")
_TIME_RANGE_NUM = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*s?\s*[–\-—~～至]\s*(\d+(?:\.\d+)?)\s*s?")


def time_range_seconds(text: str):
    """'0.0s–4.0s｜镜头1' → (0.0, 4.0)；不是时间码首行返回 None。"""
    m = _TIME_RANGE_NUM.match(text)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))


def model_native_min(project: Project) -> Optional[float]:
    """02 目标模型「视频」行里区间写法的下限（3-15s → 3.0；4s-15s → 4.0）。"""
    rows = table_rows(project.doc("02"), ("用途", "模型"))
    for row in rows or []:
        if "视频" not in row.cells.get("用途", ""):
            continue
        cell = " ".join(row.cells.values())
        m = re.search(r"(\d+(?:\.\d+)?)\s*s?\s*[-–~]\s*(\d+(?:\.\d+)?)\s*s", cell)
        if m:
            return float(m.group(1))
        nums = [float(x) for x in DURATION_RE.findall(cell)]
        if len(nums) >= 2:
            return min(nums)
        low = cell.lower()
        for key, lowv in MODEL_MIN.items():
            if key in low:
                return lowv
    return None
_SHOT_HEAD = re.compile(r"^##\s*镜头\s*S?\d")
_GEN_SECONDS = re.compile(r"生成\s*(\d+(?:\.\d+)?)\s*s")


def is_segment_heading(text: str) -> bool:
    return bool(_SEGMENT_HEAD.match(text))


def blocks(lines: Optional[List[str]], only_segments: bool = False) -> List[List[Tuple[int, str]]]:
    """按任意 '## ' 切块，返回 [(行号, 文本)] 列表（含标题行）。"""
    if lines is None:
        return []
    out: List[List[Tuple[int, str]]] = []
    cur: Optional[List[Tuple[int, str]]] = None
    for i, ln in enumerate(lines, start=1):
        if ln.startswith("## "):
            if cur:
                out.append(cur)
            cur = [(i, ln)]
        elif cur is not None:
            cur.append((i, ln))
    if cur:
        out.append(cur)
    if only_segments:
        out = [b for b in out if is_segment_heading(b[0][1])]
    return out


def shot_blocks(lines: Optional[List[str]]) -> List[List[Tuple[int, str]]]:
    """镜头块：骨架 B 的 '## 镜头N' 整节；骨架 A 内按时间码首行切。"""
    out: List[List[Tuple[int, str]]] = []
    for seg in blocks(lines):
        if _SHOT_HEAD.match(seg[0][1]):
            out.append(seg)
            continue
        cur: Optional[List[Tuple[int, str]]] = None
        for no, text in seg[1:]:
            if text.strip() == "```":
                if cur:
                    out.append(cur)
                    cur = None
                continue
            if _TIME_RANGE.match(text):
                if cur:
                    out.append(cur)
                cur = [(no, text)]
            elif cur is not None:
                cur.append((no, text))
        if cur:
            out.append(cur)
    return out


def block_text(block: List[Tuple[int, str]]) -> str:
    return "\n".join(t for _, t in block)


def sub_blocks(lines: Optional[List[str]], prefix: str = "### ") -> List[List[Tuple[int, str]]]:
    """按指定级别标题切子块（02 的 '### 角色名' 用）。"""
    if lines is None:
        return []
    out: List[List[Tuple[int, str]]] = []
    cur: Optional[List[Tuple[int, str]]] = None
    for i, ln in enumerate(lines, start=1):
        if ln.startswith("## ") or ln.startswith(prefix):
            if cur:
                out.append(cur)
            cur = [(i, ln)] if ln.startswith(prefix) else None
        elif cur is not None:
            cur.append((i, ln))
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------ 台词

# 04 里这些小节的技术文本不是台词（结构作用域，不是词表黑名单）
SKIP_SECTIONS = frozenset((
    "AUDIO", "PERFORMANCE LOCK", "FACE LOCK", "出场人物", "NO",
    "LIGHTING", "ACTIVE REFERENCES", "CONTINUITY RULE", "SCENE CONTEXT",
))

QUOTE_RE = re.compile(r'"([^"]+)"|“([^”]+)”|「([^」]+)」')
# 台词判据：引号紧跟冒号（说话人/语气描述之后），或整行以引号开头（两行式）
_SPEAKER_CUE = re.compile(r"[：:]\s*$")

ACTION_PREFIXES = ("第", "格", "镜", "段", "场景状态", "场景", "镜头", "画面", "站位", "落点", "动机")


def dialogue_quotes(lines: Optional[List[str]]) -> List[Tuple[int, str]]:
    """04 的台词引号：(行号, 文本)。按结构判定，不按关键词黑名单。"""
    if lines is None:
        return []
    out: List[Tuple[int, str]] = []
    section = ""
    for i, ln in enumerate(lines, start=1):
        s = ln.strip()
        if s.startswith((">", "#", "|")) or "→" in s:
            continue
        if s in SKIP_SECTIONS:
            section = s
            continue
        if section in SKIP_SECTIONS and not s.startswith("```"):
            # 小节标签之前的内容才算离开小节；遇到新镜头块首行也离开
            if not _TIME_RANGE.match(s) and not s.startswith("## "):
                continue
            section = ""
        for m in QUOTE_RE.finditer(ln):
            text = next(g for g in m.groups() if g is not None)
            pre = ln[:m.start()]
            is_cue = bool(_SPEAKER_CUE.search(pre[-6:]))
            starts_line = not pre.strip(" -·\t")
            if is_cue or starts_line:
                out.append((i, text))
    return out


def character_names(project: Project) -> set:
    """02 角色锚定表 + 01 人物表里的角色名（用于 01 台词说话人白名单）。"""
    names = set()
    for _no, text in project.section("02", "角色锚定表"):
        if text.startswith("### "):
            name = re.split(r"[（(]", text[4:].strip())[0].strip()
            if name and "锚定表" not in name:
                names.add(name)
    for _no, text in project.section("01", "人物表"):
        m = re.match(r"^-\s*([^：:（(]{1,20})[：:]", text.strip())
        if m:
            names.add(m.group(1).strip())
    return names


_DIALOGUE_LINE_RE = re.compile(r"^(\S{1,30})：(.*)$")


def _speaker_rest(line: str, names: set) -> Optional[str]:
    m = _DIALOGUE_LINE_RE.match(line.strip())
    if not m:
        return None
    speaker, rest = m.group(1), m.group(2)
    if speaker.startswith("（"):
        return None
    if names:
        if not any(speaker.startswith(n) for n in names):
            return None
    elif any(speaker.startswith(p) for p in ACTION_PREFIXES):
        return None
    return rest


def dialogue_set_01(project: Project) -> set:
    """01 分场剧本的台词集合。支持「名字：台词」与「名字（描述）：」换行「"台词"」。"""
    out: set = set()
    names = character_names(project)
    prev_speaker = False
    for _no, ln in project.section("01", "分场剧本"):
        s = ln.strip()
        rest = _speaker_rest(ln, names)
        if rest is not None:
            if rest.strip():
                out.add(_clean(rest))
                prev_speaker = False
            else:
                prev_speaker = True
            continue
        if not s:
            continue
        if prev_speaker and s[0] in "\"“「" and s[-1] in "\"”」":
            out.add(_clean(s[1:-1]))
            prev_speaker = False
            continue
        prev_speaker = False
    return out


_QUOTE_PAIRS = {'"': '"', "“": "”", "「": "」"}


def extract_dialogue_cell(text: str) -> str:
    """05 单元格 → 台词文本。支持「"台词"（批注）」这种带注形态。"""
    t = text.strip()
    if t and t[0] in _QUOTE_PAIRS:
        close = _QUOTE_PAIRS[t[0]]
        end = t.find(close, 1)
        if end > 0:
            return t[1:end].strip()
    return _clean(t)


def _clean(text: str) -> str:
    """去首尾空白与一层外层引号（A11 逐字比对：引号是容器不是台词）。"""
    t = text.strip()
    if len(t) >= 2 and t[0] in "\"“「" and t[-1] in "\"”」":
        t = t[1:-1].strip()
    return t


def is_dialogue_line(line: str) -> bool:
    """01 说话人行判定（SCR-18：排除全角冒号开头的动作段与（舞台指示）。"""
    m = _DIALOGUE_LINE_RE.match(line.strip())
    if not m:
        return False
    speaker = m.group(1)
    if speaker.startswith("（"):
        return False
    return not any(speaker.startswith(p) for p in ACTION_PREFIXES)


# ------------------------------------------------------------------ 关键词表

EMPHASIS_SLOW = ("慢动作", "慢镜", "Time Ramp", "升格")
EMPHASIS_OTHER = ("冲击重复", "短促推近", "定格", "闪白")
EMPHASIS_WORDS = EMPHASIS_SLOW + EMPHASIS_OTHER

ENV_MOTION_WORDS = (
    "风吹", "风在吹", "风声", "微风", "风穿过", "风穿",
    "衣摆", "衣角", "树叶", "枝叶", "涟漪", "水面", "光斑", "尘埃",
    "雾气", "薄雾", "雾", "火焰", "火苗", "微振", "机体振动",
    "雪", "雨丝", "雨滴", "下雨", "雨点", "飘动", "摇晃", "摆动", "摇曳",
)

SKELETON_A_SECTIONS = (
    "SCENE CONTEXT", "ACTIVE REFERENCES", "CONTINUITY RULE", "FORMAT",
    "CAMERA / EDITING", "ENDING FRAME", "PERFORMANCE LOCK", "FACE LOCK",
    "AUDIO", "LIGHTING", "NO",
)

PEAK_RE = re.compile(r"←峰值：(情节点\d+|交手账R\d+)")

# 剧情特征 → 必现运镜族（A12）
CHASE_RE = re.compile(r"奔跑|追逐|追捕|追打|追赶|逃跑|逃亡|奔逃|拔腿就跑|追上去")
REVEAL_RE = re.compile(r"揭示|发现真相|真相大白|认出|看穿|识破|露出真面目")
FOLLOW_FAMILY = re.compile(r"跟拍|横移|跟随")
REVEAL_FAMILY = re.compile(r"摇|后拉|拉远|俯仰")

CT1_RE = re.compile(
    r"^(reveal|pressure|alignment|relationship|transition)\(R[1-7]\)：\S")

HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*s")

PLANREF_RE = re.compile(r"(PLAN|REF)-([A-Z0-9]+(?:-[A-Z0-9]+)*)")

SHOT_ID_RE = re.compile(r"^(S?\d+[a-z]?)(?:（[^）]*）)?$")
VOIDED_RE = re.compile(r"^~~(S?\d+[a-z]?)~~")
REF_SHOT_RE = re.compile(r"(?:镜|镜头)\s*(S?\d+[a-z]?)")

MODEL_CAP = {
    "happyhorse": 15.0,
    "h3": 15.0,
    "minimax": 15.0,
    "seedance": 15.0,
}
# 模型原生最短时长（models.md：happyhorse 3-15s / H3·MiniMax 4-15s）
MODEL_MIN = {
    "happyhorse": 3.0,
    "h3": 4.0,
    "minimax": 4.0,
}
