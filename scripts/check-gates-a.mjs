// K1-K6 门（行为对齐 check.py）。
import {
  DOC_FILES,
  blocks,
  cell,
  CHASE_RE,
  CT1_RE,
  dialogueQuotes,
  dialogueSet01,
  EMPHASIS_OTHER,
  EMPHASIS_SLOW,
  EMPHASIS_WORDS,
  extractDialogueCell,
  finding,
  FOLLOW_FAMILY,
  iterTables,
  MODEL_CAP,
  PEAK_RE,
  REVEAL_FAMILY,
  REVEAL_RE,
  SHOT_ID_RE,
  subBlocks,
  tableRows,
  VOIDED_RE,
} from "./vigen-md.mjs";
import {
  DUR_G,
  DUR_ONE,
  NEG_LINE,
  REF_SHOT_G,
  SECTION_LABELS,
  STORY_ALIASES,
  TECH_LINE,
  cpLen,
  cpSlice,
  f1,
  g,
  plotRows,
  shotIds,
  storyRows,
  warn,
} from "./check-core.mjs";

// ------------------------------------------------------------------ K1 台词
export function gateK1(project) {
  if (project.doc("01") === null) return [];
  const findings = [];
  const base = dialogueSet01(project);
  if (base.size === 0) {
    findings.push(warn("K1", "01", "01 未解析到台词（缺「分场剧本」节或说话人行格式不同），K1 无法核对"));
  }
  if (project.doc("04") !== null) {
    const quotes = dialogueQuotes(project.doc("04"));
    if (quotes.length === 0) findings.push(warn("K1", "04", "未找到任何台词引号，K1 未执行"));
    for (const [lineNo, text] of quotes) {
      const t = text.trim();
      if (t && !base.has(t)) {
        findings.push(finding(
          "K1", DOC_FILES["04"], lineNo,
          `台词与01定稿不一致：「${t}」（01 定稿中无此句——改写/修订后须从 01 逐字搬运）`,
        ));
      }
    }
  }
  if (project.doc("05") !== null) {
    const rows = tableRows(project.doc("05"), ["台词原文"]);
    if (rows === null) {
      findings.push(warn("K1", "05", "未找到含「台词原文」列的台词清单，K1 未核对 05"));
    } else {
      for (const r of rows) {
        const t = extractDialogueCell(r.cells["台词原文"]);
        if (t && !base.has(t)) {
          findings.push(finding(
            "K1", DOC_FILES["05"], r.line,
            `台词与01定稿不一致：「${t}」（05 台词总账须与 01 逐字一致）`,
          ));
        }
      }
    }
  }
  return findings;
}

// ------------------------------------------------------------------ K2 时长
function videoRow(project) {
  const rows = tableRows(project.doc("02"), ["用途", "模型"], {
    用途: ["用途"],
    模型: ["模型"],
  });
  if (!rows) return null;
  return rows.find((r) => cell(r, "用途").includes("视频")) || null;
}

function videoModel(project) {
  const r = videoRow(project);
  return r ? cell(r, "模型").trim() : null;
}

function isH3(project) {
  const low = (videoModel(project) || "").toLowerCase();
  return low.includes("h3") || low.includes("minimax");
}

function videoCap(project) {
  const r = videoRow(project);
  if (!r) return null;
  const text = Object.values(r.cells).join(" ");
  const nums = [...text.matchAll(DUR_G())].map((m) => Number(m[1]));
  if (nums.length) return Math.max(...nums);
  const low = text.toLowerCase();
  for (const [key, cap] of Object.entries(MODEL_CAP)) {
    if (low.includes(key)) return cap;
  }
  return null;
}

export function gateK2(project) {
  const findings = [];
  const cap = videoCap(project);
  const h3 = isH3(project);

  if (project.doc("04") !== null && cap !== null) {
    let checked = 0;
    for (const block of blocks(project.doc("04"), true)) {
      const headNo = block[0][0];
      const secsList = [...block[0][1].matchAll(/生成\s*(\d+(?:\.\d+)?)\s*s/g)].map((m) => Number(m[1]));
      if (!secsList.length) continue;
      checked += 1;
      for (const secs of secsList) {
        if (secs > cap) {
          findings.push(finding(
            "K2", DOC_FILES["04"], headNo,
            `生成时长 ${g(secs)}s 超模型上限 ${g(cap)}s（超限须拆条+尾帧续接——A2）`,
          ));
        }
        if (h3 && Math.abs(secs - Math.round(secs)) > 1e-9) {
          findings.push(finding(
            "K2", DOC_FILES["04"], headNo,
            `生成时长 ${g(secs)}s 不是整数秒（H3 网关 seconds 只收整数，9.5→10——A2）`,
          ));
        }
      }
    }
    if (checked === 0) {
      findings.push(warn("K2", "04", "段落标题未写「生成 Xs」，K2 未核对生成时长"));
    }
  }

  if (project.doc("01") !== null && cap !== null) {
    const rows = tableRows(project.doc("01"), ["镜号", "生成时长"], STORY_ALIASES);
    for (const r of rows || []) {
      const m = DUR_ONE(cell(r, "生成时长"));
      if (m && Number(m[1]) > cap) {
        findings.push(finding(
          "K2", DOC_FILES["01"], r.line,
          `生成时长 ${m[1]}s 超模型上限 ${g(cap)}s（超限须拆条+尾帧续接——A2）`,
        ));
      }
    }
  }

  if (project.doc("05") !== null) {
    const rows = tableRows(project.doc("05"), ["台词原文", "朗读时长", "所在镜头时长"]);
    if (rows === null) {
      findings.push(warn("K2", "05", "台词清单缺「朗读时长/所在镜头时长」列，K2 未核对台词时长"));
    } else {
      const segSum = new Map();
      for (const r of rows) {
        const txt = extractDialogueCell(r.cells["台词原文"]);
        const readM = DUR_ONE(r.cells["朗读时长"]);
        const shotM = DUR_ONE(r.cells["所在镜头时长"]);
        if (!readM || !shotM) continue;
        const read = Number(readM[1]);
        const shot = Number(shotM[1]);
        if (read > shot) {
          findings.push(finding(
            "K2", DOC_FILES["05"], r.line,
            `台词朗读超镜头时长：朗读 ${g(read)}s > 镜头 ${g(shot)}s（延长时间码或拆多镜——A3）`,
          ));
        }
        if (txt) {
          const est = Math.ceil(cpLen(txt) / 4);
          if (est > shot) {
            findings.push(finding(
              "K2", DOC_FILES["05"], r.line,
              `台词估算朗读 ${est}s（${cpLen(txt)}字÷4字/秒）> 镜头 ${g(shot)}s（A3 含标点估算）`,
            ));
          }
        }
        const segM = /段\s*(\d+)/.exec(cell(r, "镜号/段落", "镜号"));
        const key = segM ? segM[1] : "?";
        segSum.set(key, (segSum.get(key) || 0) + read);
      }
      for (const [seg, total] of segSum) {
        if (total > 14.0) {
          findings.push(finding(
            "K2", DOC_FILES["05"], 0,
            `段${seg} 台词朗读合计 ${f1(total)}s > 14s 必拆段（A3 段级预算）`,
          ));
        }
      }
    }
  }
  return findings;
}

// ------------------------------------------------------------------ K3 锚定
const HEX_G = () => /#[0-9A-Fa-f]{6}/g;

function kvLookup(block, key) {
  const texts = block.map(([, t]) => t);
  for (const [, header, body] of iterTables(texts)) {
    if (header.length < 2 && body.length === 0) continue;
    for (const [, cells] of body) {
      if (
        cells.length >= 2 &&
        cells[0].replace(/^[* ]+|[* ]+$/g, "").trim() === key
      ) {
        return cells[1].trim();
      }
    }
  }
  return null;
}

function palette(project) {
  const out = [];
  for (const [, header, body] of iterTables(project.doc("02") || [])) {
    if (!header.some((h) => h.includes("色号"))) continue;
    const roleI = 0;
    const hexI = header.findIndex((h) => h.includes("色号"));
    for (const [, cells] of body) {
      const role = cells.length ? cells[roleI] : "";
      if (!["环境", "中间调", "暗部"].some((k) => role.includes(k))) continue;
      const text = 0 <= hexI && hexI < cells.length ? cells[hexI] : "";
      for (const m of text.matchAll(HEX_G())) {
        if (!out.includes(m[0])) out.push(m[0]);
      }
    }
  }
  return out;
}

function characterAnchors(project) {
  const out = [];
  for (const block of subBlocks(project.doc("02"))) {
    const name = block[0][1].slice(4).trim();
    const phrase = kvLookup(block, "锚定短语（中文）");
    if (phrase) out.push([name, phrase]);
  }
  return out;
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function gateK3(project) {
  if (project.doc("02") === null || project.doc("04") === null) return [];
  const findings = [];
  const lines04 = project.doc("04");

  const hexes = palette(project);
  if (hexes.length) {
    let checked = 0;
    for (const block of blocks(lines04, true)) {
      const tone = block.filter(([, t]) => t.trim().startsWith("色调"));
      if (!tone.length) {
        findings.push(finding(
          "K3", DOC_FILES["04"], block[0][0],
          "段落缺「色调：」行，K3 无法核对色号（FORMAT 须写色号+落点——A1）",
        ));
        continue;
      }
      checked += 1;
      const body = tone.map(([, t]) => t).join("\n");
      for (const hx of hexes) {
        if (!body.includes(hx)) {
          findings.push(finding(
            "K3", DOC_FILES["04"], tone[0][0],
            `色彩基调色号缺失：${hx} 未逐字出现（02 色板登记项——A1）`,
          ));
        }
      }
    }
    if (checked === 0) findings.push(warn("K3", "04", "未找到段落块，K3 色号检查未执行"));
  }

  const anchors = characterAnchors(project);
  if (!anchors.length) {
    findings.push(warn("K3", "02", "未解析到「锚定短语（中文）」，K3 角色锚定未核对"));
  }
  const docText = lines04.join("\n");
  for (const [name, phrase] of anchors) {
    const refBind = new RegExp(`@\\s*REF-[A-Z0-9-]+[^\\n]*${escapeRegExp(name)}`);
    if (refBind.test(docText)) continue;
    if (!docText.includes(name) || docText.includes(phrase)) continue;
    const lineNo = lines04.findIndex((ln) => ln.includes(name)) + 1;
    findings.push(finding(
      "K3", DOC_FILES["04"], lineNo,
      `角色「${name}」锚定短语缺失：无 REF 图绑定，锚定短语须逐字出现（02 登记：${cpSlice(phrase, 24)}…——A1）`,
    ));
  }
  return findings;
}

// ------------------------------------------------------------------ K4 镜号
function shotHeaderLines(lines) {
  if (lines === null) return [];
  const out = [];
  for (let i = 0; i < lines.length; i += 1) {
    const s = lines[i].trim();
    if (/^#{1,4}\s*镜头/.test(s) || /^\d+(?:\.\d+)?\s*s?\s*[–\-—~～至]/.test(s)) {
      out.push([i + 1, s]);
    }
  }
  return out;
}

export function gateK4(project) {
  if (project.doc("01") === null) return [];
  const findings = [];
  const [live, voided] = shotIds(project);
  if (live.size === 0) findings.push(warn("K4", "01", "未解析到分镜表镜号，K4 未执行"));

  const seen = new Set();
  for (const r of storyRows(project) || []) {
    const raw = (r.cells["镜号"] || "").trim();
    if (VOIDED_RE.exec(raw)) continue;
    const m = SHOT_ID_RE.exec(raw);
    if (!m) continue;
    const sid = m[1];
    if (seen.has(sid)) {
      findings.push(finding(
        "K4", DOC_FILES["01"], r.line,
        `镜号重复：${sid} 已分配（插入用后缀式 S3a，不重排已有镜号）`,
      ));
    }
    seen.add(sid);
  }

  for (const key of ["03", "04"]) {
    for (const [lineNo, text] of shotHeaderLines(project.doc(key))) {
      for (const m of text.matchAll(REF_SHOT_G())) {
        const ref = m[1];
        if (live.has(ref)) continue;
        if (voided.has(ref)) {
          findings.push(finding(
            "K4", DOC_FILES[key], lineNo,
            `引用了已作废镜号：镜${ref}（作废镜号仅供追溯，禁止再引用）`,
          ));
        } else {
          findings.push(finding(
            "K4", DOC_FILES[key], lineNo,
            `引用了01分镜表不存在的镜号：镜${ref}`,
          ));
        }
      }
    }
  }
  return findings;
}

// ------------------------------------------------------------------ K5 强调手段
function emphasisSpots(block) {
  const out = [];
  let section = "";
  for (const [no, text] of block) {
    const s = text.trim();
    if (SECTION_LABELS.has(s)) {
      section = s;
      continue;
    }
    if (section === "FORMAT" || section === "NO") continue;
    if (!s || s.startsWith("```")) continue;
    if (TECH_LINE.test(s) || NEG_LINE.test(s)) continue;
    const hitSlow = EMPHASIS_SLOW.find((w) => s.includes(w));
    const hitOther = EMPHASIS_OTHER.find((w) => s.includes(w));
    const hit = hitSlow || hitOther;
    if (hit) out.push([no, Boolean(hitSlow), hit]);
  }
  return out;
}

function plotPeakIds(project) {
  const ids = new Set();
  for (const r of plotRows(project) || []) {
    if ((r.cells["情节点"] || "").includes("【峰】")) {
      const num = cell(r, "#").trim();
      if (/^\d+$/.test(num)) ids.add(num);
    }
  }
  return ids;
}

function combatStarRounds(project) {
  const rounds = new Set();
  for (const [, ln] of project.section("01", "打斗交手账")) {
    const m = /^\|\s*R(\d+)/.exec(ln);
    if (m && ln.includes("★")) rounds.add(m[1]);
  }
  return rounds;
}

export function gateK5(project) {
  if (project.doc("04") === null) return [];
  const findings = [];
  const peakIds = plotPeakIds(project);
  const starRounds = combatStarRounds(project);
  const segs = blocks(project.doc("04"), true);
  if (!segs.length) return [warn("K5", "04", "未找到段落块，K5 未执行")];
  let units = 0;
  for (const block of segs) {
    let slow = 0;
    for (const [lineNo, isSlow, word] of emphasisSpots(block)) {
      units += 1;
      if (isSlow) slow += 1;
      const line = block.find(([n]) => n === lineNo)[1];
      const pm = PEAK_RE.exec(line);
      if (!pm) {
        findings.push(finding(
          "K5", DOC_FILES["04"], lineNo,
          `强调手段无峰值标注：「${word}」须标注 ←峰值：情节点N/交手账RN`,
        ));
        continue;
      }
      const src = pm[1];
      if (src.startsWith("交手账R")) {
        const r = src.slice("交手账R".length);
        if (!starRounds.has(r)) {
          findings.push(finding(
            "K5", DOC_FILES["04"], lineNo,
            `峰值来源无法解析：${src}（01 交手账该回合不存在或未标 ★ 胜负手）`,
          ));
        }
      } else {
        const n = src.slice("情节点".length);
        if (!peakIds.has(n)) {
          findings.push(finding(
            "K5", DOC_FILES["04"], lineNo,
            `峰值来源无法解析：${src}（01 情节点清单该编号不存在或未标【峰】）`,
          ));
        }
      }
    }
    if (slow > 2) {
      findings.push(finding(
        "K5", DOC_FILES["04"], block[0][0],
        `慢镜超配额：本段 ${slow} 处慢镜 > 2（配额是上限不是任务）`,
      ));
    }
  }
  if (units === 0) {
    findings.push(warn("K5", "04", "全片未出现强调手段，K5 未核对（如是纯文戏可忽略）"));
  }
  return findings;
}

// ------------------------------------------------------------------ K6 运镜条件
export function gateK6(project) {
  if (project.doc("01") === null) return [];
  const findings = [];
  const plot = plotRows(project) || [];
  const story = storyRows(project) || [];
  if (!story.length) return [warn("K6", "01", "未解析到分镜表，K6 未执行")];

  const plotText = plot.map((r) => r.cells["情节点"] || "").join("\n");
  const camText = story.map((r) => r.cells["运镜"] || "").join("\n");

  if (plot.length && CHASE_RE.test(plotText) && !FOLLOW_FAMILY.test(camText)) {
    const hit = plot.find((r) => CHASE_RE.test(r.cells["情节点"] || ""));
    findings.push(finding(
      "K6", DOC_FILES["01"], hit ? hit.line : 0,
      `剧情含奔跑/追逐/逃（${hit ? cpSlice(hit.cells["情节点"] || "", 24) : ""}）但分镜运镜列无跟拍族（跟拍/横移/跟随 ≥1 且指认镜号——A12）`,
    ));
  }
  if (plot.length && REVEAL_RE.test(plotText) && !REVEAL_FAMILY.test(camText)) {
    const hit = plot.find((r) => REVEAL_RE.test(r.cells["情节点"] || ""));
    findings.push(finding(
      "K6", DOC_FILES["01"], hit ? hit.line : 0,
      `剧情含信息揭示（${hit ? cpSlice(hit.cells["情节点"] || "", 24) : ""}）但分镜运镜列无摇/后拉/俯仰族（揭示须停在新信息上——A12）`,
    ));
  }
  if (plotText.includes("【峰】") && project.doc("04") !== null) {
    const doc04 = project.doc("04").join("\n");
    if (!EMPHASIS_WORDS.some((w) => doc04.includes(w))) {
      findings.push(finding(
        "K6", DOC_FILES["01"], 0,
        "情节点含【峰】但 04 无任何强调手段（峰值须配手段）",
      ));
    }
  }

  for (const r of story) {
    const cam = cell(r, "运镜").trim();
    const motive = cell(r, "运镜动机", "动机").trim();
    if (motive && !CT1_RE.test(motive)) {
      findings.push(finding(
        "K6", DOC_FILES["01"], r.line,
        `运镜动机列不合CT1（需 五类词(R行号)：一句展开，如 pressure(R3)：台词正压到她身上）：${cpSlice(motive, 30)}`,
      ));
    }
    if (cam.includes("固定") && !motive.includes("(R7)")) {
      findings.push(finding(
        "K6", DOC_FILES["01"], r.line,
        `运镜列写固定，但动机列未报 (R7)（固定=决策表最后一行，必须带 R7+理由）：${cpSlice(motive, 30) || "空"}`,
      ));
    }
  }
  return findings;
}

