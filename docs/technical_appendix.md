---
title: "Technical Appendix: Organizing Machine Science"
subtitle: "A ground-truth testbed for the organizational design of AI research collectives"
date: "Anonymized for review"

---

# Technical Appendix

This appendix documents the prototype that accompanies the proposal: the world generator, the claim schema and scorer, the organizational designs, the model backends and reproducibility machinery, the pilot protocol and its results, the planned studies, and known limitations. Code, worlds, recorded model calls and results are in the repository `organizing-machine-science` (Python package `oms`; MIT license).

## A. Architecture

A run takes one *world* and one *organizational design* and returns a structured set of causal claims, which the scorer evaluates against the world’s hidden truth.

```
world bundle                       research collective (one design)              scoring (no model)
──────────────                     ─────────────────────────────────             ──────────────────
data.csv ─────────┐                ┌─ theorist ──┐                                claims ─┐
codebook.md ──────┼─► brief ──────►│  analyst ───┼──► lead ──► [critic] ──► final ───────┼─► exact metrics
literature (L1–L7)┘   (visible)    └─ sandbox ───┘      (draft)   (advisory / veto)      │   vs. truth.json
spec.json / truth.json  (hidden) ───────────────────────────────────────────────────────┘
```

Three properties matter for the science. (1) Nothing a collective sees reveals the truth: the brief, codebook, literature texts and dataset are the only inputs; `spec.json` and `truth.json` are used by the scorer alone. (2) Role prompts are held constant across designs; designs differ only in who exists, who sees what and when, who can veto, and which model each role runs on. (3) Scoring is deterministic and model-free.

## B. World generator

### B.1 Structural model

A world is a linear structural causal model with pairwise interaction terms over $K$ standardized constructs $X_1,\dots,X_K$ (here $K = 11$ or $12$). Variables are generated in topological order:

$$X_j \;=\; \sum_{i} \beta_{ji} X_i \;+\; \sum_{(a,m)} \gamma_{j,am}\, X_a X_m \;+\; \varepsilon_j, \qquad \varepsilon_j \sim \mathcal N(0, \sigma^2),$$

with $\sigma = 1$, exogenous variables consisting of noise only, and $N = 1{,}200$ units per world. Coefficient magnitudes are drawn from template-specific ranges with a seed derived from (template, variant, seed), so a world is fully reproducible from three identifiers. Data are exported as `data.csv` with a `unit_id` column; the codebook describes each variable as a standardized index with a realistic label (e.g., “Loss of team-specific procedural knowledge, from quarterly skills audits”).

### B.2 Causal quantities, estimand and truth

The scored estimand is the *local causal effect at the center of the distribution*: for a cause $x$ and outcome $y$, the derivative of $\mathbb{E}[y \mid do(x)]$ at $x = 0$ with every other variable held at its structural mean of zero; for a moderation claim about $(x, z)$ and outcome $y$, the mixed second derivative of $\mathbb{E}[y \mid do(x), do(z)]$ at zero. Both quantities are computed by deterministic forward simulation of the structural equations under interventions (noise terms at zero, incoming edges of intervened variables cut) with central differences; because the equations are polynomial with pairwise interactions, the differences are exact up to floating-point error. This oracle captures interactions that are specified directly, interactions that propagate through mediators, and interactions inherited from upstream causes (if $M = aX + \varepsilon_M$ and $Y = bM + \gamma MZ + \varepsilon_Y$, the effect of $X$ on $Y$ is moderated by $Z$ with coefficient $a\gamma$ although no $X \times Z$ term is specified). The earlier matrix formulas, $T = (I - B)^{-1} - I$ for linear path effects and coefficient propagation for directly specified interactions, remain in the code as a cross-check; the test suite verifies that both agree on all direct paths of the three templates and that only the simulation oracle recovers the inherited case.

The brief (world format 2) states the assumptions under which an adjusted regression identifies these quantities: causes precede effects within the observation window, every common cause of two codebook variables is itself in the codebook, and relations are approximately linear with pairwise interactions. It also states the relevance thresholds, so that a claim is a claim about a non-negligible effect. The truth table then contains:

* **Effects.** For every ordered pair $(x, y)$: the raw local effect and its sign at the relevance threshold ($|\cdot| \ge 0.10$; otherwise “none”).
* **Moderations.** For every unordered pair and outcome with a non-zero mixed effect: the raw value and its sign at the threshold ($|\cdot| \ge 0.08$).
* **Mediations.** Every direct two-edge chain $x \to m \to y$ with both legs non-zero, the sign of the indirect effect, the legs, and whether both legs meet the threshold ($|\beta| \ge 0.10$).
* **Focal truths.** The set a collective is expected to recover: the focal cause’s effect on the focal outcome; focal moderations at or above threshold; mediations through designated mediators with both legs at or above threshold and $|\beta_{mx}\beta_{ym}| \ge 0.05$; and edges the template marks as focal. Focal truths are the denominator for coverage. Their selection is a design choice of the template author and is published with each template.
* **Trap pairs.** Pairs with zero causal effect that are correlated through an observed common cause; the planted literature interprets the association causally.
* **Consensus claims.** The textbook claims about the focal relations; those that are false in a given world are the opportunities for a prior-conformity error.

Verdicts distinguish three cases: TRUE (asserted sign matches the truth at the threshold), WEAK (the asserted direction matches a structurally present effect below the threshold), and FALSE (wrong direction, asserted absence of a present effect, or asserted presence of a structurally absent relation). Precision is reported strictly (WEAK counts as not true) and leniently (WEAK counts as true), so threshold sensitivity is visible.

### B.3 Templates

Each template exists in an *orthodox* variant (textbook sign holds) and a *contrarian* variant (a different mechanism mix reverses the focal effect). The variable set is identical across variants, so the codebook does not reveal the variant.

| Template (unit) | Focal cause → outcome | Designated mediators | Moderators | Trap pair (common cause) | What flips in the contrarian variant |
|------------|------------------|------------------------|-----------------------|--------------------|------------------------|
| `turnover` (team-year) | team turnover → team performance | knowledge loss; idea novelty | routine codification; task interdependence; hiring quality | training investment → performance (budget slack) | Knowledge-loss path shrinks; idea-novelty path dominates; turnover × hiring quality becomes the live moderation; codification buffer becomes negligible |
| `monitoring` (unit-year) | monitoring intensity → creative output | perceived autonomy; trust in management; feedback frequency | feedback quality | wellness program → creative output (unit budget) | Autonomy and trust paths shrink; feedback-frequency path dominates; monitoring is also confounded upward by technology investment in both variants |
| `decentralization` (unit-year) | decision decentralization → unit performance | local knowledge use; coordination cost | environmental turbulence; IT integration | formal planning hours → performance (HQ attention) | Coordination-cost path dominates; decentralization × turbulence turns negative; HQ attention confounds decentralization downward in both variants |

Each world also contains at least one *unpublished* focal truth (a true mechanism that no abstract mentions), which defines the discovery metric.

### B.4 Planted literature

Each world carries seven abstracts, L1–L7, built from a fixed slate of claims rendered into prose with fictitious sample descriptions and effect sizes consistent with the claimed sign. The slate is: the textbook main effect (L1); one mechanism leg (L2); a published moderation or mediation (L3); the trap association presented as causal (L4); a peripheral true effect (L5); a true null (L6); another peripheral effect (L7). Each abstract states the proposition it is scored on explicitly (world format 2 adds a sentence such as “The authors interpret this as a causal effect …” or “The authors conclude that … has no effect …”; the pilot’s format-1 abstracts reported associations and recommendations only). The status of every abstract is *computed* by evaluating its proposition against the world’s truth table, so the same slate yields L1 = TRUE in orthodox worlds and L1 = FALSE in contrarian worlds. Because the abstracts describe other settings, a FALSE status means that the proposition does not hold in the focal world, not that the fictitious original study was wrong; what the metrics capture is whether a collective transports a claim uncritically. Collectives see only the abstract IDs and texts (`literature_public.json`); the scorer sees the propositions and statuses.

### B.5 Example: the `turnover-contrarian-s1` world as the collective sees it

*Research question (from the brief).* What determines team performance in this firm, and in particular how does team turnover affect team performance, through which mechanisms, and under what conditions?

*Literature available to the collective* (format 1, as used in the pilot; the status column is hidden from it):

| ID | Abstract (as shown) | Truth in this world |
|--------|---------------------------------------------------------------------------------|-------------------------------|
| L1 | Panel of 212 manufacturing teams over four years. Higher share of team members who left and were replaced during the year was associated with lower supervisor-rated team performance against annual targets (standardized b = -0.15, p < .01). The authors attribute the pattern to the loss of tacit, team-specific knowledge. | FALSE |
| L2 | Field study of 96 software teams with quarterly skills audits. Higher share of team members who left and were replaced during the year was associated with higher loss of team-specific procedural knowledge, from quarterly skills audits (standardized b = +0.24, p < .01). | TRUE |
| L3 | Survey of 340 service teams in two retail chains. The association between share of team members who left and were replaced during the year and supervisor-rated team performance against annual targets was more positive when degree to which the team's work procedures are documented in written routines was high (interaction b = +0.34, p < .05). Documented routines are argued to buffer teams against the disruption of member exit. | WEAK (right direction, below threshold) |
| L4 | Cross-sectional study of 1,105 teams in a logistics firm. Higher hours of formal training purchased for the team was associated with higher supervisor-rated team performance against annual targets (standardized b = +0.21, p < .01). The authors recommend expanding formal training budgets. | FALSE (confounded trap) |
| L5 | Two-wave survey of 180 hospital units. Higher average weekly workload per member relative to the firm norm was associated with lower supervisor-rated team performance against annual targets (standardized b = -0.24, p < .01). | TRUE |
| L6 | Meta-analytic summary of 41 team studies. Units with higher number of team members showed no significant difference in supervisor-rated team performance against annual targets (standardized b = +0.03, n.s.). | TRUE |
| L7 | Archival study of 2,300 hires in a professional services firm. Higher quality of replacement hires, from structured assessment scores at entry was associated with higher supervisor-rated team performance against annual targets (standardized b = +0.17, p < .01). | TRUE |

*Focal truths the scorer expects* (none of the positive ones appears in the literature; L1 asserts the opposite sign; format-2 briefs add the identification assumptions and relevance thresholds, and format-2 abstracts state their causal interpretation explicitly):

- effect: `team_turnover` → `team_performance` is **positive** (total effect +0.25)
- moderation: the effect of `team_turnover` on `team_performance` becomes more **positive** as `hiring_quality` rises (total interaction +0.13)
- mediation: `team_turnover` → `idea_novelty` → `team_performance` (indirect effect +0.28)
- effect: `team_turnover` → `idea_novelty` is **positive** (total effect +0.64)
- effect: `idea_novelty` → `team_performance` is **positive** (total effect +0.43)

In the orthodox twin of this world the same codebook and the same seven abstracts appear, but L1 and L3 are true, the knowledge-loss path carries the effect, and the undiscovered truth is the task-interdependence moderation.

## C. Claim schema and scoring

### C.1 Schema

The final report is a JSON object with `theory_summary`, `limitations` and up to ten `claims`. Each claim has `type` (effect, moderation, mediation), `cause`, `outcome`, `sign` (effect), `moderator` and `interaction_sign` (moderation), `mediator` and optional `indirect_sign` (mediation), `confidence` in $[0, 1]$, `basis` (a list such as `["data", "literature:L3"]`) and a free-text `rationale`. Variable fields are enumerated from the codebook in the JSON schema, so model outputs cannot name variables that do not exist. Claims that fail normalization (unknown variable, missing sign, cause equal to outcome) are dropped before scoring and counted in the transcript.

### C.2 Metrics (per run)

Let $C$ be the set of final claims after normalization, $R$ the number of claims in the final model output before normalization, $F$ the set of focal truths and $U \subseteq F$ the unpublished focal truths. The metrics use retrieval terminology; the Sah–Stiglitz language of acceptance and rejection errors is an analogy that applies exactly only to the AND/OR designs, where a fixed candidate set is evaluated.

| Metric | Definition | Reading |
|---|---|---|
| `n_claims`, `n_raw_claims`, `n_dropped_claims`, `empty_report` | reported claims; claims before normalization; claims dropped as malformed; whether the report was empty | abstention and malformed-output accounting |
| `precision` | share of $C$ that is TRUE (WEAK counts as not true) | $1 -$ false-discovery proportion among reported claims, strict |
| `precision_lenient` | share of $C$ that is TRUE or WEAK | threshold sensitivity |
| `n_false`, `false_claim_rate` | FALSE claims and their share of $C$ | |
| `focal_recall` (coverage) | share of $F$ matched by a TRUE claim | retrieval of the designated mechanisms |
| `discovery_rate` (recovery of unpublished truths) | share of $U$ recovered | benchmark-relative novelty, not substantive novelty |
| `parroting_rate` (literature overlap) | share of $C$ that restates an abstract’s proposition | agreement with the literature, warranted or not |
| `consensus_conformity` | share of the textbook claims that are FALSE in this world which the collective asserted | prior-conformity error over its opportunities |
| `n_textbook_assertions` | claims matching any textbook claim, true or false | |
| `trap_rate` | share of $C$ asserting a non-null effect on a trap pair | confounding error |
| `confident_false_rate` | share of $C$ that is FALSE with confidence $\ge 0.7$ | one failure dimension of slop, not an exhaustive definition |
| `brier` | mean of $(\text{confidence} - \mathbb 1[\text{TRUE}])^2$ over submitted claims | a probability score on self-selected propositions; reliability by confidence level is reported where claim counts allow |
| `citation_errors` | literature IDs cited that do not exist or share fewer than two variables with the claim | identifier validity and topical relevance only; evidential use is not checked |
| `n_calls`, `total_tokens`, `wall_s` | model calls, tokens, wall-clock seconds | cost |

All metrics are computed by `oms.scoring` from the final claims and the hidden truth; no language model is involved.

## D. Organizational designs

### D.1 Roles

Four role prompts are used, held constant across designs (`oms.roles`): a **theorist** (proposes a causal theory as structured claims and the tests that would discriminate it from alternatives; instructed to engage the literature critically), an **analyst** (writes one self-contained Python script that is executed against `data.csv` in the sandbox, then interprets the output into findings and data-based claims), a **critic** (adversarial referee: did an analysis test the claim; is confounding addressed given the codebook; does the claim merely restate literature; is confidence justified; are citations correct), and a **lead** (writes the final report from the materials in front of it). A **solo** prompt combines theorist and analyst in one agent. Role prompts contain no information about the world beyond the brief and codebook and no coaching specific to any design.

### D.2 Design levers and their operationalization

| Lever | Values | Operationalization |
|----------------------|----------------------------------------|----------------------------------------------------------|
| Division of labor | `solo`; `pipeline`; `two_theorists` | solo: one agent proposes claims and code, then revises after seeing output. pipeline: theorist → analyst (code, execution, interpretation) → lead. two_theorists: two theorists with distinct epistemic lenses (mechanism-focused; contingency-focused) feed a shared analyst and lead. |
| Sequencing | `theory_first`; `data_first` | data_first: the analyst explores the data with no hypotheses and no access to the literature; the theorist then explains the analyst’s findings with the literature. |
| Evaluation architecture | `none`; `polyarchy` (advisory); `hierarchy` (veto, revisions allowed); `and`; `or` | The lead writes a draft. With a critic, the critic reviews the draft with the full evidence (plan, script, output, findings) and returns accept / revise / reject per claim; the lead then writes the final report. `polyarchy`: verdicts are advisory and the lead is told so (an advisory arrangement, not a Sah–Stiglitz polyarchy). `hierarchy`: verdicts are binding; the harness keeps final claims about relations the critic accepted *or asked to revise*, without checking the revision (the pilot rule; it lets revise verdicts pass). `and`: a claim survives only if the lead kept it and the critic accepted that same claim, sign included (strict hierarchy). `or`: a draft claim survives if either the lead kept it or the critic accepted it (polyarchy). |
| Heterogeneity | same model; different model for the critic | the critic role is routed to a second model family. Model identity is a crude proxy for error dependence: it also changes capability, conservatism and evaluation norms. Study 1 uses reciprocal assignments (each family as generator and as critic) and holds the critic’s instructions constant so that norm differences can be separated from dependence. |
| Proposal exposure | `connected`; `isolated` (two_theorists) | connected: the second theorist sees the first theorist’s proposal and may build on it or dissent. isolated: both propose independently and are merged only by the analyst and lead. This is a single directed exposure between two proposal generators, not a network: it tests sequential influence on proposal diversity, and the richer network mechanisms of the cited work (repeated search, diffusion, time-dependent convergence) are not instantiated. |

The mapping to theory: the `and` and `or` rules operationalize Sah and Stiglitz’s contrast between a hierarchy (a project must pass every evaluator) and a polyarchy (one acceptance suffices) on a fixed candidate set; the advisory and veto-with-revision arrangements are additional governance forms in which review changes claim generation; the heterogeneity lever targets the assumption that evaluators’ errors are imperfectly correlated; the exposure lever operationalizes sequential influence on proposal diversity, in the spirit of the network results of Lazer and Friedman and Fang, Lee and Schilling but without their dynamics; the sequencing lever operationalizes theory-driven versus phenomenon-driven discovery and targets conformity to priors.

### D.3 Designs in the pilot

| Design | Structure | Sequence | Evaluation | Critic model | Model calls per run |
|-------------------------|-------------------------|-----------|---------------|---------------|----------------------------|
| `mechanical` | fixed statistical procedure | – | – | – | 0 |
| `solo` | solo | – | none | – | 2 (3 if the script fails once) |
| `pipeline` | pipeline | theory-first | none | – | 4 (5) |
| `pipeline_polyarchy` | pipeline | theory-first | advisory critic | same | 6 (7) |
| `pipeline_hierarchy` | pipeline | theory-first | veto critic, revisions allowed | same | 6 (7) |
| `pipeline_and` (Study 1) | pipeline | theory-first | strict AND rule | same | 6 (7) |
| `pipeline_or` (Study 1) | pipeline | theory-first | OR rule | same | 6 (7) |
| `pipeline_hierarchy_hetero` | pipeline | theory-first | veto critic, revisions allowed | different family | 6 (7) |
| `datafirst_hierarchy` | pipeline | data-first | veto critic, revisions allowed | same | 6 (7) |
| `two_theorists_connected` | two theorists | theory-first | veto critic, revisions allowed | same | 7 (8) |
| `two_theorists_isolated` | two theorists | theory-first | veto critic, revisions allowed | same | 7 (8) |

The **mechanical baseline** is a deliberately naive reference procedure that knows only the focal cause and outcome named in the brief: ordinary least squares of the outcome on all other variables (reporting significant coefficients as effect claims at $\alpha = 0.01$), interactions of the focal cause with every other variable (moderation claims) without multiplicity adjustment, and two-equation mediation screens (mediation claims), with confidence $1 - p$, which is not a probability that the claim is true. It exists to show that the scorer flags known statistical mistakes (conditioning on mediators turns a real effect into a “none” claim; unadjusted screening produces spurious interactions) and to mark the number of claims a procedure without a reporting filter makes. It cannot isolate the value of theorizing, organization or models; competent baselines matched to the declared estimand (total-effect regressions with pre-treatment adjustment sets, with and without oracle knowledge of the adjustment set) are planned for Study 1.

### D.4 Sandbox

Analyst and solo scripts run in a subprocess in a scratch directory containing only `data.csv`, with Python’s isolated mode, a wall-clock timeout of 120 seconds, a stripped environment, and a preamble that pre-loads the scientific stack and blocks the analysis script from importing networking, subprocess, filesystem and process-control modules. This is containment for cooperative agents, not a security boundary against adversarial code; a container should be used for untrusted models. Script failures are fed back to the analyst once; a second failure is reported to the interpreting step as a failed script and recorded.

## E. Model backends and reproducibility

`oms.llm` provides three backends behind one interface: any OpenAI-compatible chat endpoint (OpenAI, OpenRouter, vLLM, Ollama, LM Studio), the OpenAI Codex command-line interface used as a stateless completion engine with JSON-schema-enforced output, and a deterministic mock used by the tests. A caching wrapper records every request (messages, schema, model, temperature) and response under a SHA-256 content key in `llm_cache.jsonl`. In `replay` mode the cache is the only source of responses and a miss is an error, so a published run reproduces exactly from the repository with no model access: `oms run configs/pilot_codex.yaml --mode replay`. Worlds are regenerated deterministically from (template, variant, seed). Per-run transcripts (`runs/<experiment>/transcripts/*.json`) contain every prompt, every parsed response, the executed script and its output, the critic’s verdicts, the draft and final claims, and the metrics.

The pilot used GPT-6 Astra (reasoning effort “medium”) for all roles and GPT-5.6 Terra as the heterogeneous critic, both through the Codex command-line interface, because that was the model access available to the author. Other researchers can reproduce the pilot from the cache and re-run it live on any of the supported endpoints.

## F. Pilot protocol and results

### F.1 Protocol

Nine designs (Table D.3) on six worlds (three templates, two variants, seed 1), one run per cell, six runs in parallel. Each collective received identical materials. All runs, including failures, are recorded; scoring is from final claims only.

### F.2 Results

Fifty-four runs completed (264 model calls, about 4.9 million tokens including reasoning tokens; one run failed on a model-capacity error and was re-run from the same prompts). The pilot used world format 1 (associational abstracts, no identification note in the brief) and the `polyarchy` (advisory) and `hierarchy` (veto, revisions allowed) governance rules; the scores below were recomputed with the current oracle and verdict rules from the stored claims, which never change. Tables F.1a and F.1b report means per run across the six worlds with standard errors across worlds, and error and abstention counts; Table F.2 splits by variant. Precision is conditional on reporting: four of the six reports of the cross-model veto design and one report of the exposed two-theorist design were empty, and their precision averages over the remaining reports. Figures F.1–F.3 (in `results/pilot_codex/`) plot precision against coverage, the confident-false and conformity rates, and recovery and the probability score.

**Table F.1a.** Pilot means per run (six worlds, one seed); standard errors across worlds in parentheses.

| Design | Claims | Empty reports | Precision, strict (SE) | Precision, lenient | Coverage (SE) | Recovery (SE) | Literature overlap | Brier |
|--------------------------------|------|------|------------|------|------------|------------|------|------|
| naive reference (no model) | 9.5 | 0 | 0.77 (0.04) | 0.86 | 0.51 (0.04) | 0.68 (0.10) | 0.20 | 0.16 |
| solo | 6.7 | 0 | 1.00 (0.00) | 1.00 | 0.66 (0.08) | 0.56 (0.09) | 0.56 | 0.06 |
| pipeline, no review | 6.3 | 0 | 1.00 (0.00) | 1.00 | 0.56 (0.08) | 0.40 (0.08) | 0.67 | 0.10 |
| pipeline, advisory critic | 6.0 | 0 | 1.00 (0.00) | 1.00 | 0.52 (0.08) | 0.33 (0.10) | 0.72 | 0.19 |
| pipeline, veto critic (rev.) | 5.7 | 0 | 1.00 (0.00) | 1.00 | 0.48 (0.09) | 0.33 (0.10) | 0.72 | 0.22 |
| pipeline, veto critic (other family) | 1.2 | 4 | 1.00 (0.00) | 1.00 | 0.11 (0.11) | 0.06 (0.06) | 0.92 | 0.28 |
| data-first, veto critic | 5.8 | 0 | 0.95 (0.03) | 1.00 | 0.57 (0.06) | 0.58 (0.07) | 0.35 | 0.25 |
| two theorists, exposed | 5.7 | 1 | 1.00 (0.00) | 1.00 | 0.52 (0.12) | 0.39 (0.11) | 0.63 | 0.24 |
| two theorists, unexposed | 5.3 | 0 | 1.00 (0.00) | 1.00 | 0.47 (0.10) | 0.31 (0.11) | 0.75 | 0.22 |

**Table F.1b.** Error, abstention and cost counts (sums over the six worlds; cost per run).

| Design | False claims (sum) | Below-threshold claims (sum) | Confident-false (sum) | Dropped as malformed (sum) | Focal misses (sum) | Citation errors | Calls | Tokens | Wall s |
|--------------------------------|------|------|------|------|------|------|------|------|------|
| naive reference (no model) | 8 | 5 | 2 | 0 | 19 | 0.0 | 0 | 0k | 2 |
| solo | 0 | 0 | 0 | 0 | 13 | 0.0 | 2 | 39k | 157 |
| pipeline, no review | 0 | 0 | 0 | 0 | 17 | 0.0 | 4 | 80k | 220 |
| pipeline, advisory critic | 0 | 0 | 0 | 0 | 19 | 0.0 | 6 | 109k | 132 |
| pipeline, veto critic (rev.) | 0 | 0 | 0 | 0 | 21 | 0.0 | 6 | 120k | 138 |
| pipeline, veto critic (other family) | 0 | 0 | 0 | 0 | 36 | 0.0 | 6 | 121k | 71 |
| data-first, veto critic | 0 | 2 | 0 | 0 | 18 | 0.0 | 6 | 107k | 366 |
| two theorists, exposed | 0 | 0 | 0 | 0 | 18 | 0.0 | 7 | 121k | 322 |
| two theorists, unexposed | 0 | 0 | 0 | 0 | 21 | 0.0 | 7 | 125k | 382 |

**Table F.2.** Means by design and world variant (three worlds each). The prior-conformity error is computed over the textbook claims that are false in the world (one to two per contrarian world; none in orthodox worlds).

| Design | Variant | Claims | Precision | Coverage | Recovery | Prior-conformity error | Textbook assertions | Literature overlap |
|----------------------------|----------|------|------|------|------|------|------|------|
| naive reference (no model) | orthodox | 9.7 | 0.69 | 0.56 | 0.87 | – | 0.7 | 0.21 |
| naive reference (no model) | contrarian | 9.3 | 0.86 | 0.46 | 0.49 | 0.00 | 0.3 | 0.18 |
| solo | orthodox | 6.7 | 1.00 | 0.74 | 0.56 | – | 2.0 | 0.67 |
| solo | contrarian | 6.7 | 1.00 | 0.57 | 0.56 | 0.00 | 0.3 | 0.45 |
| pipeline, no review | orthodox | 6.3 | 1.00 | 0.61 | 0.31 | – | 2.0 | 0.79 |
| pipeline, no review | contrarian | 6.3 | 1.00 | 0.50 | 0.49 | 0.00 | 0.3 | 0.55 |
| pipeline, advisory critic | orthodox | 5.7 | 1.00 | 0.54 | 0.18 | – | 2.0 | 0.89 |
| pipeline, advisory critic | contrarian | 6.3 | 1.00 | 0.50 | 0.49 | 0.00 | 0.3 | 0.55 |
| pipeline, veto critic (rev.) | orthodox | 5.0 | 1.00 | 0.46 | 0.18 | – | 1.7 | 0.89 |
| pipeline, veto critic (rev.) | contrarian | 6.3 | 1.00 | 0.50 | 0.49 | 0.00 | 0.3 | 0.55 |
| pipeline, veto critic (other family) | orthodox | 2.3 | 1.00 | 0.22 | 0.11 | – | 0.7 | 0.92 |
| pipeline, veto critic (other family) | contrarian | 0.0 | – | 0.00 | 0.00 | 0.00 | 0.0 | – |
| data-first, veto critic | orthodox | 5.7 | 0.90 | 0.50 | 0.49 | – | 1.7 | 0.44 |
| data-first, veto critic | contrarian | 6.0 | 1.00 | 0.64 | 0.68 | 0.00 | 0.3 | 0.25 |
| two theorists, exposed | orthodox | 6.7 | 1.00 | 0.67 | 0.42 | – | 2.0 | 0.75 |
| two theorists, exposed | contrarian | 4.7 | 1.00 | 0.37 | 0.36 | 0.00 | 0.0 | 0.44 |
| two theorists, unexposed | orthodox | 6.3 | 1.00 | 0.62 | 0.36 | – | 2.0 | 0.81 |
| two theorists, unexposed | contrarian | 4.3 | 1.00 | 0.31 | 0.27 | 0.00 | 0.3 | 0.70 |

![Figure F.1. Precision against coverage by design (small points: individual worlds; large points: means with standard errors).](../results/pilot_codex/fig1_validity_frontier.png)

![Figure F.2. Confident-false rate (all worlds) and prior-conformity error (contrarian worlds) by design.](../results/pilot_codex/fig2_slop_and_conformity.png)

![Figure F.3. Recovery of unpublished focal truths and Brier score by design.](../results/pilot_codex/fig3_discovery_calibration.png)

**What the pilot shows, hypothesis by hypothesis.**

*False claims did not occur in model-based designs.* The eight model-based designs made 256 claims: 0 FALSE, 2 WEAK (both mediation claims from `datafirst_hierarchy`, through idea novelty in `turnover-orthodox-s1` and through feedback frequency in `monitoring-orthodox-s1`, chains whose second leg is between 0.05 and 0.09, below the 0.10 relevance threshold), none on a trap pair, none miscited, and none dropped as malformed. Of the 32 opportunities to assert a textbook claim that was false in a contrarian world, none was taken; collectives did assert textbook claims that were true (Table F.2, textbook assertions), which earlier drafts of this appendix had mislabeled as conformity. The naive reference procedure made 8 FALSE and 5 WEAK claims in 57, including declaring the focal effect absent after conditioning on its mediators; its trap rate was zero because the common cause is in the regression.

*H1 (evaluation architecture).* The pilot ran the advisory and veto-with-revision arrangements, not the AND and OR rules, and no false claims were available for review to remove, so the predicted reduction in false claims was untestable. The cost side appeared: coverage fell from 0.56 (no review) to 0.52 (advisory) to 0.48 (veto), recovery from 0.40 to 0.33 to 0.33, and the probability score worsened from 0.10 to 0.19 to 0.22 because the lead lowered the confidence of claims the critic had questioned (the collectives were underconfident: mean confidence minus precision was negative for every design). In Sah and Stiglitz’s analysis, whether review pays depends on the quality of the candidate portfolio together with reviewer discrimination, error dependence and costs; these worlds supply a portfolio in which every candidate was good.

*H2 (heterogeneity).* Untested for the same reason, and the cross-model condition is confounded by a difference in evaluation norms. The GPT-5.6 Terra critic classified the cross-sectional regressions as “adjusted associations, not causal effects” in every world, asked for almost every claim to be “recast as an association” (32 revise and 6 reject verdicts, no accepts) and rejected mediation claims. That objection is reasonable in general and unwarranted in these worlds, where the common causes are observed; the brief did not say so. The schema had no association type, so the lead could not comply and dropped the claims: final reports were empty in four worlds, one claim in a fifth, six in the sixth. The same-model critic accepted or rejected on the evidence presented and left 3–7 claims per world. The repairs are a brief that states the identification assumptions (format 2), the strict AND and OR rules, a planned `association` and `cannot_identify` claim type with scoring rules for warranted abstention, and reciprocal critic assignments with constant critic instructions in Study 1.

*H3 (proposal exposure).* Not supported. Unexposed theorists recovered fewer unpublished mechanisms than exposed ones (0.31 against 0.39) and overlapped more with the literature (0.75 against 0.63); the differences are within one standard error. In the transcripts the two independent proposals overlap heavily and the shared analyst tests the union, so unexposed generation bought little diversity. Role order was not counterbalanced.

*H4 (sequencing).* The stated predictions (fewer prior-conformity errors, more trap errors) were not testable: both error types were zero in every design. Exploratory findings: `datafirst_hierarchy` had the highest recovery among reviewed designs (0.58 against 0.33 for its theory-first twin), the lowest literature overlap (0.35 against 0.72) and the highest coverage in contrarian worlds (0.64); its two WEAK claims were the only imperfections.

*Division of labor.* The solo generalist had the highest coverage (0.66), the best probability score (0.06) and the lowest cost (two calls); its recovery (0.56) was second to data-first (0.58). Pipelines lost information at handoffs: theorists proposed claims the analyst did not test, analysts found patterns the lead did not report, and critics removed claims the data supported. The comparison is at native resources; matched-resource comparisons are planned.

*Cost.* Model-based runs used two to eight calls and 40,000–125,000 tokens each (reasoning included); wall time per run was 1–7 minutes with six runs in parallel.

**Table F.3.** The cross-model critic’s verdicts (pipeline, veto critic from another model family), counted over the six worlds.

| Verdict | Count | Typical reason (quoted from transcripts) |
|---|---|---|
| accept | 0 | – |
| revise | 32 | “supports a positive adjusted association, not a causal effect”; “recast as an association” |
| reject | 6 | “a product-of-coefficients estimate … does not establish mediation” |

### F.3 Reading the pilot

The pilot is a single-seed, six-world instrument check. It establishes that (1) the metrics discriminate between designs that differ only in organization while the model is held constant (coverage 0.47–0.66 among same-model designs; 0.11 with the cross-model veto critic); (2) the metrics behave as designed, including on the naive reference procedure, whose known mistakes the scorer flags; (3) the record/replay pipeline reproduces results exactly; and (4) with a frontier model in easy worlds, false claims and prior conformity did not occur, so the binding constraint on these collectives was what they failed to report, not what they wrongly reported. It also found two flaws in the instrument (an unstated identification standard and a leaky veto rule), which is what a pilot of an instrument is for. Standard errors across six worlds are wide; the pilot motivates the pre-registered factorial in Study 1 and the difficulty ladder in Study 2 and does not estimate the effects in H1–H4.

## G. Planned studies

**Study 1 (full design).** The levers are nested, so the design is not a full factorial. Valid cells: solo (1); pipeline with no review in theory-first and data-first sequencing (2); pipeline with four review rules (advisory, veto with revision, AND, OR) in two sequencings and two critic models (16); two theorists, exposed or unexposed, with no review or the AND rule, same-model critic (4): 23 cells, of which 21 are retained after dropping the two redundant data-first/no-critic-model combinations. Sampling hierarchy: three templates × two variants (fixed) × five world-parameter seeds (each with its own dataset draw) × two live model replicates per cell, with the replicate index included in the request so that the cache does not return a stored answer. That is about 1,300 runs per model family. Three families (two commercial, one open-weights) each serve as generator and, reciprocally, as critic, with the critic’s instructions held constant. Budget: at the pilot’s ~100,000 tokens per run, on the order of 1.3 × 10^8 tokens per family and 4 × 10^8 in total, plus 20% for robustness runs; at current list prices for frontier models this is in the low thousands of US dollars per family, and the open-weights family runs on rented GPUs. Analyses are pre-registered: mixed-effects models of each metric on design contrasts with random effects for template, world and replicate; primary outcomes are the false-claim proportion and coverage (H1, H2), proposal diversity and recovery (H3), and prior-conformity and trap errors (H4); error counts are analyzed with their denominators (claims reported, opportunities available). Robustness: paraphrased role prompts, three held-out templates written after the designs are frozen, and matched-resource comparisons (equal call budgets) for the division-of-labor contrast. Minimum publishable deliverable: Study 1 on one family with the repaired instrument.

**Study 2 (difficulty ladder).** Generator extensions, each with a known answer and a declared estimand: nonlinear and threshold effects; panel structure with unit fixed effects and time shocks; unobserved confounding and observationally equivalent worlds, where the warranted answer is a `cannot_identify` claim and the scorer rewards it; measurement error; selection into the sample; and larger variable sets with irrelevant variables. Worlds are graded by the identification strategy they require, and designs are compared on how gracefully they degrade. This is the regime in which false claims occur and in which H1 and H2 receive their real test.

**Study 3 (transfer).** (a) Experiment-benchmarked observational tasks: the collective receives the observational portion of a dataset for which an experimental or quasi-experimental estimate exists; the score carries the reference estimate’s uncertainty and any estimand difference (population, intervention, horizon) explicitly, so that disagreement is a graded distance rather than an error label. (b) Time-split rediscovery: the literature as it stood before a now-established finding, with recall probes administered in separate sessions to each model and treated as imperfect diagnostics; training-cutoff claims are verified against vendor documentation. These studies test transfer; they do not inherit the synthetic benchmark’s exact-truth language.

**Study 4 (human and machine research organizations on one benchmark).** Doctoral-student teams (individuals, teams, and teams with an AI assistant) work the same worlds under the same brief and submit claims through the same schema. Participants are told that the abstracts are synthetic and that the worlds are simulated, so no deception is involved; sessions are ninety minutes with the same notebook environment and time budget across conditions; assignment of worlds is randomized; compensation and consent follow the ethics board’s requirements. The comparison is of error profiles under stated resources, not of unconditioned ability.

**Infrastructure.** The package scores any claim set in its ontology against any world (`oms evaluate`). Integration with an independently built research loop, including a documented account of what free-form output loses in conversion to the schema, is a Stage-2 deliverable, and public execution of external code will use container isolation rather than the current subprocess sandbox.

## H. Ethics, misuse and footprint

Studies 1–2 involve no human subjects and no personal data; all data are synthetic. Study 3 uses existing public datasets under their licenses, with provenance, identifiability and review status documented per dataset before use. Study 4 will be reviewed by the authors’ institutional ethics board, with informed consent, disclosure that the materials are synthetic, and no deception. The main misuse risk is that the instrument is used to tune collectives for persuasive false claims; we release the detection metrics with the generator and publish error profiles for every configuration we recommend. Compute footprint is modest and is reported per experiment in tokens.

## I. Known limitations of the prototype

* Worlds are linear-Gaussian with pairwise interactions, observed confounding only, and cross-sectional structure. They are intentionally easy; Study 2 addresses difficulty, and observationally equivalent worlds are needed before “warranted abstention” can be scored.
* Scoring is sign-based at declared relevance thresholds; magnitudes are not rewarded, and mediation truths are restricted to direct two-edge chains. The threshold sensitivity is visible through strict and lenient precision but has not been studied systematically.
* The claim schema admits only causal claim types (effect, moderation, mediation). A collective that wants to report an association, or to say that an effect cannot be identified from the data, has no legitimate way to do so; the pilot shows that this interacts with the veto rule (Section F.2, H2). `association` and `cannot_identify` types, with scoring rules, are the first planned schema change.
* The pilot’s `hierarchy` rule kept claims the critic marked “revise” without checking that the revision was made. The AND and OR rules now implement the strict decision rules; the pilot results are reported under the rule that generated them.
* Three templates and seven abstracts per world limit the variety of traps and discovery targets; focal truths and the literature slate are author choices, published with each template, and sensitivity to alternative slates is planned.
* The pilot’s heterogeneous critic is a sibling model from the same vendor and differs from the base model in evaluation norms as well as in errors; cross-vendor, reciprocal assignments with constant critic instructions are planned.
* The Codex backend flattens system and user messages into one prompt and does not expose sampling temperature; the OpenAI-compatible backend passes messages natively. Backend is therefore an experimental condition to be reported, not a nuisance.
* Replay reproduces recorded model answers exactly; computational reproduction of the analyses additionally depends on the pinned environment (`requirements-lock.txt`) and on the sandbox’s output capture; fresh replication requires live model access and will differ.
* Role prompts, although constant across designs, are a single operationalization; paraphrase robustness is planned.

## J. Use of AI

The authors designed the research question, theory, hypotheses, testbed architecture, metrics and both documents, and take responsibility for all content. AI coding and writing assistants (Claude and GPT-family models, October 2026) were used extensively under the authors’ direction to implement the prototype, run the pilot, verify references and polish language. Before submission, a separate model (GPT-6 Astra, reasoning effort “ultra”) reviewed the proposal, this appendix and the pilot tables from a referee’s perspective; Section K lists the objections that were checked and led to changes.

## K. What an adversarial model review changed

The review returned twenty-one objections. Those that survived checking against the code and the transcripts were: (1) the truth formulas were not a general oracle for the advertised model class (inherited moderation was missed); replaced by the intervention-based oracle in B.2, with tests. (2) Sub-threshold effects were scored as false; replaced by the WEAK verdict and strict/lenient precision. (3) “Consensus conformity” counted assertions of textbook claims that were true in the world; replaced by the prior-conformity error over false textbook claims, which is zero in the pilot. (4) The advisory arrangement is not a Sah–Stiglitz polyarchy and the veto rule let “revise” verdicts pass; AND and OR rules added, pilot designs relabeled. (5) The brief did not state identification assumptions or relevance thresholds, so the cross-model critic’s demand for associational claims could not be adjudicated; the format-2 brief states both, and the pilot’s “paralysis” is reported as a norm conflict the instrument failed to resolve. (6) Several narrative statements contradicted the tables (a six-fold “Type II” range, a coverage range that mixed model compositions, which design had the highest recovery); corrected. (7) Type I/Type II labels, Brier as calibration, citation checks as fidelity, “discovery” as novelty, replay as full reproducibility, and the pre-deployment-standard claim were overstated; relabeled or qualified throughout. (8) The factorial, replication units, cache behavior, budget and the ethics statement for Study 3 were underspecified; specified in G and H. Objections not adopted: that a frontier-model collective asserting the sign in the data over the textbook sign is uninformative because it may reflect pretraining rather than the abstracts (we agree the mechanism is not identified and add literature-free and neutral-label conditions to Study 1, but the absence of prior-conformity errors remains a measured property of the collective), and that recovery of designated mechanisms should not be reported at all (it is reported as benchmark-relative recovery, not as novelty).

## L. Repository map

| Path | Contents |
|-----------------------------------------------------|-------------------------------------------------------------------|
| `src/oms/worlds.py` | world generator, templates, truth table, literature rendering |
| `src/oms/claims.py` | claim schema, normalization, evaluation |
| `src/oms/roles.py` | role prompts and output schemas |
| `src/oms/collective.py` | organizational designs, governance rules, mechanical baseline |
| `src/oms/sandbox.py` | contained execution of analyst scripts |
| `src/oms/scoring.py` | metrics |
| `src/oms/llm.py` | backends and record/replay cache |
| `src/oms/experiments.py`, `report.py`, `cli.py` | harness, aggregation and figures, command line |
| `configs/` | `pilot_codex.yaml`, `smoke_mock.yaml` |
| `worlds/` | six pilot worlds |
| `runs/pilot_codex/` | config, `llm_cache.jsonl`, transcripts, `results.jsonl` |
| `results/pilot_codex/` | tables (`RESULTS.md`, CSV) and figures |
| `docs/` | proposal and this appendix |
| `tests/` | pytest suite (34 tests, no model access required) |
| `requirements-lock.txt` | pinned environment used for the pilot |
| `scripts/refresh_truth.py` | recompute truth files of existing worlds with the current oracle |
