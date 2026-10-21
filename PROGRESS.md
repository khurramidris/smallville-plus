# Smallville+ progress

## Current work — Phase 2
- User authorized the next phase on 2026-10-21. Scope is recorded in `PHASE2.md`;
  the complete original `SPEC.md` is preserved.
- Read the cloud runtime/network instructions and inspected the existing code.
  No new model variables, credentials or paid-run approval are configured.
- Reviewed the public genagents GSS bank documentation and Twin-2K-500 dataset
  card/metadata. Licenses are MIT and CC BY 4.0 respectively; dataset licensing
  and exact source revisions will be retained before importing data.
- Next: acquire a bounded source subset, add structured profiles and surveys,
  compile histories and population validation, integrate 100 residents, run
  offline acceptance and record limitations. No later phase will be built.

### Phase 2 step 1 — Licensed sources and pipeline prototype
- Retrieved all 75 GSS demographic records and both official Twin response CSVs
  without a blocked download. Recorded revisions, URLs and hashes. The source
  GSS names include two duplicate full names; resident IDs remain distinct.
- Retained a normalized Twin subset: 20 of 2,058 participants, 122 supported
  held-out items, 640 profile evidence fields and 1,888 eligible human answers.
- Added structured life histories, typed categorical/numerical surveys, bounded
  consistency repair, reciprocal digital histories, signed pre-epoch timestamps,
  a versioned population artifact and residential map overlays.
- Prototype MockLLM population: 100 residents, 4,200 messages across 21 prior
  calendar days, 300 appointments and 100 passed t=0 checks. Preparation took
  300 requests, $0 and 4.437 seconds. This is preliminary engineering evidence.
- Existing component tests still pass: 19 tests. New module tests, CLI workflows,
  full integration and final measurements are next.

## Step 1 — Specification and environment
- Saved the complete user request in `SPEC.md` before implementation.
- Workspace was empty; Python 3.12 is available. Pydantic, FastAPI, Uvicorn and HTTPX are installed.
- Cloud environment reports unrestricted networking, no configured model variables or API credentials.
- No paid service has been added or called.

## Next
1. Complete the Phase 2 deliverables and validation in `PHASE2.md`.
2. A live day remains blocked on model configuration, API credentials and
   explicit spending approval. No paid service was added or called.

## Step 2 — Reference inspection and provenance
- Read all six current-phase repository licenses before copying any material.
- Retained original Smallville Tiled map, collision/sector matrices, relationship
  whispers and all 25 persona scratch seeds at pinned upstream commit hashes.
- Studied Concordia event resolution/scene tracking, ARE event/notification
  documentation, HumanoidAgents drives and genagents persona organization.
- Recorded source paths, hashes and licenses in `THIRD_PARTY.md` and `references/`.
- Verified paper §7.1 benchmark targets: Sam 8/25; party 13/25; attendance
  5/12 guests; mutual-knowledge density 0.167 to 0.74.
- Installed local test tools and the LiteLLM library. This adds no paid service.
- No network download was blocked.

## Step 3 — World and event engine
- Added typed world entities, SQLite WAL projections, hash-chained append-only
  events, a JSONL mirror with interrupted-write recovery, and replay.
- Added deterministic simulated clock, ordered heap scheduler, condition triggers
  and asynchronous event subscriptions.
- Added a swappable map contract and a tile-derived Smallville graph with
  addresses, hours, capacities and walkable travel routes.
- Validation: 5 engine/world tests pass with network sockets disabled; Ruff passes.
- Found and fixed an upstream-map integration issue: centroid tiles can fall in
  isolated rooms, and the largest walkable component is exterior decoration.
  Representatives now use the component connecting the most named sectors.

## Open issues / acceptance
- (a) Offline tests: **25 passed**, final run 102.71 seconds; internet sockets disabled.
- (b) Two MockLLM days / 25 agents: **passed**, completed all 2,880 simulated minutes.
- (c) Valentine's benchmark: **passed**, runnable CLI and saved measurements.
- (d) One paid API day under cap: pending explicit approval and configured models/credentials.
- This section records Phase 1 acceptance; Phase 2 is now authorized above.
- Mock behavior and synthetic token counts do not demonstrate realism gains.
- No blinded human ratings or 1,000-resident load test have been conducted.
- Seed relationships start at density 0.233, differing from the paper's 0.167.

## Step 4 — Model gateway and offline backend
- Added env-only live model configuration, individual model overrides, a lazy
  LiteLLM adapter and a deterministic MockLLM fixture.
- Added persistent response caching by model, request/prompt hash and seed;
  sampling parameters are included in the hash.
- Added durable per-call model/token/USD accounting, preflight reservations,
  a hard stop before unaffordable requests, and conservative charging for failures.
- Paid requests require explicit opt-in, a positive cap and configured pricing.
- Validation: 10 tests pass offline, including concurrent budget checks, cache
  replay, retained failed-call reservations and sanitized provider errors.

## Step 5 — Minds, apps and authoritative outcomes
- Added the 25 original seeded personas, two inference tiers, per-person
  temperature/speech settings, finite memory and evidence-linked reflections.
- Added elapsed-time needs/emotions, conversation closeness, daily plans,
  hourly actions and replanning on surprises.
- Added private messaging and calendar APIs; messages enter recipient memory
  only on reading, and actions take simulated time to complete.
- Added rules-first GM validation for location, hours, capacity, resources,
  work/sleep location, contacts and calendar conflicts; ambiguous attempts alone
  use GM inference. Agents cannot directly apply outcomes.
- Validation: 17 component tests passed offline before integration.

## Step 6 — Integration and research tools
- Added a runnable CLI, Valentine's party benchmark, paper-comparison metrics,
  behavior variance, ATUS time-use shape diagnostics and an interview protocol.
- Added a local read-only FastAPI/HTML replay viewer with resident notebooks
  and historical cost dashboard. HTTP endpoints pass integration tests;
  visual browser verification remains next.
- Final pre-interruption suite: 23 tests passed with internet sockets disabled,
  including two days/25 residents, exact event/state replay, deterministic runs,
  cached reruns, sparse activation, budget stops and viewer history/privacy.
- Development run: 2 days, 25 residents, 1,720 mock requests, 162 messages,
  $0 total / $0 per resident-day, about 110 seconds before condition-check
  optimization. These are preliminary engineering measurements.
- Fixed campaign-awareness false positives from questions about an election,
  and mock planning that repeatedly chose a closed venue. The final benchmark
  must be measured again after those fixes.
- Restored workspace after interruption on 2026-10-21. No code or test files
  were lost. Model variables and API credentials are still absent.

## Step 7 — Final offline acceptance and stop
- Final suite: **25 passed in 102.71 seconds**, including the two additional
  budget-persistence and single-writer regression tests. Ruff/format checks pass.
- Fresh CLI benchmark: 25 residents, 2 simulated days, 1,594 model requests,
  161 messages, $0 total / **$0 per resident per simulated day**. Wall time
  was 121.296 seconds while the full suite ran concurrently.
- Awareness: Sam 1 to 14; party 1 to 19. Attendance: 12 of 18 invited guests;
  mutual-knowledge density 0.233 to 0.327. These are scripted mock diagnostics.
- The GM rejected 12 attempts that crossed a venue's closing time; no rejected
  intent was allowed to change physical outcomes.
- Chromium/Playwright verified 25 rendered residents, selection, all five needs,
  past sleep state, play/pause, party-time inspection and cost display, with no
  page errors or external browser requests. Saved a screenshot.
- Ran all five interview categories for all 25 residents: 125 responses, $0
  additional cost. Human ratings remain uncollected. Interview calls are separate
  from the 1,594-request simulation measurement.
- Rechecked all 31 retained map/seed files against recorded upstream hashes.
- Saved benchmark, interviews, browser evidence and acceptance status under
  `reports/`; complete replay artifacts remain in `runs/phase1-acceptance/`.
- All Phase 1 implementation is committed. No Phase 2 or later work was started.
- Paid API validation was not attempted: models, credentials, cap and spending
  approval are absent. Acceptance (d) remains explicitly incomplete.
