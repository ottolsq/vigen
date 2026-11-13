// K17 提示词卫生（V3.17）——与 check.py gate_k17 行为对齐。
import { DOC_FILES, blocks, dialogueQuotes, finding } from "./vigen-md.mjs";

const MUSIC_WORDS = /音乐|配乐|旋律|节拍|和声|音符|伴奏|演唱|哼唱|吟唱|节奏性|节奏点|BGM/i;
const QUOTE_STRIP = /"[^"]*"|“[^”]*”|「[^」]*」|『[^』]*』/g;

function dropNegativeSection(items) {
  const out = [];
  let inside = false;
  for (const [no, ln] of items) {
    const s = ln.trim();
    if (s.startsWith("【负面提示词】") || s.toUpperCase().startsWith("NEGATIVE PROMPT")) {
      inside = true;
      continue;
    }
    if (inside) {
      if (s.startsWith("【") || s.startsWith("## ")) inside = false;
      else continue;
    }
    out.push([no, ln]);
  }
  return out;
}

function promptLines(lines) {
  if (lines === null) return [];
  if (lines.join("\n").includes("```")) {
    const out = [];
    let current = [];
    let inside = false;
    lines.forEach((ln, i) => {
      if (ln.trim().startsWith("```")) {
        if (inside && current.length) out.push(...dropNegativeSection(current));
        current = [];
        inside = !inside;
        return;
      }
      if (inside) current.push([i + 1, ln]);
    });
    if (inside && current.length) out.push(...dropNegativeSection(current));
    if (out.length) return out;
  }
  return dropNegativeSection(lines
    .map((ln, i) => [i + 1, ln])
    .filter(([, ln]) => !/^\s*[>#|]/.test(ln)));
}

export function gateK17(project) {
  const findings = [];
  for (const key of ["04", "03"]) {
    const doc = project.doc(key);
    if (doc === null) continue;
    for (const [no, ln] of promptLines(doc)) {
      const stripped = ln.replace(QUOTE_STRIP, "");
      const m = stripped.match(MUSIC_WORDS);
      if (m) {
        findings.push(finding(
          "K17", DOC_FILES[key], no,
          `提示词正文出现音乐类词「${m[0]}」——改为正向声音白名单（V3.16：写音乐词会诱导音乐层）`,
        ));
      }
    }
  }

  const doc04 = project.doc("04");
  if (doc04 !== null) {
    for (const block of blocks(doc04, true)) {
      const blockLines = block.map(([, t]) => t);
      const text = promptLines(blockLines).map(([, t]) => t).join("\n");
      const hasDialogue = dialogueQuotes(blockLines).length > 0;
      if (!hasDialogue && !/无台词|无旁白|无人声/.test(text)) {
        findings.push(finding(
          "K17", DOC_FILES["04"], block[0][0],
          "无台词段缺「无台词/无旁白/无人声」首行声明（V3.16）",
        ));
      }
      if (/AUDIO|声音/.test(text)
        && !text.includes("没有第二种声音")
        && !text.includes("没有任何持续声底")) {
        findings.push(finding(
          "K17", DOC_FILES["04"], block[0][0],
          "声音节缺正向收尾「没有第二种声音，也没有任何持续声底」（V3.16）",
        ));
      }
    }
  }
  return findings;
}
