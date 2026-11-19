#!/usr/bin/env node
// vigen check.mjs — CLI + 门注册（行为对齐 check.py；Phase 2c：K1-K17 全量）。
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { DOC_FILES, Project, finding } from "./vigen-md.mjs";
import { gateK1, gateK2, gateK3, gateK4, gateK5, gateK6 } from "./check-gates-a.mjs";
import { gateK7, gateK8, gateK9, gateK10, gateK11, gateK12 } from "./check-gates-b.mjs";
import { gateK13, gateK14 } from "./check-gates-c.mjs";
import { gateK15, gateK16 } from "./check-gates-d.mjs";
import { gateA16, gateA17, gateA18, gateA19 } from "./check-gates-e.mjs";
import { gateK17 } from "./check-gates-f.mjs";
import { gateK18 } from "./check-gates-g.mjs";

const ALL_GATES = [
  "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8",
  "K9", "K10", "K11", "K12", "K13", "K14", "K15", "K16", "K17", "A16", "A17", "A18", "A19", "K18",
];
const IMPLEMENTED = new Set(ALL_GATES);
const GATES = [
  ["K1", gateK1], ["K2", gateK2], ["K3", gateK3], ["K4", gateK4],
  ["K5", gateK5], ["K6", gateK6], ["K7", gateK7], ["K8", gateK8],
  ["K9", gateK9], ["K10", gateK10], ["K11", gateK11], ["K12", gateK12],
  ["K13", gateK13], ["K14", gateK14], ["K15", gateK15], ["K16", gateK16],
  ["K17", gateK17],
];
const OPTIONAL_GATES = [
  ["A16", gateA16], ["A17", gateA17], ["A18", gateA18], ["A19", gateA19], ["K18", gateK18],
];
const ALL_GATE_FNS = [...GATES, ...OPTIONAL_GATES];

function loadBatchGates() {
  try {
    const scriptDir = path.dirname(fileURLToPath(import.meta.url));
    const raw = readFileSync(path.join(scriptDir, "batch-gates.json"), "utf8");
    const data = JSON.parse(raw);
    const out = {};
    for (const [name, gates] of Object.entries(data)) {
      if (Array.isArray(gates)) out[name] = gates.map(String);
    }
    return out;
  } catch {
    return {};
  }
}

function usage() {
  return [
    "usage: check.mjs [-h] [--partial] [--gate GATE] [--batch BATCH] [--batch-list] [--video-variant SUFFIX] project_dir",
    "",
    "vigen 项目文件机械校验（默认 K1-K17；A16-A19/K18 为可选审计：A16 锁定审计，A17 执行契约留痕，A18 图片约束预算，A19 母版事实一致性，K18 动作链诊断）",
    "",
    "positional arguments:",
    "  project_dir   项目目录（含 01-06 Markdown）",
    "",
    "options:",
    "  -h, --help    show this help message and exit",
    "  --partial     只核对已有文档；缺文档的门静默跳过",
    "  --gate GATE   只跑指定门，可用逗号分隔，如 K1,K5",
    "  --batch BATCH 中间批只跑映射门（03/04/05/milestone）；--gate 优先",
    "  --batch-list  打印批次门映射",
    "  --video-variant SUFFIX  轻量项目：选择 视频生成提示词_<后缀>.md（如 9x16）",
  ].join("\n");
}

function parseArgs(argv) {
  const out = {
    projectDir: null, partial: false, gate: null, batch: null, batchList: false,
    videoVariant: null, help: false, error: null,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "-h" || a === "--help") {
      out.help = true;
    } else if (a === "--partial") {
      out.partial = true;
    } else if (a === "--batch-list") {
      out.batchList = true;
    } else if (a === "--gate") {
      if (i + 1 >= argv.length) {
        out.error = "argument --gate: expected one argument";
        break;
      }
      out.gate = argv[i + 1];
      i += 1;
    } else if (a.startsWith("--gate=")) {
      out.gate = a.slice("--gate=".length);
    } else if (a === "--batch") {
      if (i + 1 >= argv.length) {
        out.error = "argument --batch: expected one argument";
        break;
      }
      out.batch = argv[i + 1];
      i += 1;
    } else if (a.startsWith("--batch=")) {
      out.batch = a.slice("--batch=".length);
    } else if (a === "--video-variant") {
      if (i + 1 >= argv.length) {
        out.error = "argument --video-variant: expected one argument";
        break;
      }
      out.videoVariant = argv[i + 1];
      i += 1;
    } else if (a.startsWith("--video-variant=")) {
      out.videoVariant = a.slice("--video-variant=".length);
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

function projectProfile(project) {
  const text = (project.doc("01") || []).join("\n");
  if (text.includes("交付形态：轻量") || text.includes("交付形态: 轻量")) return "light";
  const hasAlias = existsSync(path.join(project.root, "图片生成提示词.md"))
    || existsSync(path.join(project.root, "视频生成提示词.md"))
    || (() => {
      try {
        return readdirSync(project.root).some((n) => /^视频生成提示词_.*\.md$/.test(n));
      } catch {
        return false;
      }
    })();
  if (hasAlias && project.doc("02") === null && project.doc("05") === null) return "light";
  return "standard";
}

export function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  if (args.help) {
    console.log(usage());
    return 0;
  }
  const batchMap = loadBatchGates();
  if (args.batchList) {
    for (const [name, gates] of Object.entries(batchMap)) {
      console.log(`${name}: ${gates.join(", ")}`);
    }
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
  const project = new Project(root, args.videoVariant);
  const doc01 = project.doc("01");
  const doc04 = project.doc("04");
  if (project.videoVariantMissing) {
    console.log(`未找到视频生成提示词_${args.videoVariant}.md——检查 --video-variant 后缀`);
    return 2;
  }
  if (doc01 === null && doc04 === null) {
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
    const missing = [...wanted].filter((gid) => !IMPLEMENTED.has(gid)).sort();
    if (missing.length) {
      console.log(`check.mjs 未移植门：${missing.join(", ")}（请用 check.py 跑全量）`);
      return 2;
    }
    selected = wanted;
  } else if (args.batch) {
    const gates = batchMap[args.batch];
    if (!gates) {
      console.log(`未知批次：${args.batch}（合法取值：${Object.keys(batchMap).join(", ")}）`);
      return 2;
    }
    const wanted = new Set(gates.map((g) => g.trim().toUpperCase()).filter(Boolean));
    const bad = [...wanted].filter((gid) => !ALL_GATES.includes(gid)).sort();
    if (bad.length) {
      console.log(`批次 ${args.batch} 含未知门：${bad.join(", ")}`);
      return 2;
    }
    const missing = [...wanted].filter((gid) => !IMPLEMENTED.has(gid)).sort();
    if (missing.length) {
      console.log(`check.mjs 未移植门：${missing.join(", ")}（请用 check.py 跑全量）`);
      return 2;
    }
    selected = wanted;
  }

  const findings = [];
  let rcExtra = 0;
  for (const note of project.notes) {
    findings.push(finding("PRE", DOC_FILES["04"], 0, note));
  }
  if (!args.partial) {
    const profile = projectProfile(project);
    const required = profile === "light" ? ["01", "03", "04"] : ["01", "02", "03", "04", "05"];
    if (profile === "light") {
      console.log("profile: 轻量（03/04 使用别名；02/05 可缺省）");
    }
    let variantFiles = [];
    try {
      variantFiles = readdirSync(project.root).filter((n) => /^视频生成提示词_.*\.md$/.test(n));
    } catch {
      variantFiles = [];
    }
    for (const key of required) {
      if (key === "04" && project.doc(key) === null && variantFiles.length) continue;
      if (project.doc(key) === null) {
        findings.push(finding(
          "PRE", DOC_FILES[key], 0,
          `全量校验缺文件 ${DOC_FILES[key]}（只跑部分文档请用 --partial）`,
        ));
      }
    }
  }
  for (const [gateId, gateFn] of (selected !== null ? ALL_GATE_FNS : GATES)) {
    if (selected !== null && !selected.has(gateId)) continue;
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
