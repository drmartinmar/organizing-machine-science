"""Research collectives as organizations.

An ``OrgDesign`` fixes *who* exists (division of labor), *who sees what and in
which order* (communication structure and sequencing), *who can veto*
(evaluation architecture) and *how alike the members are* (model
heterogeneity).  ``run_collective`` executes a design on a world and returns
the final structured report plus a full transcript.

Design levers (see the technical appendix for the mapping to theory):

* ``structure``: ``solo`` (one generalist), ``pipeline`` (theorist -> analyst
  -> lead), ``two_theorists`` (two theorists feeding one analyst and lead).
* ``sequence``: ``theory_first`` or ``data_first`` (analyst explores the data
  blind to the literature before the theorist sees anything).
* ``evaluation``: ``none``, ``polyarchy`` (independent critic, advisory) or
  ``hierarchy`` (independent critic with veto; Sah and Stiglitz 1986).
* ``team_structure`` (two_theorists only): ``connected`` (the second theorist
  sees the first proposal) or ``isolated`` (independent proposals merged late;
  Fang, Lee and Schilling 2010).
* ``critic_model`` / ``theorist_models``: use a different model for the critic
  or the second theorist to break error correlation (heterogeneity).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import pandas as pd

from . import roles
from .claims import normalize_claim, same_relation, same_claim
from .llm import Backend, LLMResponse
from .sandbox import run_analysis

PERSONAS = {
    "mechanism": ("You favor mechanism-based explanations (which mediators carry an effect) and treat received "
                  "wisdom as a hypothesis to be tested rather than a premise."),
    "contingency": ("You favor contingency explanations (which moderators change the size or sign of an effect) and "
                    "take prior findings seriously unless the data contradict them."),
}


@dataclass
class OrgDesign:
    name: str
    structure: str = "pipeline"            # solo | pipeline | two_theorists
    sequence: str = "theory_first"         # theory_first | data_first
    evaluation: str = "none"               # none | polyarchy (advisory) | hierarchy (veto, revisions allowed) | and | or
    team_structure: str = "connected"      # connected | isolated (two_theorists)
    critic_model: str | None = None
    theorist_models: list[str | None] = field(default_factory=lambda: [None, None])
    llm: bool = True                       # False -> mechanical baseline
    description: str = ""

    def to_json(self) -> dict:
        return asdict(self)


@dataclass
class RunResult:
    design: str
    world_id: str
    final_claims: list[dict]
    report: dict
    transcript: list[dict]
    n_calls: int
    total_tokens: int
    wall_s: float
    code_runs: int
    code_failures: int
    draft_claims: list[dict] = field(default_factory=list)
    critic_verdicts: list[dict] = field(default_factory=list)
    n_raw_claims: int = 0
    error: str | None = None

    def to_json(self) -> dict:
        return asdict(self)


class Collective:
    """Executes one design on one world; keeps a transcript of every step."""

    def __init__(self, design: OrgDesign, world: dict, backend: Backend, sandbox_dir: Path | None = None,
                 verbose: bool = False):
        self.d = design
        self.w = world
        self.spec = world["spec"]
        self.backend = backend
        self.sandbox_dir = sandbox_dir
        self.verbose = verbose
        self.transcript: list[dict] = []
        self.n_calls = 0
        self.tokens = 0
        self.code_runs = 0
        self.code_failures = 0
        self.last_raw_count = 0
        self.names = self.spec.names
        self.public_lit = [{"id": l["id"], "text": l["text"], "claim": l["claim"]} for l in world["literature"]]
        self.brief_min = (f"Setting: {self.spec.setting}. Research question: {self.spec.research_question} "
                          f"Focal cause: `{self.spec.focal_cause}`. Focal outcome: `{self.spec.focal_outcome}`.")

    # ----- infrastructure -------------------------------------------------
    def _call(self, role: str, messages: list[dict], schema: dict | None, model: str | None = None,
              extra_meta: dict | None = None) -> Any:
        meta = {"role": role, "spec": self.spec, "literature": self.public_lit}
        if extra_meta:
            meta.update(extra_meta)
        t0 = time.time()
        r: LLMResponse = self.backend.complete(messages, schema=schema, model=model, meta=meta)
        self.n_calls += 1
        self.tokens += int(r.usage.get("total_tokens") or (r.usage.get("prompt_tokens", 0) + r.usage.get("completion_tokens", 0)))
        try:
            parsed = r.json()
        except Exception as e:  # unparseable -> record and return empty
            parsed = {"_parse_error": str(e), "_raw": r.text[:2000]}
        self.transcript.append({"step": len(self.transcript) + 1, "role": role, "model": r.model,
                                "messages": messages, "response": parsed, "raw": r.text if "_parse_error" in parsed else None,
                                "cached": r.cached, "latency_s": round(time.time() - t0, 2), "usage": r.usage})
        if self.verbose:
            print(f"  [{self.d.name} | {self.spec.world_id}] {role} done ({r.model}, {round(time.time()-t0,1)}s)")
        return parsed

    def _data_preview(self) -> str:
        df = pd.read_csv(self.w["path"] / "data.csv")
        with pd.option_context("display.width", 200, "display.max_columns", 40):
            head = df.head(5).to_string(index=False)
            desc = df.drop(columns=["unit_id"]).describe().round(2).T[["mean", "std", "min", "max"]].to_string()
        return f"{head}\n\n{desc}"

    def _norm_claims(self, raw: Any) -> list[dict]:
        if not isinstance(raw, dict):
            self.last_raw_count = 0
            return []
        out = []
        self.last_raw_count = len(raw.get("claims", []) or [])
        for c in raw.get("claims", []) or []:
            n = normalize_claim(c, self.names)
            if n is not None:
                out.append(n)
        for i, c in enumerate(out, start=1):
            if not c["id"]:
                c["id"] = f"C{i}"
        return _dedupe(out)

    def _run_code(self, code: str) -> dict:
        self.code_runs += 1
        res = run_analysis(code, self.w["path"] / "data.csv", workdir=self.sandbox_dir)
        if not res.ok:
            self.code_failures += 1
        return {"ok": res.ok, "stdout": res.stdout, "stderr": res.stderr, "seconds": res.seconds}

    # ----- role steps ---------------------------------------------------------
    def theorist(self, persona: str | None = None, prior_theory: dict | None = None,
                 data_findings: dict | None = None, model: str | None = None) -> dict:
        msgs = roles.theorist_messages(self.w["brief"], self.w["codebook"], persona=persona,
                                       prior_theory=prior_theory, data_findings=data_findings)
        out = self._call("theorist", msgs, roles.theory_schema(self.names), model=model)
        out = out if isinstance(out, dict) else {}
        out["claims"] = self._norm_claims(out)
        return out

    def analyst(self, hypotheses: list[dict] | None, model: str | None = None) -> dict:
        preview = self._data_preview()
        msgs = roles.analyst_code_messages(self.w["codebook"], preview, hypotheses, self.brief_min)
        plan_code = self._call("analyst_code", msgs, roles.analyst_code_schema(), model=model)
        code = plan_code.get("code", "") if isinstance(plan_code, dict) else ""
        plan = plan_code.get("plan", "") if isinstance(plan_code, dict) else ""
        exec_res = self._run_code(code) if code.strip() else {"ok": False, "stdout": "", "stderr": "no code returned", "seconds": 0}
        if not exec_res["ok"]:
            msgs = roles.analyst_code_messages(self.w["codebook"], preview, hypotheses, self.brief_min,
                                               error_feedback=(exec_res["stderr"] or exec_res["stdout"])[-2000:])
            plan_code = self._call("analyst_code", msgs, roles.analyst_code_schema(), model=model)
            code = plan_code.get("code", "") if isinstance(plan_code, dict) else ""
            plan = plan_code.get("plan", plan) if isinstance(plan_code, dict) else plan
            exec_res = self._run_code(code) if code.strip() else exec_res
        output = exec_res["stdout"] if exec_res["ok"] else f"[script failed]\n{exec_res['stderr']}\n{exec_res['stdout']}"
        self.transcript.append({"step": len(self.transcript) + 1, "role": "sandbox", "model": None, "messages": None,
                                "response": {"ok": exec_res["ok"], "seconds": exec_res["seconds"],
                                             "stdout": output[-6000:], "stderr": exec_res["stderr"][-1500:]},
                                "cached": False, "latency_s": exec_res["seconds"], "usage": {}})
        msgs = roles.analyst_interpret_messages(self.w["codebook"], hypotheses, plan, code, output, self.brief_min)
        interp = self._call("analyst_interpret", msgs, roles.analyst_interpret_schema(self.names), model=model)
        interp = interp if isinstance(interp, dict) else {}
        interp["claims"] = self._norm_claims(interp)
        return {"plan": plan, "code": code, "output": output, "code_ok": exec_res["ok"],
                "findings": interp.get("findings", []), "data_summary": interp.get("data_summary", ""),
                "claims": interp["claims"]}

    def synthesizer(self, theory: dict | None, analysis: dict | None, critique: dict | None, extra: str = "") -> dict:
        analysis_view = None
        if analysis is not None:
            analysis_view = {k: analysis[k] for k in ("plan", "data_summary", "findings", "claims") if k in analysis}
            analysis_view["output_excerpt"] = (analysis.get("output") or "")[-3500:]
        msgs = roles.synthesizer_messages(self.w["brief"], self.w["codebook"], theory, analysis_view, critique,
                                          self.d.evaluation, extra=extra)
        out = self._call("synthesizer", msgs, roles.final_schema(self.names))
        out = out if isinstance(out, dict) else {}
        out["claims"] = self._norm_claims(out)
        return out

    def critic(self, claims: list[dict], analysis: dict | None, model: str | None = None) -> dict:
        evidence = "No data analysis was presented." if analysis is None else (
            f"Analysis plan: {analysis.get('plan','')}\n\nScript:\n```python\n{analysis.get('code','')}\n```\n\n"
            f"Output:\n```\n{(analysis.get('output') or '')[-3500:]}\n```\n\nAnalyst's findings:\n```json\n"
            f"{json.dumps(analysis.get('findings', []), indent=1)}\n```")
        binding = self.d.evaluation in ("hierarchy", "and")
        msgs = roles.critic_messages(self.w["brief"], self.w["codebook"], claims, evidence, binding)
        out = self._call("critic", msgs, roles.critic_schema(), model=model, extra_meta={"n_claims": len(claims)})
        return out if isinstance(out, dict) else {"verdicts": [], "concerns": ""}

    # ----- governance ---------------------------------------------------------
    def apply_veto(self, final_claims: list[dict], draft_claims: list[dict], verdicts: list[dict]) -> list[dict]:
        """``hierarchy`` (pilot rule): keep final claims about relations the critic accepted or asked to revise."""
        by_id = {c["id"]: c for c in draft_claims}
        allowed = [by_id[v["claim_id"]] for v in verdicts
                   if v.get("verdict") in ("accept", "revise") and v.get("claim_id") in by_id]
        return [c for c in final_claims if any(same_relation(c, a) for a in allowed)]

    def apply_and(self, final_claims: list[dict], draft_claims: list[dict], verdicts: list[dict]) -> list[dict]:
        """Strict hierarchy (AND): a claim survives only if the lead kept it and the critic accepted that same
        claim (same relation and same asserted sign)."""
        by_id = {c["id"]: c for c in draft_claims}
        accepted = [by_id[v["claim_id"]] for v in verdicts if v.get("verdict") == "accept" and v.get("claim_id") in by_id]
        return [c for c in final_claims if any(same_claim(c, a) for a in accepted)]

    def apply_or(self, final_claims: list[dict], draft_claims: list[dict], verdicts: list[dict]) -> list[dict]:
        """Polyarchy (OR): a draft claim survives if either the lead kept it in the final report or the critic
        accepted it."""
        by_id = {c["id"]: c for c in draft_claims}
        accepted = [by_id[v["claim_id"]] for v in verdicts if v.get("verdict") == "accept" and v.get("claim_id") in by_id]
        out = list(final_claims)
        for a in accepted:
            if not any(same_relation(a, c) for c in out):
                out.append(a)
        return out

    # ----- orchestration ------------------------------------------------------
    def run(self) -> RunResult:
        t0 = time.time()
        d = self.d
        theory: dict | None = None
        analysis: dict | None = None
        draft: dict
        critique: dict | None = None
        try:
            if d.structure == "solo":
                preview = self._data_preview()
                msgs = roles.solo_step1_messages(self.w["brief"], self.w["codebook"], preview)
                step1 = self._call("solo", msgs, roles.solo_step1_schema(self.names))
                step1 = step1 if isinstance(step1, dict) else {}
                step1["claims"] = self._norm_claims(step1)
                code = step1.get("code", "")
                exec_res = self._run_code(code) if code.strip() else {"ok": False, "stdout": "", "stderr": "no code", "seconds": 0}
                if not exec_res["ok"]:
                    msgs2 = list(msgs)
                    msgs2[-1] = {"role": "user", "content": msgs[-1]["content"] +
                                 "\n\nYour previous script failed with this error; fix it:\n```\n" +
                                 (exec_res["stderr"] or exec_res["stdout"])[-2000:] + "\n```"}
                    step1b = self._call("solo", msgs2, roles.solo_step1_schema(self.names))
                    if isinstance(step1b, dict):
                        step1 = step1b
                        step1["claims"] = self._norm_claims(step1)
                        code = step1.get("code", "")
                        exec_res = self._run_code(code) if code.strip() else exec_res
                output = exec_res["stdout"] if exec_res["ok"] else f"[script failed]\n{exec_res['stderr']}\n{exec_res['stdout']}"
                self.transcript.append({"step": len(self.transcript) + 1, "role": "sandbox", "model": None, "messages": None,
                                        "response": {"ok": exec_res["ok"], "seconds": exec_res["seconds"],
                                                     "stdout": output[-6000:], "stderr": exec_res["stderr"][-1500:]},
                                        "cached": False, "latency_s": exec_res["seconds"], "usage": {}})
                step1_view = {k: step1.get(k) for k in ("theory_summary", "claims", "proposed_tests", "code")}
                draft = self._call("solo", roles.solo_step2_messages(self.w["brief"], self.w["codebook"], step1_view, output),
                                   roles.final_schema(self.names))
                draft = draft if isinstance(draft, dict) else {}
                draft["claims"] = self._norm_claims(draft)
                final = draft
                theory = step1
            else:
                if d.structure == "two_theorists":
                    tA = self.theorist(persona=PERSONAS["mechanism"], model=d.theorist_models[0])
                    tB = self.theorist(persona=PERSONAS["contingency"],
                                       prior_theory=(_view(tA) if d.team_structure == "connected" else None),
                                       model=d.theorist_models[1] if len(d.theorist_models) > 1 else None)
                    theory = {"theorist_A": _view(tA), "theorist_B": _view(tB)}
                    hyps = _dedupe(tA["claims"] + tB["claims"])
                    analysis = self.analyst(hyps)
                elif d.sequence == "data_first":
                    analysis = self.analyst(None)
                    t = self.theorist(data_findings={"data_summary": analysis["data_summary"],
                                                     "claims": analysis["claims"]}, model=d.theorist_models[0])
                    theory = _view(t)
                else:
                    t = self.theorist(model=d.theorist_models[0])
                    theory = _view(t)
                    analysis = self.analyst(t["claims"])
                draft = self.synthesizer(theory, analysis, None)
                final = draft
                if d.evaluation in ("polyarchy", "hierarchy", "and", "or") and draft["claims"]:
                    critique = self.critic(draft["claims"], analysis, model=d.critic_model)
                    final = self.synthesizer(theory, analysis, critique,
                                             extra="Your earlier draft of the final claims:\n```json\n" +
                                                   json.dumps(draft["claims"], indent=1) + "\n```")
                    verdicts = critique.get("verdicts", [])
                    if d.evaluation == "hierarchy":
                        final["claims"] = self.apply_veto(final["claims"], draft["claims"], verdicts)
                    elif d.evaluation == "and":
                        final["claims"] = self.apply_and(final["claims"], draft["claims"], verdicts)
                    elif d.evaluation == "or":
                        final["claims"] = self.apply_or(final["claims"], draft["claims"], verdicts)
            return RunResult(design=d.name, world_id=self.spec.world_id, final_claims=final.get("claims", []),
                             report={k: final.get(k) for k in ("theory_summary", "limitations")},
                             transcript=self.transcript, n_calls=self.n_calls, total_tokens=self.tokens,
                             wall_s=round(time.time() - t0, 1), code_runs=self.code_runs, code_failures=self.code_failures,
                             draft_claims=draft.get("claims", []) if isinstance(draft, dict) else [],
                             critic_verdicts=(critique or {}).get("verdicts", []),
                             n_raw_claims=self.last_raw_count)
        except Exception as e:  # keep the run in the record even if it crashed
            return RunResult(design=d.name, world_id=self.spec.world_id, final_claims=[], report={},
                             transcript=self.transcript, n_calls=self.n_calls, total_tokens=self.tokens,
                             wall_s=round(time.time() - t0, 1), code_runs=self.code_runs, code_failures=self.code_failures,
                             error=f"{type(e).__name__}: {e}")


def _view(theory: dict) -> dict:
    return {k: theory.get(k) for k in ("theory_summary", "claims", "proposed_tests", "limitations")}


def _dedupe(claims: list[dict]) -> list[dict]:
    out: list[dict] = []
    for c in claims:
        if not any(same_relation(c, o) for o in out):
            out.append(c)
    return out


# ---------------------------------------------------------------------------
# Mechanical baseline (no language model)
# ---------------------------------------------------------------------------

def run_mechanical(world: dict, alpha: float = 0.01) -> RunResult:
    """A fixed statistical procedure: kitchen-sink OLS for direct effects, focal-cause interactions, two-equation
    mediation screens.  It knows the focal cause and outcome (from the brief) but nothing else."""
    import statsmodels.formula.api as smf
    t0 = time.time()
    spec = world["spec"]
    df = pd.read_csv(world["path"] / "data.csv").drop(columns=["unit_id"])
    fc, fo = spec.focal_cause, spec.focal_outcome
    others = [c for c in df.columns if c not in (fc, fo)]
    claims: list[dict] = []
    k = 0

    def add(c):
        nonlocal k
        k += 1
        c["id"] = f"M{k}"
        n = normalize_claim(c, spec.names)
        if n:
            claims.append(n)

    m = smf.ols(f"{fo} ~ {fc} + " + " + ".join(others), data=df).fit()
    for v in [fc] + others:
        p = float(m.pvalues[v]); b = float(m.params[v])
        sign = "none" if p >= alpha else ("positive" if b > 0 else "negative")
        if v == fc or sign != "none":
            add({"type": "effect", "cause": v, "outcome": fo, "sign": sign, "confidence": round(min(0.99, 1 - p), 3) if sign != "none" else 0.6,
                 "basis": ["data"], "rationale": f"OLS with all covariates: b={b:.3f}, p={p:.3g}"})
    for v in others:
        mi = smf.ols(f"{fo} ~ {fc} * {v} + " + " + ".join(o for o in others if o != v), data=df).fit()
        term = f"{fc}:{v}"
        p = float(mi.pvalues[term]); b = float(mi.params[term])
        if p < alpha:
            add({"type": "moderation", "cause": fc, "outcome": fo, "moderator": v,
                 "interaction_sign": "positive" if b > 0 else "negative", "confidence": round(min(0.99, 1 - p), 3),
                 "basis": ["data"], "rationale": f"interaction b={b:.3f}, p={p:.3g}"})
    for v in others:
        m1 = smf.ols(f"{v} ~ {fc} + " + " + ".join(o for o in others if o != v), data=df).fit()
        p1 = float(m1.pvalues[fc]); b1 = float(m1.params[fc])
        p2 = float(m.pvalues[v]); b2 = float(m.params[v])
        if p1 < alpha and p2 < alpha:
            add({"type": "mediation", "cause": fc, "outcome": fo, "mediator": v,
                 "indirect_sign": "positive" if b1 * b2 > 0 else "negative",
                 "confidence": round(min(0.99, (1 - p1) * (1 - p2)), 3), "basis": ["data"],
                 "rationale": f"a={b1:.3f} (p={p1:.3g}), b={b2:.3f} (p={p2:.3g})"})
    claims = claims[:10] if len(claims) > 10 else claims
    return RunResult(design="mechanical", world_id=spec.world_id, final_claims=claims,
                     report={"theory_summary": "Mechanical OLS baseline (no language model).", "limitations": ""},
                     transcript=[], n_calls=0, total_tokens=0, wall_s=round(time.time() - t0, 1), code_runs=1,
                     code_failures=0)


def run_collective(design: OrgDesign, world: dict, backend: Backend, sandbox_dir: Path | None = None,
                   verbose: bool = False) -> RunResult:
    if not design.llm:
        r = run_mechanical(world)
        r.design = design.name
        return r
    return Collective(design, world, backend, sandbox_dir=sandbox_dir, verbose=verbose).run()
