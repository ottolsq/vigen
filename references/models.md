# 模型档案（2026-10 调研快照）

> **确定模型时读本文件**，按档案选提示词轨道。**各视频模型"癖好"完全不同，提示词语法/语言/结构/负面机制绝不能混用**。更换模型时只更新本文件，核心流程与骨架不变。未证实参数一律不使用。

## 轨道总览（视频模型选择器）

| 模型 | 提示词语言 | 结构 | 负面约束方式 | 独有模式 |
| --- | --- | --- | --- | --- |
| happyhorse-1.1 | 中文 | i2v 极简 30-60 字 / r2v 四段式 | 结尾约束槽禁令 | — |
| MiniMax-H3 | 结构化语法用英文（台词/歌词/画面文字保留原语言） | 三段式 / Ref2VA 六段式 | **无 negative prompt**，正文 ban list | fl2va（首尾帧）/ l2va（尾帧）/ ref2va（9图+3音频，含音色参考） |

## 图片模型

### gpt-image-2（OpenAI，2026-04）
- 模式：文生图 / 图生图 / 多图参考
- API 内最高 2K 分辨率；宽高比最宽 3:1（宽高比直接写进提示词，如 "Aspect ratio 16:9"）
- 提示词风格：长句自然语言（官方示例全为叙事长句）；官方定位 "smarter images with less prompting"——维度全覆盖即可，不必堆砌
- 多图参考：无权重/顺序参数，靠提示词声明每张图用途（"Use the input photos only for each person's identity"）
- 已知缺陷：物理世界模型类任务失败（折纸/魔方类）；极致密集细节；图上文字标注
- 行为要点：**否定词无效**（"no text" 会把文字画进去）——一律正向表述；训练数据带 EXIF，镜头词（18mm 广角等）确实改变视野但是"建议"不是精确光学

### gpt-image-2.5（OpenAI，2026-10，Flare/Sunburst）
- 模式：文生图 / 参考图驱动生成与编辑 / 透明背景 / 多轮编辑
- Flare：默认（快，比 2.0 延迟低 50%）；Sunburst：编辑精度优先（慢）。精确 API id 未公布，使用前控制台核对
- 相对 2.0 改进：**参考图人物保真度提升**（正是我们多图参考工作流的依赖）、"understands what not to change"（只改指定元素保住其余构图）
- 编辑类任务：把"要改什么 + 保持什么"都写明
- 注意：复杂度上限约 256 token 有效；同会话连生成 3-5 张会风格污染（API 独立请求无此问题）

## 视频模型 A 轨：happyhorse-1.1-t2v / -i2v / -r2v（阿里百炼 DashScope，中文轨道）

- duration 3-15 秒；size 写法 `1920*1080`（`1080P` 写法已废弃）；语言：中/英/日；异步任务轮询
- **t2v 提示词偏好**：支持超长 prompt（2500 字符后指令遵循度显著提升）；推荐结构：总述（时长/风格/画质）→ 角色设定 → 时间码分镜 `[00:00-00:04]` → 音频/对白段 → 全局约束尾段；总长 150-300 字常规最优
- **i2v 提示词偏好**：首帧已含画面信息，**prompt 绝不描述外观/服装/背景**；最优区间 **30-60 字**，聚焦三要素：动作 + 运镜 + 音效（复杂武打可放宽到数百字）
- 1.1 相对 1.0 修复：动作偏慢、面部油光、过度锐化；运动建模与帧间时序一致性增强
- 音频控制（纯提示词层，无 API 参数）：背景音效可关闭（"无背景音乐"）；台词语速停顿随情绪自然变化
- 对白格式（任选）：`[女人/低声/克制/"你写了一夜。"]`（标签式）/ `她开口：「我……终究是错付了。」`（嵌叙式）
- **口型同步规则**：台词语言匹配文化（日漫场景用日语）；时长 = 4字/秒 × 1.2 情绪倍数；每段时间窗台词 ≤2 句口型触发率最高；无台词段用 `[角色/沉默/情绪/无台词]` 占位防"加戏"；12s 单段 ≤32 字，15s ≤40 字
- **文字渗透风险**：对参考图忠实度极高，会把图上的文字/水印渲染进视频——参考图提交前确保无文字 + 约束槽禁令
- 已知问题：时间码执行过于字面化（单人情绪戏用松绑叙述更自然）；同 prompt 重抽差异大（择优必要）；真实国家/民族对抗描写触发内容安全拦截
- r2v 多图参考（1-9 张，跨镜一致性利器）：`[Image 1]`~`[Image 9]` 引用（**[Image 1] 必须带空格**，[Image1] 解析失败）；四段式：①每张图用途声明 ②风格氛围+角色卡 ③分镜/表演 ④全局约束尾段；多段连续叙事段首加"延续上段：[站位/手部/光线/道具状态]"

## 视频模型 B 轨：MiniMax-H3（英文结构化轨道，2026-10-23 调研）

> 经 easyframe 网关直连（无 Context-IR 中间层）→ **必须用官方结构化语法**。托管 API/海螺 App 走自然语言即可（官方 Feature Highlights 全是自然语言），但本 skill 统一按结构化语法产出（直连场景必用，且对托管 API 兼容）。

### 基本参数（easyframe 网关）
- model：minimax-h3-mini / -fast / -base（pro 暂未开放，503）；mode：t2va / i2va / fl2va / l2va / ref2va；resolution：480p / 720p；seconds：5-15 整数；aspect_ratio：16:9 / 9:16 / 1:1 / 4:3 / 3:4 / 21:9 / 9:21 / 4:5 / 5:4
- 提示词上限：单文本项 7000 字符、合计 30000；`prompt_optimization=false` 时**逐字传递**（与锚定逐字原则契合，必须 false）
- **视频留存 24h、下载 URL 1h 有效——生成后立即转存**
- **I2VA 首帧图会被拉伸到画布（不保宽高比）、尾帧图居中裁剪——参考图必须与目标画幅同比例**
- 媒体限制：图 ≤9 张、音频 ≤3 个、合计 ≤12；图片单张 ≤20MiB、超 8MiB 或长边超 2048px 自动缩放转 JPEG；**参考视频不支持**（422 拒绝）
- 异步：POST /v1/videos → GET /v1/videos/{id} 轮询；240s 强制供给期限

### 提示词结构（官方 h3-prompt-writing 语法）

**三段式（T2VA / I2VA / FL2VA / L2VA）**——字段名与正文用英文，台词/歌词/画面文字保留原语言：
```
integrated_multimodal_description: [Shot 1] {正文：视觉+动作+镜头+对话+画内声音，按时间线}
overall_soundscape: {1-4 句英文：环境声+动作声+非语言人声，具体声源逗号链，不重复台词；全片静音才写 N/A}
non_diegetic_music: {N/A 或 1-3 句英文配乐：乐器/速度/节奏/动态}
```

**Ref2VA 六段式**（多参考：图+音频）：
```
subject_definitions: <Subject 1> is the {人物} whose appearance comes from <Picture 1>. {每个素材一句分工声明——上传素材没写用途是官方六错误之一}
summary: [reference generation + audio reference] {任务类型：keyframe completion / reference generation / audio reuse / audio reference}
retention_analysis: <Subject 1> (appears in [Shot 1]): fully_preserved - identity and clothing are retained.
detailed_description: {350-500 英文词：构图/主体/环境/动作/运镜/声音/参考素材生效位置}
overall_soundscape: ...
non_diegetic_music: ...
```

### 关键帧模式指令（放提示词第一行）
- I2VA：`For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.`
- FL2VA：`How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the {S.SS}-second mark of the target video.`
- L2VA：`How the reference pictures align with the target video — <Picture 1> (from [Shot 1]) aligns with the {S.SS}-second mark of the target video.`

### 镜头与时间体系（与 happyhorse 哲学相反）
- `[Shot 1]` 首镜不写时间；**[Shot N] 只用于真实切镜**（编号连续、切镜时间递增且小于总时长）；镜内动作/表情/台词阶段用 `At 00:02.000, she raises her gaze.`——不切镜
- **想一镜到底就不要写多个 [Shot]**（官方六错误之一）；要一镜到底显式写且社区经验强调两遍（"single continuous shot, no cuts"）

### 台词体系
- `(S1)` 说话人 ID：按首次发声顺序编号，**跨镜头复用同一 ID**；不发声主体不分配；多人共同说话 `(S1,S2)`
- `<d>[Chinese] 台词原文</d>`：逐字保留永不删减/改写/翻译；时长不足模型自动压缩语速（不需要我们手工估时，但台词量仍受节拍容量约束）
- 旁白：确切短语 `says in an off-screen voiceover: <d>...</d> while his lips remain completely closed.`（必须声明闭唇）
- 跨镜语音：切镜前后各放 `<scenetrans>` 并说明声音连续；结尾截断用 `<cutoff>`
- 画面文字（招牌/标签）：英文双引号 `"营业中"` 保留原文
- `<d>` 内省略号损害可懂度；标点只留 `, . ? !`
- 多说话人+音频参考会说错人——台词绑到可见事件而非时间码

### 运镜语法（英文自然句，14 种官方类型）
- Zoom In/Out、Push In/Pull Out、Pan Left/Right、Truck Left/Right、Tilt Up/Down、Pedestal Up/Down、Arc Shot、Tracking Shot、Static Shot、Shake Slightly/Strongly、POV、Roll Clockwise/Counterclockwise
- 写法：自然句 + 幅度/速度修饰——`The camera pushes in with small amplitude at slow speed toward the folded letter.`（中等幅度和正常速度通常省略）
- **幅度与速度修饰本身就是 H3 轨的平滑机制**（对应 V1.4 平滑规则的"缓慢匀速平滑"：写 `with small amplitude at slow speed`）

### 负面约束（无 negative prompt）
- H3 无负分支（cfg=1）——负面概念写正文结尾 ban list：`Avoid AI artifacts, duplicated pedestrians, warped limbs, floating objects, distorted hands, extra fingers.`
- 手部需主动防御（社区普遍堆禁令）

### 官方公式与六错误
- 公式：完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明
- I2VA 正文结构：首帧锚定（先描述图内风格/主体/构图）→ 动作发生 → 连续发展 → 结果或反应；身份/服装/颜色/关键物体/空间关系保持一致
- FL2VA：默认**单镜头插值最好**；正文写"变化路径"而非重复两张静帧描述
- 六错误：①糊成一段无结构 ②上传素材没写用途 ③又要配乐又禁 BGM ④想一镜到底却写多 [Shot] ⑤要脸部一致却不传参考图 ⑥无参考时提示词太短（底线=主体外观+场景+动作+风格）
- 写实技巧：开头钉死媒介+调色（"Shot on 35mm film, dense grain"）；格式指令（"Grainy webcam footage, slightly compressed"）比氛围词（"amateur"）有效；环境声具体声源逗号链（"footsteps, rain, sirens"）
- 物理规律显式要求：`believable weight, inertia, traction`
- **翻译过的提示词跑出来不是同一段片子**——按原语言写；`<d>` 是 tokenizer 特殊 token 不能翻译

### 已知缺陷
- 15s 长时序角色漂移（分段链式；面部纹理最先崩，误差累积）——与"一段一运镜/拆段"规则互证
- 音频收敛晚于视频（语音/音色需更多步数）
- Turbo/蒸馏档伤音频（气声/长音/口音平庸化）、快速运动发糊
- 提示词太短是官方记录在案的失败模式（与 happyhorse i2v 的"越短越好"完全相反）

### 音色参考（Ref2VA 独有，跨段音色一致新解法）
- `<Audio 1> is the voice-timbre reference for <Subject 1> (S1).`
- 音频关系：fully_copy / partially_copy / reference（只参考音色不复制信号）/ weak_reference
- 与 cosyvoice TTS 方案可并存：05 台词表两条路线都列出

## 语音模型

### cosyvoice-v3.5-flash（阿里云百炼，DashScope）
- **音色一致性机制**：复刻音色（voice clone）创建后默认长期有效，保存 voice_id 每次调用传同一个；加固定 seed 可完全复现
- 参考音频要求：10-20 秒（≤60s）、≤10MB、≥16kHz、无 BGM/噪声/其他人声、正常语速
- voice 绑定创建时的 target_model，不能跨模型使用
- 关键参数：format（mp3 默认）、rate 0.5-2.0、pitch 0.5-2.0、instruction ≤100 字符（仅复刻/设计音色）
- 开源版长文本前后音色一致性无保证（拆句逐句合成、每句同参考音频更稳）
- `qwen/` 前缀来自第三方聚合网关；官方渠道模型名不带前缀

## 换模型指引

1. **先问用户用什么模型**（生图/视频/语音三件套），创意里已说明的不重复问；新项目模型记入 01 与 02 锚定表
2. 新模型档案按上述格式追加到本文件（轨道总览表加一行 + 完整档案：能力/偏好/限制/已知问题/关键参数/提示词语法）
3. 视频模型必须有独立轨道：提示词语言/结构/负面机制/台词体系/运镜语法分轨，不得混用
4. 未证实参数标注"未证实"，不写入提示词规则
5. models.md 没有档案的模型：向用户要文档或提示词样例，临时建档再生成，不套用其他模型风格
