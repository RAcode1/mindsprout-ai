import json
import sys
from datetime import datetime
from pathlib import Path

from mindsprout_core import evaluate_safety, evaluate_story
from regression_common import (
    QUALITY_THRESHOLDS,
    generate_for_test,
    load_golden_cases,
    print_summary,
    score_adversarial,
    score_scenario,
)


# ==========================================
# ONE-CASE-AT-A-TIME REGRESSION RUN
# ==========================================
#
# Runs cases one after another at normal API prices. Handy for checking a
# single case quickly:
#
#     python regression.py ADV007
#
# For full runs use regression_batch.py, which sends every case through
# the Batch API at half price. Both runners share the same pass/fail
# rules (regression_common.py), so their results are comparable.


# ==========================================
# LOAD TEST CASES
# ==========================================

requested_case = None

# Optional: run just one test case
if len(sys.argv) > 1:
    requested_case = sys.argv[1].upper()
    golden_cases = load_golden_cases(ids=[requested_case])

    if not golden_cases:
        print(f"Test case {requested_case} was not found.")
        sys.exit()
else:
    golden_cases = load_golden_cases()


all_results = []


# ==========================================
# RUN EVERY TEST CASE
# ==========================================

for case in golden_cases:

    print("\n" + "=" * 70)
    print(f"{case['id']} - {case['name']} ({case['type']})")
    print("=" * 70)

    age = case["age"]
    concept = case["concept"]
    theme = case["theme"]

    result_row = {
        "run_id": case["id"],
        "id": case["id"],
        "name": case["name"],
        "type": case["type"],
        "age": age,
    }

    print("\nGenerating story...")

    try:
        story, _ = generate_for_test(case)

        if story is None:
            print("Generator declined to write a story.")

        print("Evaluating...")

        if case["type"] == "adversarial":
            verdict = evaluate_safety(age, concept, theme, story, case["pass_rule"])
            passed, failure_reasons, structural_checks = score_adversarial(story, verdict)
            result_row["safety_verdict"] = verdict.model_dump()
            ai_scores = None
        else:
            evaluation = None
            if story is not None:
                evaluation = evaluate_story(
                    age, concept, theme, story, watch_for=case.get("watch_for")
                )
            passed, failure_reasons, ai_scores, structural_checks = score_scenario(
                story, evaluation
            )

    except Exception as error:
        # A failed API call (or any other error) should not crash the
        # whole suite - record this case as ERROR and keep going.
        print(f"\n{case['id']} ERROR - {error}")
        result_row.update({"result": "ERROR", "error": str(error)})
        all_results.append(result_row)
        continue

    # ==========================================
    # PRINT THIS CASE'S RESULTS
    # ==========================================

    if structural_checks:
        print("\nStructural QA:")
        for check_name, check_passed in structural_checks.items():
            print(f"  {check_name}: {'PASS' if check_passed else 'FAIL'}")

    if ai_scores:
        print("\nAI Quality Scores vs Thresholds:")
        for criterion, required_score in QUALITY_THRESHOLDS.items():
            actual_score = ai_scores[criterion]
            status = "PASS" if actual_score >= required_score else "FAIL"
            print(f"  {criterion}: {actual_score} (>= {required_score} required) {status}")

    if case["type"] == "adversarial":
        print(f"\nSafety verdict: {'PASS' if verdict.passed else 'FAIL'} - {verdict.reason}")

    if passed:
        print(f"\n{case['id']} PASS")
    else:
        print(f"\n{case['id']} FAIL - {'; '.join(failure_reasons)}")

    result_row.update({
        "concept": concept,
        "theme": theme,
        "result": "PASS" if passed else "FAIL",
        "failure_reasons": failure_reasons,
        "story": story.model_dump() if story is not None else None,
        "structural_checks": structural_checks,
        "ai_scores": ai_scores,
        "quality_thresholds": QUALITY_THRESHOLDS if ai_scores else None,
    })
    all_results.append(result_row)


# ==========================================
# OVERALL REGRESSION SUMMARY
# ==========================================

print_summary(all_results, "MINDSPROUT GENERATION REGRESSION SUMMARY")


# ==========================================
# SAVE REGRESSION REPORT (TIMESTAMPED)
# ==========================================
#
# A timestamped filename (instead of a fixed name) means running a
# single case never overwrites a previous full-suite report, and every
# run is kept for later comparison.

results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

if requested_case:
    report_filename = f"regression_{requested_case}_{timestamp}.json"
else:
    report_filename = f"regression_all_{timestamp}.json"

report_path = results_dir / report_filename

with open(report_path, "w", encoding="utf-8") as file:
    json.dump(all_results, file, indent=2, ensure_ascii=False)

print(f"\nFull results saved to {report_path}")
