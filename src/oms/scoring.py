"""Exact scoring of a collective's final claims against the world's truth.

Metrics (per run):

* ``n_claims``, ``precision`` (share of claims TRUE), ``n_false`` (Type I errors)
* ``focal_recall`` (share of focal truths recovered), ``n_focal_missed`` (Type II errors)
* ``discovery_rate``: share of *unpublished* focal truths recovered (novelty beyond the planted literature)
* ``parroting_rate``: share of claims that restate a planted abstract (true or false)
* ``consensus_conformity``: among claims about the textbook relations, share that assert the textbook answer
  (in contrarian worlds this is the prior-conformity error)
* ``trap_rate``: share of claims asserting a confounded (zero-effect) relation
* ``confident_false_rate`` ("Potemkin rate"): share of claims that are FALSE with confidence >= 0.7
* ``brier``: mean squared error of stated confidence against truth; ``overconfidence`` = mean confidence - precision
* ``citation_errors``: literature IDs cited that do not exist or share fewer than two variables with the claim
"""
from __future__ import annotations

from .claims import evaluate_claim, same_claim, same_relation

CONFIDENT = 0.7


def annotate(claims: list[dict], world: dict) -> list[dict]:
    truth = world["truth"]
    lit = world["literature"]
    out = []
    for c in claims:
        ev = evaluate_claim(c, truth)
        a = dict(c)
        a["verdict"] = ev["verdict"]
        a["truth_value"] = ev.get("truth_value")
        a["is_trap"] = bool(ev.get("trap"))
        a["is_consensus"] = bool(ev.get("consensus"))
        a["about_consensus_relation"] = any(same_relation(c, cc) for cc in truth.get("consensus", []))
        a["parrots"] = any(same_claim(c, l["claim"]) for l in lit)
        cites = [b.split(":", 1)[1].strip() for b in c.get("basis", []) if b.lower().startswith("literature:")]
        errs = 0
        for cid in cites:
            l = next((x for x in lit if x["id"] == cid), None)
            if l is None or not _relevant_citation(c, l["claim"]):
                errs += 1
        a["citation_errors"] = errs
        out.append(a)
    return out


def _vars(c: dict) -> set:
    return {v for v in (c.get("cause"), c.get("outcome"), c.get("moderator"), c.get("mediator")) if v}


def _relevant_citation(claim: dict, abstract_claim: dict) -> bool:
    """An abstract supports a claim if it concerns the same relation or shares at least two of its variables
    (e.g., citing the main-effect abstract for a mediation claim about the same cause and outcome is fine)."""
    return same_relation(claim, abstract_claim) or len(_vars(claim) & _vars(abstract_claim)) >= 2


def score(claims: list[dict], world: dict) -> dict:
    truth = world["truth"]
    lit = world["literature"]
    ann = annotate(claims, world)
    n = len(ann)
    n_true = sum(1 for a in ann if a["verdict"] == "TRUE")
    focal = truth["focal"]
    focal_claims = [_as_claim(f) for f in focal]
    published = [f for f in focal_claims if any(same_claim(f, l["claim"]) for l in lit)]
    unpublished = [f for f in focal_claims if f not in published]

    def recovered(f):
        return any(a["verdict"] == "TRUE" and same_claim(a, f) for a in ann)

    n_focal_rec = sum(1 for f in focal_claims if recovered(f))
    n_unpub_rec = sum(1 for f in unpublished if recovered(f))
    cons_claims = [a for a in ann if a["about_consensus_relation"]]
    confs = [a["confidence"] for a in ann]
    brier = (sum((a["confidence"] - (1.0 if a["verdict"] == "TRUE" else 0.0)) ** 2 for a in ann) / n) if n else None
    return {
        "n_claims": n,
        "n_true": n_true,
        "n_false": n - n_true,
        "precision": (n_true / n) if n else None,
        "n_focal": len(focal_claims),
        "focal_recall": (n_focal_rec / len(focal_claims)) if focal_claims else None,
        "n_focal_missed": len(focal_claims) - n_focal_rec,
        "n_unpublished_focal": len(unpublished),
        "discovery_rate": (n_unpub_rec / len(unpublished)) if unpublished else None,
        "parroting_rate": (sum(1 for a in ann if a["parrots"]) / n) if n else None,
        "consensus_conformity": (sum(1 for a in cons_claims if a["is_consensus"]) / len(cons_claims)) if cons_claims else None,
        "n_consensus_relation_claims": len(cons_claims),
        "trap_rate": (sum(1 for a in ann if a["is_trap"]) / n) if n else None,
        "confident_false_rate": (sum(1 for a in ann if a["verdict"] == "FALSE" and a["confidence"] >= CONFIDENT) / n) if n else None,
        "n_confident_false": sum(1 for a in ann if a["verdict"] == "FALSE" and a["confidence"] >= CONFIDENT),
        "mean_confidence": (sum(confs) / n) if n else None,
        "brier": brier,
        "overconfidence": ((sum(confs) / n) - (n_true / n)) if n else None,
        "citation_errors": sum(a["citation_errors"] for a in ann),
        "f1_focal": _f1(n_true, n, n_focal_rec, len(focal_claims)),
    }, ann


def _f1(n_true, n, n_focal_rec, n_focal):
    if not n or not n_focal:
        return None
    p = n_true / n
    r = n_focal_rec / n_focal
    return (2 * p * r / (p + r)) if (p + r) else 0.0


def _as_claim(f: dict) -> dict:
    c = {"type": f["type"], "cause": f["cause"], "outcome": f["outcome"], "sign": None, "moderator": None,
         "interaction_sign": None, "mediator": None, "indirect_sign": None}
    if f["type"] == "effect":
        c["sign"] = f["sign"]
    elif f["type"] == "moderation":
        c["moderator"], c["interaction_sign"] = f["moderator"], f["interaction_sign"]
    else:
        c["mediator"], c["indirect_sign"] = f["mediator"], f.get("indirect_sign")
    return c
