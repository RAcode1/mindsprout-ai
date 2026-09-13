from mindsprout_core import (
    generate_story,
    evaluate_story,
    check_story_structure,
)


# ==========================================
# GET USER INPUT
# ==========================================

age = input("Child's age: ")
concept = input("Concept or lesson to teach: ")
theme = input("Story theme: ")


# ==========================================
# GENERATE STORY
# ==========================================

story = generate_story(age, concept, theme)


# ==========================================
# DISPLAY STORY
# ==========================================

print("\n--- MindSprout Story ---\n")
print("Title:", story.title)

for page in story.pages:
    print(f"\nPage {page.page_number}")
    print(page.story_text)

print("\nCore lesson:")
print(story.core_lesson)


# ==========================================
# DETERMINISTIC QA
# ==========================================

checks = check_story_structure(story)

print("\n--- Structural QA ---")

for check_name, passed in checks.items():
    status = "PASS" if passed else "FAIL"
    print(f"{check_name}: {status}")


# ==========================================
# AI QUALITY EVALUATION
# ==========================================

evaluation = evaluate_story(
    age,
    concept,
    theme,
    story
)


print("\n========== MINDSPROUT AI QUALITY REPORT ==========\n")


def print_score(name, result):
    print(f"{name}: {result.score}/5")
    print(f"Reason: {result.reason}\n")


print_score(
    "Concept fidelity",
    evaluation.concept_fidelity
)

print_score(
    "Age appropriateness",
    evaluation.age_appropriateness
)

print_score(
    "Story quality",
    evaluation.story_quality
)

print_score(
    "Show, don't lecture",
    evaluation.show_dont_lecture
)

print_score(
    "Coherence",
    evaluation.coherence
)

print_score(
    "Emotional safety",
    evaluation.emotional_safety
)


scores = [
    evaluation.concept_fidelity.score,
    evaluation.age_appropriateness.score,
    evaluation.story_quality.score,
    evaluation.show_dont_lecture.score,
    evaluation.coherence.score,
    evaluation.emotional_safety.score,
]

average_score = sum(scores) / len(scores)

print(f"Overall average: {average_score:.1f}/5")

print("\nEvaluator summary:")
print(evaluation.overall_summary)