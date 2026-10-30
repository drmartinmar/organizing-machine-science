import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from oms.worlds import (TEMPLATES, build_world, generate_data, truth_table, total_effect, save_world, load_world,
                        EFFECT_THR)
from oms.claims import normalize_claim, evaluate_claim, claim_schema
from oms.scoring import score
from oms.sandbox import run_analysis


@pytest.mark.parametrize("template", list(TEMPLATES))
@pytest.mark.parametrize("variant", ["orthodox", "contrarian"])
def test_world_is_acyclic_and_focal_sign_matches_variant(template, variant):
    spec = build_world(template, variant, seed=1)
    df = generate_data(spec)
    assert len(df) == spec.n_obs and not df.isna().any().any()
    te = total_effect(spec, spec.focal_cause, spec.focal_outcome)
    assert abs(te) >= EFFECT_THR
    consensus_sign = spec.consensus[0]["sign"]
    truth_sign = "positive" if te > 0 else "negative"
    if variant == "orthodox":
        assert truth_sign == consensus_sign
    else:
        assert truth_sign != consensus_sign


def test_data_recovers_structural_coefficients():
    """OLS on the generated data should recover a known direct edge within sampling error."""
    import statsmodels.formula.api as smf
    spec = build_world("turnover", "orthodox", seed=3, n_obs=5000)
    df = generate_data(spec)
    edge = next(e for e in spec.edges if e.cause == "team_turnover" and e.effect == "knowledge_loss")
    m = smf.ols("knowledge_loss ~ team_turnover + routine_codification + team_turnover:routine_codification", data=df).fit()
    assert abs(m.params["team_turnover"] - edge.coef) < 0.08


def test_literature_truth_flips_in_contrarian_world(tmp_path):
    for variant, expected in (("orthodox", "TRUE"), ("contrarian", "FALSE")):
        spec = build_world("monitoring", variant, seed=1)
        out = save_world(spec, tmp_path)
        lit = json.loads((out / "literature.json").read_text())
        assert lit[0]["truth"] == expected          # L1 is the textbook claim
        trap = [l for l in lit if l["trap"]]
        assert trap and all(l["truth"] == "FALSE" for l in trap)
        public = json.loads((out / "literature_public.json").read_text())
        assert "truth" not in public[0] and "claim" not in public[0]


def test_claim_normalization_and_evaluation():
    spec = build_world("turnover", "orthodox", seed=1)
    truth = truth_table(spec)
    names = spec.names
    good = normalize_claim({"type": "effect", "cause": "team_turnover", "outcome": "team_performance", "sign": "-",
                            "confidence": 1.3, "basis": ["data"]}, names)
    assert good["sign"] == "negative" and good["confidence"] == 1.0
    assert evaluate_claim(good, truth)["verdict"] == "TRUE"
    wrong = dict(good, sign="positive")
    assert evaluate_claim(wrong, truth)["verdict"] == "FALSE"
    assert normalize_claim({"type": "effect", "cause": "nonexistent", "outcome": "team_performance", "sign": "+"}, names) is None
    mod = normalize_claim({"type": "moderation", "cause": "team_turnover", "outcome": "team_performance",
                           "moderator": "task_interdependence", "interaction_sign": "negative"}, names)
    assert evaluate_claim(mod, truth)["verdict"] == "TRUE"
    trap = normalize_claim({"type": "effect", "cause": "training_investment", "outcome": "team_performance", "sign": "positive"}, names)
    ev = evaluate_claim(trap, truth)
    assert ev["verdict"] == "FALSE" and ev["trap"] is True


def test_scoring_metrics(tmp_path):
    spec = build_world("turnover", "contrarian", seed=1)
    out = save_world(spec, tmp_path)
    world = load_world(out)
    names = spec.names
    claims = [
        normalize_claim({"id": "C1", "type": "effect", "cause": "team_turnover", "outcome": "team_performance", "sign": "negative",
                         "confidence": 0.9, "basis": ["literature:L1"]}, names),           # textbook, FALSE here, confident
        normalize_claim({"id": "C2", "type": "effect", "cause": "team_turnover", "outcome": "idea_novelty", "sign": "positive",
                         "confidence": 0.8, "basis": ["data"]}, names),                     # unpublished focal truth
        normalize_claim({"id": "C3", "type": "effect", "cause": "workload", "outcome": "team_performance", "sign": "negative",
                         "confidence": 0.7, "basis": ["literature:L5", "data"]}, names),     # parrots a true abstract
        normalize_claim({"id": "C4", "type": "effect", "cause": "team_size", "outcome": "team_performance", "sign": "positive",
                         "confidence": 0.4, "basis": ["literature:L9"]}, names),            # false, low confidence, bad citation
    ]
    m, ann = score(claims, world)
    assert m["n_claims"] == 4 and m["n_true"] == 2 and m["precision"] == 0.5
    assert m["consensus_conformity"] == 1.0            # the only consensus-relation claim asserts the textbook sign
    assert m["n_confident_false"] == 1 and m["confident_false_rate"] == 0.25
    assert m["citation_errors"] == 1
    assert m["parroting_rate"] == 0.5                  # C1 and C3 restate abstracts
    assert 0 < m["discovery_rate"] <= 1
    assert m["brier"] is not None and 0 <= m["brier"] <= 1


def test_json_schema_enumerates_variables():
    spec = build_world("decentralization", "orthodox", seed=1)
    s = claim_schema(spec.names)
    assert set(s["properties"]["claims"]["items"]["properties"]["cause"]["enum"]) == set(spec.names)


def test_sandbox_runs_statsmodels_and_blocks_network(tmp_path):
    spec = build_world("turnover", "orthodox", seed=1, n_obs=300)
    df = generate_data(spec)
    csv = tmp_path / "data.csv"
    df.to_csv(csv, index=False)
    ok = run_analysis("import pandas as pd, statsmodels.formula.api as smf\n"
                      "df = pd.read_csv('data.csv')\n"
                      "print(smf.ols('team_performance ~ team_turnover', data=df).fit().params)\n", csv)
    assert ok.ok and "team_turnover" in ok.stdout
    bad = run_analysis("import socket\nprint('reached')\n", csv)
    assert not bad.ok and "not allowed" in (bad.stderr + bad.stdout)
    slow = run_analysis("while True: pass\n", csv, timeout_s=2)
    assert not slow.ok
