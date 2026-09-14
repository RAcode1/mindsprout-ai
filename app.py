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
    estimate_cost,
)


# ==========================================
# PAGE SETUP + LIGHT STYLING
# ==========================================

st.set_page_config(
    page_title="MindSprout AI",
    page_icon="🌱",
    layout="centered",
)

st.markdown(
    """
    <style>
    .mindsprout-header {
        text-align: center;
        padding: 0.5rem 0 1rem 0;
    }
    .mindsprout-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.1rem;
        color: #2E7D32;
    }
    .mindsprout-header p {
        font-size: 1.05rem;
        color: #6b7a6e;
        margin-top: 0;
    }
    .section-gap {
        margin-top: 1.25rem;
    }
    button[kind="primary"] {
        background-color: #2E7D32 !important;
        border-color: #2E7D32 !important;
        color: #FFFFFF !important;
    }
    button[kind="primary"]:hover {
        background-color: #1B5E20 !important;
        border-color: #1B5E20 !important;
        color: #FFFFFF !important;
    }
    button[kind="primary"]:active {
        background-color: #174E1B !important;
        border-color: #174E1B !important;
        color: #FFFFFF !important;
    }
    </style>

    <div class="mindsprout-header">
        <h1>🌱 MindSprout AI</h1>
        <p>Turn important life lessons into age-appropriate stories.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# USER INPUTS
# ==========================================

with st.form("story_form"):
    col1, col2 = st.columns(2)

    with col1:
        age = st.number_input(
            "Child's age",
            min_value=1,
            max_value=18,
            value=5,
            step=1,
        )

    with col2:
        theme = st.text_input(
            "Story theme",
            placeholder="e.g. Family and a toy store",
        )

    concept = st.text_area(
        "Lesson / concept to teach",
        height=150,
        placeholder=(
            "e.g. Boredom is alright. Parents will sometimes be busy "
            "and friends may not be available."
        ),
    )

    submitted = st.form_submit_button(
        "Generate Story",
        use_container_width=True,
        type="primary",
    )


# ==========================================
# GENERATE STORY ONLY (NO AI EVALUATION HERE)
# ==========================================
#
# Generate Story calls only generate_story(). Structural QA is cheap
# and local (no API call), so it also runs automatically here. The AI
# evaluator (evaluate_story) is intentionally NOT called in this block
# - it only runs when the user explicitly clicks "Run AI Quality Check"
# further down, since that call uses the Opus 5 judge model and costs
# real money.
#
# The story, and its structural checks, are cached in st.session_state
# so that later reruns (opening the expander, clicking the quality
# check button) redisplay the same story instead of regenerating it.

if submitted:
    if not concept.strip():
        st.warning("Please enter a lesson or concept before generating a story.")
    else:
        # A new story invalidates any previous evaluation.
        st.session_state["story"] = None
        st.session_state["story_inputs"] = None
        st.session_state["structural_checks"] = None
        st.session_state["generation_error"] = None
        st.session_state["generation_usage"] = None
        st.session_state["evaluation"] = None
        st.session_state["evaluation_error"] = None
        st.session_state["evaluation_usage"] = None

        with st.spinner("Writing your story..."):
            try:
                story, usage = generate_story(age, concept, theme, return_usage=True)
                st.session_state["story"] = story
                st.session_state["story_inputs"] = (age, concept, theme)
                st.session_state["structural_checks"] = check_story_structure(story)
                st.session_state["generation_usage"] = usage
            except Exception as error:
                st.session_state["generation_error"] = str(error)


# ==========================================
# ERROR DISPLAY (FRIENDLY, NO TRACEBACKS)
# ==========================================

if st.session_state.get("generation_error"):
    st.error(
        "Something went wrong while generating the story. "
        "Please try again in a moment.\n\n"
        f"Details: {st.session_state['generation_error']}"
    )


# ==========================================
# DISPLAY STORY (FROM CACHE - NOT REGENERATED)
# ==========================================

story = st.session_state.get("story")

if story is not None:
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    st.header(story.title)

    for page in story.pages:
        with st.container(border=True):
            st.markdown(f"#### 📖 Page {page.page_number}")
            st.write(page.story_text)

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("#### 🌿 Core Lesson")
        st.write(story.core_lesson)

    # ==========================================
    # DEVELOPER / QUALITY CHECK (COLLAPSED)
    # ==========================================

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    with st.expander("Developer / Quality Check", expanded=False):

        st.markdown("**Structural QA** _(automatic, no API cost)_")
        structural_checks = st.session_state.get("structural_checks") or {}
        for check_name, passed in structural_checks.items():
            st.write(f"- {check_name}: {'PASS' if passed else 'FAIL'}")

        st.divider()

        st.markdown("**AI Quality Check** _(calls the Opus 5 judge model)_")
        run_quality_check = st.button("Run AI Quality Check")

        if run_quality_check:
            eval_age, eval_concept, eval_theme = st.session_state["story_inputs"]

            with st.spinner("Running AI quality evaluation..."):
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

        st.markdown("**API Usage & Cost** _(estimated, developer-only)_")

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
elif not submitted:
    st.info("Fill in the details above and click **Generate Story** to begin.")
