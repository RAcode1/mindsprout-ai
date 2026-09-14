"""Presentation helpers for the MindSprout AI Streamlit app.

Everything in this module is pure rendering - CSS and small markup
helpers. It never touches st.session_state and never calls the
backend (mindsprout_core). All app flow, state transitions, and API
calls stay in app.py.
"""

import html

import streamlit as st


BASE_STYLES = """
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

/* ---- Trim default Streamlit chrome (safe, CSS-only) ---- */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
div[data-testid="stDecoration"] { display: none; }
.block-container {
    max-width: 720px;
    padding-top: 2.25rem;
    padding-bottom: 3rem;
}

.stApp {
    background-color: var(--ms-cream);
}

/* ---- Header ---- */
.mindsprout-header {
    text-align: center;
    padding: 0.25rem 0 1.75rem 0;
}
.mindsprout-header .brand-mark {
    font-size: 1.9rem;
    line-height: 1;
}
.mindsprout-header h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0.35rem 0 0.3rem 0;
    color: var(--ms-green-dark);
    letter-spacing: -0.01em;
}
.mindsprout-header p.tagline {
    font-size: 1.05rem;
    color: var(--ms-muted);
    margin: 0 0 0.5rem 0;
}
.mindsprout-header p.helper-line {
    font-size: 0.92rem;
    color: var(--ms-muted);
    margin: 0;
}

/* ---- Vertical rhythm ---- */
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
.ms-examples-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--ms-muted);
    margin: 0.35rem 0 0.5rem 0;
}

/* ---- Story cover ---- */
.ms-cover {
    text-align: center;
    padding: 0.25rem 0 1.25rem 0;
}
.ms-cover .ms-eyebrow { justify-content: center; }
.ms-cover h2 {
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--ms-green-dark);
    margin: 0.2rem 0 0.6rem 0;
    letter-spacing: -0.01em;
}
.ms-cover-divider {
    width: 56px;
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

/* ---- Progress bar ---- */
.ms-progress-track {
    width: 100%;
    height: 5px;
    background: var(--ms-border);
    border-radius: 3px;
    overflow: hidden;
    margin: 0.9rem 0 0.35rem 0;
}
.ms-progress-fill {
    height: 100%;
    background: var(--ms-green);
    border-radius: 3px;
    transition: width 0.2s ease;
}

/* ---- Page indicator ---- */
.ms-page-indicator {
    text-align: center;
    color: var(--ms-muted);
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}

/* ---- Lesson screen ---- */
.ms-lesson-eyebrow {
    text-align: center;
    color: var(--ms-accent);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.ms-lesson-card {
    background: linear-gradient(180deg, var(--ms-accent-tint) 0%, #FFFFFF 100%);
    border: 1px solid #EFD9B8;
    border-radius: 22px;
    padding: 2.6rem 2.1rem;
    text-align: center;
    box-shadow: 0 10px 30px rgba(201, 138, 59, 0.1);
}
.ms-lesson-mark {
    font-size: 1.6rem;
    margin-bottom: 0.75rem;
}
.ms-lesson-text {
    font-size: 1.35rem;
    line-height: 1.7;
    color: var(--ms-text);
    font-weight: 600;
    margin: 0;
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
button[kind="secondary"] {
    border-color: var(--ms-border) !important;
    color: var(--ms-text) !important;
    background-color: #FFFFFF !important;
}

/* ---- Example prompt chips ---- */
div[data-testid="column"] div.stButton > button {
    font-size: 0.85rem;
    padding: 0.4rem 0.6rem;
}

hr.ms-divider {
    border: none;
    border-top: 1px solid var(--ms-border);
    margin: 1.75rem 0;
}

/* ---- Small screens ---- */
@media (max-width: 480px) {
    .mindsprout-header h1 { font-size: 1.6rem; }
    .ms-cover h2 { font-size: 1.4rem; }
    .ms-page-card { padding: 1.5rem 1.25rem; min-height: 180px; }
    .ms-page-text { font-size: 1.05rem; }
    .ms-lesson-card { padding: 1.9rem 1.4rem; }
    .ms-lesson-text { font-size: 1.15rem; }
}
</style>
"""


def inject_base_styles():
    st.markdown(BASE_STYLES, unsafe_allow_html=True)


def render_header():
    st.markdown(
        """
        <div class="mindsprout-header">
            <div class="brand-mark">🌱</div>
            <h1>MindSprout AI</h1>
            <p class="tagline">Turn important life lessons into stories they'll remember.</p>
            <p class="helper-line">
                Tell us what you want to teach. MindSprout will shape it for their age.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_bar(current, total):
    pct = max(0, min(100, round(current / total * 100)))
    st.markdown(
        f"""
        <div class="ms-progress-track">
            <div class="ms-progress-fill" style="width:{pct}%;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_cover(title):
    safe_title = html.escape(title)
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


def render_page_card(story_text):
    safe_text = html.escape(story_text).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="ms-page-card">
            <p class="ms-page-text">{safe_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_lesson_card(core_lesson):
    safe_lesson = html.escape(core_lesson).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="ms-lesson-eyebrow">The Core Lesson</div>
        <div class="ms-lesson-card">
            <div class="ms-lesson-mark">🌿</div>
            <p class="ms-lesson-text">{safe_lesson}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
