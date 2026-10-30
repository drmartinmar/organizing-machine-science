from pathlib import Path

from oms.collective import OrgDesign, run_collective
from oms.experiments import DEFAULT_DESIGNS, resolve_designs
from oms.llm import MockBackend, CachingBackend
from oms.scoring import score
from oms.worlds import build_world, save_world, load_world


def _world(tmp_path, template="turnover", variant="orthodox"):
    spec = build_world(template, variant, seed=1, n_obs=400)
    return load_world(save_world(spec, tmp_path))


def test_all_default_designs_run_on_mock(tmp_path):
    world = _world(tmp_path)
    cfg = {"designs": list(DEFAULT_DESIGNS), "backend": {"alt_model": "alt-mock"}}
    for d in resolve_designs(cfg):
        res = run_collective(d, world, MockBackend(), sandbox_dir=tmp_path)
        assert res.error is None, (d.name, res.error)
        metrics, ann = score(res.final_claims, world)
        assert metrics["n_claims"] == len(res.final_claims)
        if d.name == "mechanical":
            assert res.n_calls == 0 and metrics["n_claims"] > 0
        if d.evaluation == "hierarchy":
            # the mock critic rejects every third claim; the veto must have removed something
            assert len(res.final_claims) < len(res.draft_claims)
        if d.name == "pipeline_hierarchy_hetero":
            critic_steps = [s for s in res.transcript if s["role"] == "critic"]
            assert critic_steps and critic_steps[0]["model"] == "mock"  # mock ignores model names but the call is routed


def test_record_replay_cache_roundtrip(tmp_path):
    world = _world(tmp_path, "monitoring", "contrarian")
    cache = tmp_path / "cache.jsonl"
    d = OrgDesign(name="pipeline", structure="pipeline")
    rec = CachingBackend(MockBackend(), cache, mode="record")
    r1 = run_collective(d, world, rec, sandbox_dir=tmp_path)
    assert r1.error is None and cache.exists()
    rep = CachingBackend(None, cache, mode="replay")
    r2 = run_collective(d, world, rep, sandbox_dir=tmp_path)
    assert r2.error is None
    assert r1.final_claims == r2.final_claims
    assert all(s["cached"] for s in r2.transcript if s["role"] not in ("sandbox",))


def test_mechanical_baseline_finds_planted_trap_null(tmp_path):
    world = _world(tmp_path, "turnover", "orthodox")
    d = OrgDesign(name="mechanical", llm=False)
    res = run_collective(d, world, MockBackend())
    trap_claims = [c for c in res.final_claims if c["cause"] == "training_investment" and c["type"] == "effect"]
    assert all(c["sign"] == "none" for c in trap_claims)
