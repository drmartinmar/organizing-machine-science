"""Synthetic organizational worlds with known causal structure.

A *world* is a linear structural causal model (SCM) with pairwise interaction
terms, defined over a set of organizational constructs with realistic labels.
Each world ships with:

* a dataset drawn from the SCM (``data.csv``),
* a codebook that the research collective is allowed to see,
* a planted literature of short "prior study" abstracts whose claims are
  TRUE or FALSE in this particular world (computed, not asserted),
* a hidden truth file used only by the scorer.

Templates come in two *variants*: ``orthodox`` (the focal relationship has the
sign the real-world literature expects) and ``contrarian`` (the sign is
reversed by a different mechanism mix).  Contrarian worlds let us measure
*prior conformity*: how often a collective reports the textbook answer rather
than what its own data say.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

EFFECT_THR = 0.10        # |total effect| below this counts as "no effect"
INTER_THR = 0.08         # |total interaction effect| below this counts as "no moderation"
MED_EDGE_THR = 0.10      # both legs of a mediation chain need |coef| >= this
MED_FOCAL_THR = 0.05     # |indirect effect| needed before a mediation counts as a focal truth


@dataclass
class Variable:
    name: str
    label: str
    role: str = "covariate"   # focal_cause | focal_outcome | mediator | moderator | covariate


@dataclass
class Edge:
    cause: str
    effect: str
    coef: float
    focal: bool = False


@dataclass
class Interaction:
    cause: str
    moderator: str
    effect: str
    coef: float
    focal: bool = False


@dataclass
class LitItem:
    """A planted prior-study abstract. ``claim`` uses the claim schema of ``oms.claims``."""
    claim: dict
    design: str
    mechanism: str = ""
    beta: float | None = None


@dataclass
class WorldSpec:
    world_id: str
    template: str
    variant: str
    setting: str
    unit: str
    research_question: str
    variables: list[Variable]
    edges: list[Edge]
    interactions: list[Interaction]
    literature: list[LitItem]
    consensus: list[dict]          # textbook claims about the focal relationship(s)
    trap_pairs: list[tuple[str, str]]  # confounded pairs with zero causal effect
    designated_mediators: list[str]
    n_obs: int = 1200
    noise_sd: float = 1.0
    seed: int = 0

    # ----- helpers -----------------------------------------------------
    @property
    def names(self) -> list[str]:
        return [v.name for v in self.variables]

    def var(self, name: str) -> Variable:
        return next(v for v in self.variables if v.name == name)

    @property
    def focal_cause(self) -> str:
        return next(v.name for v in self.variables if v.role == "focal_cause")

    @property
    def focal_outcome(self) -> str:
        return next(v.name for v in self.variables if v.role == "focal_outcome")

    def to_json(self) -> dict:
        d = asdict(self)
        d["trap_pairs"] = [list(p) for p in self.trap_pairs]
        return d

    @staticmethod
    def from_json(d: dict) -> "WorldSpec":
        d = dict(d)
        d["variables"] = [Variable(**v) for v in d["variables"]]
        d["edges"] = [Edge(**e) for e in d["edges"]]
        d["interactions"] = [Interaction(**i) for i in d["interactions"]]
        d["literature"] = [LitItem(**l) for l in d["literature"]]
        d["trap_pairs"] = [tuple(p) for p in d["trap_pairs"]]
        return WorldSpec(**d)


# ---------------------------------------------------------------------------
# Causal algebra
# ---------------------------------------------------------------------------

def _index(spec: WorldSpec) -> dict[str, int]:
    return {n: i for i, n in enumerate(spec.names)}


def direct_matrix(spec: WorldSpec) -> np.ndarray:
    """B[j, i] = coefficient of i in the structural equation of j."""
    idx = _index(spec)
    k = len(idx)
    B = np.zeros((k, k))
    for e in spec.edges:
        B[idx[e.effect], idx[e.cause]] += e.coef
    return B


def total_effects(spec: WorldSpec) -> np.ndarray:
    """T[j, i] = total (path-summed) linear effect of i on j, evaluated at moderators = 0."""
    B = direct_matrix(spec)
    k = B.shape[0]
    T = np.linalg.inv(np.eye(k) - B) - np.eye(k)
    return T


def total_effect(spec: WorldSpec, cause: str, outcome: str) -> float:
    idx = _index(spec)
    return float(total_effects(spec)[idx[outcome], idx[cause]])


def total_interaction_effect(spec: WorldSpec, cause: str, moderator: str, outcome: str) -> float:
    """Total effect of the (cause x moderator) term on ``outcome``.

    Each interaction term enters some variable E; its influence on the outcome is
    coef * total_effect(E -> outcome), with total_effect(outcome -> outcome) = 1.
    """
    idx = _index(spec)
    T = total_effects(spec)
    out = 0.0
    for it in spec.interactions:
        if {it.cause, it.moderator} == {cause, moderator}:
            path = 1.0 if it.effect == outcome else T[idx[outcome], idx[it.effect]]
            out += it.coef * path
    return float(out)


# ---------------------------------------------------------------------------
# General oracle: deterministic forward simulation under interventions
# ---------------------------------------------------------------------------

def simulate_do(spec: WorldSpec, interventions: dict[str, float]) -> dict[str, float]:
    """Evaluate the structural equations with all noise terms at zero, holding the intervened variables at the
    given values (their incoming edges are cut). Every other variable sits at its structural center (zero)."""
    vals: dict[str, float] = {}
    for name in topological_order(spec):
        if name in interventions:
            vals[name] = float(interventions[name])
            continue
        x = 0.0
        for e in spec.edges:
            if e.effect == name:
                x += e.coef * vals[e.cause]
        for it in spec.interactions:
            if it.effect == name:
                x += it.coef * vals[it.cause] * vals[it.moderator]
        vals[name] = x
    return vals


def do_effect(spec: WorldSpec, cause: str, outcome: str, h: float = 0.01) -> float:
    """Local causal effect of ``cause`` on ``outcome`` at the center of the distribution: the derivative of
    E[outcome | do(cause)] at cause = 0 with every other variable at zero (central difference)."""
    return (simulate_do(spec, {cause: h})[outcome] - simulate_do(spec, {cause: -h})[outcome]) / (2 * h)


def do_interaction(spec: WorldSpec, cause: str, moderator: str, outcome: str, h: float = 0.01) -> float:
    """How the local effect of ``cause`` on ``outcome`` changes per unit of ``moderator``: the mixed second
    derivative of E[outcome | do(cause), do(moderator)] at zero. This captures interactions specified directly,
    interactions propagated through mediators, and interactions inherited from upstream causes."""
    f = lambda a, b: simulate_do(spec, {cause: a, moderator: b})[outcome]
    return (f(h, h) - f(h, -h) - f(-h, h) + f(-h, -h)) / (4 * h * h)


def topological_order(spec: WorldSpec) -> list[str]:
    parents: dict[str, set[str]] = {n: set() for n in spec.names}
    for e in spec.edges:
        parents[e.effect].add(e.cause)
    for it in spec.interactions:
        parents[it.effect].update({it.cause, it.moderator})
    order: list[str] = []
    remaining = set(spec.names)
    while remaining:
        ready = sorted(n for n in remaining if parents[n] <= set(order))
        if not ready:
            raise ValueError("cyclic world specification")
        order.extend(ready)
        remaining -= set(ready)
    return order


def generate_data(spec: WorldSpec) -> pd.DataFrame:
    rng = np.random.default_rng(spec.seed * 7919 + 17)
    n = spec.n_obs
    data: dict[str, np.ndarray] = {}
    for name in topological_order(spec):
        x = rng.normal(0.0, spec.noise_sd, size=n)
        for e in spec.edges:
            if e.effect == name:
                x = x + e.coef * data[e.cause]
        for it in spec.interactions:
            if it.effect == name:
                x = x + it.coef * data[it.cause] * data[it.moderator]
        data[name] = x
    df = pd.DataFrame({n: data[n] for n in spec.names})
    df.insert(0, "unit_id", np.arange(1, n + 1))
    return df.round(4)


# ---------------------------------------------------------------------------
# Truth derivation
# ---------------------------------------------------------------------------

def sign_of(x: float, thr: float) -> str:
    if x >= thr:
        return "positive"
    if x <= -thr:
        return "negative"
    return "none"


def truth_table(spec: WorldSpec) -> dict:
    """All scoreable truths for a world, computed with the intervention oracle.

    ``effects``: every ordered observed pair with the local causal effect (sign at the relevance threshold and the
    raw magnitude). ``moderations``: every unordered pair and outcome whose mixed effect is non-negligible, plus the
    consensus moderation relations (so that textbook claims always have a row). ``mediations``: every direct two-edge
    chain with both legs non-zero (raw magnitudes kept; thresholds applied at scoring time). ``focal``: the truths a
    collective is expected to recover.
    """
    names = spec.names
    effects = []
    for c in names:
        for o in names:
            if c == o:
                continue
            te = do_effect(spec, c, o)
            effects.append({"cause": c, "outcome": o, "sign": sign_of(te, EFFECT_THR), "magnitude": round(te, 4)})
    moderations = []
    consensus_pairs = {(frozenset({cc["cause"], cc["moderator"]}), cc["outcome"]) for cc in spec.consensus if cc.get("type") == "moderation"}
    focal_pairs = {(frozenset({it.cause, it.moderator})) for it in spec.interactions if it.focal}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for o in names:
                if o in (a, b):
                    continue
                v = do_interaction(spec, a, b, o)
                key = (frozenset({a, b}), o)
                if abs(v) >= INTER_THR or key in consensus_pairs or abs(v) > 1e-9:
                    moderations.append({"cause": a, "moderator": b, "outcome": o,
                                        "interaction_sign": sign_of(v, INTER_THR), "magnitude": round(v, 4),
                                        "focal": bool(frozenset({a, b}) in focal_pairs and o == spec.focal_outcome
                                                      and abs(v) >= INTER_THR)})
    mediations = []
    for e1 in spec.edges:
        for e2 in spec.edges:
            if e1.effect == e2.cause and e1.cause != e2.effect and abs(e1.coef) > 1e-9 and abs(e2.coef) > 1e-9:
                strong = abs(e1.coef) >= MED_EDGE_THR and abs(e2.coef) >= MED_EDGE_THR
                mediations.append({
                    "cause": e1.cause, "mediator": e1.effect, "outcome": e2.effect,
                    "indirect_sign": sign_of(e1.coef * e2.coef, 1e-9),
                    "magnitude": round(e1.coef * e2.coef, 4),
                    "legs": [round(e1.coef, 4), round(e2.coef, 4)],
                    "meets_threshold": bool(strong),
                    "focal": bool(e1.cause == spec.focal_cause and e2.effect == spec.focal_outcome
                                   and e1.effect in spec.designated_mediators and strong
                                   and abs(e1.coef * e2.coef) >= MED_FOCAL_THR),
                })
    focal: list[dict] = []
    fc, fo = spec.focal_cause, spec.focal_outcome
    te = do_effect(spec, fc, fo)
    focal.append({"type": "effect", "cause": fc, "outcome": fo, "sign": sign_of(te, EFFECT_THR), "magnitude": round(te, 4)})
    for m in moderations:
        if m["focal"]:
            focal.append({"type": "moderation", **{k: m[k] for k in ("cause", "moderator", "outcome", "interaction_sign", "magnitude")}})
    for m in mediations:
        if m["focal"]:
            focal.append({"type": "mediation", **{k: m[k] for k in ("cause", "mediator", "outcome", "indirect_sign", "magnitude")}})
    for e in spec.edges:
        if e.focal:
            te_e = do_effect(spec, e.cause, e.effect)
            item = {"type": "effect", "cause": e.cause, "outcome": e.effect, "sign": sign_of(te_e, EFFECT_THR), "magnitude": round(te_e, 4)}
            if item not in focal and item["sign"] != "none":
                focal.append(item)
    return {"effects": effects, "moderations": moderations, "mediations": mediations, "focal": focal,
            "trap_pairs": [list(p) for p in spec.trap_pairs], "consensus": spec.consensus,
            "thresholds": {"effect": EFFECT_THR, "interaction": INTER_THR, "mediation_edge": MED_EDGE_THR, "mediation_focal": MED_FOCAL_THR},
            "semantics": "local effects at the center of the distribution (all variables at their structural mean) under do-interventions; "
                         "signs are reported at the relevance thresholds, raw magnitudes are kept"}


# ---------------------------------------------------------------------------
# Literature rendering
# ---------------------------------------------------------------------------

def _interpretation_sentence(c: dict, lab) -> str:
    """The causal proposition the abstract is scored on, stated explicitly in its text."""
    if c["type"] == "effect":
        if c["sign"] == "none":
            return f"The authors conclude that {lab(c['cause'])} has no effect on {lab(c['outcome'])}."
        return (f"The authors interpret this as a causal effect: higher {lab(c['cause'])} "
                f"{'raises' if c['sign'] == 'positive' else 'lowers'} {lab(c['outcome'])}.")
    if c["type"] == "moderation":
        return (f"The authors interpret this as {lab(c['moderator'])} making the effect of {lab(c['cause'])} on "
                f"{lab(c['outcome'])} more {'positive' if c['interaction_sign'] == 'positive' else 'negative'}.")
    return f"The authors interpret {lab(c['mediator'])} as the mechanism through which {lab(c['cause'])} affects {lab(c['outcome'])}."


def _dir_word(sign: str) -> str:
    return {"positive": "higher", "negative": "lower", "none": "no different"}[sign]


def render_literature(spec: WorldSpec, rng: np.random.Generator, causal_language: bool = True) -> list[dict]:
    """Turn LitItems into abstracts with a (hidden) truth status."""
    from .claims import evaluate_claim  # local import to avoid cycle
    truth = truth_table(spec)
    out = []
    for k, item in enumerate(spec.literature, start=1):
        c = item.claim
        lab = lambda v: spec.var(v).label.split(" (")[0].lower()
        beta = item.beta if item.beta is not None else float(rng.uniform(0.14, 0.34))
        if c["type"] == "effect":
            if c["sign"] == "none":
                finding = (f"Units with higher {lab(c['cause'])} showed no significant difference in "
                           f"{lab(c['outcome'])} (standardized b = {rng.uniform(-0.04, 0.04):+.2f}, n.s.).")
            else:
                finding = (f"Higher {lab(c['cause'])} was associated with {_dir_word(c['sign'])} "
                           f"{lab(c['outcome'])} (standardized b = {beta if c['sign']=='positive' else -beta:+.2f}, p < .01).")
        elif c["type"] == "moderation":
            more = "more positive" if c["interaction_sign"] == "positive" else "more negative"
            finding = (f"The association between {lab(c['cause'])} and {lab(c['outcome'])} was {more} "
                       f"when {lab(c['moderator'])} was high (interaction b = "
                       f"{beta if c['interaction_sign']=='positive' else -beta:+.2f}, p < .05).")
        elif c["type"] == "mediation":
            finding = (f"The effect of {lab(c['cause'])} on {lab(c['outcome'])} was statistically mediated by "
                       f"{lab(c['mediator'])} (indirect effect significant at p < .05).")
        else:
            raise ValueError(c["type"])
        text = f"{item.design} {finding}"
        if causal_language:
            text += " " + _interpretation_sentence(c, lab)
        if item.mechanism:
            text += f" {item.mechanism}"
        status = evaluate_claim(c, truth)
        out.append({"id": f"L{k}", "text": text, "claim": c, "truth": status["verdict"], "verdict": status["verdict"],
                    "trap": status.get("trap", False)})
    return out


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, Callable[[str, np.random.Generator], WorldSpec]] = {}


def register(fn):
    TEMPLATES[fn.__name__] = fn
    return fn


def _u(rng, lo, hi):
    return round(float(rng.uniform(lo, hi)), 3)


@register
def turnover(variant: str, rng: np.random.Generator) -> WorldSpec:
    V = [
        Variable("team_turnover", "Share of team members who left and were replaced during the year (standardized index)", "focal_cause"),
        Variable("team_performance", "Supervisor-rated team performance against annual targets (standardized index)", "focal_outcome"),
        Variable("knowledge_loss", "Loss of team-specific procedural knowledge, from quarterly skills audits (standardized index)", "mediator"),
        Variable("idea_novelty", "Novelty of the team's submissions to the firm's improvement program, rated by independent judges (standardized index)", "mediator"),
        Variable("routine_codification", "Degree to which the team's work procedures are documented in written routines (standardized index)", "moderator"),
        Variable("task_interdependence", "Degree to which members' tasks depend on one another's outputs (standardized index)", "moderator"),
        Variable("hiring_quality", "Quality of replacement hires, from structured assessment scores at entry (standardized index)", "moderator"),
        Variable("workload", "Average weekly workload per member relative to the firm norm (standardized index)"),
        Variable("team_size", "Number of team members (standardized index)"),
        Variable("budget_slack", "Unspent discretionary budget available to the team (standardized index)"),
        Variable("training_investment", "Hours of formal training purchased for the team (standardized index)"),
    ]
    common = [
        Edge("hiring_quality", "team_performance", _u(rng, 0.15, 0.25)),
        Edge("workload", "team_performance", -_u(rng, 0.15, 0.25)),
        Edge("budget_slack", "team_performance", _u(rng, 0.25, 0.35)),
        Edge("budget_slack", "training_investment", _u(rng, 0.5, 0.7)),
        Edge("task_interdependence", "team_performance", _u(rng, 0.05, 0.09)),
    ]
    if variant == "orthodox":
        E = common + [
            Edge("team_turnover", "knowledge_loss", _u(rng, 0.5, 0.7), focal=True),
            Edge("knowledge_loss", "team_performance", -_u(rng, 0.4, 0.6), focal=True),
            Edge("team_turnover", "idea_novelty", _u(rng, 0.1, 0.2)),
            Edge("idea_novelty", "team_performance", _u(rng, 0.05, 0.09)),
        ]
        I = [
            Interaction("team_turnover", "routine_codification", "knowledge_loss", -_u(rng, 0.25, 0.35), focal=True),
            Interaction("team_turnover", "task_interdependence", "team_performance", -_u(rng, 0.2, 0.3), focal=True),
        ]
    elif variant == "contrarian":
        E = common + [
            Edge("team_turnover", "knowledge_loss", _u(rng, 0.2, 0.3)),
            Edge("knowledge_loss", "team_performance", -_u(rng, 0.1, 0.15)),
            Edge("team_turnover", "idea_novelty", _u(rng, 0.5, 0.7), focal=True),
            Edge("idea_novelty", "team_performance", _u(rng, 0.4, 0.6), focal=True),
        ]
        I = [
            Interaction("team_turnover", "hiring_quality", "idea_novelty", _u(rng, 0.25, 0.35), focal=True),
            Interaction("team_turnover", "routine_codification", "knowledge_loss", -_u(rng, 0.1, 0.15)),
        ]
    else:
        raise ValueError(variant)
    lit = [
        LitItem({"type": "effect", "cause": "team_turnover", "outcome": "team_performance", "sign": "negative"},
                "Panel of 212 manufacturing teams over four years.",
                "The authors attribute the pattern to the loss of tacit, team-specific knowledge."),
        LitItem({"type": "effect", "cause": "team_turnover", "outcome": "knowledge_loss", "sign": "positive"},
                "Field study of 96 software teams with quarterly skills audits."),
        LitItem({"type": "moderation", "cause": "team_turnover", "outcome": "team_performance",
                 "moderator": "routine_codification", "interaction_sign": "positive"},
                "Survey of 340 service teams in two retail chains.",
                "Documented routines are argued to buffer teams against the disruption of member exit."),
        LitItem({"type": "effect", "cause": "training_investment", "outcome": "team_performance", "sign": "positive"},
                "Cross-sectional study of 1,105 teams in a logistics firm.",
                "The authors recommend expanding formal training budgets."),
        LitItem({"type": "effect", "cause": "workload", "outcome": "team_performance", "sign": "negative"},
                "Two-wave survey of 180 hospital units."),
        LitItem({"type": "effect", "cause": "team_size", "outcome": "team_performance", "sign": "none"},
                "Meta-analytic summary of 41 team studies."),
        LitItem({"type": "effect", "cause": "hiring_quality", "outcome": "team_performance", "sign": "positive"},
                "Archival study of 2,300 hires in a professional services firm."),
    ]
    return WorldSpec(
        world_id="", template="turnover", variant=variant,
        setting="work teams in a large multi-site manufacturing and services firm",
        unit="team-year",
        research_question=("What determines team performance in this firm, and in particular how does team "
                           "turnover affect team performance, through which mechanisms, and under what conditions?"),
        variables=V, edges=E, interactions=I, literature=lit,
        consensus=[{"type": "effect", "cause": "team_turnover", "outcome": "team_performance", "sign": "negative"},
                   {"type": "moderation", "cause": "team_turnover", "outcome": "team_performance",
                    "moderator": "routine_codification", "interaction_sign": "positive"}],
        trap_pairs=[("training_investment", "team_performance")],
        designated_mediators=["knowledge_loss", "idea_novelty"],
    )


@register
def monitoring(variant: str, rng: np.random.Generator) -> WorldSpec:
    V = [
        Variable("monitoring_intensity", "Intensity of electronic performance monitoring of employees in the unit (standardized index)", "focal_cause"),
        Variable("creative_output", "Number and quality of novel solutions and process improvements generated by the unit, judged by an expert panel (standardized index)", "focal_outcome"),
        Variable("routine_output", "Volume of standard tasks completed per employee (standardized index)"),
        Variable("perceived_autonomy", "Employees' reported discretion over how they do their work (standardized index)", "mediator"),
        Variable("trust_in_management", "Employees' reported trust in unit management (standardized index)", "mediator"),
        Variable("feedback_frequency", "Frequency of performance feedback conversations between supervisors and employees (standardized index)", "mediator"),
        Variable("feedback_quality", "Developmental quality of feedback, rated by trained observers (standardized index)", "moderator"),
        Variable("tech_investment", "Unit spending on workplace technology and analytics (standardized index)"),
        Variable("unit_budget", "Total discretionary unit budget (standardized index)"),
        Variable("wellness_program", "Scope of employee wellness programs offered by the unit (standardized index)"),
        Variable("job_tenure", "Average employee tenure in the unit (standardized index)"),
        Variable("manager_span", "Number of direct reports per supervisor (standardized index)"),
    ]
    common = [
        Edge("tech_investment", "monitoring_intensity", _u(rng, 0.5, 0.7)),
        Edge("tech_investment", "creative_output", _u(rng, 0.25, 0.35)),
        Edge("monitoring_intensity", "routine_output", _u(rng, 0.3, 0.5)),
        Edge("unit_budget", "wellness_program", _u(rng, 0.5, 0.7)),
        Edge("unit_budget", "creative_output", _u(rng, 0.25, 0.35)),
        Edge("job_tenure", "creative_output", _u(rng, 0.15, 0.25)),
        Edge("manager_span", "trust_in_management", -_u(rng, 0.1, 0.15)),
    ]
    if variant == "orthodox":
        E = common + [
            Edge("monitoring_intensity", "perceived_autonomy", -_u(rng, 0.5, 0.7), focal=True),
            Edge("perceived_autonomy", "creative_output", _u(rng, 0.4, 0.6), focal=True),
            Edge("monitoring_intensity", "trust_in_management", -_u(rng, 0.3, 0.5), focal=True),
            Edge("trust_in_management", "creative_output", _u(rng, 0.25, 0.35), focal=True),
            Edge("monitoring_intensity", "feedback_frequency", _u(rng, 0.4, 0.6)),
            Edge("feedback_frequency", "creative_output", _u(rng, 0.05, 0.09)),
        ]
        I = [Interaction("monitoring_intensity", "feedback_quality", "creative_output", _u(rng, 0.25, 0.35), focal=True)]
    elif variant == "contrarian":
        E = common + [
            Edge("monitoring_intensity", "perceived_autonomy", -_u(rng, 0.12, 0.18)),
            Edge("perceived_autonomy", "creative_output", _u(rng, 0.12, 0.18)),
            Edge("monitoring_intensity", "trust_in_management", -_u(rng, 0.12, 0.18)),
            Edge("trust_in_management", "creative_output", _u(rng, 0.12, 0.18)),
            Edge("monitoring_intensity", "feedback_frequency", _u(rng, 0.5, 0.7), focal=True),
            Edge("feedback_frequency", "creative_output", _u(rng, 0.4, 0.6), focal=True),
        ]
        I = [Interaction("monitoring_intensity", "feedback_quality", "creative_output", _u(rng, 0.25, 0.35), focal=True)]
    else:
        raise ValueError(variant)
    lit = [
        LitItem({"type": "effect", "cause": "monitoring_intensity", "outcome": "creative_output", "sign": "negative"},
                "Multi-level study of 310 units in a financial services firm.",
                "Monitoring is argued to crowd out intrinsic motivation and exploratory behavior."),
        LitItem({"type": "effect", "cause": "monitoring_intensity", "outcome": "perceived_autonomy", "sign": "negative"},
                "Three-wave survey of 1,480 employees in 120 units."),
        LitItem({"type": "mediation", "cause": "monitoring_intensity", "mediator": "perceived_autonomy", "outcome": "creative_output"},
                "Survey of 204 R&D units with structural equation modeling."),
        LitItem({"type": "effect", "cause": "wellness_program", "outcome": "creative_output", "sign": "positive"},
                "Cross-sectional study of 890 units across 14 firms.",
                "The authors argue that well-being frees cognitive resources for creative work."),
        LitItem({"type": "effect", "cause": "monitoring_intensity", "outcome": "routine_output", "sign": "positive"},
                "Natural experiment around the staggered rollout of a monitoring system in 62 call centers."),
        LitItem({"type": "effect", "cause": "manager_span", "outcome": "creative_output", "sign": "none"},
                "Archival study of 2,100 supervisor-unit observations."),
        LitItem({"type": "effect", "cause": "job_tenure", "outcome": "creative_output", "sign": "positive"},
                "Panel of 150 units over six years."),
    ]
    return WorldSpec(
        world_id="", template="monitoring", variant=variant,
        setting="operating units of a large knowledge-intensive services firm",
        unit="unit-year",
        research_question=("What determines creative output in these units, and in particular how does the intensity of "
                           "electronic performance monitoring affect creative output, through which mechanisms, and under what conditions?"),
        variables=V, edges=E, interactions=I, literature=lit,
        consensus=[{"type": "effect", "cause": "monitoring_intensity", "outcome": "creative_output", "sign": "negative"},
                   {"type": "mediation", "cause": "monitoring_intensity", "mediator": "perceived_autonomy", "outcome": "creative_output"}],
        trap_pairs=[("wellness_program", "creative_output")],
        designated_mediators=["perceived_autonomy", "trust_in_management", "feedback_frequency"],
    )


@register
def decentralization(variant: str, rng: np.random.Generator) -> WorldSpec:
    V = [
        Variable("decision_decentralization", "Share of operating decisions delegated from headquarters to the unit (standardized index)", "focal_cause"),
        Variable("unit_performance", "Unit operating performance relative to plan (standardized index)", "focal_outcome"),
        Variable("environmental_turbulence", "Volatility of demand and competitive conditions in the unit's market (standardized index)", "moderator"),
        Variable("local_knowledge_use", "Extent to which unit decisions draw on local customer and market information, from decision audits (standardized index)", "mediator"),
        Variable("coordination_cost", "Managerial time and rework spent reconciling the unit's decisions with other units (standardized index)", "mediator"),
        Variable("it_integration", "Degree of integration of the unit's information systems with headquarters systems (standardized index)", "moderator"),
        Variable("unit_size", "Number of employees in the unit (standardized index)"),
        Variable("managerial_experience", "Average years of managerial experience in the unit leadership team (standardized index)"),
        Variable("hq_attention", "Attention headquarters devotes to the unit, from meeting and review logs (standardized index)"),
        Variable("formal_planning_hours", "Hours the unit spends on formal strategic planning (standardized index)"),
        Variable("market_concentration", "Concentration of the unit's market (standardized index)"),
    ]
    common = [
        Edge("hq_attention", "decision_decentralization", -_u(rng, 0.4, 0.6)),
        Edge("hq_attention", "unit_performance", _u(rng, 0.2, 0.3)),
        Edge("hq_attention", "formal_planning_hours", _u(rng, 0.5, 0.7)),
        Edge("managerial_experience", "unit_performance", _u(rng, 0.15, 0.25)),
        Edge("unit_size", "coordination_cost", _u(rng, 0.1, 0.15)),
        Edge("market_concentration", "unit_performance", _u(rng, 0.1, 0.2)),
    ]
    if variant == "orthodox":
        E = common + [
            Edge("decision_decentralization", "local_knowledge_use", _u(rng, 0.6, 0.8), focal=True),
            Edge("local_knowledge_use", "unit_performance", _u(rng, 0.4, 0.6), focal=True),
            Edge("decision_decentralization", "coordination_cost", _u(rng, 0.3, 0.5), focal=True),
            Edge("coordination_cost", "unit_performance", -_u(rng, 0.25, 0.35), focal=True),
        ]
        I = [
            Interaction("decision_decentralization", "environmental_turbulence", "unit_performance", _u(rng, 0.3, 0.4), focal=True),
            Interaction("decision_decentralization", "it_integration", "coordination_cost", -_u(rng, 0.3, 0.4), focal=True),
        ]
    elif variant == "contrarian":
        E = common + [
            Edge("decision_decentralization", "local_knowledge_use", _u(rng, 0.25, 0.35)),
            Edge("local_knowledge_use", "unit_performance", _u(rng, 0.25, 0.35)),
            Edge("decision_decentralization", "coordination_cost", _u(rng, 0.6, 0.8), focal=True),
            Edge("coordination_cost", "unit_performance", -_u(rng, 0.4, 0.6), focal=True),
        ]
        I = [
            Interaction("decision_decentralization", "environmental_turbulence", "unit_performance", -_u(rng, 0.25, 0.35), focal=True),
            Interaction("decision_decentralization", "it_integration", "coordination_cost", -_u(rng, 0.3, 0.4), focal=True),
        ]
    else:
        raise ValueError(variant)
    lit = [
        LitItem({"type": "effect", "cause": "decision_decentralization", "outcome": "unit_performance", "sign": "positive"},
                "Panel of 418 business units in 37 multi-unit firms.",
                "Delegation is argued to put decisions where the relevant knowledge sits."),
        LitItem({"type": "moderation", "cause": "decision_decentralization", "outcome": "unit_performance",
                 "moderator": "environmental_turbulence", "interaction_sign": "positive"},
                "Survey of 265 units matched to market volatility data.",
                "Decentralized units are argued to adapt faster when conditions change."),
        LitItem({"type": "effect", "cause": "formal_planning_hours", "outcome": "unit_performance", "sign": "positive"},
                "Cross-sectional study of 720 units.",
                "The authors recommend formal planning routines."),
        LitItem({"type": "effect", "cause": "decision_decentralization", "outcome": "local_knowledge_use", "sign": "positive"},
                "Decision-audit study of 1,900 decisions in 84 units."),
        LitItem({"type": "effect", "cause": "managerial_experience", "outcome": "unit_performance", "sign": "positive"},
                "Archival study of 3,400 unit-years."),
        LitItem({"type": "effect", "cause": "unit_size", "outcome": "unit_performance", "sign": "none"},
                "Meta-analytic summary of 29 studies."),
        LitItem({"type": "effect", "cause": "decision_decentralization", "outcome": "coordination_cost", "sign": "positive"},
                "Time-use study of 140 unit management teams."),
    ]
    return WorldSpec(
        world_id="", template="decentralization", variant=variant,
        setting="operating units of multi-unit firms",
        unit="unit-year",
        research_question=("What determines unit performance in these firms, and in particular how does the decentralization of "
                           "operating decisions affect unit performance, through which mechanisms, and under what conditions?"),
        variables=V, edges=E, interactions=I, literature=lit,
        consensus=[{"type": "effect", "cause": "decision_decentralization", "outcome": "unit_performance", "sign": "positive"},
                   {"type": "moderation", "cause": "decision_decentralization", "outcome": "unit_performance",
                    "moderator": "environmental_turbulence", "interaction_sign": "positive"}],
        trap_pairs=[("formal_planning_hours", "unit_performance")],
        designated_mediators=["local_knowledge_use", "coordination_cost"],
    )


# ---------------------------------------------------------------------------
# Building and saving world bundles
# ---------------------------------------------------------------------------

def build_world(template: str, variant: str, seed: int, n_obs: int = 1200, noise_sd: float = 1.0) -> WorldSpec:
    rng = np.random.default_rng(_stable_seed(template, variant, seed))
    spec = TEMPLATES[template](variant, rng)
    spec.world_id = f"{template}-{variant}-s{seed}"
    spec.seed = seed
    spec.n_obs = n_obs
    spec.noise_sd = noise_sd
    return spec


def _stable_seed(template: str, variant: str, seed: int) -> int:
    import hashlib
    h = hashlib.sha256(f"{template}|{variant}|{seed}".encode()).hexdigest()
    return int(h[:8], 16)


def codebook_markdown(spec: WorldSpec) -> str:
    lines = [f"# Codebook: {spec.world_id}", "",
             f"Setting: {spec.setting}. Unit of observation: {spec.unit}. N = {spec.n_obs}.", "",
             "All variables are standardized indices (mean ~0, SD ~1); higher values mean more of the construct.", "",
             "| variable | description |", "|---|---|"]
    for v in spec.variables:
        lines.append(f"| `{v.name}` | {v.label} |")
    return "\n".join(lines) + "\n"


def brief_markdown(spec: WorldSpec, literature: list[dict], identification_note: bool = True) -> str:
    lines = [f"# Research brief", "",
             f"**Setting.** {spec.setting.capitalize()}.", "",
             f"**Research question.** {spec.research_question}", "",
             f"**Data.** `data.csv` with N = {spec.n_obs} observations at the {spec.unit} level. See the codebook for variables.", "",
             "**Prior literature available to the team** (summaries of earlier studies in comparable settings; cite them by ID):", ""]
    for l in literature:
        lines.append(f"- **[{l['id']}]** {l['text']}")
    if identification_note:
        lines += ["", "**What may be assumed about the data.** Causes precede their effects within the observation window; every "
                  "common cause of any two variables in the codebook is itself in the codebook; relations are approximately "
                  "linear with possible pairwise interactions. Under these assumptions a regression adjusted for the relevant "
                  "codebook variables identifies the causal effect, and a mediator must not be held constant when a total effect "
                  "is the target. Report an effect only if its standardized magnitude is practically meaningful (about 0.1 or "
                  "more), moderation only if the slope changes by about 0.08 or more per unit of the moderator, and a mechanism "
                  "only if both of its links are meaningful."]
    lines += ["", "**Deliverable.** A set of causal claims about what determines the focal outcome, each stated with the exact "
              "variable names in the codebook, a calibrated confidence in [0, 1], and its evidential basis (data analysis, "
              "literature IDs, or both). Claims may assert positive, negative or no effects, moderation (whether the "
              "effect of a cause on an outcome becomes more positive or more negative as a moderator increases), or "
              "mediation (a cause acting on an outcome through a mediator)."]
    return "\n".join(lines) + "\n"


def save_world(spec: WorldSpec, root: Path, world_format: int = 2) -> Path:
    out = root / spec.world_id
    out.mkdir(parents=True, exist_ok=True)
    df = generate_data(spec)
    df.to_csv(out / "data.csv", index=False)
    rng = np.random.default_rng(_stable_seed(spec.template, spec.variant, spec.seed) + 1)
    lit = render_literature(spec, rng, causal_language=(world_format >= 2))
    spec_json = spec.to_json()
    spec_json["world_format"] = world_format   # 1 = pilot worlds (associational abstracts, no identification note)
    (out / "spec.json").write_text(json.dumps(spec_json, indent=2))
    (out / "truth.json").write_text(json.dumps(truth_table(spec), indent=2))
    (out / "literature.json").write_text(json.dumps(lit, indent=2))
    (out / "codebook.md").write_text(codebook_markdown(spec))
    (out / "brief.md").write_text(brief_markdown(spec, lit, identification_note=(world_format >= 2)))
    public_lit = [{"id": l["id"], "text": l["text"]} for l in lit]
    (out / "literature_public.json").write_text(json.dumps(public_lit, indent=2))
    return out


def load_world(path: Path) -> dict:
    path = Path(path)
    raw = json.loads((path / "spec.json").read_text())
    world_format = raw.pop("world_format", 1)
    spec = WorldSpec.from_json(raw)
    return {
        "spec": spec,
        "world_format": world_format,
        "path": path,
        "truth": json.loads((path / "truth.json").read_text()),
        "literature": json.loads((path / "literature.json").read_text()),
        "codebook": (path / "codebook.md").read_text(),
        "brief": (path / "brief.md").read_text(),
    }
