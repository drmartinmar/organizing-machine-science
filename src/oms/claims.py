"""Claim schema and exact evaluation of claims against a world's truth table.

A claim is a dict with these fields (unused fields may be ``None``):

* ``type``: ``effect`` | ``moderation`` | ``mediation``
* ``cause``, ``outcome``: variable names
* ``sign`` (effect): ``positive`` | ``negative`` | ``none``
* ``moderator``, ``interaction_sign`` (moderation): the slope of ``cause`` on
  ``outcome`` becomes more ``positive`` / more ``negative`` as the moderator
  increases; ``none`` asserts no moderation
* ``mediator``, ``indirect_sign`` (mediation; ``indirect_sign`` optional)
* ``confidence``: float in [0, 1]
* ``basis``: list such as ``["data", "literature:L3"]``
* ``rationale``: free text

Evaluation returns a verdict ``TRUE`` or ``FALSE`` and annotations used by the
scorer (whether the claim restates a planted abstract, matches the textbook
consensus, or falls on a confounded trap pair).
"""
from __future__ import annotations

from typing import Any

SIGNS = ("positive", "negative", "none")


def claim_schema(variable_names: list[str], max_claims: int = 12) -> dict:
    """JSON schema for a structured final report; variable names are enumerated."""
    var = {"type": "string", "enum": list(variable_names)}
    var_or_null = {"anyOf": [{"type": "string", "enum": list(variable_names)}, {"type": "null"}]}
    claim = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "type": {"type": "string", "enum": ["effect", "moderation", "mediation"]},
            "cause": var,
            "outcome": var,
            "sign": {"anyOf": [{"type": "string", "enum": list(SIGNS)}, {"type": "null"}]},
            "moderator": var_or_null,
            "interaction_sign": {"anyOf": [{"type": "string", "enum": list(SIGNS)}, {"type": "null"}]},
            "mediator": var_or_null,
            "indirect_sign": {"anyOf": [{"type": "string", "enum": list(SIGNS)}, {"type": "null"}]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "basis": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
        },
        "required": ["id", "type", "cause", "outcome", "sign", "moderator", "interaction_sign",
                     "mediator", "indirect_sign", "confidence", "basis", "rationale"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "theory_summary": {"type": "string"},
            "claims": {"type": "array", "items": claim, "maxItems": max_claims},
            "limitations": {"type": "string"},
        },
        "required": ["theory_summary", "claims", "limitations"],
    }


def normalize_claim(c: dict, variable_names: list[str]) -> dict | None:
    """Coerce a raw claim dict into canonical form; return None if unusable."""
    if not isinstance(c, dict):
        return None
    t = str(c.get("type", "")).lower().strip()
    if t not in ("effect", "moderation", "mediation"):
        return None
    cause, outcome = c.get("cause"), c.get("outcome")
    if cause not in variable_names or outcome not in variable_names or cause == outcome:
        return None
    out: dict[str, Any] = {
        "id": str(c.get("id", "")),
        "type": t, "cause": cause, "outcome": outcome,
        "sign": None, "moderator": None, "interaction_sign": None, "mediator": None, "indirect_sign": None,
        "confidence": _clip(c.get("confidence", 0.5)),
        "basis": [str(b) for b in (c.get("basis") or [])],
        "rationale": str(c.get("rationale", ""))[:1000],
    }
    if t == "effect":
        s = _sign(c.get("sign"))
        if s is None:
            return None
        out["sign"] = s
    elif t == "moderation":
        m = c.get("moderator")
        s = _sign(c.get("interaction_sign"))
        if m not in variable_names or m in (cause, outcome) or s is None:
            return None
        out["moderator"], out["interaction_sign"] = m, s
    else:
        m = c.get("mediator")
        if m not in variable_names or m in (cause, outcome):
            return None
        out["mediator"] = m
        out["indirect_sign"] = _sign(c.get("indirect_sign")) if c.get("indirect_sign") else None
    return out


def _clip(x) -> float:
    try:
        return float(min(1.0, max(0.0, float(x))))
    except (TypeError, ValueError):
        return 0.5


def _sign(s) -> str | None:
    if s is None:
        return None
    s = str(s).lower().strip()
    aliases = {"+": "positive", "pos": "positive", "positive": "positive", "increase": "positive",
               "-": "negative", "neg": "negative", "negative": "negative", "decrease": "negative",
               "none": "none", "null": "none", "zero": "none", "no effect": "none", "0": "none"}
    return aliases.get(s)


def same_relation(a: dict, b: dict) -> bool:
    """True if two claims are about the same relation (ignoring asserted signs)."""
    if a["type"] != b["type"] or a["cause"] != b["cause"] or a["outcome"] != b["outcome"]:
        return False
    if a["type"] == "moderation":
        return a.get("moderator") == b.get("moderator")
    if a["type"] == "mediation":
        return a.get("mediator") == b.get("mediator")
    return True


def same_claim(a: dict, b: dict) -> bool:
    if not same_relation(a, b):
        return False
    if a["type"] == "effect":
        return a.get("sign") == b.get("sign")
    if a["type"] == "moderation":
        return a.get("interaction_sign") == b.get("interaction_sign")
    return True


def evaluate_claim(claim: dict, truth: dict) -> dict:
    """Evaluate a canonical claim against ``truth_table`` output.

    Verdicts: ``TRUE`` (asserted sign matches the truth at the relevance threshold), ``WEAK`` (the asserted
    direction matches a structurally present effect that is below the relevance threshold), ``FALSE`` (wrong
    direction, asserted absence of a present effect, or asserted presence of a structurally absent relation).
    """
    t = claim["type"]
    res: dict[str, Any] = {"verdict": "FALSE", "truth_value": None, "magnitude": None}
    if t == "effect":
        row = next((e for e in truth["effects"] if e["cause"] == claim["cause"] and e["outcome"] == claim["outcome"]), None)
        if row is None:
            return res
        res["truth_value"], res["magnitude"] = row["sign"], row["magnitude"]
        res["verdict"] = _verdict(claim["sign"], row["sign"], row["magnitude"])
    elif t == "moderation":
        row = next((m for m in truth["moderations"] if {m["cause"], m["moderator"]} == {claim["cause"], claim["moderator"]}
                    and m["outcome"] == claim["outcome"]), None)
        tv = row["interaction_sign"] if row else "none"
        mag = row["magnitude"] if row else 0.0
        res["truth_value"], res["magnitude"] = tv, mag
        res["verdict"] = _verdict(claim["interaction_sign"], tv, mag)
    elif t == "mediation":
        row = next((m for m in truth["mediations"] if m["cause"] == claim["cause"] and m["mediator"] == claim["mediator"]
                    and m["outcome"] == claim["outcome"]), None)
        if row is None:
            res["truth_value"] = "none"
            res["verdict"] = "FALSE"
        else:
            res["truth_value"], res["magnitude"] = row["indirect_sign"], row["magnitude"]
            sign_ok = claim.get("indirect_sign") in (None, row["indirect_sign"])
            if not sign_ok:
                res["verdict"] = "FALSE"
            elif row.get("meets_threshold", True):
                res["verdict"] = "TRUE"
            else:
                res["verdict"] = "WEAK"
    res["trap"] = t == "effect" and [claim["cause"], claim["outcome"]] in truth.get("trap_pairs", []) and claim["sign"] != "none"
    res["consensus"] = any(same_claim(claim, c) for c in truth.get("consensus", []))
    return res


def _verdict(asserted: str, truth_sign: str, magnitude: float) -> str:
    if asserted == truth_sign:
        return "TRUE"
    if asserted != "none" and truth_sign == "none" and magnitude is not None and abs(magnitude) > 1e-9:
        raw_sign = "positive" if magnitude > 0 else "negative"
        if raw_sign == asserted:
            return "WEAK"
    return "FALSE"
