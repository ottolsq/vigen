# AGENTS.md — vigen

## 命令

```powershell
# 校验一个项目目录（只核对已有文档）
python scripts\check.py <project_dir> --partial
# 全量校验（要求 01-05 齐备）
python scripts\check.py <project_dir>
# 交付快照（输出到项目目录之外）
python scripts\export.py <project_dir> --out <dir>
# 自检：lint + 核心门夹具 + Node 委托边界（需 Git Bash）
& 'C:\Program Files\Git\bin\bash.exe' scripts/selftest.sh
# Node 侧：有 Python 时委托 check.py，无 Python 时跑子集
node scripts\check.mjs <project_dir> --partial
```

## 禁止事项

- 不要把同一条规则写进第二个文件：单一事实源，重复即缺陷（V2.8 起强制）
- 不要在未跑 `selftest.sh` 的情况下改 `scripts/check*.py`、`scripts/check*.mjs` 或 `batch-gates.json`
- 不要提交 `tests/`、`docs/superpowers/`、`study/`、`.claude/`、`.superpowers/`
- 不要在本 skill 里调用生成 API 或执行剪辑
- 不要在 Windows 上用 `WindowsApps\bash.exe` 跑 `selftest.sh`：那是 WSL 入口，不可用

## 环境事实

- Windows 11；Python 3.15、Node 26；Git Bash 位于 `C:\Program Files\Git\bin\bash.exe`
- 安装形态是复制 `SKILL.md`、`references/`、`assets/`、`scripts/` 到 agent 的 skill 目录
- 校验脚本只读项目 Markdown，不联网、不写文件

## 完成定义

- 改规则：同步 `SKILL.md` 的「规则归属表」，并跑 `selftest.sh`
- 改校验器：Python 与 Node 各跑一次；有 Python 时 Node 应当委托而不是跑子集
- 改模板：确认 00–06 的槽位仍与 `check.py` 的解析一致

## 文档指针

- 目标与范围：`docs/goal.md`
- 架构：`docs/architecture.md`
- 规则索引：`references/knowledge-index.md`
- 规则归属：`SKILL.md` 的「规则归属表」
