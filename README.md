# Organizing Machine Science

**A ground-truth testbed for the organizational design of AI research collectives.**

Research artifact accompanying a Stage-1 proposal to the *Organization Science* special issue
*AI-Enabled Frontiers in Organizational Science* (2026).

## The idea in one paragraph

Multi-agent "AI scientist" systems are organizations: they divide epistemic labor among roles, route
information through a communication structure, and accept or veto claims through an evaluation
architecture. Organization science has a century of theory about how such choices shape what an
organization gets right and wrong (hierarchies versus polyarchies, exploration versus exploitation,
network structure and collective problem solving, diversity and correlated error). But nobody can test
that theory on machine collectives, because when an AI pipeline writes a paper there is no way to tell
valid knowledge from confident slop. This testbed supplies the missing instrument: **synthetic
organizational worlds with known causal mechanisms and planted literatures**, so that the validity,
novelty, calibration and "Potemkin rate" of what a collective reports can be measured exactly, and the
collective's *organizational design* can be varied while holding model capability constant.

## What is here

| Path | Contents |
|---|---|
| `src/oms/worlds.py` | World generator: linear structural causal models with interactions; three templates (`turnover`, `monitoring`, `decentralization`), each in an `orthodox` and a `contrarian` variant (textbook sign reversed); planted literature whose truth status is *computed* against the world |
| `src/oms/claims.py` | Structured claim schema (effect / moderation / mediation with signs and calibrated confidence) and exact evaluation of a claim against a world's truth |
| `src/oms/collective.py` | Research collectives as organizations: `solo`, `pipeline`, `two_theorists`; `theory_first` / `data_first` sequencing; `none` / `polyarchy` / `hierarchy` evaluation; `connected` / `isolated` theorist networks; heterogeneous critic model; and a no-LLM `mechanical` baseline |
| `src/oms/roles.py` | Role prompts and output schemas (theorist, analyst, critic, lead, solo), held constant across designs |
| `src/oms/sandbox.py` | Executes analyst-written Python on the world's data in a contained subprocess |
| `src/oms/scoring.py` | Metrics: precision, focal recall, discovery of unpublished truths, parroting, consensus conformity, trap rate, confident-false ("Potemkin") rate, Brier score, citation errors |
| `src/oms/llm.py` | Backends: any OpenAI-compatible endpoint, the OpenAI Codex CLI, a deterministic mock; **record/replay cache** so every published run reproduces exactly without model access |
| `src/oms/experiments.py`, `report.py`, `cli.py` | Factorial harness, aggregation, figures, CLI |
| `worlds/` | The six pilot worlds (data, codebook, brief, literature, hidden truth) |
| `runs/pilot_codex/` | Pilot run: config, every LLM request/response (`llm_cache.jsonl`), per-run transcripts, results |
| `results/pilot_codex/` | Tables and figures produced from the pilot |
| `docs/` | The proposal and the technical appendix |
| `tests/` | pytest suite (runs without any model access) |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q                                   # 26 tests, no model access needed

oms worlds --seeds 1                        # (re)build the six pilot worlds deterministically
oms inspect worlds/turnover-contrarian-s1   # show a world's hidden truth and which abstracts are false there
oms evaluate --claims my_claims.json --world worlds/turnover-contrarian-s1   # score any external research loop's claims

# Reproduce the pilot exactly from the recorded cache (no API keys):
oms run configs/pilot_codex.yaml --mode replay
oms report runs/pilot_codex --out results/pilot_codex

# Run the whole factorial with a deterministic mock (pipeline check only, no science):
oms run configs/smoke_mock.yaml && oms report runs/smoke_mock
```

### Running with your own models

Any OpenAI-compatible endpoint works (OpenAI, OpenRouter, vLLM, Ollama, LM Studio):

```bash
export OMS_BASE_URL=https://openrouter.ai/api/v1   # or http://localhost:11434/v1 for Ollama
export OMS_API_KEY=...                              # falls back to OPENAI_API_KEY
```

and in a config file:

```yaml
backend: {name: openai, model: anthropic/claude-opus-5.5, alt_model: openai/gpt-6-astra, mode: record}
```

The pilot used the OpenAI Codex CLI (`backend: {name: codex, model: gpt-6-astra}`) because that was the model
access available to the author; the backend flattens the role messages into a single prompt and enforces the JSON
schema with `--output-schema`. Every request and response is in `runs/pilot_codex/llm_cache.jsonl`.

## How a run works

1. A **world** is drawn: a structural causal model over 11–12 organizational constructs (e.g., team turnover, routine
   codification, knowledge loss, team performance), a dataset of 1,200 units, a codebook, and seven short "prior study"
   abstracts. Each abstract makes a claim whose truth in *this* world is computed, not asserted: in `contrarian`
   variants the textbook claim about the focal relationship is false; one abstract always reports a confounded
   (zero-effect) association as if it were causal.
2. A **collective** with a given organizational design reads the brief, codebook and literature, writes and executes
   analysis code against the data, argues, reviews, and returns a structured set of causal claims with confidence
   levels and evidential basis.
3. The **scorer** evaluates every claim against the hidden truth and computes the metrics above. Nothing in the scoring
   involves a language model.

## Design levers and the theory they operationalize

| Lever | Values | Theory being tested on machine collectives |
|---|---|---|
| Division of labor | `solo` vs `pipeline` (theorist, analyst, lead) | specialization and the division of cognitive labor |
| Evaluation architecture | `none` / `polyarchy` (advisory critic) / `hierarchy` (critic with veto) | Sah and Stiglitz (1986): hierarchies reduce Type I errors at the cost of Type II errors |
| Member heterogeneity | same model vs critic on a different model | error correlation; Hong and Page (2004) |
| Sequencing | `theory_first` vs `data_first` | theory-driven vs phenomenon-driven discovery; prior conformity |
| Communication structure | `connected` vs `isolated` theorists | Lazer and Friedman (2007); Fang, Lee and Schilling (2010): isolation preserves diversity |

## Status and honesty notes

* This is a prototype. The worlds are linear-Gaussian with pairwise interactions and no unobserved confounding;
  extending the generator to nonlinear, panel and partially unobserved worlds is planned work (see the proposal).
* The pilot is small (6 worlds × 9 designs, one seed). Its numbers are preliminary evidence that the instrument
  discriminates between designs, not estimates of population effects.
* The mock backend is a *parrot* (it restates the planted literature); it exists to test the pipeline, not to stand
  in for a model.
* The author directed the design of this study and prototype and used AI coding and writing assistants extensively
  in building it; see the technical appendix for a full use-of-AI statement.

## License

MIT (code). World specifications and generated data are released under the same terms.
