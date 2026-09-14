from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

client = Anthropic()


# ==========================================
# DATA STRUCTURES
# ==========================================

class StoryPage(BaseModel):
    page_number: int
    story_text: str


class MindSproutStory(BaseModel):
    title: str
    pages: list[StoryPage]
    core_lesson: str


class QualityScore(BaseModel):
    score: int = Field(ge=1, le=5)
    reason: str


class EvaluationReport(BaseModel):
    concept_fidelity: QualityScore
    age_appropriateness: QualityScore
    story_quality: QualityScore
    show_dont_lecture: QualityScore
    coherence: QualityScore
    emotional_safety: QualityScore
    overall_summary: str


# ==========================================
# USAGE / COST TRACKING (DISPLAY ONLY)
# ==========================================
#
# Pricing is per 1M tokens, keyed to the exact model strings used
# below. This estimate is for display in the app's Developer / Quality
# Check panel only - it never changes what is sent to the API and has
# no effect on actual billing. Update these numbers if Anthropic's
# published pricing for these models changes.

MODEL_PRICING = {
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    "claude-opus-5": {"input": 5.00, "output": 25.00},
}


def estimate_cost(model, usage):
    """Estimate USD cost from a response's usage metadata.

    Returns None if the model has no known pricing or usage is
    unavailable, so callers can display "unknown" instead of a wrong
    number.
    """

    if usage is None:
        return None

    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        return None

    input_cost = usage.input_tokens / 1_000_000 * pricing["input"]
    output_cost = usage.output_tokens / 1_000_000 * pricing["output"]

    return input_cost + output_cost


# ==========================================
# OUTPUT LENGTH STRATEGY
# ==========================================
#
# max_tokens is a safety ceiling, not a cost control - Anthropic bills
# for tokens actually generated, not for the ceiling. This age-tiering
# exists so naturally-shorter young-child stories get a tighter safety
# cap, while naturally-longer, more nuanced older-audience stories keep
# enough headroom to avoid truncation.
#
# The generator model (Sonnet 5) runs adaptive thinking by default even
# though this app never requests it, and thinking tokens count against
# the same max_tokens budget as the visible story text. These tiers
# carry extra headroom versus a plain non-thinking model to keep that
# from truncating the actual story output.

def _max_tokens_for_age(age):
    try:
        age_value = int(age)
    except (TypeError, ValueError):
        age_value = 5

    if age_value <= 6:
        return 1500
    elif age_value <= 12:
        return 2200
    else:
        return 3500


# ==========================================
# STORY GENERATION
# ==========================================

def generate_story(age, concept, theme, return_usage=False):

    system_prompt = """
You are MindSprout AI, an educational storyteller.

Your job is to turn important life concepts into engaging,
age-appropriate stories.

Rules:
- Use language appropriate for the person's age.
- Teach through the story instead of lecturing.
- Use concrete situations the audience can understand.
- Keep the tone appropriate for the selected age.
- Preserve the exact lesson requested.
- Do not replace it with a different but related lesson.
"""

    user_prompt = f"""
Create a short 6-page story.

Age: {age}
Lesson to teach: {concept}
Story theme: {theme}

There must be exactly 6 pages.

At the end, give one simple core lesson
the reader can remember.
"""

    message = client.messages.parse(
        model="claude-sonnet-5",
        max_tokens=_max_tokens_for_age(age),
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        output_format=MindSproutStory,
    )

    if return_usage:
        return message.parsed_output, message.usage

    return message.parsed_output


# ==========================================
# STORY EVALUATION
# ==========================================

def evaluate_story(age, concept, theme, story, return_usage=False):

    judge_system_prompt = """
You are a strict quality evaluator for MindSprout AI.

Evaluate the story exactly as generated.
Do NOT rewrite or improve it.

Score every criterion from 1 to 5.

1 = poor
2 = significant problems
3 = acceptable but noticeable problems
4 = strong
5 = excellent

Be especially strict about concept fidelity.

A story should not receive a high concept-fidelity score
simply because it teaches a useful related lesson.
It must preserve the specific lesson the user intended.
"""

    judge_prompt = f"""
Evaluate this MindSprout story.

AGE:
{age}

INTENDED LESSON:
{concept}

THEME:
{theme}

GENERATED STORY:
{story.model_dump_json(indent=2)}

Evaluate:

1. Concept fidelity
Did the story preserve the exact intended lesson?

2. Age appropriateness
Are the language, situations and ideas appropriate for the age?

3. Story quality
Is it engaging and does it function as an actual story?

4. Show, don't lecture
Does the story demonstrate the lesson instead of mostly explaining it?

5. Coherence
Are the characters, events and logic consistent?

6. Emotional safety
Is the content emotionally appropriate and safe?
"""

    judge_message = client.messages.parse(
        model="claude-opus-5",
        max_tokens=3000,
        system=judge_system_prompt,
        messages=[
            {
                "role": "user",
                "content": judge_prompt
            }
        ],
        output_format=EvaluationReport,
    )

    if return_usage:
        return judge_message.parsed_output, judge_message.usage

    return judge_message.parsed_output


# ==========================================
# DETERMINISTIC CHECKS
# ==========================================

def check_story_structure(story):

    results = {
        "exactly_6_pages": len(story.pages) == 6,
        "title_present": bool(story.title.strip()),
        "core_lesson_present": bool(story.core_lesson.strip()),
        "all_pages_have_text": all(
            page.story_text.strip()
            for page in story.pages
        ),
    }

    return results