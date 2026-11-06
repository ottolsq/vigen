#!/usr/bin/env node
// vigen check.mjs — Phase 1 机械校验（行为对齐 scripts/check.py 的 K1/K2/K5/K6/K10/K11/K12）。
// 纪律：只 enforce 文档已写的门；与 check.py 同输出、同退出码。
// Phase 1 未移植 K3/K4/K7/K8/K9/K13-K16：默认运行会明确报错，不静默宣称“全部通过”。
import { existsSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  DOC_FILES,
  Project,
  blocks,
  cell,
  characterNames,
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
  MODEL_CAP,
  modelNativeMin,
  PEAK_RE,
  REVEAL_FAMILY,
  REVEAL_RE,
  SKELETON_A_SECTIONS,
  tableRows,
  timeRangeSeconds,
} from "./vigen-md.mjs";

const STORY_ALIASES = {
  镜号: ["镜号", "镜头"],
  运镜: ["运镜"],
  运镜动机: ["运镜动机", "动机"],
  生成时长: ["生成时长"],
};

const ALL_GATES = [
  "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8",
  "K9", "K10", "K11", "K12", "K13", "K14", "K15", "K16",
];
const PHASE1 = new Set(["K1", "K2", "K5", "K6", "K10", "K11", "K12"]);

const DUR_ONE = (s) => /(\d+(?:\.\d+)?)\s*s/.exec(s);
const DUR_G = () => /(\d+(?:\.\d+)?)\s*s/g;
const PLANREF_G = () => /(PLAN|REF)-([A-Z0-9]+(?:-[A-Z0-9]+)*)/g;
const QUOTE_G = () => /"([^"]+)"|“([^”]+)”|「([^」]+)」/g;
const PRONOUN_G = () => /(?<!其)(对方|那个人|两人|二人|双方|他|她|它)(?!人)/g;
const BODY_G = () => /(左手|右手|左臂|右臂|左肩|右肩|左腿|右腿|左脚|右脚|左腰侧|右腰侧|左脸颊|右脸颊)(?!边)/g;
const VAGUE_G = () => /(打在|踢在|砍在|刺在|击中|砸在|撞在|落在)[^。；\n]{0,8}(身上|某处|要害)/g;
const TECH_LINE = /fps|快门|帧率|镜头运动|运镜库/;
const NEG_LINE = /^\s*[*\-—·]?\s*(禁止|不要|不得|避免|无|没有|不)/;
const SECTION_LABELS = new Set(SKELETON_A_SECTIONS);
const HUMAN_ACTION = new Set("说看走站坐抬转拿握伸退冲停笑低靠盯望递接推拉蹲跪扑抓挥砍刺劈跳跑");

function warn(gate, key, msg) {
  return finding(gate, DOC_FILES[key], 0, "警告：" + msg);
}

function cpLen(s) {
  return Array.from(s).length;
}

function cpSlice(s, n) {
  return Array.from(s).slice(0, n).join("");
}

function g(x) {
  return String(Number(x));
}

function f1(x) {
  return Number(x).toFixed(1);
}

function plotRows(project) {
  return tableRows(project.doc("01"), ["情节点", "覆盖镜号"], {
    覆盖镜号: ["覆盖镜号", "覆盖"],
  });
}

function storyRows(project) {
  const rows = tableRows(project.doc("01"), ["镜号", "运镜"], STORY_ALIASES);
  if (rows !== null) return rows;
  return tableRows(project.doc("01"), ["镜号"], STORY_ALIASES);
}

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

// ------------------------------------------------------------------ K10 PLAN/REF
export function gateK10(project) {
  const lines = project.doc("04");
  if (lines === null) return [];
  const findings = [];
  const doc03 = project.doc("03");
  const refIds = new Set([...(doc03 || []).join("\n").matchAll(PLANREF_G())].map((m) => m[0]));
  for (let i = 0; i < lines.length; i += 1) {
    const ln = lines[i];
    if (ln.includes("待补参考图")) {
      findings.push(finding(
        "K10", DOC_FILES["04"], i + 1,
        "模糊占位「待补参考图」：缺图须写 PLAN-<ID> 占位（CT5）",
      ));
    }
    for (const m of ln.matchAll(PLANREF_G())) {
      const kind = m[1];
      const oid = m[2];
      if (kind === "REF" && doc03 !== null && !refIds.has(m[0])) {
        findings.push(finding(
          "K10", DOC_FILES["04"], i + 1,
          `REF-${oid} 在03中无法解析（03 资产引用矩阵须登记同一 REF-id）`,
        ));
      }
    }
  }
  return findings;
}

// ------------------------------------------------------------------ K11 算术冲突
export function gateK11(project) {
  const findings = [];
  const lines = project.doc("04");
  if (lines === null) return [];
  const segs = blocks(lines, true);
  if (!segs.length) return [warn("K11", "04", "未找到段落块，K11 未执行")];

  for (const block of segs) {
    const headNo = block[0][0];
    const secsList = [...block[0][1].matchAll(/生成\s*(\d+(?:\.\d+)?)\s*s/g)].map((m) => Number(m[1]));
    const secs = secsList.length ? secsList.reduce((a, b) => a + b, 0) : null;
    if (secs === null) continue;
    let total = 0;
    let found = 0;
    for (const [, text] of block) {
      const rng = timeRangeSeconds(text);
      if (rng) {
        total += rng[1] - rng[0];
        found += 1;
      }
    }
    if (found && Math.abs(total - secs) > 1.0) {
      findings.push(finding(
        "K11", DOC_FILES["04"], headNo,
        `段内镜头时长合计 ${f1(total)}s 与标题「生成 ${g(secs)}s」不符（容差 1s——改时长须同步标题与 01 分镜表）`,
      ));
    }
  }

  const minv = modelNativeMin(project);
  const rows = tableRows(project.doc("01"), ["镜号", "生成时长"], STORY_ALIASES);
  if (minv && rows) {
    const durs = [];
    for (const r of rows) {
      const m = DUR_ONE(cell(r, "生成时长"));
      if (m) durs.push(Number(m[1]));
    }
    if (durs.length && durs.reduce((a, b) => a + b, 0) / durs.length < minv) {
      const avg = durs.reduce((a, b) => a + b, 0) / durs.length;
      findings.push(finding(
        "K11", DOC_FILES["01"], 0,
        `平均生成时长 ${f1(avg)}s 低于模型原生下限 ${g(minv)}s：多数镜头须由多镜容器（骨架 A）承载，否则模型会把每镜自行拉长到下限`,
      ));
    }
  }
  return findings;
}

// ------------------------------------------------------------------ K12 指代与部位
function promptLines(project, key) {
  const lines = project.doc(key);
  if (lines === null) return [];
  const out = [];
  let inBlock = false;
  for (let i = 0; i < lines.length; i += 1) {
    const ln = lines[i];
    if (ln.trim() === "```") {
      inBlock = !inBlock;
      continue;
    }
    if (!inBlock) continue;
    const s = ln.trim();
    if (!s || SKELETON_A_SECTIONS.includes(s)) continue;
    out.push([i + 1, ln]);
  }
  return out;
}

export function gateK12(project) {
  const findings = [];
  const names = characterNames(project);
  let totalUnits = 0;
  for (const key of ["03", "04"]) {
    if (project.doc(key) === null) continue;
    let units = 0;
    for (const [lineNo, ln] of promptLines(project, key)) {
      units += 1;
      const text = ln.replace(QUOTE_G(), "");
      const lineNames = [...names].filter((n) => text.includes(n)).sort();
      for (const m of text.matchAll(PRONOUN_G())) {
        const tok = m[1];
        if (tok === "它") {
          const nxt = text[m.index + m[0].length];
          if (!(nxt && HUMAN_ACTION.has(nxt))) continue;
        }
        findings.push(finding(
          "K12", DOC_FILES[key], lineNo,
          `人物指代用了「${tok}」——改为角色名（本行角色：${lineNames.join("/") || "见 02 锚定表"}；台词引号内不受限）`,
        ));
      }
      for (const m of text.matchAll(VAGUE_G())) {
        findings.push(finding(
          "K12", DOC_FILES[key], lineNo,
          `命中位置模糊「${m[1]}${m[2]}」——写具体部位（<角色名>的<左/右><部位>，如「林枫的右侧肋下」）`,
        ));
      }
      for (const m of text.matchAll(BODY_G())) {
        const part = m[1];
        const back = text.slice(Math.max(0, m.index - 14), m.index);
        let owned = [...names].some((n) => back.endsWith(n) || back.endsWith(n + "的"));
        if (!owned && back.includes("自己的")) owned = lineNames.length <= 1;
        if (!owned) {
          findings.push(finding(
            "K12", DOC_FILES[key], lineNo,
            `部位「${part}」未带主人与左右归属——写「<角色名>的${part}」并写明位置/朝向/持握`,
          ));
        }
      }
    }
    totalUnits += units;
  }
  if (totalUnits === 0 && (project.doc("03") !== null || project.doc("04") !== null)) {
    findings.push(warn("K12", "04", "未找到可检查的提示词正文（03/04 无 code block），K12 未执行"));
  }
  return findings;
}

const GATES = [
  ["K1", gateK1], ["K2", gateK2], ["K5", gateK5], ["K6", gateK6],
  ["K10", gateK10], ["K11", gateK11], ["K12", gateK12],
];

function usage() {
  return [
    "usage: check.mjs [-h] [--partial] [--gate GATE] project_dir",
    "",
    "vigen 项目文件机械校验（Phase 1：K1/K2/K5/K6/K10/K11/K12）",
    "",
    "positional arguments:",
    "  project_dir   项目目录（含 01-06 Markdown）",
    "",
    "options:",
    "  -h, --help    show this help message and exit",
    "  --partial     只核对已有文档；缺文档的门静默跳过",
    "  --gate GATE   只跑指定门，可用逗号分隔，如 K1,K5",
  ].join("\n");
}

function parseArgs(argv) {
  const out = { projectDir: null, partial: false, gate: null, help: false, error: null };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "-h" || a === "--help") {
      out.help = true;
    } else if (a === "--partial") {
      out.partial = true;
    } else if (a === "--gate") {
      if (i + 1 >= argv.length) {
        out.error = "argument --gate: expected one argument";
        break;
      }
      out.gate = argv[i + 1];
      i += 1;
    } else if (a.startsWith("--gate=")) {
      out.gate = a.slice("--gate=".length);
    } else if (a.startsWith("-")) {
      out.error = `unrecognized arguments: ${a}`;
      break;
    } else if (out.projectDir === null) {
      out.projectDir = a;
    } else {
      out.error = `unrecognized arguments: ${a}`;
      break;
    }
  }
  return out;
}

export function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  if (args.help) {
    console.log(usage());
    return 0;
  }
  if (args.error || !args.projectDir) {
    if (args.error) console.error(usage() + "\n\ncheck.mjs: error: " + args.error);
    else console.error(usage() + "\n\ncheck.mjs: error: the following arguments are required: project_dir");
    return 2;
  }

  const root = path.resolve(args.projectDir);
  if (!existsSync(root) || !statSync(root).isDirectory()) {
    console.log(`项目目录不存在：${args.projectDir}`);
    return 2;
  }
  const project = new Project(root);
  if (project.doc("01") === null && project.doc("04") === null) {
    console.log("项目目录内无 01/04 文件——未按 vigen 01-06 契约组织，跳过");
    return 2;
  }

  let selected = null;
  if (args.gate) {
    const wanted = new Set(
      args.gate.split(",").map((s) => s.trim().toUpperCase()).filter(Boolean),
    );
    const bad = [...wanted].filter((gid) => !ALL_GATES.includes(gid)).sort();
    if (bad.length) {
      console.log(`未知门：${bad.join(", ")}（合法取值：${ALL_GATES.join(", ")}）`);
      return 2;
    }
    const missing = [...wanted].filter((gid) => !PHASE1.has(gid)).sort();
    if (missing.length) {
      console.log(`check.mjs Phase 1 未移植门：${missing.join(", ")}（请用 check.py 跑全量）`);
      return 2;
    }
    selected = wanted;
  } else {
    const missing = ALL_GATES.filter((gid) => !PHASE1.has(gid));
    console.log(`check.mjs Phase 1 未覆盖 ${missing.join(", ")}——请用 --gate 指定已移植门，或运行 check.py 全量`);
    return 2;
  }

  const findings = [];
  let rcExtra = 0;
  if (!args.partial) {
    for (const key of ["01", "02", "03", "04", "05"]) {
      if (project.doc(key) === null) {
        findings.push(finding(
          "PRE", DOC_FILES[key], 0,
          `全量校验缺文件 ${DOC_FILES[key]}（只跑部分文档请用 --partial）`,
        ));
      }
    }
  }
  for (const [gateId, gateFn] of GATES) {
    if (!selected.has(gateId)) continue;
    try {
      findings.push(...gateFn(project, args.partial));
    } catch (exc) {
      findings.push(finding(gateId, "-", 0, `内部错误：${exc.name}: ${exc.message}`));
      rcExtra = 2;
    }
  }

  for (const f of findings) {
    const loc = f.line ? `${f.file}:${f.line}` : f.file;
    console.log(`[${f.gate}] ${loc}: ${f.message}`);
  }
  if (findings.length) {
    console.log(`check: ${findings.length} 项未通过（不过不进下一阶段——SKILL.md 硬规则 15）`);
    return rcExtra || 1;
  }
  console.log("check: 全部通过");
  return 0;
}

const isEntry = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isEntry) {
  process.exitCode = main();
}
