---
title: "Organizing Machine Science: A Ground-Truth Testbed for the Organizational Design of AI Research Collectives"
subtitle: "Stage-1 research proposal for the Organization Science special issue “AI-Enabled Frontiers in Organizational Science”"
author: "Yongchao Martin Ma"
date: "October 2026"
---

# Organizing Machine Science: A Ground-Truth Testbed for the Organizational Design of AI Research Collectives

*Stage-1 research proposal. Contribution types: AI-enabled research loops under human direction; reusable research infrastructure; critical and boundary-setting work.*

## 1. The problem: machine science is an organizational problem, and we have no instrument for it

The field’s debate about artificial intelligence in research has been framed as a question about *models*: can a large language model generate a novel hypothesis, run an analysis, write a paper? The systems that actually do this, however, are not models. They are organizations. An “AI scientist” divides epistemic labor among roles (a literature agent, a theorist, an analyst, a reviewer), routes information among them in a particular order and topology, and decides which claims survive through some evaluation architecture (self-check, advisory review, or a referee with veto power). These are the classic variables of organization design, and organization science has well-developed theory about how they shape what an organization gets right and gets wrong: hierarchies reject more bad projects and more good ones than polyarchies [Sah and Stiglitz 1986]; the generation and the evaluation of alternatives are separable faces of search [Knudsen and Levinthal 2007]; efficient communication speeds convergence but destroys the diversity that long-run performance needs [Lazer and Friedman 2007; Fang, Lee and Schilling 2010]; diverse problem solvers can beat able ones [Hong and Page 2004]; and social influence can erase the wisdom of crowds [Lorenz et al. 2011].

This proposal makes two claims. First, whether an AI research collective produces knowledge or confident slop depends on its organizational design at least as much as on the capability of its models. Second, the inherited theory may fail for machine organizations in an instructive way. The error-correcting value of independent review in Sah and Stiglitz’s framework rests on evaluators whose errors are imperfectly correlated. Members of an AI collective are frequently copies of one base model prompted into different roles, and language models are known to favor their own outputs and to agree with the premises they are given [Panickssery, Bowman and Feng 2024; Sharma et al. 2024]. An organization of near-clones may obtain the costs of hierarchy (missed true discoveries) without its benefit (fewer false ones). Testing this requires varying organizational design while holding model capability constant, and it requires something the AI-for-science literature does not have: ground truth.

Current evaluations of AI research systems rely on language-model judges or human raters of novelty and quality [Lu et al. 2024; Si, Yang and Hashimoto 2025; Gottweis et al. 2025]. Raters can tell whether a claim is interesting; they cannot tell whether it is true, and so they cannot separate a valid finding from a well-written false one. This is exactly the failure mode the special-issue editors describe as a Potemkin village of slop masquerading as research, and it is why the question “more or better?” [Gartenberg et al. 2026] cannot currently be answered for machine-produced science.

## 2. The idea: synthetic organizational worlds as a wind tunnel for research organizations

We propose, and have prototyped, a testbed in which AI research collectives of different organizational designs do organizational research on worlds whose causal structure is known. A *world* is a structural causal model over a dozen organizational constructs with realistic labels (team turnover, routine codification, knowledge loss, team performance), a dataset drawn from it, a codebook, and a planted literature of seven short abstracts of “prior studies.” Each abstract makes a claim whose truth *in this world* is computed rather than asserted. Every template comes in an *orthodox* variant, where the textbook relationship holds, and a *contrarian* variant, where a different mix of mechanisms reverses the sign of the focal effect so that the consensus abstract is false. Every world also contains a confounding trap: an abstract that reports a spurious association (training hours and performance, both driven by budget slack) as if it were causal.

The collective receives the brief, codebook and literature, writes and executes analysis code against the data, deliberates according to its design, and returns a structured set of causal claims (effects, moderations, mediations with signs, a calibrated confidence, and the evidential basis for each). Because the truth is known, scoring is exact and involves no language model: Type I errors (false claims), Type II errors (focal truths missed), *discovery* (recovery of true mechanisms that no abstract mentions), *parroting* (restating the planted literature), *prior conformity* (asserting the textbook answer in a world where it is false), trap errors, calibration (Brier score), and citation errors (citing an abstract for a claim it does not make). The confident-false rate is our operational definition of slop.

The testbed treats the organization of the collective as the experimental factor. The current design space has five levers, each tied to a body of theory:

| Lever | Values | Theory tested on machine collectives |
|---|---|---|
| Division of labor | solo generalist vs. theorist–analyst–lead pipeline | specialization; division of cognitive labor [Kitcher 1990] |
| Evaluation architecture | none / advisory critic (polyarchy) / critic with veto (hierarchy) | Type I vs. Type II error trade-off [Sah and Stiglitz 1986; Christensen and Knudsen 2010] |
| Member heterogeneity | critic on the same model vs. a different model | correlated errors; diversity [Hong and Page 2004] |
| Sequencing | theory-first vs. data-first (analyst explores blind to the literature) | theory-driven vs. phenomenon-driven discovery; conformity to priors |
| Communication structure | two theorists connected vs. isolated until a late merge | network structure and exploration [Lazer and Friedman 2007; Fang, Lee and Schilling 2010] |

Four hypotheses organize the first study. **H1.** Relative to no review, a critic with veto power lowers the Type I rate and raises the Type II rate; an advisory critic sits in between. **H2.** The Type I reduction from review is smaller when critic and theorist share a base model than when they do not. **H3.** Isolated theorists recover more unpublished mechanisms and conform less to the consensus than connected theorists, at some cost in coherence. **H4.** Data-first sequencing reduces prior conformity in contrarian worlds but increases trap errors, a herding-versus-spuriousness trade-off that the evaluation architecture should moderate.

## 3. What we have done

A working prototype is in the repository that accompanies this proposal (`organizing-machine-science`). It contains the world generator with three templates in two variants; the claim schema and exact scorer; nine organizational designs, including a no-model mechanical baseline (kitchen-sink regression with interaction and mediation screens) that marks how much a collective adds beyond fixed statistics; a contained sandbox in which the analyst role executes its own code; and backends for any OpenAI-compatible endpoint, for the OpenAI Codex command-line interface, and for a deterministic mock used by the test suite. Every model request and response is recorded, so that `oms run --mode replay` reproduces a published run bit-for-bit with no model access. The suite of eleven tests runs without a model.

We ran a pilot of all nine designs on the six worlds with GPT-6 Astra as the base model and a GPT-5.6 model as the heterogeneous critic (one seed; roughly [[N_CALLS]] model calls). [[PILOT_RESULTS_PARAGRAPH]]

Two caveats are deliberate. The pilot is small and single-seed; its purpose is to show that the instrument discriminates between designs and that the metrics behave as designed, not to estimate effects. And the worlds are, for now, linear-Gaussian with pairwise interactions and no unobserved confounding. They are meant to be easy: a design that produces slop here will not produce knowledge anywhere.

## 4. What we hope to do

*Study 1 (Stage 2).* Run the full factorial over the five levers with ten seeds per world, add cross-vendor heterogeneity (at least one model from each of three vendors, plus an open-weights model), and test H1–H4 with pre-registered analyses. The design space and hypotheses will be registered before the full runs.

*Study 2: a difficulty ladder.* Extend the generator to nonlinear effects, panel structure with unit fixed effects, unobserved confounding, measurement error and selection, so that worlds can be graded by the identification strategy they demand. Which organizational designs degrade gracefully as worlds get harder is itself a result.

*Study 3: external validity.* Two bridges from synthetic to real evidence. First, experiment-benchmarked observational tasks: the collective receives the observational portion of a dataset for which an experimental estimate exists and is scored against it. Second, time-split rediscovery: collectives receive the literature as it stood before a now-established finding, with explicit contamination probes to detect models that already know the answer.

*Study 4: a common benchmark for human and machine research organizations.* Teams of doctoral students will work the same worlds under the same brief and be scored by the same instrument. To our knowledge no benchmark allows human research teams, human–AI teams and machine collectives to be compared on identical problems with known answers. This also tests directly whether the error profile of a machine collective differs in kind from that of a human team, which the many-analysts studies suggest is itself far from error-free [Breznau et al. 2022].

*Infrastructure.* The testbed is released as a package so that any research loop, including those submitted to this special issue, can publish a Type I/Type II profile alongside its outputs. The same instrument evaluates review architectures, which bears directly on the editors’ concern with AI in peer review.

## 5. Key risks

*Artificiality.* Synthetic worlds may reward skills that do not transfer. Mitigations: the difficulty ladder, Study 3, and a commitment to report where designs that win in the wind tunnel lose outside it.

*Goodhart effects.* Designs can be tuned to our metrics. Mitigations: held-out world templates never used during development; pre-registration; releasing the generator so that others can build adversarial worlds.

*Prompt confounds.* Organizational effects could be prompt effects in disguise. Role prompts are held constant across designs and we will report robustness to paraphrased prompts.

*Model drift and cost.* Models change under our feet. Every run is recorded and replayable; results are reported per model version. Cost is modest (five to eight model calls per run), which is what makes ten seeds and several vendors feasible.

*Contamination (Study 3).* Models may recall the finding they are meant to rediscover. We use post-training-cutoff findings and direct recall probes, and we report rediscovery conditional on probe failure.

*Ethics and misuse.* Studies 1–3 involve no human subjects; Study 4 will be reviewed by an ethics board. The instrument could be used to optimize collectives that produce persuasive false claims. We mitigate by publishing the detection metrics with the generator and by reporting slop metrics for every configuration we release.

## 6. How organizational and social science would change

If this works, three things change. First, the question moves from “can AI do science?” to “how should machine science be organized?” That is a question organization science owns, and the field would supply the design knowledge for the research systems that are about to produce a growing share of its own literature. Second, organization theory gains an experimental domain in which the design of real cognitive organizations can be randomized cheaply, at scale, with ground truth. Simulation has long been a route to theory in our field [Davis, Eisenhardt and Bingham 2007; Harrison et al. 2007]; here the agents are not stylized rules but systems that read, argue and analyze, and the classic predictions may need revision for organizations whose members share one mind. Third, the field gains a pre-deployment standard. Before a research loop is trusted, it can be run through the wind tunnel and its error profile published, in the same way that an instrument is calibrated before it is used. The special issue asks whether AI will give us more or better science. A measurement of “better” is a prerequisite for the answer, and organizing for it is our discipline’s contribution.

## Use of AI

The author designed the research question, theory, hypotheses, testbed architecture and this proposal, and takes responsibility for all content. AI coding and writing assistants were used extensively under the author’s direction to implement the prototype, run the pilot, verify references and polish language. The organization of that work (a lead that theorizes and integrates, assistants that retrieve and format, an independent model that reviews) mirrors the designs studied here.

## References

[[REFERENCES]]
