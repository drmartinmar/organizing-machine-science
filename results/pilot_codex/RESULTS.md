# Results: pilot_codex

Runs: 54 (designs: 9, worlds: 6).

## Means by design (all worlds)

| design | n_runs | n_claims | precision | focal_recall | discovery_rate | confident_false_rate | parroting_rate | trap_rate | brier | citation_errors | n_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mechanical | 6 | 9.50 | 0.77 | 0.51 | 0.68 | 0.12 | 0.20 | 0.00 | 0.16 | 0.00 | 0 |
| solo | 6 | 6.67 | 1.00 | 0.66 | 0.56 | 0.00 | 0.56 | 0.00 | 0.06 | 0.00 | 2 |
| pipeline | 6 | 6.33 | 1.00 | 0.56 | 0.40 | 0.00 | 0.67 | 0.00 | 0.10 | 0.00 | 4 |
| pipeline_polyarchy | 6 | 6 | 1.00 | 0.52 | 0.33 | 0.00 | 0.72 | 0.00 | 0.19 | 0.00 | 6 |
| pipeline_hierarchy | 6 | 5.67 | 1.00 | 0.48 | 0.33 | 0.00 | 0.72 | 0.00 | 0.22 | 0.00 | 6 |
| pipeline_hierarchy_hetero | 6 | 1.17 | 1.00 | 0.11 | 0.06 | 0.00 | 0.92 | 0.00 | 0.28 | 0.00 | 6 |
| datafirst_hierarchy | 6 | 5.83 | 0.95 | 0.57 | 0.58 | 0.00 | 0.35 | 0.00 | 0.25 | 0.00 | 6 |
| two_theorists_connected | 6 | 5.67 | 1.00 | 0.52 | 0.39 | 0.00 | 0.63 | 0.00 | 0.24 | 0.00 | 7 |
| two_theorists_isolated | 6 | 5.33 | 1.00 | 0.47 | 0.31 | 0.00 | 0.76 | 0.00 | 0.22 | 0.00 | 7 |

## Standard errors (across worlds)

| design | precision_se | focal_recall_se | discovery_rate_se | confident_false_rate_se | consensus_conformity_se | parroting_rate_se | trap_rate_se | brier_se | citation_errors_se | n_claims_se |
|---|---|---|---|---|---|---|---|---|---|---|
| mechanical | 0.04 | 0.04 | 0.10 | 0.04 | 0.11 | 0.02 | 0.00 | 0.04 | 0.00 | 0.34 |
| solo | 0.00 | 0.08 | 0.09 | 0.00 | 0.20 | 0.06 | 0.00 | 0.01 | 0.00 | 0.42 |
| pipeline | 0.00 | 0.08 | 0.08 | 0.00 | 0.20 | 0.08 | 0.00 | 0.01 | 0.00 | 0.33 |
| pipeline_polyarchy | 0.00 | 0.08 | 0.10 | 0.00 | 0.20 | 0.10 | 0.00 | 0.01 | 0.00 | 0.36 |
| pipeline_hierarchy | 0.00 | 0.09 | 0.10 | 0.00 | 0.20 | 0.10 | 0.00 | 0.03 | 0.00 | 0.61 |
| pipeline_hierarchy_hetero | 0.00 | 0.11 | 0.06 | 0.00 | – | 0.08 | 0.00 | 0.07 | 0.00 | 0.98 |
| datafirst_hierarchy | 0.03 | 0.06 | 0.07 | 0.00 | 0.20 | 0.08 | 0.00 | 0.02 | 0.00 | 0.70 |
| two_theorists_connected | 0.00 | 0.12 | 0.11 | 0.00 | 0.24 | 0.08 | 0.00 | 0.02 | 0.00 | 1.17 |
| two_theorists_isolated | 0.00 | 0.10 | 0.11 | 0.00 | 0.20 | 0.08 | 0.00 | 0.02 | 0.00 | 0.76 |

## Contrarian worlds only (textbook sign is wrong here)

| design | n_runs | precision | focal_recall | consensus_conformity | confident_false_rate | parroting_rate |
|---|---|---|---|---|---|---|
| mechanical | 3 | 0.86 | 0.46 | 0.17 | 0.03 | 0.18 |
| solo | 3 | 1.00 | 0.57 | 0.17 | 0.00 | 0.45 |
| pipeline | 3 | 1.00 | 0.51 | 0.17 | 0.00 | 0.55 |
| pipeline_polyarchy | 3 | 1.00 | 0.51 | 0.17 | 0.00 | 0.55 |
| pipeline_hierarchy | 3 | 1.00 | 0.51 | 0.17 | 0.00 | 0.55 |
| pipeline_hierarchy_hetero | 3 | – | 0.00 | – | – | – |
| datafirst_hierarchy | 3 | 1.00 | 0.64 | 0.17 | 0.00 | 0.25 |
| two_theorists_connected | 3 | 1.00 | 0.37 | 0.00 | 0.00 | 0.44 |
| two_theorists_isolated | 3 | 1.00 | 0.31 | 0.25 | 0.00 | 0.70 |

## Orthodox worlds only

| design | n_runs | precision | focal_recall | consensus_conformity | confident_false_rate | parroting_rate |
|---|---|---|---|---|---|---|
| mechanical | 3 | 0.69 | 0.56 | 0.33 | 0.21 | 0.21 |
| solo | 3 | 1.00 | 0.74 | 1.00 | 0.00 | 0.67 |
| pipeline | 3 | 1.00 | 0.61 | 1.00 | 0.00 | 0.79 |
| pipeline_polyarchy | 3 | 1.00 | 0.54 | 1.00 | 0.00 | 0.89 |
| pipeline_hierarchy | 3 | 1.00 | 0.46 | 1.00 | 0.00 | 0.89 |
| pipeline_hierarchy_hetero | 3 | 1.00 | 0.22 | 1.00 | 0.00 | 0.92 |
| datafirst_hierarchy | 3 | 0.90 | 0.50 | 1.00 | 0.00 | 0.44 |
| two_theorists_connected | 3 | 1.00 | 0.67 | 1.00 | 0.00 | 0.75 |
| two_theorists_isolated | 3 | 1.00 | 0.62 | 1.00 | 0.00 | 0.81 |
