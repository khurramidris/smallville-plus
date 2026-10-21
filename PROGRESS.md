# Smallville+ progress

## Current status — Phase 3 resumed
- The latest request resumes Phase 3. Implement bounded inference concurrency,
  latency accounting, smaller contexts and safe continuation of chosen routines;
  then rerun offline checks and the three-day real-model experiment.
- The phrase "number thing" is ambiguous; an optional clarification is pending.
  Work proceeds on the explicitly authorized Phase 3. No later phase is assumed.
- Preserve the interrupted run and its reports. Use fresh directories, the same
  authorized free route and the existing zero-dollar cap; add no paid service.

## Previous stop — preserved results
- Phase 3 implementation is complete. Both three-day MockLLM scenarios (25 and
  100 residents) passed their audits and exact event replays; 76 tests pass offline.
- The user stopped the live 25-resident run at minute 1,260 (day 1, 21:00), short
  of the requested 4,320 minutes. Status is `interrupted`, never completed.
- Final live accounting: 947 attempts, 946 successful responses, one uncertain
  interrupted request, $0. The viewer and all simulation processes are stopped.
- See `reports/PHASE3_REPORT.md`. No Phase 4 work or further inference is scheduled.

### Resumption step 1 — Bounded inference and routine execution
- Implemented `--optimized` (four same-time independent decisions, compact
  context and chosen routine continuation), with separate environment controls.
  The GM applies results in scheduler order and rechecks scarce resources.
- Removed network waiting from the budget lock, bounded concurrency and deduplicated
  concurrent identical prompts. In-flight reservations count toward the hard cap.
- Added separate provider/queue timing storage. No timing enters deterministic
  event payloads. Context limits phone history and spells out known reachable
  venues/work minutes; recent refusals include their rejected intentions.
- New tests exercise overlap, budget races, cancellation, cache rerun, event
  replay, routine interruptions and ordered capacity reservation. Six initial
  cases passed; the seventh had a test-only home-ID literal error, now fixed and
  passing. The full suite and optimized three-day offline run are in progress.
- No API calls yet during this resumption; no paid service or later-phase code.

### Resumption step 2 — Offline acceptance and fresh live experiment
- Final suite: **83 tests passed offline in 142.49 seconds**. The preceding
  run had 82 passes and the already-fixed test-only location literal mismatch;
  no production failure was found. Ruff passes.
- Optimized 25-resident fixture completed 4,320 minutes with 2,870 mock calls,
  versus 3,317 previously (13.5% fewer). Wall time 332.999 seconds versus 389.783;
  runs had different competing work, so this is not an isolated speed benchmark.
  All economy audits pass. Full event import is underway.
- A synthetic fixed-100ms provider probe measured peak concurrency four and
  4.07x gateway throughput; this is not a full-engine or API speed claim.
- Verified the exact authorized endpoint still lists zero prompt/output prices.
  Start a fresh three-day original-25 API experiment after offline acceptance,
  preserving the earlier interrupted run and every cost record. Production
  behavior is frozen at `8e2b410`; no later phase or paid fallback is included.

## Phase 3 authorization and scope
- Authorized on 2026-10-21: implement the next phase, then run three simulated
  days. Scope and acceptance are in `PHASE3.md`; original `SPEC.md` is unchanged.
- Inspected the existing engine, GM, apps, prompts, metrics and tests. The cloud
  environment is ready with unrestricted enforced HTTP policy and no bound keys.
- Plan: financial/world foundations; GM/apps/scheduled events; minds/viewer and
  scoring fixes; offline validation; three-day runs and measured report.
- Preserve earlier phase modes. No new paid service or Phase 4 work is included.
- Used the original 25 for live inference and verified the expanded 100-resident
  population offline; the optional population question received no reply.

### Phase 3 step 1 — Financial and civic foundations
- Added conserved integer-cent ledger batches, work contracts with fractional
  cent carry, finite shop/wholesale stock, portable meals, prorated household
  leases and arrears, funded allowances, replenishment and bank transfers.
- Added public news with event evidence, owner-scoped reading state, secret
  ballots, quorum/deadline checks and a funded meal-stock council proposal.
- Added shared event attachments and calendar links. A received invitation's
  host/date/venue controls confirmed attendance; private entries cannot create
  a party. Corrected common written AM/PM invitation time formats.
- Connected scheduled economic/civic events, GM validation, private app context
  and MockLLM fixtures. Earlier phase defaults remain available.
- Validation: 13 new component cases pass offline; lint and compile checks pass.
  Integration/regression, viewer support and final scenario measurements follow.

### Phase 3 step 2 — Research tools and validation
- Added economic conservation/ledger/work-limit audits, financial/resource
  metrics, ballots/news statistics and confirmed shared-event party scoring.
- Viewer now replays personal finances and public shop/council/news state at
  the selected time. Town amounts are clearly separate from real API USD.
- Expanded app authority/privacy and historical viewer tests. The initial full
  regression passed: **59 tests offline in 159.69 seconds**. All 16 current
  Phase 3 component cases also pass; final full-suite verification follows.
- Verified the exact requested free route still has zero published prices.
  Started the 100-resident three-day MockLLM scenario and the original 25-resident
  three-day live experiment, both with an explicit second-day delivery delay.
  The live process received the existing authorized key through hidden input;
  no key file or paid fallback was added. Results remain pending.

### Phase 3 step 3 — Observed stock and interruption fixes
- The expanded diagnostic exposed repeated trips between empty shops: local
  stock observations were lost after leaving. Added owner-scoped, timestamped
  shop observations. Only a visit or a read, evidence-backed supply bulletin
  updates them; remote changes and newer private observations remain private.
- Mock shoppers now use dated observations instead of repeatedly treating empty
  shops as unknown. Scarcity is still allowed to persist; no free goods are added.
- Retained interrupted diagnostics: 100-resident mock reached minute 840 with
  3,038 synthetic calls; live reached minute 410 with 52 attempts (51 known
  responses, one interrupted/uncertain), all $0. Original histories are retained
  in `runs/*-diagnostic` with explicit interruption events and compact reports.
- Added graceful cancellation to record elapsed activity and incomplete status.
  Reading new notices can trigger replanning. Phase 3 tests: **20 passed offline
  in 13.80 seconds**; the preceding full suite passed 62 cases in 153.44 seconds.
- Next: freeze the corrected implementation, repeat final regression and run
  fresh three-day scenarios. No blocked request was bypassed or paid route used.

### Phase 3 step 4 — Contract classification audit
- Corrected a professor/student substring error, unpaid household work,
  `In school`/`Other` source statuses and four-hour part-time limits. Original
  personas and Phase 2 artifacts remain unchanged; only authored contracts change.
- The second corrected-stock diagnostic reached minute 785/100 residents with
  2,204 mock calls; the live diagnostic reached minute 390 with 31 attempts
  (30 known, one uncertain). Graceful interruption now records status correctly.
- Total Phase 3 live diagnostics so far: 83 attempts, 81 known responses and two
  uncertain interrupted requests, all $0. Their reports/histories are retained.
- The preceding full suite passed **65 tests offline in 141.91 seconds**.
  Contract-specific regression tests are added. Finish the complete offline
  three-day scenario before starting the final live run to avoid further churn.

### Phase 3 step 5 — Complete original-cohort offline scenario
- The corrected 25-resident MockLLM benchmark completed **3 days / 4,320 minutes
  each**, with 3,317 synthetic calls and $0 cost, in 389.783 seconds while other
  validation ran concurrently. Full economic/civic measurements are being audited.
- Full regression passed **73 tests offline in 179.49 seconds**. Chromium verified
  the finance panel, corrected professor contract, historical pending council
  state and 25 resident buttons; no page errors or external requests.
- Added two news sequence/backlog regression cases: posts later in the same
  minute remain unread, and the eight-notice attention limit does not lose ties.
  All **30 Phase 3 cases pass offline in 18.11 seconds**. Final full-suite check
  includes these additions. The scenario run uses revision `4525c58`; the later
  change affects notice cursors, not its scripted actions or financial rules.
- The 100-resident three-day scenario is still running. No API run is active.

### Phase 3 step 6 — Scoring and command validation
- Corrected initial-awareness counting when an initialization event contains
  multiple updates for one agent. The initial projection is counted once per
  resident; no extra person or knowledge is inferred from a contract update.
- Recomputed the completed 25-resident report from its unchanged event history.
  All money/food/work-limit audits pass. The council fixture records 15 yes,
  5 no, 5 abstentions and a funded 100-meal policy. Party: 12/20 invited guests
  attended. Mock social results remain scripted engineering evidence.
- Validated CLI scenario settings before creating a run and preserved the run's
  phase when reopening for interviews. All 31 Phase 3 tests pass offline in
  13.66 seconds. The final full regression and 100-resident run are in progress.

### Phase 3 step 7 — Final offline suite and original-cohort replay
- Final production code: **76 tests pass offline in 173.06 seconds**, Ruff and
  formatting pass for 59 Python files. Evidence: `reports/phase3/offline-checks.json`.
- Added a Phase 3 response-cache assertion to the integration test. The targeted
  check passes in 15.40 seconds: 443/443 requests served from cache, no provider
  calls and identical world state except the replay flag. A test-only metadata
  selection typo was corrected; no production cache defect was found.
- Full three-day/25-resident event import matches all state and all 14,528 JSONL
  events byte for byte. Money, food, work limits, ledger balances and all 4,320
  activity minutes per resident pass audit. No inference during verification.
- Saved the completed viewer screenshot/browser checks and corrected run report.
  The 100-resident run is on its third afternoon. Final API inference starts only
  after that completed offline scenario passes its audits.

### Phase 3 step 8 — Expanded scenario completed; final live run started
- **100 residents completed 3 days / 4,320 minutes each**, with 14,076 synthetic
  requests, $0 and 2,260.967 seconds wall time under concurrent validation.
- Audits pass: all 19,873,747 town cents conserved; 974 initial meals equal
  461 eaten plus 513 remaining; ledger matches every account; no overdrafts or
  work-limit violations. Eleven residents owe 27,081 cents of prorated rent.
- Council: 67 yes, 22 no, 11 abstentions; funded 100 additional meals with
  30,000 town cents. Shared-party attendance: 31 of 46 guests receiving details
  across the two-hour window (distinct guests, not simultaneous occupancy).
- Recomputed the derived report with corrected initial-awareness counting.
  Full 100-resident event import is in progress using a read-only source reader.
- Started the final original-25 live run after the completed offline audit,
  using the existing authorized key only in the process environment. Production
  behavior is frozen at `87778b4`; cap remains $0 and no paid fallback is enabled.
- Final API cost/behavior and full replay evidence remain pending. No Phase 4.

### Phase 3 step 9 — Expanded replay and report
- All **59,768** expanded-run events import to identical state and byte-identical
  JSONL. All 100 agents account for 4,320 minutes, and all resource/ledger audits
  pass without further inference. The full log is about 954 MiB.
- Added `reports/PHASE3_REPORT.md` with complete offline measurements, methods,
  fixed defects and limits. Its API section is explicitly pending.
- The final API run is progressing through its first morning with successful
  real requests, no provider failures so far and $0 cost. Keep observing the
  frozen experiment; do not advance to Phase 4.

### Phase 3 step 10 — Recorded stock timeline
- Generated standalone PNG/SVG figures and CSV from 207 recorded stock-changing
  transactions in the completed fixtures. Verified each reconstructed retail
  total against final shop projections. No inference or world writes.
- The figure distinguishes the configured delivery delay, regular replenishment
  and funded council stock purchase. It is labelled as scripted MockLLM evidence.
- The final API experiment continues with the frozen production behavior and
  zero-dollar cap. No provider failures have occurred so far.

### Phase 3 step 11 — User-requested stop and final accounting
- Cancelled the API run immediately on the user's stop. Graceful cleanup records
  1,260 of 4,320 minutes, an explicit operator interruption and final observations.
  Stopped the local viewer too; no simulation, verification or viewer process remains.
- Final API ledger: 946 successful responses and one interrupted/uncertain call;
  3,261,849 known input / 252,265 known output tokens; $0 under the $0 cap.
  With prior diagnostics: 1,030 attempts, 1,027 known responses, three uncertain.
- At interruption, all financial/resource/work-limit audits pass. Eighteen
  ballots and 25 messages are recorded. The council remains open and the party
  lies beyond the observed period; no live three-day or party result is claimed.
- Saved the interrupted report and final progress record, updated the phase
  report, and preserved complete offline experiments and immutable partial history.
- Open work: the requested three-day live run is unfinished, partial live replay
  is unverified, and realism/planning/storage limits remain documented. Do not
  resume development or inference without a subsequent user request.

## Historical follow-up — Phase 2 live inference
- **Completed.** The 25-resident real-API day passes; evidence and problems are
  in `reports/LIVE_API_REPORT.md`. Development remains stopped at Phase 2.
- The user authorized the exact OpenRouter route
  `minimax/minimax-m3.1-flash:free`. Verified published zero prices, used a hard
  `SIM_MAX_USD=0`, disabled paid/provider fallbacks and retries, and kept the key
  only in the active process environment after hidden terminal input.
- Added zero-price/free-route support, timeout/reasoning environment controls,
  cache identity for reasoning settings and sanitized provider HTTP diagnostics.
- The first town request failed under the 45-second timeout. A low-effort
  diagnostic exposed ambiguous location targets on non-move actions. Preserved
  both attempts, clarified the prompt and added readable date/time context.
- Final live day: **25/25 residents, 1,440 minutes each, 908 successful API calls,
  1,924,730 input / 163,254 output tokens, no API failures, $0 total and $0 per
  resident/day.** Wall time: 3,201.746 seconds. All live/debug stages total 950
  provider attempts and $0; two diagnostic requests retain uncertain usage.
- Full regression: **45 tests pass offline in 106.21 seconds**. Ruff/formatting
  pass. Complete cached rerun: 908/908 hits, no provider calls, identical world
  state except the replay flag. Event import replay and all 4,053 SQLite/JSONL
  records match exactly.
- Chromium verified the completed day: 25 residents, five needs, a real plan and
  the 908-request zero-dollar dashboard; no page errors or external requests.
- Observed 9 routine-plan fallbacks, 1 invalid intention, 2 rejected reflections,
  30 GM refusals and 44 messages. Sam awareness stayed 1/25; party awareness
  reached 3/25. Coordination and uncalibrated time use remain research problems;
  the party attendance window lies beyond this one-day run.
- Monitoring uses the read-only viewer/SQLite interface. A debug writer/recovery
  reader race required no repair; the complete final event mirror is intact.
- Key values are absent from project files and logs. No paid route, 100-resident
  live day, real Twin/GSS fidelity evaluation or Phase 3 work was performed.

### Live-day behavior review — 2026-10-21
- Read the completed messages, calendars and action events through read-only
  SQLite to answer the user's request for a narrative summary. No new API calls.
- Corrected the report: Isabella sent two complete party invitations, both
  accepted. The machine count of zero misses the written `5:00 to 7:00 p.m.`
  time format; original metric artifacts are retained unchanged.
- Found a date/coordination defect: Carlos booked and attended his own party
  entry on February 13, while the host's event is February 14. The GM accepted
  his calendar without checking a matching host event. Actual party attendance
  remains outside the run's horizon.
- Recorded coffee, literature, performance and election storylines, while
  separating plans/co-location from confirmed communication and outcomes.
- Open issues for later authorized development: time parsing, shared-event/date
  validation, repeated meals/trips and stale plans. Development remains stopped
  at Phase 2; this review changes documentation only.

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
- None scheduled: the user requested a stop. Phase 3 implementation and offline
  validation are complete; the live three-day experiment remains incomplete.
- Phase 4, human/model fidelity ratings and paid spending remain outside this work.

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
- (d) One real-API day under cap: **passed** on the subsequently authorized
  MiniMax free route: 25 residents, 908 calls, $0 within a $0 cap. See
  `reports/LIVE_API_REPORT.md`. Paid-model pricing remains unvalidated.
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
