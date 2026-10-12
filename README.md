# MindSprout AI

MindSprout AI turns an important life lesson into a short, age-appropriate
story for a child, using Claude.

You give it a child's age, the concept/lesson you want taught, and a story
theme. It generates a 6-page story with a title and a core lesson, and
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
    price; supports `--ids`, `--type`, `--repeats` (consistency) and
    `--resume`.
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

Next: prompt and validation fixes, then a re-run against this baseline.

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
regression_batch.py          Full regression runs through the Batch API (half price)
regression.py                One-case-at-a-time regression runs (normal price)
regression_common.py         Pass/fail rules and summary shared by both runners
judge_calibration.py         Skeleton for future judge-vs-human calibration work
golden_cases.json            70 golden test cases (50 scenarios + 20 adversarial)
requirements.txt             Python dependencies
.streamlit/secrets.toml.example   Template showing the Streamlit Cloud secrets format
.gitignore                   Excludes .env, .venv/, __pycache__/, results/, and secrets
results/                     Timestamped regression run output (not committed)
```

## Deployment

This app is intended to be deployed on **Streamlit Community Cloud**,
pointing at `app.py` as the entry point, with `ANTHROPIC_API_KEY` set as
an app secret (see above). No other configuration is required.
