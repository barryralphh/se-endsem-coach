# SE end-sem coach: 5 short animated Hinglish videos (one per unit)

Subject: **Software Engineering (CD CSC 5 02)**, B.Tech sem IV. Exam style: end-sem 40 marks, 5 questions, attempt any 2 of 3 in each, 4 marks each. Mid-sem 15 marks, 1.5 marks each.

Goal: 5 videos (Unit 1 to 5), each easy enough for a layman, with a **diagram + flowchart for every topic**, **numericals never skipped**, and an **answer template** so any topic can be written as a full 4-page answer.

Theme (mascot already in engine = angry red bird, Gussa Guru): **Angry Birds x Pokemon x Ben 10**. Analogies only, shapes drawn with Pillow, no copyrighted art.
- SDLC = building and attacking the pig castle (plan, design, launch, check damage, repair)
- Evolutionary model = Pokemon evolution; V-model = Pokemon type matching (each build step has a matching test)
- Spiral = Ben 10 Omnitrix: every spin you pick an alien after checking risk
- Agile = Ash adapting every battle; Traditional = Prof Oak's fixed plan

## STATUS (update this table every time you push; another AI continues from here)

| Unit | Topic | Lesson file | Video |
|---|---|---|---|
| 4 | Testing (white/black box, cyclomatic complexity, BVA, TDD) | `lessons/L04_testing.py` | TODO (build first) |
| 5 | Cost, metrics, risk, quality, CMM (FP, COCOMO, LOC, failure %) | `lessons/L05_*.py` | TODO (build second) |
| 1 | Intro, crisis, SDLC, Structured vs OOAD, Agile vs Traditional | `lessons/L01_*.py` | TODO |
| 2 | Requirements, SRS, use case, ER, DFD, state diagram | `lessons/L02_*.py` | TODO |
| 3 | Coupling/cohesion, architecture, process models | `lessons/L03_*.py` | TODO |

Order requested by owner: **Unit 4 and 5 first**, then 1, 2, 3. Last commit before this repo existed: `cn-endsem-coach` (engine reused, see docs/ENGINE.md).

## Files
- `docs/MASTER_FLOWCHART.md` overview flowchart of every topic, down to minute points (also the first scene of every video)
- `docs/CONTENT_PLAN.md` scene by scene plan for all 5 videos with worked numericals already computed
- `docs/PYQ_MAP.md` every past-paper question mapped to the unit and the scene that answers it
- `docs/ENGINE.md` how videos are made (Pillow frames + edge-tts Hinglish + ffmpeg), the lesson file format, how to add scene types, how to run GitHub Actions
- `render.py`, `lessons/`, `.github/workflows/build.yml` (added as the work lands)

## How a video is made (short)
1. One lesson file per unit in `lessons/Lnn_name.py` defines `L = dict(title, points, scenes)`.
2. `python render.py build 04` makes frames (Pillow), Hinglish voice (edge-tts en-IN-PrabhatNeural, espeak fallback), joins with ffmpeg to `out/04.mp4` plus `out/04.md` (written notes).
3. GitHub Actions matrix: **20 workers = 5 videos x 4 parts** (each worker renders a quarter of the scenes), then a merge job joins the 4 parts and commits `videos/NN.mp4`.
4. Trigger: Actions tab > build-videos > Run workflow, or the GitHub API workflow_dispatch.

## Rules for writing lessons (keep these)
- Hinglish in Roman script, simple, with one analogy per topic.
- Every topic scene has a diagram on the left (shapes or flow) and the written answer skeleton or working on the right.
- Software crisis and similar common-sense topics: 1 table of keywords (cost, time, quality, change...) and move on.
- Hard-to-remember things (agile vs traditional, models, coupling, cohesion): use a mnemonic or trick.
- Never skip numericals: show every step on the right panel (`## title`, `? question`, `! answer`, `~ note`).
