# Report evidence labels

The independent-review rules apply to all reports on the current branch. The
original audit tag preserves the original presentation and raw event checksums.
No stored event log, behavioral count, cost, token count or source input was
rewritten by this labeling pass. Paper comparison fields were removed from mock
exports; scorer formulas are unchanged.

## Fixture only

Every mock-derived number in the following files is **fixture only**. This includes
captured figures/screenshots: their original image bytes are retained for provenance,
and this index labels all depicted counts and measurements. JSON exports carry
machine-readable labels too. Source/human reference values and test counts are
distinct from predictions and do not validate model behavior.

- [phase1/acceptance.json](phase1/acceptance.json) — **fixture only**.
- [phase1/benchmark.json](phase1/benchmark.json) — **fixture only**.
- [phase1/browser-check.json](phase1/browser-check.json) — **fixture only**.
- [phase1/interviews.json](phase1/interviews.json) — **fixture only**.
- [phase2/acceptance.json](phase2/acceptance.json) — **fixture only**.
- [phase2/browser-check.json](phase2/browser-check.json) — **fixture only**.
- [phase2/cached-preparation.json](phase2/cached-preparation.json) — **fixture only**.
- [phase2/fidelity.json](phase2/fidelity.json) — **fixture only**.
- [phase2/preparation.json](phase2/preparation.json) — **fixture only**.
- [phase2/sample-personas.json](phase2/sample-personas.json) — **fixture only**.
- [phase2/simulation.json](phase2/simulation.json) — **fixture only**.
- [phase3/browser-check.json](phase3/browser-check.json) — **fixture only**.
- [phase3/concurrency-probe.json](phase3/concurrency-probe.json) — **fixture only**.
- [phase3/diagnostic-mock-simulation.json](phase3/diagnostic-mock-simulation.json) — **fixture only**.
- [phase3/mock-100-simulation.json](phase3/mock-100-simulation.json) — **fixture only**.
- [phase3/mock-100-verification.json](phase3/mock-100-verification.json) — **fixture only**.
- [phase3/mock-25-simulation.json](phase3/mock-25-simulation.json) — **fixture only**.
- [phase3/mock-25-verification.json](phase3/mock-25-verification.json) — **fixture only**.
- [phase3/optimized-fixture-comparison.json](phase3/optimized-fixture-comparison.json) — **fixture only**.
- [phase3/optimized-mock-100-simulation.json](phase3/optimized-mock-100-simulation.json) — **fixture only**.
- [phase3/optimized-mock-100-verification.json](phase3/optimized-mock-100-verification.json) — **fixture only**.
- [phase3/optimized-mock-25-simulation.json](phase3/optimized-mock-25-simulation.json) — **fixture only**.
- [phase3/optimized-mock-25-verification.json](phase3/optimized-mock-25-verification.json) — **fixture only**.
- [phase3/stock-diagnostic-mock-simulation.json](phase3/stock-diagnostic-mock-simulation.json) — **fixture only**.
- [r2/acceptance.json](r2/acceptance.json) — **fixture only**.
- [r2/browser-check.json](r2/browser-check.json) — **fixture only**.
- [r2/replay-check.json](r2/replay-check.json) — **fixture only**.
- [phase1/viewer.png](phase1/viewer.png) — **fixture only**.
- [phase2/viewer.png](phase2/viewer.png) — **fixture only**.
- [r2/viewer.png](r2/viewer.png) — **fixture only**.
- [phase3/viewer.png](phase3/viewer.png) — **fixture only**.
- [phase3/food-stock.png](phase3/food-stock.png) — **fixture only**.
- [phase3/food-stock.svg](phase3/food-stock.svg) — **fixture only**.
- [phase1/benchmark.md](phase1/benchmark.md) — **fixture only**.
- [phase3/food-stock.csv](phase3/food-stock.csv) — **fixture only**.

The Phase 1, Phase 2 and three REALISM_IMPLEMENTATION narrative reports label all
mock-derived numbers fixture only. In PHASE3_REPORT.md the offline table and the
synthetic latency probe are fixture only; its separately identified live results
came from the free MiniMax route. The REALISM_AUDIT report analyzes that earlier
free-route trace, not a new paid experiment.

## Live observations and engineering records

`live-api/`, files named `*live*`, and the recovery/cache/latency records for the
documented live experiment contain historical free-route observations. Their $0
costs are not paid-model validation and their single-seed results do not satisfy M3.
Model catalogs and readiness files are configuration evidence, not behavior.
Offline-checks files report test/lint execution, not resident realism.

The active milestone status and required paid-run fields are in
[M0_REPORT.md](M0_REPORT.md) and [MILESTONES.md](../MILESTONES.md).
