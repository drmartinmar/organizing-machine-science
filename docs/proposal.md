---
title: "Organizing Machine Science: A Ground-Truth Testbed for the Organizational Design of AI Research Collectives"
subtitle: "Stage-1 research proposal for the Organization Science special issue “AI-Enabled Frontiers in Organizational Science”"
date: "Anonymized for review. Contribution types: AI-enabled research loops under human direction; reusable research infrastructure; critical and boundary-setting work. Package: this proposal, a technical appendix, and a Git repository with a working prototype and a recorded pilot."
---

**Abstract.** Multi-agent “AI scientist” systems are organizations: they divide epistemic labor among roles, route information through a communication structure, and accept or veto claims through an evaluation architecture. Organization science has decades of theory about how such choices shape what an organization gets right and wrong, but nobody can test that theory on machine collectives, because when an AI pipeline produces a finding there is no way to tell valid knowledge from confident slop. We propose, and have prototyped, a testbed that supplies the missing instrument: synthetic organizational worlds with known causal mechanisms and planted literatures whose truth status is computed, so that Type I errors, Type II errors, discoveries, prior conformity, calibration and citation fidelity are scored exactly, with no language model in the loop. The organization of the collective is the experimental factor: division of labor, hierarchy versus polyarchy in review, member heterogeneity, theory-first versus data-first sequencing, and connected versus isolated theorists. A pilot of nine designs on six worlds found no confident false claim from any model-based design, but organization moved the Type II error rate across a six-fold range, and a veto critic from a different model family silenced the collective in four of six worlds. If the program succeeds, the question moves from “can AI do science?” to “how should machine science be organized?”, organization theory gains an experimental domain with ground truth, and the field gains a pre-deployment standard for research loops, including the review architectures the editors worry about.

**Keywords.** AI-enabled research loops; organizational design; hierarchies and polyarchies; synthetic social systems; research infrastructure; validity and slop; peer review.

## 1. The problem: machine science is an organizational problem, and we have no instrument for it

The debate about artificial intelligence in research is framed as a question about models: can a large language model generate a hypothesis, run an analysis, write a paper? The systems that do this are not models. They are organizations. The AI Scientist, Co-Scientist and the Virtual Lab each divide epistemic labor among roles, route information in a particular order, and decide which claims survive through an evaluation architecture (Lu et al. 2026, Gottweis et al. 2026, Swanson et al. 2025). These are the classic variables of organization design, and the field has theory about them: hierarchies reject more bad projects and more good ones than polyarchies (Sah and Stiglitz 1986, Christensen and Knudsen 2010); generating and evaluating alternatives are separable faces of search (Knudsen and Levinthal 2007); efficient communication speeds convergence but destroys the diversity that long-run performance needs (Lazer and Friedman 2007, Fang et al. 2010); and diverse problem solvers can beat able ones (Hong and Page 2004).

Our research question is whether the organizational design of an AI research collective, holding model capability fixed, determines whether it produces valid knowledge or confident slop, and whether the inherited theory holds for collectives of near-identical agents. We expect it to fail instructively. The error-correcting value of review in Sah and Stiglitz’s framework rests on evaluators whose errors are imperfectly correlated. Members of an AI collective are usually copies of one base model prompted into roles, and language models favor their own outputs, defer to the premises they are given, and err alike even across model families (Panickssery et al. 2024, Sharma et al. 2024, Kim et al. 2025). An organization of near-clones may pay the cost of hierarchy, missed discoveries, without its benefit, fewer false ones.

Answering either question requires something the AI-for-science literature lacks: ground truth. Current evaluations rely on language-model judges or human raters of novelty and quality (Si et al. 2025). Raters can tell whether a claim is interesting, not whether it is true, and the consequences are documented: about 56% of the AI-authored papers at the Agents4Science conference contained a reference flagged as possibly fabricated (Bianchi et al. 2025), research agents can write unsound papers that language-model reviewers accept at rates up to 82% (Jiang et al. 2026), and auditing an AI-generated paper without its logs and code misses most of its hidden flaws (Luo et al. 2025). The question “more or better?” (Gartenberg et al. 2026) cannot be answered for machine-produced science until “better” can be measured.

## 2. The idea: synthetic organizational worlds as a wind tunnel for research organizations

We propose a testbed in which AI research collectives of different organizational designs do organizational research on worlds whose causal structure is known. A *world* is a structural causal model over a dozen organizational constructs with realistic labels (team turnover, routine codification, knowledge loss, team performance), a dataset drawn from it, a codebook, and a planted literature of seven abstracts of “prior studies,” each making a claim whose truth *in this world* is computed rather than asserted. Every template has an *orthodox* variant, where the textbook relationship holds, and a *contrarian* variant, where a different mix of mechanisms reverses the focal effect and the consensus abstract is false. Every world plants a confounding trap, an abstract that reports a spurious association as causal, and hides at least one true mechanism that no abstract mentions.

The collective receives the brief, codebook and literature, writes and executes analysis code against the data, deliberates according to its design, and returns structured causal claims: effects, moderations and mediations with signs, a calibrated confidence, and the evidential basis of each. Scoring is exact and model-free: Type I errors (false claims), Type II errors (focal truths missed), *discovery* (true mechanisms absent from the literature), *parroting*, *prior conformity* (asserting the textbook answer where it is false), trap errors, calibration, and citation errors. The confident-false rate is our operational definition of slop. The nearest analogue, HypoBench, scores hypothesis generators against known hypotheses in datasets (Liu et al. 2025); ours adds the planted literature, the contrarian twins, organizational-science constructs and, above all, the organization of the collective as the experimental factor. AI is both the object of study and the tool: the collectives run on current language models, and agents that read, argue and analyze make organizational design a factor that can be randomized at scale with a known answer.

Five levers define the current design space:

| Lever | Values | Theory tested on machine collectives |
|---|---|---|
| Division of labor | solo generalist vs. theorist–analyst–lead pipeline | division of cognitive labor (Kitcher 1990) |
| Evaluation architecture | none / advisory critic (polyarchy) / veto critic (hierarchy) | Type I vs. Type II trade-off (Sah and Stiglitz 1986) |
| Member heterogeneity | critic on the same vs. a different model | correlated errors; diversity (Hong and Page 2004, Kim et al. 2025) |
| Sequencing | theory-first vs. data-first (analyst explores before seeing the literature) | theory- vs. phenomenon-driven discovery; prior conformity |
| Communication structure | two theorists connected vs. isolated until a late merge | network structure and exploration (Lazer and Friedman 2007, Fang et al. 2010, Zollman 2010) |

**H1.** Relative to no review, a veto critic lowers the Type I rate and raises the Type II rate; an advisory critic sits between. **H2.** The Type I reduction from review is smaller when critic and theorist share a base model than when they do not. **H3.** Isolated theorists recover more unpublished mechanisms and conform less to the consensus than connected theorists. **H4.** Data-first sequencing reduces prior conformity in contrarian worlds but increases trap errors, a trade-off that the evaluation architecture should moderate.

## 3. What we have done

The accompanying repository contains a working prototype: the world generator with three templates in two variants; the claim schema and exact scorer; nine organizational designs, including a no-model mechanical baseline (kitchen-sink regression with interaction and mediation screens); a contained sandbox in which the analyst role executes its own code; and backends for any OpenAI-compatible endpoint, the OpenAI Codex command-line interface, and a deterministic mock for a key-free test suite. Every model request and response is recorded, so a published run replays bit-for-bit without model access, and every transcript, script, output, critic verdict, draft and final claim is stored. Auditability is a property of the artifact, not a promise.

We ran all nine designs on the six worlds with GPT-6 Astra as the base model and GPT-5.6 Terra as the heterogeneous critic (one seed, 54 runs, 264 model calls). Table 1 summarizes the pilot; the appendix gives standard errors, per-variant results and transcripts.

**Table 1.** Pilot means per run across six worlds (one seed).

| Design | Claims | Precision | Focal recall | Discovery | Confident-false | Parroting | Calls |
|---|---|---|---|---|---|---|---|
| Mechanical baseline (no model) | 9.5 | 0.77 | 0.51 | 0.68 | 0.12 | 0.20 | 0 |
| Solo generalist | 6.7 | 1.00 | 0.66 | 0.56 | 0.00 | 0.56 | 2 |
| Pipeline, no review | 6.3 | 1.00 | 0.56 | 0.40 | 0.00 | 0.67 | 4 |
| Pipeline, advisory critic | 6.0 | 1.00 | 0.52 | 0.33 | 0.00 | 0.72 | 6 |
| Pipeline, veto critic | 5.7 | 1.00 | 0.48 | 0.33 | 0.00 | 0.72 | 6 |
| Pipeline, veto critic, other model family | 1.2 | 1.00 | 0.11 | 0.06 | 0.00 | 0.92 | 6 |
| Data-first, veto critic | 5.8 | 0.95 | 0.57 | 0.58 | 0.00 | 0.35 | 6 |
| Two theorists, connected, veto critic | 5.7 | 1.00 | 0.52 | 0.39 | 0.00 | 0.63 | 7 |
| Two theorists, isolated, veto critic | 5.3 | 1.00 | 0.47 | 0.31 | 0.00 | 0.75 | 7 |

Three results stand out. First, with a frontier model in these easy worlds, slop was not the binding constraint: the eight model-based designs made 256 claims, two false and none confidently false, asserted no trap association, miscited no abstract, and in contrarian worlds mostly reported the sign in the data rather than the textbook’s. Organization moved the Type II error instead: with the model held constant, focal recall ranged from 0.66 to 0.11 and discovery from 0.58 to 0.06. Second, review behaved as Sah and Stiglitz predict on the cost side and had nothing to deliver on the benefit side: an advisory critic lowered recall, a veto critic lowered it further, and precision had nowhere to go. The cross-model veto critic imported a different epistemic norm, demanding that every cross-sectional claim be recast as an association, a form the claim schema cannot express; the lead dropped the claims, and in four of six worlds the collective reported nothing. Heterogeneity turned a veto into paralysis. Third, the solo generalist beat every division of labor on recall, discovery and calibration (Brier 0.06) at the lowest cost; data-first sequencing recovered the most unpublished mechanisms among reviewed designs and parroted the literature least, at the cost of two low-confidence false mediation claims; isolated theorists did not outperform connected ones. The mechanical baseline shows what the instrument catches: 13 false claims, including declaring the focal effect absent after conditioning on its mediators.

The pilot is single-seed and six worlds wide; it shows that the instrument discriminates between designs and that the metrics behave as designed, not the size of effects. The worlds are linear-Gaussian with observed confounding only, deliberately easy. In Sah and Stiglitz’s terms they put the collective where candidate claims are mostly good, which is where review should cost more than it returns; the difficulty ladder below moves the collective to where review earns its keep.

## 4. What we hope to do

*Study 1 (Stage 2).* The full factorial over the five levers with ten seeds per world, three model families (two commercial vendors and one open-weights model) so that heterogeneity is tested across vendors, and pre-registered tests of H1–H4 with mixed-effects models and random effects for world and seed.

*Study 2: a difficulty ladder.* Nonlinear effects, panel structure, unobserved confounding where the right answer is to report low confidence, measurement error and selection, so that worlds are graded by the identification strategy they demand. Which designs degrade gracefully as worlds get harder is itself a result, and it is where H1 and H2 get their real test.

*Study 3: external validity.* Experiment-benchmarked observational tasks, in which the collective receives the observational portion of a dataset for which an experimental estimate exists; and time-split rediscovery, in which collectives receive the literature as it stood before a now-established finding, with recall probes to detect contamination.

*Study 4: human and machine research organizations on one benchmark.* Doctoral-student teams, with and without AI assistants, work the same worlds under the same brief and submit claims through the same schema, under ethics-board approval. No benchmark today compares human teams, human–AI teams and machine collectives on identical problems with known answers.

*Infrastructure.* The package is a public good: any research loop, including those submitted to this special issue, can publish a Type I/Type II/discovery profile with one command, and the same instrument evaluates review architectures.

## 5. Key risks

*Artificiality.* Synthetic worlds may reward skills that do not transfer. Mitigations: the difficulty ladder, Study 3, and a commitment to report where designs that win in the wind tunnel lose outside it.

*Goodhart effects.* Designs can be tuned to our metrics. Mitigations: held-out templates written after the designs are frozen, pre-registration, and release of the generator so that others can build adversarial worlds.

*Prompt and schema confounds.* Organizational effects could be prompt effects in disguise, and the pilot shows that the claim schema shapes what a collective can say. Role prompts are held constant across designs, paraphrase robustness will be reported, and the schema will gain association and cannot-identify claim types.

*Model drift and cost.* Models change under our feet. Every run is recorded and replayable, and results are reported per model version. Cost is modest, two to eight calls per run, which makes ten seeds and three vendors feasible.

*Contamination (Study 3).* Models may recall the finding they are meant to rediscover; we use post-cutoff findings and recall probes, and report rediscovery conditional on probe failure.

*Ethics and misuse.* Studies 1–3 involve no human subjects; Study 4 will be reviewed by an ethics board. The instrument could be used to optimize collectives for persuasive false claims; we publish the detection metrics with the generator and report slop metrics for every configuration we release.

## 6. How organizational and social science would change

Three things change if this works. First, the question moves from “can AI do science?” to “how should machine science be organized?” That is a question organization science owns, and the field would supply the design knowledge for the research systems about to produce a growing share of its own literature. Second, organization theory gains an experimental domain in which the design of real cognitive organizations can be randomized cheaply, at scale, with ground truth. Simulation has long been a route to theory in our field (Davis et al. 2007, Harrison et al. 2007); here the agents are not stylized rules but systems that read, argue and analyze, and the classic predictions may need revision for organizations whose members share one mind. Third, the field gains a pre-deployment standard: before a research loop is trusted, it can be run through the wind tunnel and its error profile published. The editors ask whether AI will give us more or better science. A measurement of “better” is a prerequisite for the answer, and organizing for it is our discipline’s contribution.

## Use of AI

The authors designed the research question, theory, hypotheses, testbed architecture, metrics and this document, and take responsibility for all content. AI coding and writing assistants (Claude and GPT-family models, October 2026) were used extensively under the authors’ direction to implement the prototype, run the pilot, verify references and polish language; a separate model reviewed the proposal from a referee’s perspective before revision. Every model call in the pilot is recorded in the repository.

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
