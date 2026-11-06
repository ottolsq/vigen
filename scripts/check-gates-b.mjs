// K7-K12 门（行为对齐 check.py）。
import {
  DOC_FILES,
  blockText,
  blocks,
  cell,
  characterNames,
  ENV_MOTION_WORDS,
  finding,
  modelNativeMin,
  shotBlocks,
  SKELETON_A_SECTIONS,
  tableRows,
  timeRangeSeconds,
} from "./vigen-md.mjs";
import {
  DUR_ONE,
  HUMAN_ACTION,
  REF_SHOT_G,
  STORY_ALIASES,
  cpSlice,
  f1,
  g,
  plotRows,
  shotIds,
  warn,
} from "./check-core.mjs";

const PLANREF_G = () => /(PLAN|REF)-([A-Z0-9]+(?:-[A-Z0-9]+)*)/g;
const QUOTE_G = () => /"([^"]+)"|“([^”]+)”|「([^」]+)」/g;
const PRONOUN_G = () => /(?<!其)(对方|那个人|两人|二人|双方|他|她|它)(?!人)/g;
const BODY_G = () => /(左手|右手|左臂|右臂|左肩|右肩|左腿|右腿|左脚|右脚|左腰侧|右腰侧|左脸颊|右脸颊)(?!边)/g;
const VAGUE_G = () => /(打在|踢在|砍在|刺在|击中|砸在|撞在|落在)[^。；\n]{0,8}(身上|某处|要害)/g;

// ------------------------------------------------------------------ K7 环境动态
export function gateK7(project) {
  if (project.doc("04") === null) return [];
  const blocks_ = shotBlocks(project.doc("04"));
  if (!blocks_.length) return [warn("K7", "04", "未找到任何镜头块，K7 未执行")];
  const findings = [];
  for (const block of blocks_) {
    const text = blockText(block);
    const m = /镜头\s*(S?\d+[a-z]?)/.exec(block[0][1]);
    const sid = m ? m[1] : "?";
    if (!ENV_MOTION_WORDS.some((w) => text.includes(w))) {
      findings.push(finding(
        "K7", DOC_FILES["04"], block[0][0],
        `镜头${sid} 无环境动态层元素（每镜 ≥1：风吹/衣摆/涟漪/雾/尘埃/微振——固定≠静止）`,
      ));
    }
    if (
      text.includes("固定") &&
      !["微振", "风吹", "风在吹", "机体振动"].some((w) => text.includes(w))
    ) {
      findings.push(finding(
        "K7", DOC_FILES["04"], block[0][0],
        `镜头${sid} 写固定机位但未注明微振来源（机体振动/风吹——B13）`,
      ));
    }
  }
  return findings;
}

// ------------------------------------------------------------------ K8 骨架槽位
function codeBlocks(lines) {
  const out = [];
  let cur = null;
  let start = 0;
  for (let i = 0; i < lines.length; i += 1) {
    const ln = lines[i];
    if (ln.trim() === "```") {
      if (cur === null) {
        cur = [];
        start = i + 1;
      } else {
        out.push([start, cur]);
        cur = null;
      }
      continue;
    }
    if (cur !== null) cur.push(ln);
  }
  return out;
}

export function gateK8(project) {
  const lines = project.doc("04");
  if (lines === null) return [];
  const findings = [];
  let seenA = 0;
  for (const [start, block] of codeBlocks(lines)) {
    const texts = block.map((t) => t.trim());
    if (!texts.includes("SCENE CONTEXT")) continue;
    seenA += 1;
    for (const sec of SKELETON_A_SECTIONS) {
      if (!texts.includes(sec)) {
        findings.push(finding(
          "K8", DOC_FILES["04"], start,
          `骨架A缺节：${sec}（须单独成行——prompt-rules 骨架槽位清单）`,
        ));
      }
    }
  }
  if (seenA === 0) findings.push(warn("K8", "04", "未找到骨架 A code block，K8 未执行"));

  if (/^##\s*镜头\s*S?\d/m.test(lines.join("\n"))) {
    const doc01 = (project.doc("01") || []).join("\n");
    const note = project.section("01", "分镜总览表").map(([, t]) => t).join("\n");
    const ok =
      /骨架\s*B[^\n]{0,40}(理由|：|—|-)/.test(note) ||
      /骨架\s*B[^\n]{0,40}(理由|：|—|-)/.test(doc01);
    const negated = /(不使用|不用|非|不需要)\s*骨架\s*B/.test(doc01);
    if (!ok || negated) {
      findings.push(finding(
        "K8", DOC_FILES["04"], 0,
        "04 含骨架 B 单镜块但 01 未正面标注骨架 B 理由（fl2va/一镜到底张力——特例须写明）",
      ));
    }
  }
  return findings;
}

// ------------------------------------------------------------------ K9 情节点覆盖
export function gateK9(project) {
  if (project.doc("01") === null) return [];
  const rows = plotRows(project);
  if (!rows || !rows.length) return [warn("K9", "01", "未解析到情节点清单，K9 未执行")];
  const findings = [];
  const [live] = shotIds(project);
  const hasStatus = Object.hasOwn(rows[0].cells, "状态");
  if (!hasStatus) {
    findings.push(finding(
      "K9", DOC_FILES["01"], rows[0].line,
      "情节点清单缺「状态」列——K9 无法核对覆盖状态",
    ));
  }
  for (const r of rows) {
    const label = cpSlice(cell(r, "情节点"), 20);
    const cov = cell(r, "覆盖镜号", "覆盖").trim();
    const status = cell(r, "状态");
    if (!cov) {
      findings.push(finding(
        "K9", DOC_FILES["01"], r.line,
        `情节点${label}未覆盖：覆盖镜号列为空（分镜必须 100% 覆盖情节点——硬规则7）`,
      ));
      continue;
    }
    if (hasStatus && !status.includes("✓")) {
      findings.push(finding(
        "K9", DOC_FILES["01"], r.line,
        `情节点${label}状态未勾：状态列须 ✓`,
      ));
    }
    for (const m of cov.matchAll(REF_SHOT_G())) {
      if (!live.has(m[1])) {
        findings.push(finding(
          "K9", DOC_FILES["01"], r.line,
          `情节点${label}覆盖镜号镜${m[1]}在01分镜表不存在`,
        ));
      }
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

