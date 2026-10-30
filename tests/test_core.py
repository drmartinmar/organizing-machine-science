import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from oms.worlds import (TEMPLATES, build_world, generate_data, truth_table, total_effect, total_interaction_effect,
                        save_world, load_world, EFFECT_THR)
from oms.claims import normalize_claim, evaluate_claim, claim_schema
from oms.scoring import score
from oms.sandbox import run_analysis
from oms.collective import OrgDesign, run_collective, run_mechanical
from oms.llm import MockBackend, CachingBackend, parse_json


@pytest.fixture(scope="module")
def world_dir(tmp_path_factory):
    root = tmp_path_factory.mktemp("worlds")
    spec = build_world("turnover", "orthodox", 1, n_obs=800)
    save_world(spec, root)
    return root / spec.world_id


def test_templates_build_both_variants():
    for t in TEMPLATES:
        for v in ("orthodox", "contrarian"):
            spec = build_world(t, v, 3)
            df = generate_data(spec)
            assert len(df) == spec.n_obs
            assert set(spec.names) <= set(df.columns)
            tt = truth_table(spec)
            assert tt["focal"], f"{t}/{v} has no focal truths"


def test_determinism():
    a = generate_data(build_world("monitoring", "contrarian", 7))
    b = generate_data(build_world("monitoring", "contrarian", 7))
    pd.testing.assert_frame_equal(a, b)
    c = generate_data(build_world("monitoring", "contrarian", 8))
    assert not a.equals(c)


def test_variants_flip_focal_sign():
    for t in TEMPLATES:
        o = build_world(t, "orthodox", 1)
        c = build_world(t, "contrarian", 1)
        so = total_effect(o, o.focal_cause, o.focal_outcome)
        sc = total_effect(c, c.focal_cause, c.focal_outcome)
        assert abs(so) >= EFFECT_THR and abs(sc) >= EFFECT_THR
        assert np.sign(so) != np.sign(sc)


def test_data_recovers_total_effect():
    """Regression on the generated data should recover the sign of the focal total effect."""
    import statsmodels.formula.api as smf
    spec = build_world("turnover", "orthodox", 2, n_obs=3000)
    df = generate_data(spec)
    # exogenous controls only (no mediators) -> total effect
    exog = [v.name for v in spec.variables if not any(e.effect == v.name for e in spec.edges)
            and not any(i.effect == v.name for i in spec.interactions) and v.name != spec.focal_cause]
    m = smf.ols(f"{spec.focal_outcome} ~ {spec.focal_cause} + " + " + ".join(exog), data=df).fit()
    assert np.sign(m.params[spec.focal_cause]) == np.sign(total_effect(spec, spec.focal_cause, spec.focal_outcome))
    assert m.pvalues[spec.focal_cause] < 0.001


def test_literature_truth_status_computed(world_dir):
    w = load_world(world_dir)
    ids = {l["id"]: l for l in w["literature"]}
    assert ids["L1"]["truth"] == "TRUE"          # consensus holds in the orthodox world
    assert ids["L4"]["truth"] == "FALSE" and ids["L4"]["trap"]  # confounded training claim
    c = build_world("turnover", "contrarian", 1)
    tt = truth_table(c)
    cons = {"type": "effect", "cause": "team_turnover", "outcome": "team_performance", "sign": "negative"}
    assert evaluate_claim(cons, tt)["verdict"] == "FALSE"


def test_claim_normalization_and_evaluation(world_dir):
    w = load_world(world_dir)
    names = w["spec"].names
    raw = {"id": "C1", "type": "Effect", "cause": "team_turnover", "outcome": "team_performance", "sign": "-",
           "confidence": 1.4, "basis": ["data"], "rationale": "x"}
    c = normalize_claim(raw, names)
    assert c["sign"] == "negative" and c["confidence"] == 1.0
    assert evaluate_claim(c, w["truth"])["verdict"] == "TRUE"
    bad = normalize_claim({"type": "effect", "cause": "nope", "outcome": "team_performance", "sign": "+"}, names)
    assert bad is None
    mod = normalize_claim({"type": "moderation", "cause": "team_turnover", "outcome": "team_performance",
                           "moderator": "task_interdependence", "interaction_sign": "negative", "confidence": 0.8}, names)
    assert evaluate_claim(mod, w["truth"])["verdict"] == "TRUE"
    med = normalize_claim({"type": "mediation", "cause": "team_turnover", "outcome": "team_performance",
                           "mediator": "knowledge_loss", "confidence": 0.8}, names)
    assert evaluate_claim(med, w["truth"])["verdict"] == "TRUE"
    med_false = normalize_claim({"type": "mediation", "cause": "team_turnover", "outcome": "team_performance",
                                 "mediator": "idea_novelty", "confidence": 0.8}, names)
    assert evaluate_claim(med_false, w["truth"])["verdict"] == "FALSE"


def test_scoring_metrics(world_dir):
    w = load_world(world_dir)
    names = w["spec"].names
    claims = [normalize_claim(c, names) for c in [
        {"id": "C1", "type": "effect", "cause": "team_turnover", "outcome": "team_performance", "sign": "negative",
         "confidence": 0.9, "basis": ["data", "literature:L1"]},
        {"id": "C2", "type": "effect", "cause": "training_investment", "outcome": "team_performance", "sign": "positive",
         "confidence": 0.8, "basis": ["literature:L4"]},
        {"id": "C3", "type": "effect", "cause": "team_size", "outcome": "team_performance", "sign": "positive",
         "confidence": 0.9, "basis": ["literature:L9"]},
    ]]
    m, ann = score(claims, w)
    assert m["n_claims"] == 3 and m["n_true"] == 1
    assert m["trap_rate"] == pytest.approx(1 / 3)
    assert m["confident_false_rate"] == pytest.approx(2 / 3)
    assert m["citation_errors"] == 1          # L9 does not exist
    assert m["parroting_rate"] == pytest.approx(2 / 3)
    assert 0 < m["focal_recall"] < 1


def test_sandbox_runs_pandas(world_dir):
    res = run_analysis("import pandas as pd, statsmodels.formula.api as smf\n"
                       "df = pd.read_csv('data.csv')\nprint(df.shape)\n"
                       "print(smf.ols('team_performance ~ team_turnover', data=df).fit().params.round(3))",
                       world_dir / "data.csv")
    assert res.ok, res.stderr
    assert "(800," in res.stdout
    blocked = run_analysis("import socket\n", world_dir / "data.csv")
    assert not blocked.ok and "not allowed" in blocked.stderr


def test_mechanical_and_mock_collective(world_dir, tmp_path):
    w = load_world(world_dir)
    r = run_mechanical(w)
    m, _ = score(r.final_claims, w)
    assert m["n_claims"] > 0 and m["precision"] is not None
    cache = tmp_path / "cache.jsonl"
    be = CachingBackend(MockBackend(), cache, mode="record")
    d = OrgDesign(name="pipeline_hierarchy", structure="pipeline", evaluation="hierarchy")
    res = run_collective(d, w, be, sandbox_dir=tmp_path)
    assert res.error is None, res.error
    assert res.n_calls >= 5
    roles = [s["role"] for s in res.transcript]
    assert "critic" in roles and "sandbox" in roles
    # replay from cache without any backend
    be2 = CachingBackend(None, cache, mode="replay")
    res2 = run_collective(d, w, be2, sandbox_dir=tmp_path)
    assert res2.error is None and res2.final_claims == res.final_claims


def test_parse_json_tolerates_fences():
    assert parse_json('```json\n{"a": 1}\n```')["a"] == 1
    assert parse_json('Here you go: {"a": [1,2,{"b":"}"}]} trailing')["a"][2]["b"] == "}"


def test_schema_enumerates_variables():
    s = claim_schema(["x", "y"])
    assert s["properties"]["claims"]["items"]["properties"]["cause"]["enum"] == ["x", "y"]
