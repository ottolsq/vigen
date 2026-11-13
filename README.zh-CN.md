# vigen — AI 视频制作辅助 Skill

[English](README.md) | **简体中文**

把一句创意或一份剧本变成一套完整的、可直接复制到生成工具使用的视频制作方案。面向零影视基础的用户：分镜、运镜、转场、光影、提示词工程全部自动补全，只需回答需求问卷并在三个确认点（GATE0 / GATE1.5 / GATE1）做决定。

> **本 README 只做介绍与导航，不重述规则细节**——规则全文的唯一权威在各 references 文件里（下方目录结构列明）。

## 它解决什么问题

AI 视频制作的痛点不在"没有工具"，而在"不知道怎么指挥工具"。本 skill 解决以下问题：

| 痛点 | 解法在哪 |
| --- | --- |
| 图片有 AI 油腻感、单一死板 | "描述这张照片怎么拍出来的" + 画面张力四法 → [realism.md](references/realism.md) |
| 分段生成色调漂移 | 全片色彩基调（3-5 个十六进制色号按面积分配，色号+落点进每条提示词）→ [styles.md](references/styles.md) |
| 提示词不精准、模型听不懂 | 语义绑定三层法 + 正向引导>负面约束（分端裁决）→ [prompt-rules.md](references/prompt-rules.md) / [knowledge-index.md](references/knowledge-index.md) |
| 复杂动作生成不出来 | 反先验动作先用首帧锁姿势，视频只写后续运动 → [prompt-rules.md](references/prompt-rules.md) |
| 人物/场景/道具跨图不一致 | 四层锚定逐字复用 + 参考图六条硬标准 + 头身分离 + 互挂参考 + **同一对象唯一权威参考** + **服装锁定三档** + **事实继承原则** → [consistency.md](references/consistency.md) |
| 道具状态混乱、前后镜头背着/没背 | 道具六条判定 + **多状态合图生成后裁切单张** + 组合道具拆单张 + **逐镜位置账** → [prompt-rules.md](references/prompt-rules.md) / [consistency.md](references/consistency.md) |
| 多张参考图互相打架 | 同一对象只留一张权威图，其余显式降级或裁掉该对象 → [consistency.md](references/consistency.md) |
| 复杂场景一段视频装不下 | 拆成多个骨架 B 单镜片段，剪辑端拼接 → [prompt-rules.md](references/prompt-rules.md) 骨架选择器 |
| 动作违反物理常识 | 动作三段式 + ENDING FRAME + 秒级时序 → [prompt-rules.md](references/prompt-rules.md) |
| 跨片段音色漂移 | 按模型选语音路线（happyhorse 自带语音 / H3 音色自提取 / cosyvoice 对轨）+ 发声描述公式 → [consistency.md](references/consistency.md) |
| 一段视频只有一个镜头 | 骨架 A 多镜头段落公式为默认 → [prompt-rules.md](references/prompt-rules.md) |
| 运镜单一、转场呆板 | 运镜功能决策表 R1-R7 + 40 运镜 + 8 生成端转场/5 剪辑端转场 + 峰值与强调手段（稀缺品）→ [cinematography.md](references/cinematography.md) |
| 长剧遗忘细节 | 00_剧情状态.md 每集强制更新 + 尾帧续接 → [consistency.md](references/consistency.md) |
| 剧情被擅自删改 | 情节点清单逐点登记，100% 覆盖校验 → [screenwriting-craft.md](references/screenwriting-craft.md) |
| 做红果/抖音付费短剧，不知道排多少集、墙卡在哪 | 立项单（档位/集数/赛道/情绪契约/单元链/付费墙）+ 前三集节拍卡 → [short-drama-market.md](references/short-drama-market.md) |
| 竖屏短剧台词观众听不懂、节奏拖 | 形态 B 覆盖规则（同轮直给/15 秒四拍/集内结算/独白配额）→ [screenwriting-craft.md](references/screenwriting-craft.md) 一·九 |
| 短剧剧本踩内容红线 | 备案分类 + 11 条红线 + 敏感词替换 → [content-compliance.md](references/content-compliance.md) |
| 生成资产浪费钱 | 资产引用矩阵先行，零引用不生成；**单次入画道具不建参考图** → [prompt-rules.md](references/prompt-rules.md) 一节4 |
| 生成失败不知道怎么救 | 结构判定前置的回退阶梯 → [SKILL.md](SKILL.md) |
| 提示词被内容审核拦截 | 反应式降级：已登记模式前置复用 + 拦截后降级阶梯（措辞→构图→拆独角→二分定位）→ [content-safety.md](references/content-safety.md) |
| 负面词加了没效果/越加越糟 | 先查是否与正向冲突（正向要A又禁A / 负面引入正向未要求的对象）→ [knowledge-index.md](references/knowledge-index.md) 负面词裁决 |
| 技能特效/法阵/剑气/粒子爆发 | Niagra 三层光效（emissive/分层/高光锚定）+ 法师/射手/剑修三类形态 + 动态轨迹 → [vfx-effects.md](references/vfx-effects.md) |
| 中途要加镜头/改情节 | 活剧本修订（局部重排 + 稳定镜号），不重走全流程 → [SKILL.md](SKILL.md) |
| 人物跨段瞬移/换位/消失 | 段走位账 + 04【走位总谱】+ 连续性铁律（每角色位置/坐站走/朝向）→ [consistency.md](references/consistency.md) |
| 切点生硬、动作接不上 | 每个切点写动作桥（上镜结尾→本镜开头）→ [templates.md](assets/templates.md) 04 |
| 群演每镜换一批人、服装乱色 | 群像锚定表 + 群像参考图（只锁服装形象，避开主角主色）→ [templates.md](assets/templates.md) 02/03 |
| 负面词想用但不知道写哪 | 负面提示词两段式（全片通用+本段连续性，模型负向字段支持时）→ [templates-execution.md](assets/templates-execution.md) 七 |
| 图片提示词越写越长、画面越来越死板 | 图片约束预算两档（技术参考图全量 / 叙事图精简意图版）→ [prompt-rules.md](references/prompt-rules.md) 0.12 |
| 每段视频都要先出一张首帧图，成本高 | Seedance 项目免 L1 情景图（详细提示词+资产参考图直出；H3/happyhorse 维持必出）→ [prompt-rules.md](references/prompt-rules.md) 一节3 |
| 提示词结构对但密度不够、镜头像大纲 | 逐镜动线+背景动作线 + 每镜焦段 mm + 四组负面词库 + 光影演变线 → [templates.md](assets/templates.md) 04 |

## 工作流

```
GATE0 需求问卷+对齐
  → 阶段1a 剧本创作 ─GATE1.5 剧本定稿─→ 阶段1b 分镜+锚定 ─GATE1 确认─
  → 阶段2-4 图片提示词（先资产矩阵）→ 阶段5 视频提示词 + 台词表
  → 阶段6 剪辑清单 →（系列：更新 00_剧情状态）
```

三个停点：**GATE0**（问卷+需求对齐）、**GATE1.5**（剧本定稿——未定稿绝不进分镜）、**GATE1**（锚定确认）。定稿锁的是故事骨架与情节点清单，分镜表是活文档（后续增删镜头走活剧本修订的局部重排）。

**执行契约（V3.16）**：每批写 03/04/05 前重读 02/01/05；每段填「批次生产卡」；每批在 01 追加「批次校验记录」（A1-A16 + 证据）；可选 `--gate A17` 机检留痕、`--gate A18` 机检图片预算；没有记录不得说"已完成"。

**项目结构**：单视频 `<项目名>/01-06`；系列 `<系列名>/00_剧情状态.md + ep01/…ep02/…`。

每个项目产出的文件（Markdown 即"创作真相"）：

| 文件 | 内容 |
| --- | --- |
| `00_剧情状态.md` | 系列专用：**立项单（竖屏短剧）** + 剧情摘要/角色状态/道具状态/上集尾帧/伏笔——每集完成后强制更新 |
| `01_方案与剧本.md` | GATE0 对齐记录 + **立项单（单视频）** + **短剧集结构（结算/中段小钩/断章）** + GATE1.5 定稿记录 + 分场剧本 + 情节点清单 + 分镜总览表（活文档，稳定镜号）+ **批次生产卡 + 批次校验记录（V3.16 执行契约）** + 变更记录 |
| `02_锚定表.md` | 目标模型 / 色彩基调 / 角色 / 场景（LOCATION MAP+四视图）/ 道具 / 风格圣经 |
| `03_图片提示词.md` | 资产引用矩阵 + 人物/道具/场景/情景参考图（L1-L4 分级出图）+ 内容安全措辞规范（高危题材项目） |
| `04_视频提示词.md` | 默认骨架 A 多镜头段落公式 / 骨架 B 单镜头（特例）；时长硬校验+尾帧续接 |
| `05_语音台词表.md` | 台词总账 + 发声描述公式（前置身份两段+六参数）+ 音色参考资产 + SPEAKER LOCK |
| `06_剪辑清单.md` | 拼接/转场实现/转场音频处理/BGM/调色/导出 |

## 模型能力与提示词策略（2026-11）

| 模型 | 生成方式 | 段首情景图（L1） | 视频/音频参考 | 现状 |
| --- | --- | --- | --- | --- |
| **Seedance / 即梦（Seedance 型号）** | 参考生视频（多模态） | **默认可不出** | 有（视频/音色） | 当前文本遵从度最高；3 分钟案例 8 段零情景图 |
| **MiniMax-H3** | t2va / 首帧 / 首尾帧 / Ref2VA | **必出**，且**跨环境切点也要** | 有（图 ≤9、视频 ≤3、音频 ≤3、总数 ≤12） | 无情景图画面质感明显下降；用多帧对齐或拆段 |
| **happyhorse-1.1** | t2v / i2v / r2v（仅图片） | **必出** | 无 | 无多帧对齐；跨环境切镜拆段 |

### Seedance：情景图不是必需

实测 Seedance 的参考生视频 + 详细视频提示词 + 人物/场景/道具参考图即可直出，段首情景图默认可不出。案例《长安如昼》3 分钟、8 个视频段，全程没有生成情景图；它的"首帧"是上一段的尾帧抽帧，不是新生成的图。注意：**L2 反先验/接触类动作的锁姿图仍然必出**——文字锁不住姿势，这一点与模型文本遵从度无关。

### H3：情景图是画质的一部分

H3 不是"只保留段首一张首帧图"就够了：段内切镜一旦环境/光线/空间布局明显变化，缺少对应情景图时画面质感会骤降。做法：

1. 段首 L1 必出；
2. 段内**跨环境切点**出切点帧，按「H3 多帧对齐配方」用 `Picture k` 钉到秒；
3. 供应商不支持多帧对齐 → 把跨环境切镜**拆成独立生成段**（每段一个环境），让该镜成为新段 L1；
4. 同环境同轴线的景别/正反打切镜可不加。happyhorse 无多帧对齐能力，跨环境切镜同样拆段。

### 让 H3 逼近 Seedance 的提示词优化

H3 与 Seedance 在参考生视频能力和文本遵从度上有代差，**能逼近，不能等同**。把差距压到最小，靠的是以下八条：

1. **开镜信息写全**：不挂首帧时，段首镜的机位/景别/构图/光线/主体位置/焦段 mm 必须由 04 正文写清楚——Seedance 能靠文本直接起画面，H3 需要文字把"第一帧长什么样"说明白。
2. **走位总谱升级为逐镜动线 + 背景动作线**：H3 段内切镜多，人物位置和背景动作不连续会放大"换了一批人"的感觉。
3. **每个切点写动作桥**：上镜最后一拍的动作/视线/声音 → 本镜第一拍，至少承接一项。
4. **光影演变线**：起点光 → 中段变化 → 收束光，防切镜后光色跳变。
5. **跨环境切镜出切点情景图**：能多帧对齐就钉到秒，不能就拆段。
6. **四组负面词库**：画质/材质、背景动态/运镜、连续性、音乐/字幕；模型有独立负向字段时按"全片通用 + 本段连续性"两段式写入。
7. **每镜写密度**：焦段 mm、运镜 M 编号、动作三段式/秒级时序、声音演变——案例的"厚"来自逐镜信息完整，不是形容词堆叠。
8. **不压缩提示词结构**：H3 的差距不是靠删字解决的；该写的调度、光照、连续性一条都不能少。

> 结论：优化后的 H3 可以明显接近 Seedance 的完成度，但不会变成同一个模型。目标是缩小差距，不是宣称同质。

## 目录结构（规则全文的唯一权威）

```
├── SKILL.md              # GATE0 问卷（含叙事形态/平台）+ 工作流 + 意图路由（含活剧本修订）+ 23 条硬规则（要点+指针，含 K1-K17 check.py 门 + A16-A18 opt-in 审计 + 执行契约）+ 回退阶梯 + 停点收缩（真分叉才停）+ E2 挂图不阻塞 + 效率纪律
├── references/
│   ├── screenwriting-craft.md # 剧本创作：7 大漏洞自检 + 台词行动理论 + 场景发动机与升级六问 + 当集兑现 + 反对七式 + 误会四判据 + 钩子悬念纪律 + 故事三层分离 + GATE1.5 + 故事板四格 + 一·九 形态 B（竖屏短剧）
│   ├── short-drama-market.md # 平台短剧立项与排集：档位/集数 + 40 赛道 + 流派/情绪契约/单元链 + 六档证据×反驳 + 付费墙 + 前三集节拍卡（仅竖屏短剧项目读）
│   ├── content-compliance.md # 内容合规：备案分类 + 11 条红线 + 暴力/迷信专项 + 敏感词替换（仅竖屏短剧项目读）
│   ├── prompt-rules.md   # 四大底层认知 + 0.7 可生成性前置门 + 0.8 技术动作语义锚 + 0.9 朝向三要素 + 0.10 方向锚图/目标状态图 + 0.12 图片约束预算 + 尺度三件套/入画即登记 + 混音工程语言 + 图片/视频骨架 A·B + 道具六条判定 + L1-L4 分级 + 发声描述公式 + 校验（A1-A16 + 13 抽查项 + K17 + A17/A18 opt-in）
│   ├── models.md         # 模型能力档案 + 生成路径判定 + 换模型指引
│   ├── cinematography.md # 运镜功能决策表（R1-R7）+ 动机五类词表 + 40 运镜 + 8 生成端/5 剪辑端转场 + 机位语义 + 对白场切法 + 工作景别 + 光影选型库 + 峰值与强调手段 + 单镜时长/节奏 + 竖屏构图安全区 + 7 类场景镜头序列
│   ├── realism.md        # 去AI味 + 张力四法 + 表面两档与塑形约束 + 三·七 解剖学约束 + 朝代纪律 + 文字物理化
│   ├── styles.md         # 16 风格库（含 Pixar 3D 动画电影）+ 色彩基调色板 + 风格提取解梦卡 + 项目风格隔离
│   ├── consistency.md    # 〇 锁定清单 + 服装默认专属图 + 场景持续物/锁定三件套 + 身体-器械空间账 + 段走位账/群像锚定 + 错误示范 ref 处理 + 四层锚定 + 参考图六条/头身分离 + 角色路由/基准参考法 + 最小参考集 + 音色自提取 + 系列记忆 + 失效传播
│   ├── content-safety.md # 内容安全反应式降级：措辞级解法库 + 构图级模式表 + 降级阶梯 + 显式否定旧设定 + 失败分类对策
│   ├── knowledge-index.md# 扩展知识库路由表（命中才读）+ 负面词效力分端裁决
│   ├── examples.md       # 完整示例
│   ├── action-combat.md  # [扩展] 武打动作引擎：交手账 + 打击呈现三件套 + 围攻方位纪律 + 三拍容器 + 打斗接触专条
│   ├── vfx-effects.md    # [扩展] 技能特效：Niagra 三层光效 + 法师/射手/剑修三类形态 + 动态轨迹 + 失败模式负面清单
│   ├── cinema-grade-params.md # [扩展] 电影级参数块 + 国漫四视图
│   ├── expressions.md / director-styles.md / extended-views.md / emotion-craft.md / ugc-realism.md / anime-to-real.md  # [扩展]
│   ├── learning-guide.md # 学习指导（缺陷清单/使用边界/资料吸收台账）——不进日常执行链路
│   ├── execution-pitfalls.md # 执行端操作坑清单（不进 Module Map/运行时）
│   └── _archive-suspended-claims.md  # 停用主张归档（不读不用）
├── assets/
│   ├── templates.md      # 00-06 项目文件标准模板（01 含变更影响范围/入画道具/焦段；02 含服装锁定档位/场景持续在场/身体-器械空间账/四组负面词库；03 含方向锚图/目标状态图/竖屏安全区；04 含 PLAN/REF + PLAN-TAIL/挂图顺序表/逐镜动线/背景动作线/焦段/光影演变；06 含单镜时长/剪辑端转场/节奏/关键音效混音）
│   ├── templates-character.md  # 人物参考图模板（0a 合图变体默认 / 分张退路 / 0c / 多人脸对照条 / 0d）
│   └── templates-execution.md  # 执行契约模板（批次生产卡 / 段状态账 / 批次校验记录 A1-A16 / 段落锁定清单九项 / 无台词段 / 一页版段模板含走位总谱（逐镜动线/背景动作线）/光影演变/动作桥 / 负面提示词两段式）
├── scripts/
│   ├── check.py          # 薄校验层（K1-K17 机械门，纯标准库；A16/A17/A18 为 opt-in）
│   ├── check.mjs         # Node CLI + 门注册（默认 K1-K17；A16/A17/A18 可选，与 check.py 行为对齐）
│   ├── check-core.mjs    # check.mjs 共享 helpers
│   ├── check-gates-a.mjs # K1-K6 门
│   ├── check-gates-b.mjs # K7-K12 门
│   ├── check-gates-c.mjs # K13-K14 门
│   ├── check-gates-d.mjs # K15-K16 门
│   ├── check-gates-e.mjs # A16/A17/A18 可选审计
│   ├── check-gates-f.mjs # K17 提示词卫生
│   ├── vigen_md.py       # Python 解析层
│   ├── vigen-md.mjs      # Node 解析层（行为对齐 vigen_md.py）
│   └── export.py         # 交付打包（快照 + manifest + checksums，不声称审批）
└── tests/
    ├── test_check.py       # check.py 单元测试（122 tests；含 test_export）
    ├── check-mjs.test.mjs  # check.mjs K1-K17 + A16/A17/A18 parity（132 tests）
    ├── baseline-record.md  # TDD 测试记录
    ├── baseline-checkpy-record.md  # 真实项目试跑误拦观察记录
    └── fixtures/           # good/bad 样例项目
```

## 当前模型栈（2026-11）

- 图片：gpt-image-2 / gpt-image-2.5（文生图、单图参考、多图参考；2.5 提示词上限 32,000 字符、编辑输入 1-16 张、支持 mask/markup）
- 视频：happyhorse-1.1（3-15s）/ MiniMax-H3（4-15s）/ Seedance·即梦系（参考生视频）
- 语音：默认视频模型自带语音；需严格音色一致时备选 cosyvoice TTS 对轨
- 剪辑：剪映

> models.md 只记支持能力（模式/时长/分辨率/参考素材限制）；调研所得"癖好"类主张已全部停用归档，用户实测有效的规则保留并标注依据。

## 安装

```bash
# Claude Code 个人技能目录（只拷运行所需文件）
cd vigen
mkdir -p ~/.claude/skills/vigen
cp SKILL.md ~/.claude/skills/vigen/
cp -r references assets scripts ~/.claude/skills/vigen/
```

> **脚本调用路径**：装好后 check.py 在 `~/.claude/skills/vigen/scripts/check.py`。你的项目目录里没有 `scripts/`，调用时必须用技能目录的绝对路径（或先解析技能根目录），不要写 `python scripts/check.py`。
> 校验：`python ~/.claude/skills/vigen/scripts/check.py <项目目录> --partial`
> 交付：`python ~/.claude/skills/vigen/scripts/export.py <项目目录> --out <项目外目录>`（快照 + manifest + checksums，不声称审批）

安装后无需手动调用——对话中出现"帮我做一个短视频 / 分镜 / 视频提示词 / 多集短剧 / 王家卫感短片"等意图时自动触发；也可显式 `/vigen`。

## 开发过程文档

- [create.md](create.md) — 需求文档 + 设计方案 + 迭代记录
- [research-notes.md](research-notes.md) — 历史调研笔记（结论已按"停用主张"处理，仅存档）
- [references/execution-pitfalls.md](references/execution-pitfalls.md) — 执行端操作坑清单

## 持续学习机制

以 **Seedance 2.5 提示词模式为当前质量标杆**，经 [learning-guide.md](references/learning-guide.md) 持续迭代：

- **四步学习法**：学习→提炼→总结→积累——新资料拆成可执行的规则/模板/例句三层，禁止笼统总结
- **可信度分级入库**：`[官方文档]` > `[用户实测]` > `[成品样例]` > `[社区方法论]`；无出处的主张不入库
- **单一事实源**：每条规则只在一个文件写全文，其余处只写"要点+指针"——重复即缺陷（V2.8 起强制执行）
- **缺陷清单只增不删**：已修复的移入存档附证据

## 已知边界

- 只产提示词与项目文件，不调用生成 API、不做剪辑执行；check.py / check.mjs 只读校验项目 Markdown，同样不调 API、不改文件
- `check.mjs` 已 **K1-K17 全量**，与 check.py 同输出/同退出码；全量 parity 由 `tests/check-mjs.test.mjs` 覆盖。check.py 仍是权威实现，改门必须两边同步
- **A16（先锁后写）是 opt-in 审计**：`--gate A16` 机检风格圣经逐字/入画 REF 登记/持续在场三项；技术动作与朝向三要素仍人工核对
- **A17（执行契约留痕）是 opt-in 审计**：`--gate A17` 机检批次生产卡/批次校验记录 A1-A16/段状态账/参考契约/时间账/风格锁逐字/04 段锁定清单九项/人物道具群像就地绑定/走位总谱+逐镜动线+背景动作线/动作桥/负面提示词闭环/每镜焦段/光影演变线；不查内容质量
- **A18（图片约束预算）是 opt-in 审计**：`--gate A18` 对 03 单张图提示词 >260 汉字或约束词 >10 处报警；技术参考图/文字排版类豁免。警告后按 prompt-rules 0.12 删减，不为过 A18 删承重锚
- **K17（提示词卫生）是默认门**：04/03 正向正文禁音乐类词；无台词段须含"无台词/无旁白/无人声"；有声音节须有"没有第二种声音，也没有任何持续声底"。明确标记的【负面提示词】节跳过音乐词检查
- **04 分卷（V3.17）**：大项目可按 `04_视频提示词_卷NN.md` 拆分；`04_视频提示词.md` 只作索引，check.py/check.mjs 自动按文件名排序合并分卷校验
- **测试现状**：Python 122 tests；Node 132 tests（含 A17/A18 全夹具 parity）
- 平台商业层（赛道/集数/付费墙）是**立项参考**，不是平台官方规则；本 skill 不预测爆款、不承诺过审
- 不做真人拍摄指导；剧本必须经 GATE1.5 用户定稿（skill 自检是辅助不是替代）
- 内容安全走**反应式降级**：未登记模式不预防性降敏；被拦后按措辞级/构图级降级，解法登记进已验证模式库，不保证通过所有平台审核
- 模型能力按"模型 × 供应商"两维登记；同名模型经不同网关接入时能力可能不同，生成前按当前供应商实测为准

## 许可证

本项目采用 **MIT** 许可证——见 [LICENSE](LICENSE)。
