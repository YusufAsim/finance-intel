"""Question clean up."""

import re

from app.graph.state import AgentState

_WHITESPACE = re.compile(r"\s+")

# Routing keywords are written in plain ascii, so turkish letters are folded
# before matching. Otherwise "islem" would never match a question that spells
# it "islem" with the dotless i. The combining dot is stripped because lower()
# turns a capital dotted I into "i" plus U+0307.
_FOLD = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "â": "a",
        "î": "i",
        "û": "u",
        "̇": "",
    }
)


def preprocess(state: AgentState) -> AgentState:
    """Normalise the question so routing sees a predictable string."""
    question = (state.get("question") or "").strip()
    normalized = _WHITESPACE.sub(" ", question).lower().translate(_FOLD)
    return {**state, "question": question, "normalized": normalized}
