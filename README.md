# MindSprout AI

MindSprout AI turns an important life lesson into a short, age-appropriate
story for a child, using Claude.

You give it a child's age, the concept/lesson you want taught, and a story
theme. It finds the best-matching parenting guide (retrieval), generates a
6-page story with a title and a core lesson that follows that guide, and
(on request) grades its own output against a quality rubric using a
second, separate Claude model as a judge.

## Current MVP features

- **Streamlit web app** (`app.py`) — enter age, theme, and a lesson, click
  **Generate My Story**, and read the result as a one-page-at-a-time
  digital book (`ui.py`), ending in a standalone Core Lesson screen.
- **Story generation only on demand** — clicking **Generate My Story** calls
  only the story generator (Claude Sonnet 5). It does **not** automatically
  run the AI quality evaluator, to keep API cost predictable.
- **Automatic structural QA** — cheap, local, non-AI checks (exactly 6
  pages, title present, core lesson present, no empty pages) run
  automatically after every generation, at no API cost.
- **Optional AI quality check** — inside the collapsed **"Developer /
  Quality Check"** section, a separate **"Run AI Quality Check"** button
  calls a second, more capable Claude model (Opus 5) as a judge, scoring
  the story on six criteria (concept fidelity, age appropriateness, story
  quality, show-don't-lecture, coherence, emotional safety). This only
  runs when you click that button.
- **Usage & cost visibility** — the same Developer / Quality Check section
  shows estimated input/output token counts and API cost for the last
  generation and (if run) evaluation call. This is developer-facing only
  and never shown to normal users.
- **Session caching** — the generated story and any evaluation result are
  cached for the session, so browsing the UI (e.g. opening the
  Developer section) never silently re-triggers an API call.
- **CLI app** (`mindsprout.py`) — the original interactive command-line
  version of the same flow, unchanged.
- **Golden test set** (`golden_cases.json`) — 70 human-reviewed test
  cases:
  - **50 scenarios** across four age bands (2–4, 5–7, 8–12, 13–18), each
    with a `watch_for` note describing the specific failure a reviewer
    would look for (e.g. turning "boredom is okay" into "boredom leads to
    creativity").
  - **20 adversarial cases** — prompt injection, age-inappropriate
    requests, harmful "lessons" (e.g. keeping secrets from parents),
    misinformation, hateful themes, and unusual input (gibberish, a
    5,000-character lesson, Spanish, age 1). Each has its own `pass_rule`,
    because for these inputs *following* the lesson is the failure.
- **Regression suite** — generates a story for every case and scores it:
  structural checks, then a separate Claude Opus 5 judge (the quality
  rubric for scenarios, the case's pass rule for adversarial cases).
  - `regression_batch.py` — full runs through the Batch API at half
    price; supports `--ids`, `--type`, `--repeats` (consistency),
    `--generator` (model comparison) and `--resume`.
  - `regression_smoke.py` — the quick CI gate (8 key cases).
  - `regression.py` — one case at a time at normal price, for quick
    checks (`python regression.py ADV007`).
  - Both share the same pass/fail rules (`regression_common.py`).
- **Judge calibration** (`judge_calibration.py`) — a documented skeleton
  for a future tool that checks whether the AI judge agrees with human
  scoring on a *fixed* story. Not implemented yet.

## Baseline results (October 2026)

First full run of all 70 golden cases through the Batch API (about $1.78):

| | Passed |
| --- | --- |
| All cases | 55 / 70 (79%) |
| Scenarios | 36 / 50 (72%) |
| Adversarial / safety | 19 / 20 (95%) |

What the run found:

- **Malformed output** in 3 of 70 runs: an empty extra page, or a story
  that stopped after one sentence with no core lesson.
- **Lesson drift** — stories that swap the requested lesson for a related
  one, exactly the failures the `watch_for` notes describe.
- **Lecturing instead of showing**, and pages too long or confusing for
  ages 2–4.
- **One safety miss** — a request for romance content for a 6-year-old
  produced a kiss scene instead of being redirected.
- **Low variety** — two character names (Mia, Maya) appear in most
  stories. The judge doesn't score this; it surfaced from analysing the
  outputs.

## After prompt and validation fixes (October 12, 2026)

Fixes: general prompt rules (show rather than explain, keep the lesson as
asked with no added reward, short pages for ages 4 and under, varied
names, safety before every other rule) plus output validation (drop empty
pages, regenerate once if a story is still incomplete).

| | Baseline | After fixes |
| --- | --- | --- |
| All cases | 55 / 70 (79%) | 59 / 70 (84%) |
| Scenarios | 36 / 50 (72%) | 39 / 50 (78%) |
| Adversarial / safety | 19 / 20 (95%) | 20 / 20 (100%) |
| Malformed outputs | 3 | 0 |

10 cases moved from fail to pass, 6 moved from pass to fail, and 5 failed
both times. The run also exposed a test-harness bug: the judge's
3,000-token output limit cut off the grading of one long story, so the
limit is now 8,000.

**Consistency.** Running 10 cases 3 times each showed 3 of the 10 changing
result between runs, so single-run changes on individual cases are partly
noise. Two lesson-drift cases (TC001, TC003) failed every run: a real
defect and the next fix. Safety cases passed every run.

**Character names.** Banning overused names only moved the repetition:
Mia and Maya went from 43 of 70 stories to 0, but Pip (17) and Priya (15)
took their place, and the top two names' share fell only from 61% to 46%.
Name variety needs names chosen in code, not a prompt rule.

## Model comparison (October 12, 2026)

Same fixed prompts, same Claude Opus 5 judge, generator swapped:

| Generator | All cases | Safety cases | Story cost per 1,000 (Batch API) |
| --- | --- | --- | --- |
| Claude Sonnet 5 | 59 / 70 (84%) | 20 / 20 | $4.42 |
| Claude Haiku 4.5 | 50 / 70 (71%) | 19 / 20 | $1.89 |

Haiku writes stories 57% cheaper but passes 13 points fewer cases and
missed a child-safety case (fear used as discipline in a bedtime story
for a 3-year-old), so the app stays on Sonnet.

## Retrieval (RAG) (October 12, 2026)

`rag.py` keeps 23 short parenting guides (`guides/`) and picks the best
match for each lesson with BM25 keyword search: no embeddings service and
no extra API cost. The chosen guide is added to the generator's prompt.
The guides were written from general parenting advice, not from the test
cases' `watch_for` notes, so retrieval can't hand the generator the
test's answers. They are general guidance, not professional advice.

**Retrieval on its own** (`python rag_eval.py`, no API calls): the right
guide for 48 of 50 scenario cases (96%), and in the top 3 for all 50.
Gibberish and non-English input get no guide. One bug found on the way:
the app's default theme word "Anything" matched guide text, so even
gibberish was getting a guide.

**Full run, all 70 cases:**

| | Without retrieval | With retrieval |
| --- | --- | --- |
| All cases | 59 / 70 (84%) | 61 / 70 (87%) |
| Scenarios | 39 / 50 (78%) | 42 / 50 (84%) |
| Adversarial / safety | 20 / 20 | 19 / 20 |

A separate faithfulness check compared each story with its guide: 68 of
68 stories stayed faithful (no contradictions).

**Regression caught.** A request for a violent war story for a 5-year-old
retrieved the grief guide (it matched words like "dying"), and the story
became one about a pet dying, a heavy topic the parent never asked for.
Fix: a prompt rule to use a guide only when it fits the lesson, and to
leave its topic out otherwise.

**The first fix didn't hold.** Re-running all 20 safety cases with that
rule, the same case still failed: the request itself mentions dying, so
the model judged the grief guide a fit and chose grief as its "safe"
topic. The other 19 safety cases passed, and all 18 guided stories stayed
faithful to their guides.

**Second fix:** for children under 8, unsafe requests now redirect to a
light, everyday lesson (courage, kindness, solving disagreements) rather
than death or loss, unless the parent is asking for help with a real loss.
The grief guide also says not to bring loss into stories that didn't ask
for it. The failing case and three related safety cases now pass, and the
real grief scenario (a pet that died) still passes. A full 20-case re-run
with the final prompt is the next check.

## Regression gate (CI)

`regression_smoke.py` runs 8 key cases in a few minutes (about $0.60) and
fails if any safety case fails or more than one scenario fails. One miss
is allowed because the consistency run showed scenario results can flip
between runs. `.github/workflows/prompt-regression.yml` runs it whenever
the prompts, judge, retrieval, or test cases change. Until the
`ANTHROPIC_API_KEY` repository secret is added, the check is skipped.

## Running it locally

1. Create/activate the virtual environment and install dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Create a `.env` file in the project root (never commit this file):
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```
3. Run the app:
   ```
   streamlit run app.py
   ```
   This opens the app at `http://localhost:8501`.

Other entry points:
- `python mindsprout.py` — interactive CLI version.
- `python regression_batch.py` — run the full regression suite through
  the Batch API (half price; results usually arrive within minutes).
- `python rag_eval.py` — measure retrieval accuracy (no API calls).
- `python regression.py TC001` — run a single test case at normal price
  (see `golden_cases.json` for valid IDs). Each run is saved as a
  timestamped file under `results/`.

## Environment variables and secrets

The app needs one secret: `ANTHROPIC_API_KEY`.

- **Locally**: put it in a `.env` file (see above). `mindsprout_core.py`
  loads it via `python-dotenv`. `.env` is listed in `.gitignore` and must
  never be committed.
- **On Streamlit Community Cloud**: there is no `.env` file in the
  deployed environment. Instead, set the key in the app's **Settings →
  Secrets** panel in the Streamlit Cloud dashboard, using:
  ```toml
  ANTHROPIC_API_KEY = "your-api-key-here"
  ```
  `app.py` reads this via `st.secrets` and copies it into the environment
  before the backend is imported, so the rest of the code needs no
  changes between local and deployed environments. See
  `.streamlit/secrets.toml.example` for the exact format (that file is a
  placeholder template only — it is not a real secret and is safe to
  commit).

**API keys must never be committed to git**, in any file, under any
name. If you ever need to rotate a key that was accidentally exposed,
revoke it from the Anthropic console immediately.

## Project structure

```
app.py                       Streamlit frontend (entry point for the web app)
ui.py                        Pure UI rendering helpers (CSS, header, page/lesson cards) used by app.py
mindsprout.py                Original interactive CLI app
mindsprout_core.py           Shared backend: story generation, AI evaluation, structural checks
rag.py                       Retrieval: picks the best-matching parenting guide (BM25)
guides/                      23 parenting guides used for retrieval
rag_eval.py                  Retrieval accuracy check (no API calls)
regression_batch.py          Full regression runs through the Batch API (half price)
regression.py                One-case-at-a-time regression runs (normal price)
regression_common.py         Pass/fail rules and summary shared by the runners
regression_smoke.py          Quick regression gate run by CI (8 key cases)
.github/workflows/           CI workflow that runs the regression gate
judge_calibration.py         Skeleton for future judge-vs-human calibration work
golden_cases.json            70 golden test cases (50 scenarios + 20 adversarial), with expected guides
requirements.txt             Python dependencies
.streamlit/secrets.toml.example   Template showing the Streamlit Cloud secrets format
.gitignore                   Excludes .env, .venv/, __pycache__/, results/, and secrets
results/                     Timestamped regression run output (not committed)
```

## Deployment

This app is intended to be deployed on **Streamlit Community Cloud**,
pointing at `app.py` as the entry point, with `ANTHROPIC_API_KEY` set as
an app secret (see above). No other configuration is required.
