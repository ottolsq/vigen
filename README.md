# vigen — AI Video Production Assistant Skill

**English** | [简体中文](README.zh-CN.md)

Turn one idea or one script into a complete, copy-paste-ready video production plan. Built for people with no film background: shot design, camera movement, transitions, lighting, and prompt engineering are filled in automatically. You answer an intake questionnaire and make decisions at three gates (GATE0 / GATE1.5 / GATE1).

> This README is an introduction and navigation guide, not the rulebook. The authoritative rules live in the reference files (listed below).

## What it solves

The hard part of AI video is not "having tools"; it is "knowing how to direct them". This skill addresses:

| Pain point | Where the fix lives |
| --- | --- |
| Images look AI-greasy, flat, or stiff | "Describe how this photo was shot" + four composition-tension methods → [realism.md](references/realism.md) |
| Color drifts across segments | Film-wide palette (3-5 hex colors assigned by area; color + placement in every prompt) → [styles.md](references/styles.md) |
| Prompts are vague; the model does not understand | Three-layer semantic binding + positive guidance over negative constraints (model-specific) → [prompt-rules.md](references/prompt-rules.md) / [knowledge-index.md](references/knowledge-index.md) |
| Complex actions will not generate | Lock anti-prior poses with a first-frame image; the video prompt only writes subsequent motion → [prompt-rules.md](references/prompt-rules.md) |
| Characters/scenes/props drift across images | Four-layer anchoring, six hard reference-image standards, head/body separation, cross-referencing, one authoritative reference per object, three-tier costume locking, fact inheritance → [consistency.md](references/consistency.md) |
| Prop state confusion (carried / not carried) | Six prop rules, multi-state sheet → crop singles, split combination props, per-shot position ledger → [prompt-rules.md](references/prompt-rules.md) / [consistency.md](references/consistency.md) |
| Reference images fight each other | Keep one authoritative image per object; downgrade or crop the rest → [consistency.md](references/consistency.md) |
| A complex scene will not fit in one clip | Split into skeleton-B single-shot clips and join in editing → [prompt-rules.md](references/prompt-rules.md) |
| Actions violate physics | Three-stage action + ENDING FRAME + second-level timing → [prompt-rules.md](references/prompt-rules.md) |
| Voice timbre drifts across clips | Model-specific voice route (native voice / H3 timbre extraction / cosyvoice) + vocal description formula → [consistency.md](references/consistency.md) |
| One clip contains only one shot | Skeleton A multi-shot segment formula is the default → [prompt-rules.md](references/prompt-rules.md) |
| Repetitive camera moves, dull transitions | R1-R7 camera-function table + 40 moves + 8 generation-side / 5 editing-side transitions + peak-emphasis methods → [cinematography.md](references/cinematography.md) |
| Long series forgets details | `00_story_state.md` updated every episode + tail-frame handoff → [consistency.md](references/consistency.md) |
| Plot gets silently changed | Plot-point checklist with 100% coverage validation → [screenwriting-craft.md](references/screenwriting-craft.md) |
| Paid short drama: episode count, paywall placement | Project brief (tier / episodes / track / emotion contract / unit chain / paywall) + first-three-episode beat cards → [short-drama-market.md](references/short-drama-market.md) |
| Vertical-drama dialogue is hard to follow or slow | Form B coverage rules (same-round answer / 15-second four beats / episode settlement / monologue quota) → [screenwriting-craft.md](references/screenwriting-craft.md) §1.9 |
| Script hits content red lines | Filing category + 11 red lines + sensitive-word replacement → [content-compliance.md](references/content-compliance.md) |
| Wasting money on unnecessary assets | Asset reference matrix first; zero-reference assets are not generated; one-shot props get no reference image → [prompt-rules.md](references/prompt-rules.md) §1.4 |
| Generation fails; no idea how to recover | Structure-first fallback ladder → [SKILL.md](SKILL.md) |
| Prompts get blocked by moderation | Reactive downgrade: reuse registered patterns, then wording → composition → split solo → binary search → [content-safety.md](references/content-safety.md) |
| Negative words do not work, or make it worse | Check for conflict with positive intent first → [knowledge-index.md](references/knowledge-index.md) |
| Skill VFX / magic circles / sword aura / particles | Niagara three-layer lighting + mage / archer / swordsman forms + motion trails → [vfx-effects.md](references/vfx-effects.md) |
| Add or change shots mid-project | Living-script revision (local reflow, stable shot IDs) → [SKILL.md](SKILL.md) |
| Characters teleport / swap / disappear between segments | Segment blocking ledger + 04 blocking score + continuity iron rules → [consistency.md](references/consistency.md) |
| Cuts feel harsh; actions do not connect | Action bridge at every cut (previous shot's ending → this shot's opening) → [templates.md](assets/templates.md) 04 |
| Crowd extras change every shot; colors clash | Group anchor table + group reference sheet (costume only; avoid protagonist colors) → [templates.md](assets/templates.md) 02/03 |
| Negative words: where do they go? | Two-part negative block (global + per-segment continuity, when the model supports a negative field) → [templates-execution.md](assets/templates-execution.md) §7 |
| Image prompts get longer and the image gets deader | Two-tier image constraint budget (technical sheet full / narrative concise-intent) → [prompt-rules.md](references/prompt-rules.md) 0.12 |
| Every segment needs a first-frame image (costly) | Seedance projects skip L1 scene images; H3/happyhorse still require them → [prompt-rules.md](references/prompt-rules.md) §1.3 |
| Structure is right but density is low; shots read like an outline | Per-shot blocking + background action line + lens mm + four-group negative library + light-evolution line → [templates.md](assets/templates.md) 04 |

## Workflow

```
GATE0 intake + alignment
  → Phase 1a script writing ─GATE1.5 script lock─→ Phase 1b shot design + anchoring ─GATE1 confirm─
  → Phases 2-4 image prompts (asset matrix first) → Phase 5 video prompts + dialogue table
  → Phase 6 edit list → (series: update 00_story_state)
```

Three stops: **GATE0** (questionnaire + requirement alignment), **GATE1.5** (script lock — never move to shot design before this), **GATE1** (anchoring confirmation). The lock covers the story skeleton and plot-point checklist; the shot table remains a living document (later additions follow the living-script revision path).

**Execution contract (V3.16)**: before writing 03/04/05 in each batch, re-read 02/01/05; fill a "batch production card" per segment; append a "batch validation record" (A1-A16 + evidence) to 01; optional `--gate A17` mechanical audit and `--gate A18` image-budget audit. No record means you may not say "done".

**Project layout**: single video `<project>/01-06`; series `<series>/00_story_state.md + ep01/…ep02/…`.

Files produced per project (Markdown is the creative source of truth):

| File | Contents |
| --- | --- |
| `00_story_state.md` | Series only: project brief (vertical drama) + plot summary / character state / prop state / previous tail frame / foreshadowing — updated after every episode |
| `01_plan_and_script.md` | GATE0 alignment record + project brief (single video) + short-drama episode structure (settlement / mid-episode hook / cliffhanger) + GATE1.5 lock record + scene script + plot-point checklist + shot overview table (living document, stable shot IDs) + batch production cards + batch validation records + change log |
| `02_anchoring.md` | Target models / color palette / characters / scenes (LOCATION MAP + four views) / props / style bible |
| `03_image_prompts.md` | Asset reference matrix + character / prop / scene / scene-image references (L1-L4 grading) + content-safety wording (high-risk projects) |
| `04_video_prompts.md` | Skeleton A multi-shot segment formula by default / skeleton B single-shot (exception); duration hard checks + tail-frame handoff |
| `05_voice_dialogue.md` | Dialogue ledger + vocal description formula (identity preamble + six parameters) + voice-reference assets + SPEAKER LOCK |
| `06_edit_list.md` | Assembly / transition implementation / transition audio / BGM / grading / export |

## Model capabilities and prompt strategy (2026-11)

| Model | Generation mode | Segment-start scene image (L1) | Video/audio reference | Current state |
| --- | --- | --- | --- | --- |
| **Seedance / Jimeng (Seedance models)** | Reference-to-video (multimodal) | **Not required by default** | Yes (video / voice) | Highest text adherence in current tests; a 3-minute case study used 8 segments with zero scene images |
| **MiniMax-H3** | t2va / first frame / first+last frame / Ref2VA | **Required**, including **environment-changing cut points** | Yes (images ≤9, video ≤3, audio ≤3, total ≤12) | Visual quality drops noticeably without scene images; use multi-frame alignment or split segments |
| **happyhorse-1.1** | t2v / i2v / r2v (images only) | **Required** | No | No multi-frame alignment; split cross-environment cuts |

### Seedance: scene images are optional

Tested: Seedance reference-to-video plus a detailed video prompt and character / scene / prop reference images is enough. Segment-start scene images can be skipped. The 3-minute case study *Chang'an, Bright as Day* used 8 video segments with zero generated scene images; its "first frame" was a frame extracted from the previous segment's tail, not a newly generated image. Important: **L2 pose-lock images for anti-prior or contact actions are still required** — text cannot reliably lock a pose, regardless of how well the model follows prompts.

### H3: scene images are part of image quality

For H3, one first-frame image at the start of a segment is not enough. When a cut inside the segment changes the environment, lighting, or spatial layout, the absence of a matching scene image makes visual quality drop sharply. The procedure:

1. Always generate the segment-start L1 image.
2. For an **environment-changing cut point**, generate a cut-point frame and pin it to the second with the H3 multi-frame alignment recipe (`Picture k` at `t` seconds).
3. If the provider does not support multi-frame alignment, **split the cross-environment cut into its own generation segment** (one environment per segment), making that shot the new segment's L1.
4. Cuts within the same environment and axis (coverage / shot-reverse-shot) do not need an extra image. happyhorse has no multi-frame alignment; split cross-environment cuts the same way.

### Making H3 approach Seedance through prompt optimization

H3 and Seedance differ in reference-to-video capability and text adherence. **They can be brought closer; they cannot be made identical.** Eight practices close most of the gap:

1. **Write the opening state in full.** Without a first frame, the segment-opening shot must specify camera position, shot size, composition, lighting, subject position, and lens mm in the 04 body — Seedance can start a frame from text; H3 needs the text to describe what the first frame looks like.
2. **Upgrade the blocking ledger to per-shot routes + background action lines.** H3 segments contain more cuts; discontinuous character positions and background action amplify the "new cast every shot" feeling.
3. **Write an action bridge at every cut.** At least one of action / eyeline / sound must carry over from the previous shot's last beat to this shot's first beat.
4. **Add a light-evolution line.** Opening light → mid-segment change → closing light, preventing color/light jumps across cuts.
5. **Generate cut-point scene images for environment changes.** Pin them to the second when multi-frame alignment is available; otherwise split the segment.
6. **Use the four-group negative library.** Image quality/material, background motion/camera, continuity, music/subtitles. When the model has a dedicated negative field, write it as two parts: global list + per-segment continuity list.
7. **Write density into every shot.** Lens mm, camera-move ID, three-stage action / second-level timing, sound evolution. The case study's "thickness" comes from complete per-shot information, not from stacked adjectives.
8. **Do not compress the prompt structure.** H3's gap is not solved by deleting words; blocking, lighting, and continuity details all have to stay.

> Bottom line: an optimized H3 can get visibly close to Seedance's finish, but it does not become the same model. The goal is to narrow the gap, not to claim equivalence.

## Directory layout (the single source of truth for rules)

```
├── SKILL.md              # GATE0 questionnaire + workflow + intent routing + 23 hard rules + K1-K17 checks + A16-A18 opt-in audits + execution contract + fallback ladder
├── references/
│   ├── screenwriting-craft.md # Script craft: seven-hole self-check + dialogue-as-action + scene engine + payoff + seven opposition forms + four misunderstanding tests + hook discipline + three-layer story + GATE1.5 + Form B vertical drama
│   ├── short-drama-market.md # Platform short-drama planning: tiers / episode counts / 40 tracks / genre / emotion contract / unit chain / paywall / first-three-episode beat cards (vertical drama only)
│   ├── content-compliance.md # Filing category + 11 red lines + violence/superstition specifics + sensitive-word replacement (vertical drama only)
│   ├── prompt-rules.md   # Four foundational models + 0.7 generability gate + 0.8 technical-action anchors + 0.9 orientation + 0.10 direction/target anchors + 0.12 image constraint budget + scale kit + mixing language + image/video skeletons A·B + six prop rules + L1-L4 grading + vocal formula + checks (A1-A16 + 13 spot checks + K17 + A17/A18 opt-in)
│   ├── models.md         # Model capability profiles + generation-path decision + model-switch guide
│   ├── cinematography.md # R1-R7 camera-function table + five motivation categories + 40 moves + 8 generation-side / 5 editing-side transitions + shot semantics + dialogue coverage + working shot sizes + lighting library + peak emphasis + shot duration/rhythm + vertical safe zones + 7 scene sequence types
│   ├── realism.md        # De-AI look + four tension methods + surface tiers + anatomy constraints + period discipline + physicalized text
│   ├── styles.md         # 16 style library (incl. Pixar 3D) + color palette + style extraction + project isolation
│   ├── consistency.md    # Nine-item lock list + costume locking + persistent scene elements + body-prop spatial ledger + segment blocking / group anchoring + bad-reference handling + four-layer anchoring + reference-image standards + character routing / baseline-reference method + minimal reference set + voice extraction + series memory + failure propagation
│   ├── content-safety.md # Reactive moderation downgrade: wording solutions + composition patterns + ladder + explicit negation + failure classification
│   ├── knowledge-index.md# Extension-knowledge router (read on hit) + negative-word adjudication
│   ├── examples.md       # Complete example
│   ├── action-combat.md  # [extension] Combat engine: exchange ledger + impact presentation + siege orientation + three-beat container + contact rules
│   ├── vfx-effects.md    # [extension] Skill VFX: Niagara three-layer lighting + mage/archer/swordsman forms + motion trails + failure-mode negative list
│   ├── cinema-grade-params.md # [extension] Cinema parameter block + anime four-view sheets
│   ├── expressions.md / director-styles.md / extended-views.md / emotion-craft.md / ugc-realism.md / anime-to-real.md  # [extensions]
│   ├── learning-guide.md # Learning guide (defect list / usage boundaries / source ledger) — not in the daily execution path
│   ├── execution-pitfalls.md # Execution-side pitfalls (not in Module Map/runtime)
│   └── _archive-suspended-claims.md  # Archived suspended claims (do not read/use)
├── assets/
│   ├── templates.md      # Standard templates for project files 00-06 (01 includes impact scope / on-screen props / lens column; 02 includes costume tiers / persistent scene state / body-prop ledger / four-group negative library; 03 includes direction anchors / target-state images / vertical safe zones; 04 includes PLAN/REF + PLAN-TAIL / attachment order / per-shot routes / background action lines / lens / light evolution; 06 includes shot duration / editing transitions / rhythm / key sound mixing)
│   ├── templates-character.md  # Character reference templates (0a combined sheet default / split fallback / 0c / multi-face strip / 0d)
│   └── templates-execution.md  # Execution-contract templates (batch card / segment state ledger / A1-A16 validation record / nine-item segment lock / no-dialogue segment / one-page segment template with blocking score (per-shot routes / background action lines) / light evolution / action bridges / two-part negative block)
├── scripts/
│   ├── check.py          # Thin validation layer (K1-K17 mechanical gates, standard library only; A16/A17/A18 opt-in)
│   ├── check.mjs         # Node CLI + gate registry (K1-K17 default; A16/A17/A18 optional, behavior-aligned with check.py)
│   ├── check-core.mjs    # Shared helpers for check.mjs
│   ├── check-gates-a.mjs # K1-K6 gates
│   ├── check-gates-b.mjs # K7-K12 gates
│   ├── check-gates-c.mjs # K13-K14 gates
│   ├── check-gates-d.mjs # K15-K16 gates
│   ├── check-gates-e.mjs # A16/A17/A18 optional audits
│   ├── check-gates-f.mjs # K17 prompt hygiene
│   ├── vigen_md.py       # Python parsing layer
│   ├── vigen-md.mjs      # Node parsing layer (aligned with vigen_md.py)
│   └── export.py         # Delivery packaging (snapshot + manifest + checksums; does not assert approval)
└── tests/
    ├── test_check.py       # check.py unit tests (122 tests; includes test_export)
    ├── check-mjs.test.mjs  # check.mjs K1-K17 + A16/A17/A18 parity (132 tests)
    ├── baseline-record.md  # TDD record
    ├── baseline-checkpy-record.md  # Real-project false-positive observations
    └── fixtures/           # good/bad sample projects
```

## Current model stack (2026-11)

- Image: gpt-image-2 / gpt-image-2.5 (text-to-image, single-reference, multi-reference; 2.5 supports up to 32,000 prompt characters, 1-16 edit inputs, mask/markup)
- Video: happyhorse-1.1 (3-15s) / MiniMax-H3 (4-15s) / Seedance·Jimeng (reference-to-video)
- Voice: native video-model voice by default; cosyvoice TTS alignment when strict timbre consistency is required
- Editing: CapCut / Jianying

> models.md records supported capabilities only (mode / duration / resolution / reference-asset limits). "Model quirks" claims from research are archived as suspended; rules validated by user testing are retained with their evidence.

## Install

```bash
# Claude Code personal skill directory (copy runtime files only)
cd vigen
mkdir -p ~/.claude/skills/vigen
cp SKILL.md ~/.claude/skills/vigen/
cp -r references assets scripts ~/.claude/skills/vigen/
```

> **Script path**: after installation, check.py lives at `~/.claude/skills/vigen/scripts/check.py`. Your project directory has no `scripts/`; always call the skill's absolute path (or resolve the skill root first). Do not write `python scripts/check.py`.
> Validate: `python ~/.claude/skills/vigen/scripts/check.py <project> --partial`
> Deliver: `python ~/.claude/skills/vigen/scripts/export.py <project> --out <outside-project-dir>` (snapshot + manifest + checksums; does not assert approval)

No manual invocation is needed after installation — intents such as "make me a short video / shot list / video prompts / multi-episode drama / Wong Kar-wai-style short" trigger it automatically; you can also call `/vigen` explicitly.

## Development documents

- [create.md](create.md) — requirements, design, and iteration log
- [research-notes.md](research-notes.md) — historical research notes (conclusions handled as suspended claims; archive only)
- [references/execution-pitfalls.md](references/execution-pitfalls.md) — execution-side pitfalls

## Continuous learning

**Seedance 2.5 prompt patterns are the current quality benchmark**, improved through [learning-guide.md](references/learning-guide.md):

- **Four-step learning**: study → distill → summarize → accumulate — split new material into executable rules / templates / examples; no vague summaries
- **Credibility tiers**: `[official docs]` > `[user-tested]` > `[finished sample]` > `[community methodology]`; unsourced claims do not enter the library
- **Single source of truth**: each rule is written in full in exactly one file; other places carry only "key point + pointer" — duplication is a defect (enforced since V2.8)
- **Defect list only grows**: fixed defects move to the archive with evidence

## Known boundaries

- Produces prompts and project files only; does not call generation APIs or perform editing. check.py / check.mjs only read project Markdown; they do not call APIs or modify files
- `check.mjs` is at **full K1-K17 parity** with check.py (same output / exit code); full parity is covered by `tests/check-mjs.test.mjs`. check.py remains the authoritative implementation; gate changes must be mirrored on both sides
- **A16 (lock-before-write)** is an opt-in audit: style-bible verbatim / on-screen REF registration / persistent presence. Technical actions and three-element orientation remain human-reviewed
- **A17 (execution-contract evidence)** is an opt-in audit: batch cards / A1-A16 validation records / segment state ledger / reference contracts / time ledger / style-lock verbatim / nine-item segment lock / character-prop-group inline binding / blocking score + per-shot routes + background action lines / action bridges / negative-block closure / lens per shot / light-evolution line. It does not judge content quality
- **A18 (image constraint budget)** is an opt-in audit: flags 03 image prompts over 260 CJK characters or more than 10 constraint words; technical sheets and text-layout images are exempt. Reduce prompts per prompt-rules 0.12 after a warning; never delete load-bearing anchors just to pass A18
- **K17 (prompt hygiene)** is a default gate: 04/03 positive bodies must not contain music words; no-dialogue segments must declare "no dialogue / no narration / no voices"; sound sections need the positive closing line "no second sound, no continuous ambience". Explicitly marked negative-prompt sections are skipped
- **04 split volumes (V3.17)**: large projects may split into `04_video_prompts_volNN.md`; `04_video_prompts.md` is only an index, and check.py/check.mjs merge volumes by filename order
- **Test status**: Python 122 tests; Node 132 tests (including A17/A18 parity across all fixtures)
- Platform commercial layers (tracks / episode counts / paywalls) are **planning references**, not official platform rules; this skill does not predict virality or guarantee approval
- No real-actor filming guidance; scripts must be locked by the user at GATE1.5 (self-checks assist, they do not replace the user)
- Content safety is **reactive**: unregistered patterns are not pre-emptively softened; after a block, downgrade by wording/composition and register the solution. Approval by every platform is not guaranteed
- Model capabilities are registered per "model × provider"; the same model behind different gateways may differ. Verify against the current provider before generating

## License

This project is released under the **MIT License** — see [LICENSE](LICENSE).
