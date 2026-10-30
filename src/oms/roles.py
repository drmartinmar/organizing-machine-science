"""Role prompts and output schemas for the members of a research collective.

Every role receives only the materials its organizational position entitles
it to see (``collective.py`` decides that).  Prompts are deliberately plain:
the testbed studies organizational design, so role instructions are held
constant across designs and no design-specific coaching is added.
"""
from __future__ import annotations

from .claims import claim_schema

CLAIM_RULES = """Rules for claims:
- Use the exact variable names from the codebook (snake_case). Never invent variables.
- type "effect": `sign` is "positive", "negative" or "none" (no causal effect). Leave moderator/mediator fields null.
- type "moderation": `moderator` names the moderating variable; `interaction_sign` says whether the effect of `cause` on
  `outcome` becomes more positive ("positive") or more negative ("negative") as the moderator increases.
- type "mediation": `mediator` names the mechanism variable; `indirect_sign` may be given or left null.
- `confidence` is your honest probability (0 to 1) that the claim is true in this setting. Do not inflate it.
- `basis` lists the evidence: "data" and/or "literature:L<k>" entries. Cite only literature IDs that actually exist in the brief
  and only for the relation that abstract is about.
- Prefer fewer, well-supported claims to many speculative ones (at most 10)."""


def theory_schema(var_names: list[str]) -> dict:
    s = claim_schema(var_names, max_claims=10)
    s["properties"]["proposed_tests"] = {"type": "array", "items": {"type": "string"}}
    s["required"] = ["theory_summary", "claims", "proposed_tests", "limitations"]
    return s


def analyst_code_schema() -> dict:
    return {"type": "object", "additionalProperties": False,
            "properties": {"plan": {"type": "string"}, "code": {"type": "string"}},
            "required": ["plan", "code"]}


def analyst_interpret_schema(var_names: list[str]) -> dict:
    finding = {"type": "object", "additionalProperties": False,
               "properties": {"claim_id": {"type": "string"},
                              "supported": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
                              "estimate": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                              "p_value": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                              "note": {"type": "string"}},
               "required": ["claim_id", "supported", "estimate", "p_value", "note"]}
    claims = claim_schema(var_names, max_claims=10)["properties"]["claims"]
    return {"type": "object", "additionalProperties": False,
            "properties": {"data_summary": {"type": "string"},
                           "findings": {"type": "array", "items": finding},
                           "claims": claims},
            "required": ["data_summary", "findings", "claims"]}


def critic_schema() -> dict:
    verdict = {"type": "object", "additionalProperties": False,
               "properties": {"claim_id": {"type": "string"},
                              "verdict": {"type": "string", "enum": ["accept", "revise", "reject"]},
                              "reason": {"type": "string"},
                              "suggested_confidence": {"anyOf": [{"type": "number"}, {"type": "null"}]}},
               "required": ["claim_id", "verdict", "reason", "suggested_confidence"]}
    return {"type": "object", "additionalProperties": False,
            "properties": {"verdicts": {"type": "array", "items": verdict},
                           "concerns": {"type": "string"},
                           "suggested_additional_analyses": {"type": "array", "items": {"type": "string"}}},
            "required": ["verdicts", "concerns", "suggested_additional_analyses"]}


def final_schema(var_names: list[str]) -> dict:
    return claim_schema(var_names, max_claims=10)


def solo_step1_schema(var_names: list[str]) -> dict:
    s = theory_schema(var_names)
    s["properties"]["code"] = {"type": "string"}
    s["required"] = s["required"] + ["code"]
    return s


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _materials(brief: str | None, codebook: str, data_preview: str | None) -> str:
    parts = []
    if brief:
        parts.append(brief)
    parts.append(codebook)
    if data_preview:
        parts.append("Data preview (first rows and summary statistics):\n```\n" + data_preview + "\n```")
    return "\n\n".join(parts)


def theorist_messages(brief: str, codebook: str, persona: str | None = None, prior_theory: dict | None = None,
                      data_findings: dict | None = None) -> list[dict]:
    system = ("You are the theorist of a research team in organization science. Your job is to propose the most "
              "plausible causal theory for the research question, stated as precise, testable claims, and to say "
              "which tests would discriminate between it and alternatives. Engage the prior literature critically: "
              "earlier findings may not hold in this setting. Return JSON only.\n\n" + CLAIM_RULES)
    if persona:
        system += f"\n\nEpistemic stance for this role: {persona}"
    user = _materials(brief, codebook, None)
    if data_findings is not None:
        user += ("\n\nThe team's analyst has already explored the data without reading the literature. Their report:\n"
                 f"```json\n{_j(data_findings)}\n```\nBuild a theory that explains these patterns; you may also "
                 "propose claims the analyst did not test.")
    if prior_theory is not None:
        user += ("\n\nA colleague on the team has already proposed the following theory. You may build on it, "
                 "refine it, or dissent from it; say which in theory_summary.\n"
                 f"```json\n{_j(prior_theory)}\n```")
    user += "\n\nReturn: theory_summary, claims, proposed_tests (what analyses would test the claims), limitations."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def analyst_code_messages(codebook: str, data_preview: str, hypotheses: list[dict] | None, brief_min: str,
                          error_feedback: str | None = None) -> list[dict]:
    system = ("You are the empirical analyst of a research team. You write a single self-contained Python script that "
              "reads `data.csv` (in the working directory) with pandas and tests the hypotheses you are given (or, if none "
              "are given, explores what determines the focal outcome). Use statsmodels (e.g. `statsmodels.formula.api`), "
              "numpy, pandas and scipy only. Think about confounding: include relevant controls and be explicit about "
              "which coefficients are total versus direct effects. For moderation use interaction terms; for mediation "
              "use the two-equation approach. Print compact, labeled results (coefficients, standard errors, p-values). "
              "No plotting, no file writing, no network. Keep the script under 120 lines. Return JSON with `plan` and `code`.")
    user = brief_min + "\n\n" + _materials(None, codebook, data_preview)
    if hypotheses:
        user += "\n\nHypotheses to test (from the theorist):\n```json\n" + _j(hypotheses) + "\n```"
    else:
        user += ("\n\nNo hypotheses are given. Explore the data to find what determines the focal outcome: main "
                 "effects with sensible controls, candidate moderators of the focal cause, and candidate mediators. "
                 "Report only what the data support.")
    if error_feedback:
        user += "\n\nYour previous script failed. Fix it. Error output:\n```\n" + error_feedback + "\n```"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def analyst_interpret_messages(codebook: str, hypotheses: list[dict] | None, plan: str, code: str, output: str,
                               brief_min: str) -> list[dict]:
    system = ("You are the empirical analyst of a research team. Interpret the output of the analysis you ran. "
              "For each hypothesis you were given, say whether the data support it (`supported` true/false, or null if "
              "untestable), with the key estimate and p-value. Then list the empirical claims the data warrant as "
              "structured claims with calibrated confidence and basis [\"data\"]. Flag confounding or sign changes "
              "between bivariate and controlled estimates. Return JSON only.\n\n" + CLAIM_RULES)
    user = brief_min + "\n\n" + codebook
    if hypotheses:
        user += "\n\nHypotheses tested:\n```json\n" + _j(hypotheses) + "\n```"
    user += f"\n\nAnalysis plan: {plan}\n\nScript:\n```python\n{code}\n```\n\nOutput:\n```\n{output}\n```"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def critic_messages(brief: str, codebook: str, claims: list[dict], evidence: str, binding: bool) -> list[dict]:
    system = ("You are the critic (referee) of a research team. Your job is adversarial: for each proposed claim, decide "
              "whether the evidence presented actually supports it in this setting. Check (1) whether a data analysis "
              "tested the claim at all, (2) confounding and alternative explanations given the variables in the codebook, "
              "(3) whether the claim merely restates prior literature that may not hold here, (4) whether the stated "
              "confidence is justified, and (5) whether literature IDs are cited correctly. Verdicts: accept, revise "
              "(fixable with a stated change), reject. Be specific and brief. Return JSON only.")
    system += ("\n\nYour verdicts are binding: rejected claims will be removed from the team's final report."
               if binding else
               "\n\nYour verdicts are advisory: the team lead will weigh them but may overrule you.")
    user = brief + "\n\n" + codebook + "\n\nProposed claims:\n```json\n" + _j(claims) + "\n```\n\nEvidence presented by the team:\n" + evidence
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def synthesizer_messages(brief: str, codebook: str, theory: dict | None, analysis: dict | None, critique: dict | None,
                         evaluation_rule: str, extra: str = "") -> list[dict]:
    system = ("You are the lead of a research team and write its final report: a short theory summary, a set of final "
              "causal claims with calibrated confidence and evidential basis, and limitations. Integrate the theorist's "
              "proposal, the analyst's evidence and (if present) the critic's review. Keep a claim only if you can defend "
              "it with the evidence in front of you; drop or re-sign claims the data contradict; lower confidence where "
              "support is thin. Return JSON only.\n\n" + CLAIM_RULES)
    if evaluation_rule == "hierarchy":
        system += ("\n\nGovernance: the critic has veto power. Claims the critic rejected must not appear in the final "
                   "report; claims marked 'revise' may appear only in the revised form the critic asked for.")
    elif evaluation_rule == "polyarchy":
        system += ("\n\nGovernance: the critic's review is advisory. You may keep a claim the critic rejected if you judge "
                   "the evidence sufficient; say why in the rationale.")
    user = brief + "\n\n" + codebook
    if theory is not None:
        user += "\n\nTheorist's proposal:\n```json\n" + _j(theory) + "\n```"
    if analysis is not None:
        user += "\n\nAnalyst's report:\n```json\n" + _j(analysis) + "\n```"
    if critique is not None:
        user += "\n\nCritic's review:\n```json\n" + _j(critique) + "\n```"
    if extra:
        user += "\n\n" + extra
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def solo_step1_messages(brief: str, codebook: str, data_preview: str) -> list[dict]:
    system = ("You are a solo researcher in organization science. In one pass: (a) propose a causal theory for the "
              "research question as structured claims, engaging the literature critically, and (b) write one "
              "self-contained Python script that reads `data.csv` with pandas and tests your claims with statsmodels "
              "(controls for confounding, interaction terms for moderation, two-equation mediation). Print compact "
              "labeled results. No plotting, file writing or network. Keep the script under 120 lines. Return JSON only.\n\n"
              + CLAIM_RULES)
    user = _materials(brief, codebook, data_preview) + "\n\nReturn: theory_summary, claims, proposed_tests, limitations, code."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def solo_step2_messages(brief: str, codebook: str, step1: dict, output: str) -> list[dict]:
    system = ("You are a solo researcher in organization science writing your final report. Revise your claims in light "
              "of the analysis output: drop or re-sign claims the data contradict, add claims the data clearly support, "
              "calibrate confidence honestly, and state the basis for each claim. Return JSON only.\n\n" + CLAIM_RULES)
    user = (brief + "\n\n" + codebook + "\n\nYour initial theory and script:\n```json\n" + _j(step1) +
            "\n```\n\nScript output:\n```\n" + output + "\n```")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _j(x) -> str:
    import json
    return json.dumps(x, indent=1, ensure_ascii=False)
