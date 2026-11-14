"""Compliance gate: the league's prohibited wager classes, as executable code.

This is the only module in the repository that can veto a bet for a reason other than
statistics, and it fails closed: an unrecognised market is held for human review rather
than assumed permissible. The classes and their examples are the league's own published
categories (see data/sources.json SRC-007, SRC-008); the keyword lists are our
approximation of them and are therefore a floor, not a ceiling.

The distinction that matters, and that this module deliberately does not police: using
injury information as an *input* to a permitted market (a game total, a spread) is
analysis; a market whose *subject* is an injury is a wager class the league asks
operators not to offer. We test the subject of the offer, never the provenance of the
feature, because a feature-level ban would ban the entire injury requirement of the brief.
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

# ---------------------------------------------------------------------------
# the four prohibited classes, as the league states them
# ---------------------------------------------------------------------------

PROHIBITED_CLASSES: dict[str, dict] = {
    "INJURY_OR_HEALTH": {
        "league_description": "Inherently Objectionable: markets based on subject matter against public "
                              "policy, the league's own examples including player injuries, fan safety and misconduct.",
        "patterns": [
            r"injur", r"concussion", r"\bprotocol\b", r"placed on (?:the )?ir\b", r"injured reserve",
            r"designated to return", r"will .{0,24}(?:be|go) (?:out|down|inactive)\b", r"illness",
            r"medical", r"hospitali",
        ],
    },
    "OFFICIATING": {
        "league_description": "Officiating-Related: markets or bets based on officials or officiating, "
                              "including assignments, penalties and replays.",
        "patterns": [
            r"referee", r"official(?:s|ing)?\b", r"\bflag(?:s|ged)?\b", r"penalt", r"replay",
            r"\bchallenge(?:s|d)?\b", r"ejection", r"coin toss", r"booth", r"crew chief",
        ],
    },
    "ONE_PERSON_ONE_PLAY": {
        "league_description": "Determinable by One Person in One Play: outcomes 100% determinable by a "
                              "single person in a single play, e.g. a kicker missing a field goal or a "
                              "quarterback's first pass being incomplete.",
        "patterns": [
            r"first pass (?:to be|is) (?:in)?complete",
            r"miss(?:es|ed|ing)?\b[^.]{0,30}\bfield goal", r"field goal\b[^.]{0,30}\bmiss",
            r"(?:game[- ]winning|last[- ]second) (?:kick|field goal|extra point)",
            r"kicker[^.]{0,30}(?:miss|shake|slip)", r"\bextra point\b[^.]{0,20}\b(miss|good)\b",
            r"first play from scrimmage", r"\bcoin\b", r"(?:will|would) .{0,20}audible",
            r"\bpunt (?:on )?(?:fourth|4th) down\b",
        ],
    },
    "PRE_DETERMINED": {
        "league_description": "Pre-Determined: outcomes directly related to on-field competition that are "
                              "settled before the play, e.g. whether a quarterback starts, or whether a "
                              "team's first play from scrimmage is a run or a pass.",
        "patterns": [
            r"will .{0,24}start\b", r"\bstart(?:s|ing)? this week\b", r"to be named starter",
            r"depth chart (?:to|will)", r"first play (?:of|from) (?:the )?(?:game|scrimmage)",
            r"(?:run|pass) ?first\b", r"coin toss call", r"captain(s)? to (?:win|lose) toss",
            r"anthem|national anthem", r"toss the coin",
        ],
    },
}

# A market whose subject is a player's participation is one of the classes above in
# almost every real case; this is the belt-and-braces check on naming tricks.
_SEMANTIC_GUARDS = [
    (r"\b(?:active|inactive)\b.*\blist\b", "pre-determined roster decision presented as a market"),
    (r"\b(?:out|doubtful|questionable)\b.*\b(?:yes|no)\b", "designation-as-market"),
]

_SAFE_MARKET_FAMILIES = [
    "game spread", "team spread", "game total", "team total", "money line", "moneyline",
    "first half spread", "first half total", "quarter spread", "quarter total",
    "passing yards", "pass attempts", "rushing yards", "rush attempts", "receptions",
    "receiving yards", "receiving touchdowns", "tackles", "sacks", "sack",
    "interceptions thrown", "points scored", "team to score first", "win margin",
    "touchdowns scored", "longest completion", "completions", "fantasy points",
]

_MATCH = [(cls, re.compile(p, re.I)) for cls, d in PROHIBITED_CLASSES.items() for p in d["patterns"]]
_GUARDS = [(re.compile(p, re.I), why) for p, why in _SEMANTIC_GUARDS]


def classify_market(name: str, family: str | None = None) -> dict:
    """Decide whether an offer may be considered at all.

    Returns {"decision": ALLOW|PROHIBIT|HOLD, "classes": [...], "reasons": [...],
    "recognised_family": bool}. PROHIBIT is definitive; HOLD means we did not
    recognise the market and no bet may be emitted without a human reading its rules.
    """
    text = f"{name or ''} {family or ''}"
    hits: list[str] = []
    reasons: list[str] = []
    for cls, rx in _MATCH:
        if rx.search(text):
            if cls not in hits:
                hits.append(cls)
            reasons.append(f"{cls}: matched /{rx.pattern}/ in market text")
    for rx, why in _GUARDS:
        if rx.search(text):
            reasons.append(f"semantic guard: {why}")
            if "PRE_DETERMINED" not in hits:
                hits.append("PRE_DETERMINED")
    recognised = family is not None and family.lower() in _SAFE_MARKET_FAMILIES
    if hits:
        return {"decision": "PROHIBIT", "classes": hits, "reasons": reasons,
                "recognised_family": recognised}
    if not recognised:
        return {"decision": "HOLD", "classes": [], "reasons": reasons + [
            "market family not on the recognised list; default posture is to hold, not to allow"],
            "recognised_family": False}
    return {"decision": "ALLOW", "classes": [], "reasons": reasons, "recognised_family": True}


def check_bet(bet: dict) -> dict:
    """Gate one bet object. Expects keys 'market' (name) and optionally 'family'.

    Anything carrying a 'non_public' or 'insider' flag is refused outright regardless
    of the market, because the prohibited conduct is the information, not the offer.
    """
    if bet.get("non_public") or bet.get("insider_source"):
        return {"decision": "PROHIBIT", "classes": ["NON_PUBLIC_INFORMATION"],
                "reasons": ["the league's gambling policy prohibits sharing and using inside "
                            "information such as unannounced injuries or lineup changes"],
                "recognised_family": False}
    res = classify_market(bet.get("market", ""), bet.get("family"))
    return res


def filter_offers(offers: Iterable[dict]) -> tuple[list[dict], list[dict]]:
    """Split a slate into (permitted, refused). Refused rows keep the reason attached."""
    allowed, refused = [], []
    for o in offers:
        d = check_bet(o)
        if d["decision"] == "ALLOW":
            allowed.append(o)
        else:
            refused.append({**o, "refusal": d})
    return allowed, refused


def check_provenance(source_ids: Sequence[str], allowlist: Iterable[str]) -> dict:
    """Every input must be in the registered allowlist; unregistered input fails closed."""
    allow = set(allowlist)
    unknown = sorted({s for s in source_ids if s not in allow})
    return {"ok": not unknown, "unknown_sources": unknown,
            "note": "an input with no registered source is indistinguishable from a rumour"}
