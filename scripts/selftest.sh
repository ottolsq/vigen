#!/usr/bin/env bash
# vigen 自检入口（V3.24）：文档 lint + 核心门 fixture + Node 委托/子集边界。
# 用法：bash scripts/selftest.sh   （在仓库根目录或任意目录运行均可）
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PASS=0
FAIL=0

ok() { PASS=$((PASS + 1)); }
bad() { FAIL=$((FAIL + 1)); echo "FAIL: $1"; shift; for line in "$@"; do echo "  $line"; done; }

# ---------- 1. 文档 lint ----------
if python -I "$ROOT/scripts/lint_docs.py" > "$TMP/lint.txt" 2>&1; then
  ok
else
  bad "lint_docs" "$(cat "$TMP/lint.txt")"
fi

# ---------- 2. fixture：A19 正例 + K14 正例 ----------
mkdir -p "$TMP/fix"
cat > "$TMP/fix/01_方案与剧本.md" <<'EOF'
# t
## 整体方案
| 项 | 值 |
| --- | --- |
| 总时长 | 31.5s（预算口径） |
| 时长模式 | 上限档（≤31.5s） |
| 实际时间轴合计 | 30s |
| 时长容差 | ±15% |
| 节拍制 | on |

## 场次节拍表
| 场次 | 节拍号 | 类型 | 内容摘要 | 台词字数 | 估算秒 | 认领镜号 | 标记 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | B1 | 动作 | x | 0 | 10 | 镜S1 | 【钩子】 |
| 1 | B2 | 动作 | y | 0 | 10 | 镜S1 | — |
| 1 | B3 | 动作 | z | 0 | 10 | 镜S1 | 【悬念】 |

## 分镜总览表
| 镜号 | 运镜 | 生成时长 | 内容摘要 | 认领节拍 |
| --- | --- | --- | --- | --- |
| S1 | 固定 | 35s | x | B1-B3 |

## 时长预算
| 项 | 值 |
| --- | --- |
| 预计总时长 | 30s |
EOF
cat > "$TMP/fix/02_锚定表.md" <<'EOF'
# t
## 场景锚定表
### 山道（SC01）
#### 母版事实清单（SC01-9x16）
| 事实 | 冻结值（逐字） | 允许变体（ / 分隔） | 适用文件 | 母版事实标记 |
| --- | --- | --- | --- | --- |
| 机位高度 | 约7米高 | 7m / about 7 meters up | 04 | [MASTER:SC01-9x16] |
EOF
cat > "$TMP/fix/04_视频提示词.md" <<'EOF'
# t
## 段落1（0-10s，生成10s）
```text
母版事实标记：[MASTER:SC01-9x16]
机位约7米高。
```
EOF
if python "$ROOT/scripts/check.py" "$TMP/fix" --gate K14,A19 --partial > "$TMP/gate.txt" 2>&1; then
  ok
else
  bad "K14/A19 fixture" "$(tail -3 "$TMP/gate.txt")"
fi

# ---------- 3. A20（原 K18）fixture ----------
mkdir -p "$TMP/k18"
cat > "$TMP/k18/01_方案与剧本.md" <<'EOF'
# t
## 整体方案
| 项 | 值 |
| --- | --- |
| 节拍制 | off |
EOF
cat > "$TMP/k18/04_视频提示词.md" <<'EOF'
# t
## 段落1（0-5s，生成5s）
```text
动作锁：握着梢棒→挥动梢棒→收起梢棒
道具锁：梢棒｜完整｜右手｜共1件｜入画
0.0s–1.0s
武松握着梢棒。
1.0s–3.0s
武松挥动梢棒。
3.0s–5.0s
武松收起梢棒。
```
EOF
if python "$ROOT/scripts/check.py" "$TMP/k18" --gate A20 --partial > "$TMP/a20.txt" 2>&1; then
  ok
else
  bad "A20 fixture" "$(tail -3 "$TMP/a20.txt")"
fi

# ---------- 4. Node 子集边界（强制本地） ----------
VIGEN_NODE_NO_DELEGATE=1 node "$ROOT/scripts/check.mjs" "$TMP/k18" --gate A20 --partial > "$TMP/node-a20.txt" 2>&1
if [ $? -eq 2 ] && grep -q "Node 子集不支持" "$TMP/node-a20.txt"; then
  ok
else
  bad "Node 子集应拒绝 A20" "$(cat "$TMP/node-a20.txt")"
fi

# ---------- 5. 委托模式与 Python 一致 ----------
if python "$ROOT/scripts/check.py" "$TMP/fix" --gate K14,A19 --partial > "$TMP/py.txt" 2>&1; then :; fi
if node "$ROOT/scripts/check.mjs" "$TMP/fix" --gate K14,A19 --partial > "$TMP/nd.txt" 2>&1; then :; fi
if diff --strip-trailing-cr "$TMP/py.txt" "$TMP/nd.txt" > /dev/null; then
  ok
else
  bad "委托模式与 Python 输出不一致" "$(diff --strip-trailing-cr "$TMP/py.txt" "$TMP/nd.txt" | head -5)"
fi

# ---------- 6. batch-list ----------
if python "$ROOT/scripts/check.py" --batch-list | grep -q "milestone"; then
  ok
else
  bad "batch-list 缺 milestone"
fi

echo "selftest: $PASS 通过 / $FAIL 失败"
[ "$FAIL" -eq 0 ]
