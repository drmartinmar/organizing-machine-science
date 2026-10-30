---
title: "Organizing Machine Science: A Ground-Truth Testbed for the Organizational Design of AI Research Collectives"
subtitle: "Stage-1 research proposal for the Organization Science special issue “AI-Enabled Frontiers in Organizational Science”"
date: "Anonymized for review. Contribution types: AI-enabled research loops under human direction; reusable research infrastructure; critical and boundary-setting work. Package: this proposal, a technical appendix, and a Git repository with a working prototype and a recorded pilot."
---

**Abstract.** Multi-agent “AI scientist” systems are organizations: they divide epistemic labor among roles, route information through a communication structure, and accept or veto claims through an evaluation architecture. Organization science offers decades of theory on how such choices shape what an organization gets right and wrong, but that theory cannot be tested on machine collectives as long as the validity of what they report cannot be measured. We propose, and have prototyped, a testbed that supplies the missing instrument: synthetic organizational worlds with known causal structure, declared identification assumptions and planted literatures whose claims are checked against each world. As a result, false claims, coverage, recovery of mechanisms absent from the literature, conformity to textbook claims that are false in the world, and calibration are scored exactly, with no language model in the loop. The experimental factor is the organization of the collective: division of labor, evaluation architecture, member heterogeneity, theory-first versus data-first sequencing, and exposure between theorists. A pilot of nine designs on six worlds observed no false claim and no conformity to false textbook claims from any model-based design, but large organizational effects on what was found: coverage ranged from 0.47 to 0.66 across designs sharing one model and fell to 0.11 when a critic from another model family held a veto. If the program succeeds, the question shifts from “can AI do science?” to “how should machine science be organized?”, and the field gains a way to measure what “better” means for machine-produced research.

**Keywords.** AI-enabled research loops; organizational design; hierarchies and polyarchies; synthetic social systems; research infrastructure; validity and slop; peer review.

## 1. The problem: machine science is an organizational problem, and we have no instrument for it

The debate about artificial intelligence in research is framed as a question about models: can a large language model generate a hypothesis, run an analysis, write a paper? The systems that do this are not models. They are organizations. The AI Scientist, Co-Scientist and the Virtual Lab each divide epistemic labor among roles, route information in a set order, and decide through an evaluation architecture which claims survive (Lu et al. 2026, Gottweis et al. 2026, Swanson et al. 2025). These are the classic variables of organization design, and the field has theory about them: hierarchies reject more bad projects than polyarchies do, and more good ones (Sah and Stiglitz 1986, Christensen and Knudsen 2010); generating and evaluating alternatives are separable faces of search (Knudsen and Levinthal 2007); efficient communication speeds convergence but erodes the diversity that long-run performance needs (Lazer and Friedman 2007, Fang et al. 2010); and diverse problem solvers can outperform high-ability ones (Hong and Page 2004).

Our research question is whether, holding model capability fixed, the organizational design of an AI research collective determines whether it produces valid knowledge or confident slop, and whether the inherited theory holds for collectives of near-identical agents. In Sah and Stiglitz’s framework, the value of review comes from evaluators whose errors are imperfectly correlated. Members of an AI collective are usually copies of one base model prompted into roles; language models favor their own outputs, defer to the premises they are given, and err alike even across model families (Panickssery et al. 2024, Sharma et al. 2024, Kim et al. 2025). When a critic shares the generator’s judgment of which claims are plausible but is prompted to apply a stricter threshold, review removes true claims without catching false ones: the cost of hierarchy without its benefit. That asymmetry is a hypothesis about dependence and thresholds, and testing it requires an instrument.

Current evaluations of research loops rely on language-model judges or human raters of novelty and quality (Si et al. 2025), which score whether a claim is interesting, not whether it is true. The consequences are documented: about 56% of the AI-authored papers at the Agents4Science conference contained a reference flagged as possibly fabricated (Bianchi et al. 2025), research agents can write unsound papers that language-model reviewers accept at rates of up to 82% (Jiang et al. 2026), and auditing an AI-generated paper without its logs and code misses most of its hidden flaws (Luo et al. 2025). The question “more or better?” (Gartenberg et al. 2026) cannot be answered for machine-produced science until “better” can be measured.

## 2. The idea: synthetic organizational worlds as a wind tunnel for research organizations

We propose a testbed in which collectives with different organizational designs conduct organizational research on worlds whose causal structure is known. A *world* comprises a structural causal model over a dozen organizational constructs (team turnover, routine codification, knowledge loss, team performance), a dataset drawn from it, a codebook, a brief that states the identification assumptions and the relevance thresholds against which the claims are scored, and a planted literature of seven abstracts of “prior studies” from comparable settings, each stating a causal proposition whose status *in this world* is computed. Every template has an *orthodox* variant, in which the textbook relationship holds, and a *contrarian* variant, in which a different mix of mechanisms reverses the focal effect and the textbook abstract does not hold. Every world plants a confounding trap and hides at least one true mechanism that no abstract mentions.

The collective receives the brief, codebook and literature, writes and executes analysis code, deliberates according to its design, and returns structured claims: effects, moderations and mediations, each with a sign, a calibrated confidence, and its evidential basis. Scoring against a declared estimand (local effects under intervention at the center of the distribution) is exact and model-free. The metrics are the proportion of reported claims that are false, with right-direction claims below the relevance threshold counted separately; coverage of the focal mechanisms; recovery of mechanisms absent from the literature; overlap with the literature; the prior-conformity error (asserting a textbook claim that is false in the world); trap errors; abstention; a probability score on submitted claims; and citation checks. The nearest analogue, HypoBench, scores hypothesis generators against known hypotheses in datasets (Liu et al. 2025); our testbed adds the planted literature, the contrarian twins, organizational-science constructs and the organization of the collective as the experimental factor. AI is both the object of study and the tool: the collectives run on current language models, and agents that read, argue and analyze make organization a factor that can be randomized at scale against a known answer.

Five levers define the current design space:

| Lever | Values | Theory tested on machine collectives |
|---|---|---|
| Division of labor | solo generalist vs. theorist–analyst–lead pipeline | division of cognitive labor (Kitcher 1990) |
| Evaluation architecture | none / advisory critic / veto critic; strict AND and OR rules over the same candidate claims | acceptance and rejection errors in hierarchies and polyarchies (Sah and Stiglitz 1986) |
| Member heterogeneity | critic on the same vs. a different model, with reciprocal assignments | error dependence and evaluation norms (Hong and Page 2004, Kim et al. 2025) |
| Sequencing | theory-first vs. data-first (analyst explores before seeing the literature) | theory- vs. phenomenon-driven discovery; prior conformity |
| Proposal exposure | second theorist sees vs. does not see the first proposal | sequential influence on proposal diversity (Lazer and Friedman 2007, Fang et al. 2010, Zollman 2010) |

**H1.** Relative to no review, an AND rule (both lead and critic must accept) lowers the false-claim proportion and lowers coverage; an OR rule does the reverse. **H2.** The reduction in false claims from review is smaller when critic and generator share a base model than when they do not, holding evaluation norms constant. **H3.** Theorists who do not see each other’s proposals produce more diverse proposals and recover more unpublished mechanisms. **H4.** Data-first sequencing reduces prior-conformity errors in contrarian worlds and raises trap errors, a trade-off the evaluation architecture should moderate.

## 3. What we have done

The accompanying repository contains a working prototype: the world generator with three templates in two variants; the claim schema and scorer, validated against hand-computed intervention examples; eleven organizational designs, including the AND and OR rules and a deliberately naive statistical reference procedure; a contained sandbox in which the analyst role executes its own code; and backends for any OpenAI-compatible endpoint, the OpenAI Codex command-line interface, and a deterministic mock for a key-free test suite. Every model request and response is recorded, so the pilot replays from the repository without model access; the environment is pinned; and every transcript, script, output, verdict, draft and final claim is stored for audit.

We ran nine designs on the six worlds, with GPT-6 Astra as the base model and GPT-5.6 Terra as the cross-model critic (one seed, 54 runs, 264 model calls). Table 1 summarizes the pilot; the appendix reports standard errors, per-variant results and transcripts.

**Table 1.** Pilot means per run across six worlds (one seed). Precision counts below-threshold claims as not true; coverage is the share of focal mechanisms recovered; recovery is the share of unpublished focal mechanisms recovered.

| Design | Claims | Empty reports | Precision | Coverage | Recovery | Literature overlap | Calls |
|---|---|---|---|---|---|---|---|
| Naive statistical reference (no model) | 9.5 | 0 | 0.77 | 0.51 | 0.68 | 0.20 | 0 |
| Solo generalist | 6.7 | 0 | 1.00 | 0.66 | 0.56 | 0.56 | 2 |
| Pipeline, no review | 6.3 | 0 | 1.00 | 0.56 | 0.40 | 0.67 | 4 |
| Pipeline, advisory critic | 6.0 | 0 | 1.00 | 0.52 | 0.33 | 0.72 | 6 |
| Pipeline, veto critic (revisions allowed) | 5.7 | 0 | 1.00 | 0.48 | 0.33 | 0.72 | 6 |
| Pipeline, veto critic, other model family | 1.2 | 4 | 1.00 | 0.11 | 0.06 | 0.92 | 6 |
| Data-first, veto critic | 5.8 | 0 | 0.95 | 0.57 | 0.58 | 0.35 | 6 |
| Two theorists, exposed, veto critic | 5.7 | 1 | 1.00 | 0.52 | 0.39 | 0.63 | 7 |
| Two theorists, unexposed, veto critic | 5.3 | 0 | 1.00 | 0.47 | 0.31 | 0.75 | 7 |

Three results stand out. First, with a frontier model in these deliberately easy worlds, false claims did not occur. The eight model-based designs made 256 claims: none was false, two were in the right direction but below the relevance threshold, none concerned a trap pair, and none was miscited. Of the 32 opportunities to assert a textbook claim that was false in the world, none was taken. Organization moved coverage instead: among designs sharing one model, coverage ranged from 0.47 to 0.66 and recovery of unpublished mechanisms from 0.31 to 0.58. Second, review had costs but nothing to correct: an advisory critic lowered coverage, a veto critic lowered it further, and with no false claims, the predicted benefit (H1, H2) was untestable. The cross-model critic applied a stricter identification norm than the brief had resolved and asked for every claim to be recast as an association, which the schema could not express; the collective reported nothing in four of six worlds. The pilot thereby found two flaws in the instrument: the brief had not stated the identification assumptions under which a claim counts as warranted, and the governance rule let “revise” verdicts pass unchecked. Both have since been repaired in the repository; the pilot ran on the earlier version. Third, the solo generalist had the highest coverage and the best probability score at the lowest cost; data-first sequencing had the highest recovery of unpublished mechanisms and the lowest literature overlap; and unexposed theorists did not outperform exposed ones. The naive reference procedure shows the scorer at work: eight false claims, among them a declaration that the focal effect was absent after conditioning on its mediators.

The pilot is single-seed and six worlds wide. It shows that the instrument discriminates between designs that differ only in organization, that the metrics behave as designed, and where the instrument itself was wrong; it does not estimate effects. The worlds place the collective where candidate claims are mostly good, which in Sah and Stiglitz’s analysis is where review costs more than it returns; the difficulty ladder below moves the collective to where review earns its keep.

## 4. What we hope to do

*Study 1 (Stage 2).* Twenty-one valid design cells (the levers are nested; the appendix enumerates them), each tested on six worlds and five world-parameter seeds in two live replicates with caching bypassed, for three model families with reciprocal critic assignments: about 1,300 runs per family and, at the pilot’s 100,000 tokens per run, on the order of 10^8 tokens per family. Pre-registered mixed-effects analyses with random effects for template, world and replicate; matched-resource comparisons for the division-of-labor contrast; paraphrased prompts and three held-out templates. The minimum deliverable is Study 1 on one family.

*Study 2: a difficulty ladder.* Nonlinear effects, panel structure, unobserved confounding and observationally equivalent worlds (where the warranted answer is abstention, which the schema accepts), measurement error and selection. Which designs degrade gracefully is itself a result; H1 and H2 are tested in the regime where false claims actually occur.

*Study 3: transfer.* Observational tasks scored against experimental estimates, with the estimates’ uncertainty and estimand differences carried into the score; and time-split rediscovery, with contamination probes run in separate sessions and treated as imperfect diagnostics.

*Study 4: human and machine research organizations on one benchmark.* Doctoral-student teams, with and without AI assistants, work the same worlds under the same brief, with matched time and tools; they are told that the abstracts are synthetic, and the study runs under ethics-board approval. The comparison concerns error profiles under stated resources.

*Infrastructure.* The package scores any claim set expressed in its ontology against any world. Integration with an independently built research loop, documenting what the conversion loses, is a Stage-2 deliverable.

## 5. Key risks

*Benchmark validity.* Agreement with a hidden model is not the same as warranted inference. Mitigations: declared identification assumptions and estimand in every brief, separate scoring of correctness and warrant, worlds where abstention is correct, and sensitivity to relevance thresholds.

*Artificiality and Goodhart effects.* Synthetic worlds may reward skills that do not transfer, and designs can be tuned to our metrics. Mitigations: the difficulty ladder, Study 3, held-out templates, pre-registration, and release of the generator for building adversarial worlds.

*Prompt and schema confounds.* Organizational effects could be prompt effects, and the pilot shows that the schema shapes what a collective can say. Role prompts are held constant, paraphrase robustness is reported, and the schema gains association claims and cannot-identify claims.

*Model drift and cost.* Runs are recorded and replayable; results are reported per model version; the budget is stated in tokens. *Ethics and misuse.* Studies 1–2 use only synthetic data; Study 3 uses public datasets under their licenses; Study 4 is reviewed by an ethics board. The instrument could be used to tune collectives to produce persuasive false claims; the detection metrics ship with the generator.

## 6. How organizational and social science would change

If this works, the question shifts from “can AI do science?” to “how should machine science be organized?”, a question that organization science owns and will need answered for the systems about to produce a growing share of its own literature. Organization theory gains an experimental domain in which the design of cognitive organizations can be randomized cheaply, at scale, against a known answer. Simulation has long been a route to theory in our field (Davis et al. 2007, Harrison et al. 2007); here the agents read, argue and analyze. The field also gains a calibration step for research loops, including review architectures: an error profile measured where the answer is known, whose predictive validity outside the wind tunnel must itself be established before anyone calls it a standard. The editors ask whether AI will give us more or better science. Measuring “better” is a prerequisite for the answer, and organizing for it is our discipline’s contribution.

## Use of AI

The authors designed the research question, theory, hypotheses, testbed architecture, metrics and this document, and take responsibility for all content. AI coding and writing assistants (Claude and GPT-family models, October 2026) were used extensively under the authors’ direction to implement the prototype, run the pilot, verify references and polish language. A separate model reviewed the package from a referee’s perspective; its objections to the oracle, the governance rules and the metric labels were checked and led to the repairs reported above. Every model call in the pilot is recorded in the repository.

## References

Bianchi F, Queen O, Thakkar N, Sun E, Zou J (2025) Exploring the use of AI authors and reviewers at Agents4Science. Preprint, submitted November 19, https://arxiv.org/abs/2511.15534.

Christensen M, Knudsen T (2010) Design of decision-making organizations. *Management Sci.* 56(1):71–89.

Davis JP, Eisenhardt KM, Bingham CB (2007) Developing theory through simulation methods. *Acad. Management Rev.* 32(2):480–499.

Fang C, Lee J, Schilling MA (2010) Balancing exploration and exploitation through structural design: The isolation of subgroups and organizational learning. *Organ. Sci.* 21(3):625–642.

Gartenberg C, Hasan S, Murray A, Pierce L (2026) More versus better: Artificial intelligence, incentives, and the emerging crisis in peer review. *Organ. Sci.* 37(3):795–812.

Gottweis J, Weng W-H, Daryin A, Tu T, Sirkovic P, Myaskovsky A, et al. (2026) Accelerating scientific discovery with Co-Scientist. *Nature* 655(8122):487–496.

Harrison JR, Lin Z, Carroll GR, Carley KM (2007) Simulation modeling in organizational and management research. *Acad. Management Rev.* 32(4):1229–1245.

Hong L, Page SE (2004) Groups of diverse problem solvers can outperform groups of high-ability problem solvers. *Proc. Natl. Acad. Sci. USA* 101(46):16385–16389.

Jiang F, Feng Y, Li Y, Niu L, Alomair B, Poovendran R (2026) BadScientist: Can a research agent write convincing but unsound papers that fool LLM reviewers? *Proc. 64th Annual Meeting Assoc. Comput. Linguistics, Vol. 1: Long Papers* (ACL, San Diego), 24712–24727.

Kim EM, Garg A, Peng K, Garg N (2025) Correlated errors in large language models. *Proc. 42nd Internat. Conf. Machine Learn.*, PMLR 267:30038–30066.

Kitcher P (1990) The division of cognitive labor. *J. Philos.* 87(1):5–22.

Knudsen T, Levinthal DA (2007) Two faces of search: Alternative generation and alternative evaluation. *Organ. Sci.* 18(1):39–54.

Lazer D, Friedman A (2007) The network structure of exploration and exploitation. *Admin. Sci. Quart.* 52(4):667–694.

Liu H, Huang S, Hu J, Zhou Y, Tan C (2025) HypoBench: Towards systematic and principled benchmarking for hypothesis generation. Preprint, submitted April 15, https://arxiv.org/abs/2504.11524.

Lu C, Lu C, Lange RT, Yamada Y, Hu S, Foerster J, Ha D, Clune J (2026) Towards end-to-end automation of AI research. *Nature* 651(8107):914–919.

Luo Z, Kasirzadeh A, Shah NB (2025) The more you automate, the less you see: Hidden pitfalls of AI scientist systems. Preprint, submitted September 10, https://arxiv.org/abs/2509.08713.

Panickssery A, Bowman SR, Feng S (2024) LLM evaluators recognize and favor their own generations. *Adv. Neural Inform. Processing Systems* 37:68772–68802.

Sah RK, Stiglitz JE (1986) The architecture of economic systems: Hierarchies and polyarchies. *Amer. Econom. Rev.* 76(4):716–727.

Sharma M, Tong M, Korbak T, Duvenaud D, Askell A, Bowman SR, Cheng N, et al. (2024) Towards understanding sycophancy in language models. *Proc. 12th Internat. Conf. Learn. Representations* (ICLR 2024), https://openreview.net/forum?id=tvhaxkMKAn.

Si C, Yang D, Hashimoto T (2025) Can LLMs generate novel research ideas? A large-scale human study with 100+ NLP researchers. *Proc. 13th Internat. Conf. Learn. Representations* (ICLR 2025), https://openreview.net/forum?id=M23dTGWCZy.

Swanson K, Wu W, Bulaong NL, Pak JE, Zou J (2025) The Virtual Lab of AI agents designs new SARS-CoV-2 nanobodies. *Nature* 646(8085):716–723.

Zollman KJS (2010) The epistemic benefit of transient diversity. *Erkenntnis* 72(1):17–35.
