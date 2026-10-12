"""
rag.py

Retrieval for MindSprout: a small library of parenting guides
(guides/*.md) and a keyword search that picks the guide that best
matches a parent's lesson and theme. The chosen guide is added to the
generator's prompt so the story follows that guidance instead of the
model's defaults.

Search is BM25 (classic keyword ranking): no embeddings service, no
extra API cost, and every match can be explained by the words it shares
with the request.

The guides are written from general parenting advice, not from the
golden cases' watch_for notes, so retrieval can't hand the generator
the test's answers.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from rank_bm25 import BM25Okapi

GUIDES_DIR = Path(__file__).parent / "guides"

# Below this score no guide is a real match (e.g. gibberish input), and
# the story is written without one.
MIN_SCORE = 1.5

# "anything" is the app's default theme, so it carries no meaning.
STOPWORDS = set("""
anything
a an and are as at be because but by can do does for from has have how i if in is it its
just like make makes me more my no not of on or our should so some than that the their
them then there they this to too up us very was we what when where who will with you your
""".split())


@dataclass(frozen=True)
class Guide:
    id: str
    title: str
    text: str


def _tokens(text):
    words = re.findall(r"[a-z]+", text.lower())
    out = []
    for w in words:
        if w in STOPWORDS:
            continue
        # light stemming so "saving"/"save" and "friends"/"friend" match
        for suffix in ("ing", "ies", "es", "ed", "s"):
            if len(w) > 4 and w.endswith(suffix):
                w = w[: -len(suffix)]
                break
        out.append(w)
    return out


@lru_cache(maxsize=1)
def _index():
    guides = []
    for path in sorted(GUIDES_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        guides.append(Guide(path.stem, title, text))

    # The title and keyword line are repeated so they weigh more than
    # the body text.
    corpus = []
    for g in guides:
        keywords = next((line for line in g.text.splitlines() if line.startswith("Keywords:")), "")
        corpus.append(_tokens(g.title) * 2 + _tokens(keywords) * 2 + _tokens(g.text))

    return guides, BM25Okapi(corpus)


def rank_guides(concept, theme=""):
    """All guides with their scores for this request, best first."""
    guides, bm25 = _index()
    scores = bm25.get_scores(_tokens(f"{concept} {theme}"))
    return sorted(zip(guides, scores), key=lambda pair: pair[1], reverse=True)


def select_guide(concept, theme=""):
    """The best-matching guide, or None when nothing matches well enough."""
    ranked = rank_guides(concept, theme)
    if not ranked:
        return None
    guide, score = ranked[0]
    return guide if score >= MIN_SCORE else None


def get_guide(guide_id):
    guides, _ = _index()
    return next((g for g in guides if g.id == guide_id), None)
