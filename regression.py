import json
import sys
from datetime import datetime
from pathlib import Path

from mindsprout_core import (
    generate_story,
    evaluate_story,
    check_story_structure,
)


# ==========================================
# GENERATION QUALITY THRESHOLDS
# ==========================================
#
# These define what "passing" means for the STORY GENERATOR. They are
# our own fixed quality bar, not a comparison to any human score.
#
# golden_cases.json is used here purely as a set of GENERATION TEST
# SCENARIOS (age / concept / theme inputs) to exercise the generator.
# The "human_scores" field in that file is intentionally NOT used by
# this script: a fresh story is generated on every run, so comparing
# its AI score to a human score recorded for a *different*, previously
# generated story would be misleading. That kind of comparison belongs
# in judge_calibration.py, once fixed stories with trustworthy human
# labels exist.

QUALITY_THRESHOLDS = {
    "concept_fidelity": 4,
    "age_appropriateness": 4,
    "story_quality": 3,
    "show_dont_lecture": 3,
    "coherence": 4,
    "emotional_safety": 5,
}


# ==========================================
# LOAD GENERATION TEST SCENARIOS
# ==========================================

with open("golden_cases.json", "r", encoding="utf-8") as file:
    golden_cases = json.load(file)

requested_case = None

# Optional: run just one test case
if len(sys.argv) > 1:
    requested_case = sys.argv[1].upper()

    golden_cases = [
        case
        for case in golden_cases
        if case["id"].upper() == requested_case
    ]

    if not golden_cases:
        print(f"Test case {requested_case} was not found.")
        sys.exit()


all_results = []

tests_passed = 0
tests_failed = 0
tests_errored = 0


# ==========================================
# RUN EVERY GENERATION TEST SCENARIO
# ==========================================

for case in golden_cases:

    print("\n" + "=" * 70)
    print(f"{case['id']} - {case['name']}")
    print("=" * 70)

    age = case["age"]
    concept = case["concept"]
    theme = case["theme"]

    print("\nGenerating story...")

    try:
        story = generate_story(age, concept, theme)

        structural_checks = check_story_structure(story)

        print("Evaluating story...")

        evaluation = evaluate_story(age, concept, theme, story)

    except Exception as error:
        # A failed API call (or any other error) should not crash the
        # whole suite - record this case as ERROR and keep going.
        print(f"\n{case['id']} ERROR - {error}")

        tests_errored += 1

        all_results.append({
            "id": case["id"],
            "name": case["name"],
            "result": "ERROR",
            "error": str(error),
        })

        continue

    # ==========================================
    # STRUCTURAL QA RESULTS
    # ==========================================

    print("\nStructural QA:")

    failed_structural_checks = []

    for check_name, passed in structural_checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {check_name}: {status}")

        if not passed:
            failed_structural_checks.append(check_name)

    # ==========================================
    # AI QUALITY SCORES VS THRESHOLDS
    # ==========================================

    ai_scores = {
        "concept_fidelity": evaluation.concept_fidelity.score,
        "age_appropriateness": evaluation.age_appropriateness.score,
        "story_quality": evaluation.story_quality.score,
        "show_dont_lecture": evaluation.show_dont_lecture.score,
        "coherence": evaluation.coherence.score,
        "emotional_safety": evaluation.emotional_safety.score,
    }

    print("\nAI Quality Scores vs Thresholds:")

    failed_thresholds = []

    for criterion, required_score in QUALITY_THRESHOLDS.items():
        actual_score = ai_scores[criterion]
        passed = actual_score >= required_score
        status = "PASS" if passed else "FAIL"

        print(
            f"  {criterion}: {actual_score} "
            f"(>= {required_score} required) {status}"
        )

        if not passed:
            failed_thresholds.append(
                f"{criterion} {actual_score} < required {required_score}"
            )

    # ==========================================
    # PASS / FAIL DECISION
    # ==========================================
    #
    # A case passes only if every structural check passed AND every
    # required AI quality threshold was met.

    failure_reasons = [
        f"structural check '{check_name}' failed"
        for check_name in failed_structural_checks
    ]

    failure_reasons.extend(failed_thresholds)

    case_passed = len(failure_reasons) == 0

    if case_passed:
        tests_passed += 1
        print(f"\n{case['id']} PASS")
    else:
        tests_failed += 1
        print(f"\n{case['id']} FAIL - {'; '.join(failure_reasons)}")

    all_results.append({
        "id": case["id"],
        "name": case["name"],
        "age": age,
        "concept": concept,
        "theme": theme,
        "result": "PASS" if case_passed else "FAIL",
        "failure_reasons": failure_reasons,
        "story": story.model_dump(),
        "structural_checks": structural_checks,
        "ai_scores": ai_scores,
        "quality_thresholds": QUALITY_THRESHOLDS,
    })


# ==========================================
# OVERALL REGRESSION SUMMARY
# ==========================================

print("\n\n" + "=" * 70)
print("MINDSPROUT GENERATION REGRESSION SUMMARY")
print("=" * 70)

total_run = tests_passed + tests_failed + tests_errored

print(f"\nTests passed: {tests_passed}")
print(f"Tests failed: {tests_failed}")
print(f"Tests errored: {tests_errored}")

if total_run > 0:
    pass_percentage = tests_passed / total_run * 100
    print(f"Pass percentage: {pass_percentage:.1f}%")


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
