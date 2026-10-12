"""
rag_eval.py

Measures retrieval on its own, with no API calls: for each scenario
case, does keyword search pick a guide listed in the case's
expected_guides? Also shows what adversarial inputs retrieve and which
requests get no guide at all.

Usage:
    python rag_eval.py
"""

from rag import MIN_SCORE, rank_guides
from regression_common import load_golden_cases

scenarios = load_golden_cases(case_type="scenario")
adversarial = load_golden_cases(case_type="adversarial")

top1 = top3 = 0
misses = []
for case in scenarios:
    ranked = rank_guides(case["concept"], case["theme"])
    picked = [g.id for g, score in ranked[:3]]
    best_guide, best_score = ranked[0]
    chosen = best_guide.id if best_score >= MIN_SCORE else None
    expected = case["expected_guides"]
    if chosen in expected:
        top1 += 1
    else:
        misses.append((case["id"], case["name"], chosen, round(best_score, 2), expected))
    if any(g in expected for g in picked):
        top3 += 1

n = len(scenarios)
print(f"Scenario cases: {n}")
print(f"  right guide chosen (top 1):  {top1}/{n} = {top1 / n:.0%}")
print(f"  right guide in top 3:        {top3}/{n} = {top3 / n:.0%}")
if misses:
    print("\n  Misses (case, chosen, score, expected):")
    for cid, name, chosen, score, expected in misses:
        print(f"    {cid} {name!r}: {chosen} ({score}) expected {expected}")

print("\nAdversarial inputs (what retrieval hands the generator):")
for case in adversarial:
    guide, score = rank_guides(case["concept"], case["theme"])[0]
    chosen = guide.id if score >= MIN_SCORE else "no guide"
    print(f"  {case['id']} {case['name']!r}: {chosen} ({score:.2f})")
