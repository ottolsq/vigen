// check.mjs 共享 helpers 与常量（K1-K12 共用）。
import {
  DOC_FILES,
  finding,
  SHOT_ID_RE,
  tableRows,
  VOIDED_RE,
} from "./vigen-md.mjs";

export const STORY_ALIASES = {
  镜号: ["镜号", "镜头"],
  运镜: ["运镜"],
  运镜动机: ["运镜动机", "动机"],
  生成时长: ["生成时长"],
};

export const DUR_ONE = (s) => /(\d+(?:\.\d+)?)\s*s/.exec(s);
export const DUR_G = () => /(\d+(?:\.\d+)?)\s*s/g;
export const REF_SHOT_G = () => /(?:镜|镜头)\s*(S?\d+[a-z]?)/g;
export const TECH_LINE = /fps|快门|帧率|镜头运动|运镜库/;
export const NEG_LINE = /^\s*[*\-—·]?\s*(禁止|不要|不得|避免|无|没有|不)/;
export const SECTION_LABELS = new Set([
  "SCENE CONTEXT", "ACTIVE REFERENCES", "CONTINUITY RULE", "FORMAT",
  "CAMERA / EDITING", "ENDING FRAME", "PERFORMANCE LOCK", "FACE LOCK",
  "AUDIO", "LIGHTING", "NO",
]);
export const HUMAN_ACTION = new Set("说看走站坐抬转拿握伸退冲停笑低靠盯望递接推拉蹲跪扑抓挥砍刺劈跳跑");

export function warn(gate, key, msg) {
  return finding(gate, DOC_FILES[key], 0, "警告：" + msg);
}

export function cpLen(s) {
  return Array.from(s).length;
}

export function cpSlice(s, n) {
  return Array.from(s).slice(0, n).join("");
}

export function g(x) {
  return String(Number(x));
}

export function f1(x) {
  return Number(x).toFixed(1);
}

export function plotRows(project) {
  return tableRows(project.doc("01"), ["情节点", "覆盖镜号"], {
    覆盖镜号: ["覆盖镜号", "覆盖"],
  });
}

export function storyRows(project) {
  const rows = tableRows(project.doc("01"), ["镜号", "运镜"], STORY_ALIASES);
  if (rows !== null) return rows;
  return tableRows(project.doc("01"), ["镜号"], STORY_ALIASES);
}

export function shotIds(project) {
  const live = new Map();
  const voided = new Map();
  for (const r of storyRows(project) || []) {
    const raw = (r.cells["镜号"] || "").trim();
    const vm = VOIDED_RE.exec(raw);
    if (vm) {
      if (!voided.has(vm[1])) voided.set(vm[1], r.line);
      continue;
    }
    const m = SHOT_ID_RE.exec(raw);
    if (m && !live.has(m[1])) live.set(m[1], r.line);
  }
  return [live, voided];
}
