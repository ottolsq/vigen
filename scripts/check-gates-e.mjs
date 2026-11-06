// A16 先锁后写（opt-in 审计）——只做机械可判定的子集。
import {
  DOC_FILES,
  blocks,
  cell,
  finding,
  iterTables,
  tableRows,
} from "./vigen-md.mjs";
import { STORY_ALIASES } from "./check-core.mjs";

function styleBible(project) {
  const parts = [];
  for (const [, ln] of project.section("02", "风格圣经")) {
    const s = ln.trim();
    if (!s || s.startsWith(">") || s.startsWith("|") || s.startsWith("#")) continue;
    parts.push(s);
  }
  const text = parts.join(" ").trim();
  return text.includes("{") || text.includes("}") ? "" : text;
}

function normWs(text) {
  return (text || "").replace(/\s+/g, " ").trim();
}

function isPlaceholder(value) {
  const v = (value || "").trim();
  return /[{}]/.test(v) || ["—", "-", "–"].includes(v);
}

function scenePersistent(project) {
  for (const [, , body] of iterTables(project.doc("02") || [])) {
    for (const [, cells] of body) {
      if (cells.length >= 2 && cells[0].includes("持续在场要素")) {
        const value = cells[1].trim();
        if (value && !isPlaceholder(value)) return value;
      }
    }
  }
  return "";
}

export function gateA16(project) {
  const findings = [];
  const bible = styleBible(project);
  if (bible && project.doc("04") !== null) {
    const target = normWs(bible);
    for (const block of blocks(project.doc("04"), true)) {
      const body = normWs(block.map(([, t]) => t).join("\n"));
      if (!body.includes(target)) {
        findings.push(finding(
          "A16", DOC_FILES["04"], block[0][0],
          `段落缺风格圣经逐字句（A16 风格三件套——02 已登记：${Array.from(bible).slice(0, 30).join("")}…）`,
        ));
      }
    }
  }

  if (project.doc("01") !== null) {
    const rows = tableRows(project.doc("01"), ["镜号"], STORY_ALIASES);
    if (rows && rows.length && Object.keys(rows[0].cells).some((k) => k.includes("入画道具"))) {
      const doc03 = (project.doc("03") || []).join("\n");
      const doc02 = (project.doc("02") || []).join("\n");
      for (const r of rows) {
        const raw = cell(r, "入画道具").trim();
        if (!raw || ["—", "-", "–"].includes(raw)) continue;
        const ids = [...raw.matchAll(/REF-[A-Z0-9-]+/g)].map((m) => m[0]);
        if (!ids.length) {
          findings.push(finding(
            "A16", DOC_FILES["01"], r.line,
            `入画道具列有内容但未写 REF-id（A16 入画即登记）：${Array.from(raw).slice(0, 20).join("")}`,
          ));
          continue;
        }
        for (const rid of ids) {
          if (!doc03.includes(rid) && !doc02.includes(rid)) {
            findings.push(finding(
              "A16", DOC_FILES["01"], r.line,
              `入画道具 ${rid} 未在 03 资产矩阵登记（A16 入画即登记）`,
            ));
          }
        }
      }
    }
  }

  const persistent = scenePersistent(project);
  if (persistent && project.doc("04") !== null) {
    const doc04 = (project.doc("04") || []).join("\n");
    if (!doc04.includes("始终在场") && !doc04.includes("全程不出现")) {
      findings.push(finding(
        "A16", DOC_FILES["04"], 0,
        "02 已登记持续在场要素，但 04 未复述「始终在场/全程不出现」（A16）",
      ));
    }
  }
  return findings;
}
