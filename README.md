# vigen — AI 视频制作辅助 Skill

把一句创意或一份剧本变成一套完整的、可直接复制到生成工具使用的视频制作方案。面向零影视基础的用户：分镜、运镜、转场、光影、提示词工程全部自动补全，只需回答需求问卷并在三个确认点（GATE0 / GATE1.5 / GATE1）做决定。

> **本 README 只做介绍与导航，不重述规则细节**——规则全文的唯一权威在各 references 文件里（下方目录结构列明）。重述会漂移：这份文档过去就因逐条复述规则而落后于实际版本。

## 它解决什么问题

AI 视频制作的痛点不在"没有工具"，而在"不知道怎么指挥工具"。本 skill 解决六大类问题：

| 痛点 | 解法在哪 |
| --- | --- |
| 图片有 AI 油腻感、单一死板 | "描述这张照片怎么拍出来的" + 画面张力四法 → [realism.md](references/realism.md) |
| 分段生成色调漂移 | 全片色彩基调（3-5 个十六进制色号按面积分配，色号+落点进每条提示词）→ [styles.md](references/styles.md) |
| 提示词不精准、模型听不懂 | 语义绑定三层法 + 正向引导>负面约束（分端裁决）→ [prompt-rules.md](references/prompt-rules.md) / [knowledge-index.md](references/knowledge-index.md) |
| 复杂动作生成不出来 | 反先验动作先用首帧锁姿势，视频只写后续运动 → [prompt-rules.md](references/prompt-rules.md) |
| 人物/场景/道具跨图不一致 | 四层锚定逐字复用 + 参考图六条硬标准 + 头身分离 + 互挂参考 → [consistency.md](references/consistency.md) |
| 道具状态混乱 | 道具六条判定 → 独立参考图每状态一张 + 组合道具拆分出图 → [prompt-rules.md](references/prompt-rules.md) |
| 动作违反物理常识 | 动作三段式 + ENDING FRAME + 秒级时序 → [prompt-rules.md](references/prompt-rules.md) |
| 跨片段音色漂移 | 按模型选语音路线（happyhorse 自带语音 / H3 音色自提取 / cosyvoice 对轨）+ 发声描述公式 → [consistency.md](references/consistency.md) |
| 一段视频只有一个镜头 | 骨架 A 多镜头段落公式为默认 → [prompt-rules.md](references/prompt-rules.md) |
| 运镜单一、转场呆板 | 40 运镜 + 8 转场 + 高风险运镜双方案制 → [cinematography.md](references/cinematography.md) |
| 长剧遗忘细节 | 00_剧情状态.md 每集强制更新 + 尾帧续接 → [consistency.md](references/consistency.md) |
| 剧情被擅自删改 | 情节点清单逐点登记，100% 覆盖校验 → [screenwriting-craft.md](references/screenwriting-craft.md) |
| 生成资产浪费钱 | 资产引用矩阵先行，零引用不生成 → [prompt-rules.md](references/prompt-rules.md) |
| 生成失败不知道怎么救 | 结构判定前置的回退阶梯 → [SKILL.md](SKILL.md) |
| 提示词被内容审核拦截 | 高危题材降敏改写 + 二分法定位触发词 → [content-safety.md](references/content-safety.md) |
| 中途要加镜头/改情节 | 活剧本修订（局部重排 + 稳定镜号），不重走全流程 → [SKILL.md](SKILL.md) |

## 工作流

```
GATE0 需求问卷+对齐
  → 阶段1a 剧本创作 ─GATE1.5 剧本定稿─→ 阶段1b 分镜+锚定 ─GATE1 确认─
  → 阶段2-4 图片提示词（先资产矩阵）→ 阶段5 视频提示词 + 台词表
  → 阶段6 剪辑清单 →（系列：更新 00_剧情状态）
```

三个停点：**GATE0**（问卷+需求对齐）、**GATE1.5**（剧本定稿——未定稿绝不进分镜）、**GATE1**（锚定确认）。定稿锁的是故事骨架与情节点清单，分镜表是活文档（后续增删镜头走活剧本修订的局部重排）。

**项目结构**：单视频 `<项目名>/01-06`；系列 `<系列名>/00_剧情状态.md + ep01/…ep02/…`。

每个项目产出的文件（Markdown 即"创作真相"）：

| 文件 | 内容 |
| --- | --- |
| `00_剧情状态.md` | 系列专用：剧情摘要/角色状态/道具状态/上集尾帧/伏笔——每集完成后强制更新 |
| `01_方案与剧本.md` | GATE0 对齐记录 + GATE1.5 定稿记录 + 分场剧本 + 情节点清单 + 分镜总览表（活文档，稳定镜号）+ 变更记录 |
| `02_锚定表.md` | 目标模型 / 色彩基调 / 角色 / 场景（LOCATION MAP+四视图）/ 道具 / 风格圣经 |
| `03_图片提示词.md` | 资产引用矩阵 + 人物/道具/场景/情景参考图（L1-L4 分级出图）+ 内容安全措辞规范（高危题材项目） |
| `04_视频提示词.md` | 默认骨架 A 多镜头段落公式 / 骨架 B 单镜头（特例）；时长硬校验+尾帧续接 |
| `05_语音台词表.md` | 台词总账 + 发声描述公式（前置身份两段+六参数）+ 音色参考资产 + SPEAKER LOCK |
| `06_剪辑清单.md` | 拼接/转场实现/转场音频处理/BGM/调色/导出 |

## 目录结构（规则全文的唯一权威）

```
├── SKILL.md              # GATE0 问卷 + 工作流 + 意图路由（含活剧本修订）+ 14 条硬规则（要点+指针）+ 回退阶梯 + 效率纪律
├── references/
│   ├── screenwriting-craft.md # 剧本创作：7 大漏洞自检 + 钩子悬念纪律 + 故事三层分离 + GATE1.5 + 故事板四格
│   ├── prompt-rules.md   # 四大底层认知 + 图片/视频骨架 A·B + 道具六条判定 + L1-L4 分级 + 发声描述公式 + 校验（10 关键门 + 13 抽查项）
│   ├── models.md         # 模型能力档案 + 生成路径判定 + 换模型指引
│   ├── cinematography.md # 40 运镜 + 8 转场 + 机位语义 + 段长/慢镜预算 + 双方案表 + 节奏模板
│   ├── realism.md        # 去AI味 + 张力四法 + 表面两档与塑形约束 + 朝代纪律 + 文字物理化
│   ├── styles.md         # 15 风格库 + 色彩基调色板 + 风格提取解梦卡
│   ├── consistency.md    # 四层锚定 + 参考图六条/头身分离 + 角色路由/基准参考法 + 最小参考集 + 音色自提取 + 系列记忆 + 失效传播
│   ├── content-safety.md # 内容安全降敏（高危题材项目必读）：降敏对照表 + 显式否定旧设定 + 二分法定位 + 失败分类对策
│   ├── knowledge-index.md# 扩展知识库路由表（命中才读，token 纪律守门文件）+ 负面词效力分端裁决
│   ├── examples.md       # 完整示例
│   ├── action-combat.md  # [扩展] 武打动作引擎
│   ├── cinema-grade-params.md # [扩展] 电影级参数块 + 国漫四视图
│   ├── expressions.md / director-styles.md / extended-views.md / emotion-craft.md / ugc-realism.md / anime-to-real.md  # [扩展]
│   ├── learning-guide.md # 学习指导（缺陷清单/使用边界/资料吸收台账）——不进日常执行链路
│   └── _archive-suspended-claims.md  # 停用主张归档（不读不用）
├── assets/
│   └── templates.md      # 00-06 项目文件标准模板
└── tests/
    └── baseline-record.md  # TDD 测试记录
```

## 当前模型栈（2026-10）

- 图片：gpt-image-2 / gpt-image-2.5（文生图、单图参考、多图参考）
- 视频：happyhorse-1.1（3-15s）或 MiniMax-H3（4-15s）——提示词骨架统一，模型差异只在能力参数
- 语音：默认视频模型自带语音；需严格音色一致时备选 cosyvoice TTS 对轨
- 剪辑：剪映

> models.md 只记支持能力（模式/时长/分辨率/参考素材限制）；调研所得"癖好"类主张已全部停用归档，用户实测有效的规则保留并标注依据。

## 安装

```bash
# Claude Code 个人技能目录（只拷运行所需文件）
cd skillsCreate
mkdir -p ~/.claude/skills/vigen
cp SKILL.md ~/.claude/skills/vigen/
cp -r references assets ~/.claude/skills/vigen/
```

安装后无需手动调用——对话中出现"帮我做一个短视频 / 分镜 / 视频提示词 / 多集短剧 / 王家卫感短片"等意图时自动触发；也可显式 `/vigen`。

## 开发过程文档

- [create.md](create.md) — 需求文档 + 设计方案 + 迭代记录
- [research-notes.md](research-notes.md) — 历史调研笔记（结论已按"停用主张"处理，仅存档）

## 持续学习机制

以 **Seedance 2.5 提示词模式为当前质量标杆**，经 [learning-guide.md](references/learning-guide.md) 持续迭代：

- **四步学习法**：学习→提炼→总结→积累——新资料拆成可执行的规则/模板/例句三层，禁止笼统总结
- **可信度分级入库**：`[官方文档]` > `[用户实测]` > `[成品样例]` > `[社区方法论]`；无出处的主张不入库
- **单一事实源**：每条规则只在一个文件写全文，其余处只写"要点+指针"——重复即缺陷（V2.8 起强制执行）
- **缺陷清单只增不删**：已修复的移入存档附证据

## 已知边界

- 只产提示词与项目文件，不调用生成 API、不做剪辑执行
- 不做真人拍摄指导；剧本必须经 GATE1.5 用户定稿（skill 自检是辅助不是替代）
- 内容安全降敏是措辞层（剧情可保留、措辞必须换），不保证通过所有平台审核
