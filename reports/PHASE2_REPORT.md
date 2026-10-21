# Phase 2 report

Phase 2 is implemented and verified offline. The original 25-resident workflow
still passes its acceptance tests. No Phase 3 work or paid inference was started.

## Delivered

- A versioned, content-hashed population artifact with the original 25 residents
  and 75 residents from the licensed public genagents GSS demographic bank.
- Six dated life events, first-person biographies, interests, values, goals,
  source provenance and locked identity/demographic facts for every resident.
- Twenty-one prior calendar days of reciprocal phone history: 4,200 messages and
  300 appointments, with owner-scoped contacts, read states and memories.
- Seventy-five apartment units grouped at three accessible entrances. These are
  authored map overlays, not new upstream artwork or a claim about real geography.
- T=0 categorical/numerical consistency surveys, bounded regeneration, fresh
  survey revisions per repair attempt, and refusal to publish unresolved residents.
- An offline Twin/GSS fidelity harness with masked profiles, strict answer scales,
  coverage, missingness, categorical accuracy, numerical error and human
  test–retest baselines. Gold keys and prior target responses stay in the scorer.
- CLI commands to populate, validate, import local Twin files, evaluate fidelity
  and run an expanded town; viewer support for life stories and apartment units.

The public GSS bank contains demographic proxies with fictional names/addresses,
not Stanford's restricted interview agents. Biographies and phone histories are
fictional generated additions. Duplicate full names remain distinct residents.

## Verification

| Check | Result |
| --- | --- |
| Full offline regression | **39 passed** in 97.54 seconds |
| Population preparation | **100 residents** pass t=0; 300 mock requests |
| Contradiction repair / rejection | Both paths verified by fault-injection tests |
| Original seed identities and goals | Preserved and revalidated before launch |
| Phone chronology, ownership, appointment time/capacity | Validated |
| Exact population rerun | **300 cache hits; byte-identical artifact** |
| Expanded simulation | **100 residents complete 1,440 simulated minutes** |
| Browser | 100 residents, 94 locations, biographies, prior history, needs and playback verified |
| Retained source integrity | All 76 Phase 2 source/derived hashes match |

The Chromium check had no page errors or external requests. Ruff and formatting
checks pass. Tests disable internet sockets; all runtime fixtures and data are local.
The default 25-resident two-day run, replay and cost-control regressions still pass.

Population digest:
`50cee46bfaa2168ab74dc3d5b2f4302a3c7efec8840edbfde75a3e0c74664912`.

## Costs and runtime

| Stage | Requests | USD |
| --- | ---: | ---: |
| Prepare 100 residents | 300 | $0 |
| Run 100 residents for one day | 2,739 | $0 |
| Twin and GSS fidelity evaluation | 395 | $0 |
| Exact preparation replay | 300 cached | $0 |

**Runtime cost: $0 per resident per simulated day on MockLLM.** Real-API cost
remains unmeasured. Mock token counts are synthetic estimates, not billable usage.

Preparation took 4.763 seconds; cached replay took 1.391 seconds. The town run
took 261.278 seconds while regression/fidelity jobs also ran, so this is not an
isolated performance benchmark. The simulation produced 300 new messages in
addition to its 4,200 historical records. Eight intents crossed a venue's closing
time and were rejected. No rejected intent applied its requested outcome.

## Fidelity harness results

These are **MockLLM fixture scores**, not evidence of human fidelity or improvement
over Park et al. Categorical answers use deterministic hashed choices; numerical
answers use range midpoints when the held-out fact is unavailable.

| Measure | Twin subset | GSS bank subset |
| --- | ---: | ---: |
| Subjects | 20 / 2,058 | 75 / 3,505 |
| Held-out scalar items | 122 | 4 |
| Eligible human/source answers | 1,888 | 300 |
| Valid prediction coverage | 100% | 100% |
| Categorical accuracy | 38.11% | 13.78% |
| Penalized normalized numerical MAE | 0.22425 | 0.22693 |
| Human test–retest categorical accuracy | 69.96% | Not available |
| Human test–retest normalized numerical MAE | 0.19054 | Not available |

Twin profiles contain 32 supported wave 1–3 evidence fields per subject. Every
wave-4 QuestionID is excluded from those profiles, including earlier answers to
the same questions. Those earlier answers are used only for the scorer's
test–retest baseline. There are 552 missing/out-of-scale target cells in the
20 × 122 grid; they are declared unscorable rather than imputed.

The GSS harness masks age, political views, party identification and religion.
It evaluates reconstruction of source demographic-bank fields rather than the
full GSS social-science instrument or a restricted interview-based agent bank.

Invalid/missing model answers count as categorical errors or maximum normalized
numerical error. Raw numerical MAE is also saved, but ranges/units differ across
items; normalized error and per-item results are the interpretable comparisons.
No held-out answers are supplied to repair feedback in the fidelity workflow.

## Problems fixed and remaining limits

- Fixed a repair-cache loop: an identical regenerated biography could reuse its
  previous wrong survey. Each t=0 attempt now has a distinct request revision;
  repeating the entire sequence still replays deterministically from cache.
- Extended timestamp models for pre-epoch records while keeping runtime app
  requests and event time nonnegative.
- Preserved duplicate names through distinct source-based IDs, and added
  housing overlays instead of overfilling original homes.
- Changed metric extraction to avoid retaining every full agent snapshot in
  memory when scoring an expanded run.
- T=0 checks cover locked facts and structural/age anchors; they do not prove
  every sentence in a free-form biography is semantically consistent.
- Mock biographies/history templates are repetitive research fixtures. Narrative
  quality, human believability and real-model survey fidelity remain unvalidated.
- The bounded dataset, supported encodings, demographic mix and experimental
  context differ from the source papers. Model-training contamination is unassessed.
- Time-use averages were 8.452 hours sleeping, 4.955 working/studying, 9.873
  leisure/communication, 0.191 travel and 0.528 other activity. They remain
  uncalibrated and do not establish realistic daily-life behavior.
- SQLite plus JSONL still uses full snapshots; the one-day town database is
  about 113 MB. A 1,000-resident load test and scheduler resume remain unimplemented.
- Paid API compatibility/cost are pending configuration and explicit spending
  approval. The earlier Phase 1 real-API acceptance is still incomplete.

## Evidence and reproduction

- [Acceptance record](phase2/acceptance.json), [preparation](phase2/preparation.json)
  and [cached preparation](phase2/cached-preparation.json).
- [Simulation measurements](phase2/simulation.json) and
  [fidelity results](phase2/fidelity.json).
- [Sample personas](phase2/sample-personas.json),
  [browser check](phase2/browser-check.json) and [viewer screenshot](phase2/viewer.png).
- Source attribution, licenses and exact revisions: [THIRD_PARTY.md](../THIRD_PARTY.md)
  and [Phase 2 source manifest](../references/phase2/sources.json).

```bash
python -m smallville populate --out runs/my-population --residents 100 --history-days 21
python -m smallville run --population runs/my-population/population.json --out runs/my-town --days 1
python -m smallville serve --run runs/my-town
python -m smallville fidelity --dataset all --out runs/my-fidelity
```

Local complete artifacts are in `runs/phase2-population/`, `runs/phase2-town/`
and `runs/phase2-fidelity/`; they are intentionally excluded from Git. Development
stops at Phase 2. Jobs/wages/rent/shops, councils/news/resource pressure, graph
memory, long-run drift, 1,000-agent batching and social media remain later work.
