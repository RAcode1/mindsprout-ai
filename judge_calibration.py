"""
judge_calibration.py

PURPOSE (future work - not implemented yet)
--------------------------------------------

This file will measure how well the AI judge (evaluate_story in
mindsprout_core.py) agrees with human judgment.

This is a DIFFERENT question than the one regression.py answers:

- regression.py asks: "Does the STORY GENERATOR still produce stories
  that meet our quality bar?" It generates a NEW story every run, so
  the story text itself is never the same twice.

- judge_calibration.py will ask: "Does the AI JUDGE score a FIXED,
  already-reviewed story the way a human would?" To answer that
  fairly, the judge must evaluate the exact same story text a human
  already looked at - not a freshly generated one.

HOW THIS SHOULD WORK ONCE BUILT
--------------------------------

1. Load a small set of FIXED stories: each one generated once,
   reviewed by a human, and saved verbatim together with the human's
   per-criterion scores (e.g. in a future "calibration_cases.json").
2. Re-run evaluate_story() against each fixed story (not generate_story
   - the story must not change between runs).
3. Compare the AI's scores to the saved human scores per criterion,
   using calibration metrics such as exact-match rate and mean
   absolute difference.
4. Report where the judge over-scores or under-scores relative to a
   human, so the judge's prompt/rubric can be tuned.

WHY THIS FILE IS EMPTY FOR NOW
--------------------------------

No fixed stories or trustworthy human ratings tied to a specific story
exist yet. golden_cases.json is currently used only as generation test
input (age/concept/theme) by regression.py, not as frozen stories with
labels. Inventing fixed stories or scores here would produce fake
calibration data, so this file is intentionally left as a skeleton
until real fixed-story + human-score pairs are captured.
"""

# TODO: define/load a dataset of {story, human_scores} pairs where the
#       story is fixed text, not something generated at run time.
# TODO: for each pair, call evaluate_story() on the fixed story only.
# TODO: compare ai scores vs human scores per criterion.
# TODO: report exact-match rate and mean absolute difference.
# TODO: save a calibration report, separate from regression results.


def run_judge_calibration():
    """Placeholder entry point. Not implemented yet."""
    raise NotImplementedError(
        "judge_calibration.py is a skeleton. It needs a dataset of "
        "fixed stories with trustworthy human scores before this can "
        "be implemented."
    )


if __name__ == "__main__":
    run_judge_calibration()
