# 资产系统模板（V3.25——Seedance 官方资产系统 / 人脸一致性）

> 何时读：建 02 角色/服装/场景/道具锚定与 03 资产矩阵时；需要人物设定板、表情/动作矩阵、场景圣经、道具 turnaround 时。
> 来源：seedance.tv 官方《AI 视频资产怎么做，画面才稳定？》《如何在 AI 修图中保持人脸一致》`[官方文档]`。规则家和纪律见 consistency.md；本文件只放可复制的模板。

## 一、资产表（先定"每份资产必须固定什么"）

| 资产 | 必须固定 | 最小交付 | 不要继承 |
| --- | --- | --- | --- |
| 人物身份 | 五官、发型、肤色、体型 | 正脸、侧脸、服装正面、完整背面 | 动作、场景、镜头 |
| 妆造 | 版型、材质、配色、鞋子 | 每套造型一张独立全身资产 | 表情和剧情 |
| 表情 | 情绪状态与强度 | 同机位、同光线的表情矩阵 | 身体动作 |
| 动作 | 路径、重心、接触和顺序 | 连续关键姿态 | 身份和场景风格 |
| 场景 | 空间、光线、材质和家具 | 多角度空镜 + 平面图 | 无关人物 |
| 道具 | 形状、比例、结构和材质 | 正面、侧面、背面 + 功能细节 | 手势和剧情 |
| 色板 | 颜色角色与使用比例 | 角色、HEX、用途 | 物体形状 |

> 每份资产只有一个编号、一个主体、一项职责；同一素材不要在提示词中途改名。

## 二、人物模板 A（宽松四视图：左头像 + 右三视图）

```text
Create a photorealistic four-view character reference sheet from Image 1. Use a clean white studio background. On the left, show one highly detailed, perfectly front-facing live-action head-and-shoulders portrait. Preserve the exact facial structure, expression, hairstyle, hair accessories, pores, fine lines, eyelashes, flyaway hairs, and natural skin texture. No beauty retouching and no over-sharpening. On the right, show the exact same character in a standard A-pose as three aligned full-body views: front, side, and back. Preserve the same body proportions, complete wardrobe design, fabric layers, shoes, accessories, and realistic material behavior in every view. No scene, no action, no extra people, no logo, no watermark.
```

## 三、人物模板 B（双头像 + 放大服装 + 完整背面——重脸部细节/服装结构时用）

```text
Create a professional photorealistic character reference board from Image 1 on a neutral grey studio background. The layout must have two sections. The upper third contains two large face close-ups: a perfectly front-facing portrait on the left and a clean side-profile portrait on the right. Preserve the exact facial identity, bone structure, hair, makeup, age, skin texture, and accessories. The lower two-thirds contains two wardrobe views. On the left, show a magnified front-facing A-pose wardrobe view cropped from just below the neck to the shoes so the garment construction fills the frame. On the right, show a complete rear full-body view. Keep lighting, lens, body proportions, clothing, and materials identical across all panels. This is a production reference sheet, not a poster or fashion editorial. No action, no complex background, no logo, no watermark.
```

## 四、妆造库（LOOK 命名 + 每套三视图）

- 先做中性全身底图，再一次只替换一套完整造型（人物/姿势/镜头/光线不变）。
- 每套命名 `LOOK_DAILY` / `LOOK_SPORT` / `LOOK_FORMAL`，各出正面/侧面/背面。
- 换装提示词：`Use Image 1 for identity and body proportions. Use Image 2 only for the complete wardrobe, shoes, and accessories. Replace the outfit in Image 1 with the full outfit from Image 2 while preserving the same face, hairstyle, glasses, pose, body shape, lighting, camera, and neutral studio background. Do not change the person. No logo, watermark, or extra text.`

## 五、表情矩阵（4×4 十六格）

```text
Using the exact same person from Image 1, create a photorealistic facial-expression asset sheet on a neutral grey studio background. Use a clean 4×4 grid with sixteen consistent head-and-shoulder portraits. Preserve the same facial structure, hairstyle, glasses, makeup, age, skin texture, lens, angle, and lighting in every cell. Show restrained, realistic variations: neutral, focused, soft smile, curious, surprised, tense, tired, calm, frown, angry, relieved, sad, thinking, happy, shy, and unbothered. Avoid cartoon acting, face drift, beauty retouching, and plastic skin. English labels only. No logo or watermark.
```

## 六、动作 beat 图鉴（16 格连续关键姿态）

```text
Convert the described action sequence into a coherent 16-panel cinematic action-beat library. Each panel must show one readable action instant with a clear number, short English beat name, body direction, balance, contact point, and screen direction. Keep both character identities, wardrobe, scene geography, lighting, and camera language consistent. No injury detail, no logo, no watermark.
```
> 每格只表达一个可读瞬间、接触点、重心状态与运动方向；与 01 的 action-combat 交手账对齐。

## 七、场景圣经（3×3：多角度空镜 + 俯视平面图）

```text
Create a complete production scene bible for [scene] using a clean 3×3 grid. Show: entrance wide shot; reverse wide shot; left-side view; right-side view; eye-level view; low view; key furniture/props close-up; material and wear detail; and a readable top-down floor plan. Preserve the exact room geometry, furniture positions, doors, windows, light direction, materials and color palette across every panel. No people, logos, subtitles, or invented rooms. Use small English view labels only.
```
> 场景资产只放空镜与空间事实；人物和剧情动作属于最终镜头，不属于场景证据。

## 八、道具 turnaround（正/侧/背 + 功能细节）

```text
Create a physical prop turnaround sheet on a white or light-grey background. Show the selected prop in front, side, and rear views, plus one close-up of its most important functional detail. Preserve the exact shape, color, material, scale, seams, hardware, and structural features across every view. Use clean English labels only. No hands, people, scene lighting, brand logo, or watermark.
```

## 九、色板资产（7 角色 + HEX + 用途）

```text
You are a film colorist, visual art director, and AI-video palette designer. Analyze all uploaded frame references as one visual system. Extract exactly seven shared production colors: BASE, SUPPORT, SHADOW, HIGHLIGHT, SKIN, REFLECTION, and ACCENT. For each color, provide one #RRGGBB HEX value and one concise use case. Then create one clean professional palette asset image containing only the seven swatches, English role label, HEX value, and use case. Explain which colors may cover large areas, which must remain small accents, and which hues should be avoided. No people, scene illustration, long theory, logo, watermark, subtitles, neon saturation, or random colors.
```
> 与 02 色彩基调（环境底色/中间调/点缀/肤色/暗部）映射：BASE→环境底色，SUPPORT→中间调，ACCENT→点缀，SKIN→肤色，SHADOW→暗部；HIGHLIGHT/REFLECTION 作为选配扩展。

## 十、多素材职责表（交给视频模型前逐行填）

| 输入 | 对应主体 | 唯一职责 | 明确排除 |
| --- | --- | --- | --- |
| 图片 1 | CHARACTER_A | 人脸、发型、肤色、体型 | 不参考摄影棚背景 |
| 图片 2 | LOOK_SPORT | 服装、鞋子、配饰 | 不重新定义人脸 |
| 图片 3 | EXPRESSION_A | 情绪与强度 | 不改变身体动作 |
| 图片 4 | ACTION_A | 动作顺序与接触关系 | 不参考身份和环境 |
| 图片 5 | LOCATION_A | 空间、材质、家具与光线 | 忽略偶然物品 |
| 图片 6 | PROP_A | 形状、比例、结构 | 忽略参考背景 |
| 图片 7 | PALETTE_A | 颜色职责与比例 | 不给肤色染色 |

> 提交前检查：每个常驻角色一份身份母版；换装不改脸；表情强度有边界；动作含路径/重心/接触/结束；场景含反打与平面关系；重要道具有稳定几何；每份资产一个编号/主体/职责；最终提示词含时间轴/连续性/声音/排除项。
