# Phase 1 progress

## Step 1 — Specification and environment
- Saved the complete user request in `SPEC.md` before implementation.
- Workspace was empty; Python 3.12 is available. Pydantic, FastAPI, Uvicorn and HTTPX are installed.
- Cloud environment reports unrestricted networking, no configured model variables or API credentials.
- No paid service has been added or called.

## Next
1. Finish browser verification and save a final acceptance report.
2. Commit the remaining Phase 1 modules and documentation.
3. Stop at Phase 1. A live day additionally requires model configuration,
   API credentials and explicit spending approval.

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
- (a) Offline tests: 23 passed before the interruption (55.30 seconds).
  Two additional gateway regression tests await the final run.
- (b) Two MockLLM days / 25 agents: passed in the offline integration test and
  a development run; final report artifact pending.
- (c) Valentine's benchmark: CLI implemented and exercised in integration.
- (d) One paid API day under cap: pending explicit approval and configured models/credentials.
- Later phases are deliberately out of scope.

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
