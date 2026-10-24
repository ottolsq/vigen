# 提示词规则（骨架 / 必填槽位 / 校验）

> 写任何图片或视频提示词之前读本文件。核心原则：**完整但不越界**——每个职责维度必须有明确描述（留白=不可预期=画面不符预期），但各阶段职责边界之外的描述必须省略（重复=干扰模型）。

## 一、图片提示词骨架

### 0. 角色视觉锚定资产（阶段2，每角色一组，gpt-image 文生图）

**三层分工架构**（参考图的底层逻辑：AI 识别的是像素/轮廓/色彩/五官比例/形体结构，不"读懂"图里的文字与分区——所以给 AI 的图必须信息精准单一，文字约束放提示词，拼贴卡留给人看）：

| 层 | 载体 | 用途 |
| --- | --- | --- |
| 视觉锚定层（给 AI） | 拆分的干净锚定图：白底三视图（主锚，锁全身形体）+ 面部特写锚定图（锁脸）+ 按需 1-2 张细节图（表情板/服装细节） | 所有情景图/视频生成的参考图输入 |
| 文字规则层（给 AI） | 锚定短语逐字段落（02_锚定表），固定粘贴在每条提示词相关位置 | 文本层面约束固定特征 |
| 人工参考层（给自己） | 完整拼贴式设定卡（含分区标注、色卡、文字说明）| 核对生成结果、统一全片人设的制作规范手册，**不喂给 AI** |

**为什么拆分而不整卡上传**（拼贴卡单独当参考图的实证缺陷）：
- 分割线/边框/文字标注/网格会被当作画面特征学习——轻则杂线色块，重则表情格的小脸被当成不同人物（串脸）
- 小格子里的表情/服装细节占比太小，AI 提取不到有效五官与花纹信息
- 图中文字（"身高170""左脸有痣"）AI 视觉模型不读取——这些信息必须放提示词（我们的锚定短语机制正是干这个的）

#### 0a. 白底三视图（主锚，写实人物必做）

一张图内 正面全身 + 侧面全身 + 背面全身，**严格自然直立或 T-pose、统一光线统一比例**：

```
[媒介句] A character three-view reference sheet, flat even studio lighting.
[锚定描述] {年龄/性别/体型/脸型/发型发色/服饰/标志性特征——固定文字，与锚定短语完全一致}
[版式] three-view reference sheet: front view, side view and back view of the same character standing in a relaxed neutral pose, full body, side by side, evenly spaced, equal height
[一致性强调] same person in all three views, consistent height, hairstyle, outfit and details across views
[背景] 纯白背景，无分割线、无边框、无道具、无文字标注
[质感] natural skin texture, visible pores, realistic and imperfect
```

规则：
- **无分割线、无网格、无文字**——多余元素会被当特征学习（也是 happyhorse 文字渗透的防御）
- 一致性强调句必写：三视图互相不一致，这张卡本身就是污染源
- 生成后裁出三个视图分别存 assets/（{角色}_front.png / _side.png / _back.png）；整张也存档
- **白底三视图的优势**：无背景干扰（100% 注意力在人物）、每视图信息精准单一（形体/服装/发型三角度稳定提取）、全身完整入画（脸/躯干/四肢/服装权重均匀，不出现"只锁脸不锁身体"）。多角度运镜稳定性公认高于拼贴设定卡

#### 0b. 面部特写锚定图（写实人物必做，锁脸专用）

三视图脸部占比小，特写镜头需要独立的脸部锚：

```
[媒介句] A head-and-shoulders portrait reference photo, medium-format camera, 85mm f/2, flat even studio lighting.
[锚定描述] {锚定短语中的头部要素逐字：年龄/脸型/发型发色/五官特征}
[构图] 正面平视，头部完整居中，表情平静，纯白背景
[质感] natural skin texture, visible pores, realistic and imperfect
```

#### 0c. 按需补充锚（可选，每角色 ≤2 张）

- **表情板**：`expression studies sheet, same face: neutral, smiling, sad, angry, front view, plain white background`（面部特写镜头多的项目）
- **服装细节图**：全身像中对标志性服饰/配饰的单独特写（花纹复杂的服装）

#### 选型速查

| 项目类型 | 资产组合 |
| --- | --- |
| 写实人物（有侧/背镜头） | 三视图 + 面部特写（+按需表情板） |
| 写实人物（纯正面镜头） | 面部特写 + 白底正面全身（从三视图裁或单独拍） |
| 产物/动物主角 | 白底正面图（+按需侧/背视图） |
| 任何项目 | 人工参考层的拼贴设定卡（给用户自看，不喂 AI） |

### 1. 人物参考图（阶段2，gpt-image 文生图）

```
[拍摄媒介句] A character reference photo shot on medium-format camera, 85mm f/4, soft even studio lighting.
[主体锚定描述] {年龄/性别/体型/脸型/发型发色/服饰/标志性特征——写成一段固定文字}
[构图] 正面全身像，自然放松站姿，纯白背景，人物完整居中
[质感] natural skin texture, visible pores, realistic and imperfect, no plastic sheen
```

规则：
- **纯白背景**——防止背景被模型学成人物特征
- 主体锚定描述即该角色的**锚定短语**，生成后原样存入 02_锚定表，后续所有图/视频提示词逐字复用
- 不写"photorealistic"（触发绘画模仿风格），用相机参数表达真实感
- 本骨架用于产物/动物主角；写实人物走骨架 0（三层资产）。有侧/背镜头的情景图，参考图除正面锚定图外**必须加对应视图**（gpt-image 多图参考：image 1 三视图或正面锚定、image 2 场景图、image 3 侧/背视图——用途声明相应扩展）；特写/近景镜头**加面部特写锚定图**

### 2. 场景参考图（阶段3，gpt-image 文生图）

```
[拍摄媒介句] {见 realism.md 媒介句库，按风格选}
[场景全貌] {空间结构/主要道具/材质/生活痕迹：没喝完的杯子、搭着的毛毯、风吹动的窗帘——至少 2 处}
[光线] {时段+方向+色温，如"傍晚从左侧窗户斜射入内的暖橙色光，色温偏暖"}
[景深层次] {前景：...；中景：...；背景：...}
[风格圣经后缀] {02_锚定表中的风格圣经，逐字}
```

规则：
- **生活痕迹（lived-in）是去AI味的关键维度**——空干净的房间=AI感
- 光线的时段/方向/色温三要素齐全，此描述将被情景图与视频提示词引用（光线锁定链）

### 3. 情景参考图（阶段4，gpt-image 多图参考：人物锚定图+场景锚定图）

```
[参考图用途声明] Use image 1 only for the character's identity and appearance. Use image 2 only for the scene environment and lighting.
[拍摄媒介句] {与场景图同款或同风格}
[主体位置] {锚定短语逐字}，{在场景中的具体位置与朝向}
[动作起点] {蓄力瞬间描述：有势能但不锁定方向}
[景别/机位/构图] {如"medium shot, off-center composition, shot through foreground foliage（前景遮挡）"}
[光线] {与场景图同时段同方向}
[风格圣经后缀] {逐字}
```

规则：
- **一次多参考图生成，绝不编辑已生成的图换场景**（每次编辑累积伪影）
- **蓄力瞬间五标准**（此图即视频首帧）：①构图完整但不是"最终画面" ②有势能但不锁定方向（坐沙发边缘前倾✓，陷进沙发深处✗）③面朝方向留 2/3 空间（Lead Room）④身份清晰可辨（脸不被头发/前景挡）⑤与下一镜光线一致或有合理变化路径
- 构图用"偏心+前景遮挡"组合防证件照感；"portrait" 单独出现会默认头像式构图，必须搭配景别机位词
- **画面中不得出现任何文字、水印、logo**（正向表述：保持画面干净无文字元素）——happyhorse 会把参考图上的文字渲染进视频

## 二、视频提示词骨架（按模型分轨——两轨语法完全不同，禁止混用）

> 轨道选择：02 锚定表记录的视频模型。happyhorse → A 轨（中文）；MiniMax-H3 → B 轨（英文结构化）。选轨前 Read references/models.md 对应档案。两轨共用的规则：动作三段式、单一运镜、动作终点、时长容量、质感锚定（B 轨质感锚定写进三段式正文的风格部分）。

### A 轨：happyhorse（中文）

#### A1. i2v 精简型（默认路线）

```
[不变声明] 保持人物与背景不变。
[动作三段式] {主体}从{起始状态}，{过程：2-3个具体动词+速度曲线}，至{明确终点状态}。
[运镜] 镜头：{运镜槽——固定机位写"固定机位"；运动运镜必用平滑模板（见下），禁止裸写运移动词}。
[音效] 声音：{环境音+动作音效}，无背景音乐。
[质感锚定] {一行紧凑质感词，从项目风格圣经压缩，必含三项：介质质感+自然皮肤纹理+自然运动模糊}
[约束槽] 画面严禁出现任何字幕/水印/logo。
```

规则：
- **运动运镜平滑规则（V1.4，实测反馈）**：含运动的运镜（推/拉/移/跟/环绕）易帧间抖动——AI 无物理惯性，每帧相机位置独立采样。三层防御：①运镜必带"缓慢匀速平滑"+英文平滑锚定词，模板：推=`镜头缓慢匀速平滑推近（slow smooth dolly in）`、拉=`镜头缓慢匀速平滑拉远（slow smooth dolly out）`、横移=`镜头缓慢匀速平滑横移（slow smooth tracking shot）`、跟拍=`镜头如稳定器般平滑跟随（smooth steadicam follow）`、环绕=`镜头以缓慢平滑的弧线环绕（slow smooth arc）`；②镜头动则主体动作放缓、主体动则镜头固定/极慢（双高速=双抖动源）；③抖动敏感内容（特写/人脸）优先固定机位。完整规则见 cinematography.md 二·五节
- **长度调和规则（V1.7，消除与 models.md 的表述冲突）**：官方最优区间 **30-60 字**针对的是**核心三要素**（动作三段式+运镜+音效）——这三部分合计不注水、不超 60 字的纪律不变。V1.1 质感锚定行（约 15 字）与 V1.4 平滑运镜模板（运镜槽变长）是**结构性附加槽**，加满后全条 100-160 字属正常水平，不算违反"极简"。红线只有一条：**绝不回填外观/服装/背景描述**——长度超标若因外观描述回流，立即删。
- **绝不描述外观/服装/背景**——首帧图已承载，文字重复反而干扰。**质感锚定不属于外观描述**：外观=身份/服装/背景（干扰合成），质感=渲染质量方向（抑制 AI 塑料感/油光/数字锐化——HappyHorse 官方推荐"提示词末尾加风格限定词统一质感，避免塑料感"）。实测教训（V1.1）：图片端无油腻但视频端油腻——视频模型不保留首帧像素而是逐帧重渲染，质感维度必须显式声明
- **质感锚定三项缺一不可**：介质质感（"真实胶片质感"）压数字感；主体表面纹理压油光/塑料感——**人物=自然皮肤纹理，物体/动物=对应材质**（"自然毛发纹理""真实玻璃透明质感""冷峻金属质感"），V1.1 回归测试确认的弹性已固化为此规则；自然运动模糊压"逐帧清晰的游戏感"（真实摄像机拍运动必有 motion blur）。词从项目风格圣经同族压缩（治愈柔和→"柔焦胶片质感，低饱和暖调，自然运动模糊"；电影写实→"真实胶片质感，自然皮肤纹理，自然运动模糊"）
- 台词（如有）：`{角色}（{情绪}）说："{台词≤15字}"`，时长按 **4字/秒 × 1.2 情绪倍数** 估算，必须 ≤ 镜头时长；有台词的镜头配"锁定中近景、嘴部动作小、无头部转动"
- 无台词但有表演的镜头：微动作编排 3-4 个按时间顺序（"眨眼一次，视线微微下移，手指轻触杯沿"）
- 音效具体化公式：什么物体+什么动作+什么材质=什么声音（"雨滴打在玻璃窗上的密集轻响"✓，"雨声"✗）
- BGM 显式关闭（"无背景音乐"）——后期统一配乐

#### A2. r2v 四段式（可选路线，跨镜一致性要求高时）

```
① [参考图声明] [Image 1] 为{角色}的人物锚定图，[Image 2] 为{场景}的场景参考图。（[Image 1] 必须带空格，[Image1] 会导致解析失败）
② [风格氛围+角色卡] {风格圣经逐字}；{角色锚定短语逐字}；{质感锚定行——同 i2v 三项}
③ [分镜表演] {时间码分镜 [00:00-00:04] 或叙述体}
④ [全局约束尾段] 角色面部、发型、服装保持一致；台词语速自然，口型与台词同步；画面严禁出现任何字幕/水印/logo。
```

### B 轨：MiniMax-H3（英文结构化语法，2026-10-23 新增）

> 完整语法与参数见 references/models.md B 轨档案。此处只列骨架。**字段名/正文/运镜句用英文；台词/歌词/画面文字保留原语言；`<d>` 标签不可翻译**。

#### B1. I2VA 三段式（首帧模式，H3 默认路线）

提示词第一行放关键帧指令，正文按官方 I2VA 结构（首帧锚定→动作→发展→结果）：

```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
integrated_multimodal_description: [Shot 1] {风格圣经英文化开场：媒介+调色}. {首帧锚定：the scene established in <Picture 1> shows...—只一句，不重复细节}. {主体}（锚定短语英文版逐字）starts from {起始状态}, {过程: 2-3 specific verbs with speed}, until {明确终点状态}. The camera {运镜英文句+幅度速度修饰，如 pushes in with small amplitude at slow speed}. At {MM:SS.mmm}, {镜内动作/台词阶段变化（如需）}. {台词: The {角色} (S1) says: <d>[Chinese] {台词原文}</d>}. {物理词: believable weight, inertia, traction（动作涉及时）}. Avoid AI artifacts, warped limbs, distorted hands, extra fingers, on-screen text, watermarks, logos.
overall_soundscape: {1-4 句英文：具体声源逗号链+动作音效，不重复台词}
non_diegetic_music: N/A
```

B 轨规则：
- **提示词不能太短**（官方六错误之一）：无参考时底线=主体外观+场景+动作+风格；I2VA 虽有首帧也要写全动作发展与声音——与 A 轨"越短越好"完全相反
- **一镜到底不写多个 [Shot]**；镜内阶段变化用 `At MM:SS.mmm`（毫秒三位）
- 运镜用 14 种官方类型英文自然句 + `with small/large amplitude` / `at slow/fast speed` 修饰（幅度+速度修饰即 B 轨的平滑机制）；Static Shot 写 `The camera holds a static shot`
- 负面约束：**无 negative prompt**，正文结尾 ban list（`Avoid AI artifacts, warped limbs, distorted hands, extra fingers, on-screen text, watermarks, logos.`）
- 质感锚定（V1.1 规则在 B 轨的实现）：风格圣经英文化开场承担（`Shot on 35mm film, visible grain, natural skin texture` 等），不必单独一行
- 台词：`(S1)` ID 跨镜头复用；`<d>[Chinese] 原文</d>` 逐字；旁白必须 `while his lips remain completely closed`；标点只留 `, . ? !`；台词绑可见事件不绑时间码
- 环境声：具体声源逗号链（`footsteps, rain, sirens, paint cans clattering`），禁抽象词
- 参数（生成时选，不进提示词）：mode=i2va、seconds、aspect_ratio、resolution 480p/720p、prompt_optimization=false

#### B2. FL2VA 三段式（首尾帧模式——skill"蓄力起点+动作终点"机制的直接载体）

```
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the {S.SS}-second mark of the target video.
integrated_multimodal_description: [Shot 1] {风格开场}. The video begins from the exact pose and framing established by Picture 1. {主体}（锚定英文版）{变化路径：从起点图状态如何运动到终点图状态——写过程，不重复两张静帧描述}. The camera {运镜句}. The video ends settled into the exact pose and composition established by Picture 2. Avoid AI artifacts, warped limbs, distorted hands, extra fingers, on-screen text, watermarks, logos.
overall_soundscape: {具体声源}
non_diegetic_music: N/A
```

- FL2VA 默认**单镜头插值最好**；正文写"变化路径"；想一镜到底显式写 `single continuous shot, no cuts` 且**写两遍**（社区经验）——第二遍换个说法紧跟其后，如 `the entire video plays as one single continuous shot with no cuts`
- 03 情景图须为 FL2VA 每镜生成**起点图+终点图两张**（终点图=动作终点字段的画面化，与起点图同机位同景别同光线；**独立新生成**——起点图+角色锚定图+场景图作多图参考输入，绝不能靠编辑起点图改姿势改出来，伪影累积禁令同样适用；配方见 templates.md 03 模板终点图节）

#### B3. Ref2VA 六段式（多参考+音色参考，跨镜一致性要求高时）

```
subject_definitions:
<Subject 1> is the {人物英文名} whose appearance comes from <Picture 1>.
<Audio 1> is the voice-timbre reference for <Subject 1> (S1).
summary:
[reference generation + audio reference] The target video preserves <Subject 1> and follows the referenced voice timbre.
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - identity and clothing are retained.
<Audio 1>: reference - voice timbre is referenced without copying the signal.
detailed_description:
{350-500 英文词：风格+构图+主体+环境+动作+运镜+声音+参考生效位置}
overall_soundscape: {具体声源}
non_diegetic_music: N/A
```

- 每个上传素材必须一句分工声明（六错误之二）；summary 任务类型：keyframe completion / reference generation / audio reuse / audio reference
- 05 台词表在 B 轨项目下列两条路线：cosyvoice TTS 对轨（主）与 Ref2VA 音色参考（H3 独有，视频直出台词时用）

## 三、必填槽位清单（输出前逐槽自检）

### 图片提示词 11 槽位
| # | 槽位 | 缺省来源 |
| --- | --- | --- |
| 1 | 拍摄媒介句 | realism.md 媒介句库（按风格） |
| 2 | 主体锚定 | 02_锚定表锚定短语（逐字） |
| 3 | 环境细节/生活痕迹 | 按场景主题补（≥2 处） |
| 4 | 光线（类型+方向+时段） | 场景锚定表 |
| 5 | 色调 | 风格圣经 |
| 6 | 构图/景别/机位 | cinematography.md 景别表（避免连续 3 个同景别） |
| 7 | 景深 | 按景别默认（特写=浅景深，全景=深焦） |
| 8 | 质感 | realism.md 质感词（natural skin texture 等） |
| 9 | 参考图用途声明 | 仅情景图（多图参考时必填） |
| 10 | 风格圣经后缀 | 02_锚定表风格圣经（逐字） |
| 11 | 画幅 | 01 整体方案的画幅，写进提示词末尾（如 "Aspect ratio 16:9"）；**B 轨（H3）项目必填**——I2VA 首帧会被拉伸到画布不保宽高比，情景图必须与目标画幅同比例 |

### 视频提示词槽位（按轨道）

**A 轨（happyhorse）i2v 7 槽位**
| # | 槽位 | 缺省来源 |
| --- | --- | --- |
| 1 | 不变声明 | 固定句式 |
| 2 | 动作三段式 | 分镜表的动作设计（起/程/终） |
| 3 | 运镜 | 分镜表运镜（固定机位 或 平滑模板） |
| 4 | 音效 | 场景音景（环境音+动作音效） |
| 5 | 质感锚定 | 风格圣经压缩（介质质感+主体表面纹理——人物=自然皮肤纹理，物体/动物=对应材质+自然运动模糊，三项缺一不可） |
| 6 | 约束槽 | 固定句式（字幕/水印/logo 禁令） |
| 7 | 台词+时长校验 | 有台词时必填（≤15字，4字/秒×1.2） |

**B 轨（H3）三段式槽位**
| # | 槽位 | 缺省来源 |
| --- | --- | --- |
| 1 | 关键帧指令（第一行） | models.md B 轨（按 i2va/fl2va/l2va 模式固定句式） |
| 2 | 风格英文化开场 | 风格圣经英文版（媒介+调色，兼作质感锚定） |
| 3 | 首帧锚定句 | 一句话引用 <Picture 1>（不重复细节） |
| 4 | 动作三段式（英文） | 分镜表动作设计（起/程/终）+ 物理词 |
| 5 | 运镜英文句 | 14 种官方类型 + 幅度/速度修饰 |
| 6 | 台词（如有） | (S1) ID + <d>[语言] 原文</d> 逐字 |
| 7 | ban list | 固定句式（Avoid AI artifacts, warped limbs...） |
| 8 | overall_soundscape | 具体声源逗号链（1-4 句英文） |
| 9 | non_diegetic_music | N/A（后期配乐）或配乐描述 |

**任一槽位为空 → 先补默认值再输出，不留白。**

## 四、校验规则（输出前全部通过）

1. **单值规则**：把所有速度词拎出来（快速/缓慢/匀速只能留一个）、所有光线词（正午/黄昏只能一个）、所有景别词（中景/特写只能一个）。矛盾时模型随机选边=不可控
2. **动作终点检查**：每镜自问"最后一帧长什么样"——答不出=动作无终点=重写
3. **容量检查**：5s=1 动作节拍，10s=1动作+1反应，15s≤3节拍；A 轨台词按 4字/秒×1.2 估时；B 轨台词逐字保留模型自动匹配语速，但台词量仍受节拍约束
4. **反空话**：逐词过一遍——能被摄影机/麦克风/测光表/秒表检测到吗？"电影感/史诗感/8K/氛围感/高质量"→改写成景别+运动+光线+色调的具体组合
5. **风险运镜降级**：分镜用了 dolly zoom / 360°环绕 / 长距离跟拍 / crash zoom → 套用 cinematography.md 降级表
6. **锚定逐字校验**：对照 02_锚定表，锚定短语和风格圣经在每条提示词中逐字出现（复制粘贴，不是"意思相同"）；A 轨用中文版、B 轨用英文版（锚定表双语的对应侧）；视频提示词的质感锚定行必须与风格圣经的质感词同族（治愈柔和风格不能配"冷峻锐利"质感）
7. **图片正向表述**：图片提示词中无否定词；A 轨视频否定只出现在约束槽；B 轨负面概念统一进正文 ban list
8. **轨道隔离**：B 轨提示词中不得出现 A 轨语法（中文运镜句、[Image N]、中文约束槽句式）；A 轨提示词中不得出现 B 轨语法（[Shot N]、At 时间点、<d>、<Subject>/<Picture> 标签）
9. **画幅一致性**：图片提示词末尾的画幅槽与 01 整体方案一致；B 轨（H3）项目情景图/首帧图与 aspect_ratio 参数同比例（I2VA 拉伸不保宽高比）
