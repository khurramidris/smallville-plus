# Phase 1 report

**Evidence label: fixture only.** Every MockLLM-derived behavioral, cost, token,
runtime and storage number in this report is fixture only. Tests demonstrate
engineering correctness; no paid-model milestone is completed by these results.
Historical implementation status below predates the [M0–M4 rules](../MILESTONES.md).

The Phase 1 implementation and offline checks are complete. Three acceptance
criteria pass; **the real-API day remains unvalidated** because models, credentials
and spending approval are absent. No paid calls were made.

## Built

- Original 25 licensed character seeds and a tile-derived Smallville location
  graph behind a replaceable map interface.
- SQLite WAL world state, simulated clock, scheduled/condition events, sparse
  activation, append-only indexed event history and exact state replay.
- Rules-first GM with delayed outcomes and per-person observations, limited
  perception, needs/emotions, finite memories, reflections and hierarchical plans.
- Private messaging/calendar apps; deterministic MockLLM; env-configured LiteLLM
  boundary, persistent cache, call ledger, reservations and original-cap protection.
- CLI, Valentine's benchmark, paper comparisons, variance and ATUS diagnostics,
  interview protocol and read-only FastAPI/HTML replay viewer.

## Acceptance

| Criterion | Result |
| --- | --- |
| Tests pass offline | **25 passed**; internet sockets disabled |
| 25 residents complete two MockLLM days | **Passed**; 2,880 simulated minutes |
| Valentine's party benchmark runnable | **Passed**; CLI and saved report |
| One real-API day stays under `SIM_MAX_USD` | **Not run**; approval/configuration needed |

The final suite took 102.71 seconds. Chromium verification covered map selection,
five needs, historical sleep state, play/pause and party-time inspection. There
were no JavaScript errors or external browser requests. All retained source data
still matches its recorded hashes.

## Measured mock run

- 25 residents × 2 days = **50 resident-days**.
- **$0 total; $0 per resident per simulated day**.
- 1,594 mock requests, 161 messages, no cache hits or uncertain calls.
- 2,723,385 synthetic input tokens and 64,425 synthetic output tokens. These are
  fixture estimates, not billable API usage.
- 121.296 seconds wall time while the test suite ran concurrently; this is not
  an isolated performance benchmark.
- Subsequent interviews added 125 requests for 25 residents at $0 additional cost.
  Human believability scores are uncollected.

| Measurement | Fixture only |
| --- | ---: |
| Sam candidacy awareness | 1 → 14 of 25 |
| Party awareness | 1 → 19 of 25 |
| Invited guests attending | 12 / 18 |
| Mutual-knowledge density | 0.233 → 0.327 |

Mock decisions include explicit scenario logic. These figures verify the engine
and measurement paths; **they do not establish emergence or improved realism**.
The starting relationship graph, messaging channel and awareness measurement
also differ from the paper's experiment.

Average daily hours were 8.429 sleeping, 6.583 working/studying, 7.905 leisure and
communication, 0.251 travel, and 0.832 other activity. The report compares their
shape with ATUS 2024 while disclosing different demographics, days and categories.
No time-use calibration or survey fidelity claim is made.

## Problems and limits

- Fixed inaccessible map representatives: geometric centers could select
  isolated rooms, and the largest collision-free region was outside town.
- Fixed election-awareness false positives from residents asking who was running.
- Fixed mock attempts to share a complete party schedule without receiving its
  time/place, and reduced repeated choices of already-closed destinations.
- Twelve intents still crossed closing time; the GM rejected them. Rejection is
  observable and causes replanning rather than applying an impossible outcome.
- Needs, emotion, sentiment and opinion coefficients are explicit research
  assumptions. Mock speech and behavior are fixtures. Human ratings are pending.
- Events currently contain full agent snapshots, and the viewer reconstructs
  historical state from them. A 1,000-resident load test has not been performed.
- Replay restores recorded state; scheduler resume is not implemented.
- Provider compatibility, real token usage and paid USD per resident-day remain
  unmeasured. Budget enforcement has offline regression coverage; its USD bound
  assumes configured prices cover billed tokens and provider limits are honored.

## Saved evidence and use

- [Benchmark data](phase1/benchmark.json) and [comparison report](phase1/benchmark.md).
- [Acceptance record](phase1/acceptance.json), [browser check](phase1/browser-check.json)
  and [viewer screenshot](phase1/viewer.png).
- [125 interview responses](phase1/interviews.json), with human ratings left null.
- Large local run files: `runs/phase1-acceptance/` (intentionally Git-ignored).

```bash
python -m pytest
python -m smallville benchmark valentine --out runs/another-run --days 2
python -m smallville serve --run runs/phase1-acceptance
```

The viewer defaults to http://127.0.0.1:8000. Readiness can be checked without
spending using `python -m smallville preflight`. The only remaining Phase 1
acceptance action is an approved one-day paid run with configured models, API
credentials, verified prices and `SIM_MAX_USD`. No later phase was started.
