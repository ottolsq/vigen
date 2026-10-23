# 真实感与去AI味（摄影词汇库）

> 写人物/场景/情景图提示词时读本文件。核心方法论：**描述"这张照片是怎么被拍出来的"**，而不是堆砌画质形容词。

## 一、拍摄媒介句库（提示词开头第一句）

按风格选用，一句定调真实感：

| 场景类型 | 媒介句 |
| --- | --- |
| 人物参考（棚拍） | A character reference photo shot on medium-format camera, 85mm f/4, soft even studio lighting |
| 日常纪实 | A candid photograph shot on 35mm film. Natural imperfect framing, visible grain, ambient light, muted colors |
| 生活随拍 | A photorealistic everyday photo taken casually, slightly imperfect framing, natural realism of a real phone snapshot |
| 夜景/派对 | shot on a compact point-and-shoot camera with direct flash, deep shadow falloff, spontaneous energy |
| 怀旧年代 | a candid disposable-camera snapshot, visible grain, slightly faded colors |
| 电影感叙事 | shot on a medium-format analogue camera using colour film, 85mm f/4, realistic, authentic, imperfect, and natural |

通用公式：**相机/胶片媒介 + 镜头参数 + 光线性质 + "imperfect/natural" 修饰**。

## 二、去AI味词汇表

### 画质质感
- natural skin texture, visible pores（皮肤毛孔——人物必备）
- visible film grain（胶片颗粒）
- authentic, imperfect, natural（官方点名三词）
- no plastic sheen（防塑料感——正向表述用 natural matte finish）
- muted colors / low saturation（低饱和）
- warm highlights, desaturated shadows（暖高光低饱和阴影）
- LESS DETAILS（抑制高频纹理噪声、clone-stamp 重复感）

### 环境瑕疵感（lived-in——去AI味关键维度，每图至少 2 处）
- uneven sunlight（不均匀阳光）
- half-finished drinks（没喝完的饮品）
- wind in clothing and hair（风吹动衣物头发）
- lived-in documentary feel（有生活痕迹）
- slightly imperfect framing / slightly tilted（构图略歪）
- wrinkled fabric, worn edges, dust motes in the light beam（布料褶皱/磨损边缘/光束中浮尘）

### 禁用词（触发AI感）
| ❌ 禁用 | ✅ 改用 |
| --- | --- |
| photorealistic / hyperrealistic | a photograph + 相机参数（禁用词触发"画得很像照片的绘画"风格） |
| 8K / ultra HD / masterpiece | 具体质感词（film grain / skin texture） |
| beautiful / stunning / amazing | 具体构图光线描述 |
| no text / don't add...（否定词） | 正向写要什么（文字防御靠"画面干净无文字元素"） |
| portrait（单独出现） | medium shot + off-center + 机位（单独 portrait 默认头像式构图） |

## 三、构图多样性（防死板组合拳）

**破证件照三件套**：偏心构图（off-center）+ 前景遮挡（foreground occlusion / shot through foreground foliage）+ 具体景别机位。

| 构图 | 英文 | 效果 |
| --- | --- | --- |
| 三分法 | rule of thirds | 基础 |
| 引导线 | leading lines | 纵深 |
| 框中框 | frame within a frame（门窗/镜子） | 聚焦 |
| 负空间 | negative space | 孤独/高级感 |
| 前景遮挡 | out-of-focus foreground element | **破证件照最有效** |
| 偏心 | off-center composition | 自然 |
| 景深层次 | layered depth (foreground/midground/background) | 丰富 |
| 选择性对焦 | selective focus | 对抗"处处清晰=AI感" |
| 自然歪斜 | natural imperfect framing | 随拍感 |

**每图构图必须变化**：同一项目内不连续使用相同构图；分镜设计时与景别节奏联动（见 cinematography.md）。

## 四、镜头与光线词库（与 cinematography.md 互补，此处为图片专用速查）

- 焦段：85mm f/1.4（人像特写浅景深）/ 35mm（日常纪实）/ 24mm f/11（环境深焦）
- 光线：natural window light / soft diffused daylight / golden hour / overcast morning / Rembrandt lighting / rim light / subtle fill flash
- 色调锚定（写具体不写模糊）："color grading: warm highlights, slightly desaturated shadows" ✓；"beautiful colors" ✗（模糊词是"倾向"，精确图形词才是锚点）

## 六、电影级写真人像全维度描述（人物图强化包）

> 人物参考图/情景图需要更强真实感时，把以下维度并入提示词（与骨架 0a/0b 的质感行合并使用，逐项按需选取，不必全堆）：

```
电影级写真人像，真实活人质感：
- 光效维度：场景包含体积光（volumetric light）、空气悬浮微粒
- 质感维度：自然胶片颗粒感，背景层次丰富有真实氛围感
- 眼部维度：清晰的眼神光（catchlight）与自然对焦效果，眼神灵动不呆滞
- 表情维度：面部带有微妙情绪表情
- 肢体维度：肢体具备真实重量感，动态动作体现自然的力度传导，衣物一角随身体动作自然摆动，姿态松弛舒展
- 皮肤维度：原生真实质感，可见自然毛孔、微细血管，肤色自然红润，保留真实微小皱纹
```

**原负面提示词清单**（保留原文——后续换用支持负面提示词的生图模型时直接使用）：
> 干净如僵硬，肢体僵硬漂浮，动作不符合物理逻辑，塑料感皮肤，陶瓷板光滑肌肤，过度磨皮，无暇假脸，AI失真的，过度完美的不真实质感

适配规则（见 knowledge-index.md）：gpt-image 用上面的正向维度描述即可（负面词无效）；H3 把负面概念英文化并入 ban list（`Avoid plastic skin, ceramic-smooth complexion, over-retouched face, stiff floating limbs, motion violating physics`）；支持负面提示词的模型原文直接可用。

## 七、实操要点

1. **顺序权重**：最重要的写最前，技术参数（画幅/宽高比）写最后
2. **复杂度上限**：有效内容约 256 token——"整体构图"描述优于"物品清单式罗列"，诗意长文无效
3. **角色脸部细节分层**（防"塑料硅胶脸"模板）：头发→脸型→眉眼→嘴鼻逐项具体描述，用细节覆盖模板
4. **颜色感染**：主体颜色会散射影响整体色调；需要统一色调时，色调词在提示词不同位置重复出现以加权
5. **同会话生成 3-5 张后风格污染**：API 独立请求可避免；网页连续生成时分批重开
6. **参考图描述法**：找到满意的真实照片时，可让视觉模型描述它（"describe this photo in detail"）反向生成提示词骨架
