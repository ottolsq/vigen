// A16 先锁后写（opt-in 审计）——只做机械可判定的子集。
import {
  DOC_FILES,
  blocks,
  cell,
  finding,
  iterTables,
  shotBlocks,
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

function promptLines(lines) {
  if (lines === null) return [];
  if (lines.join("\n").includes("```")) {
    const out = [];
    let inside = false;
    lines.forEach((ln, i) => {
      if (ln.trim().startsWith("```")) {
        inside = !inside;
        return;
      }
      if (inside) out.push([i + 1, ln]);
    });
    if (out.length) return out;
  }
  return lines.map((ln, i) => [i + 1, ln]).filter(([, ln]) => !/^\s*[>#|]/.test(ln));
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function namesWithRefs(project, sectionName) {
  const lines = project.doc("02");
  if (lines === null) return new Set();
  const blocksArr = [];
  let inSection = false;
  let cur = null;
  for (let i = 0; i < lines.length; i += 1) {
    const ln = lines[i];
    if (ln.startsWith("## ")) {
      inSection = ln.slice(3).trim().startsWith(sectionName);
      cur = null;
      continue;
    }
    if (!inSection) continue;
    if (ln.startsWith("### ")) {
      cur = [[i + 1, ln]];
      blocksArr.push(cur);
    } else if (cur) {
      cur.push([i + 1, ln]);
    }
  }
  const names = new Set();
  for (const block of blocksArr) {
    const name = block[0][1].slice(4).trim().split(/[（(]/)[0].trim();
    if (!name) continue;
    for (const [, t] of block) {
      if (!t.includes("参考图路径")) continue;
      const cells = t.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
      const value = cells[1] || "";
      if (value && !isPlaceholder(value)) names.add(name);
      break;
    }
  }
  return names;
}

function hasInlineRef(text, name) {
  const re = new RegExp(`${escapeRegExp(name)}\\s*@\\s*\\{?\\{?\\s*(?:Ref|REF|图)`);
  return re.test(text);
}

function shotContent(shot) {
  const out = [];
  for (const [, t] of shot) {
    const s = t.trim();
    if (["ENDING FRAME", "PERFORMANCE LOCK", "FACE LOCK", "AUDIO", "LIGHTING", "NO"].includes(s.toUpperCase())) break;
    if (s.startsWith("表演：") || s.startsWith("表演注") || s.startsWith("自检")) continue;
    out.push(t);
  }
  return out.join("\n");
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
  let stateHead = null;
  for (const [headNo, header, body] of iterTables(doc)) {
    const gi = headerIndex(header, "门");
    const ri = headerIndex(header, "结果");
    const ei = headerIndex(header, "证据");
    if (gi >= 0 && ri >= 0 && ei >= 0) {
      auditHead = headNo;
      const seen = new Set();
      let hasCheckRow = false;
      for (const [no, cells] of body) {
        const gateText = (cells[gi] || "").trim();
        if (gateText.includes("K17") || gateText.toLowerCase().includes("check")) {
          hasCheckRow = true;
        }
        const m = (gateText.match(/A\s*(\d+)/));
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
      if (!hasCheckRow) {
        findings.push(finding(
          "A17", DOC_FILES["01"], auditHead,
          "批次校验记录缺 K17/check 结果行（该批是否跑过 check.py）",
        ));
      }
    }

    const ci = headerIndex(header, "段号");
    const si = headerIndex(header, "镜号");
    const di = headerIndex(header, "生成时长");
    if (ci >= 0 && si >= 0 && di >= 0) {
      cardHead = headNo;
      if (!body.length) {
        findings.push(finding("A17", DOC_FILES["01"], headNo, "批次生产卡没有数据行（每段一行）"));
      } else {
        const required = [
          ["台词朗读(s)", ["台词朗读", "朗读"]],
          ["动作(s)", ["动作"]],
          ["镜头(s)", ["镜头时长", "镜头"]],
          ["帽", ["帽"]],
          ["须", ["须"]],
          ["道具", ["道具"]],
        ];
        const colIdx = new Map();
        for (const [name, aliases] of required) {
          const idx = headerIndex(header, ...aliases);
          colIdx.set(name, idx);
          if (idx < 0) {
            findings.push(finding("A17", DOC_FILES["01"], headNo, `批次生产卡缺列「${name}」（V3.17 段卡必填）`));
          }
        }
        const optionalMissing = [];
        for (const [name, aliases] of [["单镜理由", ["单镜理由"]], ["峰值归属", ["峰值"]]]) {
          if (headerIndex(header, ...aliases) < 0) optionalMissing.push(name);
        }
        if (optionalMissing.length) {
          findings.push(finding("A17", DOC_FILES["01"], headNo, `批次生产卡缺列 ${optionalMissing.join("、")}（建议补：单镜理由/峰值归属）`));
        }
        for (const [no, cells] of body) {
          if (cells.some((c) => c.includes("{") || c.includes("}"))) {
            findings.push(finding("A17", DOC_FILES["01"], no, "批次生产卡仍是模板占位（从 02/01/05 复制填写）"));
            break;
          }
          for (const name of ["帽", "须", "道具"]) {
            const idx = colIdx.get(name);
            if (idx >= 0) {
              const value = (cells[idx] || "").trim();
              if (isPlaceholder(value)) {
                findings.push(finding("A17", DOC_FILES["01"], no, `段卡「${name}」为空或占位（状态三问必填）`));
              }
            }
          }
          const r = colIdx.get("台词朗读(s)");
          const a = colIdx.get("动作(s)");
          const sh = colIdx.get("镜头(s)");
          if (r >= 0 && a >= 0 && sh >= 0) {
            const raw = [cells[r], cells[a], cells[sh]].map((v) => (v || "").trim());
            const nums = raw.map((v) => {
              const m = /(\d+(?:\.\d+)?)/.exec(v);
              return m ? Number.parseFloat(m[1]) : null;
            });
            if (nums.some((v) => v === null)) {
              findings.push(finding("A17", DOC_FILES["01"], no, `时间账不是数字（台词朗读/动作/镜头：${raw.join(" / ")}）`));
            } else if (nums[0] + nums[1] > nums[2] + 0.5) {
              findings.push(finding("A17", DOC_FILES["01"], no, `时间账不通过：台词 ${nums[0].toFixed(1)}s + 动作 ${nums[1].toFixed(1)}s > 镜头 ${nums[2].toFixed(1)}s`));
            }
          }
        }
      }
    }

    const hi = headerIndex(header, "帽");
    const sui = headerIndex(header, "须");
    const pi = headerIndex(header, "道具");
    const bi = headerIndex(header, "依据");
    if (hi >= 0 && sui >= 0 && pi >= 0 && bi >= 0) {
      stateHead = headNo;
      if (!body.length) {
        findings.push(finding("A17", DOC_FILES["01"], headNo, "段状态账没有数据行（每段一行）"));
      }
      for (const [no, cells] of body) {
        for (const [name, idx] of [["帽", hi], ["须", sui], ["道具", pi], ["依据", bi]]) {
          const value = (cells[idx] || "").trim();
          if (isPlaceholder(value)) {
            findings.push(finding("A17", DOC_FILES["01"], no, `段状态账「${name}」为空或占位（跨段状态必填）`));
          }
        }
      }
    }
  }
  if (auditHead === null) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到批次校验记录（表头含 门/结果/证据），A17 未执行"));
  if (cardHead === null) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到批次生产卡（表头含 段号/镜号/生成时长），A17 未执行"));
  if (stateHead === null) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到段状态账（表头含 帽/须/道具/依据），A17 状态三问未核对"));

  if (project.doc("04") !== null) {
    for (const [no, ln] of promptLines(project.doc("04"))) {
      const s = ln.trim();
      if (!s.startsWith("@") || !s.includes("=")) continue;
      if (!s.includes("Ref") && !s.includes("REF")) continue;
      if (!s.includes("锁定") && !s.includes("只取")) {
        findings.push(finding("A17", DOC_FILES["04"], no, `参考声明缺「锁定/只取」：${s.slice(0, 24)}`));
      }
      if (!s.includes("不复刻")) {
        findings.push(finding("A17", DOC_FILES["04"], no, `参考声明缺「不复刻」：${s.slice(0, 24)}`));
      }
    }
  }

  if (project.doc("04") !== null) {
    (project.doc("04") || []).forEach((ln, i) => {
      const s = ln.trim();
      if (s.startsWith("## ") && /修正说明|修正记录|变更记录|附录/.test(s)) {
        findings.push(finding(
          "A17", DOC_FILES["04"], i + 1,
          `04 出现非段落标题（修正说明/变更记录应写 01）：${s.slice(0, 30)}`,
        ));
      }
    });
  }

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
      } else {
        const bible = styleBible(project);
        const m = /风格锁[：:]\s*(.+)/.exec(text);
        if (bible && m && !normWs(m[1]).includes(normWs(bible))) {
          findings.push(finding("A17", DOC_FILES["04"], headNo, "风格锁未逐字复制 02 风格圣经（A1/A17）"));
        }
      }
    }
  }

  const chars = namesWithRefs(project, "角色锚定表");
  const props = namesWithRefs(project, "道具锚定表");
  if ((chars.size || props.size) && project.doc("04") !== null) {
    for (const shot of shotBlocks(project.doc("04"))) {
      const text = shotContent(shot);
      for (const name of chars) {
        if (text.includes(name) && !hasInlineRef(text, name)) {
          findings.push(finding(
            "A17", DOC_FILES["04"], shot[0][0],
            `角色「${name}」在本镜出现但名字后未绑定参考（写 角色名 @{{Ref N}}——硬规则20）`,
          ));
        }
      }
      for (const name of props) {
        if (text.includes(name) && !hasInlineRef(text, name)) {
          findings.push(finding(
            "A17", DOC_FILES["04"], shot[0][0],
            `道具「${name}」在本镜出现但名字后未绑定参考（写 道具名 @{{Ref N}}——硬规则20）`,
          ));
        }
      }
    }
  }
  return findings;
}
