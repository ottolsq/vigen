// A20 动作链自检（opt-in 诊断门，V3.23 原名 K18）——行为对齐 check.py gate_a20。
// V3.26：打斗段另警告抽象频率写法与中景以上 90° 侧面正拍。
import { DOC_FILES, blocks, blockText, finding } from "./vigen-md.mjs";

const AT_RE = /^\s*(?:[-*]\s*)?At\s+(\d{1,3}):(\d{2})(?:\.(\d{1,3}))?\s*[：:,]?/;
const RANGE_RE = /^\s*(\d+(?:\.\d+)?)\s*s?\s*[–\-—~～至]\s*(\d+(?:\.\d+)?)\s*s?\s*(?:[｜|]\s*)?(.*)$/;
const DUR_RE = /生成\s*(\d+(?:\.\d+)?)\s*s/;
const ACTION_LOCK_RE = /^\s*[-*]?\s*(?:自然)?动作锁\s*[：:]\s*(.+)$/;
const PROP_LOCK_RE = /^\s*[-*]?\s*道具锁\s*[：:]\s*(.+)$/;
const NEG_HDR_RE = /^\s*(禁止|NO|【负面提示词】)/;
const PUNCT_RE = /[\s，。；、：:,.!?！？（）()"'“”「」\-—…]+/g;

function norm(text) {
  return (text || "").replace(PUNCT_RE, "");
}

function fencedBlocks(lines) {
  const out = [];
  let cur = null;
  let start = 0;
  lines.forEach((ln, i) => {
    if (ln.trim().startsWith("```")) {
      if (cur === null) {
        cur = [];
        start = i + 1;
      } else {
        out.push([start, cur.join("\n")]);
        cur = null;
      }
      return;
    }
    if (cur !== null) cur.push(ln);
  });
  if (cur !== null) out.push([start, cur.join("\n")]);
  return out;
}

function units(doc) {
  const segs = blocks(doc, true);
  if (segs.length) return segs.map((b) => [b[0][0], blockText(b)]);
  const fenced = fencedBlocks(doc);
  if (fenced.length) return fenced;
  return [[1, doc.join("\n")]];
}

function warn(gate, key, msg) {
  return finding(gate, DOC_FILES[key], 0, "警告：" + msg);
}

function matchChain(body, items) {
  const normBody = norm(body);
  const missing = [];
  const positions = [];
  let hits = 0;
  for (const raw of items) {
    let item = raw.split(/[（(]/, 1)[0].trim();
    if (item.includes("：") || item.includes(":")) {
      const parts = item.split(/[：:]/);
      item = parts[parts.length - 1].trim();
    }
    const key = norm(item);
    const chars = Array.from(key);
    if (chars.length < 2) {
      missing.push(item);
      continue;
    }
    const pos = normBody.indexOf(key);
    if (pos >= 0) {
      hits += 1;
      positions.push([pos, chars.length]);
      continue;
    }
    let found = false;
    for (let size = chars.length - 1; size >= 2; size -= 1) {
      if (normBody.indexOf(chars.slice(0, size).join("")) >= 0) {
        found = true;
        break;
      }
    }
    if (found) hits += 1;
    else missing.push(item);
  }
  return { missing, positions, hits };
}

export function gateA20(project) {
  const doc = project.doc("04");
  if (doc === null) return [warn("A20", "04", "04 缺失，A20 未执行")];
  const findings = [];
  const warned = new Set();
  for (const [unitLine, text] of units(doc)) {
    const lines = text.split(/\r\n|\r|\n/);
    const durM = DUR_RE.exec(text);
    const duration = durM ? Number(durM[1]) : null;

    // ---- 时间块 ----
    const atBlocks = [];
    for (const ln of lines) {
      const m = AT_RE.exec(ln);
      if (m) {
        const sec = Number(m[1]) * 60 + Number(m[2]) + Number(m[3] || 0) / 1000;
        atBlocks.push([sec, ln.slice(m[0].length).trim()]);
      }
    }
    const rangeBlocks = [];
    lines.forEach((ln, i) => {
      const m = RANGE_RE.exec(ln);
      if (!m) return;
      let content = (m[3] || "").trim();
      if (!content) {
        let look = i + 1;
        while (look < lines.length && !RANGE_RE.exec(lines[look]) && !AT_RE.exec(lines[look])) {
          if (lines[look].trim()) {
            content = lines[look].trim();
            break;
          }
          look += 1;
        }
      }
      rangeBlocks.push([Number(m[1]), Number(m[2]), content]);
    });
    if (atBlocks.length) {
      if (atBlocks[0][0] > 0.5) {
        findings.push(finding(
          "A20", DOC_FILES["04"], unitLine,
          `首个时间块起始 ${atBlocks[0][0].toFixed(1)}s > 0.5s（时间轴须从 0 附近开始）`,
        ));
      }
      let prev = -1;
      for (const [sec, content] of atBlocks) {
        if (sec <= prev) {
          findings.push(finding(
            "A20", DOC_FILES["04"], unitLine,
            `时间块 ${sec.toFixed(1)}s 未严格递增（上一块 ${prev.toFixed(1)}s）`,
          ));
        }
        if (!content) {
          findings.push(finding(
            "A20", DOC_FILES["04"], unitLine,
            `时间块 ${sec.toFixed(1)}s 后无内容（空时间块）`,
          ));
        }
        prev = sec;
      }
      if (duration !== null && atBlocks[atBlocks.length - 1][0] > duration + 0.2) {
        findings.push(finding(
          "A20", DOC_FILES["04"], unitLine,
          `末个时间块 ${atBlocks[atBlocks.length - 1][0].toFixed(1)}s > 生成时长 ${duration.toFixed(1)}s + 0.2s`,
        ));
      }
    } else if (rangeBlocks.length) {
      if (rangeBlocks[0][0] > 0.5) {
        findings.push(finding(
          "A20", DOC_FILES["04"], unitLine,
          `首个时间块起始 ${rangeBlocks[0][0].toFixed(1)}s > 0.5s（时间轴须从 0 附近开始）`,
        ));
      }
      let prevStart = -1;
      let prevEnd = -1;
      for (const [start, end, content] of rangeBlocks) {
        if (start < prevStart) {
          findings.push(finding(
            "A20", DOC_FILES["04"], unitLine,
            `时间块 ${start.toFixed(1)}s–${end.toFixed(1)}s 乱序（前一拍从 ${prevStart.toFixed(1)}s 开始）`,
          ));
        } else if (prevEnd >= 0 && start > prevEnd + 1.0) {
          findings.push(finding(
            "A20", DOC_FILES["04"], unitLine,
            `时间块断档：${prevStart.toFixed(1)}s–${prevEnd.toFixed(1)}s 之后下一拍从 ${start.toFixed(1)}s 开始（>${(prevEnd + 1.0).toFixed(1)}s 间隙）`,
          ));
        }
        if (!content) {
          findings.push(finding(
            "A20", DOC_FILES["04"], unitLine,
            `时间块 ${start.toFixed(1)}s–${end.toFixed(1)}s 后无内容（空时间块）`,
          ));
        }
        prevStart = start;
        prevEnd = end;
      }
      if (duration !== null && rangeBlocks[rangeBlocks.length - 1][1] > duration + 0.2) {
        findings.push(finding(
          "A20", DOC_FILES["04"], unitLine,
          `末个时间块 ${rangeBlocks[rangeBlocks.length - 1][1].toFixed(1)}s > 生成时长 ${duration.toFixed(1)}s + 0.2s`,
        ));
      }
    } else {
      const key = "k18-no-time";
      if (!warned.has(key)) {
        findings.push(warn("A20", "04", "本块无时间块（At/时间范围），A20 时间连续性未核对"));
        warned.add(key);
      }
    }

    // ---- 动作锁 ----
    let lockLine = -1;
    let lockItems = [];
    lines.forEach((ln, i) => {
      if (lockLine >= 0) return;
      const m = ACTION_LOCK_RE.exec(ln);
      if (m) {
        lockLine = i;
        lockItems = m[1].split("→").map((x) => x.trim()).filter(Boolean);
      }
    });
    const propBodyLines = [];
    let negProp = false;
    for (const ln of lines) {
      if (ACTION_LOCK_RE.test(ln) || PROP_LOCK_RE.test(ln)) continue;
      if (NEG_HDR_RE.test(ln)) negProp = true;
      if (!negProp) propBodyLines.push(ln);
    }
    const propBody = norm(propBodyLines.join("\n"));
    const actionBodyLines = [];
    if (lockLine >= 0) {
      const lockLabelRe = /^\s*(身份锁|表情锁|表演锁|说话人锁|道具锁|空间锁|风格锁|声音锁|动作锁)\s*[：:]/;
      let startIdx = lockLine + 1;
      lines.forEach((ln, i) => {
        if (lockLabelRe.test(ln)) startIdx = Math.max(startIdx, i + 1);
        else if (ln.trim().startsWith("detailed_description")) startIdx = Math.max(startIdx, i + 1);
      });
      let negAct = false;
      for (let i = startIdx; i < lines.length; i += 1) {
        const ln = lines[i];
        if (/^\s*(overall_soundscape|non_diegetic_music|CONTINUITY RULE)/i.test(ln)) break;
        if (NEG_HDR_RE.test(ln)) negAct = true;
        if (!negAct) actionBodyLines.push(ln);
      }
      if (!actionBodyLines.some((ln) => ln.trim())) {
        actionBodyLines.push(...propBodyLines);
      }
    }
    if (lockItems.length >= 2) {
      const { missing, positions } = matchChain(actionBodyLines.join("\n"), lockItems);
      const missRatio = missing.length / lockItems.length;
      if (missRatio > 0.5) {
        findings.push(warn(
          "A20", "04",
          `动作锁与正文措辞差异较大（${missing.length}/${lockItems.length} 项未匹配），跳过顺序检查（人工确认）`,
        ));
      } else {
        for (const item of missing) {
          findings.push(finding(
            "A20", DOC_FILES["04"], unitLine,
            `动作锁项「${item}」未在正文找到（可能改写或遗漏，人工确认）`,
          ));
        }
        const strong = positions;
        if (!missing.length && positions.length === lockItems.length) {
          for (let i = 0; i + 1 < strong.length; i += 1) {
            if (strong[i + 1][0] < strong[i][0]) {
              findings.push(finding(
                "A20", DOC_FILES["04"], unitLine,
                "动作锁顺序与正文不一致（可能改写或遗漏，人工确认）",
              ));
              break;
            }
          }
        }
      }
    }

    // ---- 道具状态账 ----
    let propLine = "";
    for (const ln of lines) {
      const m = PROP_LOCK_RE.exec(ln);
      if (m) {
        propLine = m[1];
        break;
      }
    }
    if (propLine) {
      const entries = propLine.split(/[；;]/).map((e) => e.trim()).filter(Boolean);
      let parsed = false;
      for (const entry of entries) {
        if (!entry.includes("｜") && !entry.includes("|")) continue;
        const parts = entry.split(/[｜|]/).map((p) => p.trim());
        if (parts.length < 2) continue;
        parsed = true;
        const name = parts[0];
        const joined = parts.join(" ");
        const normName = norm(name);
        if (joined.includes("不入画")) {
          if (normName && propBody.includes(normName)) {
            findings.push(warn("A20", "04", `道具「${name}」标记不入画，但正文出现（人工确认）`));
          }
        } else if (joined.includes("入画")) {
          if (normName && !propBody.includes(normName)) {
            findings.push(finding(
              "A20", DOC_FILES["04"], unitLine,
              `道具「${name}」标记入画，但正文未出现`,
            ));
          }
        }
      }
      const key = `k18-prop-fmt|${unitLine}`;
      if (!parsed && !warned.has(key)) {
        findings.push(warn("A20", "04", "道具锁格式未识别（缺 ｜ 分隔），A20 道具账未核对"));
        warned.add(key);
      }
    }

    // ---- 打斗段正文诊断（V3.26） ----
    if (text.includes("打斗段：是")) {
      const fightBody = propBodyLines.join("\n");
      if (/(每秒|每秒钟|每\s*秒\s*\d+).{0,8}(攻击|出拳|出腿|击打|拳|脚|招)|每击间隔|攻击频率|次\s*\/\s*秒|机枪节奏/.test(fightBody)) {
        findings.push(warn(
          "A20", "04",
          "打斗段出现抽象频率写法（每秒攻击N次/每击间隔/攻击频率/机枪节奏）——改用招式链：招式+落点+防守反馈（action-combat §6.5）",
        ));
      }
      for (const ln of propBodyLines) {
        if (/(中景|全景|中全景|大全景|远景)/.test(ln)
            && /(90\s*°?\s*侧|侧面\s*90|90\s*度\s*侧|正侧拍|90°\s*侧拍)/.test(ln)) {
          findings.push(warn(
            "A20", "04",
            "打斗段中景及以上出现 90° 侧面正拍（格斗游戏感/丢纵深）——改 30-60° 斜角（action-combat §6）",
          ));
          break;
        }
      }
    }
  }
  return findings;
}
