#!/usr/bin/env node
// vigen check.mjs — CLI + 门注册（行为对齐 check.py；Phase 2c：K1-K16 全量）。
import { existsSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { DOC_FILES, Project, finding } from "./vigen-md.mjs";
import { gateK1, gateK2, gateK3, gateK4, gateK5, gateK6 } from "./check-gates-a.mjs";
import { gateK7, gateK8, gateK9, gateK10, gateK11, gateK12 } from "./check-gates-b.mjs";
import { gateK13, gateK14 } from "./check-gates-c.mjs";
import { gateK15, gateK16 } from "./check-gates-d.mjs";

const ALL_GATES = [
  "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8",
  "K9", "K10", "K11", "K12", "K13", "K14", "K15", "K16",
];
const IMPLEMENTED = new Set(ALL_GATES);
const GATES = [
  ["K1", gateK1], ["K2", gateK2], ["K3", gateK3], ["K4", gateK4],
  ["K5", gateK5], ["K6", gateK6], ["K7", gateK7], ["K8", gateK8],
  ["K9", gateK9], ["K10", gateK10], ["K11", gateK11], ["K12", gateK12],
  ["K13", gateK13], ["K14", gateK14], ["K15", gateK15], ["K16", gateK16],
];

function usage() {
  return [
    "usage: check.mjs [-h] [--partial] [--gate GATE] project_dir",
    "",
    "vigen 项目文件机械校验（K1-K16 全量）",
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
    const missing = [...wanted].filter((gid) => !IMPLEMENTED.has(gid)).sort();
    if (missing.length) {
      console.log(`check.mjs 未移植门：${missing.join(", ")}（请用 check.py 跑全量）`);
      return 2;
    }
    selected = wanted;
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
