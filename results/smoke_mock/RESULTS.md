# Results: smoke_mock

Runs: 48 (designs: 8, worlds: 6).

## Means by design (all worlds)

| design | n_runs | n_claims | precision | focal_recall | discovery_rate | confident_false_rate | parroting_rate | trap_rate | brier | citation_errors | n_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mechanical | 6 | 9.50 | 0.77 | 0.51 | 0.68 | 0.12 | 0.20 | 0.00 | 0.16 | 0.00 | 0 |
| solo | 6 | 7 | 0.74 | 0.24 | 0.00 | 0.26 | 1.00 | 0.14 | 0.20 | 0.00 | 3 |
| pipeline | 6 | 7 | 0.74 | 0.24 | 0.00 | 0.26 | 1.00 | 0.14 | 0.20 | 0.00 | 5 |
| pipeline_polyarchy | 6 | 7 | 0.74 | 0.24 | 0.00 | 0.26 | 1.00 | 0.14 | 0.20 | 0.00 | 7 |
| pipeline_hierarchy | 6 | 5 | 0.73 | 0.20 | 0.00 | 0.27 | 1.00 | 0.13 | 0.20 | 0.00 | 7 |
| datafirst_hierarchy | 6 | 5 | 0.73 | 0.20 | 0.00 | 0.27 | 1.00 | 0.13 | 0.20 | 0.00 | 7 |
| two_theorists_connected | 6 | 5 | 0.73 | 0.20 | 0.00 | 0.27 | 1.00 | 0.13 | 0.20 | 0.00 | 8 |
| two_theorists_isolated | 6 | 5 | 0.73 | 0.20 | 0.00 | 0.27 | 1.00 | 0.13 | 0.20 | 0.00 | 8 |

## Standard errors (across worlds)

| design | precision_se | focal_recall_se | discovery_rate_se | confident_false_rate_se | consensus_conformity_se | parroting_rate_se | trap_rate_se | brier_se | citation_errors_se | n_claims_se |
|---|---|---|---|---|---|---|---|---|---|---|
| mechanical | 0.04 | 0.04 | 0.10 | 0.04 | 0.11 | 0.02 | 0.00 | 0.04 | 0.00 | 0.34 |
| solo | 0.06 | 0.09 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0 |
| pipeline | 0.06 | 0.09 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0 |
| pipeline_polyarchy | 0.06 | 0.09 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.02 | 0.00 | 0 |
| pipeline_hierarchy | 0.07 | 0.07 | 0.00 | 0.07 | 0.00 | 0.00 | 0.04 | 0.03 | 0.00 | 0 |
| datafirst_hierarchy | 0.07 | 0.07 | 0.00 | 0.07 | 0.00 | 0.00 | 0.04 | 0.03 | 0.00 | 0 |
| two_theorists_connected | 0.07 | 0.07 | 0.00 | 0.07 | 0.00 | 0.00 | 0.04 | 0.03 | 0.00 | 0 |
| two_theorists_isolated | 0.07 | 0.07 | 0.00 | 0.07 | 0.00 | 0.00 | 0.04 | 0.03 | 0.00 | 0 |

## Contrarian worlds only (textbook sign is wrong here)

| design | n_runs | precision | focal_recall | consensus_conformity | confident_false_rate | parroting_rate |
|---|---|---|---|---|---|---|
| mechanical | 3 | 0.86 | 0.46 | 0.17 | 0.03 | 0.18 |
| solo | 3 | 0.62 | 0.05 | 1.00 | 0.38 | 1.00 |
| pipeline | 3 | 0.62 | 0.05 | 1.00 | 0.38 | 1.00 |
| pipeline_polyarchy | 3 | 0.62 | 0.05 | 1.00 | 0.38 | 1.00 |
| pipeline_hierarchy | 3 | 0.60 | 0.05 | 1.00 | 0.40 | 1.00 |
| datafirst_hierarchy | 3 | 0.60 | 0.05 | 1.00 | 0.40 | 1.00 |
| two_theorists_connected | 3 | 0.60 | 0.05 | 1.00 | 0.40 | 1.00 |
| two_theorists_isolated | 3 | 0.60 | 0.05 | 1.00 | 0.40 | 1.00 |

## Orthodox worlds only

| design | n_runs | precision | focal_recall | consensus_conformity | confident_false_rate | parroting_rate |
|---|---|---|---|---|---|---|
| mechanical | 3 | 0.69 | 0.56 | 0.33 | 0.21 | 0.21 |
| solo | 3 | 0.86 | 0.44 | 1.00 | 0.14 | 1.00 |
| pipeline | 3 | 0.86 | 0.44 | 1.00 | 0.14 | 1.00 |
| pipeline_polyarchy | 3 | 0.86 | 0.44 | 1.00 | 0.14 | 1.00 |
| pipeline_hierarchy | 3 | 0.87 | 0.34 | 1.00 | 0.13 | 1.00 |
| datafirst_hierarchy | 3 | 0.87 | 0.34 | 1.00 | 0.13 | 1.00 |
| two_theorists_connected | 3 | 0.87 | 0.34 | 1.00 | 0.13 | 1.00 |
| two_theorists_isolated | 3 | 0.87 | 0.34 | 1.00 | 0.13 | 1.00 |
