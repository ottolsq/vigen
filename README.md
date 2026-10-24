# vigen — AI 视频制作辅助 Skill（ai-video-maker）

把一句创意变成一套完整的、可直接复制到生成工具使用的视频制作方案。面向零影视基础的用户：分镜、运镜、光影、提示词工程全部自动补全，只需输入一句创意并在锚定确认点（GATE1）点一次头。

## 它解决什么问题

AI 视频制作的痛点不在"没有工具"，而在"不知道怎么指挥工具"：

| 痛点 | 本 Skill 的解法 |
| --- | --- |
| 图片有"AI 油腻感"、单一死板 | "描述这张照片怎么拍出来的"方法论：真实相机媒介+镜头参数+环境瑕疵感（[realism.md](references/realism.md)） |
| 人物/场景跨图不一致 | 锚定表机制：锚定短语逐字复用 + 参考图多图输入双保险（[consistency.md](references/consistency.md)） |
| 首帧图生视频动作突兀 | 情景图强制捕捉"蓄力瞬间"（有势能不锁定方向），视频从静止自然起势 |
| 动作违反物理常识 | 动作三段式（起始→过程+速度曲线→明确终点）+ 每镜容量硬约束（[prompt-rules.md](references/prompt-rules.md)） |
| 分段生成色调/音色不一致 | 风格圣经逐字后缀 + cosyvoice voice_id 固定 + 剪映统一调色兜底 |
| 运镜单一/抖动 | 20 种电影运镜库 + 情绪映射 + 高风险运镜降级表 + 运动运镜平滑规则（[cinematography.md](references/cinematography.md)） |
| 换视频模型提示词全废 | 双轨道隔离：happyhorse 轨（中文极简）/ MiniMax-H3 轨（英文结构化），模型记入 02 锚定表按轨道出稿（[models.md](references/models.md)） |
| 进阶需求（导演风格/漫剧微表情/UGC自拍/2D转真人） | 扩展知识库按需取用：knowledge-index 路由，命中场景才读（[knowledge-index.md](references/knowledge-index.md)） |

## 工作流

```
一句创意
  → 阶段1 剧本 + 锚定表 ──GATE1 确认──→ 阶段2-4 图片提示词
  → 阶段5 视频提示词 + 台词表 → 阶段6 剪辑清单
```

每个视频项目产出 6 个文件（Markdown 即"创作真相"）：

| 文件 | 内容 |
| --- | --- |
| `01_方案与剧本.md` | 主题/时长/风格/情绪 + 分镜总览表 + 运镜大白话解释 + 校验记录 |
| `02_锚定表.md` | 目标模型（三件套，续作/换轨依据）/ 角色锚定（逐字短语+参考图+音色绑定）/ 场景锚定 / 风格圣经 |
| `03_图片提示词.md` | 人物参考图（白底）/ 场景参考图 / 情景参考图（=视频首帧，蓄力瞬间；fl2va 项目加终点图） |
| `04_视频提示词.md` | 按视频模型选轨：happyhorse（i2v 精简型 + r2v 备选）或 MiniMax-H3（i2va/fl2va/ref2va） |
| `05_语音台词表.md` | cosyvoice 音色配置 + 台词逐句时长校验 + 剪映对轨位置表 |
| `06_剪辑清单.md` | 拼接顺序 / 头尾裁剪 / 转场 / BGM / 调色 / 防抖 / H3 素材转存 / 导出参数 |

支持四种调用：**一句话全流程**（经 GATE1）、**定向修改**（"镜头3动作改成转身离开"只动对应文件）、**续作**（从第一个未完成阶段继续）、**阶段重做**（带失效传播标记，防止旧提示词配新锚定）。生成失败有回退阶梯（同 seed 重试→拆镜→换运镜/轨道→问用户）。

## 当前模型栈（2026-10）

- 图片：gpt-image-2 / gpt-image-2.5（文生图、单图参考、多图参考）
- 视频：**happyhorse-1.1**（t2v / i2v 首帧参考 / r2v 多图参考）或 **MiniMax-H3**（t2va / i2va / fl2va 首尾帧 / l2va / ref2va 多参考+音色参考，经 easyframe 网关）——两轨提示词语法完全不同，绝不混用
- 语音：cosyvoice-v3.5-flash（音色复刻 + voice_id 持久化）
- 剪辑：剪映

更换模型时只更新 [models.md](references/models.md)（按档案卡格式追加新模型），骨架与流程不变。

## 目录结构

```
├── SKILL.md              # 核心流程 + 意图路由 + 10 条硬规则 + Module Map
├── references/           # 知识库（按需加载）
│   ├── prompt-rules.md   #   提示词骨架（A/B 双轨）/ 必填槽位 / 校验规则
│   ├── models.md         #   模型档案（gpt-image×2 / happyhorse / H3 / cosyvoice）+ 换模型指引
│   ├── cinematography.md #   20 运镜 / 景别机位光影 / AI 避坑与平滑规则 / 15-60s 节奏模板
│   ├── realism.md        #   去AI味方法论 / 摄影词汇表 / 构图多样性 / 人像强化包
│   ├── styles.md         #   15 风格库（每风格=完整风格圣经词条）
│   ├── consistency.md    #   锚定机制（模型/角色/场景/色调/音色）/ 跨镜一致性 / 失效传播
│   ├── examples.md       #   3 类完整示例（治愈自然 / 人物剧情 / 科技概念）
│   ├── knowledge-index.md #  扩展知识库路由表（命中场景才读，省 token）
│   ├── expressions.md    #   [扩展] 微表情库（女主50 + 男主45 条）+ 表演五步法
│   ├── director-styles.md #  [扩展] 8 位导演视觉档案 + 诺兰调色专项
│   ├── extended-views.md #   [扩展] 场景四视图补全 + 十二宫格分镜矩阵
│   ├── emotion-craft.md  #   [扩展] 情绪影像方法论（色调/光线因果/构图四要素）
│   ├── ugc-realism.md    #   [扩展] UGC 缺陷保留哲学 + 手持自拍范式 + 韩系随拍
│   └── anime-to-real.md  #   [扩展] 2D 转真人五维度模板
├── assets/
│   └── templates.md      # 01-06 项目文件标准模板（含 fl2va 终点图配方）
└── tests/
    └── baseline-record.md  # TDD：基线 10 项违规 → GREEN 3/3 → V1.1/V1.3/V1.4/V1.5/V1.7 回归全过
```

## 安装

```bash
# Claude Code 个人技能目录（只拷运行所需文件，不带开发文档）
cd skillsCreate
mkdir -p ~/.claude/skills/ai-video-maker
cp SKILL.md ~/.claude/skills/ai-video-maker/
cp -r references assets ~/.claude/skills/ai-video-maker/
```

安装后无需手动调用——对话中出现"帮我做一个短视频 / 分镜 / 视频提示词 / 王家卫感短片 / 漫剧微表情"等意图时自动触发；也可显式 `/ai-video-maker`。

## 开发过程文档

- [create.md](create.md) — 需求文档 + 设计方案（十二节）+ 迭代记录 V1.1-V1.7
- [research-notes.md](research-notes.md) — 6 路调研结论（社区 Skill 规范 / 图片真实感 / 视频生成技巧 / 模型档案 / 电影运镜库 / MiniMax-H3），含来源链接与"未证实清单"

本 Skill 经 TDD 开发：先跑无 skill 基线记录 10 项典型违规，再以多轮子代理测试验证清零，详见 [tests/baseline-record.md](tests/baseline-record.md)。

## 已知边界

- Sora / Runway / Pika / Veo 官方一手文档未获取（网络封锁），相关结论为社区转述并已在调研笔记中标注；主栈模型均有可靠一手资料
- gpt-image-2/2.5 的提示词字符上限官方未公布，skill 内未使用具体数字
- 提示词规则来自调研与社区 A/B 实测资料，真实工具端效果建议以小项目先验证，反馈后迭代对应规则文件
