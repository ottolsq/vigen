// vigen 项目文档解析层（check.mjs 的依赖模块）——与 scripts/vigen_md.py 行为对齐。
// 只读：本模块不写任何文件。
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

export const DOC_FILES = {
  "00": "00_剧情状态.md",
  "01": "01_方案与剧本.md",
  "02": "02_锚定表.md",
  "03": "03_图片提示词.md",
  "04": "04_视频提示词.md",
  "05": "05_语音台词表.md",
  "06": "06_剪辑清单.md",
};

export function finding(gate, file, line, message) {
  return { gate, file, line, message };
}

export function row(line, cells) {
  return { line, cells };
}

export class Project {
  constructor(root) {
    this.root = path.resolve(root);
    this.cache = new Map();
  }

  path(key) {
    return path.join(this.root, DOC_FILES[key]);
  }

  doc(key) {
    if (this.cache.has(key)) return this.cache.get(key);
    // 04 分卷（V3.17）：有 04_视频提示词_*.md 时按文件名排序合并；base 只作索引。
    if (key === "04") {
      let volumes = [];
      try {
        volumes = readdirSync(this.root)
          .filter((name) => /^04_视频提示词_.*\.md$/.test(name))
          .sort();
      } catch {
        volumes = [];
      }
      if (volumes.length) {
        const lines = [];
        for (const name of volumes) {
          try {
            lines.push(...readFileSync(path.join(this.root, name), "utf8").split(/\r\n|\r|\n/));
          } catch {
            // 单卷读取失败时跳过该卷；其余卷仍可校验
          }
        }
        const value = lines.length ? lines : null;
        this.cache.set(key, value);
        return value;
      }
    }
    const p = this.path(key);
    let lines = null;
    try {
      if (existsSync(p) && statSync(p).isFile()) {
        const text = readFileSync(p, "utf8");
        lines = text.split(/\r\n|\r|\n/);
      }
    } catch {
      lines = null;
    }
    this.cache.set(key, lines);
    return lines;
  }

  section(key, heading) {
    const lines = this.doc(key);
    if (lines === null) return [];
    const out = [];
    let inside = false;
    for (let i = 0; i < lines.length; i += 1) {
      const ln = lines[i];
      if (ln.startsWith("## ")) {
        if (inside) break;
        inside = ln.slice(3).trim().startsWith(heading);
        continue;
      }
      if (inside) out.push([i + 1, ln]);
    }
    return out;
  }
}

const SEP_CELL = /^:?-{3,}:?$/;

export function splitCells(line) {
  let s = line.trim();
  if (s.startsWith("|")) s = s.slice(1);
  if (s.endsWith("|")) s = s.slice(0, -1);
  return s.split("|").map((c) => c.trim());
}

function isSeparator(line) {
  const cells = splitCells(line).map((c) => c.replace(/ /g, "")).filter(Boolean);
  return cells.length > 0 && cells.every((c) => SEP_CELL.test(c));
}

export function* iterTables(lines) {
  let i = 0;
  const n = lines.length;
  while (i < n) {
    if (lines[i].trimStart().startsWith("|")) {
      const headNo = i + 1;
      const block = [];
      while (i < n && lines[i].trimStart().startsWith("|")) {
        block.push([i + 1, lines[i]]);
        i += 1;
      }
      const header = splitCells(block[0][1]);
      const body =
        block.length > 1 && isSeparator(block[1][1]) ? block.slice(2) : block.slice(1);
      yield [headNo, header, body.map(([no, text]) => [no, splitCells(text)])];
    } else {
      i += 1;
    }
  }
}

export function colIndex(header, ...names) {
  for (const name of names) {
    for (let i = 0; i < header.length; i += 1) {
      if (header[i].includes(name)) return i;
    }
  }
  return -1;
}

export function cell(r, ...names) {
  for (const name of names) {
    for (const [key, value] of Object.entries(r.cells)) {
      if (key.includes(name)) return value;
    }
  }
  return "";
}

export function tableRows(lines, required, aliases = {}) {
  if (lines === null) return null;
  for (const [, header, body] of iterTables(lines)) {
    const idx = new Map();
    let ok = true;
    for (const name of required) {
      const i = colIndex(header, ...(aliases[name] || [name]));
      if (i < 0) {
        ok = false;
        break;
      }
      idx.set(name, i);
    }
    if (!ok) continue;
    const rows = [];
    for (const [no, cells] of body) {
      const d = {};
      for (let ci = 0; ci < header.length; ci += 1) {
        const name = header[ci];
        if (name && !(name in d)) d[name] = ci < cells.length ? cells[ci] : "";
      }
      rows.push(row(no, d));
    }
    return rows;
  }
  return null;
}

const SEGMENT_HEAD = /^##\s*(段落|段\d|段\s|镜头\s*S?\d)/;
const TIME_RANGE = /^\s*\d+(?:\.\d+)?\s*s?\s*[–\-—~～至]\s*\d+(?:\.\d+)?\s*s?\s*[｜|]/;
const TIME_RANGE_NUM = /^\s*(\d+(?:\.\d+)?)\s*s?\s*[–\-—~～至]\s*(\d+(?:\.\d+)?)\s*s?/;
export function timeRangeSeconds(text) {
  const m = TIME_RANGE_NUM.exec(text);
  if (!m) return null;
  return [Number(m[1]), Number(m[2])];
}

export function isSegmentHeading(text) {
  return SEGMENT_HEAD.test(text);
}

export function blocks(lines, onlySegments = false) {
  if (lines === null) return [];
  const out = [];
  let cur = null;
  for (let i = 0; i < lines.length; i += 1) {
    const ln = lines[i];
    if (ln.startsWith("## ")) {
      if (cur) out.push(cur);
      cur = [[i + 1, ln]];
    } else if (cur) {
      cur.push([i + 1, ln]);
    }
  }
  if (cur) out.push(cur);
  return onlySegments ? out.filter((b) => isSegmentHeading(b[0][1])) : out;
}

const SHOT_HEAD = /^##\s*镜头\s*S?\d/;

export function shotBlocks(lines) {
  const out = [];
  for (const seg of blocks(lines)) {
    if (SHOT_HEAD.test(seg[0][1])) {
      out.push(seg);
      continue;
    }
    let cur = null;
    for (const [no, text] of seg.slice(1)) {
      if (text.trim() === "```") {
        if (cur) {
          out.push(cur);
          cur = null;
        }
        continue;
      }
      if (TIME_RANGE.test(text)) {
        if (cur) out.push(cur);
        cur = [[no, text]];
      } else if (cur) {
        cur.push([no, text]);
      }
    }
    if (cur) out.push(cur);
  }
  return out;
}

export function blockText(block) {
  return block.map(([, t]) => t).join("\n");
}

export function subBlocks(lines, prefix = "### ") {
  if (lines === null) return [];
  const out = [];
  let cur = null;
  for (let i = 0; i < lines.length; i += 1) {
    const ln = lines[i];
    if (ln.startsWith("## ") || ln.startsWith(prefix)) {
      if (cur) out.push(cur);
      cur = ln.startsWith(prefix) ? [[i + 1, ln]] : null;
    } else if (cur) {
      cur.push([i + 1, ln]);
    }
  }
  if (cur) out.push(cur);
  return out;
}

export const SKIP_SECTIONS = new Set([
  "AUDIO",
  "PERFORMANCE LOCK",
  "FACE LOCK",
  "出场人物",
  "NO",
  "LIGHTING",
  "ACTIVE REFERENCES",
  "CONTINUITY RULE",
  "SCENE CONTEXT",
]);

export const QUOTE_RE = /"([^"]+)"|“([^”]+)”|「([^」]+)」/g;
const SPEAKER_CUE = /[：:]\s*$/;

export const ACTION_PREFIXES = [
  "第",
  "格",
  "镜",
  "段",
  "场景状态",
  "场景",
  "镜头",
  "画面",
  "站位",
  "落点",
  "动机",
];

export function dialogueQuotes(lines) {
  if (lines === null) return [];
  const out = [];
  let section = "";
  for (let i = 0; i < lines.length; i += 1) {
    const ln = lines[i];
    const s = ln.trim();
    if (s.startsWith(">") || s.startsWith("#") || s.startsWith("|") || s.includes("→")) {
      continue;
    }
    if (SKIP_SECTIONS.has(s)) {
      section = s;
      continue;
    }
    if (SKIP_SECTIONS.has(section) && !s.startsWith("```")) {
      if (!TIME_RANGE.test(s) && !s.startsWith("## ")) continue;
      section = "";
    }
    for (const m of ln.matchAll(QUOTE_RE)) {
      const text = m[1] ?? m[2] ?? m[3];
      const pre = ln.slice(0, m.index);
      const isCue = SPEAKER_CUE.test(pre.slice(-6));
      const startsLine = pre.replace(/^[ \-·\t]+|[ \-·\t]+$/g, "") === "";
      if (isCue || startsLine) out.push([i + 1, text]);
    }
  }
  return out;
}

export function characterNames(project) {
  const names = new Set();
  for (const [, text] of project.section("02", "角色锚定表")) {
    if (text.startsWith("### ")) {
      const name = text.slice(4).trim().split(/[（(]/)[0].trim();
      if (name && !name.includes("锚定表")) names.add(name);
    }
  }
  for (const [, text] of project.section("01", "人物表")) {
    const m = /^-\s*([^：:（(]{1,20})[：:]/.exec(text.trim());
    if (m) names.add(m[1].trim());
  }
  return names;
}

const DIALOGUE_LINE_RE = /^(\S{1,30})：(.*)$/;

function speakerRest(line, names) {
  const m = DIALOGUE_LINE_RE.exec(line.trim());
  if (!m) return null;
  const speaker = m[1];
  const rest = m[2];
  if (speaker.startsWith("（")) return null;
  if (names.size > 0) {
    if (![...names].some((n) => speaker.startsWith(n))) return null;
  } else if (ACTION_PREFIXES.some((p) => speaker.startsWith(p))) {
    return null;
  }
  return rest;
}

const OPEN_QUOTES = '"“「';
const CLOSE_QUOTES = '"”」';

export function clean(text) {
  let t = text.trim();
  if (t.length >= 2 && OPEN_QUOTES.includes(t[0]) && CLOSE_QUOTES.includes(t[t.length - 1])) {
    t = t.slice(1, -1).trim();
  }
  return t;
}

export function dialogueSet01(project) {
  const out = new Set();
  const names = characterNames(project);
  let prevSpeaker = false;
  for (const [, ln] of project.section("01", "分场剧本")) {
    const s = ln.trim();
    const rest = speakerRest(ln, names);
    if (rest !== null) {
      if (rest.trim()) {
        out.add(clean(rest));
        prevSpeaker = false;
      } else {
        prevSpeaker = true;
      }
      continue;
    }
    if (!s) continue;
    if (
      prevSpeaker &&
      OPEN_QUOTES.includes(s[0]) &&
      CLOSE_QUOTES.includes(s[s.length - 1])
    ) {
      out.add(clean(s.slice(1, -1)));
      prevSpeaker = false;
      continue;
    }
    prevSpeaker = false;
  }
  return out;
}

const QUOTE_PAIRS = new Map([
  ['"', '"'],
  ["“", "”"],
  ["「", "」"],
]);

export function extractDialogueCell(text) {
  const t = text.trim();
  if (t && QUOTE_PAIRS.has(t[0])) {
    const close = QUOTE_PAIRS.get(t[0]);
    const end = t.indexOf(close, 1);
    if (end > 0) return t.slice(1, end).trim();
  }
  return clean(t);
}

export const EMPHASIS_SLOW = ["慢动作", "慢镜", "Time Ramp", "升格"];
export const EMPHASIS_OTHER = ["冲击重复", "短促推近", "定格", "闪白"];
export const EMPHASIS_WORDS = [...EMPHASIS_SLOW, ...EMPHASIS_OTHER];

export const ENV_MOTION_WORDS = [
  "风吹", "风在吹", "风声", "微风", "风穿过", "风穿",
  "衣摆", "衣角", "树叶", "枝叶", "涟漪", "水面", "光斑", "尘埃",
  "雾气", "薄雾", "雾", "火焰", "火苗", "微振", "机体振动",
  "雪", "雨丝", "雨滴", "下雨", "雨点", "飘动", "摇晃", "摆动", "摇曳",
];

export const SKELETON_A_SECTIONS = [
  "SCENE CONTEXT", "ACTIVE REFERENCES", "CONTINUITY RULE", "FORMAT",
  "CAMERA / EDITING", "ENDING FRAME", "PERFORMANCE LOCK", "FACE LOCK",
  "AUDIO", "LIGHTING", "NO",
];

export const PEAK_RE = /←峰值：(情节点\d+|交手账R\d+)/;

export const CHASE_RE = /奔跑|追逐|追捕|追打|追赶|逃跑|逃亡|奔逃|拔腿就跑|追上去/;
export const REVEAL_RE = /揭示|发现真相|真相大白|认出|看穿|识破|露出真面目/;
export const FOLLOW_FAMILY = /跟拍|横移|跟随/;
export const REVEAL_FAMILY = /摇|后拉|拉远|俯仰/;

export const CT1_RE = /^(reveal|pressure|alignment|relationship|transition)\(R[1-7]\)：\S/;
export const HEX_RE = /#[0-9A-Fa-f]{6}/g;
export const DURATION_RE = /(\d+(?:\.\d+)?)\s*s/g;
export const SHOT_ID_RE = /^(S?\d+[a-z]?)(?:（[^）]*）)?$/;
export const VOIDED_RE = /^~~(S?\d+[a-z]?)~~/;
export const REF_SHOT_RE = /(?:镜|镜头)\s*(S?\d+[a-z]?)/g;
export const BEAT_RE = /(?<![A-Za-z0-9])B(\d+[a-z]?)(?:\s*[-–—~至]\s*B?(\d+[a-z]?))?/g;

export function beatIds(text) {
  const out = [];
  for (const m of (text || "").matchAll(BEAT_RE)) {
    const start = m[1];
    const end = m[2];
    if (end && /^\d+$/.test(start) && /^\d+$/.test(end)) {
      const a = Number(start);
      const b = Number(end);
      if (a <= b) {
        for (let i = a; i <= b; i += 1) out.push("B" + i);
        continue;
      }
    }
    out.push("B" + start);
  }
  return out;
}

export const MODEL_CAP = {
  happyhorse: 15.0,
  h3: 15.0,
  minimax: 15.0,
  seedance: 15.0,
};

export const MODEL_MIN = {
  happyhorse: 3.0,
  h3: 4.0,
  minimax: 4.0,
};

export function modelNativeMin(project) {
  const rows = tableRows(project.doc("02"), ["用途", "模型"]);
  for (const r of rows || []) {
    if (!(r.cells["用途"] || "").includes("视频")) continue;
    const text = Object.values(r.cells).join(" ");
    const m = /(\d+(?:\.\d+)?)\s*s?\s*[-–~]\s*(\d+(?:\.\d+)?)\s*s/.exec(text);
    if (m) return Number(m[1]);
    const nums = [...text.matchAll(DURATION_RE)].map((x) => Number(x[1]));
    if (nums.length >= 2) return Math.min(...nums);
    const low = text.toLowerCase();
    for (const [key, lowv] of Object.entries(MODEL_MIN)) {
      if (low.includes(key)) return lowv;
    }
  }
  return null;
}
