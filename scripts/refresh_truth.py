"""Recompute truth.json and the literature truth statuses of existing world bundles with the current oracle,
leaving data.csv, codebook, brief and abstract texts untouched (so recorded runs still replay)."""
import json, sys
from pathlib import Path
from oms.worlds import WorldSpec, truth_table
from oms.claims import evaluate_claim

root = Path(sys.argv[1] if len(sys.argv) > 1 else "worlds")
for wd in sorted(p for p in root.iterdir() if (p / "spec.json").exists()):
    raw = json.loads((wd / "spec.json").read_text()); raw.pop("world_format", None)
    spec = WorldSpec.from_json(raw)
    truth = truth_table(spec)
    (wd / "truth.json").write_text(json.dumps(truth, indent=2))
    lit = json.loads((wd / "literature.json").read_text())
    changed = 0
    for l in lit:
        ev = evaluate_claim(l["claim"], truth)
        new = ev["verdict"]
        if new != l["truth"]:
            changed += 1
        l["truth"] = new; l["verdict"] = ev["verdict"]; l["trap"] = bool(ev.get("trap"))
    (wd / "literature.json").write_text(json.dumps(lit, indent=2))
    print(f"{wd.name}: focal={len(truth['focal'])} moderation rows={len(truth['moderations'])} literature statuses changed={changed}")
