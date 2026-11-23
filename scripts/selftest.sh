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

# ---------- 3b. A20 打斗段诊断（V3.26：抽象频率 / 中景90°侧拍） ----------
mkdir -p "$TMP/k18bad"
cat > "$TMP/k18bad/01_方案与剧本.md" <<'EOF'
# t
## 整体方案
| 项 | 值 |
| --- | --- |
| 节拍制 | off |
EOF
cat > "$TMP/k18bad/04_视频提示词.md" <<'EOF'
# t
## 段落1（0-5s，生成5s）
```text
打斗段：是（交手账 R1）
动作锁：出拳→格挡→踢腿
道具锁：棍｜完整｜右手｜共1件｜入画
0.0s–2.0s
中景·侧面90°平视·跟拍跟镜，武松握着棍出拳，每秒攻击3次。
2.0s–5.0s
武松格挡后踢腿，棍仍在右手。
```
EOF
if python "$ROOT/scripts/check.py" "$TMP/k18bad" --gate A20 --partial > "$TMP/a20bad.txt" 2>&1; then
  bad "A20 打斗诊断 fixture 应失败" "$(tail -3 "$TMP/a20bad.txt")"
elif grep -q "抽象频率" "$TMP/a20bad.txt" && grep -q "90° 侧面正拍" "$TMP/a20bad.txt"; then
  ok
else
  bad "A20 打斗诊断未同时报两条" "$(tail -5 "$TMP/a20bad.txt")"
fi

# ---------- 3c. K5 冲击帧/黑白闪纳入闪白家族（V3.26-D） ----------
mkdir -p "$TMP/k5bad" "$TMP/k5good"
for d in k5bad k5good; do
  cat > "$TMP/$d/01_方案与剧本.md" <<'EOF'
# t
## 情节点清单
| # | 情节点 | 覆盖镜号 |
| --- | --- | --- |
| 1 | 【峰】反击 | 镜头1 |
EOF
done
cat > "$TMP/k5bad/04_视频提示词.md" <<'EOF'
# t
## 段落1（0-5s，生成5s）
```text
0.0s–2.0s
决定性一击命中，插入 1-2 帧冲击帧。
2.0s–5.0s
余波。
```
EOF
cat > "$TMP/k5good/04_视频提示词.md" <<'EOF'
# t
## 段落1（0-5s，生成5s）
```text
0.0s–2.0s
决定性一击命中，插入 1-2 帧冲击帧 ←峰值：情节点1。
2.0s–5.0s
余波。
```
EOF
if python "$ROOT/scripts/check.py" "$TMP/k5bad" --gate K5 --partial > "$TMP/k5bad.txt" 2>&1; then
  bad "K5 冲击帧无峰值标注应失败" "$(tail -3 "$TMP/k5bad.txt")"
elif grep -q "冲击帧" "$TMP/k5bad.txt"; then
  ok
else
  bad "K5 未把冲击帧纳入强调手段" "$(tail -5 "$TMP/k5bad.txt")"
fi
if python "$ROOT/scripts/check.py" "$TMP/k5good" --gate K5 --partial > "$TMP/k5good.txt" 2>&1; then
  ok
else
  bad "K5 冲击帧+峰值标注应通过" "$(tail -5 "$TMP/k5good.txt")"
fi
VIGEN_NODE_NO_DELEGATE=1 node "$ROOT/scripts/check.mjs" "$TMP/k5bad" --gate K5 --partial > "$TMP/k5bad-node.txt" 2>&1
if grep -q "冲击帧" "$TMP/k5bad-node.txt"; then
  ok
else
  bad "Node K5 未把冲击帧纳入强调手段" "$(tail -5 "$TMP/k5bad-node.txt")"
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

if python - "$ROOT/scripts" "$TMP" > "$TMP/export.txt" 2>&1 <<'PY'
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])
import export

parent = Path(sys.argv[2]) / "export-guard"
project = parent / "group" / "project"
project.mkdir(parents=True)
source = project / "01_fixture.md"
source.write_bytes(b"# Source fixture\n")
with patch.object(export.shutil, "rmtree", side_effect=AssertionError("export attempted recursive deletion")):
    for ancestor in (project.parent, parent):
        code = export.main(["export.py", str(project), "--out", str(ancestor), "--overwrite"])
        assert code == 2, f"expected rejection for {ancestor}, got {code}"
        assert source.read_bytes() == b"# Source fixture\n"

destination = project.parent / "delivery"
code = export.main(["export.py", str(project), "--out", str(destination)])
assert code == 0, f"expected sibling export to succeed, got {code}"
assert (destination / source.name).read_bytes() == source.read_bytes()
assert (destination / "manifest.json").is_file()
PY
then
  ok
else
  bad "export ancestor guard" "$(cat "$TMP/export.txt")"
fi

if python - "$ROOT/scripts" "$TMP" > "$TMP/export-episode.txt" 2>&1 <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
import export

base = Path(sys.argv[2]) / "export-episodes"
project = base / "project"
shared = "00_series.md"
by_episode = {
    episode: {f"{container}{episode}/01_script.md" for container in ("剧集/", "episodes/", "")}
    for episode in ("EP001", "EP002", "EP003")
}
all_paths = {shared}.union(*by_episode.values())
for relative in all_paths:
    source = project / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"# Series fixture\n")

for label, chosen in (("single", ["EP001"]), ("multiple", ["EP001", "EP003"]), ("all", [])):
    destination = base / label
    args = ["export.py", str(project), "--out", str(destination)]
    for episode in chosen:
        args.extend(["--episode", episode])
    code = export.main(args)
    assert code == 0, f"{label}: export returned {code}"
    expected = {shared}.union(*(by_episode[episode] for episode in chosen)) if chosen else all_paths
    copied = {file.relative_to(destination).as_posix() for file in destination.rglob("*.md")}
    assert copied == expected, f"{label}: unexpected {sorted(copied - expected)}, missing {sorted(expected - copied)}"
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert {item["path"] for item in manifest["files"]} == expected
PY
then
  ok
else
  bad "export episode filter" "$(cat "$TMP/export-episode.txt")"
fi

if python - "$ROOT/scripts" "$TMP" > "$TMP/export-overwrite.txt" 2>&1 <<'PY'
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])
import export

base = Path(sys.argv[2]).resolve() / "export-overwrite"
project = base / "project"
project.mkdir(parents=True)
source = project / "01_fixture.md"
source.write_bytes(b"# Initial fixture\n")

def run(out, *flags):
    return export.main(["export.py", str(project), "--out", str(out), *flags])

foreign = base / "foreign"
foreign.mkdir()
(foreign / "notes.md").write_bytes(b"# Keep these notes\n")
mixed = base / "mixed"
assert run(mixed) == 0
(mixed / "notes.md").write_bytes(b"# Keep these notes\n")
empty = base / "empty"
empty.mkdir()

with patch.object(export.shutil, "rmtree", side_effect=AssertionError("unexpected recursive deletion")):
    for unsafe in (foreign, mixed):
        assert run(unsafe, "--overwrite") == 2
        assert (unsafe / "notes.md").read_bytes() == b"# Keep these notes\n"
    assert run(empty, "--overwrite") == 0

snapshot = base / "snapshot"
assert run(snapshot) == 0
source.write_bytes(b"# Updated fixture\n")
remove = export.shutil.rmtree

def remove_snapshot(path):
    assert path == snapshot.resolve() and path.parent == base.resolve()
    remove(path)

with patch.object(export.shutil, "rmtree", side_effect=remove_snapshot):
    assert run(snapshot, "--overwrite") == 0
assert (snapshot / source.name).read_bytes() == source.read_bytes()
PY
then
  ok
else
  bad "export protects non-snapshot directories" "$(cat "$TMP/export-overwrite.txt")"
fi

mkdir -p "$TMP/offline-project"
cat > "$TMP/offline-project/01_方案与剧本.md" <<'EOF'
# 雨棚下的信
## 整体方案
| 项 | 值 |
| --- | --- |
| 叙事形态 | 电影化 |
| 节拍制 | on |
| 总时长 | 8s |
| 实际时间轴合计 | 8s |

## 分场剧本
### 第1场 · 站台雨棚 · 日
林青把湿信放到雨棚内侧的长椅上。
林青：信还没干。
雨水沿信纸折痕洇开，露出蓝色门牌号。

## 场次节拍表
| 场次 | 节拍号 | 类型 | 内容摘要 | 台词字数 | 估算秒 | 认领镜号 | 标记 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | B1 | 动作 | 将湿信放到长椅 | 0 | 2 | 镜S1 | 【钩子】 |
| 1 | B2 | 台词 | 提醒信纸仍湿 | 5 | 2 | 镜S1 | — |
| 1 | B3 | 动作 | 折痕洇开，出现门牌号 | 0 | 4 | 镜S2 | 【悬念】 |

## 时长预算
| 项 | 值 |
| --- | --- |
| 台词秒数 | 2s |
| 动作秒数 | 6s |
| 预计总时长 | 8s |

## 情节点清单
| # | 情节点 | 覆盖镜号 | 状态 |
| --- | --- | --- | --- |
| 1 | 林青在雨棚放下湿信并提醒 | 镜S1 | ✓ |
| 2 | 【峰】湿信折痕出现蓝色门牌号 | 镜S2 | ✓ |

## 分镜总览表
| 镜号 | 生成时长 | 运镜 | 运镜动机 | 认领节拍 |
| --- | --- | --- | --- | --- |
| S1 | 4s | 固定 | alignment(R7)：保留人物与长椅的相对位置 | B1,B2 |
| S2 | 4s | 短促推近 | pressure(R3)：让注意力落在信纸的蓝色门牌号上 | B3 |
EOF
cat > "$TMP/offline-project/02_锚定表.md" <<'EOF'
# 锚定表
## 目标模型
| 用途 | 模型 | 生成时长 |
| --- | --- | --- |
| 视频 | 离线测试模型 | 4s–12s |

## 角色锚定表
### 林青
| 项 | 值 |
| --- | --- |
| 锚定短语（中文） | 林青，齐耳黑发，灰蓝雨衣 |

## 色彩基调
| 角色 | 色号 | 落点 |
| --- | --- | --- |
| 环境底色 | #697A87 | 雨后站台 |
EOF
cat > "$TMP/offline-project/03_图片提示词.md" <<'EOF'
# 图片提示词
## 镜头S1 · 起点图
```
林青，齐耳黑发，灰蓝雨衣。雨棚内侧的木长椅在画面右下；窗外雨后站台落在 #697A87。平视中景，50mm，棚外漫射日光，椅面有细小水滴。
```
EOF
cat > "$TMP/offline-project/04_视频提示词.md" <<'EOF'
# 视频提示词
## 段落1（0–8s，生成 8s）
```
SCENE CONTEXT
雨后站台，雨棚内从人物到长椅的距离约半米。林青，齐耳黑发，灰蓝雨衣。
ACTIVE REFERENCES
无；本段使用文字锚定。
CONTINUITY RULE
只有一封湿信，始终留在长椅内侧。
FORMAT
8 秒，横画幅，普通话，无字幕。
色调：#697A87 落在雨后站台。
CAMERA / EDITING
从人物中景硬切到信纸特写。
0.0s–4.0s｜镜头S1｜放信
平视固定机位，50mm，雨棚支架随风微振。林青将湿信放在长椅内侧，说：“信还没干。”信纸贴在椅面上。
4.0s–8.0s｜镜头S2｜墨迹现形
俯拍特写，85mm。雨滴在椅面形成小圈涟漪，蓝色墨迹沿折痕散开。短促推近，停在蓝色门牌号上。←峰值：情节点2
ENDING FRAME
蓝色门牌号位于画面中央，信纸仍贴着椅面。
PERFORMANCE LOCK
林青说完即停，不再补充。
FACE LOCK
保留林青的发型和面部轮廓。
AUDIO
只留林青的单句对白。没有第二种声音，也没有任何持续声底。
LIGHTING
雨棚外的漫射日光保持不变。
NO
不要字幕，不新增人物。
```
EOF
cat > "$TMP/offline-project/05_语音台词表.md" <<'EOF'
# 语音台词表
| # | 镜号/段落 | 角色 | 台词原文 | 朗读时长 | 所在镜头时长 |
| --- | --- | --- | --- | --- | --- |
| 1 | 镜S1 / 段1 | 林青 | 信还没干。 | 2s | 4s |
EOF

if python "$ROOT/scripts/check.py" "$TMP/offline-project" > "$TMP/offline.txt" 2>&1 &&
   python "$ROOT/scripts/export.py" "$TMP/offline-project" --out "$TMP/offline-delivery" --no-media >> "$TMP/offline.txt" 2>&1 &&
   python - "$TMP/offline-project" "$TMP/offline-delivery" >> "$TMP/offline.txt" 2>&1 <<'PY'
import hashlib
import json
import sys
from pathlib import Path

project, delivery = map(Path, sys.argv[1:])
source_names = {path.name for path in project.glob("*.md")}
expected = source_names | {"manifest.json", "checksums.sha256"}
assert len(source_names) == 5
assert {path.name for path in delivery.iterdir()} == expected
manifest = json.loads((delivery / "manifest.json").read_text(encoding="utf-8"))
assert manifest["asserts_approval"] is False
assert {entry["path"] for entry in manifest["files"]} == source_names
checksums = set((delivery / "checksums.sha256").read_text(encoding="utf-8").splitlines())
expected_checksums = set()
for entry in manifest["files"]:
    name = entry["path"]
    data = (delivery / name).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    assert data == (project / name).read_bytes()
    assert entry["sha256"] == digest and entry["size"] == len(data)
    expected_checksums.add(f"{digest}  {name}")
assert checksums == expected_checksums
PY
then
  ok
else
  bad "offline full-project check and export" "$(cat "$TMP/offline.txt")"
fi

# ---------- K8/K12：语言标签不改变提示词覆盖 ----------
mkdir -p "$TMP/fence-ok" "$TMP/fence-bad" "$TMP/fence-open" "$TMP/fence-single"
fence_doc='04_视频提示词.md'
sed '0,/^```$/s//```text/' "$TMP/offline-project/$fence_doc" > "$TMP/fence-ok/$fence_doc"
cp "$TMP/offline-project/$fence_doc" "$TMP/fence-bad/$fence_doc"
printf '\n## 段落2（8–16s，生成 8s）\n' >> "$TMP/fence-bad/$fence_doc"
sed -n '/^SCENE CONTEXT$/,$p' "$TMP/offline-project/$fence_doc" |
  sed '/^ENDING FRAME$/d;s/林青将湿信/她将湿信/' |
  { printf '%s\n' '```text'; cat; } >> "$TMP/fence-bad/$fence_doc"
sed '$d' "$TMP/fence-ok/$fence_doc" > "$TMP/fence-open/$fence_doc"
printf '%s\n' '# 分镜' '骨架 B 理由：一镜到底张力' > "$TMP/fence-single/01_方案与剧本.md"
printf '%s\n' '## 镜头S1（生成 8s）' '```text' '林青将湿信放到长椅上。' '```' > "$TMP/fence-single/$fence_doc"

for runtime in python node; do
  if [ "$runtime" = python ]; then
    checker=(python "$ROOT/scripts/check.py")
  else
    checker=(env VIGEN_NODE_NO_DELEGATE=1 node "$ROOT/scripts/check.mjs")
  fi
  if "${checker[@]}" "$TMP/fence-ok" --gate K8,K12 --partial > "$TMP/fence-ok.txt" 2>&1; then
    ok
  else
    bad "$runtime: valid tagged fence" "$(cat "$TMP/fence-ok.txt")"
  fi
  "${checker[@]}" "$TMP/fence-bad" --gate K8,K12 --partial > "$TMP/fence-bad.txt" 2>&1
  rc=$?
  if [ "$rc" -eq 1 ] && grep -q '\[K8\].*缺节：ENDING FRAME' "$TMP/fence-bad.txt" &&
     grep -q '\[K12\].*人物指代用了「她」' "$TMP/fence-bad.txt"; then
    ok
  else
    bad "$runtime: tagged block must not disappear behind a valid block (exit $rc)" "$(cat "$TMP/fence-bad.txt")"
  fi
  "${checker[@]}" "$TMP/fence-open" --gate K8,K12 --partial > "$TMP/fence-open.txt" 2>&1
  rc=$?
  if [ "$rc" -eq 1 ] && grep -q '\[K8\].*围栏未闭合' "$TMP/fence-open.txt" &&
     grep -q '\[K12\].*围栏未闭合' "$TMP/fence-open.txt"; then
    ok
  else
    bad "$runtime: unclosed prompt fence (exit $rc)" "$(cat "$TMP/fence-open.txt")"
  fi
  if "${checker[@]}" "$TMP/fence-single" --gate K8,K12 --partial > "$TMP/fence-single.txt" 2>&1; then
    ok
  else
    bad "$runtime: skeleton B requires no skeleton A" "$(cat "$TMP/fence-single.txt")"
  fi
done

# ---------- K9：剧本阶段允许先登记情节点，进入分镜后才核对覆盖 ----------
plot_doc='01_方案与剧本.md'
for fixture in script-only plot-draft story-empty plot-uncovered prompts-only plot-covered; do
  mkdir -p "$TMP/k9-$fixture"
  cat > "$TMP/k9-$fixture/$plot_doc" <<'EOF'
# 剧本
## 场次节拍表
| 节拍号 | 内容摘要 | 认领镜号 |
| --- | --- | --- |
| B1 | 林青把信放到长椅上 | |
EOF
done
for fixture in plot-draft story-empty plot-uncovered plot-covered; do
  cat >> "$TMP/k9-$fixture/$plot_doc" <<'EOF'

## 情节点清单
| 情节点 | 覆盖镜号 | 状态 |
| --- | --- | --- |
EOF
  if [ "$fixture" = plot-covered ]; then
    printf '%s\n' '| 林青交出信 | 镜S1 | ✓ |' >> "$TMP/k9-$fixture/$plot_doc"
  else
    printf '%s\n' '| 林青交出信 | | 待定稿 |' >> "$TMP/k9-$fixture/$plot_doc"
  fi
done
for fixture in story-empty plot-uncovered plot-covered; do
  printf '%s\n' '' '## 分镜总览表' '| 镜号 | 运镜 |' '| --- | --- |' >> "$TMP/k9-$fixture/$plot_doc"
  if [ "$fixture" != story-empty ]; then
    printf '%s\n' '| S1 | 固定 |' >> "$TMP/k9-$fixture/$plot_doc"
  fi
done
printf '# 图片提示词\n' > "$TMP/k9-prompts-only/03_图片提示词.md"

for runtime in python node; do
  if [ "$runtime" = python ]; then
    checker=(python "$ROOT/scripts/check.py")
  else
    checker=(env VIGEN_NODE_NO_DELEGATE=1 node "$ROOT/scripts/check.mjs")
  fi
  for fixture in script-only plot-draft plot-covered; do
    if "${checker[@]}" "$TMP/k9-$fixture" --gate K9 --partial > "$TMP/k9.txt" 2>&1; then
      ok
    else
      bad "$runtime: K9 $fixture should pass" "$(cat "$TMP/k9.txt")"
    fi
  done
  for fixture in story-empty plot-uncovered prompts-only plot-draft; do
    mode=(--partial)
    diagnostic='覆盖镜号列为空'
    if [ "$fixture" = prompts-only ]; then diagnostic='未解析到情节点清单'; fi
    if [ "$fixture" = plot-draft ]; then mode=(); fi
    "${checker[@]}" "$TMP/k9-$fixture" --gate K9 "${mode[@]}" > "$TMP/k9.txt" 2>&1
    rc=$?
    if [ "$rc" -eq 1 ] && grep -q "\[K9\].*$diagnostic" "$TMP/k9.txt"; then
      ok
    else
      bad "$runtime: K9 $fixture should preserve coverage check (exit $rc)" "$(cat "$TMP/k9.txt")"
    fi
  done
done

# ---------- K14：闭合短片收束、续接悬念、旧稿兼容 ----------
for fixture in closed closed-early closed-no-ending continue continue-early legacy legacy-no-ending; do
  mkdir -p "$TMP/k14-$fixture"
  mode=''
  middle='—'
  ending='【余韵】'
  case "$fixture" in
    closed*) mode='| 结尾模式 | 闭合 |' ;;
    continue*) mode='| 结尾模式 | 续接 |' ;;
  esac
  case "$fixture" in
    closed-early) middle='【收束】'; ending='—' ;;
    closed-no-ending) ending='—' ;;
    continue-early) middle='【悬念】'; ending='—' ;;
    legacy) ending='【悬念】' ;;
  esac
  cat > "$TMP/k14-$fixture/01_方案与剧本.md" <<EOF
# 短片
## 整体方案
| 项 | 值 |
| --- | --- |
| 节拍制 | on |
| 总时长 | 9s |
$mode

## 场次节拍表
| 节拍号 | 类型 | 台词字数 | 估算秒 | 认领镜号 | 标记 |
| --- | --- | --- | --- | --- | --- |
| B1 | 动作 | 0 | 3 | | 【钩子】 |
| B2 | 动作 | 0 | 3 | | $middle |
| B3 | 动作 | 0 | 3 | | $ending |

## 时长预算
| 项 | 值 |
| --- | --- |
| 预计总时长 | 9s |
EOF
done

for runtime in python node; do
  if [ "$runtime" = python ]; then
    checker=(python "$ROOT/scripts/check.py")
  else
    checker=(env VIGEN_NODE_NO_DELEGATE=1 node "$ROOT/scripts/check.mjs")
  fi
  for fixture in closed closed-early closed-no-ending continue continue-early legacy legacy-no-ending; do
    expected=''
    case "$fixture" in
      closed-early) expected='须在末拍' ;;
      closed-no-ending) expected='须恰好一个【收束】或【余韵】' ;;
      continue|legacy-no-ending) expected='须恰好一个【悬念】' ;;
      continue-early) expected='须在末拍' ;;
    esac
    "${checker[@]}" "$TMP/k14-$fixture" --gate K14 --partial > "$TMP/k14.txt" 2>&1
    rc=$?
    if { [ -z "$expected" ] && [ "$rc" -eq 0 ]; } ||
       { [ -n "$expected" ] && [ "$rc" -eq 1 ] && grep -q "\[K14\].*$expected" "$TMP/k14.txt"; }; then
      ok
    else
      bad "$runtime: K14 $fixture (exit $rc)" "$(cat "$TMP/k14.txt")"
    fi
  done
done

# ---------- K1/K17：Seedance 原生台词、旧引号与静默段 ----------
dialogue_fixtures=(native changed quoted metadata metadata-changed single-quoted single-quoted-changed silent)
for fixture in "${dialogue_fixtures[@]}"; do
  mkdir -p "$TMP/dialogue-$fixture"
  cat > "$TMP/dialogue-$fixture/01_方案与剧本.md" <<'EOF'
# 剧本
## 人物表
- 周姐：值班员

## 分场剧本
周姐：空袋搁这儿就行。
周姐：
"她刚才说：「搁这儿」。"
EOF
  case "$fixture" in
    native) line='周姐（中文，平声）轻扣「空袋」，以中文同期声说{空袋搁这儿就行。} 随后低声说道：{她刚才说：「搁这儿」。}' ;;
    changed) line='道具入画 → 周姐（中文，平声）以中文同期声说{空袋拿回去吧。}' ;;
    quoted) line='周姐（平声）：「空袋搁这儿就行。」' ;;
    metadata) line='周姐（中文，平声）：{她刚才说：「搁这儿」。}' ;;
    metadata-changed) line='周姐说{空袋搁这儿就行。} 随后，周姐（中文，平声）：{空袋拿回去吧。}' ;;
    single-quoted) line="周姐（中文，平声）说:'空袋搁这儿就行。'" ;;
    single-quoted-changed) line="周姐说{空袋搁这儿就行。} 随后，周姐（中文，平声）说:'空袋拿回去吧。'" ;;
    silent) line='用 {{ref 1}} 锁定木柜；{道具}留在原位；转写模板示例说{{ref 2}}。周姐（中文，平声）：{{ref 3}}。构图（近景）：{道具}。' ;;
  esac
  cat > "$TMP/dialogue-$fixture/04_视频提示词.md" <<EOF
# 视频提示词
## 段1
CONTINUITY RULE
参照原样说{这是技术段的示例。}
0s–8s｜镜头S1 $line
EOF
done

for runtime in python node; do
  if [ "$runtime" = python ]; then
    checker=(python "$ROOT/scripts/check.py")
  else
    checker=(env VIGEN_NODE_NO_DELEGATE=1 node "$ROOT/scripts/check.mjs")
  fi
  for fixture in "${dialogue_fixtures[@]}"; do
    gates=K1,K17
    if [ "$fixture" = silent ]; then gates=K17; fi
    "${checker[@]}" "$TMP/dialogue-$fixture" --gate "$gates" --partial > "$TMP/dialogue.txt" 2>&1
    rc=$?
    if { [[ "$fixture" =~ ^(native|quoted|metadata|single-quoted)$ ]] && [ "$rc" -eq 0 ] && ! grep -q '\[K[0-9]' "$TMP/dialogue.txt"; } ||
       { [[ "$fixture" == *changed ]] && [ "$rc" -eq 1 ] && grep -q '\[K1\].*台词与01定稿不一致.*空袋拿回去吧' "$TMP/dialogue.txt" && ! grep -q '\[K17\]' "$TMP/dialogue.txt"; } ||
       { [ "$fixture" = silent ] && [ "$rc" -eq 1 ] && grep -q '\[K17\].*无台词段缺' "$TMP/dialogue.txt"; }; then
      ok
    else
      bad "$runtime: K1/K17 $fixture (exit $rc)" "$(cat "$TMP/dialogue.txt")"
    fi
  done
done

echo "selftest: $PASS 通过 / $FAIL 失败"
[ "$FAIL" -eq 0 ]
