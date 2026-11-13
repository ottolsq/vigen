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

const TIME_RANGE_ANY = /^\s*\d+(?:\.\d+)?\s*s?\s*[–\-—~～至]\s*\d+(?:\.\d+)?\s*s?\s*(?:[｜|]|\s+镜头)/;
const CUT_LINE = /^\s*\d+(?:\.\d+)?\s*s?\s*(?:HARD CUT|硬切|相似动作|前景遮挡|形状匹配|甩镜|闪白|匹配剪辑|叠化|淡入淡出|闪黑|缩放|划像|转场)(?:\s|（|\()/i;
const CONTINUITY_NEG = /瞬移|换位|消失|重复|状态|teleport|swapp|disappear|duplicate|continuity/i;
const WALK_STOPS = [
  "\nACTIVE REFERENCES", "\n**ACTIVE REFERENCES",
  "\nCONTINUITY RULE", "\n**CONTINUITY",
  "\n出场人物", "\n**出场人物",
  "\nFORMAT", "\n**FORMAT",
  "\n【", "\n## ",
];

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

function extractBetween(text, start, stops) {
  const idx = text.indexOf(start);
  if (idx < 0) return "";
  const rest = text.slice(idx + start.length);
  let cut = rest.length;
  for (const stop of stops) {
    const j = rest.indexOf(stop);
    if (j >= 0) cut = Math.min(cut, j);
  }
  return rest.slice(0, cut);
}

function groupsWithRefs(project) {
  const lines = project.doc("02");
  if (lines === null) return new Set();
  const blocksArr = [];
  let inSection = false;
  let cur = null;
  for (let i = 0; i < lines.length; i += 1) {
    const ln = lines[i];
    if (ln.startsWith("## ")) {
      inSection = ln.slice(3).trim().startsWith("群像锚定表");
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
    let name = block[0][1].slice(4).trim();
    name = name.split(/[（(]/)[0].trim();
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

function negativeSectionText(text) {
  const m = text.match(/【负面提示词】|NEGATIVE\s+PROMPTS?/i);
  if (!m) return "";
  return extractBetween(text, m[0], ["\n【", "\n## ", "\n```"]);
}

function modelNegativeSupport(project) {
  const rows = tableRows(project.doc("02"), ["用途", "模型"]);
  for (const r of rows || []) {
    const purpose = cell(r, "用途");
    if (!purpose.includes("负向") && !purpose.includes("负面")) continue;
    const value = cell(r, "模型").trim();
    if (!value || isPlaceholder(value)) continue;
    if (value.includes("不支持")) return "不支持";
    if (value.includes("支持")) return "支持";
  }
  return "";
}

function hasFullNegativeList(project) {
  const lines = project.section("02", "全片负面清单");
  for (const [, ln] of lines) {
    const s = ln.trim();
    if (!s || /^[>#`]/.test(s)) continue;
    if (s.startsWith("|")) {
      const cells = s.replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
      if (cells.length < 2) continue;
      if (cells.every((c) => !c || /^:?-{2,}:?$/.test(c))) continue;
      if (cells[0] === "组" || cells[1].includes("条目")) continue;
      if (cells.slice(1).some((c) => c && !isPlaceholder(c))) return true;
      continue;
    }
    if (!isPlaceholder(s)) return true;
  }
  return false;
}

function shotContent(shot) {
  const out = [];
  for (const [, t] of shot) {
    const s = t.trim();
    if (["ENDING FRAME", "PERFORMANCE LOCK", "FACE LOCK", "AUDIO", "LIGHTING", "NO"].includes(s.toUpperCase())) break;
    if (s.startsWith("表演：") || s.startsWith("表演注") || s.startsWith("自检")
      || s.startsWith("走位总谱") || s.startsWith("连续性铁律") || s.startsWith("动作桥")) continue;
    if (s.includes("（动作桥") || s.includes("(动作桥")) continue;
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
          ["运镜选型", ["运镜选型", "运镜"]],
          ["转场选型", ["转场选型"]],
          ["表演依据", ["表演依据"]],
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
          for (const name of ["帽", "须", "道具", "运镜选型", "转场选型", "表演依据"]) {
            const idx = colIdx.get(name);
            if (idx >= 0) {
              const value = (cells[idx] || "").trim();
              if (!value || isPlaceholder(value)) {
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
    const vi = headerIndex(header, "服装版本");
    if (hi >= 0 && sui >= 0 && pi >= 0 && bi >= 0 && vi >= 0) {
      stateHead = headNo;
      if (!body.length) {
        findings.push(finding("A17", DOC_FILES["01"], headNo, "段状态账没有数据行（每段一行）"));
      }
      for (const [no, cells] of body) {
        for (const [name, idx] of [["帽", hi], ["须", sui], ["道具", pi], ["依据", bi]]) {
          const value = (cells[idx] || "").trim();
          if (!value || isPlaceholder(value)) {
            findings.push(finding("A17", DOC_FILES["01"], no, `段状态账「${name}」为空或占位（跨段状态必填）`));
          }
        }
      }
    }
  }
  const storyRows = tableRows(project.doc("01"), ["镜号", "运镜"], STORY_ALIASES);
  if (storyRows) {
    for (const r of storyRows) {
      const value = cell(r, "运镜").trim();
      if (!value || ["—", "-", "–"].includes(value)) continue;
      if (!/M\d{2}/.test(value)) {
        findings.push(finding(
          "A17", DOC_FILES["01"], r.line,
          `运镜列缺 Mxx 编号（V3.20——写不出编号=没有选）：${value.slice(0, 24)}`,
        ));
      }
    }
  }

  const transitions = ["硬切", "相似动作", "前景遮挡", "形状匹配", "甩镜", "闪白", "视线", "匹配剪辑",
    "叠化", "淡入淡出", "淡出", "闪黑", "缩放", "划像"];
  const transRows = tableRows(project.doc("01"), ["镜号", "转场"], STORY_ALIASES);
  if (transRows) {
    for (const r of transRows) {
      const value = cell(r, "转场").trim();
      if (!value || ["—", "-", "–"].includes(value)) continue;
      if (value.includes("硬切")) {
        if (!/硬切\s*[（(].+[）)]/.test(value)) {
          findings.push(finding(
            "A17", DOC_FILES["01"], r.line,
            `转场写「硬切」须带理由（硬切（理由）——V3.21）：${value.slice(0, 24)}`,
          ));
        }
        continue;
      }
      if (value.includes("匹配剪辑") && !/匹配剪辑\s*[（(].+[）)]/.test(value)) {
        findings.push(finding(
          "A17", DOC_FILES["01"], r.line,
          `匹配剪辑须写对应对象（匹配剪辑（对应：A→B）——V3.22）：${value.slice(0, 24)}`,
        ));
        continue;
      }
      if (!transitions.some((t) => value.includes(t))) {
        findings.push(finding(
          "A17", DOC_FILES["01"], r.line,
          `转场不在库内（生成端 8 种：硬切/相似动作/前景遮挡/形状匹配/甩镜/闪白/视线/匹配剪辑；剪辑端 5 种：叠化/淡入淡出/闪黑/缩放/划像）：${value.slice(0, 24)}`,
        ));
      }
    }
  }

  const ledgerNames = ["运镜库", "转场库", "场景镜头序列", "FACS", "身体姿态", "情绪反向", "打斗七段", "导演风格", "VFX", "方向锚", "群像参考", "负面清单", "短剧市场", "内容合规"];
  let ledgerFound = false;
  for (const [headNo, header, body] of iterTables(doc)) {
    const capI = headerIndex(header, "能力");
    const statusI = headerIndex(header, "使用");
    const reasonI = headerIndex(header, "证据", "理由");
    if (capI >= 0 && statusI >= 0 && reasonI >= 0) {
      ledgerFound = true;
      const seenNames = new Set();
      for (const [no, cells] of body) {
        const cap = (cells[capI] || "").trim();
        const status = (cells[statusI] || "").trim();
        const reason = (cells[reasonI] || "").trim();
        for (const name of ledgerNames) if (cap.includes(name)) seenNames.add(name);
        if (isPlaceholder(status) || !status) {
          findings.push(finding("A17", DOC_FILES["01"], no, `可选能力台账「${cap.slice(0, 20)}」未填使用/不适用/待定`));
        } else if (!["使用", "不适用", "待定"].includes(status)) {
          findings.push(finding("A17", DOC_FILES["01"], no, `可选能力台账「${cap.slice(0, 20)}」状态须为 使用/不适用/待定（当前：${status}）`));
        }
        if (isPlaceholder(reason) || !reason) {
          findings.push(finding("A17", DOC_FILES["01"], no, `可选能力台账「${cap.slice(0, 20)}」缺证据/理由`));
        }
      }
      const missingNames = ledgerNames.filter((n) => !seenNames.has(n));
      if (missingNames.length) {
        findings.push(finding("A17", DOC_FILES["01"], headNo, `可选能力台账缺项：${missingNames.join("、")}`));
      }
    }
  }
  if (!ledgerFound) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到可选能力台账（表头含 能力/使用/证据），A17 未核对"));

  if (auditHead === null) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到批次校验记录（表头含 门/结果/证据），A17 未执行"));
  if (cardHead === null) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到批次生产卡（表头含 段号/镜号/生成时长），A17 未执行"));
  if (stateHead === null) findings.push(finding("A17", DOC_FILES["01"], 0, "警告：未找到段状态账（表头含 帽/须/道具/依据），A17 状态三问未核对"));

  if (project.doc("04") !== null) {
    for (const [no, ln] of promptLines(project.doc("04"))) {
      const s = ln.trim();
      if (!s.startsWith("@") || !s.includes("=")) continue;
      if (!s.includes("Ref") && !s.includes("REF")) continue;
      if (!s.includes("锁定") && !s.includes("只取") && !s.includes("仅参考")) {
        findings.push(finding("A17", DOC_FILES["04"], no, `参考声明缺「锁定/只取/仅参考」：${s.slice(0, 24)}`));
      }
      if (!s.includes("不复刻") && !s.includes("不复制")) {
        findings.push(finding("A17", DOC_FILES["04"], no, `参考声明缺「不复刻/不复制」：${s.slice(0, 24)}`));
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
  const segCharNames = namesWithRefs(project, "角色锚定表");
  const segGroupNames = groupsWithRefs(project);
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
      if (text.includes("打斗段：是")) {
        const stages = [
          ["Start State", "起始状态"], ["Intent", "意图"], ["Attack", "攻击"],
          ["Response", "应对"], ["Impact", "命中"], ["Recovery", "恢复"],
          ["End State", "结束状态"],
        ];
        const missingStages = stages
          .filter(([en, zh]) => !text.includes(en) && !text.includes(zh))
          .map(([en]) => en);
        if (missingStages.length) {
          findings.push(finding(
            "A17", DOC_FILES["04"], headNo,
            `打斗段缺七段：${missingStages.join("、")}（action-combat 第7节）`,
          ));
        }
        if (!(project.doc("01") || []).join("\n").includes("交手账")) {
          findings.push(finding(
            "A17", DOC_FILES["04"], headNo,
            "打斗段标记存在但 01 无「打斗交手账」（先写交手账再排镜）",
          ));
        }
      }

      // V3.22 走位总谱：段内出现 ≥2 个有参考图的角色（或群像）→ 走位总谱 + 连续性铁律
      const presentChars = [...segCharNames].filter((n) => text.includes(n)).sort();
      const presentGroups = [...segGroupNames].filter((n) => text.includes(n)).sort();
      const hasGroup = presentGroups.length > 0;
      const shotLines = block.filter(([, t]) => TIME_RANGE_ANY.test(t.trim()));
      if (presentChars.length >= 2 || hasGroup) {
        if (!text.includes("走位总谱")) {
          findings.push(finding(
            "A17", DOC_FILES["04"], headNo,
            "多角色段缺【走位总谱】（硬规则22：每角色位置/坐站走/朝向——防瞬移/换位/消失）",
          ));
        } else {
          const walk = extractBetween(text, "走位总谱", WALK_STOPS);
          if (!walk.includes("连续性铁律") && !text.includes("连续性铁律")) {
            findings.push(finding(
              "A17", DOC_FILES["04"], headNo,
              "走位总谱缺「连续性铁律」（本段承接上段结尾；不得瞬移/换位/消失/离席）",
            ));
          }
          const missingWalk = presentChars.filter((n) => !walk.includes(n));
          if (missingWalk.length) {
            findings.push(finding(
              "A17", DOC_FILES["04"], headNo,
              `走位总谱缺角色位置：${missingWalk.join("、")}（每个在场角色都要写场景锚点+坐站走+朝向）`,
            ));
          }
          const missingGroups = presentGroups.filter((g) => !walk.includes(g));
          if (missingGroups.length) {
            findings.push(finding(
              "A17", DOC_FILES["04"], headNo,
              `走位总谱缺群像位置：${missingGroups.join("、")}（群像写场景锚点+流动范围）`,
            ));
          }
          if (shotLines.length >= 2 && !walk.includes("逐镜动线")) {
            findings.push(finding(
              "A17", DOC_FILES["04"], headNo,
              "多镜段走位总谱缺「逐镜动线」（每镜位置变化：镜头1→镜头2→…）",
            ));
          }
          if ((presentChars.length >= 3 || hasGroup) && shotLines.length >= 2 && !walk.includes("背景动作线")) {
            findings.push(finding(
              "A17", DOC_FILES["04"], headNo,
              "≥3 人段走位总谱缺「背景动作线」（焦点不在也不停/不消失/不换人）",
            ));
          }
        }
      }

      // V3.22 动作桥：多镜段的每个切点须写「动作桥：上镜结尾→本镜开头」
      if (shotLines.length >= 2) {
        if (!text.includes("光影演变")) {
          findings.push(finding(
            "A17", DOC_FILES["04"], headNo,
            "多镜段缺「光影演变」线（起点光→中段变化→收束光——防切镜后光色跳变）",
          ));
        }
        const cutPoints = block
          .map((entry, i) => [i, entry])
          .filter(([, entry]) => CUT_LINE.test(entry[1].trim()));
        if (cutPoints.length) {
          for (const [i, entry] of cutPoints) {
            const window = entry[1] + "\n"
              + block.slice(i + 1, i + 3).map(([, t]) => t).join("\n");
            if (!window.includes("动作桥")) {
              findings.push(finding(
                "A17", DOC_FILES["04"], entry[0],
                "切点缺「动作桥：上镜结尾→本镜开头」（硬规则22）",
              ));
            }
          }
        } else if (!text.includes("动作桥")) {
          findings.push(finding(
            "A17", DOC_FILES["04"], headNo,
            "多镜段未写「动作桥」（硬规则22：每个切点写动作/视线/声音承接）",
          ));
        }
      }

      // V3.22 负面提示词两段式：有【负面提示词】节时查 02 闭环与连续性条目
      const negText = negativeSectionText(text);
      const negSupport = modelNegativeSupport(project);
      if (negText) {
        if (negSupport === "不支持") {
          findings.push(finding(
            "A17", DOC_FILES["04"], headNo,
            "02 标记「负向字段=不支持」，04 仍写【负面提示词】节（负面只进 NO）",
          ));
        }
        if (!hasFullNegativeList(project)) {
          findings.push(finding(
            "A17", DOC_FILES["04"], headNo,
            "有【负面提示词】节但 02 无可用的「全片负面清单」（先登记再引用）",
          ));
        }
        if (!CONTINUITY_NEG.test(negText)) {
          findings.push(finding(
            "A17", DOC_FILES["04"], headNo,
            "【负面提示词】缺本段连续性条目（不瞬移/不换位/不消失/不重复道具/状态不跳变）",
          ));
        }
      } else if (negSupport === "支持") {
        findings.push(finding(
          "A17", DOC_FILES["04"], headNo,
          "02 标记「负向字段=支持」但本段无【负面提示词】节（有负向能力未使用——硬规则21/22）",
        ));
      }
    }
  }

  const chars = namesWithRefs(project, "角色锚定表");
  const props = namesWithRefs(project, "道具锚定表");
  const groups = groupsWithRefs(project);
  if (project.doc("04") !== null) {
    for (const shot of shotBlocks(project.doc("04"))) {
      const text = shotContent(shot);
      if (!/运镜\s*[:：]\s*M\d{2}/.test(text)) {
        findings.push(finding(
          "A17", DOC_FILES["04"], shot[0][0],
          "镜头块缺「运镜：Mxx 库名（R行号）」（V3.20——写不出编号=没有选）",
        ));
      }
      if (!/\d+\s*mm|焦段|等效视角/.test(text)) {
        findings.push(finding(
          "A17", DOC_FILES["04"], shot[0][0],
          "镜头块缺焦段（写 {N}mm 或等效视角；与 01 分镜表一致——V3.22.1）",
        ));
      }
      for (const name of [...chars].sort()) {
        if (text.includes(name) && !hasInlineRef(text, name)) {
          findings.push(finding(
            "A17", DOC_FILES["04"], shot[0][0],
            `角色「${name}」在本镜出现但名字后未绑定参考（写 角色名 @{{Ref N}}——硬规则20）`,
          ));
        }
      }
      for (const name of [...props].sort()) {
        if (text.includes(name) && !hasInlineRef(text, name)) {
          findings.push(finding(
            "A17", DOC_FILES["04"], shot[0][0],
            `道具「${name}」在本镜出现但名字后未绑定参考（写 道具名 @{{Ref N}}——硬规则20）`,
          ));
        }
      }
      for (const name of [...groups].sort()) {
        if (text.includes(name) && !hasInlineRef(text, name)) {
          findings.push(finding(
            "A17", DOC_FILES["04"], shot[0][0],
            `群像「${name}」在本镜出现但名字后未绑定参考（写 群像名 @{{Ref N}}——硬规则20/22）`,
          ));
        }
      }
    }
  }
  return findings;
}

// A18 图片提示词约束预算（V3.22，opt-in）——与 check.py gate_a18 行为对齐。
const CJK_RE = /[一-鿿]/g;
const IMAGE_EXEMPT_RE = /三视图|四视图|设计表|设定图|参考图|人物设定|道具设定|场景设定|文字排版|字体设计|reference sheet|character sheet|prop reference|pattern sheet|图案特写|图案板|typography|text layout|info sheet/i;
const CONSTRAINT_WORD_RE = /禁止|不要|不得|不能|必须|严禁|no\s+/gi;

export function gateA18(project) {
  const findings = [];
  const lines = project.doc("03");
  if (lines === null) {
    findings.push(finding("A18", DOC_FILES["03"], 0, "警告：03 缺失，A18 未执行"));
    return findings;
  }
  const blocksArr = [];
  let current = null;
  lines.forEach((ln, i) => {
    if (ln.trim().startsWith("```")) {
      if (current === null) current = [];
      else {
        blocksArr.push(current);
        current = null;
      }
      return;
    }
    if (current !== null) current.push([i + 1, ln]);
  });
  if (!blocksArr.length) {
    findings.push(finding("A18", DOC_FILES["03"], 0, "警告：未找到代码围栏提示词，A18 未执行"));
    return findings;
  }
  for (const block of blocksArr) {
    const text = block.map(([, t]) => t).join("\n");
    if (!text.trim() || IMAGE_EXEMPT_RE.test(text)) continue;
    const cjk = (text.match(CJK_RE) || []).length;
    if (cjk > 260) {
      findings.push(finding(
        "A18", DOC_FILES["03"], block[0][0],
        `图片提示词正文 ${cjk} 汉字（>260）：约束过密可能压制 GPT-image 想象力；按 prompt-rules 0.12 先删无关装饰→再删重复维度→最后才动风格/光线锚`,
      ));
    }
    const constraints = (text.match(CONSTRAINT_WORD_RE) || []).length;
    if (constraints > 10) {
      findings.push(finding(
        "A18", DOC_FILES["03"], block[0][0],
        `图片提示词约束词 ${constraints} 处（>10）：改成「意图句+2-3 关键视觉」，负面只留承重项`,
      ));
    }
  }
  return findings;
}
