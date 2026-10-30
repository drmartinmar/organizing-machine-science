"""Experiment harness: run a factorial of designs x worlds, score, and persist."""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from .collective import OrgDesign, run_collective
from .llm import make_backend
from .scoring import score
from .worlds import build_world, load_world, save_world

DEFAULT_DESIGNS: dict[str, dict] = {
    "mechanical": dict(llm=False, description="Fixed OLS procedure; no language model."),
    "solo": dict(structure="solo", description="One generalist agent theorizes, analyzes and reports."),
    "pipeline": dict(structure="pipeline", sequence="theory_first", evaluation="none",
                     description="Theorist -> analyst -> lead; no independent review."),
    "pipeline_polyarchy": dict(structure="pipeline", evaluation="polyarchy",
                               description="Pipeline plus an independent critic whose review is advisory."),
    "pipeline_hierarchy": dict(structure="pipeline", evaluation="hierarchy",
                               description="Pipeline plus an independent critic with veto power."),
    "pipeline_hierarchy_hetero": dict(structure="pipeline", evaluation="hierarchy", critic_model="__ALT_MODEL__",
                                      description="Veto critic run on a different model family."),
    "datafirst_hierarchy": dict(structure="pipeline", sequence="data_first", evaluation="hierarchy",
                                description="Analyst explores the data blind to the literature; theorist explains; veto critic."),
    "two_theorists_connected": dict(structure="two_theorists", team_structure="connected", evaluation="hierarchy",
                                    description="Second theorist sees the first proposal (connected network); veto critic."),
    "two_theorists_isolated": dict(structure="two_theorists", team_structure="isolated", evaluation="hierarchy",
                                   description="Two theorists propose independently, merged late (isolated subgroups); veto critic."),
}


def load_config(path: Path) -> dict:
    cfg = yaml.safe_load(Path(path).read_text())
    cfg.setdefault("name", Path(path).stem)
    cfg.setdefault("backend", {"name": "mock"})
    cfg.setdefault("workers", 1)
    cfg.setdefault("worlds", {"templates": ["turnover"], "variants": ["orthodox"], "seeds": [1]})
    cfg.setdefault("designs", ["mechanical", "pipeline"])
    return cfg


def resolve_designs(cfg: dict) -> list[OrgDesign]:
    alt = (cfg.get("backend") or {}).get("alt_model")
    out = []
    for item in cfg["designs"]:
        if isinstance(item, str):
            name, params = item, dict(DEFAULT_DESIGNS[item])
        else:
            name = item["name"]
            params = dict(DEFAULT_DESIGNS.get(item.get("base", name), {}))
            params.update({k: v for k, v in item.items() if k not in ("name", "base")})
        if params.get("critic_model") == "__ALT_MODEL__":
            params["critic_model"] = alt
        if "theorist_models" in params:
            params["theorist_models"] = [alt if m == "__ALT_MODEL__" else m for m in params["theorist_models"]]
        out.append(OrgDesign(name=name, **params))
    return out


def ensure_worlds(cfg: dict, worlds_root: Path) -> list[dict]:
    w = cfg["worlds"]
    worlds = []
    if "ids" in w:
        for wid in w["ids"]:
            worlds.append(load_world(worlds_root / wid))
        return worlds
    for t in w["templates"]:
        for v in w["variants"]:
            for s in w["seeds"]:
                spec = build_world(t, v, s, n_obs=w.get("n_obs", 1200), noise_sd=w.get("noise_sd", 1.0))
                path = worlds_root / spec.world_id
                if not (path / "truth.json").exists():
                    save_world(spec, worlds_root)
                worlds.append(load_world(path))
    return worlds


def run_experiment(cfg: dict, repo_root: Path, verbose: bool = True, only_designs: list[str] | None = None,
                   only_worlds: list[str] | None = None, mode: str | None = None) -> Path:
    name = cfg["name"]
    run_dir = repo_root / "runs" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "transcripts").mkdir(exist_ok=True)
    (run_dir / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    b = cfg["backend"]
    backend = make_backend(b.get("name", "mock"), model=b.get("model"), cache_path=run_dir / "llm_cache.jsonl",
                           mode=mode or b.get("mode", "record"), reasoning_effort=b.get("reasoning_effort", "medium"))
    designs = resolve_designs(cfg)
    if only_designs:
        designs = [d for d in designs if d.name in only_designs]
    worlds = ensure_worlds(cfg, repo_root / "worlds")
    if only_worlds:
        worlds = [w for w in worlds if w["spec"].world_id in only_worlds]
    results_path = run_dir / "results.jsonl"
    done = set()
    if results_path.exists():
        for line in results_path.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if not r.get("error"):
                    done.add((r["design"], r["world_id"]))
    jobs = [(d, w) for d in designs for w in worlds if (d.name, w["spec"].world_id) not in done]
    if verbose:
        print(f"[{name}] backend={backend.name} designs={len(designs)} worlds={len(worlds)} jobs={len(jobs)} (skipping {len(done)} done)")
    sandbox_dir = run_dir / "sandbox"
    sandbox_dir.mkdir(exist_ok=True)

    def job(d, w):
        t0 = time.time()
        res = run_collective(d, w, backend, sandbox_dir=sandbox_dir, verbose=verbose)
        metrics, ann = score(res.final_claims, w)
        rec = {"design": d.name, "world_id": w["spec"].world_id, "template": w["spec"].template,
               "variant": w["spec"].variant, "seed": w["spec"].seed, "design_params": d.to_json(),
               "metrics": metrics, "claims": ann, "n_calls": res.n_calls, "total_tokens": res.total_tokens,
               "wall_s": res.wall_s, "code_runs": res.code_runs, "code_failures": res.code_failures,
               "error": res.error, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
        (run_dir / "transcripts" / f"{d.name}__{w['spec'].world_id}.json").write_text(
            json.dumps({**rec, "transcript": res.transcript, "draft_claims": res.draft_claims,
                        "critic_verdicts": res.critic_verdicts, "report": res.report}, indent=1, ensure_ascii=False))
        with open(results_path, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if verbose:
            m = metrics
            print(f"[{name}] {d.name:28s} {w['spec'].world_id:28s} claims={m['n_claims']:2d} prec={_f(m['precision'])} "
                  f"recall={_f(m['focal_recall'])} potemkin={_f(m['confident_false_rate'])} calls={res.n_calls} "
                  f"{res.wall_s}s{' ERROR: ' + res.error if res.error else ''}")
        return rec

    workers = int(cfg.get("workers", 1))
    if workers <= 1:
        for d, w in jobs:
            job(d, w)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(job, d, w) for d, w in jobs]
            for fut in as_completed(futs):
                fut.result()
    return run_dir


def _f(x):
    return "  na " if x is None else f"{x:5.2f}"
