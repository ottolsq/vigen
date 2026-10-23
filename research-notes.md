# 调研笔记（2026-10-22 起）

> 并行调研的结论提炼。来源细节见各节链接。本文件是 Skill 设计的事实依据，设计阶段从这里取材。

## 调研六：MiniMax-H3 模型档案（2026-10-23）✅

> 来源：官方 GitHub MiniMax-AI/MiniMax-H3（skills/h3-prompt-writing 一手原文）、HuggingFace docs（与 skill 逐字节同）、platform.minimax.io 官方文档与 Feature Highlights、ComfyUI 官方文档、awesome-minimax-H3（17 个 Reddit 实测帖聚合）、xianyu110 274 条带成片提示词库、1000 条数据集策展分析、pixo.video 官方手册解读、用户提供的 easyframe API 文档。

### 与 happyhorse 的关键差异（提示词风格不可混用）

| 维度 | happyhorse-1.1 | minimax-h3 |
| --- | --- | --- |
| 提示词语言 | 中文自然语言 | 结构化语法的字段/标签/运镜句**必须英文**；台词歌词画面文字保留原语言；`<d>` 是 tokenizer 特殊 token 不能翻译 |
| 结构 | i2v 极简 30-60 字 / r2v 四段式 | T2VA/I2VA/FL2VA/L2VA 三段式（integrated_multimodal_description / overall_soundscape / non_diegetic_music）；Ref2VA 六段式 |
| 模式 | t2v/i2v/r2v | t2va/i2va/**fl2va（首+尾帧）**/**l2va（尾帧）**/ref2va（9图+3音频，合计12） |
| 时长 | 3-15s | 5-15s（整数）；分辨率 480p/720p，Pro 未开放 |
| 运镜 | 中文自然句 | 英文自然句+幅度/速度修饰（pushes in with small amplitude at slow speed）；14 种官方运镜类型 |
| 镜头切分 | 时间码分镜 | `[Shot N]` **只表示真实切镜**；镜内动作/台词阶段用 `At MM:SS.mmm` 不切镜——哲学与 happyhorse 时间码相反 |
| 台词 | 口语描述+4字/秒估时 | `(S1)` 说话人 ID（按首次发声顺序，跨镜复用）；`<d>[Chinese] 台词</d>` 逐字保留永不删减；`<scenetrans>` 跨镜连续；`<cutoff>` 截断；旁白必须声明 "while his lips remain completely closed" |
| 配乐 | "无背景音乐"关闭 | non_diegetic_music 独立段（写 N/A 即无）——更结构化 |
| 负面约束 | 约束槽禁令 | **无 negative prompt**（cfg=1 无负分支）——负面概念写正文 ban list（社区普遍在结尾堆 no extra fingers, warped hands...） |
| 分辨率 | 720P/1080P | 480p/720p；**I2VA 首帧会被拉伸到画布（不保宽高比）、尾帧居中裁剪**——参考图必须同比例 |
| 留存 | — | 视频 24h 留存、下载 URL 1h 有效——**到期前转存** |

### H3 提示词核心技巧（多来源确认）

- **官方提示词公式**（飞书手册经 pixo 转述）：完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明
- **I2VA 正文结构**（官方 base-en.txt）：首帧锚定（先描述图内风格/主体/构图）→ 动作发生 → 连续发展 → 结果或反应；身份/服装/颜色/关键物体/空间关系保持一致
- **FL2VA**：默认单镜头插值最好；正文写"变化路径"而非重复两张静帧描述；要一镜到底必须显式写且社区经验强调两遍（"一镜到底""不要出现拼接"）
- **写实感**：开头钉死媒介+调色（"Shot on 35mm black-and-white film, dense grain"）；格式指令（"Grainy webcam footage, slightly compressed"）比氛围词（"amateur"）有效；环境声用具体声源逗号链（"footsteps, rain, sirens"）不用抽象词
- **提示词长度**：上限 7000 字符/文本项（合计 30000）；官方手册明确"太短"是记录在案的失败模式（无参考时底线=主体外观+场景细节+动作+风格）；Ref2VA 生成类 detailed_description 建议 350-500 英文词；最长实测 6602 字符成功
- **语言选择**：托管 API/海螺 App（经 Context-IR 中间层）自然语言完全够用（官方 Feature Highlights 全是自然语言）；直连/easyframe 网关直传 → 必须结构化官方语法（无 IR 中间层）。**翻译过的提示词跑出来不是同一段片子**——按原语言写，不翻译

### 六错误清单（官方手册，pixo 转述）
1. 糊成一段无结构的话（不按公式分板块）
2. 上传素材却没写用途（每个文件必须一句分工声明）
3. 一边要配乐一边禁 BGM（自相矛盾）
4. 想一镜到底却写了镜头1/镜头2 分镜结构
5. 想要脸部一致却没传参考图
6. 无参考时提示词太短
社区补充：参考没分工、概括式台词（"她说了句安慰的话"必糊）、用比喻代替动作、画幅决定得太晚

### 已知缺陷与避坑
- 15s 长时序角色漂移（分段链式；面部纹理最先崩，误差累积）——与 skill"一段一运镜/拆段"规则互证
- 手部仍需主动防御（正文 ban list 堆禁令）
- 多说话人+音频参考会说错人——台词绑到可见事件而非时间码
- `<d>` 内省略号损害可懂度；标点只留 , . ? !
- 物理规律要显式要求（"believable weight, inertia, traction"）——可写但必须写出来
- 音频收敛晚于视频（语音/音色需更多步数）
- **Ref2VA 的 killer feature**：`<Audio 1> is the voice-timbre reference for <Subject 1> (S1)` 音色参考——跨段音色一致的新解法

### 官方 skill 生态（可借鉴）
- h3-prompt-writing（官方，MIT 可移植，npx skills add 安装）：SKILL.md 薄路由 + references/base-en.txt + ref-en.txt
- 官方失败回退阶梯（3d-animation-short-generator 的 fallback-policy）：①Reference Anchors 块强化重试 → ②缩短到 ≤6s 拆行 → ③该镜头换 Seedance → ④问用户
- 官方 QC checklist：分镜痕迹泄漏、双绑定标签残留等成片质检项
- 提示词库：xianyu110 274 条带成片（MIT）；1000 条数据集策展

### 对本 skill 的落地决策
1. models.md 加 H3 档案卡（含上述全部 + easyframe 特有边界：mode/resolution/seconds/aspect_ratio 参数、480p/720p、24h 留存）
2. **SKILL.md 触发时先问模型**（用户要求）：生图模型 + 视频模型 + 语音模型，从 02 锚定表读取或询问；按模型路由提示词风格——视频骨架分轨：happyhorse 轨（中文 i2v 精简型/r2v 四段式）与 H3 轨（英文三段式/六段式 + 标签体系）
3. prompt-rules.md 视频骨架节按模型分轨（不混用）；H3 轨的运镜/台词/禁令全部用 H3 官方语法
4. FL2VA 首尾帧 = skill"蓄力起点+动作终点"机制的新载体：情景图直接生成起点图+终点图两张
5. 06 剪辑清单加 H3 的 24h 留存转存提醒

---

## 调研一：社区已有 AI 视频 Skill 与 SKILL.md 规范 ✅

### 值得借鉴的机制（按采纳优先级）

| 机制 | 来源 | 一句话说明 | 采纳决策 |
| --- | --- | --- | --- |
| 五文档产物契约 | zenstory-ai/drama-skills (3.2k★) | 每集只维护 剧本/视觉设定/分镜/图片提示词/视频提示词 五个 md，Markdown 即"创作真相" | ✅ 直接采纳（与我们已确认的项目目录方案一致） |
| 连续性锁（continuity lock） | drama-skills | 跨镜必须保持的外观写成一条短语，逐字粘贴进每条受影响 prompt | ✅ 采纳为"锚定短语"机制（对应痛点 A3/B4） |
| 三视图锚定图策略 | eternityspring/shuohao-skills (4.9k★) | 先生成一张正面全身锚定图，其余视图（侧/背/细节）只引用锚定图 | ✅ 采纳（人物参考图阶段规则） |
| 资产库先于分镜（S2 before S3） | woanderingboy/novel-video-pipeline | 先建角色三视图+场景图资产，再写分镜；分镜只是"把资产按镜头语言排布" | ✅ 采纳（阶段顺序：剧本→锚定表→分镜） |
| 两个 GATE 人工确认点 | roy6732856/seedance-ip-pipeline | 出提示词后、粗剪后各一次确认，不多不少 | ✅ 采纳（对应用户"关键节点等确认"的工作方式） |
| 预览-确认-生产 | drama-skills | 花钱的生成任务先落文件展示确切参数，显式确认才执行 | ✅ 采纳（纯提示词方案下=提示词文件确认后再去工具生成） |
| Module Map 路由表 | FrameCoreWorks | SKILL.md 极薄，知识全在 references/，用"何时读哪个文件"表格索引 | ✅ 采纳（references 组织方式） |
| Hook 表格（技巧→心理效应→prompt 措辞） | beshuaxian/higgsfield-seedance2-jineng | 2秒钩子框架 10-12 种开场模式表格化 | ✅ 采纳进分镜知识库（开头抓眼球） |
| 台词秒数 ≤ 镜头秒数 校验 | shuohao-skills | 18 道质量门全部脚本机检 | ⚠️ 暂以规则清单形式内置（V1 不写脚本，校验规则写进 SKILL.md 由模型执行；未来可升级为 validate 脚本） |
| 站位/轴线/视线连续性 | shuohao-skills staging | 开场站位锚点、朝向、轴线 | ⚠️ 简化采纳（轴线规则进分镜知识库，不建独立 staging 阶段——我们是单条短视频不是多集剧） |
| 不伪造上游 | drama-skills | 有分镜就直接写视频提示词，不强制从头跑全流程 | ✅ 采纳（分阶段调用模式的设计依据） |
| VO 语速数学 ~2.3词/秒 | iart-ai/explainer-video-skills | seconds = words/2.3 + 0.4s | ✅ 采纳（中文约 4-5 字/秒，台词时长估算公式） |
| description 写 NOT-for 边界 | FrameCoreWorks | 防止误触发的负向边界声明 | ✅ 采纳 |

### 关键事实：官方仓库与英文圈没有视频类 skill
- anthropics/skills 官方 19 个 skill 无视频类；ComposioHQ awesome 清单无 video/film/storyboard 条目
- 社区成果集中在中文短剧/漫剧圈；最佳索引：UnderleveledBuilder/awesome-short-drama-skills (603★，含两轮盲评实测：drama-skills、shuohao-skills 剧本质量稳定胜出)
- MoneyPrinterTurbo / NarratoAI 是完整 Web 应用不是 skill，无 SKILL.md 组织可借鉴

### SKILL.md 编写规范（官方 agentskills.io + Claude Code）

**Frontmatter**：`name`（≤64字符，小写连字符，与目录名一致）、`description`（≤1024字符，必须"做什么+何时用"+具体触发词，祈使句开头）。Claude Code 扩展字段（disable-model-invocation 等）个人 skill 可用，但若未来上传 claude.ai/API 只能用标准 6 字段。

**Description 要"pushy"**：显式列举触发场景，包括用户没说"分镜/视频"也该触发的场合；中文触发词清单对中文用户有效；末尾写 NOT-for 边界。

**渐进式三级加载**：元数据（~100 tokens 常驻）→ SKILL.md 正文（<500 行 / <5000 tokens 触发时加载）→ references/ 按需读取（不限量）。

**目录约定**：`SKILL.md` + `scripts/`（可执行）+ `references/`（按需文档）+ `assets/`（模板示例）。引用只允许一层深度。**必须写明"何时读哪个文件"**（Module Map 表格）。>300 行的 reference 要有目录。

**内容原则**：
- 只写模型不知道的（检验法：没有这条指令模型会做错吗？不会就删）
- 解释 why 而非堆 MUST（满篇大写 ALWAYS/NEVER 是黄旗）
- 给默认不给菜单；按脆弱度定严格度
- Gotchas 段是最高价值内容；模板优于描述；教方法不教答案

### 一致性三大流派
1. 提示词锁定（[Character/Setting/Voice Lock] 三段锚 + 负面指令 + 结尾复述利用 recency bias）
2. 连续性锁短语（跨镜外观一条短语逐字粘贴）
3. 参考图锚定（最稳：正面锚定图→其余视图只引锚定图；`char:<id>:front` 令牌）

三者可叠加使用：参考图锚定为主 + 锚定短语为辅。

### 来源
- https://github.com/anthropics/skills · https://agentskills.io/specification · https://agentskills.io/skill-creation/best-practices
- https://github.com/zenstory-ai/drama-skills · https://github.com/eternityspring/shuohao-skills · https://github.com/beshuaxian/higgsfield-seedance2-jineng
- https://github.com/FrameCoreWorks/framecore-works-claude-skills · https://github.com/roy6732856/seedance-ip-pipeline · https://github.com/woanderingboy/novel-video-pipeline
- https://github.com/iart-ai/explainer-video-skills · https://github.com/UnderleveledBuilder/awesome-short-drama-skills

---

## 调研四：模型栈档案 ✅

> 主要来源：OpenAI 官方公告与定价页、GitHub awesome-happyhorse-prompts 仓库（47+ 场景 100+ 次 A/B 实测）、阿里云百炼文档、SiliconFlow 文档。调研日期 2026-10-22。

### gpt-image-2（2026-04 发布）
- 文生图 + 图生图 + 多图参考（官方示例 9 张人脸参考合成）；API 内最高 2K 分辨率；宽高比最宽 3:1
- 官方提示词风格：长句自然语言，结构 = 主体+场景+光线+相机参数（如 "85 mm f/4"、"shot on 35mm film"）+风格约束；宽高比直接写进 prompt
- 官方强调 "smarter images with less prompting"——不必过度堆砌（注意：与我们"完整性强制"规则的平衡点：维度全覆盖但表述自然）
- 已知缺陷：物理世界模型类任务失败（折纸/魔方）、极致密集细节、标注箭头类
- 提示词字符上限：官方未公布（gpt-image-1 时代 32000 字符，勿沿用旧值）
- 多图参考无权重/顺序 API 参数，靠 prompt 声明每张图用途（官方示例："Use the input photos only for each person's identity"）

### gpt-image-2.5（2026-10 发布，Flare/Sunburst 双型号）
- **Flare**：默认，比 2.0 延迟低 50%；**Sunburst**：编辑精度优先，生成更慢
- 相对 2.0 改进：参考图人物保真度提升、更自然光照纹理、"understands what not to change"（只改指定元素保住其余构图）、多轮编辑不越改越糊
- 编辑类任务最佳实践：把"要改什么 + 保持什么"都写明
- 精确 API id 未公布（内部字段 gpt_image_25_flare/sunburst），使用前控制台核对

### happyhorse-1.1-t2v / -i2v / -r2v（阿里百炼 DashScope）★ 核心模型
- API：`POST dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis`，异步轮询；720P ¥0.9/秒、1080P ¥1.2/秒
- size 写法 `1920*1080`（`1080P` 写法已废弃）；duration **3-15 秒**；语言：中/英/日
- **t2v 提示词偏好**：支持超长 prompt（2500 字符后指令遵循度显著提升）；推荐结构 = 总述（时长/风格/画质）→ 角色设定 → `[00:00-00:04]` 时间码分镜 → 音频/对白段 → 全局约束尾段
- **i2v 提示词偏好（与我们工作流最相关）**：
  - 首帧已含画面信息，**prompt 绝不重复描述外观/服装/背景**
  - 最优区间 **30-60 字**，聚焦三要素：动作 + 运镜 + 音效（复杂武打可放宽到 720 字）
  - 模板：`[动作描述，2-3个具体动词] + [运镜指令] + [音效/环境音]`
- **音频控制（纯 prompt 层，无 API 参数）**：BGM 可关闭（"背景音效受 Prompt 控制可关闭"）；实测写法：【音频】只保留人物极轻微的真实声音…无背景音乐
- **对白/口型规则**：台词语言匹配文化（日漫用日语）；台词时长 = **4字/秒 × 1.2 情绪倍数**（17字≈5.1s）；每段时间窗台词 ≤2 句口型触发率最高；无台词段用 `[角色/沉默/情绪/无台词]` 占位防加戏；12s 单段 ≤32 字，15s ≤40 字
- **已知问题**：
  - **文字渗透**：对参考图忠实度极高，会把参考图上的标注文字/水印渲染进视频 → 提交前擦掉参考图上的文字 + 全局尾段"画面严禁出现任何字幕/水印/logo"
  - 时间码执行过于字面化：单人情绪戏加时间码反而不如松绑叙述自然
  - 生成非确定性：同 prompt 重抽差异大，择优必要
  - 内容安全拦截：真实国家/民族对抗描写会触发；失败任务不返回原始 prompt，本地留存
  - 段间续接：Chain 策略（上段 mid/last 帧加进参考图）+ 剪映 xfade 0.4-1.0s
- **r2v 多图参考**：`[Image 1]`~`[Image 9]` 引用（**[Image 1] 必须带空格**，[Image1] 会 API 解析失败）；四段式结构：①每张图用途声明 ②风格氛围+角色卡 ③分镜/表演 ④全局约束尾段；多段连续叙事 HEADER/FOOTER 模板复用，段首加"延续上段：[站位/手部/光线/道具状态]"

### qwen/cosyvoice-v3.5-flash（阿里云百炼）
- **音色一致性机制（解决痛点 B5）**：复刻音色（voice clone）创建后**默认长期有效**，保存 voice_id 每次调用传同一个即可；再加固定 `seed`（同 seed+同参数+同文本 → 完全可复现）
- 参考音频要求：10-20 秒、≤60 秒、≤10MB、≥16kHz、无 BGM/噪声/其他人声、正常语速
- voice 绑定创建时的 target_model，不能跨模型使用；账号上限 1000 个音色
- 关键参数：format mp3 默认、rate 0.5-2.0、pitch 0.5-2.0、`instruction` free-style 指令 ≤100 字符（仅复刻/设计音色可用）、`hot_fix` 自定义发音
- 价格 ¥0.8/万字符；不支持 Function Calling/结构化输出/联网
- **考证**：`qwen/` 前缀未在任何官方平台出现——官方渠道是阿里云百炼（模型名不带前缀）；带前缀写法来自第三方聚合网关

### 未证实清单（勿写入 skill 当事实用）
1. gpt-image-2/2.5 提示词字符上限（官方未公布）
2. gpt-image 多图参考权重/顺序参数（不存在，纯 prompt 控制）
3. gpt-image-2.5 精确 API id（控制台核对）
4. happyhorse 独立音频开关 API 参数（不存在，纯 prompt 控制）

---

## 调研五：电影运镜知识库 ✅

> 主要来源：StudioBinder 全套运镜/景别/光影解析（30+ 篇已抓取核实）、Runway Academy 官方 Prompt Guide。Veo/可灵/即梦官方文档被网络阻断未能核实，相关结论标注"待验证"。

### 运镜库（20 种，进 references/cinematography.md 的核心素材）

| 运镜 | 英文表达 | 情绪效果 | 经典案例 |
| --- | --- | --- | --- |
| 推 | `camera pushes in / dolly in` | 聚焦、紧张渐强、进入内心 | 《小丑》《仲夏夜惊魂》 |
| 拉 | `camera pulls back / dolly out` | 孤独、抽离、收尾余韵 | — |
| 希区柯克变焦 | `dolly zoom / vertigo effect` | 眩晕、现实扭曲 | 《迷魂记》《大白鲨》《指环王1》 |
| 摇 | `pan left/right` | 快摇=活力；慢摇=悬念；突摇=意外 | 《慕尼黑》 |
| 横移 | `tracking / trucking shot` | 沉浸、生活质感、消化情绪 | 《老男孩》 |
| 跟 | `camera follows behind the subject` | 行动沉浸、空间连续 | 《好家伙》《光荣之路》 |
| 升 | `crane up / boom up` | 胜利、崇高、格局展开 | 《塞尔玛》 |
| 降 | `crane down` | 弱小、脆弱、被压制 | — |
| 环绕 | `camera orbits around / 360 arc` | 慢绕=浪漫/英雄；快绕=争执/恐慌 | 《搏击俱乐部》 |
| 甩镜 | `whip pan to...` | 爆发能量、喜剧节奏、时空切换 | 《热血警探》《布达佩斯大饭店》 |
| 手持 | `handheld camera, natural shake` | 纪实真实感、混乱、亲密 | 现代动作片标配 |
| 斯坦尼康 | `smooth steadicam / gliding` | 幽灵视角、顺滑沉浸 | 《好家伙》一镜、《闪灵》走廊 |
| 长镜头 | `one continuous take, no cuts, seamless shot` | 沉浸无中断、时间真实 | 《赎罪》敦刻尔克、《1917》 |
| 变焦 | `zoom in / slow zoom out / crash zoom` | 慢推=凝视/跟踪感；急推=喜剧/惊吓 | 《闪灵》、塔伦蒂诺 |
| 航拍 | `aerial drone shot` | 史诗、定场、疏离 | 《银翼杀手》开场 |
| 顶视 | `overhead top-down shot` | 孤独、被监视、抽象构图 | 《暖暖内含光》 |
| 固定 | `static shot / locked-off camera` | 情绪沉淀、喜剧timing、舞台感 | — |
| 绑定视角 | `snorricam`（AI 难度高） | 眩晕、心理崩坏 | 《梦之安魂曲》 |
| 俯仰 | `tilt up/down` | 仰=权力；俯=揭示/脆弱 | 《布达佩斯大饭店》 |
| 变焦点 | `rack focus from A to B` | 无剪辑的信息转移、埋伏笔 | — |

### 景别/机位/光影/景深速查表（完整中英对照表已抓取，进 references/cinematography.md）
- 景别 10 档（EWS→ECU + OTS + Establishing）；机位 7 种（平视/仰/俯/顶视/荷兰角/POV/航拍）
- 光影 14 种（三点布光/伦勃朗/顶光/逆光剪影/侧逆光/硬光/柔光/低调/高调/黄金时刻/蓝调时刻/霓虹/动机光/实用光源）
- 景深：浅景深（隔离主体）/深焦（多层信息）

### AI 视频运镜避坑（关键规律）
- **Runway 官方结构**：文生视频 `[Camera] shot of [subject] [action] in [environment]. [supporting details]`；图生视频 `The camera [motion] as the subject [action]`——重点写运动而非重复画面
- **运动五要素**：主体动作/环境运动/摄影机运动/运动风格与时机/方向与速度
- **官方技巧**：肯定句（说要什么）；避免矛盾指令；过长多段提示反而不自然；时序用 `X occurs, then Y. Finally, Z` 或时间戳；防乱切加 `Continuous, seamless shot`；锁机位 `The locked-off camera remains perfectly still`
- **通用崩坏规律**：运动越快、运镜越复合、时长越长，崩坏概率越高。**最稳 5 种**：慢推、慢拉、慢摇、固定机位+主体动、轻微横移；一切复合运镜（dolly+zoom、orbit+push）拆成单运动
- **高风险运镜降级方案**：dolly zoom→慢推+后期变速；360环绕→半弧90-180°+固定补镜；长距离tracking→分2-3段尾帧续接；手持→`subtle handheld, slight natural shake`；crash zoom→`slow zoom in`
- **AI 视频两大扣分项**：同一"缓慢推近"连用3次=模板感（每镜指定不同运镜动词）；连续3个同景别=死板（刻意交替景别，AI 默认大量中景）
- 真实电影里 static shot 占比很高——混合 1-2 个"固定机位+主体运动"反而更有电影感

### 短视频（15-60s）叙事节奏与运镜搭配
- **15s 单点爆破**：0-2s钩子→2-12s主体→12-15s记忆点。2-3镜足够。禁忌：缓慢长镜
- **30s 微叙事**：0-3s钩子→3-8s建立→8-22s发展（3-6镜渐快）→22-30s高潮收口。开场"景别跳跃"抓人（大远景直切大特写）；高潮前慢推蓄力，落点甩镜/急变焦卡重拍；结尾拉远留余韵
- **60s 完整三幕**：能量曲线编排运镜——低能量=固定+慢摇；爬坡=跟拍+横移；峰值=快切+甩镜+手持；回落=慢拉+航拍；结尾=静态或推入特写锚定记忆
- **每镜头 1.5-3s；AI 的 5s 素材通常剪掉头尾各 0.5s**（首尾帧质量最差）
- **搭配口诀**：情绪上扬→推/升/环绕；下坠→拉/降/慢摇；紧张→手持/快切；抒怀→固定+浅景深；史诗→航拍/大远景；幽默→急推变焦；转折→甩镜/变焦点
- 音乐重拍=运镜方向反转点；**一段一运镜**，节奏在剪辑台上完成

### 待人工补核（网络阻断）
Veo 官方 prompt guide（cloud.google.com/vertex-ai/generative-ai/docs/video/prompt-guide）、可灵/即梦官方运镜功能清单

---

## 调研三：视频生成技巧 ✅

> 主要来源：Yuyyxz/kling-prompt-engineering（MIT，26 文件方法论）、snubroot/Veo-3-Prompting-Guide（323★）、heloraai/Seedance2.0-Prompt-Optimizer-skill（362 条高分提示词提炼）、modelstudioai/awesome-happyhorse-prompts（百炼官方 Skills 仓库）、FunAudioLLM/CosyVoice 官方仓库。Runway/Google/Pika 官方文档被网络封锁，相关结论来自社区转述并标注。

### 提示词通用结构模板（skill 核心规则素材）

**I2V 骨架（核心原则：源图承载状态——图已说明"长什么样"，prompt 只写图里看不到的）**：
```
保持[人物面部/发型/服装/背景]不变。只有[运动]变化。
[主体]从[起始状态]经过[物理路径]到[明确终点状态]，[速度曲线]。
镜头：[一个运动或锁定]。光线：[来源+方向+保持一致]。声音：[环境音+动作音效]。
约束：无文字、无水印、[不能变的东西]。
```

**带音频模型扩展公式**：
- Veo 8 要素：主体→情境→动作→风格→镜头→构图→光影→音频（全 8 项=大师级）
- 即梦 SCELA：Subject/Camera/Effect/Light/Audio 独立分段
- HappyHorse 五要素：场景+主体+动作+音频+品质修饰，总长 150-300 字（i2v 则 30-60 字）

**反空话铁律**（强推荐写入 skill）：一个词若不能被摄影机、麦克风、测光表或秒表检测到，就改写。"电影感/史诗感/8K/氛围感"→拆成具体景别+运动+光线+色调；否定词只在约束槽用——提到缺陷就是在召唤它。

### 痛点 a（首帧动作突兀）解法
- **首帧选"蓄力瞬间"而非动作高潮**：❌跳到半空最高点（模型只能往下落）；✅站在跳板边缘身体微微前倾手臂展开（有势能，可覆盖起跳→腾空→入水）
- 好首帧五条标准：①构图完整但不是"最终画面" ②运动中性——有势能但不锁定方向 ③Lead Room——面朝方向留 2/3 空间 ④身份清晰可辨（脸别被头发挡） ⑤与下一段光线/色调一致
- prompt 声明起始状态+缓入："从静止开始逐渐加速"；状态层三段式：起始帧→过渡→终止帧
- 首帧若已是动作中段（改不了图时）：续写思路——"男子正处于奔跑中途，继续加速冲向…"

### 痛点 b（动作物理合理性）解法
- **动作三段式**：状态层（从X→经过Y→结束于Z）+ 运动层（速度曲线：缓入/缓出/加速/急停+方向"从左向右"）+ 节奏层（节拍锚点，5s 最多 3 个）
- **每个动作必须有终点**（高频翻车点）：只写"一只手伸向杯子"→手悬空停住；必须写"五指合拢握住玻璃杯，缓慢提起离开桌面。结束画面：杯子悬空，指关节发白"。写完问自己：最后一帧长什么样？
- **时长=信息容量硬约束**：5s=1 个动作节拍，10s=1 动作+1 反应，15s≤3 节拍。塞多了全变"闪帧"，宁可拆段
- **打斗动作写法**：慢动作给模型更多帧；单肢体单动作；避免物体交互；打斗三段式"蓄力→爆发→余波"，镜头随动作变：蓄力仰拍/慢推、爆发环绕快切、收束特写慢退
- **防变形/穿模**：面部保持两条件不可兼得——镜头不太近 AND 运动不太剧烈；近景必配锁定/极慢推进；手部简化或遮挡（"双手自然放在桌面""手插口袋"）；物理现象给方向词+具体物理动词（"蒸汽自然上升，缓慢消散"）
- **矛盾检查**：一个维度只能一个值——所有速度词拎出来只能留一个、所有光线词只能一个。矛盾时模型随机选边=不可控

### 痛点 c（分段色调不一致）解法
- **风格圣经（style bible）**：一行固定风格 token（"暖色调，35mm 胶片质感，轻微颗粒，饱和度中等偏低"），每段 prompt 逐字复制
- **帧传递链**：镜头 N 的尾帧直接作为镜头 N+1 的首帧（同一张图，非"类似"）；光线连续（上段结尾黄昏侧光，下段开头不能是正午顶光）
- **光线显式锁定**：每段写"光线方向和色温从头到尾保持一致"——模型中途变光线的根因是没给方向
- **首尾帧变化量预算**：5s 内位移≤3-5 步、转身≤180°、光线≤一个色温档；"一个主要变化+一个次要变化"；不能换场景/换衣服；首尾帧用同模型+同角色卡+同 seed 生成
- 兜底：剪映后期统一调色/LUT（分段一致性最终靠后期调色最稳）

### 痛点 d（跨片段音色不一致）解法
- **关键事实**：音频不跨片段连续——每次生成独立处理音频，多段统一配音必须放后期
- **推荐工作流**：视频模型只生成画面+环境音（或每段台词用完全相同的音色描述句），人物语音统一用 TTS（CosyVoice）批量生成后在剪映对轨
- **若坚持模型直出台词**：音色描述逐字复用同一句（"[角色，普通话，低沉温和的青年男声]"）；台词≤15 字，超了拆镜头；口型同步用锁定中近景+嘴部动作小+无头部转动+无音乐
- **CosyVoice 官方机制**：add_zero_shot_spk 注册命名说话人 → save_spkinfo 持久化 → 后续调用同一 spk_id；zero-shot 用同一段 prompt_wav+prompt_text；固定 seed+固定 pitch 提升跨次一致性；长文本拆句逐句合成、每句同一 prompt_wav 锚定（比一次长文本更稳）；开源版长文本前后一致性无保证（issue #1823：阿里云商业版有保证）

### 痛点 e（画面单一死板）解法
- **最小活力公式**："画面像壁纸"的修复 = 加一个缓慢镜头运动 + 一个自然变化（窗帘飘动/光斑移动/蒸汽上升）
- **微动作编排**：保持模式下给 3-4 个按时间顺序的微动作（"眨眼一次，视线微微下移，手指轻触杯沿"）；微表情替代大表情
- **环境动态层**：粒子/蒸汽/风向显式指定（粒子要有生命周期）；背景人物继续自然活动制造纵深
- **光影氛围显式化**：清晨柔光/黄昏逆光/夜晚霓虹/阴天漫反射——光影精准则画面层次立即拉开
- **能量曲线**：用能量标记设计节奏（▁▁▁▁▇ 长蓄力爆发 / ▇▅▃▂▁ 消退），声音跟随能量曲线

### 痛点 f（运镜单一）解法
- 中文运镜词表（Seedance vocab）：推/拉/摇/移/跟拍/环绕/航拍/手持跟拍/希区柯克变焦；节奏词：慢动作/快切/延时/一镜到底/升格/卡点/子弹时间；焦点词：浅景深/焦点转移/选择性对焦
- **每镜头一个运动方向**：多个运动指令=镜头乱舞；HappyHorse 段内串联写法："镜头快速横摇跟随他冲过画面**转为**侧面跟拍"
- **运镜要有动机**（362 条高分案例规律）：蓄力仰拍慢推、爆发环绕快切、收束特写慢退
- 5 种组合模式：定锚式/递进式（推→跟→锁定）/对比式/揭示式（缓推先藏后露）/跟随式

### 音频控制（带音频生成模型）
- **对白格式**：冒号格式 `角色看向镜头说："台词。"`（防自动字幕）；引号内配情绪注释
- **台词长度**：8 秒规则——一句台词自然说完 ≤8s；15 字以上拆镜头；太短（单字"好"）会出静音/乱音
- **BGM/音效控制**：显式写环境音覆盖模型自动配乐；HappyHorse 背景音效受 prompt 控制可关闭；音效具体化公式：什么物体+什么动作+什么材质=什么声音（"雨滴打在铁皮屋顶上的密集声"而非"雨声"）；静音也是设计——显式写"静音"比不写有效
- **声音三层模型**：环境音层（空间感）+动作音效层（时间感）+情绪音乐层（写乐器/节奏/BPM，不写"悲伤的音乐"）
- **防字幕**："no subtitles, no on-screen text"/"画面严禁出现任何文字"

### 主流模型 prompt 结构对比（进 references/models.md）
| 模型 | 结构 | 差异点 |
|---|---|---|
| Runway Gen-4 | i2v 仅运动描述 | 必须有输入图；prompt 只写 motion，<1000 字符；Turbo 草稿→Gen-4 成片省钱流 |
| Veo 3 | 8 要素全描述 | 原生音频写进 prompt；对白冒号格式防字幕；物理模拟词友好 |
| 可灵 Kling | 谁+镜头+光线+声音+约束 | 反空话文化最强；首尾帧控制力最高；技术术语英文+对话用角色语言 |
| 即梦/Seedance | SCELA 五段 | @图片N/@视频N 引用体系（运镜复刻/视频延长）；自然语言流畅叙事优先于时间戳 |
| HappyHorse 1.1 | 五要素+@图片参考 | 原生音画协同；R2V 九宫格故事板多镜头直出；i2v 极简 30-60 字 |

**共性**：主体→动作→环境→镜头→光影→风格→（音频）→约束的顺序；具体动词优于形容词；每维度单值；约束放结尾。

### 未获取一手资料（网络封锁）
Runway help center、Google Veo 官方文档、OpenAI Sora 指南、Pika 官方文档——相关结论来自社区转述已标注。Seedance 官方飞书文档两链接未直接访问。

---

## 调研二：图片真实感技巧（去AI味/构图/一致性）✅

> 主要来源：OpenAI 官方公告提示词范例、community.openai.com 论坛专题帖（Daller 万图实测长贴、_j DSLR 写法、一致性与真实感专题）、Midjourney 官方文档、StudioBinder、优设/CSDN/SegmentFault。均为一手原文。

### 核心方法论：描述"这张照片是怎么被拍出来的"（证据强，官方亲自示范）
- 官方示例句集（可直接抄结构）：
  - "shot on 35mm film. Natural imperfect framing, visible grain, ambient light, muted colors"
  - "shot on a compact point-and-shoot camera with direct flash... the unmistakable look of an early-2000s flash photograph"
  - "shot on a medium-format analogue camera using colour film, 85 mm f/4... realistic, authentic, imperfect, and natural"
  - "A photorealistic iPhone photo... taken casually by someone at the table. Half-finished drinks, uneven sunlight, relaxed posture, slightly imperfect framing"
- 社区高赞 DSLR 模板："This is a photograph taken with a modern DSLR camera with a 35mm portrait lens, and subtle fill flash... The image contents are..."（第一句定义拍摄方式，第二句起描述内容）
- **环境瑕疵感词汇**：uneven sunlight / half-finished drinks / wind in clothing and hair / lived-in documentary photograph / slightly imperfect framing / visible grain / natural skin texture

### 官方/实测避坑（证据强）
- **不要写 "photorealistic / hyperrealistic"**——会触发"画得很像照片的绘画"风格。改用 "a photograph" / 直接给相机参数
- **否定词无效**："no text / don't add" 大概率把被否定的东西画进去。只写要什么（视频模型的约束槽除外）
- **模板效应**：逆光模板（总加背光）、"塑料硅胶脸"模板——解法：脸部细节分层逐项描述（头→脸→嘴鼻），用具体描述覆盖模板
- **复杂度上限约 256 token**；"整体构图"描述优于"物品清单式罗列"；诗意长文无效
- **顺序影响权重**：最重要的写最前，技术参数写最后
- **同会话连生成 3-5 张会噪声放大/风格污染**——分批重开（API 独立请求无此问题）
- "LESS DETAILS" 可部分抑制高频纹理噪声（clone-stamp 重复纹理感）
- 脸部塑料感变通：局部裁剪放大 1024×1024 再编辑能显著保皮肤纹理
- 分层提示词法：## Pose and Style / ## Clothes / ## Realism Layers / ## Camera and Lighting 分节写

### 摄影词汇表（中英对照，进 references/realism.md）
- 景别/机位：EWS→ECU 全套 + OTS + POV + 仰/俯/斜角 + 鱼眼/微距/移轴/远摄 + 具体焦段光圈（85mm f/1.4 / 35mm / 24mm f/11）
- 光线质感：natural window light / golden hour / Rembrandt lighting / rim light / fill flash / direct flash / shallow DOF / creamy bokeh / 35mm film / medium-format colour film / Kodak Portra 400（社区常用）
- 色调：muted colors / low saturation / warm highlights, desaturated shadows / teal-and-orange / color grading
- 构图：rule of thirds / leading lines / frame within a frame / negative space / **foreground occlusion（前景遮挡——破"证件照"感最有效）** / off-center / layered depth / natural imperfect framing / selective focus（对抗"处处清晰=AI感"）
- 破证件照组合拳："medium shot, off-center, shot through foreground foliage"（避免 "portrait" 单独出现，会默认头像式构图）

### 人物一致性（痛点 A3）
- **参考图 > 文字**（官方：2.5 专门强化参考图人物跨场景保真）；API `/v1/images/edits` 多图输入
- **角色设定表**：先单独生成三视图/白底干净半身照（纯白背景防止背景被学成人物特征），再作参考图垫图（社区称一致性 30-40%→90%+，经验值）
- **固定描述锚定**：发型/发色/脸型/年龄/服饰/标志性配饰写成固定词组，每次生成逐字复制在提示词**开头**（开头权重最高），只改结尾动作场景
- **参考图用途声明**：给 1-2 张人物参考照并在语言里点名用途（官方示例："Use the input photos only for each person's identity"）；多人混淆时把多人合成一张参考图
- input_fidelity=high 只适合复刻原图（锁脸锁logo），做变化别用
- **已知短板**：多人物场景身份保持差于单人；发型/比例/服装细节仍会漂移，Logo 小字必漂移需手修；长会话（12+张）后参考图"失忆"——分批新开+每次重传

### 场景一致性
- 三视图空间锚定（正/俯/侧）约束空间漂移与透视不稳
- 2.5 强项：保持机位、透视、裁切、物体位置的编辑
- **锁定式提示无效**：堆 "HARD LOCK / MAKE NO CHANGES" 反而分不清主次——先锁姿态构图，再分步加编辑
- **避免"编辑已生成图"换场景**：每编辑一次累积一次伪影（第3代起明显）——"人物+场景"直接一次多参考图生成，优于先出人物图再改背景（这条直接决定我们情景图阶段的生成方式）

### 色调一致性
- **统一风格后缀**：每条提示词结尾拼同一段风格串（社区通用公式）
- **色调锚定词写具体**："color grading: warm highlights, slightly desaturated shadows" 优于 "beautiful colors"——模糊词是"倾向"，精确图形词才是锚点
- 颜色"感染"效应：主体颜色会散射影响整体对比与阴影；色调词在不同位置重复出现以加权

---

# 调研完成汇总（5/5）

| 调研 | 状态 | 核心产出 |
| --- | --- | --- |
| 一：社区 Skill 与规范 | ✅ | 五文档契约、连续性锁、GATE 确认点、Module Map、SKILL.md 规范 |
| 二：图片真实感 | ✅ | "描述照片怎么拍的"方法论、去AI味词汇表、人物/场景/色调一致性策略 |
| 三：视频生成技巧 | ✅ | I2V 骨架、首帧蓄力理论、动作三段式、分段一致性、音频控制 |
| 四：模型栈档案 | ✅ | happyhorse/gpt-image/cosyvoice 档案卡与未证实清单 |
| 五：电影运镜库 | ✅ | 20 运镜、景别机位光影速查、AI 避坑、短视频节奏模板 |

## 调研三：视频生成技巧（首帧动作/物理合理性/一致性）⏳ 进行中

## 调研四：模型栈档案（happyhorse / gpt-image-2.5 / cosyvoice）⏳ 进行中

## 调研五：电影运镜知识库 ⏳ 进行中
