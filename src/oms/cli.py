"""Command line interface: ``oms worlds``, ``oms run``, ``oms report``, ``oms inspect``."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .experiments import load_config, run_experiment
from .report import make_report
from .worlds import TEMPLATES, build_world, save_world, load_world


def main(argv=None):
    p = argparse.ArgumentParser(prog="oms", description="Organizing Machine Science testbed")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("worlds", help="generate world bundles")
    w.add_argument("--templates", nargs="+", default=list(TEMPLATES))
    w.add_argument("--variants", nargs="+", default=["orthodox", "contrarian"])
    w.add_argument("--seeds", nargs="+", type=int, default=[1])
    w.add_argument("--n-obs", type=int, default=1200)
    w.add_argument("--out", default="worlds")

    r = sub.add_parser("run", help="run an experiment config")
    r.add_argument("config")
    r.add_argument("--repo", default=".")
    r.add_argument("--designs", nargs="*")
    r.add_argument("--worlds", nargs="*")
    r.add_argument("--mode", choices=["record", "replay"], default=None,
                   help="override backend mode (replay reproduces a run from llm_cache.jsonl without model access)")
    r.add_argument("--quiet", action="store_true")

    rp = sub.add_parser("report", help="aggregate results into tables and figures")
    rp.add_argument("run_dir")
    rp.add_argument("--out", default=None)

    ins = sub.add_parser("inspect", help="print a world's hidden truth and literature status")
    ins.add_argument("world_dir")

    a = p.parse_args(argv)
    if a.cmd == "worlds":
        for t in a.templates:
            for v in a.variants:
                for s in a.seeds:
                    spec = build_world(t, v, s, n_obs=a.n_obs)
                    out = save_world(spec, Path(a.out))
                    print(f"built {out}")
    elif a.cmd == "run":
        cfg = load_config(Path(a.config))
        run_dir = run_experiment(cfg, Path(a.repo), verbose=not a.quiet, only_designs=a.designs, only_worlds=a.worlds,
                                 mode=a.mode)
        print(f"results in {run_dir}")
    elif a.cmd == "report":
        run_dir = Path(a.run_dir)
        out = Path(a.out) if a.out else Path("results") / run_dir.name
        info = make_report(run_dir, out)
        print(info["summary"].to_string())
        print(f"written to {out}")
    elif a.cmd == "inspect":
        wd = load_world(Path(a.world_dir))
        print(json.dumps({"focal_truths": wd["truth"]["focal"],
                          "literature": [{"id": l["id"], "truth": l["truth"], "trap": l["trap"], "claim": l["claim"]} for l in wd["literature"]],
                          "trap_pairs": wd["truth"]["trap_pairs"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
