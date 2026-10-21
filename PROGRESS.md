# Smallville+ progress

## Current follow-up — Authorized live inference
- The user supplied an OpenRouter key and the exact model
  `minimax/minimax-m3.1-flash:free`, and requested real API calls. This authorizes
  the specified free route; no paid model, fallback or later phase is authorized.
- Rechecked cloud/network readiness. OpenRouter's public model catalog lists the
  exact route with zero prompt/completion prices. No network request was blocked.
- The existing gateway required positive prices/budgets even for free routes.
  Added explicit zero-price support for OpenRouter `:free` models, a zero-dollar
  cap, and provider-side zero-price/no-fallback constraints. Authentication and
  quota diagnosis exposes only HTTP status codes, never remote error bodies.
- The key will be supplied only through a hidden terminal input into the process
  environment. It is not saved to source, configuration, reports or logs.
- Next: verify the adapter offline, authenticate through LiteLLM, and attempt a
  one-day town run. Keep all previous offline evidence unchanged.
- Adapter verification: 12 focused tests pass offline, including four new
  zero-cap/free-route/error-redaction cases. Ruff and formatting checks pass.
- Authentication succeeded (HTTP 200). The key was supplied through hidden stdin;
  the first LiteLLM completion and full offline regression are now running.
- First real completion passed JSON validation: 271 input / 136 output tokens,
  $0, 28.93 seconds. The first town request failed after 50.294 seconds under the
  default 45-second timeout; the run stopped at minute 360 and is incomplete.
- Full regression passes: **43 offline tests in 66.78 seconds**.
- The public catalog declares mandatory reasoning, defaulting to maximum effort.
  Added environment-configured timeout/reasoning effort (included in cache
  identity). A fresh attempt will use supported `low` effort and a 180-second
  timeout. The failed run is preserved; there are no internal retries.
- All 14 focused gateway/preflight checks pass after adding these controls.
- Updated full regression: **45 offline tests pass in 107.23 seconds**. Exact
  replay of a real low-reasoning API answer is byte-identical, with no provider
  invocation; a changed question correctly causes an offline cache miss.
- The low-effort attempt authenticated and made 38 successful town calls. Real
  outputs exposed an ambiguous action prompt: all 19 proposed non-move actions
  included a location target, which the strict GM rejected. Paused the attempt at
  minute 375 (one cancelled request retained as uncertain, $0) to fix the prompt.
- Clarified that only movement has a target, added an explicit meal example and
  a readable date/time/day in private context. The GM's physical rules remain
  authoritative. A fresh run will verify this correction.
- Corrected live run: the first two breakfast intentions use `target=null` and
  pass GM checks. Five real requests completed in 42.81 seconds, $0. The day is
  still running; no full-day result is claimed yet.

## Current work — Phase 2
- **Completed and stopped at Phase 2.** Final evidence is in
  `reports/PHASE2_REPORT.md`; 39 offline tests and the 100-resident day pass.
- User authorized the next phase on 2026-10-21. Scope is recorded in `PHASE2.md`;
  the complete original `SPEC.md` is preserved.
- Read the cloud runtime/network instructions and inspected the existing code.
  No new model variables, credentials or paid-run approval are configured.
- Reviewed the public genagents GSS bank documentation and Twin-2K-500 dataset
  card/metadata. Licenses are MIT and CC BY 4.0 respectively; dataset licensing
  and exact source revisions will be retained before importing data.
- The implementation steps and measurements are recorded below. No later phase
  was built, and no paid model calls were made.

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

### Phase 2 step 2 — Profiles, histories, surveys and integration
- Added the population compiler and locked source-fact validation, six dated life
  events per profile, biography anchors, finite repair attempts and atomic
  population publication. The original 25 identities and seed goals are retained.
- Added 75 apartment units at three accessible entrances, signed pre-epoch phone
  records, owner-scoped historical messages and mutually consistent appointments.
- Connected population artifacts to simulation bootstrap, map overlays, replay,
  planning and the viewer. The default 25-resident path remains available.
- Added populate/validate/import/fidelity CLI commands and expanded viewer labels,
  apartment grouping and life-story inspection.
- Added held-out scoring with prediction coverage, categorical accuracy,
  normalized numerical error, and scorer-only human test–retest baselines.
- Found and fixed a repair-cache bug: a repeated biography could reuse the same
  contradictory survey. Every t=0 attempt now has a distinct request revision;
  reruns of the whole attempt sequence still replay exactly from cache.
- Validation: all 14 new tests pass (50.59 seconds), including contradiction
  repair, unresolved-profile rejection, locked facts, history privacy/chronology,
  100 residents through nine simulated hours, replay, cache identity and held-out
  answer isolation. Full regression and final CLI acceptance are next.

### Phase 2 step 3 — Final verification
- Full regression suite: **39 tests pass offline in 97.54 seconds**. Existing
  Phase 1 acceptance and the 14 new tests all pass. Ruff and formatting checks pass.
- Fresh preparation: 100 residents, 75 new housing units, 4,200 messages,
  300 calendar entries, six dated life events each, and 100 passed t=0 surveys.
  No resident required repair in the normal fixture; fault-injection tests verify
  repair and refusal to publish unresolved profiles. Cost: 300 mock requests, $0.
- Exact cached rebuild: 300/300 cache hits; population JSON is byte-identical,
  including digest `50cee46bfaa2168ab74dc3d5b2f4302a3c7efec8840edbfde75a3e0c74664912`.
- 100 residents completed all 1,440 minutes of one simulated day with 2,739 mock
  requests, 300 runtime messages and **$0 per resident per simulated day**.
  Eight intents crossed closing time and were rejected. Wall time: 261.278 seconds
  while the regression/fidelity jobs also ran.
- Both fidelity harnesses completed: 395 mock requests, $0. Twin: 20 subjects,
  122 items, 1,888 eligible targets, categorical accuracy 0.3811 and penalized
  normalized numerical MAE 0.22425. Human test–retest: 0.6996 / 0.19054.
  GSS: 75 subjects, four masked fields, categorical accuracy 0.1378 and normalized
  numerical MAE 0.22693. Mock scores validate plumbing, not human fidelity.
- Chromium verified all 100 residents, 94 locations, six-event life stories,
  owner-scoped prior phone history, needs, playback and costs. No page errors or
  external browser requests occurred. Human-readable place labels are used in
  the life-story display; structured artifact IDs remain unchanged.
- Rechecked all 76 retained Phase 2 source/derived-file hashes.
- Saved compact reports, sample personas, browser evidence and a screenshot under
  `reports/phase2/`. Full local run files remain under ignored `runs/`.
- Phase 2 is complete within the offline scope. Real-model quality, human ratings
  and paid API validation remain unperformed. No Phase 3 work was started.

## Step 1 — Specification and environment
- Saved the complete user request in `SPEC.md` before implementation.
- Workspace was empty; Python 3.12 is available. Pydantic, FastAPI, Uvicorn and HTTPX are installed.
- Cloud environment reports unrestricted networking, no configured model variables or API credentials.
- No paid service has been added or called.

## Next
1. Finish the authorized zero-dollar live-day validation and report its actual
   completion or stop reason. Phase 2 offline deliverables remain complete.
2. Keep later phases deferred. Paid model spending is not authorized.

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
