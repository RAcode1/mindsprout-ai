"""Presentation helpers for the MindSprout AI Streamlit app.

Everything in this module is pure rendering - CSS and small markup
helpers. It never touches st.session_state and never calls the
backend (mindsprout_core). All app flow, state transitions, and API
calls stay in app.py.
"""

import html

import streamlit as st


FONT_IMPORTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link
    href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,500&family=Literata:ital,opsz,wght@0,18..36,400;0,18..36,500;1,18..36,400&family=Inter:wght@400;500;600;700&display=swap"
    rel="stylesheet"
>
"""

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
    --ms-font-display: "Fraunces", "Iowan Old Style", Georgia, serif;
    --ms-font-serif: "Literata", Georgia, "Iowan Old Style", serif;
    --ms-font-body: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

@keyframes ms-card-enter {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes ms-fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* ---- Type system ---- */
/* :not([data-testid="stIconMaterial"]) keeps Material icon buttons
   (Previous/Next/etc.) working - those render as ligatures in a
   dedicated icon font, which a blanket font-family override breaks. */
.stApp,
.stApp p,
.stApp span:not([data-testid="stIconMaterial"]),
.stApp label,
.stApp div {
    font-family: var(--ms-font-body);
}
.mindsprout-header h1,
.ms-form-title,
.ms-cover h2,
.ms-lesson-text {
    font-family: var(--ms-font-display) !important;
}
.ms-page-text {
    font-family: var(--ms-font-serif);
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
    animation: ms-fade-in 0.4s ease;
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
    position: relative;
    background:
        radial-gradient(circle at 100% 0%, rgba(46, 125, 50, 0.045), transparent 55%),
        linear-gradient(180deg, #FFFFFF 0%, #FDFCF8 100%);
    border: 1px solid var(--ms-border);
    border-left: 4px solid var(--ms-green);
    border-radius: 4px 20px 20px 4px;
    padding: 2.3rem 2.2rem 2.3rem 2rem;
    box-shadow:
        0 1px 2px rgba(43, 51, 44, 0.05),
        0 14px 32px rgba(46, 125, 50, 0.1);
    min-height: 220px;
    display: flex;
    align-items: center;
    overflow: hidden;
    animation: ms-card-enter 0.45s cubic-bezier(.16, 1, .3, 1);
}
.ms-page-card::after {
    content: "";
    position: absolute;
    top: 0;
    right: 0;
    width: 0;
    height: 0;
    border-style: solid;
    border-width: 0 22px 22px 0;
    border-color: transparent var(--ms-cream) transparent transparent;
    opacity: 0.7;
}
.ms-page-text {
    font-size: 1.18rem;
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
    background: linear-gradient(160deg, var(--ms-accent-tint) 0%, #FFFFFF 65%);
    border: 1px solid #EFD9B8;
    border-radius: 22px;
    padding: 2.6rem 2.1rem;
    text-align: center;
    box-shadow:
        0 1px 2px rgba(201, 138, 59, 0.06),
        0 16px 36px rgba(201, 138, 59, 0.14);
    animation: ms-card-enter 0.5s cubic-bezier(.16, 1, .3, 1);
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
    transition: transform 0.12s ease-out, box-shadow 0.12s ease-out;
}
div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    transform: translateY(-1px);
}
div.stButton > button:active,
div.stFormSubmitButton > button:active {
    transform: scale(0.98) translateY(0);
}
button[kind="primary"] {
    background-color: var(--ms-green) !important;
    border-color: var(--ms-green) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(46, 125, 50, 0.22);
}
button[kind="primary"]:hover {
    background-color: var(--ms-green-dark) !important;
    border-color: var(--ms-green-dark) !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 18px rgba(46, 125, 50, 0.3);
}
button[kind="secondary"] {
    border-color: var(--ms-border) !important;
    color: var(--ms-text) !important;
    background-color: #FFFFFF !important;
}

/* ---- Example prompt chips (scoped to their own container only -
   must not bleed into Previous/Next, Edit/Create, etc.) ---- */
.st-key-ms_examples div.stButton > button {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.5rem 0.9rem;
    border-radius: 999px;
    background-color: var(--ms-green-tint) !important;
    border-color: transparent !important;
    color: var(--ms-green-dark) !important;
    box-shadow: none;
}
.st-key-ms_examples div.stButton > button:hover {
    background-color: #FFFFFF !important;
    border-color: var(--ms-green) !important;
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
    .ms-page-card { padding: 1.5rem 1.25rem 1.5rem 1.1rem; min-height: 180px; }
    .ms-page-card::after { border-width: 0 14px 14px 0; }
    .ms-page-text { font-size: 1.05rem; }
    .ms-lesson-card { padding: 1.9rem 1.4rem; }
    .ms-lesson-text { font-size: 1.15rem; }
}
</style>
"""


def inject_base_styles():
    st.markdown(FONT_IMPORTS + BASE_STYLES, unsafe_allow_html=True)


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
