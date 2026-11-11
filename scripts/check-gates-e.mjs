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


// A17 执行契约留痕（opt-in）：批次生产卡 + 批次校验记录 + 04 段锁定清单九项。
function headerIndex(header, ...names) {
  for (const name of names) {
    const i = header.findIndex((h) => h.includes(name));
    if (i >= 0) return i;
  }
  return -1;
}

export function gateA17(project, partial) {
  const findings = [];
  const doc = project.doc("01");
  if (doc === null) {
    findings.push(finding("A17", DOC_FILES["01"], 0, "警告：01 缺失，A17 未执行"));
    return findings;
  }
  let auditHead = null;
  let cardHead = null;
  for (const [headNo, header, body] of iterTables(doc)) {
    const gi = headerIndex(header, "门");
    const ri = headerIndex(header, "结果");
    const ei = headerIndex(header, "证据");
    if (gi >= 0 && ri >= 0 && ei >= 0) {
      auditHead = headNo;
      const seen = new Set();
      for (const [no, cells] of body) {
        const m = ((cells[gi] || "").match(/A\s*(\d+)/));
        if (!m) continue;
        const n = Number.parseInt(m[1], 10);
        if (n < 1 || n > 16) continue;
        seen.add(n);
        const res = (cells[ri] || "").trim();
        const ev = (cells[ei] || "").trim();
        if (res.includes("{") || res.includes("}")) {
          findings.push(finding("A17", DOC_FILES["01"], no, `A${n} 结果仍是模板占位（填 PASS/OPEN/NA）`));
        } else if (!["PASS", "OPEN", "NA"].includes(res.toUpperCase())) {
          findings.push(finding("A17", DOC_FILES["01"], no, `A${n} 结果须为 PASS/OPEN/NA（当前：${res}）`));
        }
        if (!ev || ["—", "-", "–"].includes(ev)) {
          findings.push(finding("A17", DOC_FILES["01"], no, `A${n} 证据为空（写文件:行/镜号）`));
        } else if (ev.includes("{") || ev.includes("}")) {
          findings.push(finding("A17", DOC_FILES["01"], no, `A${n} 证据仍是模板占位（填文件:行/镜号）`));
        }
      }
      const missing = [];
      for (let n = 1; n <= 16; n += 1) if (!seen.has(n)) missing.push(n);
      if (missing.length) {
        const msg = missing.length === 1
          ? `批次校验记录缺 A${missing[0]}（A1-A16 必须逐项留痕）`
          : `批次校验记录缺 ${missing.length} 项（首个 A${missing[0]}；A1-A16 必须逐项留痕）`;
        findings.push(finding("A17", DOC_FILES["01"], auditHead, msg));
      }
    }
    const ci = headerIndex(header, "段号");
    const si = headerIndex(header, "镜号");
    const di = headerIndex(header, "生成时长");
    if (ci >= 0 && si >= 0 && di >= 0) {
      cardHead = headNo;
      if (!body.length) {
        findings.push(finding("A17", DOC_FILES["01"], headNo, "批次生产卡没有数据行（每段一行）"));
      } else if (body.some(([, cells]) => cells.some((c) => c.includes("{") || c.includes("}")))) {
        findings.push(finding("A17", DOC_FILES["01"], headNo, "批次生产卡仍是模板占位（从 02/01/05 复制填写）"));
      }
    }
  }
  if (auditHead === null) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到批次校验记录（表头含 门/结果/证据），A17 未执行"));
  if (cardHead === null) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到批次生产卡（表头含 段号/镜号/生成时长），A17 未执行"));

  const lockKeys = ["身份锁", "表情锁", "表演锁", "说话人锁", "道具锁", "空间锁", "风格锁", "声音锁", "动作锁"];
  if (project.doc("04") !== null) {
    const segs = blocks(project.doc("04"), true);
    if (!segs.length) findings.push(finding("A17", DOC_FILES["04"], 0, "警告：未找到段落块，A17 锁定清单未核对"));
    for (const block of segs) {
      const headNo = block[0][0];
      const text = block.map(([, t]) => t).join("\n");
      if (!text.includes("本段锁定清单")) {
        findings.push(finding("A17", DOC_FILES["04"], headNo, "段落缺「本段锁定清单」（硬规则 19：九项锁定缺一不可）"));
        continue;
      }
      const missing = lockKeys.filter((k) => !text.includes(k));
      if (missing.length) {
        findings.push(finding("A17", DOC_FILES["04"], headNo, `锁定清单缺 ${missing.join("、")}（九项缺一不可——硬规则 19）`));
      }
    }
  }
  return findings;
}
