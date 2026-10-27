# 风格库（15 风格 · 风格圣经词条）

> 阶段1 定风格时读本文件。每个风格词条 = 完整的"风格圣经"——选定时整段复制进 02_锚定表，之后逐字追加到每条图片/视频提示词末尾。用户可自定义新风格（按同样格式加入本库）。

## 使用方法

1. 按创意主题初选 2-3 个候选风格，结合用户表述的偏好定 1 个
2. **定风格后立即定全片色彩基调（3-5 个十六进制色号）**——见下节，写入 02_锚定表"色彩基调"节，先于生成任何场景图
3. 风格圣经 + 色彩基调写入 02_锚定表后**逐字冻结**——中途换风格/换色板=全部下游文件重做
4. 视频提示词的风格一致性由"情景参考图（首帧）+ 风格圣经逐字复用 + 质感锚定行"三重承担
5. **用户给了一张参考图/剧照说"要这种感觉"** → 走下方"风格提取（解梦卡）"通道，提炼出的动态风格圣经与预设词条同等冻结

## 风格提取：从用户参考图提炼风格圣经（解梦卡——第 16 类动态词条）

预设 15 风格覆盖不了"就要这张图的感觉"。此时不猜、不套最近似预设，按四步提取：

1. **三层拆解**参考图：
   - **场景事实**（不迁移）：图里的人物身份/服装/地点/文字/品牌——这些属于那张图，不属于风格
   - **视觉语法**（可迁移的**关系**）：光源行为（光从哪来、怎么衰减）、曝光行为（哪里过曝哪里死黑）、材质处理（皮肤/金属/织物怎么渲染）、捕获特征（颗粒/眩光/焦外形态）——描述"关系"，禁止用标签词（cinematic/dreamy/film look 都不许出现）
   - **条件项**（逐项裁决）：机位/构图/尺度/光向——每项标 Preserve（新场景照搬）/ Adapt（按新场景调整）/ Release（不迁移）
2. **压缩成 3-5 条核心风格律**（可执行、描述关系、每条摄影指导能直接执行）——例："主光只从画面左侧单一窗口进入，衰减快，右侧人物轮廓沉入暗部但保留眼神光"
3. **写入 02 风格圣经节**，标注"提取自用户参考图 {文件名}"，与预设词条同等逐字冻结；参考图本身登记为风格参考素材（进 ACTIVE REFERENCES 时用途声明写"只参考光色关系与材质处理，不迁移其中人物/服装/场景"）
4. **源残留清单**：提取后自查——生成的新图里不许出现参考图的身份元素（脸/服装/logo/特定道具）；发现泄漏=回退重生成

> 变体通道（用户参考图是照片且要精确复刻色彩）：先让模型"分析这张照片，输出详细 JSON 描述视觉风格——拆解色彩分级、光照及所有确切颜色（十六进制）"，再把该 JSON 的色值并入 02 色彩基调节、语法描述并入风格圣经——JSON 是提取的中间产物，最终仍以 02 冻结文本为准。
> **文字意象输入分支**（用户没有图，只给一段文字描述"想要这种感觉"）：跳过三层拆解中的"场景事实/源残留"两步（无图可拆、无残留可查、无素材可挂），直接从文字里提取**视觉语法关系**（光行为/曝光行为/材质处理/捕获特征）压缩成 3-5 条风格律，02 登记"提取自用户文字意象：{原话}"；色彩描述含色相词的转十六进制进色彩基调节（"绿色偏青色"→定具体色号）。其余冻结与复用纪律与图片输入完全一致。

## 色彩基调（十六进制色板——生成场景图之前必做）

**为什么要色号**："暖色调""低饱和"是倾向，模型每次采样出的暖都不一样；色号是锚点。优秀成品的做法是先为全片定 3-5 个具体颜色，所有场景图/情景图按同一色板生成，分段色调才真的一致。

**色板构成（按面积分配，配合 emotion-craft.md 色调三段式）**：

| 角色 | 面积 | 说明 | 示例（治愈柔和） |
| --- | --- | --- | --- |
| 环境底色 | 大面积（约 60%） | 空间主色，定调 | `#E8E0D5` 米白墙 / `#C9C3B8` 灰绿 |
| 中间调 | 中面积（约 25%） | 家具/服装/道具主色 | `#D9A87C` 暖木色 |
| 点缀色 | 小面积（约 10%，只给特定物体） | 视觉焦点，不铺满 | `#E4B7A0` 淡珊瑚（只给杯子/花） |
| 肤色基准 | — | 人物皮肤在冷环境里要保留血色 | `#E8C0A8` 暖肤色 |
| 暗部色 | — | 阴影不是纯黑，带色相 | `#8A93A6` 灰蓝阴影 |

**写法（进图片提示词的色调槽）**：色号 + 颜色落在哪里，不只列色号。
> ✓ `色调：低饱和蓝灰雨夜为环境底色（#3A4654），暗部保留墨绿与灰紫（#2E3B36 / #4A4257），人物嘴唇和鼻翼保留少量血色（#C08A82），背景点缀少量暗酒红只给打火机与商品（#6E2B31）。`
> ✗ `色调：冷色调，低饱和，有质感。`

**各风格的推荐色板**（可直接用或按主题微调；写进 02 后冻结）：

| 风格 | 环境底色 | 中间调 | 点缀色 | 暗部色 |
| --- | --- | --- | --- | --- |
| 电影写实 | `#4A4239` 暖褐 | `#A89684` 燕麦 | `#C8A05A` 暖金 | `#2A2E35` 冷灰蓝 |
| 治愈柔和 | `#E8E0D5` 米白 | `#D9C4B0` 奶茶 | `#E4B7A0` 淡珊瑚 | `#B8B0A8` 暖灰 |
| 日系清新 | `#F2F0EA` 过曝白 | `#C8D2C0` 灰绿 | `#E8DCC8` 米黄 | `#DCDCD6` 浅灰 |
| 国风写意 | `#E6E2DA` 宣纸白 | `#8A8F87` 墨灰绿 | `#B33A3A` 朱砂红 | `#5A5F5A` 淡墨 |
| 赛博朋克 | `#12141C` 深蓝黑 | `#1F3A5F` 钴蓝 | `#FF2E88` 霓虹粉 / `#00E5FF` 青 | `#080A10` 近黑 |
| 复古胶片 | `#D8C4A0` 褪色暖黄 | `#A8845C` 棕褐 | `#C86A4A` 砖橙 | `#6A5A48` 暗褐 |
| 悬疑黑色 | `#1A1C20` 炭黑 | `#3A3E45` 冷灰 | `#C8A05A` 单一暖光源 | `#0A0C0E` 死黑边缘 |
| 都市夜晚 | `#1E2530` 夜蓝 | `#D89A4A` 钠灯橙 | `#E04A5A` 店铺霓虹红 | `#12161C` 深蓝黑 |
| 科技概念 | `#E8ECF2` 冷白 | `#A8B4C4` 银灰蓝 | `#3A7AC8` 科技蓝 | `#6A7482` 中灰 |
| 自然纪录片 | `#8A9A6A` 植被绿 | `#C8B89A` 土地色 | `#E8C87A` 黄金时刻暖 | `#4A5240` 暗绿 |
| 极简高级 | `#F0F0EE` 灰白 | `#C8C8C4` 中灰 | `#8A8A86` 深灰 | `#DCDCD8` 浅灰 |
| 奇幻史诗 | `#3A2E4A` 暗紫蓝 | `#C89A4A` 古铜金 | `#E8C87A` 神性金光 | `#241E30` 深紫黑 |
| 美食特写 | `#F2EDE4` 米白 | `#C88A4A` 焦糖 | `#8AA84A` 新鲜绿 | `#A8968A` 暖灰 |
| 动漫剧场版 | `#A8D8F0` 通透天蓝 | `#F0E0C8` 云白暖 | `#F09AA8` 樱粉 | `#7A9AC8` 蓝紫阴影 |
| 手绘童趣 | `#F5EBD8` 奶油纸 | `#E8A87C` 蜡笔橙 | `#7CA8D8` 蜡笔蓝 | `#D8C8B0` 浅褐 |

> 自定义风格：按同样五栏配色板；导演风格（director-styles.md）以其标志色为准（王家卫=青绿阴影+洋红高光；诺兰=青蓝阴影+暖棕受光；韦斯·安德森=粉红/芥末黄/薄荷绿/天蓝）。

## 风格词条

### 1. 电影写实（默认推荐·通用）
- 圣经：`cinematic realism, shot on 35mm film, natural color grading with warm highlights and slightly desaturated shadows, visible film grain, shallow depth of field, realistic natural lighting`
- 适用：剧情类、纪实感、多数主题的保底选择
- 大白话：像真电影一样，颜色不艳、有胶片颗粒、光像真的

### 2. 治愈柔和
- 圣经：`soft healing atmosphere, warm pastel tones, gentle diffused daylight, soft focus, airy and clean composition, cozy and calm mood`
- 适用：宠物、日常温暖、慢生活
- 大白话：暖暖的淡彩色、光线柔柔的、看着心里舒服

### 3. 日系清新
- 圣经：`Japanese fresh style, bright overcast daylight, low contrast, slightly overexposed whites, muted green and beige palette, candid documentary feel`
- 适用：青春、日常、街道
- 大白话：日系照片那种白白的、淡淡的、像午后阴天拍的感觉

### 4. 国风写意
- 圣经：`Chinese aesthetic style, ink-wash inspired tones, muted earth colors with one accent vermilion, soft mist, traditional composition with negative space`
- 适用：古风、山水、传统文化
- 大白话：像水墨画一样留白多、颜色淡雅、有一抹红色点睛

### 5. 赛博朋克
- 圣经：`cyberpunk aesthetic, neon pink and cyan lighting, rainy night streets with reflections, high contrast shadows, Blade Runner atmosphere, volumetric fog`
- 适用：科技、未来、都市夜
- 大白话：霓虹灯粉蓝配色、雨夜地面反光、又酷又迷离

### 6. 复古胶片
- 圣经：`vintage 1970s film photograph, faded Kodachrome colors, warm orange cast, visible grain, slightly soft focus, nostalgic atmosphere`
- 适用：怀旧、家庭、回忆
- 大白话：老照片那种偏黄褪色、有颗粒、看着就想起了过去

### 7. 动漫剧场版
- 圣经：`anime theatrical film style, Makoto Shinkai inspired, vivid saturated skies, detailed cloudscapes, glowing rim light on characters, clean line art`
- 适用：青春、幻想、热血
- 大白话：新海诚电影那种天空特别漂亮、人物边缘发光的动漫画风

### 8. 极简高级
- 圣经：`minimalist aesthetic, low saturation grey tones, large negative space, clean geometry, soft even lighting, quiet and premium mood`
- 适用：产品、概念、高端品牌
- 大白话：性冷淡风，大片留白、灰灰的、看着很贵

### 9. 悬疑黑色
- 圣经：`film noir mood, low key lighting, deep shadows, single motivated light source, high contrast, desaturated cool tones, mysterious atmosphere`
- 适用：悬疑、犯罪、心理
- 大白话：黑漆漆的就一束光、影子特别深、透着股不对劲

### 10. 奇幻史诗
- 圣经：`epic fantasy style, dramatic golden hour backlight, vast scale, volumetric god rays, rich saturated palette, painterly detail`
- 适用：奇幻、冒险、大场面
- 大白话：大场面、金光从云里洒下来、又壮丽又震撼

### 11. 美食特写
- 圣经：`food photography style, soft directional window light, shallow depth of field, fresh textures with visible moisture and steam, warm appetizing tones, top-down or 45-degree angle`
- 适用：美食、烹饪
- 大白话：美食杂志那种冒着热气、水灵灵的、看着就饿

### 12. 自然纪录片
- 圣经：`nature documentary style, telephoto lens compression, natural golden hour or overcast light, authentic wildlife behavior, crisp detail, muted natural palette`
- 适用：动物、自然、生态
- 大白话：像 BBC 纪录片，远处拍动物、光是真太阳、颜色不假

### 13. 都市夜晚
- 圣经：`urban night style, sodium streetlight orange mixed with shop neon, wet asphalt reflections, cinematic anamorphic bokeh, moody atmosphere`
- 适用：城市故事、夜生活
- 大白话：晚上街边路灯黄光配店铺霓虹、地面湿湿的反光

### 14. 科技概念
- 圣经：`futuristic tech concept style, cool blue and silver palette, clean studio environment with soft gradient background, product-hero lighting with rim light, high detail`
- 适用：产品发布、科技演示
- 大白话：发布会那种蓝色调、干净背景、产品边缘一圈亮光

### 15. 手绘童趣
- 圣经：`hand-drawn storybook illustration, soft crayon texture, rounded shapes, warm primary colors, gentle imperfect lines, playful composition`
- 适用：儿童、绘本、节日
- 大白话：像手绘绘本，蜡笔质感、圆圆的、颜色暖暖的

## 自定义风格模板

```
### N. {风格名}
- 圣经：{媒介+色调+光线+质感+氛围，一段可逐字复制的英文短语}
- 适用：{主题类型}
- 大白话：{一句话给用户解释}
```
