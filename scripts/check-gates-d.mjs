// K15-K16 门（短剧立项单 / 集结构），行为对齐 check.py。
import { readFileSync } from "node:fs";
import path from "node:path";
import { DOC_FILES, finding, iterTables } from "./vigen-md.mjs";
import { cpLen } from "./check-core.mjs";

const WALL_RANGES = {
  60: [[8, 11], [21, 24], [41, 44]],
  80: [[10, 15], [28, 32], [55, 58]],
  100: [[13, 19], [35, 40], [68, 73]],
  30: [[4, 6], [10, 12], [20, 22]],
  40: [[5, 8], [14, 16], [27, 29]],
  50: [[7, 10], [17, 20], [34, 37]],
};
const FORMAT_TOTALS = {
  standard: [60, 80, 100],
  long: [30, 40, 50],
  manju: [60, 80, 100],
};
const FORMAT_LABEL = { standard: "标准档", long: "长档", manju: "漫剧档" };
const UNIT_CAP = { standard: 30, long: 15, manju: 30 };
const OS_CAP = { standard: 1, long: 2, manju: 1 };
const OS_LEN = { standard: 25, long: 30, manju: 20 };
const VO_CAP = 1;
const VO_LEN = 12;

const UNIT_RE = /([A-Za-z])\s*[（(]\s*(\d+)\s*[-–—~至]\s*(\d+)\s*[)）]/g;
const SPAN_RE = /(\d+)\s*[-–—~至]\s*(\d+)/g;
const VO_LINE_RE = /^(内心独白|独白|心声|旁白|画外音|画面字幕|字幕)(（[^）]*）|\([^)]*\))?\s*[:：]\s*(.+)$/;
const VO_BRACKET_RE = /^\[VO\]\s*[:：]?\s*(.+)$/i;
const WALL_SPLIT = /(一级|二级|三级)/;
const PLACEHOLDER_RE = /[{}]/;
const MENU_FIELDS = ["平台", "档位", "流派", "备案类别"];

function parentSeriesDoc(project) {
  const p = path.join(path.dirname(project.root), DOC_FILES["00"]);
  try {
    return readFileSync(p, "utf8").split(/\r\n|\r|\n/);
  } catch {
    return null;
  }
}

function metaValue(project, ...keys) {
  const docs = [project.doc("00"), parentSeriesDoc(project), project.doc("01")];
  for (const lines of docs) {
    for (const [, header, body] of iterTables(lines || [])) {
      if (header.length < 2 || !header[0].includes("项") || !header[1].includes("值")) {
        continue;
      }
      for (const [, cells] of body) {
        if (cells.length < 2) continue;
        const name = cells[0].replace(/^[* ]+|[* ]+$/g, "").trim();
        if (keys.some((k) => name.includes(k))) {
          const value = cells[1].trim();
          if (value) return value;
        }
      }
    }
  }
  return "";
}

function hasSeriesMeta(project) {
  return project.doc("00") !== null || parentSeriesDoc(project) !== null;
}

function isPlaceholder(value) {
  const v = (value || "").trim();
  return PLACEHOLDER_RE.test(v) || ["—", "-", "–"].includes(v);
}

function filled(value) {
  return Boolean(value) && !isPlaceholder(value);
}

function formState(project) {
  const raw = metaValue(project, "叙事形态").trim();
  if (!raw) return "auto";
  if (isPlaceholder(raw)) {
    if (raw.includes("竖屏") && raw.includes("电影化")) return "ambiguous";
    if (raw.includes("竖屏")) return "short";
    if (raw.includes("电影化")) return "film";
    return "auto";
  }
  if (/(非|不是|不用|不要)\s*竖屏/.test(raw)) return "film";
  const hasShort = raw.includes("竖屏");
  const hasFilm = raw.includes("电影化");
  if (hasShort && hasFilm) return "ambiguous";
  if (hasShort) return "short";
  if (hasFilm) return "film";
  return "auto";
}

function shortForm(project) {
  return formState(project) === "short";
}

function formatState(project) {
  const raw = metaValue(project, "档位").trim();
  if (!raw) return "";
  const hits = ["标准档", "长档", "漫剧档"].filter((k) => raw.includes(k));
  if (hits.length > 1) return "ambiguous";
  if (isPlaceholder(raw)) return "";
  if (!hits.length) return "bad";
  return { 标准档: "standard", 长档: "long", 漫剧档: "manju" }[hits[0]];
}

function shortFormat(project) {
  const state = formatState(project);
  return ["standard", "long", "manju"].includes(state) ? state : "";
}

function parseIntText(text) {
  const m = /(\d+)/.exec(text || "");
  return m ? Number(m[1]) : null;
}

function parseUnits(text) {
  const out = [];
  for (const m of (text || "").matchAll(UNIT_RE)) {
    out.push([m[1], Number(m[2]), Number(m[3])]);
  }
  if (out.length) return out;
  let i = 0;
  for (const m of (text || "").matchAll(SPAN_RE)) {
    out.push(["单元" + (i + 1), Number(m[1]), Number(m[2])]);
    i += 1;
  }
  return out;
}

function parseWalls(text) {
  const level = { 一级: 1, 二级: 2, 三级: 3 };
  const parts = (text || "").split(WALL_SPLIT);
  const out = new Map();
  for (let i = 1; i < parts.length - 1; i += 2) {
    const m = /(\d+)/.exec(parts[i + 1]);
    if (m) out.set(level[parts[i]], Number(m[1]));
  }
  return out;
}

function isNoWall(text) {
  const v = (text || "").trim();
  return v.startsWith("无") && !/\d/.test(v) && !v.includes("第");
}

function wallBounds(total, variant) {
  const base = WALL_RANGES[total];
  if (!base) return null;
  let out = base.map(([lo, hi]) => [lo, hi]);
  if (variant === "投流前置") {
    out[0] = [3, 8];
  } else if (variant === "治愈系后置") {
    out = base.map(([lo, hi]) => [lo + 2, hi + 3]);
  }
  return out;
}

function voKindBody(line) {
  const s = line.trim();
  const m = VO_LINE_RE.exec(s);
  if (m) {
    return [
      ["内心独白", "独白", "心声"].includes(m[1]) ? "os" : "vo",
      m[3],
    ];
  }
  const m2 = VO_BRACKET_RE.exec(s);
  if (m2) return ["os", m2[1]];
  return null;
}

function fieldBody(lines, ...names) {
  for (let i = 0; i < lines.length; i += 1) {
    const s = lines[i].trim();
    for (const name of names) {
      const marker = `【${name}】`;
      if (!s.includes(marker)) continue;
      const body = s
        .slice(s.indexOf(marker) + marker.length)
        .replace(/^[：: ]+/, "")
        .trim();
      if (body) return body;
      for (const nxt of lines.slice(i + 1)) {
        const t = nxt.trim();
        if (!t) continue;
        return t.startsWith("【") ? "" : t;
      }
      return "";
    }
  }
  return null;
}

export function gateK15(project) {
  const state = formState(project);
  if (state === "auto" || state === "film") return [];
  const key = hasSeriesMeta(project) ? "00" : "01";
  const fileName = DOC_FILES[key];
  const findings = [];

  if (state === "ambiguous") {
    findings.push(finding(
      "K15", fileName, 0,
      "叙事形态未选定：值同时含「竖屏短剧」与「电影化」（不要保留模板菜单）",
    ));
  }

  const baseFields = ["平台", "档位", "总集数", "赛道", "流派", "情绪契约", "备案类别"];
  for (const name of baseFields) {
    const value = metaValue(project, name);
    if (!value || isPlaceholder(value)) {
      findings.push(finding(
        "K15", fileName, 0,
        `短剧立项单缺「${name}」或仍是模板占位`,
      ));
    } else if (MENU_FIELDS.includes(name) && value.includes(" / ")) {
      findings.push(finding(
        "K15", fileName, 0,
        `「${name}」未选定（值含多个选项：${value}）`,
      ));
    }
  }

  const fmtState = formatState(project);
  if (fmtState === "ambiguous") {
    findings.push(finding(
      "K15", fileName, 0,
      `档位未选定：值同时含多个档位（${metaValue(project, "档位")}）`,
    ));
  } else if (fmtState === "bad") {
    findings.push(finding(
      "K15", fileName, 0,
      `档位「${metaValue(project, "档位")}」无法识别（须含 标准档/长档/漫剧档）`,
    ));
  }

  const rawTotal = metaValue(project, "总集数");
  const total = isPlaceholder(rawTotal) ? null : parseIntText(rawTotal);
  if (total === null || total <= 0) {
    findings.push(finding(
      "K15", fileName, 0,
      "总集数不是正整数或仍是模板占位",
    ));
    return findings;
  }

  const fmt = shortFormat(project);
  if (fmt) {
    const known = FORMAT_TOTALS[fmt];
    const allKnown = new Set(Object.values(FORMAT_TOTALS).flat());
    if (allKnown.has(total) && !known.includes(total)) {
      findings.push(finding(
        "K15", fileName, 0,
        `总集数 ${total} 不属于「${FORMAT_LABEL[fmt]}」的集数档（${[...known].sort((a, b) => a - b).join("/")}）`,
      ));
    }
  }

  if (total <= 1) return findings;

  const emotionFlow = metaValue(project, "流派").includes("情绪流");
  const rawUnits = metaValue(project, "单元划分");
  if (!rawUnits || isPlaceholder(rawUnits)) {
    if (emotionFlow) {
      findings.push(finding(
        "K15", fileName, 0,
        "情绪流项目缺「单元划分」（剧情流可写「—」）",
      ));
    }
  } else {
    const units = parseUnits(rawUnits);
    if (!units.length) {
      findings.push(finding(
        "K15", fileName, 0,
        "单元划分无法解析（写法：A(1-25) / B(26-52)）",
      ));
    } else {
      const cap = UNIT_CAP[fmt] ?? 30;
      let prevEnd = 0;
      for (const [label, start, end] of units) {
        if (start !== prevEnd + 1) {
          findings.push(finding(
            "K15", fileName, 0,
            `单元划分不连续：单元${label} 起点第${start}集，上一单元终点第${prevEnd}集`,
          ));
        }
        if (end < start) {
          findings.push(finding(
            "K15", fileName, 0,
            `单元${label} 区间 ${start}-${end} 非法`,
          ));
        }
        if (end - start + 1 > cap) {
          findings.push(finding(
            "K15", fileName, 0,
            `单元${label} 跨 ${end - start + 1} 集 > 上限 ${cap}（单矛盾硬帽）`,
          ));
        }
        prevEnd = Math.max(prevEnd, end);
      }
      if (prevEnd !== total) {
        findings.push(finding(
          "K15", fileName, 0,
          `单元划分止于第${prevEnd}集，与总集数 ${total} 不一致`,
        ));
      }
    }
  }

  const rawVariant = metaValue(project, "付费墙变体");
  let variant = "标准";
  if (isPlaceholder(rawVariant)) {
    findings.push(finding(
      "K15", fileName, 0,
      "付费墙变体未选定（仍是模板占位）",
    ));
  } else if (rawVariant.includes("投流")) {
    variant = "投流前置";
  } else if (rawVariant.includes("后置") || rawVariant.includes("治愈")) {
    variant = "治愈系后置";
  } else if (rawVariant.includes("无墙") || rawVariant.includes("广告")) {
    variant = "无墙";
  }

  const rawWalls = metaValue(project, "付费墙落位");
  if (!rawWalls || isPlaceholder(rawWalls)) {
    findings.push(finding(
      "K15", fileName, 0,
      "短剧立项单缺「付费墙落位」或仍是模板占位",
    ));
  } else if (variant === "无墙") {
    if (!isNoWall(rawWalls)) {
      findings.push(finding(
        "K15", fileName, 0,
        "付费墙变体=无墙，但「付费墙落位」填了具体墙位",
      ));
    }
  } else if (isNoWall(rawWalls)) {
    // 广告分账无付费墙
  } else {
    const walls = parseWalls(rawWalls);
    const ranges = wallBounds(total, variant);
    for (const [level, label] of [[1, "一级"], [2, "二级"], [3, "三级"]]) {
      if (!walls.has(level)) {
        findings.push(finding(
          "K15", fileName, 0,
          `付费墙落位缺「${label}墙 第N集」`,
        ));
        continue;
      }
      const wall = walls.get(level);
      if (!(1 <= wall && wall <= total)) {
        findings.push(finding(
          "K15", fileName, 0,
          `${label}墙 第${wall}集 超出总集数 ${total}`,
        ));
        continue;
      }
      if (ranges && !(ranges[level - 1][0] <= wall && wall <= ranges[level - 1][1])) {
        findings.push(finding(
          "K15", fileName, 0,
          `${label}墙 第${wall}集 不在总集数 ${total} 的允许区间 ${ranges[level - 1][0]}~${ranges[level - 1][1]}（变体：${variant}）`,
        ));
      }
    }
  }
  return findings;
}

export function gateK16(project, partial = false) {
  if (!shortForm(project)) return [];
  const lines = project.doc("01");
  if (lines === null) {
    if (partial) return [];
    return [finding(
      "K16", DOC_FILES["01"], 0,
      "叙事形态=竖屏短剧但缺 01 文件，无法核对本集结构",
    )];
  }
  const fmt = shortFormat(project) || "standard";
  const findings = [];

  const settlement = fieldBody(lines, "本集结算");
  if (!filled(settlement)) {
    findings.push(finding(
      "K16", DOC_FILES["01"], 0,
      "【本集结算】缺失或未填（空/模板占位）——须写主角可见反将 + 反派为本次施压付代价",
    ));
  }

  const breakBody = fieldBody(lines, "本集断章卡点", "本集断章");
  if (!filled(breakBody)) {
    findings.push(finding(
      "K16", DOC_FILES["01"], 0,
      "【本集断章卡点】缺失或未填（空/模板占位）——每集末拍必须是断章公式之一",
    ));
  }

  if (fmt === "long") {
    const mid = fieldBody(lines, "本集中段小钩", "中段小钩");
    if (!filled(mid)) {
      findings.push(finding(
        "K16", DOC_FILES["01"], 0,
        "【本集中段小钩】缺失或未填（空/模板占位）——长档 ≈90 秒处必设新信息/新威胁",
      ));
    }
  }

  const osCap = OS_CAP[fmt] ?? 1;
  const osLen = OS_LEN[fmt] ?? 25;
  let osCount = 0;
  let voCount = 0;
  let prevVo = false;
  for (const ln of lines) {
    const s = ln.trim();
    if (!s) continue;
    const entry = voKindBody(s);
    if (entry === null) {
      prevVo = false;
      continue;
    }
    const [kind, body] = entry;
    const clean = body.replace(/[\s，。！？；：、…—\-·“”"'‘’（）()《》!?.,]/g, "");
    if (kind === "os") {
      osCount += 1;
      if (cpLen(clean) > osLen) {
        findings.push(finding(
          "K16", DOC_FILES["01"], 0,
          `内心独白单处 ${cpLen(clean)} 字 >${osLen}（只写具体的账）`,
        ));
      }
    } else {
      voCount += 1;
      if (cpLen(clean) > VO_LEN) {
        findings.push(finding(
          "K16", DOC_FILES["01"], 0,
          `旁白/字幕单处 ${cpLen(clean)} 字 >${VO_LEN}`,
        ));
      }
    }
    if (prevVo) {
      findings.push(finding(
        "K16", DOC_FILES["01"], 0,
        "连续两条独白/旁白（禁连排）",
      ));
    }
    prevVo = true;
  }

  if (osCount > osCap) {
    findings.push(finding(
      "K16", DOC_FILES["01"], 0,
      `内心独白 ${osCount} 处 > ${osCap}（${fmt}配额）`,
    ));
  }
  if (voCount > VO_CAP) {
    findings.push(finding(
      "K16", DOC_FILES["01"], 0,
      `旁白/字幕 ${voCount} 处 > ${VO_CAP}`,
    ));
  }

  const breakIdx = lines.findIndex((ln) => ln.includes("【本集断章"));
  if (breakIdx !== -1) {
    for (let j = breakIdx - 1; j >= 0; j -= 1) {
      const s = lines[j].trim();
      if (!s) continue;
      if (voKindBody(s)) {
        findings.push(finding(
          "K16", DOC_FILES["01"], 0,
          "独白/旁白紧贴断章收尾（断章必须落在画面/事件上）",
        ));
      }
      break;
    }
  }
  return findings;
}
