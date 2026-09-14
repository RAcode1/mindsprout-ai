import concurrent.futures
import itertools
import os
import time

import streamlit as st

# ==========================================
# STREAMLIT CLOUD SECRET BRIDGE
# ==========================================
#
# Locally, ANTHROPIC_API_KEY comes from .env via load_dotenv() inside
# mindsprout_core.py - that workflow is unchanged.
#
# On Streamlit Community Cloud there is no .env file; the key is
# configured instead as an app "secret" and exposed through
# st.secrets. This block copies it into the environment variable
# mindsprout_core.py already expects, before that module is imported
# (it builds its Anthropic() client at import time). If no secret is
# configured (e.g. running locally without Streamlit secrets set up),
# this is a silent no-op and .env continues to be the source of truth.

if "ANTHROPIC_API_KEY" not in os.environ:
    try:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass

from mindsprout_core import (
    generate_story,
    evaluate_story,
    check_story_structure,
    estimate_cost,
)
from ui import (
    inject_base_styles,
    render_header,
    render_progress_bar,
    render_cover,
    render_page_card,
    render_lesson_card,
)


# ==========================================
# PAGE SETUP + STYLING
# ==========================================

st.set_page_config(
    page_title="MindSprout AI",
    page_icon="🌱",
    layout="centered",
)

inject_base_styles()
render_header()


# ==========================================
# SESSION STATE DEFAULTS
# ==========================================
#
# "stage" drives which screen is shown: the creation form, the page-by-
# page reader, or the standalone core-lesson screen. Keeping it
# explicit (rather than inferring the view from whether a story
# happens to exist) makes every navigation action - Next/Previous,
# "See the lesson", "Edit my idea", "Create another story" - a simple,
# predictable state transition instead of an ad-hoc rerun.

EXAMPLE_PROMPTS = [
    {
        "label": "Handling disappointment",
        "concept": (
            "It's okay to feel disappointed when things don't go as "
            "planned. Those feelings pass, and it's okay to try again."
        ),
        "theme": "Anything",
    },
    {
        "label": "Saving money",
        "concept": (
            "Saving a little at a time adds up, and it's okay to wait "
            "before buying something you want."
        ),
        "theme": "Anything",
    },
    {
        "label": "Being yourself",
        "concept": (
            "You don't have to change who you are to fit in. Being "
            "yourself is what makes you interesting."
        ),
        "theme": "Anything",
    },
]

LOADING_PHRASES = [
    "Planting the idea...",
    "Growing the characters...",
    "Turning the lesson into a story...",
    "Almost ready...",
]

defaults = {
    "stage": "create",              # "create" | "reading" | "lesson"
    "story": None,
    "story_inputs": None,           # (age, concept, theme) used to generate the current story
    "structural_checks": None,
    "generation_error": None,
    "generation_usage": None,
    "evaluation": None,
    "evaluation_error": None,
    "evaluation_usage": None,
    "current_page": 1,              # 1..6 story pages (lesson is its own stage, not a page slot)
    "input_age": 5,
    "input_theme": "Anything",
    "input_concept": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def start_new_story():
    """Clear everything and return to a blank creation screen."""
    st.session_state["stage"] = "create"
    st.session_state["story"] = None
    st.session_state["story_inputs"] = None
    st.session_state["structural_checks"] = None
    st.session_state["generation_error"] = None
    st.session_state["generation_usage"] = None
    st.session_state["evaluation"] = None
    st.session_state["evaluation_error"] = None
    st.session_state["evaluation_usage"] = None
    st.session_state["current_page"] = 1
    st.session_state["input_age"] = 5
    st.session_state["input_theme"] = "Anything"
    st.session_state["input_concept"] = ""


def edit_inputs():
    """Return to the creation screen, pre-filled with this story's inputs."""
    age, concept, theme = st.session_state["story_inputs"]
    st.session_state["input_age"] = age
    st.session_state["input_theme"] = theme
    st.session_state["input_concept"] = concept
    st.session_state["stage"] = "create"


def apply_example(example):
    """Populate the form from an example prompt. No API call."""
    st.session_state["input_concept"] = example["concept"]
    st.session_state["input_theme"] = example["theme"]


def run_story_generation(age, concept, theme):
    """Call generate_story exactly once, rotating friendly status text
    while the (single) request is in flight. The API call runs in a
    background thread purely so the displayed copy can rotate every
    ~1.1s; it does not add, retry, or duplicate any request.
    """

    placeholder = st.empty()
    with st.spinner("Growing your story..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                generate_story, age, concept, theme, return_usage=True
            )
            for phrase in itertools.cycle(LOADING_PHRASES):
                placeholder.caption(phrase)
                if future.done():
                    break
                time.sleep(1.1)
        placeholder.empty()
        return future.result()


# ==========================================
# DEVELOPER / QUALITY CHECK (COLLAPSED, UNOBTRUSIVE)
# ==========================================
#
# Structural QA is cheap, local, and deterministic, so it's already
# computed and simply displayed here. The AI quality evaluator only
# runs when the developer explicitly clicks the button below - it is
# never triggered automatically, including when this expander is
# opened or the page is navigated.

def render_dev_panel(story):
    st.markdown('<div class="ms-gap">', unsafe_allow_html=True)
    with st.expander("Developer / Quality Check", expanded=False):

        st.caption("Structural QA (automatic, no API cost)")
        structural_checks = st.session_state.get("structural_checks") or {}
        for check_name, passed in structural_checks.items():
            st.write(f"- {check_name}: {'PASS' if passed else 'FAIL'}")

        st.divider()

        st.caption("AI Quality Check (calls the Opus 5 judge model - not free)")
        run_quality_check = st.button("Run AI Quality Check")

        if run_quality_check:
            eval_age, eval_concept, eval_theme = st.session_state["story_inputs"]

            with st.spinner("Reviewing story quality..."):
                try:
                    evaluation, eval_usage = evaluate_story(
                        eval_age, eval_concept, eval_theme, story, return_usage=True
                    )
                    st.session_state["evaluation"] = evaluation
                    st.session_state["evaluation_error"] = None
                    st.session_state["evaluation_usage"] = eval_usage
                except Exception as error:
                    st.session_state["evaluation_error"] = str(error)

        if st.session_state.get("evaluation_error"):
            st.error(
                "Something went wrong while running the quality "
                "evaluation.\n\n"
                f"Details: {st.session_state['evaluation_error']}"
            )

        evaluation = st.session_state.get("evaluation")
        if evaluation:
            st.markdown("**AI Quality Scores**")

            criteria = [
                ("Concept fidelity", evaluation.concept_fidelity),
                ("Age appropriateness", evaluation.age_appropriateness),
                ("Story quality", evaluation.story_quality),
                ("Show, don't lecture", evaluation.show_dont_lecture),
                ("Coherence", evaluation.coherence),
                ("Emotional safety", evaluation.emotional_safety),
            ]

            for label, result in criteria:
                st.write(f"- **{label}:** {result.score}/5 - {result.reason}")

            st.markdown("**Evaluator summary**")
            st.write(evaluation.overall_summary)

        st.divider()

        st.caption("API usage & cost (estimated, developer-only)")

        generation_usage = st.session_state.get("generation_usage")
        if generation_usage:
            generation_cost = estimate_cost("claude-sonnet-5", generation_usage)
            cost_text = f"${generation_cost:.4f}" if generation_cost is not None else "unknown"
            st.write(
                f"- **Story generation (Sonnet 5):** "
                f"{generation_usage.input_tokens} input tokens, "
                f"{generation_usage.output_tokens} output tokens "
                f"(~{cost_text})"
            )

        evaluation_usage = st.session_state.get("evaluation_usage")
        if evaluation_usage:
            evaluation_cost = estimate_cost("claude-opus-5", evaluation_usage)
            cost_text = f"${evaluation_cost:.4f}" if evaluation_cost is not None else "unknown"
            st.write(
                f"- **Quality check (Opus 5):** "
                f"{evaluation_usage.input_tokens} input tokens, "
                f"{evaluation_usage.output_tokens} output tokens "
                f"(~{cost_text})"
            )
        else:
            st.caption("Run the AI Quality Check above to see its usage and cost.")


def render_story_controls():
    """The two low-key actions always available once a story exists."""
    st.markdown('<div class="ms-gap-sm"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Edit my idea", icon=":material/edit:", use_container_width=True):
            edit_inputs()
            st.rerun()
    with col2:
        if st.button("Create another story", icon=":material/auto_awesome:", use_container_width=True):
            start_new_story()
            st.rerun()


# ==========================================
# CREATION SCREEN
# ==========================================

if st.session_state["stage"] == "create":

    with st.container(border=True):
        st.markdown(
            """
            <div class="ms-eyebrow">Create a story</div>
            <div class="ms-form-title">Tell us about your child and the lesson</div>
            <div class="ms-form-subtitle">
                MindSprout turns this into a short, age-appropriate 6-page story.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("story_form"):
            age = st.slider(
                "Child's age",
                min_value=1,
                max_value=18,
                value=st.session_state["input_age"],
                help="Used to set the story's language, tone, and pacing.",
            )

            concept = st.text_area(
                "Lesson or concept to teach",
                value=st.session_state["input_concept"],
                height=170,
                placeholder=(
                    "e.g. Boredom is alright. Parents will sometimes be busy "
                    "and friends may not be available."
                ),
                help=(
                    "Describe the idea in your own words - MindSprout will "
                    "shape it into a story instead of a lecture."
                ),
            )

            theme = st.text_input(
                "Story theme",
                value=st.session_state["input_theme"],
                help='Optional. Leave it as "Anything" if you don\'t have a setting in mind.',
            )

            st.markdown('<div class="ms-gap-sm"></div>', unsafe_allow_html=True)

            submitted = st.form_submit_button(
                "Generate My Story",
                use_container_width=True,
                type="primary",
            )

        st.markdown('<div class="ms-examples-label">Need a spark? Try one of these</div>', unsafe_allow_html=True)
        with st.container(key="ms_examples"):
            example_cols = st.columns(3)
            for col, example in zip(example_cols, EXAMPLE_PROMPTS):
                with col:
                    if st.button(example["label"], use_container_width=True, key=f"example_{example['label']}"):
                        apply_example(example)
                        st.rerun()

    if submitted:
        if not concept.strip():
            st.warning("Please enter a lesson or concept before generating a story.")
        else:
            try:
                story, usage = run_story_generation(age, concept, theme)
                st.session_state["story"] = story
                st.session_state["story_inputs"] = (age, concept, theme)
                st.session_state["structural_checks"] = check_story_structure(story)
                st.session_state["generation_usage"] = usage
                st.session_state["evaluation"] = None
                st.session_state["evaluation_error"] = None
                st.session_state["evaluation_usage"] = None
                st.session_state["generation_error"] = None
                st.session_state["current_page"] = 1
                st.session_state["stage"] = "reading"
                st.rerun()
            except Exception as error:
                st.session_state["generation_error"] = str(error)

    if st.session_state.get("generation_error"):
        st.error(
            "Something went wrong while generating the story. "
            "Please try again in a moment.\n\n"
            f"Details: {st.session_state['generation_error']}"
        )


# ==========================================
# BOOK READER (FROM CACHE - NO API CALLS)
# ==========================================
#
# Everything below reads story / evaluation data that already lives in
# st.session_state. Paging, opening the dev expander, and switching to
# the lesson screen only ever change st.session_state and rerun the
# script - none of it touches generate_story() or evaluate_story()
# again.

story = st.session_state.get("story")
total_pages = len(story.pages) if story is not None else 0

if st.session_state["stage"] == "reading" and story is not None:

    current = st.session_state["current_page"]

    render_cover(story.title)

    page = story.pages[current - 1]
    render_page_card(page.story_text)

    render_progress_bar(current, total_pages)
    st.markdown(
        f'<div class="ms-page-indicator">Page {current} of {total_pages}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ms-gap-sm"></div>', unsafe_allow_html=True)
    nav_col1, nav_col2 = st.columns(2)

    with nav_col1:
        if st.button(
            "Previous",
            icon=":material/chevron_left:",
            use_container_width=True,
            disabled=(current == 1),
        ):
            st.session_state["current_page"] = max(1, current - 1)
            st.rerun()

    with nav_col2:
        is_last_page = current >= total_pages
        next_label = "See the lesson" if is_last_page else "Next"
        next_icon = ":material/auto_stories:" if is_last_page else ":material/chevron_right:"
        if st.button(next_label, icon=next_icon, use_container_width=True, type="primary"):
            if is_last_page:
                st.session_state["stage"] = "lesson"
            else:
                st.session_state["current_page"] = current + 1
            st.rerun()

    render_story_controls()
    render_dev_panel(story)


# ==========================================
# CORE LESSON SCREEN
# ==========================================

elif st.session_state["stage"] == "lesson" and story is not None:

    render_cover(story.title)
    render_lesson_card(story.core_lesson)

    st.markdown('<div class="ms-gap-sm"></div>', unsafe_allow_html=True)
    lesson_col1, lesson_col2 = st.columns(2)

    with lesson_col1:
        if st.button("Back to story", icon=":material/chevron_left:", use_container_width=True):
            st.session_state["stage"] = "reading"
            st.session_state["current_page"] = total_pages
            st.rerun()

    with lesson_col2:
        if st.button(
            "Read again from Page 1",
            icon=":material/replay:",
            use_container_width=True,
            type="primary",
        ):
            st.session_state["stage"] = "reading"
            st.session_state["current_page"] = 1
            st.rerun()

    render_story_controls()
    render_dev_panel(story)


elif st.session_state["stage"] == "create" and not st.session_state.get("generation_error"):
    st.info("Fill in the details above and click **Generate My Story** to begin.")
