import html
import os

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
)


# ==========================================
# PAGE SETUP + STYLING
# ==========================================

st.set_page_config(
    page_title="MindSprout AI",
    page_icon="🌱",
    layout="centered",
)

st.markdown(
    """
    <style>
    :root {
        --ms-green: #2E7D32;
        --ms-green-dark: #1B5E20;
        --ms-green-tint: #EAF3EA;
        --ms-cream: #FAF9F5;
        --ms-text: #2B332C;
        --ms-muted: #74806F;
        --ms-border: #E7E4DA;
        --ms-accent: #C98A3B;
        --ms-accent-tint: #FBF2E7;
    }

    .stApp {
        background-color: var(--ms-cream);
    }

    /* ---- Header ---- */
    .mindsprout-header {
        text-align: center;
        padding: 0.75rem 0 1.5rem 0;
    }
    .mindsprout-header .brand-mark {
        font-size: 2.1rem;
        line-height: 1;
    }
    .mindsprout-header h1 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.35rem 0 0.2rem 0;
        color: var(--ms-green-dark);
        letter-spacing: -0.01em;
    }
    .mindsprout-header p {
        font-size: 1.02rem;
        color: var(--ms-muted);
        margin: 0;
    }

    /* ---- Generic vertical rhythm ---- */
    .ms-gap-sm { margin-top: 0.5rem; }
    .ms-gap { margin-top: 1.5rem; }
    .ms-gap-lg { margin-top: 2.25rem; }

    /* ---- Section labels ---- */
    .ms-eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--ms-green);
        margin-bottom: 0.35rem;
    }
    .ms-form-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--ms-text);
        margin-bottom: 0.15rem;
    }
    .ms-form-subtitle {
        color: var(--ms-muted);
        font-size: 0.95rem;
        margin-bottom: 1.1rem;
    }

    /* ---- Story cover ---- */
    .ms-cover {
        text-align: center;
        padding: 0.5rem 0 1.25rem 0;
    }
    .ms-cover .ms-eyebrow { justify-content: center; }
    .ms-cover h2 {
        font-size: 1.85rem;
        font-weight: 800;
        color: var(--ms-green-dark);
        margin: 0.2rem 0 0.6rem 0;
        letter-spacing: -0.01em;
    }
    .ms-cover-divider {
        width: 64px;
        height: 3px;
        background: var(--ms-accent);
        border-radius: 3px;
        margin: 0 auto;
        opacity: 0.85;
    }

    /* ---- Reading card ---- */
    .ms-page-card {
        background: #FFFFFF;
        border: 1px solid var(--ms-border);
        border-radius: 20px;
        padding: 2.1rem 1.9rem;
        box-shadow: 0 6px 24px rgba(46, 125, 50, 0.07);
        min-height: 220px;
        display: flex;
        align-items: center;
    }
    .ms-page-text {
        font-size: 1.16rem;
        line-height: 1.85;
        color: var(--ms-text);
        margin: 0;
    }

    /* ---- Lesson card ---- */
    .ms-lesson-card {
        background: var(--ms-accent-tint);
        border: 1px solid #EFD9B8;
        border-left: 5px solid var(--ms-accent);
        border-radius: 18px;
        padding: 2rem 1.9rem;
    }
    .ms-lesson-label {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--ms-accent);
        margin-bottom: 0.5rem;
    }
    .ms-lesson-text {
        font-size: 1.2rem;
        line-height: 1.75;
        color: var(--ms-text);
        font-weight: 500;
        margin: 0;
    }

    /* ---- Page indicator ---- */
    .ms-page-indicator {
        text-align: center;
        color: var(--ms-muted);
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        padding-top: 0.4rem;
    }

    /* ---- Buttons ---- */
    div.stButton > button,
    div.stFormSubmitButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: transform 0.05s ease-in-out;
    }
    div.stButton > button:active,
    div.stFormSubmitButton > button:active {
        transform: scale(0.98);
    }
    button[kind="primary"] {
        background-color: var(--ms-green) !important;
        border-color: var(--ms-green) !important;
        color: #FFFFFF !important;
    }
    button[kind="primary"]:hover {
        background-color: var(--ms-green-dark) !important;
        border-color: var(--ms-green-dark) !important;
        color: #FFFFFF !important;
    }
    button[kind="primary"]:active {
        background-color: var(--ms-green-dark) !important;
        border-color: var(--ms-green-dark) !important;
    }
    button[kind="secondary"] {
        border-color: var(--ms-border) !important;
        color: var(--ms-text) !important;
    }

    hr.ms-divider {
        border: none;
        border-top: 1px solid var(--ms-border);
        margin: 1.75rem 0;
    }
    </style>

    <div class="mindsprout-header">
        <div class="brand-mark">🌱</div>
        <h1>MindSprout AI</h1>
        <p>Turn important life lessons into age-appropriate stories.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# SESSION STATE DEFAULTS
# ==========================================
#
# "stage" drives which view is shown: the input form, or the generated
# story. Keeping it explicit (rather than inferring the view from
# whether a story happens to exist) makes "Create another story" and
# "Edit lesson / inputs" simple, predictable state transitions instead
# of ad-hoc reruns.

defaults = {
    "stage": "form",                # "form" | "story"
    "story": None,
    "story_inputs": None,           # (age, concept, theme) used to generate the current story
    "structural_checks": None,
    "generation_error": None,
    "evaluation": None,
    "evaluation_error": None,
    "current_page": 1,              # 1..N = story pages, N+1 = core lesson
    "input_age": 5,
    "input_theme": "",
    "input_concept": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def start_new_story():
    """Clear everything and return to a blank input form."""
    st.session_state["stage"] = "form"
    st.session_state["story"] = None
    st.session_state["story_inputs"] = None
    st.session_state["structural_checks"] = None
    st.session_state["generation_error"] = None
    st.session_state["evaluation"] = None
    st.session_state["evaluation_error"] = None
    st.session_state["current_page"] = 1
    st.session_state["input_age"] = 5
    st.session_state["input_theme"] = ""
    st.session_state["input_concept"] = ""


def edit_inputs():
    """Return to the form, pre-filled with the inputs that made this story."""
    age, concept, theme = st.session_state["story_inputs"]
    st.session_state["input_age"] = age
    st.session_state["input_theme"] = theme
    st.session_state["input_concept"] = concept
    st.session_state["stage"] = "form"


# ==========================================
# INPUT EXPERIENCE
# ==========================================

if st.session_state["stage"] == "form":

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
            col1, col2 = st.columns(2)

            with col1:
                age = st.number_input(
                    "Child's age",
                    min_value=1,
                    max_value=18,
                    value=st.session_state["input_age"],
                    step=1,
                    help="Used to set the story's language, tone, and pacing.",
                )

            with col2:
                theme = st.text_input(
                    "Story theme",
                    value=st.session_state["input_theme"],
                    placeholder="e.g. Family and a toy store",
                    help="The world or setting for the story.",
                )

            concept = st.text_area(
                "Lesson or concept to teach",
                value=st.session_state["input_concept"],
                height=140,
                placeholder=(
                    "e.g. Boredom is alright. Parents will sometimes be busy "
                    "and friends may not be available."
                ),
                help="Be specific - this is the exact lesson the story will preserve.",
            )

            st.markdown('<div class="ms-gap-sm"></div>', unsafe_allow_html=True)

            submitted = st.form_submit_button(
                "🌱  Generate Story",
                use_container_width=True,
                type="primary",
            )

    if submitted:
        if not concept.strip():
            st.warning("Please enter a lesson or concept before generating a story.")
        else:
            with st.spinner("🌱 Growing your story... this usually takes a few seconds."):
                try:
                    story = generate_story(age, concept, theme)
                    st.session_state["story"] = story
                    st.session_state["story_inputs"] = (age, concept, theme)
                    st.session_state["structural_checks"] = check_story_structure(story)
                    st.session_state["evaluation"] = None
                    st.session_state["evaluation_error"] = None
                    st.session_state["generation_error"] = None
                    st.session_state["current_page"] = 1
                    st.session_state["stage"] = "story"
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
# STORY READING EXPERIENCE (FROM CACHE - NO API CALLS)
# ==========================================
#
# Everything below reads story / evaluation data that already lives in
# st.session_state. Paging through the story only changes
# st.session_state["current_page"] and reruns the script - it never
# touches generate_story() or evaluate_story() again.

story = st.session_state.get("story")

if st.session_state["stage"] == "story" and story is not None:

    total_pages = len(story.pages)
    lesson_slot = total_pages + 1
    current = st.session_state["current_page"]

    # Story cover / header
    # Story text comes from the model, so it is HTML-escaped before being
    # placed inside these unsafe_allow_html blocks (used for card styling).
    safe_title = html.escape(story.title)
    st.markdown(
        f"""
        <div class="ms-cover">
            <div class="ms-eyebrow" style="display:flex;justify-content:center;">
                A MindSprout Story
            </div>
            <h2>{safe_title}</h2>
            <div class="ms-cover-divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Page / lesson content
    if current <= total_pages:
        page = story.pages[current - 1]
        safe_page_text = html.escape(page.story_text).replace("\n", "<br>")
        st.markdown(
            f"""
            <div class="ms-page-card">
                <p class="ms-page-text">{safe_page_text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        safe_lesson_text = html.escape(story.core_lesson).replace("\n", "<br>")
        st.markdown(
            f"""
            <div class="ms-lesson-card">
                <div class="ms-lesson-label">🌿 Core Lesson</div>
                <p class="ms-lesson-text">{safe_lesson_text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Page indicator
    if current <= total_pages:
        st.markdown(
            f'<div class="ms-page-indicator">Page {current} of {total_pages}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="ms-page-indicator">The End</div>',
            unsafe_allow_html=True,
        )

    # Previous / Next navigation
    st.markdown('<div class="ms-gap-sm"></div>', unsafe_allow_html=True)
    nav_col1, nav_col2 = st.columns(2)

    with nav_col1:
        if st.button(
            "← Previous",
            use_container_width=True,
            disabled=(current == 1),
        ):
            st.session_state["current_page"] = max(1, current - 1)
            st.rerun()

    with nav_col2:
        if current < total_pages:
            next_label = "Next →"
        elif current == total_pages:
            next_label = "Core Lesson →"
        else:
            next_label = "Next →"

        if st.button(
            next_label,
            use_container_width=True,
            disabled=(current >= lesson_slot),
            type="primary" if current <= total_pages else "secondary",
        ):
            st.session_state["current_page"] = min(lesson_slot, current + 1)
            st.rerun()

    if current != 1:
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            if st.button("↺ Back to Page 1", use_container_width=True):
                st.session_state["current_page"] = 1
                st.rerun()

    # ==========================================
    # STORY ACTIONS
    # ==========================================

    st.markdown('<hr class="ms-divider">', unsafe_allow_html=True)
    action_col1, action_col2 = st.columns(2)

    with action_col1:
        if st.button("✨ Create another story", use_container_width=True, type="primary"):
            start_new_story()
            st.rerun()

    with action_col2:
        if st.button("✎ Edit lesson / inputs", use_container_width=True):
            edit_inputs()
            st.rerun()

    # ==========================================
    # DEVELOPER / QUALITY CHECK (COLLAPSED, UNOBTRUSIVE)
    # ==========================================
    #
    # Structural QA is cheap, local, and deterministic, so it's already
    # computed and simply displayed here. The AI quality evaluator only
    # runs when the developer explicitly clicks the button below - it
    # is never triggered automatically, including when this expander is
    # opened or the page is navigated.

    st.markdown('<div class="ms-gap"></div>', unsafe_allow_html=True)
    with st.expander("Developer / Quality Check", expanded=False):

        st.caption("Structural QA (automatic, no API cost)")
        structural_checks = st.session_state.get("structural_checks") or {}
        for check_name, passed in structural_checks.items():
            st.write(f"- {check_name}: {'PASS' if passed else 'FAIL'}")

        st.divider()

        st.caption("AI Quality Check (calls the Opus judge model - not free)")
        run_quality_check = st.button("Run AI Quality Check")

        if run_quality_check:
            eval_age, eval_concept, eval_theme = st.session_state["story_inputs"]

            with st.spinner("Reviewing story quality..."):
                try:
                    evaluation = evaluate_story(
                        eval_age, eval_concept, eval_theme, story
                    )
                    st.session_state["evaluation"] = evaluation
                    st.session_state["evaluation_error"] = None
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

elif st.session_state["stage"] == "form" and not st.session_state.get("generation_error"):
    st.info("Fill in the details above and click **Generate Story** to begin.")
