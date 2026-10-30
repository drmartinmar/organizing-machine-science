import json
from pathlib import Path

import numpy as np
import pytest

from oms.worlds import (WorldSpec, Variable, Edge, Interaction, build_world, truth_table, do_effect, do_interaction,
                        total_effect, total_interaction_effect, save_world, load_world, TEMPLATES)
from oms.claims import normalize_claim, evaluate_claim
from oms.collective import OrgDesign, run_collective
from oms.llm import MockBackend
from oms.scoring import score


def _toy(gamma=0.3, a=0.6, b=0.5):
    V = [Variable("X", "x", "focal_cause"), Variable("M", "m", "mediator"), Variable("Z", "z", "moderator"),
         Variable("Y", "y", "focal_outcome")]
    E = [Edge("X", "M", a, focal=True), Edge("M", "Y", b, focal=True)]
    I = [Interaction("M", "Z", "Y", gamma, focal=True)]
    return WorldSpec(world_id="toy", template="toy", variant="orthodox", setting="toy", unit="u", research_question="q",
                     variables=V, edges=E, interactions=I, literature=[], consensus=[], trap_pairs=[],
                     designated_mediators=["M"], n_obs=100)


def test_oracle_recovers_inherited_moderation():
    """M = aX, Y = bM + gamma*M*Z: the effect of X on Y is ab and is moderated by Z with coefficient a*gamma,
    although no X x Z interaction is specified directly (the reviewer's example)."""
    spec = _toy()
    assert do_effect(spec, "X", "Y") == pytest.approx(0.6 * 0.5, abs=1e-6)
    assert do_interaction(spec, "X", "Z", "Y") == pytest.approx(0.6 * 0.3, abs=1e-6)
    assert do_interaction(spec, "M", "Z", "Y") == pytest.approx(0.3, abs=1e-6)
    # the old matrix formula misses the inherited interaction
    assert total_interaction_effect(spec, "X", "Z", "Y") == 0.0
    tt = truth_table(spec)
    row = next(m for m in tt["moderations"] if {m["cause"], m["moderator"]} == {"X", "Z"} and m["outcome"] == "Y")
    assert row["interaction_sign"] == "positive"


@pytest.mark.parametrize("template", list(TEMPLATES))
def test_oracle_agrees_with_matrix_formula_on_direct_paths(template):
    spec = build_world(template, "orthodox", seed=2)
    for c in spec.names:
        for o in spec.names:
            if c != o:
                assert do_effect(spec, c, o) == pytest.approx(total_effect(spec, c, o), abs=1e-6)
    for it in spec.interactions:   # directly specified interactions propagate identically under both formulas
        assert do_interaction(spec, it.cause, it.moderator, spec.focal_outcome) == pytest.approx(
            total_interaction_effect(spec, it.cause, it.moderator, spec.focal_outcome), abs=1e-6)


def test_weak_verdict_for_subthreshold_effects():
    spec = _toy(gamma=0.02, a=0.6, b=0.05)      # X->Y = 0.03 (below 0.10), chain legs 0.6 and 0.05
    tt = truth_table(spec)
    names = spec.names
    c = normalize_claim({"type": "effect", "cause": "X", "outcome": "Y", "sign": "positive"}, names)
    assert evaluate_claim(c, tt)["verdict"] == "WEAK"
    c2 = normalize_claim({"type": "effect", "cause": "X", "outcome": "Y", "sign": "negative"}, names)
    assert evaluate_claim(c2, tt)["verdict"] == "FALSE"
    c3 = normalize_claim({"type": "effect", "cause": "X", "outcome": "Y", "sign": "none"}, names)
    assert evaluate_claim(c3, tt)["verdict"] == "TRUE"
    med = normalize_claim({"type": "mediation", "cause": "X", "mediator": "M", "outcome": "Y"}, names)
    assert evaluate_claim(med, tt)["verdict"] == "WEAK"
    absent = normalize_claim({"type": "mediation", "cause": "X", "mediator": "Z", "outcome": "Y"}, names)
    assert evaluate_claim(absent, tt)["verdict"] == "FALSE"


def test_conformity_counts_only_false_textbook_claims(tmp_path):
    spec = build_world("monitoring", "contrarian", seed=1)
    world = load_world(save_world(spec, tmp_path))
    names = spec.names
    # textbook main effect is false here; the textbook mediation through autonomy holds (weakly or fully)
    claims = [normalize_claim({"type": "effect", "cause": "monitoring_intensity", "outcome": "creative_output", "sign": "negative",
                               "confidence": 0.8}, names)]
    m, _ = score(claims, world)
    assert m["n_false_consensus_available"] >= 1 and m["consensus_conformity"] == 1.0 / m["n_false_consensus_available"]
    claims2 = [normalize_claim({"type": "effect", "cause": "monitoring_intensity", "outcome": "creative_output", "sign": "positive",
                                "confidence": 0.8}, names)]
    m2, _ = score(claims2, world)
    assert m2["consensus_conformity"] == 0.0 and m2["n_textbook_assertions"] == 0


def test_and_or_governance_on_mock(tmp_path):
    spec = build_world("turnover", "orthodox", seed=1, n_obs=300)
    world = load_world(save_world(spec, tmp_path))
    res_and = run_collective(OrgDesign(name="pipeline_and", structure="pipeline", evaluation="and"), world, MockBackend(), sandbox_dir=tmp_path)
    res_or = run_collective(OrgDesign(name="pipeline_or", structure="pipeline", evaluation="or"), world, MockBackend(), sandbox_dir=tmp_path)
    assert res_and.error is None and res_or.error is None
    # the mock critic rejects every third claim: AND keeps only accepted ones, OR keeps at least the lead's set
    assert len(res_and.final_claims) <= len(res_and.draft_claims)
    assert len(res_or.final_claims) >= len(res_and.final_claims)
    assert res_and.n_raw_claims >= len(res_and.final_claims)


def test_world_format_versions(tmp_path):
    spec = build_world("turnover", "orthodox", seed=1, n_obs=200)
    w2 = load_world(save_world(spec, tmp_path / "v2", world_format=2))
    w1 = load_world(save_world(spec, tmp_path / "v1", world_format=1))
    assert w2["world_format"] == 2 and w1["world_format"] == 1
    assert "What may be assumed about the data" in w2["brief"] and "What may be assumed" not in w1["brief"]
    assert "The authors interpret" in w2["literature"][0]["text"] and "The authors interpret" not in w1["literature"][0]["text"]
    assert w1["truth"] == w2["truth"]
