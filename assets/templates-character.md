# 人物参考图模板（0a/0b/0c/多人脸对照条/0d）

> 何时读：阶段2-4 写 03 人物参考图时。从 assets/templates.md 拆出（V3.16，控制单文件长度）。
> 默认路径：**0a 合图变体**（左半大幅正脸 + 右半三视图，生成后裁成脸锚/三视图锚两张使用）；0a-0b 分张与单锚派生为退路。规则全文见 consistency 三节 / prompt-rules 0.5。

## 一、人物参考图（阶段2）

### {角色名} · 0a 合图变体（**V3.16 默认**：左半大幅正脸 + 右半三视图）

```
A character reference sheet, flat even studio lighting.
Left half: a large head-and-shoulders portrait of the character, front view, face occupies most of the left half, calm neutral expression, face highly detailed.
Right half: the same character, three-view reference sheet — front view, side view and back view, full body, side by side, evenly spaced, equal height, natural neutral standing pose, arms relaxed at the sides, hands empty.
Both halves must be the same person: same face, same hairstyle, same outfit, same height. {锚定短语的体型/发型要素逐字 + 本套服装锚定短语逐字}。
纯白背景，两半之间留纯白间隔，无分割线、无边框、无道具、无文字标注。
natural skin texture, visible pores, realistic and imperfect。
Aspect ratio 3:2
```

> **生成后裁成两张使用**：左半 → `{角色名}_face.png`（脸部锚）；右半 → `{角色名}_sheet.png`（三视图锚，可再拆 front/side/back）。**喂给下游的必须是裁出的单张**，不喂合图（合图会让模型把"人像+三视图"的版式搬进画面）。
> **脸区必须 ≥40%**：左半正脸占不足 40% 或脸部模糊 → 直接走下方分张退路，不在合图上硬裁。
> **合图内脸/身互相污染**（脸被三视图的小脸平均、服装两边不一致）→ 走分张退路。

### {角色名} · 0a 白底三视图（分张退路——合图变体不适用时）

```
A character three-view reference sheet, flat even studio lighting.
{锚定短语的体型/发型要素逐字 + 本套服装锚定短语逐字；头部只写轮廓与发型，不写眼型/鼻梁/唇形细节——五官细节由 0b 面部特写承担}。three-view reference sheet: front view, side view and back view of the same character standing in a relaxed neutral pose, full body, side by side, evenly spaced, equal height。
same person in all three views, consistent height, hairstyle, outfit and details across views。纯白背景，无分割线、无边框、无道具、无文字标注。
natural skin texture, visible pores, realistic and imperfect。
Aspect ratio 3:2
```

> 生成后裁出三视图分别存 {角色名}_front/_side/_back.png。
> **合图变体的分工**：左半脸部锚只管脸（五官/发式/帽），右半三视图管比例/服装/轮廓；锚定短语里含五官的条目不在三视图展开——三视图小脸画不清那些细节。**分张退路**才有"0a 三视图 / 0b 面部特写"两张分工。
> **画幅**：三视图并排板用 3:2 或 16:9 横构图（竖幅会把三个全身挤成三条）；"全身 2:3 / 大头照 4:5"是裁切后单视图规格。
> **动漫/国漫设定项目**可用四视图合并例外（左侧正脸特写+右侧三视图同图，配方见 cinema-grade-params 二节，脸区占足像素）；写实项目默认合图变体，合图不适用时才分两张。
> **可选单锚派生路径**：高脸漂/多视图项目可把 0a 改成"正面全身锚点"（脸清楚、白底、均光），0b/侧/背/细节从该锚点改图派生；派生图之间不互相参考。规则见 consistency 三节·单锚派生链；默认仍走合图变体（脸区不足时再走分张或单锚）。
> 派生视图/特写用改图技法（prompt-rules 骨架0a）：构图指令放句首/正面几何化（禁 three-quarter）/背面 Rotate 180 只写背面可见物/一致性清单按视图取层/长几何段结尾重申取景/细节部位要小。
> 参考图技术规格：单边 300-5760px、比例 0.4-2.5、≤20MB；全身 2:3 / 大头照 4:5 / 道具细节 1:1。

### {角色名} · 0b 面部特写锚定图（分张退路——合图变体不适用时）

```
A head-and-shoulders portrait reference photo, medium-format camera, 85mm f/2, flat even studio lighting.
{锚定短语中的头部要素逐字}。正面平视，头部完整居中，表情平静，纯白背景。
natural skin texture, visible pores, realistic and imperfect。
Aspect ratio 4:5
```

> 年轻人物：在此模板的质感句后追加 02 锚定表的"年轻人物皮肤状态标准句·基础句"；微笑/含笑镜头再加"微笑追加句"（见 consistency 二节，逐字复用）。
> **可选单锚派生路径**：启用时本图从 0a 正面全身锚点改图派生（第一句写 `Zoom in to an extreme close-up head-and-shoulders portrait...`），不再独立文生图；派生图之间不互相参考。

### {角色名} · 0c 按需补充锚（≤2 张）
- 表情板：`expression studies sheet, same face: neutral, smiling, sad, angry, front view, plain white background`
- 单张表演特写（微笑/哭泣/愤怒等）：`{表情描述}, same face as the identity reference, plain white background`；身份参考挂 0b 中性面部特写，用途声明写"锁定脸型/五官/发型；不复刻其构图与中性表情"
- 服装细节图：{花纹复杂服装的单独特写}

> 画幅：每条补充锚提示词写 `Aspect ratio 1:1`。用户点名表情特写时，0b 中性身份锚仍必做；本 0c 特写不替代 0b，也不入情景图参考组。

### 多人脸对照条（V3.16，多个角色同时锁脸时用）

> 用途：把每个角色的**单人脸部锚**横向拼接成一条对照条，作为多人场景的**唯一脸部依据**；它不是一次生成，而是**裁切/拼接已有脸部锚**。用途声明必须写死，否则模型会把对照条搬成一张多人合影。

```
Image 1 = 多人脸对照条。逐格只取身份：第1格={角色A}，第2格={角色B}，第3格={角色C}。
不生成多人同框画面；不复刻对照条的横向排版/背景/构图。
```

- 每格必须是一张**单人**脸部锚（0a 合图左半裁出，或分张 0b）；原生多人合影不可作身份参考。
- 只替代"逐人脸部特写"的身份职能；三视图（身形/服装）仍按角色各自挂。

### {角色名} · 0d 白底正面图（产物/动物主角用）

```
{拍摄媒介句}。
{锚定短语逐字}。正面全身像，自然放松站姿，纯白背景，人物完整居中。
natural skin texture, visible pores, realistic and imperfect。
Aspect ratio 1:1
```
