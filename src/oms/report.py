"""Aggregate results of an experiment into tables and figures."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

METRICS = ["n_claims", "n_raw_claims", "n_dropped_claims", "precision", "precision_lenient", "n_weak", "focal_recall",
           "f1_focal", "discovery_rate", "parroting_rate", "consensus_conformity", "n_textbook_assertions", "trap_rate",
           "confident_false_rate", "brier", "overconfidence", "citation_errors", "n_false", "n_focal_missed", "empty_report"]


def rescore(run_dir: Path, worlds_root: Path) -> int:
    """Recompute every record's metrics from its stored claims with the current scorer (keeps results in step
    with scorer revisions; claims themselves are never changed). Returns the number of records rescored."""
    from .scoring import score
    from .worlds import load_world
    path = Path(run_dir) / "results.jsonl"
    worlds: dict[str, dict] = {}
    out, n = [], 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        wid = r["world_id"]
        if wid not in worlds:
            worlds[wid] = load_world(Path(worlds_root) / wid)
        raw = [{k: v for k, v in c.items() if k in ("id", "type", "cause", "outcome", "sign", "moderator", "interaction_sign",
                                                     "mediator", "indirect_sign", "confidence", "basis", "rationale")}
               for c in r.get("claims", [])]
        n_raw = _raw_claim_count(Path(run_dir) / "transcripts" / f"{r['design']}__{wid}.json")
        metrics, ann = score(raw, worlds[wid], n_raw_claims=n_raw)
        r["metrics"], r["claims"] = metrics, ann
        out.append(json.dumps(r, ensure_ascii=False))
        n += 1
    path.write_text("\n".join(out) + ("\n" if out else ""))
    return n


def _raw_claim_count(transcript_path: Path) -> int | None:
    """Number of claims in the final model output before normalization (from the stored transcript)."""
    if not transcript_path.exists():
        return None
    t = json.loads(transcript_path.read_text())
    steps = [st for st in t.get("transcript", []) if st.get("role") in ("synthesizer", "solo") and isinstance(st.get("response"), dict)]
    if not steps:
        return None
    return len(steps[-1]["response"].get("claims", []) or [])


def load_results(run_dir: Path) -> pd.DataFrame:
    rows = []
    for line in (Path(run_dir) / "results.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        row = {k: r[k] for k in ("design", "world_id", "template", "variant", "seed", "n_calls", "total_tokens",
                                 "wall_s", "code_runs", "code_failures", "error")}
        row.update(r["metrics"])
        rows.append(row)
    df = pd.DataFrame(rows)
    # keep the latest record per (design, world)
    df = df.drop_duplicates(subset=["design", "world_id"], keep="last").reset_index(drop=True)
    return df


def summarize(df: pd.DataFrame, by=("design",)) -> pd.DataFrame:
    g = df.groupby(list(by))
    agg = g[[m for m in METRICS if m in df.columns] + ["n_calls", "total_tokens", "wall_s"]].mean(numeric_only=True)
    agg.insert(0, "n_runs", g.size())
    return agg.round(3)


def summarize_with_se(df: pd.DataFrame, metrics: list[str], by: str = "design") -> pd.DataFrame:
    rows = []
    for key, sub in df.groupby(by):
        row = {by: key, "n_runs": len(sub)}
        for m in metrics:
            x = sub[m].dropna().astype(float)
            row[m] = x.mean() if len(x) else np.nan
            row[m + "_se"] = (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else np.nan
        rows.append(row)
    return pd.DataFrame(rows).set_index(by).round(3)


def markdown_table(df: pd.DataFrame, cols: list[str], labels: dict[str, str] | None = None, fmt: str = "{:.2f}") -> str:
    labels = labels or {}
    head = "| " + " | ".join([df.index.name or ""] + [labels.get(c, c) for c in cols]) + " |"
    sep = "|" + "---|" * (len(cols) + 1)
    lines = [head, sep]
    for idx, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, (int, np.integer)) or (isinstance(v, float) and float(v).is_integer() and c.startswith("n_")):
                cells.append(f"{int(v)}")
            elif v is None or (isinstance(v, float) and np.isnan(v)):
                cells.append("–")
            else:
                cells.append(fmt.format(v))
        lines.append("| " + " | ".join([str(idx)] + cells) + " |")
    return "\n".join(lines)


def make_report(run_dir: Path, out_dir: Path, design_order: list[str] | None = None) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    run_dir, out_dir = Path(run_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    worlds_root = run_dir.parent.parent / "worlds"
    if worlds_root.exists():
        rescore(run_dir, worlds_root)
    df = load_results(run_dir)
    df = df[df["error"].isna()] if "error" in df else df
    order = design_order or [d for d in ["mechanical", "solo", "pipeline", "pipeline_polyarchy", "pipeline_hierarchy",
                                          "pipeline_hierarchy_hetero", "datafirst_hierarchy", "two_theorists_connected",
                                          "two_theorists_isolated"] if d in set(df["design"])]
    order += [d for d in sorted(set(df["design"])) if d not in order]
    df["design"] = pd.Categorical(df["design"], categories=order, ordered=True)
    df = df.sort_values(["design", "world_id"])
    df.to_csv(out_dir / "runs_long.csv", index=False)

    overall = summarize(df)
    overall.to_csv(out_dir / "summary_by_design.csv")
    by_variant = summarize(df, by=("design", "variant"))
    by_variant.to_csv(out_dir / "summary_by_design_variant.csv")
    contr = df[df["variant"] == "contrarian"]
    orth = df[df["variant"] == "orthodox"]

    # ---- figures ----------------------------------------------------------
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    cmap = {d: colors[i % 10] for i, d in enumerate(order)}

    # Fig 1: precision against coverage by design
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    for d in order:
        sub = df[df["design"] == d]
        if sub.empty:
            continue
        x, y = sub["focal_recall"].astype(float), sub["precision"].astype(float)
        ax.scatter(x, y, s=22, alpha=0.35, color=cmap[d])
        ax.errorbar(x.mean(), y.mean(), xerr=_se(x), yerr=_se(y), fmt="o", ms=9, color=cmap[d], label=d, capsize=3)
    ax.set_xlabel("Coverage (share of focal mechanisms recovered)")
    ax.set_ylabel("Precision (share of reported claims true)")
    ax.set_xlim(-0.03, 1.03); ax.set_ylim(-0.03, 1.03)
    ax.set_title("Precision against coverage by organizational design")
    ax.legend(fontsize=7, loc="lower left")
    fig.tight_layout(); fig.savefig(out_dir / "fig1_validity_frontier.png", dpi=200); plt.close(fig)

    # Fig 2: confident-false ("Potemkin") rate and consensus conformity in contrarian worlds
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    _bar(axes[0], df, "confident_false_rate", order, cmap, "Confident-false rate (all worlds)")
    _bar(axes[1], contr, "consensus_conformity", order, cmap, "Prior-conformity error (contrarian worlds)")
    fig.tight_layout(); fig.savefig(out_dir / "fig2_slop_and_conformity.png", dpi=200); plt.close(fig)

    # Fig 3: discovery of unpublished truths and calibration
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    _bar(axes[0], df, "discovery_rate", order, cmap, "Recovery of unpublished focal truths")
    _bar(axes[1], df, "brier", order, cmap, "Brier score (lower is better)")
    fig.tight_layout(); fig.savefig(out_dir / "fig3_discovery_calibration.png", dpi=200); plt.close(fig)

    # ---- markdown summary ---------------------------------------------------
    se_cols = ["precision", "focal_recall", "discovery_rate", "confident_false_rate", "consensus_conformity",
               "parroting_rate", "trap_rate", "brier", "citation_errors", "n_claims"]
    se_tab = summarize_with_se(df, se_cols)
    se_tab = se_tab.reindex([d for d in order if d in se_tab.index])
    lines = [f"# Results: {run_dir.name}", "",
             f"Runs: {len(df)} (designs: {len(order)}, worlds: {df['world_id'].nunique()}).", "",
             "## Means by design (all worlds)", "",
             markdown_table(overall.reindex(order), ["n_runs", "n_claims", "n_dropped_claims", "empty_report", "precision",
                                                     "precision_lenient", "focal_recall", "discovery_rate",
                                                     "confident_false_rate", "parroting_rate", "trap_rate", "brier",
                                                     "citation_errors", "n_calls"]),
             "", "## Standard errors (across worlds)", "",
             markdown_table(se_tab, [c for c in se_tab.columns if c.endswith("_se")]), ""]
    if not contr.empty:
        lines += ["## Contrarian worlds only (textbook sign is wrong here)", "",
                  markdown_table(summarize(contr).reindex([d for d in order if d in set(contr['design'])]),
                                 ["n_runs", "precision", "focal_recall", "consensus_conformity", "confident_false_rate", "parroting_rate"]), ""]
    if not orth.empty:
        lines += ["## Orthodox worlds only", "",
                  markdown_table(summarize(orth).reindex([d for d in order if d in set(orth['design'])]),
                                 ["n_runs", "precision", "focal_recall", "consensus_conformity", "confident_false_rate", "parroting_rate"]), ""]
    (out_dir / "RESULTS.md").write_text("\n".join(lines))
    return {"n_runs": len(df), "summary": overall, "out_dir": out_dir}


def _se(x):
    x = pd.Series(x).dropna().astype(float)
    return (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else 0.0


def _bar(ax, df, metric, order, cmap, title):
    ds = [d for d in order if d in set(df["design"])]
    means = [df[df["design"] == d][metric].astype(float).mean() for d in ds]
    ses = [_se(df[df["design"] == d][metric]) for d in ds]
    ax.bar(range(len(ds)), means, yerr=ses, color=[cmap[d] for d in ds], capsize=3)
    ax.set_xticks(range(len(ds)))
    ax.set_xticklabels(ds, rotation=35, ha="right", fontsize=7)
    ax.set_title(title, fontsize=10)
    ax.set_ylim(0, max(0.05, np.nanmax([m + s for m, s in zip(means, ses)]) * 1.15) if len(ds) else 1)
