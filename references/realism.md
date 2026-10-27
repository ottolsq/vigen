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

### 表面处理两档（"旧"要旧得讲道理——破旧不是默认值）

| 档 | 适用 | 写法 |
| --- | --- | --- |
| **日常使用型** | 民居/店铺/常用器物 | 掉漆、水渍、包浆、角落积尘——磨损随机分布 |
| **持续维护型** | 宫殿/庙宇/豪门/官方场所 | 漆面匀泽、扫净石材；**磨损只出现在人接触得到的位置**——门槛正中、扶手、台阶踏面（"磨在该磨的地方，是人走出来的，不是年久失修"） |

> 实测事故：给金銮殿写"漆面剥落"——被维护的庄严场所拿到破败描述，画面立刻不成立。选档先问：这个场所有没有人天天打理？
> **朝代纪律**（古装/年代项目）：全剧锁定**一个具体朝代**，禁写"古代/架空"——"古代"在画面里没有对应物，模型会自己挑一个世纪混搭。架空世界观写明"像哪个朝代"（"明代风格的市井"），服制/器物/建筑形制按该朝代写进场景与服装描述。

### 画面文字的物理化写法（需要文字出现时——"文字+载体"的升级配方）

文字不是贴上去的字幕，是**物理现象**——写明文字由什么物理过程形成：

| 配方 | 关键句 |
| --- | --- |
| 光投影字母 | "每个字母均由光线投射而成，而非贴在墙上的发光字体；光源、镂空切口与墙面投影须处于同一直线" |
| 墨流成字 | "文字必须由同一股墨流自然形成，不得添加电脑字体" |
| 折射文字 | "扭曲仅限于半透明区域（瓶内清水后的部分），不要将整个标题扭曲成波浪状"；外部线条保持精准连续 |
| 温度/材质渐变字 | "变化必须连续、克制且符合重力规律"（融化向下流，不随机变形） |
| 字体框景 | "让字体去框住画面，而非叠加在画面上"——巨字作风景容器，字腔里放小剪影标比例 |

防漂移配套（海报/版式类图）：文字白名单（"文字仅限提示词中明确列出的标题与字样，不得编造价格/日期/标语"）+ 全不透明锁（"全不透明矩形背景覆盖整个画布，无透明像素、黑角、边缘羽化"）+ 防样机条款（"输出成品平面设计本身并填满画布，禁止相框/贴墙照片/边缘透视变形"）。

### 慎用词（触发AI感或无效）
| ❌ 慎用 | ✅ 改用 |
| --- | --- |
| photorealistic / hyperrealistic | a photograph + 相机参数（触发"画得很像照片的绘画"风格——社区经验，风格偏好建议） |
| 8K / ultra HD / masterpiece | 具体质感词（film grain / skin texture） |
| beautiful / stunning / amazing | 具体构图光线描述 |
| 画面类否定词（"不要四仰八叉"） | **正向引导**：把概率推到想要的样子（"坐姿端正像学生上课端坐"）——负面词模型不收且反效果；字幕/音频类禁令除外（放 NO 节有效） |
| portrait（单独出现） | medium shot + off-center + 机位（单独 portrait 默认头像式构图） |
| "暖色调/低饱和"倾向词 | 十六进制色号+颜色落在哪里（见 styles.md 色彩基调） |

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

## 三·五、画面张力四法（透视/表现力强化——情景图与场景图的"视觉张力"槽必填至少 1 法）

> 平铺直叙的均匀画面=没有张力。张力来自**对比**：明暗对比、大小对比、框内框外对比、曝光对比。每图自问"这张图的视觉重点靠什么被推出来？"

| 法 | 写法 | 范例（提炼自成品提示词） |
| --- | --- | --- |
| ① 明暗纵深 | 指明画面哪里最亮、哪里深沉但留有细节——大光比制造空间层次 | "门口是最亮的地方，室内暗部深沉而留有细节"；"窗户和她的双手是画面里最亮的部分，身后店铺退入黑暗" |
| ② 尺度对比 | 主体与环境的悬殊大小关系，用参照物锚定尺度 | "废弃工程机械在巨兽脚下如玩具，碎石堆显得微缩"；"卡车对比铁门显得十分渺小，人与建筑形成强烈大小对比" |
| ③ 框中框切割 | 用建筑/物体把画面切成几何块，主体在框中 | "方形的柱子把明亮的街道切成一块块高高的竖条"；"透过完全敞开的店面看向街道"（店框景） |
| ④ 过曝/欠曝分区 | 画面不同区域曝光刻意不均——一个区域过曝发白、一个区域沉入阴影 | "门外略微过曝：一辆经过的自行车"；"街道在阳光下白得发烫，几乎过曝，骑楼下阴凉黑暗" |

**透视强化写法**（配合张力四法）：
- 纵深透视：明确"从X深处向外望/从X向内望去"的视线路径（"从一间老早餐铺的深处向外望"）
- 消失点线索：走廊/街道/廊道的线条汇聚方向写明（"沿着骑楼深深的阴凉廊道望去"）
- 前景-中景-背景三层各有一个具体物件，不许空层
- 低角度贴地/高角度俯视等极端机位天然带透视夸张——按分镜机位选用

**张力与风格的关系**：治愈系用①③的柔和版本（窗光分层）；史诗/压迫感用②④的强对比版本；悬疑用①③（暗部占比大+框中框窥视）。张力四法至少 1 法进"视觉张力"槽，白底锚定图豁免（无背景可言）。

## 四、镜头与光线词库（与 cinematography.md 互补，此处为图片专用速查）

- 焦段：85mm f/1.4（人像特写浅景深）/ 35mm（日常纪实）/ 24mm f/11（环境深焦）
- 光线：natural window light / soft diffused daylight / golden hour / overcast morning / Rembrandt lighting / rim light / subtle fill flash
- 色调锚定（写具体不写模糊）：**十六进制色号+颜色落在哪里**是最强锚点（"低饱和蓝灰雨夜为环境底色 #3A4654，点缀暗酒红只给打火机 #6E2B31"）；退而求其次写精确图形词（"color grading: warm highlights, slightly desaturated shadows"）；"beautiful colors" ✗（模糊词是"倾向"，色号才是锚点）——色板由 02 色彩基调节统一管理（见 styles.md）

## 五、电影级写真人像全维度描述（人物图强化包）

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

适配规则（见 knowledge-index.md）：图片提示词用上面的正向维度描述即可（以正向表述为主）；视频提示词的负面概念集中写进骨架 A 的 NO 节或骨架 B 约束槽；支持负面提示词的模型原文直接可用。

## 六、实操要点

1. **顺序权重**：最重要的写最前，技术参数（画幅/宽高比）写最后——画幅写提示词末尾（如 "Aspect ratio 16:9"），与 prompt-rules.md 图片 11 槽位的画幅槽对应
2. **复杂度上限**：有效内容约 256 token——"整体构图"描述优于"物品清单式罗列"，诗意长文无效
3. **角色脸部细节分层**（防"塑料硅胶脸"模板）：头发→脸型→眉眼→嘴鼻逐项具体描述，用细节覆盖模板
4. **颜色感染**：主体颜色会散射影响整体色调；需要统一色调时，色调词在提示词不同位置重复出现以加权
5. **同会话生成 3-5 张后风格污染**：API 独立请求可避免；网页连续生成时分批重开
6. **参考图描述法**：找到满意的真实照片时，可让视觉模型描述它（"describe this photo in detail"）反向生成提示词骨架
