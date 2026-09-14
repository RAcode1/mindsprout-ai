# MindSprout AI

MindSprout AI turns an important life lesson into a short, age-appropriate
story for a child, using Claude.

You give it a child's age, the concept/lesson you want taught, and a story
theme. It generates a 6-page story with a title and a core lesson, and
(on request) grades its own output against a quality rubric using a
second, separate Claude model as a judge.

## Current MVP features

- **Streamlit web app** (`app.py`) — enter age, theme, and a lesson, click
  **Generate Story**, and read the result as a set of page cards with the
  core lesson highlighted at the end.
- **Story generation only on demand** — clicking **Generate Story** calls
  only the story generator (Claude Sonnet). It does **not** automatically
  run the AI quality evaluator, to keep API cost predictable.
- **Automatic structural QA** — cheap, local, non-AI checks (exactly 6
  pages, title present, core lesson present, no empty pages) run
  automatically after every generation, at no API cost.
- **Optional AI quality check** — inside the collapsed **"Developer /
  Quality Check"** section, a separate **"Run AI Quality Check"** button
  calls a second Claude model (Opus) as a judge, scoring the story on
  six criteria (concept fidelity, age appropriateness, story quality,
  show-don't-lecture, coherence, emotional safety). This only runs when
  you click that button.
- **Session caching** — the generated story and any evaluation result are
  cached for the session, so browsing the UI (e.g. opening the
  Developer section) never silently re-triggers an API call.
- **CLI app** (`mindsprout.py`) — the original interactive command-line
  version of the same flow, unchanged.
- **Generation regression suite** (`regression.py`) — replays a fixed set
  of test scenarios (`golden_cases.json`) through the generator and
  checks the output against fixed quality thresholds. See inline
  comments in that file for what it does and does not verify.
- **Judge calibration** (`judge_calibration.py`) — a documented skeleton
  for a future tool that checks whether the AI judge agrees with human
  scoring on a *fixed* story. Not implemented yet.

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
- `python regression.py` — run the full generation regression suite.
- `python regression.py TC001` — run a single test case (see
  `golden_cases.json` for valid IDs). Each run is saved as a timestamped
  file under `results/`.

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
mindsprout.py                Original interactive CLI app
mindsprout_core.py           Shared backend: story generation, AI evaluation, structural checks
regression.py                Generation regression suite (fixed quality thresholds)
judge_calibration.py         Skeleton for future judge-vs-human calibration work
golden_cases.json            Fixed generation test scenarios used by regression.py
requirements.txt             Python dependencies
.streamlit/secrets.toml.example   Template showing the Streamlit Cloud secrets format
.gitignore                   Excludes .env, .venv/, __pycache__/, results/, and secrets
results/                     Timestamped regression run output (not committed)
```

## Deployment

This app is intended to be deployed on **Streamlit Community Cloud**,
pointing at `app.py` as the entry point, with `ANTHROPIC_API_KEY` set as
an app secret (see above). No other configuration is required.
