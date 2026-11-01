# vigen V3.0 创作功力升级 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 spec 落地 V3.0:三痛点内容移植(剧本/分镜/打斗)+ 峰值稀缺品范式 + check.py 薄校验层 + 停点收缩,治"幼稚拖沓/镜头单调/打斗缺失慢镜滥用/逐镜人工把关太慢"。

**Architecture:** 纯文档规则层(7 个 Markdown 文件的定向插入/改写)+ 一个新校验脚本(`scripts/check.py`,纯标准库)+ unittest fixtures。规则全文的唯一权威在 spec 与本计划引用的 drama-skills 源文件;vigen 文件按"单一事实源"落位,SKILL.md 只加指针。

**Tech Stack:** Markdown、Python 3.9+(标准库)、unittest、git。Windows/Git Bash 环境:命令用 `python` 不是 `python3`;跑测试加 `PYTHONDONTWRITEBYTECODE=1`。

**Spec:** `docs/specs/2026-11-01-v3.0-craft-upgrade-design.md`(执行者必读——含 46+3 条移植条目的完整规则文本、例句原文、落位与查重结论;本计划引用 spec 条目号 S*/C*/F*/K*/E2/R*/D*)

**drama-skills 源(例句与规则原文的唯一出处,执行时按需精读对应节):**
`C:\Users\ottol\myProjects\aigc\aboutSkillsReference\otherSkills\drama-skills-main\skills\`
- write: `short-drama-write/references/{script-craft,dialogue-craft}.md`
- develop: `short-drama-develop/references/{story-craft,episode-design,reveal-reversal-payoff}.md`
- storyboard: `short-drama-storyboard/references/{shot-craft,production-shot-grammar,blocking-playbooks,fight-craft,keyframe-craft}.md`
- video-prompts: `short-drama-video-prompts/references/{generability,camera-audio-continuity,motion-recipe}.md`

## Global Constraints

- **移植纪律(spec §3)**:单一事实源(每条规则只一个家,其余要点+指针);出处标注 `[drama-skills: 文件名#节]`(改写条目标 `[drama-skills 改写]`);三层粒度(规则/模板/例句,drama-skills 弱/强对照例句**逐字摘入**);落位前 grep 全库查重(spec §6 缺陷17纪律)
- **措辞纪律(R2/C2)**:选择层文档禁用"最稳/保险/安全牌/最简单"类安全品牌词;失败兜底点(回退阶梯/反应式降级)除外
- **峰值稀缺品(R3/C13)**:强调手段(慢镜/TimeRamp/冲击重复/短促推近/定格/闪白)只花在已点名峰值上,每处标注来源;不做预先降级实现
- **check.py 纪律(R1/D4)**:纯标准库、Python 3.9+、单文件;只 enforce 机械可判定门;宁松勿滥(误拦的门比没有门更糟);解析中文 Markdown 时防 SCR-18 类语法歧义(动作段以全角冒号开头会被误判台词——解析器必须区分)
- **commit 格式**:`feat/fix/docs/refactor/test: <中文描述>`,尾行 `Co-Authored-By: Claude Code <noreply@anthropic.com>`;每任务一个 commit
- **分支**:已在 `feat/v3-craft-upgrade`;所有工作在此分支,不切回 main
- **文件行数上限**:单文件目标 <800 行(user coding-style);screenwriting-craft.md 预计增至 ~450 行,不超限不拆

## 跨任务语法契约(所有任务共同遵守,check.py 按此解析)

- **CT1 运镜动机列格式**(templates 01 分镜表):`<五类词>(R<行号>)：<一句展开>`,五类词 ∈ {reveal, pressure, alignment, relationship, transition},行号 R1-R7 对应运镜功能决策表(C1),R7=固定。示例:`pressure(R3)：台词正压到她身上，缓推停在她脸上`。写"固定"必须带 `(R7)`
- **CT2 峰值标注格式**(04 强调手段处):`←峰值：<来源>`,来源 ∈ {`情节点<N>`, `交手账R<N>`}。示例:`慢动作 0.4s ←峰值：交手账R3`。文戏来源对应 01 情节点清单带【峰】标记的行;打斗来源对应 01"打斗交手账"小节的 R 编号
- **CT3 交手账落盘位置**(F2 实例数据):01_方案与剧本.md 分镜总览表节之后新增小节 `## 打斗交手账（打斗段必填——回合三格：发起/应对/结果）`,表格行号 R1、R2…;每行末列`结果改变`(本回合改变了什么:距离/朝向/武器控制/伤/体力/先手)
- **CT4 【峰】标记**(C13):01 情节点清单"情节点"列文本内嵌 `【峰】`(情绪爆发/重大反转/打脸拍);K6 校验其有对应镜号
- **CT5 PLAN/REF**(E2):04 参考素材行用 `PLAN-<ID>`(缺图占位)或 `REF-<ID>`(已绑定);ID 格式 `[A-Z0-9-]+`;禁止"待补参考图"式模糊字样
- **CT6 check.py CLI**:`python scripts/check.py <项目目录> [--partial] [--gate K5]`;exit 0=全过,1=有 findings,2=用法/IO 错;输出行格式 `[K5] 04_视频提示词.md:123: <具体缺什么>`(报错必须具体到文件+行号+缺什么,学 drama-skills"REF 缺少用途"式报错,不给笼统语法错)

## Review Focus

最可能咬人的五类失败(spec 隐含、单任务测试盖不全),各已钉到所属任务的步骤里:

1. **check.py 误拦合法项目**(真实项目格式变体多) → Task 20 Step 4 在 `myAiSeries/firepunch_ep1` 与 `inkos-short-drama/works` 真实产物上跑 `--partial`,记录误拦并放宽
2. **措辞审计残留**(清单外的安全品牌词漏网) → Task 7 Step 4 扩展 grep 词表(稳定/可靠/省心/傻瓜/无脑/不易翻车)全库扫
3. **规则文本与 SKILL.md 指针漂移**(单一事实源破坏) → Task 22 Step 2 逐条核对 SKILL.md 规则归属表/Module Map 与新节名一致
4. **新语法契约 agent 执行时不填**(【峰】列/动机列/峰值标注成了摆设) → Task 6 Step 9 / Task 7 Step 5 / Task 8 Step 5 各自 walkthrough 用样例镜头实填一遍验证可判定,Task 18 fixtures 钉死机器可解析性
5. **中文解析歧义**(全角冒号动作段误判台词,SCR-18 教训) → Task 15 Step 1 fixture 必含"第二格：一只手把杯子推过去"式动作行,Step 2 测试断言其不被解析为台词

---

## Step 1 · 打斗层(spec §4 第三节)

### Task 1: F1 病灶修复——删除库内慢镜鼓励(自相矛盾)

**Files:**
- Modify: `references/action-combat.md`(§7 输出格式装填模板内"Time Ramp"样板句,现约 :117;§8"高风险动作的生成端处理"内"腾空旋斩主方案=慢动作",现约 :124)
- Modify: `references/cinematography.md:190`("镜头动则主体动作放缓"句核对)与 :159("最稳 5 种"——**本任务只处理 :190 的慢镜关联句,:159 留给 Task 7**)

**Interfaces:**
- Consumes: 无(第一个任务)
- Produces: action-combat.md 不再含任何"慢动作给模型更多帧/高危动作降速处理"式鼓励句;后续 Task 3(F3 判据)、Task 8(C13 峰值节)依赖此处已清干净

- [ ] **Step 1: 定位全部病灶句**

Run: `grep -n "Time Ramp\|慢动作\|升格\|降速" references/action-combat.md references/cinematography.md`
Expected: action-combat.md 命中 §7 样板句与 §8 主方案句;cinematography.md 命中 :190 及慢镜预算节(预算节是正当规则,不动)

- [ ] **Step 2: 改写 action-combat.md §7 样板句**

将"Time Ramp 快慢结合(慢动作给模型更多帧——高危动作降速处理)"替换为:

```
速度处理：默认正常速度（生成端真相：镜头给多长，模型就把动作拉多长——写"快"压不回真实速度，高危动作降速优先用"拆更短镜头+切点紧剪"实现，不用整段升格）。慢动作是强调手段，只花在已点名峰值上——判据与配额见 cinematography.md「峰值与强调手段」节（唯一的家）。
```

(注:「峰值与强调手段」节名在 Task 8 才建立;本任务先写指针名,Task 8 落地同名节。执行 Task 1 时若 Task 8 未完成,指针暂指"慢镜预算节",Task 8 会统一改名——两个任务按序执行则无此问题,直接写目标节名。)

- [ ] **Step 3: 改写 action-combat.md §8 腾空旋斩句**

将"腾空旋斩/飞檐主方案=完整写法+慢动作(Time Ramp)"替换为:

```
腾空旋斩/飞檐主方案=拆短镜（腾空段独立成镜 1-2s，落地段独立成镜），慢动作仅腾空顶点 0.3-0.5s 且须有峰值标注（←峰值：交手账R<N>，见 cinematography.md「峰值与强调手段」节）。
```

- [ ] **Step 4: 核对 cinematography.md:190**

原句"镜头动则主体动作放缓(或静止),主体动则镜头选固定/极慢(这本来就是'最稳 5 种'规律的延伸…两大稳定组合)"中,**"最稳 5 种"引用与"稳定组合"品牌词**留给 Task 7 统一处理;本任务只确认该句不含慢镜鼓励(它讲的是双高速约束,保留)。若发现其他"慢动作更好生成"类句子,一并按 Step 2 口径改写。

- [ ] **Step 5: 验证**

Run: `grep -n "给模型更多帧\|降速处理\|主方案=.*慢动作" references/action-combat.md`
Expected: 零命中
Run: `grep -c "峰值与强调手段" references/action-combat.md`
Expected: ≥2(两处指针)

- [ ] **Step 6: Commit**

```bash
git add references/action-combat.md
git commit -m "fix: 打斗引擎去除慢镜鼓励样板句——高危动作降速改拆短镜+紧剪，慢镜入峰值稀缺品管辖

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 2: F2 交手账 + F8 并行任务书补丁

**Files:**
- Modify: `references/action-combat.md`(新增"第 0 节:整场编排(交手账)",置于现 `## 1｜Combat Setup` 之前;核心链路节同步)
- Modify: `SKILL.md`(阶段 1b 分镜+锚定段加一行指针;并行生产节子代理任务书清单加打斗补丁)
- Modify: `assets/templates.md`(01 模板分镜总览表节后新增"打斗交手账"小节,按 CT3)

**Interfaces:**
- Produces: 交手账 R 编号语法(CT3)——Task 3(F3 胜负手)、Task 8(C13 峰值标注)、Task 19(K5 校验)都依赖 R 编号可解析;action-combat.md 第 0 节节名固定为 `## 0｜整场编排（交手账——动手拆镜前先回合化）`

- [ ] **Step 1: 读源文件取例句**

Read `drama-skills-main\skills\short-drama-storyboard\references\fight-craft.md` §1(交手账三格+两条硬约束原文)

- [ ] **Step 2: action-combat.md 插入第 0 节**

在 `## 1｜Combat Setup` 前插入,内容骨架(规则文本按 spec F2 逐字,例句从 fight-craft.md §1 摘):

```markdown
## 0｜整场编排（交手账——动手拆镜前先回合化）

[drama-skills: fight-craft.md#1]

剧本只写"两人打斗"时，禁止直接进分镜——先把整场打斗写成交手账：每回合三格。

| 回合 | 发起（谁/哪只手或脚/拿什么/从哪一侧来——按场景站位锚点写，不写画左画右） | 应对（闪/挡/接/反制/被打中） | 结果改变（距离/朝向/武器控制/伤/体力/下一回合谁先手） |
| --- | --- | --- | --- |
| R1 | {…} | {…} | {…} |

**硬约束**：
- 每个回合至少改变一项结果。连续两回合结果都没变，观众读到的就是重复；回到剧本找这一回合真正改变了什么，找不到就合并或删掉
- 台词、对视和喘息是回合之间的换气点，不要让它们打断一个回合的中间
- **胜负手 = 结果改变最大的那一拍**——交手账写完后点名（标 ★），它是本段慢动作的唯一合法落点（见 cinematography.md「峰值与强调手段」节）

**与 Combat Setup 的关系**：Setup 锁单镜初始状态，交手账排整场回合串；交手账每回合 = 第 3 节状态机七段块的装填素材（没有回合，七段模板没有素材可装——"激烈对打"式泛写就是缺这一层）。

**落盘**：交手账写入 01_方案与剧本.md「打斗交手账」小节（模板见 assets/templates.md），R 编号一经分配不重排（同稳定镜号规则）。
```

- [ ] **Step 3: 核心链路节同步**

`## 核心链路（每段打斗必须走完）`的第一步前加"第 0 步:整场交手账(回合化+点名胜负手)"。

- [ ] **Step 4: SKILL.md 两处指针**

阶段 1b 段(现 :92-100)"识别反先验动作并在分镜表标注"句后加:

```
打斗段先写交手账再排镜（action-combat.md 第 0 节——剧本只写"两人打斗"时禁止直接进分镜）
```

并行生产节(现 :233)子代理输入清单"02 锚定表全文 + 01 的 GATE0 对齐记录与该批镜头的分镜表行 + prompt-rules.md 对应骨架全文 + 上一段 ENDING FRAME"之后加:

```
打斗/动作段任务书额外贴入 action-combat.md 全文（交手账+装填模板+武器力学表——实测教训：打斗段并行派发时模板丢失，子代理只拿到一行指针就自研格式）
```

- [ ] **Step 5: templates.md 01 模板加交手账小节**

在 01 模板"分镜总览表"节的稳定镜号规则引注之后、"GATE1 锚定确认记录"之前插入(按 CT3):

```markdown
## 打斗交手账（打斗段必填——回合三格，R 编号一经分配不重排）

| 回合 | 发起 | 应对 | 结果改变 | 胜负手 |
| --- | --- | --- | --- | --- |
| R1 | {谁/哪只手/拿什么/从哪侧} | {闪/挡/接/反制/被打中} | {距离/朝向/武器控制/伤/体力/先手} | {★ 或空} |

> 规则全文见 action-combat.md 第 0 节。胜负手(★)=慢动作唯一合法落点。
```

- [ ] **Step 6: 查重验证**

Run: `grep -rn "交手账" SKILL.md references/ assets/ | wc -l`(应≥6:action-combat 节+SKILL 指针+templates)
Run: `grep -n "Combat Setup" references/action-combat.md`(确认第 0 节在其前)
Walkthrough(记入 commit message 或对话汇报,不落盘):用"屋顶追逐→对峙→三人围攻"样例在脑中走一遍第 0 节——能否产出 ≥3 回合且每回合结果改变不同?胜负手能否唯一点名?

- [ ] **Step 7: Commit**

```bash
git add references/action-combat.md SKILL.md assets/templates.md
git commit -m "feat: 交手账(回合三格+胜负手点名)入打斗引擎第0节 + 01模板落盘小节 + 并行任务书打斗补丁

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 3: F3 决定性动作判据 + F9 打斗终检专项

**Files:**
- Modify: `references/cinematography.md`(段长预算与慢镜预算节,现 :252-263)
- Modify: `references/prompt-rules.md`(B3 抽查项,现 :539)

**Interfaces:**
- Consumes: Task 2 的胜负手 R 编号(CT3)
- Produces: "决定性动作"的操作判据文本——Task 8(C13)会把本节升级为「峰值与强调手段」节并接管这些判据;本任务写的判据必须已含"胜负手/【峰】"双来源,Task 8 只改名+扩家族,不重写判据

- [ ] **Step 1: cinematography.md 慢镜预算节补判据**

在该节"慢动作只给决定性动作"句后插入(规则按 spec F3,出处标注):

```markdown
**"决定性动作"操作判据**（无判据=每招都像胜负手，预算形同虚设——实测教训）[drama-skills 改写: shot-craft.md#SHT-04/SHT-08]：
- 打斗段：先在交手账里点名胜负手（结果改变最大的那一拍，标 ★）——**只有胜负手、缴械、逆转可配慢镜**，普通命中一律正常速度
- 文戏段：只有情节点清单标【峰】的情绪爆发/重大反转/打脸拍可配强调手段
- **一场里处处慢镜，就没有哪一下是冲击**——配额（≤2处/段）是上限不是任务，没用完不欠
- 慢镜处必须写明从哪一刻开始、到哪一刻结束（如"腾空顶点 0.3-0.5s"），其余变速留给剪辑
```

- [ ] **Step 2: prompt-rules.md B3 收紧**

B3 现文"慢动作只给决定性动作,每段 ≤2 处,其余镜头显式'正常速度'"后追加:

```
；打斗段终检必答两问："本段慢镜共几处？每处对应交手账哪一拍胜负手（R编号）？"——答不出=不通过 [drama-skills 改写: fight-craft.md]
```

- [ ] **Step 3: 验证**

Run: `grep -n "胜负手" references/cinematography.md references/prompt-rules.md`
Expected: 两文件各≥1命中,且 cinematography 判据含【峰】与交手账双来源
Run: `grep -c "慢镜" references/action-combat.md`(确认 action-combat 只有指针无判据全文——单一事实源)

- [ ] **Step 4: Commit**

```bash
git add references/cinematography.md references/prompt-rules.md
git commit -m "feat: 决定性动作操作判据(胜负手/【峰】双来源) + 打斗段终检两问

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 4: F4-F7 打斗内容四件套(拆镜三拍/打击呈现/方位纪律/景别阶梯)

**Files:**
- Modify: `references/action-combat.md`(§4 Spatial & Distance 扩、§5 Impact & Recovery 扩、§6 Camera 扩)

**Interfaces:**
- Consumes: Task 2 交手账(回合是三拍容器的装填单元)
- Produces: "多镜容器三拍"结构名与"接触发力时段单出手者"裁决句——Task 5(F10 可生成性打斗专条)引用不重写

- [ ] **Step 1: 读源取例句**

Read `fight-craft.md` §2(三拍容器+生成端真相句)、§3(打击三件套+落空砸环境+缠斗单控制)、§4(围攻方位)、§5(景别阶梯+竖屏纵深),摘例句原文

- [ ] **Step 2: §6 Camera 节扩——回合拆镜决策序+三拍容器(F4)**

按 spec F4 全文落位,必含:三选一决策序(多镜容器默认/整回合一镜仅当最短时长装得下/单独成镜仅缴械·决定性一击·改变选择的反应)、三拍例句("起手的中景→打击的特写→余波的中景,各拍仍各自成镜;剪辑在生成出来的切点处紧剪,打击特写只留拳到前后的一小段")、生成端真相句逐字("**镜头给多长,模型就把这几下拉多长,回合中间会出现停顿;正文里写'快''一气呵成'或逐秒时间,都不能把动作压回真实速度**")

- [ ] **Step 3: §5 Impact 节扩——打击呈现三件套(F5)**

标题改 `## 5｜Impact & Recovery（命中反馈分型 + 打击呈现）`;现有分型表保留,新增"打击呈现"小节按 spec F5 全文:落空/格挡/砸环境→稳定侧面或斜侧中景一框看清+**"武器落空砸在环境上(火星、水花、凹痕)比砸在人身上更好生成,也更能说明力道"**;打到人三件套(轴线同侧肩后遮接触点/画外闯入打击特写/反应方向必须与来力一致+声音余波);缠斗单控制("一镜只写一个控制…两个状态,中间角力用声音和一次发力带过");§8 接触镜处置按 R3 改写(难生成→走 F11 改写阶梯,不做预先降级实现——F11 在 Task 5 落地,此处写指针"改写阶梯见 prompt-rules.md 可生成性节")

- [ ] **Step 4: §4 Spatial 节扩——多对手方位纪律(F6)**

按 spec F6 全文:每对手固定方位锚/每回合只有一个对手出手其余停在看得见的等待位置/换对手=换轴先全景或中全景重建/画外对手从站位记录那一侧入画/"慢动作、特写、群众反应或解说不能替代丢失的空间阶段"/对手战术调整可追溯("避免每轮都重置成同一站位")。与 §8"多人混战拆1v1"注明上下游(方位纪律是编排层,拆1v1是生成端降级实现)

- [ ] **Step 5: §6 Camera 节补景别阶梯(F7)**

按 spec F7 全文:"每个新阶段的第一镜用全景或中全景交代距离;交手用中景或双人中全景,**能看到两个人的脚——距离靠脚下读出来**;近景和特写只给信息:握紧的武器、脱手的落点、决定性一击之后的脸";竖屏"把交手的方向摆成朝向或背离镜头的纵深,或者斜线"

- [ ] **Step 6: 查重+验证**

Run: `grep -rn "三拍\|打击特写\|方位锚" references/ | grep -v action-combat`(应零命中或仅指针——打斗规则唯一家在 action-combat)
Run: `grep -c "drama-skills" references/action-combat.md`(≥4,每小节出处标注)
Walkthrough:用 Task 2 的屋顶三人围攻样例走 §4+§6——每回合能否唯一出手者?换对手处有无全景重建镜?

- [ ] **Step 7: Commit**

```bash
git add references/action-combat.md
git commit -m "feat: 打斗四件套——回合拆镜三拍容器/打击呈现三件套(落空砸环境+画外闯入+来力一致)/围攻方位纪律/打斗景别阶梯

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 5: F10+F11 可生成性前置门(通用层+打斗专条+重叠原则冲突裁决)

**Files:**
- Modify: `references/prompt-rules.md`(零节四大底层认知后新增 `### 0.7 可生成性前置门`;重叠原则处加边界句)
- Modify: `references/action-combat.md`(§6/§7 加打斗接触专条)
- Modify: `SKILL.md`(回退阶梯"结构判定"前置失败征兆一句指针)

**Interfaces:**
- Consumes: Task 4 的三拍容器(打斗专条引用)
- Produces: 改写五法阶梯(①换承担者②拆相邻镜③换停留④交声音⑤交回上游)——Task 8(C13④"生成难度走改写阶梯")引用此阶梯名

- [ ] **Step 1: 读源**

Read `generability.md` §2-7(四类高风险/比划测试/改写五法/失败征兆/VID-21/VID-28 打斗专条全文与例句)

- [ ] **Step 2: prompt-rules.md 新增 0.7 节(通用层 F11)**

按 spec F11 全文落位,必含:适用条件("只在生成模型承担画面时适用;形态未声明不预先裁剪")、四类高风险写法各配原文例句(精确拦截/不可见内部状态"像是听见了什么→眉头猛地皱起,转头看向门口"/否定式动作/精细编排链"四秒内四步双手,平均每步只剩一秒")、**比划测试**逐字、放心写vs需要改写对照表、改写五法按序(第⑤步=交回上游修订,"不在提示词里改掉戏剧结果";按 R3 不做预先降级实现)、失败征兆清单(六条,含"把可生成性当成删戏的理由,而不是换实现方式的理由")。出处 `[drama-skills: generability.md#2-6 VID-21]`

- [ ] **Step 3: 重叠原则冲突裁决(prompt-rules 骨架A"并行/打斗场面"处)**

在"多组动作重叠发生,不依次排队"句后加边界句:

```
（边界裁决：重叠原则适用于**非接触动作与环境层**——背景错峰/环境动态/非接触的多线动作；**接触发力时段单出手者**——两人同一时段同时发力=精确拦截高风险 [drama-skills: generability.md#7]，重叠原则不豁免。先后动作的咬合写成"棍还在半路对方已经偏身"与分段写法实测无差别，咬合靠剪辑在动作中途切换）
```

- [ ] **Step 4: action-combat.md 打斗接触专条(F10)**

§6 或 §7 加小节(按 spec F10 全文):每时段单出手者+时间戳例句(`0–1.5秒 他抡起木棍朝对方头顶劈下；1.5–3秒 对方上身朝自己右侧一偏，木棍擦着左肩落空`)/写路线和反应不写接触点形变(例句对照:`右拳从镜头前方朝他下巴方向挥过，他的头猛地朝左甩开，踉跄后退两步` vs 禁写`拳头打在脸上/脸被打得变形`)/左右按人物身体说+方向按场景锚点说("画左画右机位一换就反")/变速另作决定(默认正常速度,慢动作只给决定性那一下并写明起止)。出处 `[drama-skills: generability.md#7 VID-28]`

- [ ] **Step 5: SKILL.md 回退阶梯前置**

"先做结构判定"句前加一句:

```
**进阶梯前先过可生成性**（prompt-rules 0.7）：失败征兆清单命中（三步以上手部编排/推断词/否定式动作/双主体同物件精确用力）→ 先按改写五法改实现方式，不改戏剧结果。
```

- [ ] **Step 6: 查重+验证**

Run: `grep -rn "比划测试\|精确拦截" references/`(唯一家=prompt-rules 0.7,action-combat 只指针)
Run: `grep -n "重叠" references/prompt-rules.md references/action-combat.md`(确认边界句已挂)

- [ ] **Step 7: Commit**

```bash
git add references/prompt-rules.md references/action-combat.md SKILL.md
git commit -m "feat: 可生成性前置门——四类高风险+比划测试+改写五法(0.7节) + 打斗接触专条(单出手者/路线反应/身体左右) + 重叠原则边界裁决

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

## Step 2 · 分镜/运镜层(spec §4 第二节)

### Task 6: C1 运镜功能决策表 + C2 全库措辞审计

**Files:**
- Modify: `references/cinematography.md`(:159 最稳5种删除;一节口诀前插决策表;:190 改写;:250 去品牌词;二节双方案表按 R3 处置)
- Modify: `references/director-styles.md`(:89/:119 括注删除)
- Modify: `references/prompt-rules.md`(:32 去品牌词)

**Interfaces:**
- Produces: **决策表行号 R1-R7**(CT1 的引用目标):R1=人物移动(跟拍/横移) R2=新信息进画(摇/俯仰/后拉) R3=台词压身(缓推) R4=关系重估(环绕) R5=高度有意义(升降) R6=情绪爆发/重大反转(短促推近) R7=固定(最后一行)——Task 7(A12门)、Task 19(K6 校验)按 R1-R7 解析;双方案表撤销后 GATE1 呈现项由 Task 8 的分配表接管

- [ ] **Step 1: 读源取决策表原文**

Read `shot-craft.md` L172-201(SHT-04 决策表 7 行+三条咬人条款+写法强制)

- [ ] **Step 2: cinematography.md 一节插入功能决策表**

在 `## 一、运镜库` 的 40 种列表**之前**(选择发生在查库之前)插入 `### 运镜功能决策表（先查此表定功能，再进运镜库选具体写法）`,内容按 spec C1:7 行表(功能判据→运镜族,行号 R1-R7 显式标注)+ 三条咬人条款逐字("**固定是这张表的最后一行,不是起点**"/"只写'运镜:固定'说不出是上表哪一行,**等于没有选**"/写法强制"运镜:<行为>,<从什么时候开始、停在哪里>;<为什么>")+ shot-craft 例句逐字摘入("缓推,他说出'这单我接了'时开始,停在眼睛")。现"情绪映射口诀"降为决策表之后的二次参考,加一句"口诀的输入是情绪词(模糊),决策表的输入是本镜功能(可判定)——先功能后情绪"。出处 `[drama-skills: shot-craft.md#SHT-04]`

- [ ] **Step 3: 删除 :159"最稳 5 种"(A类)**

原句"**最稳 5 种**:慢推、慢拉、慢摇、固定机位+主体动、轻微横移。一切复合运镜拆成单运动"——删除"最稳 5 种"列表,保留物理事实:"一切复合运镜(dolly+zoom、orbit+push)拆成单运动"(这是防抖事实,非选择建议)。前句"运动越快、运镜越复合、时长越长,崩坏概率越高"保留(参数事实),但删掉任何"所以优先选慢/固定"式推论

- [ ] **Step 4: 改写 :190(A类)**

"主体动则镜头选固定/极慢(这本来就是'最稳 5 种'规律的延伸…两大稳定组合)"→"双重高速=双重抖动源叠加:运镜与主体运动不要同时高速——镜头动则主体动作放缓(或静止),主体高速运动则镜头运动让位或降速+平滑参数(二·五节)。(选择哪种运镜仍由功能决策表定,'让位'不等于'选固定')"

- [ ] **Step 5: director-styles.md :89/:119 括注删除(A类)**

"(AI 视频最稳组合)"/"(最稳)"删除;侯孝贤"固定机位+主体动"风格事实保留,不加评价词

- [ ] **Step 6: :250 与 prompt-rules:32 去品牌词(C类)**

"动作戏单镜 1-2s 最稳"→"动作戏单镜 1-2s(太长=模型自由发挥;太短=没有过程只有结尾,提示词被跳过)"——删"最稳"留因果

- [ ] **Step 7: 双方案表处置(R3/A类)**

`## 二、AI 视频运镜避坑与双方案表`节:双方案表(主方案/保底方案 GATE1 二选一)**撤销**,节改名 `## 二、AI 视频运镜避坑`,原表内容处置:表中"高风险运镜"的具体写法风险事实(如复合运镜崩坏率)保留为避坑条目;"保底方案"列删除;节首加一句"强调手段与高难度运镜的管理走「峰值与强调手段」节(C13)——生成难度是走改写阶梯的触发器,不是回避表现力的理由;降级只作生成失败后的回退兜底(回退阶梯见 SKILL.md)"

- [ ] **Step 8: 全库措辞扫描(Review Focus #2)**

Run: `grep -rn "最稳\|保险\|安全牌\|最简单\|稳定组合\|稳妥\|省心\|傻瓜\|无脑\|不易翻车\|保底" SKILL.md references/ assets/ | grep -v _archive`
逐行人工定性:A类(选择层默认入口)删改;B类(失败后兜底:回退阶梯"换保底运镜方案"、content-safety 反应式降级)保留;C类(参数事实)去品牌词。**SKILL.md 回退阶梯③"换保底运镜方案"是 B类保留**(生成失败后触发)。**每行处置结果记入 commit message**

- [ ] **Step 9: 验证**

Run: `grep -rn "最稳" SKILL.md references/ assets/ | grep -v _archive` → 零命中
Run: `grep -n "R1\|R7" references/cinematography.md` → 决策表行号存在
Walkthrough(Review Focus #4):取一段 6 镜对话戏+1 段追逐戏,每镜按决策表填 CT1 动机格式——每镜能否唯一命中一行?固定镜是否都写出了 R7 理由?

- [ ] **Step 10: Commit**

```bash
git add references/cinematography.md references/director-styles.md references/prompt-rules.md SKILL.md
git commit -m "feat: 运镜功能决策表(R1-R7,固定是最后一行) + 全库措辞审计(A类删改/B类保留/C类去品牌词,双方案表撤销)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 7: C3 条件触发门 A12 + C7 动机五类词表 + templates 01 表头改 CT1

**Files:**
- Modify: `references/prompt-rules.md`(校验 A 层新增 A12;B1 改写为指向 A12)
- Modify: `references/cinematography.md`(一节加五类词表小节)
- Modify: `assets/templates.md`(01 分镜表"运镜动机"列表头注改 CT1 格式;自检行改条件式)

**Interfaces:**
- Consumes: Task 6 的 R1-R7 行号
- Produces: A12 门文本(条件触发:奔跑→跟拍族/揭示→摇后拉族/峰值→强调手段)+ CT1 动机列格式落地——Task 19(K6)按 CT1 regex 校验;12 族归并表(现有)作为族指认语言

- [ ] **Step 1: prompt-rules.md A 层新增 A12**

在 A11 行后加(按 spec C3 全文):

```
| **A12** | **运镜条件触发门** | 写完 01 分镜表逐行回读：情节点清单含奔跑/追逐→跟拍族≥1 且指认镜号；含信息揭示/发现→摇/后拉/揭示族≥1；含【峰】标记→强调手段≥1（配额见 cinematography「峰值与强调手段」节）；对话戏全程固定+硬切合规，但每镜"运镜动机"列必须符合 CT1 格式（五类词+决策表行号），写"固定"必须带 (R7)。缺项=不通过 [drama-skills 改写: shot-craft.md#SHT-04 L196] |
```

- [ ] **Step 2: B1 改写**

B1 现文(族归并计数+"数字不是判据")改为:"B1 效果库使用→**已升级为 A12 条件触发门**(计数口径保留为 A12 的族指认语言,见 cinematography 一节);B1 编号保留占位防下游引用断裂,内容指向 A12"

- [ ] **Step 3: cinematography.md 一节加五类词表(C7)**

决策表之后加小节 `### 运镜动机五类封闭词表`:reveal(新信息进视野)/pressure(距离收紧压力增大)/alignment(从旁观转向贴近某角色立场)/relationship(重组两人距离权力)/transition(把注意交给终点)+ CT1 格式定义与示例 + "自由文本动机('氛围需要')不过 A12"。出处 `[drama-skills: camera-audio-continuity.md#L22-28]`

- [ ] **Step 4: templates.md 01 分镜表同步**

"运镜动机"列表头注加 CT1 格式说明与示例;示例行"缓慢推近 / —"改为"缓慢推近"(运镜列——双方案已撤销,删"/ —");动机示例填 `pressure(R3)：台词正压到她身上`;01 自检行"效果库使用自检:运镜种类{N}种…"改为条件式:"A12 条件触发回读:奔跑/追逐→跟拍族镜号{…};揭示→摇/后拉族镜号{…};【峰】→强调手段镜号{…};全部动机列符合 CT1"

- [ ] **Step 5: 验证+walkthrough**

Run: `grep -n "A12" references/prompt-rules.md assets/templates.md SKILL.md`(prompt-rules+templates 命中;SKILL.md 硬规则11行 Task 8 统一改)
Walkthrough(Review Focus #4):用 Step 4 的示例行验证 CT1 regex `^(reveal|pressure|alignment|relationship|transition)\(R[1-7]\)：` 可解析;再取一个"固定机位对话镜"填 `transition(R7)：交锋已尽，固定让她说完` 验证可解析

- [ ] **Step 6: Commit**

```bash
git add references/prompt-rules.md references/cinematography.md assets/templates.md
git commit -m "feat: A12 运镜条件触发门(奔跑→跟拍/揭示→摇拉/峰值→强调) + 动机五类封闭词表 + 01表头CT1格式

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 8: C13 峰值稀缺品范式(慢镜预算节升级+【峰】标记+GATE1 分配表+硬规则11改写)

**Files:**
- Modify: `references/cinematography.md`(段长预算与慢镜预算节→升级改名"峰值与强调手段")
- Modify: `assets/templates.md`(01 情节点清单加【峰】用法注;GATE1 锚定确认记录表"高风险运镜双方案"行→"峰值-强调手段分配表")
- Modify: `SKILL.md`(硬规则 11 改写;GATE1 呈现项改分配表)
- Modify: `references/prompt-rules.md`(B3 指向新节名;C6 冲击重复并入)

**Interfaces:**
- Consumes: Task 3 判据(已含胜负手/【峰】)、Task 6 决策表 R6、Task 7 A12
- Produces: 节名 `### 峰值与强调手段（稀缺品配额——B3/C6/F3 的唯一家）`;【峰】标记语法(CT4);GATE1 分配表格式——Task 19(K5)按 CT2 校验峰值标注可解析到 01

- [ ] **Step 1: cinematography.md 节升级**

`### 段长预算与慢镜预算` 改名 `### 峰值与强调手段（强调手段=稀缺品，只花在已点名峰值上）`,内容重组(段长预算保留为本节第一小节):①家族登记(慢镜/TimeRamp/冲击重复/短促推近/定格/闪白——一族同管)②先点名峰值再花手段(打斗=交手账★胜负手;文戏=情节点【峰】;每处标注 CT2 格式)③Task 3 已写的判据四条保留④冲击重复全文并入(C6:"打击、否定或翻盘需要观众理解其后果时,安排可读的承受者反应——独立反应镜/双人镜调度/群像反应均可"+"同一关键动作从两三个角度各给一次…只用在峰值。一集里处处重复,就没有哪一下是冲击了"+状态纪律"每个重复镜从同一动作前状态走到同一动作后状态,第二遍不能在第一遍的结果上再做一次"[drama-skills: shot-craft.md#SHT-27/SHT-08])⑤生成难度不是回避理由(R3④:走 prompt-rules 0.7 改写阶梯,降级只作失败后兜底)

- [ ] **Step 2: templates.md 两处**

01 情节点清单表头注加:"情绪爆发/重大反转/打脸拍在情节点文本内嵌【峰】标记(强调手段的合法落点,CT4)";GATE1 表"高风险运镜双方案"行替换为:

```
| 峰值-强调手段分配表 | {本集峰值几处（打斗=交手账★/文戏=【峰】情节点）、每处花什么手段（慢镜/冲击重复/短促推近/定格/闪白）、对应镜号——用户确认/否决/加峰} |
```

- [ ] **Step 3: SKILL.md 硬规则 11 与 GATE1 改写**

硬规则 11 要点改:"**效果库不许落灰+强调手段是稀缺品**:运镜按功能决策表选(R1-R7,固定须报行号);强调手段只花在已点名峰值(交手账★/【峰】),每处 CT2 标注;禁全片只用基础款,也禁处处强调——家:cinematography 决策表+峰值节";GATE1 呈现项"高风险运镜的双方案选择(如有)"改为"峰值-强调手段分配表"

- [ ] **Step 4: prompt-rules.md 指针同步**

B3 与 C6 相关行改指"cinematography「峰值与强调手段」节(唯一的家)"

- [ ] **Step 5: 验证+walkthrough**

Run: `grep -rn "双方案" SKILL.md references/ assets/ | grep -v _archive` → 零命中(或仅历史迭代记录类文档 create.md 不动)
Run: `grep -c "峰值与强调手段" references/cinematography.md references/prompt-rules.md references/action-combat.md SKILL.md` → 各≥1
Walkthrough(Review Focus #4):样例打斗段(交手账 R1-R5,R3 为★)+文戏(情节点 2【峰】)——为 R3 与情节点 2 各分配手段并写 CT2 标注;再故意给 R1 普通命中加慢镜,确认按新规则可判违规(无峰值标注)

- [ ] **Step 6: Commit**

```bash
git add references/cinematography.md references/prompt-rules.md assets/templates.md SKILL.md
git commit -m "feat: 峰值稀缺品范式落地——「峰值与强调手段」节(家族登记/先点名后花/冲击重复并入) + 【峰】标记 + GATE1分配表取代双方案 + 硬规则11改写

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 9: C4+C5 对白场切法 + 工作景别

**Files:**
- Modify: `references/cinematography.md`(三节景别表后新增两小节)

**Interfaces:**
- Produces: "工作景别"与"切镜必须变一项"规则文本——Task 19(K 门不查此条,审美)但 walkthrough 依赖;与现有 B2"避免连续3同景别"的关系(B2 保留为快速口径)

- [ ] **Step 1: 读源取例句**

Read `shot-craft.md` SHT-29(对白场六条)与 `production-shot-grammar.md` L109-133(工作景别+客厅摊牌完整例句)

- [ ] **Step 2: 新增小节"三·五、对白场默认切法"(C4)**

按 spec C4 六条全文,三条加粗("**默认给听者**——重要的一句落下时,切到听的人,让观众看见它打中了谁"/"**特写只给要落地的台词**"/"**插入镜是便宜的节奏工具**——手机屏/手/戒指可插在长台词中间");注明与正反打画面占位(prompt-rules)的分工("占位管怎么摆,本节管何时切给谁");与漏洞 7(剧本层道具互动)上下游互引。出处 `[drama-skills: shot-craft.md#SHT-29]`

- [ ] **Step 3: 新增小节"三·六、工作景别与切镜理由"(C5)**

按 spec C5 全文:工作景别机制("先开宽一档,第二镜落到工作景别,之后相邻一格收放;宽景和特写是标记事件,用过就回来")+ 客厅摊牌例句逐字摘入 + "**已经切镜:新镜必须在景别、机位角度或人物关系里至少改变一项**——相邻两镜三项全同,这个切点没有存在理由(修法:沿阶梯相邻一格一收一放,或并镜)";B2 关系注:"B2'无连续3同景别'保留为快速口径,本条是结构判据;正反打豁免继续有效"。出处 `[drama-skills: production-shot-grammar.md#五节]`

- [ ] **Step 4: 验证+walkthrough**

Run: `grep -n "工作景别\|默认给听者" references/cinematography.md`(各≥1)
Walkthrough:取 4 镜对话戏(摊牌类),按三·五+三·六重排——第 2 镜是否落到工作景别?重要台词处是否切听者?每对相邻镜是否至少变一项?

- [ ] **Step 5: Commit**

```bash
git add references/cinematography.md
git commit -m "feat: 对白场默认切法(默认给听者/特写只给落地台词/插入镜) + 工作景别与切镜必须变一项

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 10: C8-C12 次级五条(调度语义/正反打四条/水平角度/B13扩/首尾帧判定)

**Files:**
- Modify: `references/consistency.md`(开场走位机制节加"走位的戏剧语义"小节,C8)
- Modify: `references/cinematography.md`(三节正反打豁免旁加配对四条 C9;四节机位角度表扩水平角度栏 C10)
- Modify: `references/prompt-rules.md`(B13 扩固定机位三件事 C11;骨架B选择器加首尾帧判定行 C12)

**Interfaces:**
- Consumes: 无新依赖(独立条目)
- Produces: 水平角度词表(正面/斜侧四分之三/正侧/后斜侧/背面)——K 门不查,分镜表可选填

- [ ] **Step 1: 读源**

Read `blocking-playbooks.md` L124-133(正反打四条)+`shot-craft.md` L104-117(调度语义)+`production-shot-grammar.md` L139-160(角度三栏)+`camera-audio-continuity.md` L36-47(固定三件事)+`keyframe-craft.md` L106-115(首尾帧)

- [ ] **Step 2: C8 调度语义** → consistency.md 开场走位机制节后加小节"走位的戏剧语义":"靠近可以施压或寻求结盟;转身可以拒绝;占住出口可以控制;碰触证据可以暴露知情。**不要只为增加运动而让人物无理由走动**;不要为了'画面丰富'让人物轮流起身、倒水、看窗——单房戏的运动来自:说话或沉默的策略→对方怎样接住→物件、目光或空间发生什么→谁暂时掌权";LOCATION MAP 距离常数注加一句"距离同时携带权力含义(六米=对峙,半臂=贴身)" `[drama-skills: shot-craft.md#场面调度, blocking-playbooks.md]`

- [ ] **Step 3: C9 正反打配对四条** → cinematography.md 三节正反打豁免条款旁:①屏幕方向互补(两镜都望同侧=观众读成看第三个画外者)②视线高度按身高差匹配(双平视抹平身高差则"逼近"失去压迫感)③过肩镜写明前景是谁的肩、占画多少④A/B 对称是主动选择(对称=势均力敌,不对称=权力倾斜,选不对称写理由) `[drama-skills: blocking-playbooks.md#L124-133]`

- [ ] **Step 4: C10 水平角度词表** → cinematography.md 四节机位角度表扩一栏:水平角度(正面/斜侧四分之三/正侧/后斜侧/背面——"回答观众被允许读到多少表情、站在谁的一侧")+警示例句逐字("写'俯拍'时其实想要的是'从她背后越过肩膀'——那是水平角度不是高度,下游按字面给了从上往下的机位,权力关系当场反了")+"平视是主动表示势均力敌,不是'没选'";与机位数值化三要素分工注(数值化管高度/俯仰,本栏管水平朝向) `[drama-skills: production-shot-grammar.md#角度三栏]`

- [ ] **Step 5: C11 固定机位三件事** → prompt-rules.md B13 追加:"固定机位镜头写满三件事:①固定的构图(景别、机位高度、**轴线哪一侧**)②画面内还有什么在动(现有环境动态层)③**保持多久**——摄影机一栏空着会被执行端读成可以自由漂移,长出一次没人要过的推近或环绕" `[drama-skills: camera-audio-continuity.md#L36-47]`

- [ ] **Step 6: C12 首尾帧判定** → prompt-rules.md 骨架B选择器表格加一行:"路径本身是戏的镜头(夺取过程/跟随移动/逐步逼近)不适合首尾帧夹逼——两端差异越大插值越自由(实证:首尾帧模式 3 次里 2 次文件夹没打开到位;只给首帧+终点写正文的 3 次全部到达);某动作是本镜存在理由时,移到某一端或拆镜" `[drama-skills: keyframe-craft.md#L106-115]`

- [ ] **Step 7: 验证**

Run: `grep -rn "走位的戏剧语义\|屏幕方向互补\|水平角度\|轴线哪一侧\|路径本身是戏" references/`(五条各就位,唯一家正确)
Run: 查重 `grep -rn "占住出口" references/`(仅 consistency 一处全文)

- [ ] **Step 8: Commit**

```bash
git add references/consistency.md references/cinematography.md references/prompt-rules.md
git commit -m "feat: 次级五条——调度权力语义/正反打配对四条/水平角度词表/固定机位三件事/首尾帧路径是戏判定

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

## Step 3 · 剧本/台词层(spec §4 第一节)

### Task 11: S1-S5 台词组(议程卡/五说/策略库/潜台词三层/声音五维)

**Files:**
- Modify: `references/screenwriting-craft.md`(漏洞 2 节整体升级——本节是台词规则唯一家)

**Interfaces:**
- Produces: "台词议程卡"(5 问浓缩版)与"行动动词标注"要求——Task 13(S8 自检操作程序)的漏洞 2 程序引用它们

- [ ] **Step 1: 读源摘例句**

Read `dialogue-craft.md` §2(议程表)/§3(五说+策略库+反制)/§4(潜台词三层)/§6+§10.5(声音五维+交换测试),摘全部弱/强对照例句原文

- [ ] **Step 2: 漏洞 2 节升级(改写而非追加——查重风险中,先 grep"台词指纹"确认现有全文范围)**

新结构:①**台词议程卡**(S1,写对话前每角色填:想让对方做什么/最怕被看见什么/筹码/不能公开说的事及原因/策略与受阻后换法/底线——核心句"两人可以表面谈同一件事,实际争不同结果")②**台词是行动**(S2,"门在九点锁"五说例句逐字+判据)③**策略库与受阻**(S3,14 策略+反制 7 法列表+"若一方每句话都成功,对话会变成演讲""重复同一句要求只会延长时长")④**潜台词三层**(S4,现有"直白版同义=失败"保留,补风险层+反向保护句"若现场没有外人、秘密或权力差,这句就只是生活指令,不自动具有潜台词"+可观察线索四种)⑤**声音五维**(S5,五维+三声音例句逐字+"口头禅/语气词是最后一层微调,不是区分主体"+交换说话者测试)——现有"台词指纹"条目(口头禅/语气词/称呼)压缩为⑤的末层,保留"写进 02 锚定"联动句。全部标 `[drama-skills: dialogue-craft.md#节]`

- [ ] **Step 3: 验证**

Run: `grep -n "议程卡\|同一事实五说\|交换说话者" references/screenwriting-craft.md`(各≥1)
Run: `grep -rn "台词指纹" SKILL.md references/`(硬规则/SKILL 指针若引用"台词指纹"措辞,同步为"声音五维与台词指纹")
Walkthrough:用"房东催租,租客拖延"样例填议程卡两行+写 4 轮对话——每句能否标出行动动词?互换两人台词后情节关系是否改变(应变)?

- [ ] **Step 4: Commit**

```bash
git add references/screenwriting-craft.md
git commit -m "feat: 台词行动理论——议程卡/同一事实五说/策略库+反制/潜台词三层/声音五维+交换测试(漏洞2节升级)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 12: S6+S7+S9+S10 结构组(因果升级链/当集兑现/场景发动机/反对七式)

**Files:**
- Modify: `references/screenwriting-craft.md`(新增"一·四 场景与升级因果"节,置于漏洞清单后、钩子纪律前;钩子纪律节并入 S7;漏洞 5 节扩写 S10)
- Modify: `SKILL.md`(阶段 1a 加一行指针)

**Interfaces:**
- Produces: 升级六问与"因为/但是"朗读诊断——Task 13(S8)的拖沓检查程序引用;【峰】标记(CT4)的情节点来源在本节产生(情绪爆发/重大反转拍即【峰】候选)

- [ ] **Step 1: 读源**

Read `episode-design.md` §3.4/§5.2/§5.3/§3.6/§4.2 + `script-craft.md` §3/§3.2

- [ ] **Step 2: 新增"一·四 场景与升级因果"节**

内容(按 spec S6+S9 全文):①场景发动机工作卡 8 项+转向测试(逐字:"转向前人物准备做什么?转向后为什么不能照做?如果答案只是'更生气',还缺少新的事实、筹码、关系或决定"+"不以对手无因沉默或离场代替转向")+目标可执行化例句②因果升级链选择模板+"然后/所以/但是"朗读诊断③升级六问+"没有可引用的状态变化,不能只凭更强烈的表演词声称升级"④情节点清单标【峰】的指引(与 CT4 衔接:"情绪爆发/重大反转/打脸拍=【峰】候选,分镜阶段强调手段只花在【峰】上") `[drama-skills: script-craft.md#3, episode-design.md#3.4/5.2/5.3]`

- [ ] **Step 3: 钩子纪律节并入 S7**

现"一·五 钩子与悬念纪律"加第 6 条"当集兑现":留下新压力前先给局部结果(四选:能力或代价显形/回收部分旧问题/关系变化/不可撤回选择)+"'马上要揭晓'不是回报"+出去压力合法性(由本集结果产生;"不成立的替代品:无来源的新人物踹门/反派重复上一集威胁")+与第 3 条"末拍悬念"关系注(一给一收,防将来漂移) `[drama-skills: episode-design.md#3.6/4.2]`

- [ ] **Step 4: 漏洞 5 扩写 S10**

现反派三问保留为特化版,前加"反对不是说'不'(7 种反对方式)"列表+"有效反对会迫使焦点人物更换策略,而不是延长同一轮喊话" `[drama-skills: script-craft.md#3.2]`

- [ ] **Step 5: SKILL.md 阶段 1a 指针**

"按其 7 大漏洞自检清单逐条过"句后加:"冲突场景先过场景发动机工作卡与升级六问(screenwriting-craft 一·四节),分集叙事再过当集兑现(一·五节第 6 条)"

- [ ] **Step 6: 验证+walkthrough**

Run: `grep -n "场景发动机\|升级六问\|当集兑现\|7 种反对" references/screenwriting-craft.md`(各≥1)
Walkthrough:取一段"主角被当众羞辱后反击"的两场戏,用升级六问对比两场——答不出任何一问则按规则合并/重写;标出【峰】位置

- [ ] **Step 7: Commit**

```bash
git add references/screenwriting-craft.md SKILL.md
git commit -m "feat: 结构组——场景发动机+转向测试/因果升级链+因为但是朗读/升级六问/当集兑现/反对七式

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 13: S8 自检操作程序化 + 硬规则 7 裁决

**Files:**
- Modify: `references/screenwriting-craft.md`(第二节产出格式的"7 大漏洞自检结果"表升级填法;新增第 11 条拖沓检查)
- Modify: `assets/templates.md`(01 GATE1.5 记录表"7 大漏洞自检"行格式同步)
- Modify: `SKILL.md`(硬规则 7 补裁决句)

**Interfaces:**
- Consumes: Task 11 的行动动词标注、Task 12 的升级六问
- Produces: 证据引用格式("场N:「台词原文」")——K 门不查(审美术),但 GATE1.5 呈现格式依赖

- [ ] **Step 1: 自检表升级填法(S8)**

按 spec S8 全文:每条漏洞自检结果栏必须**引用证据**(哪一场哪一句,格式"场N:「…」");操作程序替换主观问句——漏洞1/7:"圈出心理词,逐个指定载体(行为选择/证据反应/空间动作/关系动作/标记的声音)";漏洞2:"删掉角色名朗读,能否凭策略和措辞辨认;每句台词旁标注行动动词(逼问/遮掩/交换/试探…),标不出且不承担必要信息的句子删掉或改成动作";新增第 11 条拖沓检查:"快扫一遍全剧本(比正常更快的速度),记下需要停下来才想明白的位置=信息挤在一起;相邻冲突答不出升级六问任何一条即合并或重写;扫完后情绪上有没有起伏,还是只知道发生了一串事"+"每一遍只解决一种失败"(因果遍/可表演遍/具体性遍/声音潜台词遍/经济性遍/扫读遍) `[drama-skills: script-craft.md#9/12, dialogue-craft.md#10]`

- [ ] **Step 2: templates.md 01 GATE1.5 行同步**

"7 大漏洞自检"行的示例格式改为带证据引用:"1 小说化 ✓场3心理词2处已指定载体 / 2 台词 ✓删名朗读可辨+行动动词全标 / … / 11 拖沓 ✓快扫无停顿点+相邻冲突六问过"

- [ ] **Step 3: SKILL.md 硬规则 7 裁决句**

硬规则 7 要点末尾补:"**覆盖≠不删**:用户定稿的情节点不擅自删;但场景级合并与信息密度优化不属删剧情(处置三选一:合并/让变化真正发生/删去移入冲突——screenwriting-craft 一·四节)" `[drama-skills: script-craft.md#2.2/9.4]`

- [ ] **Step 4: 验证+walkthrough**

Run: `grep -n "删掉角色名朗读\|快扫\|覆盖≠不删" references/screenwriting-craft.md SKILL.md`(各就位)
Walkthrough:取 vigen 任一历史项目剧本段(firepunch_ep1/02_剧本.md 若格式可读),对一场戏跑"删角色名朗读"——能否辨认?不能则证明程序可判定(而非主观打勾)

- [ ] **Step 5: Commit**

```bash
git add references/screenwriting-craft.md assets/templates.md SKILL.md
git commit -m "feat: 自检操作程序化(证据引用+删名朗读+快扫遍+六遍修订) + 硬规则7裁决句(覆盖≠不删)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 14: S11-S16 剧本次级六条

**Files:**
- Modify: `references/screenwriting-craft.md`(漏洞 1 扩写 S11;漏洞 3 并入 S12+S13;新增"能演的不说"小节 S14+S16;第二节人物表格式加 S15)

**Interfaces:**
- Consumes: Task 11 漏洞 2 节(台词相关不重复落位)
- Produces: 无下游依赖

- [ ] **Step 1: 读源摘例句**

Read `script-craft.md` §4/§4.4/§3.4、`reveal-reversal-payoff.md` §3/§4、`story-craft.md` §4、`dialogue-craft.md` §5,摘对照例句

- [ ] **Step 2: S11 意义与载体分离** → 漏洞 1 节扩写:5 类载体+弱/强对照例句逐字("他很心虚,眼神复杂"→"他把盖章页翻过去,只递出没有签名的那一面。门外的人伸手时,他仍按着纸角")+痛点规则("'他一直被人看不起'不是痛点;'酒席上,反派当众把酒泼在他脸上'才是——观众看见了被压下去的那一下,后面的回报才有落点")

- [ ] **Step 3: S12+S13** → 漏洞 3 节并入:误会四判据(逐字:"误会的失效点几乎总在解除的那一刻"+四条)+巧合方向性("把人推进麻烦可以,把人从麻烦里捞出来不可以;巧合送来的必须是负担不是礼物")+反转一句话测试模板("因为<已建立的事实/选择>,原计划<为何不再成立>,人物现在只能在<新代价A/B>之间行动")+弱反例("陌生人突然出现宣布一切都是梦")+公平揭示五问

- [ ] **Step 4: S14+S16 新增小节"能演的不说(复述禁令)"** → VO 不复述画面+台词说清的下场不重演+"两种载体重复时,留演出来的那一个"+内心独白外化("大段'我穿越了''我一定要…'换成一个动作加一句台词")+说明改传递三句判据("人物不会为了观众重复彼此都熟知的事实/过去事件只说当前动作需要的最小片段/若一句台词只复述观众刚看到的因果,删掉后画面仍完整,就让人物回应结果")+弱/强对照例句("我们这家店是母亲二十年前开的…"→"你要真觉得这只是家店,就别拿母亲那把纸柜钥匙")

- [ ] **Step 5: S15 观众四问** → 第二节人物表格式("核心欲望"行下加):四问逐字+"至少答出一条,并且它要在第一集就能被看见"

- [ ] **Step 6: 验证**

Run: `grep -n "载体\|四判据\|一句话测试\|复述禁令\|观众四问" references/screenwriting-craft.md`(各≥1)
Run: 文件行数 `wc -l references/screenwriting-craft.md`(<800;预计 ~450)
Run: 单一事实源抽查 `grep -rn "泼在他脸上" references/`(仅一处)

- [ ] **Step 7: Commit**

```bash
git add references/screenwriting-craft.md
git commit -m "feat: 剧本次级六条——意义载体分离/误会四判据/反转一句话测试/复述禁令/说明改传递/观众四问

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

## Step 4 · check.py 薄校验层(spec §4 第四节,TDD)

### Task 15: check.py 骨架 + K1 台词逐字门(TDD)

**Files:**
- Create: `scripts/check.py`
- Create: `tests/__init__.py`(空文件)
- Create: `tests/test_check.py`
- Create: `tests/fixtures/good_project/`(01/04/05 最小合法样例,格式照 assets/templates.md)
- Create: `tests/fixtures/bad_dialogue/`(01/04/05,04 中一句台词与 01 定稿不一致)

**Interfaces:**
- Produces(后续 K 门任务全部依赖,签名冻结):

```python
MINIMUM_PYTHON = (3, 9)

@dataclass(frozen=True)
class Finding:
    gate: str    # "K1".."K10"
    file: str    # "01_方案与剧本.md" 等
    line: int    # 1-based；0=文件级
    message: str # 具体到"缺什么"，学 drama-skills 报错风格

class Project:
    """项目目录加载与解析缓存。"""
    def __init__(self, root: Path): ...
    def doc(self, key: str) -> list[str] | None:
        """key ∈ {"00","01","02","03","04","05","06"}；文件不存在返回 None（--partial 容忍）。"""
    def section(self, key: str, heading: str) -> list[str]:
        """返回 '## heading' 到下一个 '## ' 之间的行（含行号偏移信息）。"""

GATES: list[tuple[str, Callable[[Project, bool], list[Finding]]]]
# 每项 (门号, gate_fn)；gate_fn(project, partial) -> findings
# partial=True 时：依赖文件缺失的门静默跳过（返回 []），存在则照常查

def main(argv: list[str]) -> int:  # 0=全过 1=有findings 2=用法/IO错
```

- CLI 按 CT6;K1 解析契约:01 台词行=分场剧本节内 `^(\S{1,12})：(.+)$` 且**排除**以"第/格/镜/段/场景状态"开头的动作行(SCR-18 防误判,Review Focus #5);04 台词=引号内文本 `"…"|"…"|「…」`;05 台词=台词清单表"台词原文"列。判定:04/05 每条台词(去首尾空白)必须逐字存在于 01 台词集合(去首尾空白),否则 Finding

- [ ] **Step 1: 写 fixtures**

`good_project/01_方案与剧本.md` 含分场剧本节(3 句台词,说话人行格式)+情节点清单+分镜总览表(3 镜);`04_视频提示词.md` 含骨架A段落(台词与 01 逐字同)+`05_语音台词表.md` 台词清单(同)。**必含歧义陷阱行**:`第二格：一只手把杯子推过去。`(动作段,全角冒号开头——不得被解析为台词)
`bad_dialogue/` 复制 good 后把 04 中一句台词改掉一个字

- [ ] **Step 2: 写失败测试**

```python
# tests/test_check.py
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check

FIXTURES = Path(__file__).parent / "fixtures"

class TestK1(unittest.TestCase):
    def test_good_project_passes(self):
        p = check.Project(FIXTURES / "good_project")
        self.assertEqual(check.gate_k1(p, partial=False), [])

    def test_changed_dialogue_fails(self):
        p = check.Project(FIXTURES / "bad_dialogue")
        findings = check.gate_k1(p, partial=False)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].gate, "K1")
        self.assertEqual(findings[0].file, "04_视频提示词.md")
        self.assertIn("台词与01定稿不一致", findings[0].message)

    def test_action_line_with_fullwidth_colon_not_dialogue(self):
        # SCR-18 歧义陷阱：动作行不得进入台词集合（否则 good_project 会误报）
        p = check.Project(FIXTURES / "good_project")
        lines = p.doc("01")
        self.assertFalse(check._is_dialogue_line("第二格：一只手把杯子推过去。"))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 跑测试确认失败**

Run: `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest tests.test_check -v`
Expected: FAIL(ModuleNotFoundError: No module named 'check')

- [ ] **Step 4: 实现骨架+K1**

实现 `Project`(doc/section 按上面契约;编码 utf-8;Windows 换行兼容)、`Finding`、`_is_dialogue_line`(排除规则见 Interfaces)、`gate_k1`、`GATES=[("K1", gate_k1)]`、`main`(argparse:project_dir/--partial/--gate;输出 CT6 格式;exit code 契约)。全部类型注解,Python 3.9 兼容(不用 `X | Y` 运行时求值——用 `from __future__ import annotations`)

- [ ] **Step 5: 跑测试确认通过**

Run: `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest tests.test_check -v`
Expected: 3 tests PASS

- [ ] **Step 6: CLI 冒烟**

Run: `PYTHONDONTWRITEBYTECODE=1 python -B scripts/check.py tests/fixtures/good_project --partial` → exit 0
Run: `PYTHONDONTWRITEBYTECODE=1 python -B scripts/check.py tests/fixtures/bad_dialogue --partial` → exit 1,输出 `[K1] 04_视频提示词.md:<行号>: 台词与01定稿不一致：「…」`

- [ ] **Step 7: Commit**

```bash
git add scripts/check.py tests/
git commit -m "feat: check.py 骨架(Project/Finding/GATES/CLI按CT6) + K1台词逐字门(含SCR-18全角冒号防误判) — TDD

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 16: K2 时长门 + K3 锚定逐字门(TDD)

**Files:**
- Modify: `scripts/check.py`(加 gate_k2/gate_k3,注册 GATES)
- Modify: `tests/test_check.py`(加 TestK2/TestK3)
- Create: `tests/fixtures/bad_duration/`、`tests/fixtures/bad_anchor/`(复制 good 后各引入一处违规)
- Modify: `tests/fixtures/good_project/02_锚定表.md`(新建——K3 需要:目标模型节+色彩基调色号+角色锚定短语+风格圣经)

**Interfaces:**
- Consumes: Task 15 的 Project/Section 契约
- Produces: `gate_k2(project, partial) -> list[Finding]`、`gate_k3(...)` 同签名;02 解析契约:目标模型节内模型名(happyhorse/H3/MiniMax/Seedance→上限 15s,查不到=15s 并输出 warning 级 Finding? 不——宁松勿滥:查不到跳过上限检查只查 05 自洽);色号 regex `#[0-9A-Fa-f]{6}`;锚定短语=角色锚定表每角色"锚定短语"字段行

- [ ] **Step 1: 写失败测试**

```python
class TestK2(unittest.TestCase):
    def test_good(self):
        p = check.Project(FIXTURES / "good_project")
        self.assertEqual(check.gate_k2(p, False), [])
    def test_over_model_cap(self):
        # bad_duration: 01 分镜表某镜 生成时长 18s > 15s 上限
        p = check.Project(FIXTURES / "bad_duration")
        f = check.gate_k2(p, False)
        self.assertTrue(any(x.gate == "K2" and "超模型上限" in x.message for x in f))
    def test_dialogue_longer_than_shot(self):
        # bad_duration: 05 某行 朗读时长 6s > 所在镜头时长 4s
        p = check.Project(FIXTURES / "bad_duration")
        f = check.gate_k2(p, False)
        self.assertTrue(any("台词朗读超镜头时长" in x.message for x in f))

class TestK3(unittest.TestCase):
    def test_good(self):
        p = check.Project(FIXTURES / "good_project")
        self.assertEqual(check.gate_k3(p, False), [])
    def test_missing_hex(self):
        # bad_anchor: 04 某段 FORMAT 节缺 02 登记的色号 #2B3A55
        p = check.Project(FIXTURES / "bad_anchor")
        f = check.gate_k3(p, False)
        self.assertTrue(any(x.gate == "K3" and "#2B3A55" in x.message for x in f))
    def test_missing_character_anchor(self):
        # bad_anchor: 04 某段提到角色"沈砚"但该段无其锚定短语
        p = check.Project(FIXTURES / "bad_anchor")
        f = check.gate_k3(p, False)
        self.assertTrue(any("沈砚" in x.message and "锚定短语缺失" in x.message for x in f))
```

- [ ] **Step 2: 跑测试确认失败**(AttributeError: gate_k2)

- [ ] **Step 3: 实现 K2**

解析 01 分镜表"生成时长"列(`(\d+(?:\.\d+)?)s`)→ 对比 02 目标模型上限(map:happyhorse→15,h3/minimax→15,seedance→15;未识别模型→跳过,宁松勿滥);解析 05 台词清单"朗读时长"列与"所在镜头时长"列→ 朗读≤镜头;估算校验:`ceil(len(台词原文含标点)/4) ≤ 镜头时长`,超出报"台词估算朗读(4字/秒)超镜头时长"(两项都查,估算容差 0:4字/秒本就是保守值)

- [ ] **Step 4: 实现 K3**

02 色号集合→04 每个段落 code block 的 FORMAT 节必须含全部色号(逐字);02 每角色锚定短语→04 段落出场人物节提到该角色名的段落,该段 code block 内必须逐字含锚定短语(白底参考图豁免不适用 04——04 全是视频段;03 的 0a/0b/0d 块豁免:块标题含"白底"或"0a/0b/0d"则跳过风格圣经检查);风格圣经逐字全文过长时按 02"风格圣经"节首行(介质质感句)为校验单元(宁松勿滥:只查首行逐字)

- [ ] **Step 5: 跑测试通过 + CLI 冒烟(bad_duration/bad_anchor 各 exit 1)**

- [ ] **Step 6: Commit**

```bash
git add scripts/check.py tests/
git commit -m "feat: K2时长门(模型上限+朗读≤镜头+4字/秒估算) + K3锚定逐字门(色号/角色锚定短语/风格圣经首行) — TDD

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 17: K4 稳定镜号门 + K9 情节点覆盖门(TDD)

**Files:**
- Modify: `scripts/check.py`(gate_k4/gate_k9)
- Modify: `tests/test_check.py`(TestK4/TestK9)
- Create: `tests/fixtures/bad_shotid/`(01 分镜表镜号重复+03 引用不存在的镜号)、`tests/fixtures/bad_coverage/`(情节点清单某行覆盖镜号为空/状态非✓)

**Interfaces:**
- Produces: 镜号解析契约:01 分镜表首列,合法形态 `S?\d+[a-z]?`(如 1/2/S3a)与作废行 `~~S3b~~（vN 作废）`;K4 检查=镜号唯一(作废行除外)+03/04 引用的镜号(镜\d+/S\d+[a-z])都存在于 01 分镜表。K9 检查=情节点清单每行:覆盖镜号列非空+状态列含✓+引用的镜号存在

- [ ] **Step 1: 写失败测试**

```python
class TestK4(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k4(check.Project(FIXTURES / "good_project"), False), [])
    def test_duplicate_and_dangling(self):
        f = check.gate_k4(check.Project(FIXTURES / "bad_shotid"), False)
        self.assertTrue(any("镜号重复" in x.message for x in f))
        self.assertTrue(any("引用了01分镜表不存在的镜号" in x.message for x in f))

class TestK9(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k9(check.Project(FIXTURES / "good_project"), False), [])
    def test_uncovered_plot_point(self):
        f = check.gate_k9(check.Project(FIXTURES / "bad_coverage"), False)
        self.assertTrue(any(x.gate == "K9" and "情节点" in x.message and "未覆盖" in x.message for x in f))
```

- [ ] **Step 2: 跑测试确认失败**
- [ ] **Step 3: 实现 K4/K9**(按 Interfaces 契约;作废行 `~~X~~` 解析后跳过唯一性但保留存在性——03/04 不得引用作废镜号,引用则报"引用了已作废镜号")
- [ ] **Step 4: 跑测试通过+CLI 冒烟**
- [ ] **Step 5: Commit**

```bash
git add scripts/check.py tests/
git commit -m "feat: K4稳定镜号门(唯一性+03/04引用解析+作废行防引用) + K9情节点覆盖门(双向核对) — TDD

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 18: K5 强调手段配额门 + K6 运镜条件门 + K7 环境动态门(TDD)

**Files:**
- Modify: `scripts/check.py`(gate_k5/k6/k7)
- Modify: `tests/test_check.py`(TestK5/K6/K7)
- Create: `tests/fixtures/bad_peak/`(04 段内 3 处慢镜+1 处无峰值标注)、`tests/fixtures/bad_camera/`(01 情节点含"追逐"但分镜无跟拍族+某镜动机列不合 CT1)、`tests/fixtures/bad_env/`(04 某段无任何环境动态词)
- Modify: `tests/fixtures/good_project/`(01 情节点清单加一行含"追逐"+【峰】标记;分镜表加跟拍镜与 CT1 动机;01 加打斗交手账小节 R1-R2 带★;04 慢镜处带 CT2 标注——good 必须过所有新门)

**Interfaces:**
- Consumes: CT1/CT2/CT3/CT4 语法契约(全局约束节)
- Produces: 强调手段词表常量 `EMPHASIS_WORDS = ("慢动作", "慢镜", "Time Ramp", "定格", "闪白", "短促推近", "冲击重复")`;峰值来源 regex `←峰值：(情节点\d+|交手账R\d+)`;五类词 regex 按 CT1;环境动态词表 `ENV_MOTION_WORDS = ("风", "尘", "雾", "光斑", "涟漪", "火焰", "衣摆", "树叶", "微振", "机体振动", "水面", "烟", "雪", "雨", "飘", "摇")`

- [ ] **Step 1: 写失败测试**

```python
class TestK5(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k5(check.Project(FIXTURES / "good_project"), False), [])
    def test_over_quota_and_unannotated(self):
        f = check.gate_k5(check.Project(FIXTURES / "bad_peak"), False)
        self.assertTrue(any("慢镜超配额" in x.message for x in f))          # 3处>2
        self.assertTrue(any("强调手段无峰值标注" in x.message for x in f))  # 缺 ←峰值：
    def test_annotation_must_resolve(self):
        # bad_peak 中一处标注 ←峰值：交手账R9 但 01 交手账只有 R1-R2
        f = check.gate_k5(check.Project(FIXTURES / "bad_peak"), False)
        self.assertTrue(any("峰值来源无法解析" in x.message for x in f))

class TestK6(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k6(check.Project(FIXTURES / "good_project"), False), [])
    def test_chase_without_follow(self):
        f = check.gate_k6(check.Project(FIXTURES / "bad_camera"), False)
        self.assertTrue(any("追逐" in x.message and "跟拍族" in x.message for x in f))
    def test_motive_column_format(self):
        f = check.gate_k6(check.Project(FIXTURES / "bad_camera"), False)
        self.assertTrue(any("运镜动机列不合CT1" in x.message for x in f))

class TestK7(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k7(check.Project(FIXTURES / "good_project"), False), [])
    def test_segment_without_env_motion(self):
        f = check.gate_k7(check.Project(FIXTURES / "bad_env"), False)
        self.assertTrue(any(x.gate == "K7" and "环境动态" in x.message for x in f))
```

- [ ] **Step 2: 跑测试确认失败**
- [ ] **Step 3: 实现 K5**(按 04 段落分块(`## 段落` 分割);块内 EMPHASIS_WORDS 计数>2 报超配额;每处命中行查 CT2 标注,缺→报;标注来源解析:情节点N→01 情节点清单该行存在且含【峰】;交手账RN→01 交手账小节该行存在且含★)
- [ ] **Step 4: 实现 K6**(01 情节点清单全文含 奔跑|追逐|追|逃 → 分镜表运镜列须有 跟拍|横移|跟随 ≥1 处,报缺时列出情节点原文;含 揭示|发现|看见|真相|认出 → 摇|后拉|拉远|俯仰;含【峰】→ EMPHASIS_WORDS 在 04 任一处;分镜表动机列逐行 match CT1 regex,不匹配报"运镜动机列不合CT1(需 五类词(R行号)：展开)";动机为固定但无 (R7) 单独报)
- [ ] **Step 5: 实现 K7**(04 每段 code block 含 ENV_MOTION_WORDS 任一,缺→报"段落N无环境动态层元素")
- [ ] **Step 6: 跑测试通过+CLI 冒烟(三个 bad fixture 各 exit 1,good 仍 exit 0)**
- [ ] **Step 7: Commit**

```bash
git add scripts/check.py tests/
git commit -m "feat: K5强调手段配额+峰值标注解析门 / K6运镜条件触发门(CT1格式+族指认) / K7环境动态层门 — TDD

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 19: K8 骨架槽位门 + K10 PLAN/REF 门 + --partial 全链路(TDD)

**Files:**
- Modify: `scripts/check.py`(gate_k8/gate_k10;main 的 --partial 语义收口:所有门 partial=True 时依赖文件缺失即跳过)
- Modify: `tests/test_check.py`(TestK8/TestK10/TestPartial)
- Create: `tests/fixtures/bad_skeleton/`(04 骨架A块缺 FACE LOCK 节;骨架B项目但 01 无"骨架 B"理由标注)、`tests/fixtures/bad_plan/`(04 含"待补参考图"字样+REF-X9 在 03 不存在)、`tests/fixtures/partial_project/`(只有 01+02——partial 模式应跳过依赖 04/05 的门且不报错)

**Interfaces:**
- Produces: 骨架A必备节名单常量 `SKELETON_A_SECTIONS = ("SCENE CONTEXT","ACTIVE REFERENCES","CONTINUITY RULE","FORMAT","CAMERA / EDITING","ENDING FRAME","PERFORMANCE LOCK","FACE LOCK","AUDIO","LIGHTING","NO")`;K10 契约:04 内 `(PLAN|REF)-[A-Z0-9-]+` 提取;"待补参考图"字样=Finding;每个 REF-id 必须在 03 全文出现同 id;PLAN-id 唯一性

- [ ] **Step 1: 写失败测试**

```python
class TestK8(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k8(check.Project(FIXTURES / "good_project"), False), [])
    def test_missing_section(self):
        f = check.gate_k8(check.Project(FIXTURES / "bad_skeleton"), False)
        self.assertTrue(any("FACE LOCK" in x.message and "缺节" in x.message for x in f))

class TestK10(unittest.TestCase):
    def test_good(self):
        self.assertEqual(check.gate_k10(check.Project(FIXTURES / "good_project"), False), [])
    def test_pending_text_and_dangling_ref(self):
        f = check.gate_k10(check.Project(FIXTURES / "bad_plan"), False)
        self.assertTrue(any("待补参考图" in x.message for x in f))
        self.assertTrue(any("REF-X9" in x.message and "03中无法解析" in x.message for x in f))

class TestPartial(unittest.TestCase):
    def test_partial_skips_missing_docs(self):
        rc = check.main(["x", str(FIXTURES / "partial_project"), "--partial"])
        self.assertEqual(rc, 0)   # 只有01+02：K1/K2(05)/K5-K8(04)/K10 全部静默跳过
```

(good_project 需补:03 文件含 REF 登记与 04 引用的 REF-id 一致;01 骨架选择行含"骨架 A")

- [ ] **Step 2: 跑测试确认失败**
- [ ] **Step 3: 实现 K8/K10/partial 收口**(K8:04 每个骨架A code block 查 SKELETON_A_SECTIONS 全在;01 分镜表"骨架选择"注含"骨架 B"时 04 对应镜块须存在且 01 有理由文字;K10:按契约;partial:gate_fn 内 `if project.doc(x) is None: return []` 统一模式,main 不再特殊处理)
- [ ] **Step 4: 跑全部测试通过**

Run: `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -v` → 全 PASS(累计 ~20 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/check.py tests/
git commit -m "feat: K8骨架槽位门 + K10 PLAN/REF闭环门 + --partial全链路(依赖缺失静默跳过) — TDD

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 20: check.py 真实项目试跑(Review Focus #1 误拦观察)

**Files:**
- Modify: `scripts/check.py`(仅当试跑暴露误拦:放宽对应门,每处放宽在代码注释记录理由)
- Create: `tests/baseline-checkpy-record.md`(试跑记录:项目/门/误拦数/处置——学 vigen tests/baseline-record.md 惯例)

**Interfaces:**
- Consumes: 全部 K1-K10
- Produces: 误拦率结论——写入 Task 22 的 learning-guide 更新

- [ ] **Step 1: 在真实项目跑 --partial**

Run(逐个): `PYTHONDONTWRITEBYTECODE=1 python -B scripts/check.py "C:\Users\ottol\myProjects\aigc\myAiSeries\firepunch_ep1" --partial` 及 `inkos-short-drama\works\蛮荒神使`、`works\最后一单`(目录内文件名与 01-06 契约不同属正常——**这类"非 vigen 契约项目"应 exit 2 并给清晰提示"未按 01-06 契约组织,跳过",不算误拦**;只有按契约组织的项目内的错报才算)

- [ ] **Step 2: 分类处置**

每条 finding 分类:真违规(项目确实漂了,保留)/误拦(格式变体,放宽+注释理由+补 fixture 防回归)/解析失败(修 parser+补 fixture)。**放宽的门槛:同一误拦模式出现 ≥2 次才放宽;单次怪例修 fixture 不改门**(宁松勿滥但不无限松)

- [ ] **Step 3: 记录+跑全测试回归**

试跑结论写入 `tests/baseline-checkpy-record.md`;`python -B -m unittest discover -s tests` 全 PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/check.py tests/
git commit -m "test: check.py 真实项目试跑记录 + 误拦处置(放宽处均附fixture防回归)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

## Step 5 · 停点收缩(spec §4 第五节)

### Task 21: SKILL.md 停点纪律改写 + E2 PLAN 挂图 + 新硬规则 15(check.py 强制)

**Files:**
- Modify: `SKILL.md`(停点纪律节、段落制节、汇报纪律句、硬规则表加 15、意图路由/画布节核对)
- Modify: `assets/templates.md`(04 模板参考素材行加 PLAN/REF 槽位说明,CT5)
- Modify: `references/prompt-rules.md`(参考图绑定处加 PLAN 挂图流程一句+定稿回读衔接)

**Interfaces:**
- Consumes: Task 15-20 的 check.py(CLI 契约 CT6)
- Produces: 硬规则 15 文本(每写完 01/03/04/05 之一跑 --partial,不过不进下一阶段)——Task 22 README 同步引用

- [ ] **Step 1: SKILL.md 停点纪律节改写**

按 spec 第五节停点表逐行落地:保留(GATE0/GATE1.5/GATE1/图片第一段验收/内容安全台词报用户);降级两处——段落制"每段验收再下一段"改为"check.py --partial 通过→自动续跑下一段;批次(全部段落)完成后统一汇报";"改前先复述一句等确认"改为"agent 自复述并写入 01 变更记录;仅当命中口语歧义清单且上下文无法消歧时才问用户";删除"高风险运镜双方案"停点行(Task 6/8 已撤销该机制,核对无残留);节首加原则句:"**只有真实创作分叉才询问用户;不要拿格式、目录、事务或检查器询问创作者**——机械问题由 check.py 拦,创作分叉才停 [drama-skills: short-drama/SKILL.md#执行请求]"

- [ ] **Step 2: 新硬规则 15**

硬规则表(14 条→15 条)加:

```
| 15 | **check.py 门**：每写完 01/03/04/05 之一必须 `python scripts/check.py <项目目录> --partial`；五份齐备后跑全量；**不过不进下一阶段**；不为通过检查补造文件；误拦时报告用户裁决，不绕过 | SKILL.md 本节 + scripts/check.py 头部注释 |
```

同步改表头"14 条"→"15 条"、README 提及处(Task 22)。

- [ ] **Step 3: E2 PLAN 挂图落地**

SKILL.md 停点纪律节加 E2 段(按 spec 第五节 E2 全文:PLAN 占位照常产出/批次汇报附挂图清单/绑定 REF 触发定稿回读/画风验收门不动);templates.md 04 参考素材行加槽位说明:"缺图写 `PLAN-<ID>` 占位照常产出(不停下等图);图生成后绑定为 `REF-<ID>` 并触发情景图定稿回读——K10 校验闭环,禁止'待补参考图'式模糊字样 [drama-skills: short-drama/SKILL.md#L52-55]";prompt-rules.md 参考图绑定处加同义一句+指针

- [ ] **Step 4: 汇报纪律句升级**

"汇报纪律(摘要的固定形状)"处:量化结果后插入"**check.py 结果(全过/哪条没过怎么修的)**+挂图清单(PLAN 项)";三条反虚报不变

- [ ] **Step 5: 验证**

Run: `grep -n "硬规则（15 条" SKILL.md`(表头已改)
Run: `grep -rn "PLAN-" SKILL.md assets/templates.md references/prompt-rules.md`(三处就位)
Run: `grep -n "只有真实创作分叉才询问" SKILL.md`(原则句就位)
Walkthrough:模拟"用户口述一段新剧情(段落制)"全流程——数出停点:应只有 批次汇报 1 处(段内 check.py 通过自动续跑);对比旧流程(每段验收)确认收缩

- [ ] **Step 6: Commit**

```bash
git add SKILL.md assets/templates.md references/prompt-rules.md
git commit -m "feat: 停点收缩——真分叉才停/段落制自动续跑/复述降为自证 + E2 PLAN挂图不阻塞 + 硬规则15 check.py门

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

## Step 6 · 文档收尾(spec §4 第六步)

### Task 22: README/create.md/learning-guide/knowledge-index 同步 + 单一事实源终检

**Files:**
- Modify: `README.md`(目录结构注释、工作流图停点标注、硬规则数、模型栈节核对、已知边界节:补"check.py 只读校验不调 API")
- Modify: `create.md`(迭代记录加 V3.0 节:来源=drama-skills 三组对比研究+用户四痛点+R1-R3 裁定,内容=本计划六步概要)
- Modify: `references/learning-guide.md`(缺陷 4 现状更新:"机制级规则已补(议程卡/升级六问/操作程序自检),仍待实测验证";缺陷清单新增两条:①措辞即决策框架(选择层禁安全品牌词,失败兜底除外)②规则不咬人的根因是缺可判定选择机制——补内容前先看选择层;新增缺陷:check.py 误拦率待观察(引 tests/baseline-checkpy-record.md);吸收台账加一行 drama-skills(类型/质量:方法论+实测·高;吸收去向:V3.0 全部;未吸收:四级分级/节奏档案/Dashboard/交接胶囊/compact_refs 及原因);版本对照表加 V3.0 行;Troubleshooting 表加新机制行(慢镜滥用→峰值标注/运镜单调→决策表行号/打斗泛写→交手账/台词幼稚→议程卡+行动动词))
- Modify: `references/knowledge-index.md`(核对新节路由:action-combat 第 0 节、cinematography 决策表/峰值节、prompt-rules 0.7/A12——扩展文件触发条件不变则只核对不改)

**Interfaces:**
- Consumes: Task 1-21 全部产出(节名/规则名必须与实际落地一致——逐个 grep 核对,不凭计划文本)
- Produces: V3.0 完整文档闭环

- [ ] **Step 1: README 同步**

按实际落地内容更新(目录结构树加 scripts/check.py 与新节名;工作流图停点标注收缩后的停点;"14 条硬规则"→15;已知边界补 check.py 说明;**README 只导航不重述规则**——遵守其自身纪律)

- [ ] **Step 2: 单一事实源终检(Review Focus #3)**

逐条核对:SKILL.md 规则归属表/Module Map 中的节名与文件实际节名一致(grep 每个新节名);跨文件指针有效性——`grep -rn "峰值与强调手段\|交手账\|功能决策表\|可生成性\|A12" SKILL.md references/ assets/` 逐行确认全文只在一处、其余皆指针;`grep -rn "双方案" SKILL.md references/ assets/ | grep -v _archive` 零命中

- [ ] **Step 3: create.md V3.0 迭代记录**(格式沿用 V2.9 条目:日期/驱动来源/批次内容/拒绝入库项——拒绝项:四级分级/节奏档案/Dashboard/交接胶囊/compact_refs/戏型诊断五问/Coverage Audition 及原因)

- [ ] **Step 4: learning-guide 四处更新**(缺陷 4/新缺陷两条+check.py 观察项/台账行/版本行/Troubleshooting 行——按 Files 所列)

- [ ] **Step 5: knowledge-index 核对**(新扩展文件=无,本轮全部落位既有文件;确认索引表无需加行;若 Task 11-14 在 screenwriting-craft 新增节影响"何时读"描述则同步一句)

- [ ] **Step 6: 全库回归**

Run: `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -v` → 全 PASS
Run: `grep -rn "最稳\|双方案" SKILL.md references/ assets/ | grep -v _archive` → 零命中
Run: `wc -l references/screenwriting-craft.md references/cinematography.md references/action-combat.md references/prompt-rules.md SKILL.md` → 各 <800

- [ ] **Step 7: Commit**

```bash
git add README.md create.md references/learning-guide.md references/knowledge-index.md
git commit -m "docs: V3.0 文档闭环——README/create迭代记录/learning-guide(缺陷4更新+措辞教训+台账+Troubleshooting)/knowledge-index核对 + 单一事实源终检

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

## 完成后

- 分支 `feat/v3-craft-upgrade` 上共 22 个 commit(含 spec 4 个);用户逐任务验收
- 全部通过后按 superpowers:finishing-a-development-branch 决定合并方式
- vigen 版本升 V3.0(create.md+README 已记);用户重装:`cp SKILL.md ~/.claude/skills/vigen/ && cp -r references assets scripts ~/.claude/skills/vigen/`(**scripts 目录新增,README 安装命令 Task 22 Step 1 已同步**)
- 首个真实项目试跑后,按 learning-guide 流程回填实测反馈(缺陷清单只增不删)
