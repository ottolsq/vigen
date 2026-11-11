// K13-K14 门（节拍认领 / 钩子与时长预算），行为对齐 check.py。
import {
  DOC_FILES,
  SHOT_ID_RE,
  VOIDED_RE,
  beatIds,
  cell,
  finding,
  iterTables,
  tableRows,
} from "./vigen-md.mjs";
import {
  DUR_ONE,
  REF_SHOT_G,
  STORY_ALIASES,
  shotIds,
  storyRows,
} from "./check-core.mjs";

const BEAT_ID_RE = /^B([1-9]\d*)([a-z]?)$/;
const REF_SHOT_ONE = /(?:镜|镜头)\s*(S?\d+[a-z]?)/;

function kvValue(project, ...keys) {
  for (const [, header, body] of iterTables(project.doc("01") || [])) {
    if (header.length < 2 || !header[0].includes("项") || !header[1].includes("值")) {
      continue;
    }
    for (const [, cells] of body) {
      if (cells.length < 2) continue;
      if (keys.some((k) => cells[0].includes(k))) return cells[1].trim();
    }
  }
  return "";
}

function beatEnabled(project) {
  return kvValue(project, "节拍制").toLowerCase().startsWith("on");
}

function beatRows(project) {
  return tableRows(project.doc("01"), ["节拍号", "认领镜号"]);
}

function shotBeatRows(project) {
  return tableRows(project.doc("01"), ["镜号", "认领节拍"]);
}

function normShotId(raw) {
  const m = REF_SHOT_ONE.exec(raw || "");
  if (m) return m[1];
  const m2 = SHOT_ID_RE.exec((raw || "").trim());
  return m2 ? m2[1] : null;
}

function shotBeatClaims(project) {
  const rows = shotBeatRows(project);
  if (rows === null) return null;
  const out = new Map();
  for (const r of rows) {
    const raw = (r.cells["镜号"] || "").trim();
    if (VOIDED_RE.exec(raw)) continue;
    const sid = normShotId(raw);
    if (sid) out.set(sid, beatIds(r.cells["认领节拍"] || ""));
  }
  return out;
}

function shotOrder(project) {
  const out = new Map();
  for (const r of storyRows(project) || []) {
    const raw = (r.cells["镜号"] || "").trim();
    if (VOIDED_RE.exec(raw)) continue;
    const m = SHOT_ID_RE.exec(raw);
    if (m && !out.has(m[1])) out.set(m[1], out.size);
  }
  return out;
}

function shotSeconds(project) {
  const out = new Map();
  for (const r of storyRows(project) || []) {
    const raw = (r.cells["镜号"] || "").trim();
    if (VOIDED_RE.exec(raw)) continue;
    const m = SHOT_ID_RE.exec(raw);
    const d = DUR_ONE(r.cells["生成时长"] || "");
    if (m && d && !out.has(m[1])) out.set(m[1], Number(d[1]));
  }
  return out;
}

function parseSeconds(text) {
  const m = /(\d+(?:\.\d+)?)\s*(s|秒|min|分钟)/i.exec(text || "");
  if (!m) return null;
  const value = Number(m[1]);
  return ["min", "分钟"].includes(m[2].toLowerCase()) ? value * 60.0 : value;
}

function parseFloatText(text) {
  const m = /(\d+(?:\.\d+)?)/.exec(text || "");
  return m ? Number(m[1]) : null;
}

export function gateK13(project, partial = false) {
  if (!beatEnabled(project)) return [];
  const rows = beatRows(project);
  if (rows === null) {
    return [finding(
      "K13", DOC_FILES["01"], 0,
      "节拍制已启用但未建场次节拍表（表头须含「节拍号」「认领镜号」）",
    )];
  }
  const findings = [];
  const required = ["类型", "内容摘要", "台词字数", "估算秒", "标记"];
  const keys = Object.keys(rows[0].cells);
  const missing = required.filter((c) => !keys.some((k) => k.includes(c)));
  if (missing.length) {
    findings.push(finding(
      "K13", DOC_FILES["01"], rows[0].line,
      `节拍表缺列：${missing.join("、")}`,
    ));
  }

  const hasStoryboard = tableRows(project.doc("01"), ["镜号", "运镜"], STORY_ALIASES) !== null;
  let claims = shotBeatClaims(project);
  const claimChecks = hasStoryboard && claims !== null;
  if (!hasStoryboard) {
    if (!partial) {
      findings.push(finding(
        "K13", DOC_FILES["01"], 0,
        "未建分镜总览表——K13 无法核对「认领镜号」（阶段1b 后必须存在；阶段1a 用 --partial）",
      ));
    }
    claims = new Map();
  } else if (claims === null) {
    findings.push(finding(
      "K13", DOC_FILES["01"], rows[0].line,
      "分镜总览表缺「认领节拍」列——K13 无法双向核对",
    ));
    claims = new Map();
  }

  const [live] = shotIds(project);
  const order = shotOrder(project);
  const beatToShot = new Map();
  const seen = new Set();
  const sceneBases = new Map();
  let prevOrder = -1;

  for (const r of rows) {
    const scene = cell(r, "场次").trim() || "?";
    const bid = cell(r, "节拍号").trim();
    const label = `${scene}/${bid}`;
    const m = BEAT_ID_RE.exec(bid);
    if (!m) {
      findings.push(finding(
        "K13", DOC_FILES["01"], r.line,
        `节拍号「${bid || "空"}」格式非法（须 B1 / B2a）`,
      ));
      continue;
    }
    if (seen.has(bid)) {
      findings.push(finding(
        "K13", DOC_FILES["01"], r.line,
        `节拍号 ${bid} 重复（每场节拍号须唯一）`,
      ));
    }
    seen.add(bid);
    if (!sceneBases.has(scene)) sceneBases.set(scene, new Set());
    sceneBases.get(scene).add(Number(m[1]));
    if (!claimChecks) continue;

    const claim = cell(r, "认领镜号").trim();
    const ids = [...claim.matchAll(REF_SHOT_G())].map((x) => x[1]);
    if (ids.length !== 1) {
      findings.push(finding(
        "K13", DOC_FILES["01"], r.line,
        `节拍${label} 须恰好一个认领镜号（当前：${claim || "空"}）`,
      ));
      continue;
    }
    const sid = ids[0];
    if (!live.has(sid)) {
      findings.push(finding(
        "K13", DOC_FILES["01"], r.line,
        `节拍${label} 认领镜号镜${sid}在01分镜表不存在`,
      ));
      continue;
    }
    beatToShot.set(bid, sid);
    if (claims && !(claims.get(sid) || []).includes(bid)) {
      findings.push(finding(
        "K13", DOC_FILES["01"], r.line,
        `镜${sid} 的认领节拍未包含 ${bid}（双向不一致：节拍表写镜${sid}）`,
      ));
    }
    const pos = order.get(sid);
    if (pos !== undefined) {
      if (pos < prevOrder) {
        findings.push(finding(
          "K13", DOC_FILES["01"], r.line,
          `节拍${label} 认领镜${sid}早于上一拍，节拍顺序与镜号顺序不一致`,
        ));
      }
      prevOrder = Math.max(prevOrder, pos);
    }
  }

  for (const [scene, bases] of sceneBases) {
    if (!bases.size) continue;
    const max = Math.max(...bases);
    const missingBeats = [];
    for (let i = 1; i <= max; i += 1) {
      if (!bases.has(i)) missingBeats.push("B" + i);
    }
    if (missingBeats.length) {
      findings.push(finding(
        "K13", DOC_FILES["01"], 0,
        `场${scene} 节拍号不连续，缺 ${missingBeats.join("、")}`,
      ));
    }
  }

  for (const [sid, bids] of claims) {
    for (const bid of bids) {
      if (!beatToShot.has(bid)) {
        findings.push(finding(
          "K13", DOC_FILES["01"], 0,
          `镜${sid} 认领的 ${bid} 不在场次节拍表`,
        ));
      } else if (beatToShot.get(bid) !== sid) {
        findings.push(finding(
          "K13", DOC_FILES["01"], 0,
          `镜${sid} 认领 ${bid}，但节拍表登记为镜${beatToShot.get(bid)}（双向不一致）`,
        ));
      }
    }
  }

  for (const r of storyRows(project) || []) {
    const raw = (r.cells["镜号"] || "").trim();
    if (VOIDED_RE.exec(raw)) continue;
    const m = SHOT_ID_RE.exec(raw);
    if (!m) continue;
    const line = cell(r, "台词/字幕", "台词").trim();
    if (line && !["—", "-", "–"].includes(line) && !(claims.get(m[1]) || []).length) {
      findings.push(finding(
        "K13", DOC_FILES["01"], r.line,
        `镜${m[1]} 有台词但未认领节拍（认领节拍须写 B 编号，不能是 —）`,
      ));
    }
  }
  return findings;
}

export function gateK14(project) {
  if (!beatEnabled(project)) return [];
  const rows = beatRows(project);
  if (rows === null) return [];
  const findings = [];
  const hooks = [];
  const suspense = [];
  rows.forEach((r, i) => {
    const mark = cell(r, "标记");
    const bid = cell(r, "节拍号").trim();
    if (mark.includes("钩子")) hooks.push([i, bid]);
    if (mark.includes("悬念")) suspense.push([i, bid]);
  });
  if (hooks.length !== 1) {
    findings.push(finding(
      "K14", DOC_FILES["01"], 0,
      `须恰好一个【钩子】标记（当前 ${hooks.length} 个）`,
    ));
  } else if (hooks[0][0] >= 3) {
    findings.push(finding(
      "K14", DOC_FILES["01"], 0,
      `钩子在第 ${hooks[0][0] + 1} 拍（${hooks[0][1]}），须落在前 3 拍`,
    ));
  }
  if (suspense.length !== 1) {
    findings.push(finding(
      "K14", DOC_FILES["01"], 0,
      `须恰好一个【悬念】标记（当前 ${suspense.length} 个）`,
    ));
  } else if (suspense[0][0] !== rows.length - 1) {
    findings.push(finding(
      "K14", DOC_FILES["01"], 0,
      `【悬念】在第 ${suspense[0][0] + 1} 拍（${suspense[0][1]}），须在末拍（第 ${rows.length} 拍）`,
    ));
  }

  const target = parseSeconds(kvValue(project, "总时长", "目标时长"));
  if (target === null) {
    findings.push(finding(
      "K14", DOC_FILES["01"], 0,
      "未找到「总时长/目标时长」——K14 无法核对时长预算",
    ));
    return findings;
  }

  let chars = 0;
  let action = 0;
  const beatSecs = new Map();
  for (const r of rows) {
    const rawChars = cell(r, "台词字数").trim();
    const n = Number(rawChars || 0);
    if (!Number.isFinite(n)) {
      findings.push(finding(
        "K14", DOC_FILES["01"], r.line,
        `节拍${cell(r, "节拍号").trim()} 的台词字数不是数字（${rawChars}）`,
      ));
    } else {
      chars += Math.trunc(n);
    }
    if (cell(r, "类型").includes("动作")) action += 1;
    const sec = parseFloatText(cell(r, "估算秒"));
    if (sec !== null) {
      const sid = [...cell(r, "认领镜号").matchAll(REF_SHOT_G())].map((m) => m[1]).join(" ");
      beatSecs.set(sid, (beatSecs.get(sid) || 0) + sec);
    }
  }
  const dialogueSec = Math.ceil(chars / 4.0);
  const actionSec = action * 2.5;
  const estimated = dialogueSec + actionSec;
  const rawTol = kvValue(project, "时长容差");
  const pctM = /(\d+(?:\.\d+)?)\s*%/.exec(rawTol);
  const pct = pctM ? Number(pctM[1]) : 15.0;
  const tolerance = Math.max((target * pct) / 100.0, 2.5);
  const mode = kvValue(project, "时长模式");
  const upperOnly = mode.includes("上限") || mode.includes("范围");
  if (upperOnly) {
    if (estimated > target + 1.0) {
      findings.push(finding(
        "K14", DOC_FILES["01"], 0,
        `时长超上限：台词 ${dialogueSec.toFixed(0)}s + 动作 ${actionSec.toFixed(1)}s = ${estimated.toFixed(1)}s > 上限 ${target.toFixed(1)}s（上限档只查不超，不要求凑满）`,
      ));
    }
  } else if (Math.abs(estimated - target) > tolerance) {
    findings.push(finding(
      "K14", DOC_FILES["01"], 0,
      `时长预算不通过：台词 ${dialogueSec.toFixed(0)}s + 动作 ${actionSec.toFixed(1)}s = ${estimated.toFixed(1)}s，目标 ${target.toFixed(1)}s，差 ${Math.abs(estimated - target).toFixed(1)}s > 容差 ${tolerance.toFixed(1)}s`,
    ));
  }

  const declared = {
    台词秒数: parseFloatText(kvValue(project, "台词秒数")),
    动作秒数: parseFloatText(kvValue(project, "动作秒数")),
    预计总时长: parseFloatText(kvValue(project, "预计总时长")),
  };
  const actual = { 台词秒数: dialogueSec, 动作秒数: actionSec, 预计总时长: estimated };
  for (const [key, value] of Object.entries(declared)) {
    if (value !== null && Math.abs(value - actual[key]) > 1.0) {
      findings.push(finding(
        "K14", DOC_FILES["01"], 0,
        `时长预算表「${key}」写 ${value.toFixed(1)}s，按节拍表重算 ${actual[key].toFixed(1)}s（差 >1s）`,
      ));
    }
  }

  const shotSecs = shotSeconds(project);
  for (const [sid, total] of beatSecs) {
    const cap = shotSecs.get(sid);
    if (cap !== undefined && total > cap + 2.5) {
      findings.push(finding(
        "K14", DOC_FILES["01"], 0,
        `镜${sid} 认领的节拍合计 ${total.toFixed(1)}s > 生成时长 ${cap.toFixed(1)}s + 2.5s（须拆镜或减拍）`,
      ));
    }
  }
  return findings;
}
