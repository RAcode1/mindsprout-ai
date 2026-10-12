"""
regression_batch.py

Full regression run through the Anthropic Batch API, at half the normal
API price. Results usually arrive within minutes (at most 24 hours).

Two batches run one after the other:
  1. generate a story for every test case (Claude Sonnet 5)
  2. judge every story (Claude Opus 5) - the quality rubric for scenario
     cases, the case's own pass rule for adversarial cases

Pass/fail rules are shared with regression.py (regression_common.py).

Usage:
    python regression_batch.py                          # all cases, 1 run each
    python regression_batch.py --ids TC001 ADV007       # selected cases
    python regression_batch.py --type adversarial       # one case type
    python regression_batch.py --ids TC001 --repeats 3  # consistency check
    python regression_batch.py --resume results/batch_state_<time>.json
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from anthropic.types.messages.batch_create_params import Request

from mindsprout_core import (
    EvaluationReport,
    GENERATOR_MODEL,
    JUDGE_MODEL,
    MindSproutStory,
    SafetyVerdict,
    build_judge_request,
    build_safety_judge_request,
    client,
    estimate_cost,
    json_output_format,
)
from regression_common import (
    generation_request_for_test,
    load_golden_cases,
    parse_structured,
    print_summary,
    score_adversarial,
    score_scenario,
)

BATCH_DISCOUNT = 0.5  # Batch API usage is billed at 50% of normal prices
POLL_SECONDS = 30

RESULTS_DIR = Path("results")


# ==========================================
# BATCH HELPERS
# ==========================================

def wait_for_batch(batch_id, label):
    """Poll until the batch has ended, printing progress."""

    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        print(
            f"  [{datetime.now():%H:%M:%S}] {label}: {batch.processing_status} "
            f"(processing {counts.processing}, succeeded {counts.succeeded}, "
            f"errored {counts.errored})",
            flush=True,
        )
        if batch.processing_status == "ended":
            return
        time.sleep(POLL_SECONDS)


def collect_results(batch_id):
    """Map custom_id -> succeeded Message, or an error string."""

    collected = {}
    for item in client.messages.batches.results(batch_id):
        if item.result.type == "succeeded":
            collected[item.custom_id] = item.result.message
        elif item.result.type == "errored":
            error = item.result.error
            detail = getattr(getattr(error, "error", None), "message", None) or str(error)
            collected[item.custom_id] = f"batch request errored: {detail}"
        else:
            collected[item.custom_id] = f"batch request {item.result.type}"
    return collected


def batch_cost(model, usage):
    cost = estimate_cost(model, usage)
    return None if cost is None else cost * BATCH_DISCOUNT


def save_state(state, path):
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ==========================================
# ARGUMENTS / STATE
# ==========================================

parser = argparse.ArgumentParser(description="Run the MindSprout regression suite through the Batch API.")
parser.add_argument("--ids", nargs="+", help="only run these case ids")
parser.add_argument("--type", choices=["scenario", "adversarial"], help="only run this case type")
parser.add_argument("--repeats", type=int, default=1, help="runs per case (to measure consistency)")
parser.add_argument("--resume", help="continue a run from its batch_state file")
args = parser.parse_args()

RESULTS_DIR.mkdir(exist_ok=True)

if args.resume:
    state_path = Path(args.resume)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    print(f"Resuming run {state['started']}")
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    state_path = RESULTS_DIR / f"batch_state_{timestamp}.json"
    selected = load_golden_cases(ids=args.ids, case_type=args.type)
    if not selected:
        raise SystemExit("No test cases matched.")
    state = {
        "started": timestamp,
        "case_ids": [case["id"] for case in selected],
        "repeats": args.repeats,
        "generation_batch_id": None,
        "judge_batch_id": None,
    }

cases = {case["id"]: case for case in load_golden_cases(ids=state["case_ids"])}

# One "run" per case per repeat, e.g. TC001__r1, TC001__r2
runs = {
    f"{case_id}__r{n}": cases[case_id]
    for case_id in state["case_ids"]
    for n in range(1, state["repeats"] + 1)
}

print(f"{len(cases)} cases x {state['repeats']} run(s) = {len(runs)} runs")


# ==========================================
# STEP 1: GENERATE STORIES
# ==========================================

if not state["generation_batch_id"]:
    batch = client.messages.batches.create(
        requests=[
            Request(custom_id=run_id, params=generation_request_for_test(case))
            for run_id, case in runs.items()
        ]
    )
    state["generation_batch_id"] = batch.id
    save_state(state, state_path)
    print(f"\nSubmitted generation batch {batch.id} (state saved to {state_path})")

print("\nWaiting for story generation...")
wait_for_batch(state["generation_batch_id"], "generation")
generation_results = collect_results(state["generation_batch_id"])

stories = {}            # run_id -> MindSproutStory or None (declined)
generation_usage = {}   # run_id -> usage
errors = {}             # run_id -> error message

for run_id in runs:
    result = generation_results.get(run_id, "missing from batch results")
    if isinstance(result, str):
        errors[run_id] = result
        continue
    generation_usage[run_id] = result.usage
    try:
        stories[run_id] = parse_structured(result, MindSproutStory)
    except Exception as error:
        errors[run_id] = f"could not read story (stop_reason {result.stop_reason}): {error}"


# ==========================================
# STEP 2: JUDGE STORIES
# ==========================================
#
# Scenario cases: quality rubric (with the case's watch_for note).
# Adversarial cases: the case's own pass rule - including when the
# generator declined, since declining can be the correct outcome.
# A scenario the generator declined fails without needing a judge call.

def judge_request_for(run_id, case):
    story = stories[run_id]
    if case["type"] == "adversarial":
        request = build_safety_judge_request(
            case["age"], case["concept"], case["theme"], story, case["pass_rule"]
        )
        request["output_config"] = {"format": json_output_format(SafetyVerdict)}
    else:
        request = build_judge_request(
            case["age"], case["concept"], case["theme"], story, watch_for=case.get("watch_for")
        )
        request.setdefault("output_config", {})["format"] = json_output_format(EvaluationReport)
    return request


to_judge = {
    run_id: case
    for run_id, case in runs.items()
    if run_id in stories and (stories[run_id] is not None or case["type"] == "adversarial")
}

if to_judge and not state["judge_batch_id"]:
    batch = client.messages.batches.create(
        requests=[
            Request(custom_id=run_id, params=judge_request_for(run_id, case))
            for run_id, case in to_judge.items()
        ]
    )
    state["judge_batch_id"] = batch.id
    save_state(state, state_path)
    print(f"\nSubmitted judge batch {batch.id}")

judge_results = {}
if state["judge_batch_id"]:
    print("\nWaiting for judging...")
    wait_for_batch(state["judge_batch_id"], "judging")
    judge_results = collect_results(state["judge_batch_id"])


# ==========================================
# STEP 3: PASS / FAIL AND COST
# ==========================================

all_results = []
total_cost = 0.0

for run_id, case in runs.items():
    row = {
        "run_id": run_id,
        "id": case["id"],
        "name": case["name"],
        "type": case["type"],
        "category": case.get("category"),
        "age": case["age"],
    }

    if run_id in generation_usage:
        cost = batch_cost(GENERATOR_MODEL, generation_usage[run_id])
        total_cost += cost or 0
        row["generation_cost_usd"] = cost

    if run_id in errors:
        row.update({"result": "ERROR", "error": errors[run_id]})
        all_results.append(row)
        continue

    story = stories[run_id]
    row["story"] = story.model_dump() if story is not None else None

    try:
        if run_id in to_judge:
            judged = judge_results.get(run_id, "missing from batch results")
            if isinstance(judged, str):
                raise RuntimeError(judged)
            cost = batch_cost(JUDGE_MODEL, judged.usage)
            total_cost += cost or 0
            row["judge_cost_usd"] = cost

        if case["type"] == "adversarial":
            verdict = parse_structured(judged, SafetyVerdict)
            if verdict is None:
                raise RuntimeError("safety judge declined to judge")
            passed, reasons, structural = score_adversarial(story, verdict)
            row["safety_verdict"] = verdict.model_dump()
        else:
            evaluation = None
            if story is not None:
                evaluation = parse_structured(judged, EvaluationReport)
                if evaluation is None:
                    raise RuntimeError("quality judge declined to judge")
                row["evaluation"] = evaluation.model_dump()
            passed, reasons, scores, structural = score_scenario(story, evaluation)
            row["ai_scores"] = scores

    except Exception as error:
        row.update({"result": "ERROR", "error": str(error)})
        all_results.append(row)
        continue

    row.update({
        "result": "PASS" if passed else "FAIL",
        "failure_reasons": reasons,
        "structural_checks": structural,
    })
    all_results.append(row)


print_summary(all_results, "MINDSPROUT BATCH REGRESSION SUMMARY")
print(f"\nEstimated cost of this run (batch pricing): ${total_cost:.2f}")

report_path = RESULTS_DIR / f"batch_regression_{state['started']}.json"
report_path.write_text(
    json.dumps(
        {"state": state, "estimated_cost_usd": total_cost, "results": all_results},
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)
print(f"Full results saved to {report_path}")
