# Smallville+ progress

## Connected realism implementation, batch 3 — in progress 2026-10-22
- R2 step 1, social state and attention: added replayable directed relationship
  state with separate trust, affinity, familiarity and obligation dimensions.
  Signed changes require an explicit resident appraisal and witnessed turn IDs;
  ordinary contact can increase familiarity without guessing sentiment from text.
- Added decaying social emotion impulses, preserving an interaction's effect over
  simulated time while needs still shape the underlying mood. The connected path
  no longer treats substrings such as `disagree` as a relationship judgment.
- Added per-resident phone-attention state and bounded message reads. Connected
  perception exposes sender/time/urgency summaries without unread bodies; a check
  prioritizes urgent mail, reads at most two messages and records its time/count.
- New focused tests cover bounded urgent-first reads, hidden unread bodies,
  asymmetric evidenced appraisal, private-evidence rejection and emotion decay.
  Fourteen affected foundation tests passed at this step.
- R2 step 2, consent and private scenes: added conversation-app proposals for one
  to three invitees, independent accept/refuse responses, response deadlines,
  calendar/travel/accepted-scene conflicts and explicit start/end state. Accepted
  commitments block ordinary actions that would run across the scene start.
- Conversation turns store the actual speaker, text, action and listener set.
  Only accepted active participants receive observations and memories; co-located
  bystanders receive neither. Statements enter listener knowledge as attributed
  testimony rather than world truth.
- A participant may leave on their own turn. The scene continues with two or more
  people and ends when fewer remain or its scheduled window closes. Direct service
  tests cover a willing invitee, an explicit refusal, a busy nonresponse, a
  three-person scene, false testimony, private routing, appraisal and departure.
  All 16 affected world/GM/social tests passed at this step.
- R2 step 3, scheduler/model integration: the engine now books scene starts and
  ends, obtains each turn from that speaker's private context, records the
  intention separately from the GM-committed utterance, and releases participants
  on departure or ending. MockLLM independently accepts/refuses using directed
  trust, checks a bounded inbox, proposes at most one scene per day and can
  disagree or leave. A focused engine test proves turns run through the scheduler,
  exclude a co-located bystander and release both participants.
- The first full-day probe exposed accumulated plan-repair seams at the 32-block
  bound. Equivalent adjacent blocks are now normalized after every repair; a
  regression performs 40 repairs without growing the plan. The next probe exposed
  a host walking away after inviting others. GM commitment checks now reserve both
  action time and the return travel needed to reach the accepted scene.
- A 25-resident one-day Phase 3 probe completed all 1,440 minutes before the travel
  fix with 21 proposals, two started scenes, eight independently generated turns
  and 19 expired/unavailable cancellations. This is diagnostic evidence: the low
  start rate is visible and is not presented as a realism success. Metrics, viewer
  inspection and final replay/full-suite gates are next.

## Connected realism implementation, batch 2 — completed 2026-10-22
- Continued the ordered plan by completing the R1 engineering gate. R2 social
  scenes and later institutional/scale work remain outside this batch.
- Step 1, connected histories: population artifact version 3 replaces a single
  generic ring partner with recurring household, workplace and friendship ties.
  The final historical exchange is an explicit request and acceptance. Every
  resident begins with one private unfinished promise due after the epoch; version
  2 artifacts remain loadable for legacy baseline runs.
- Step 2, durable goal lifecycle: accepted promises bootstrap as commitment goals
  with deadlines and evidence. Residents can revise, block, reactivate, complete
  or abandon only their own goals through a five-minute GM-validated action.
  Completion requires evidence from the resident's working or archived memory;
  every transition is recorded in `goal_history` for replay.
- Step 3, episodic archive: capacity eviction now emits owner-scoped
  `memory_archive` changes in the same event transaction as the agent update.
  Connected retrieval ranks working and archived memories together through the
  explicit `local_lexical_v1` fallback while returning only a bounded result.
- Step 4, bounded planning: a surprise repairs only the future part of today's
  plan. Elapsed blocks remain immutable. Repair accounts for known walking time,
  opening hours and appointments, and exposes infeasible conflicting appointments
  rather than double-booking them. Decisions also receive a known-feasible action
  set without remote stock, occupancy or other hidden state.
- Step 5, inspection and metrics: the viewer exposes goals, transitions and recent
  archived episodes. Reports separate working/archived evidence and include goal,
  archive, full-plan and repair-fallback diagnostics.
- Step 6, gates: the suite now contains **122 offline tests**. Added cases verify
  500-event commitment survival, archive privacy, bounded archive retrieval,
  goal ownership/evidence/abandonment, closed-shop repair, walking time and a
  conflicting appointment. Ruff and whitespace checks pass.
- Step 7, measured smoke: a fresh 25-resident version 3 artifact has 21 history
  days, 1,050 messages, 75 calendar entries and digest
  `227c856e91acb3160d61e50b582646b8ec9a40e237bf87cff0bb178a6bc7ccc1`.
  One Phase 3 day completed in 45.466 seconds with 748 MockLLM calls, 100 goals,
  25 accepted commitments, 25 full plans and 104 bounded repairs. Both full-plan
  and repair fallback rates were 0%; cost and uncertain calls were zero.
- Step 8, replay: all 3,993 events replay byte-identically with JSONL SHA-256
  `408d147c2a0af53b6612dcbb1882d1ca1751e3768d83e2cf7048c66567286150`.
  All material projections, including goals and archives, match. The 42,995,236
  byte log confirms full snapshots remain a scale bottleneck.
- No provider API, network dependency or paid service was used. MockLLM behavior,
  a 0% fixture fallback rate, or Sam's retained-awareness count matching the paper
  is not evidence of greater human realism.
- Next: R2 consent-based multi-turn conversations with independent participant
  decisions, bounded attention and asymmetric relationship appraisal.

## Connected realism implementation, batch 1 — completed 2026-10-22
- The user authorized implementation of the new realism plan. This batch covers
  the R0 evidence foundation and a bounded subset of R1; R2 social scenes and
  later stages remain outside this change.
- Step 1, evidence and reproducibility: added owner-scoped campaign claim records
  with attribution, candidacy status, epistemic status, source, timestamps,
  confidence and retained-memory linkage. Exposure, accepted self-knowledge,
  retention and human-assessed interview recall are reported separately. The
  legacy diffusion score remains present for historical comparison.
- Step 2, people and cognition: added durable goal records, protected identity
  memories, repeated-outcome coalescing and context-sensitive lexical retrieval.
  The opt-in `connected_v1` profile requires a validated population with complete
  life histories and at least 14 history days; it supplies active goals, relevant
  personal relationships, current place/people/needs and appointments to retrieval.
- Step 3, diagnostics: the request ledger records purpose; intention events report
  accepted/fallback/reused plans and actions plus reflection results; perception
  events count co-presence and unread-phone opportunities. Evaluation output now
  carries `realism-eval-v1` configuration, population digest and measurement rules.
- Step 4, tests: added 32 labeled campaign statements, a 500-event memory flood,
  knowledge/privacy/retention checks, rich-cohort launch checks and request-purpose
  accounting. Ruff passes and **119 tests pass offline** with network disabled.
- Step 5, operational smoke: generated 25 residents with 21 history days, 1,050
  messages, 75 calendar entries and digest
  `ddf8133c5210546ae26205b0f5971e9a856a85ff09ec9f34935daf43da157f09`.
  The final Phase 3 day completed in 70.716 seconds with 761 MockLLM calls, 75 goals,
  eight structured campaign records, zero uncertain calls and $0 cost. Mock token
  counts are synthetic and do not predict provider billing.
- Step 6, replay: all 4,030 events replayed with byte-identical JSONL SHA-256
  `b1f5eeabcfd36fbe5dca2729cea97f2504b607aebf7daa0a271b823351271f51`.
  Agent, goal, knowledge, message, calendar and metadata projections match. The
  41,675,392-byte event log confirms full snapshots remain a scaling problem.
  An earlier byte-identical run took 42.987 seconds, so host wall time is not a
  stable performance benchmark.
- No network or provider API was used and no service was added. This work does
  not show that Smallville+ is more realistic than Park et al.; the run is a
  deterministic engineering fixture.
- Next: finish R1 with connected histories and unfinished obligations, archived
  episodes, explicit goal changes and bounded plan repair; then implement R2
  consent-based, multi-turn interaction. Run controlled real-model comparisons
  and human evaluation only after those behavioral gates pass.

## Realism audit — completed 2026-10-22
- The user asked why complexity/realism still falls short of the original goal
  and requested an evidence-based development plan. This step audits code,
  retained upstream references and existing runs; it does not start Phase 4.
- Initial findings: bounded keyword memory, a narrow action vocabulary, simple
  needs/relationship heuristics, a minimal GM and unused Phase 2 histories in
  the completed live cohort. Functional completion is distinct from validated
  realism. Detailed trace analysis and a prioritized plan are in progress.
- Step 2: read-only trace audit covers all 16,149 events and 3,340 cached real
  responses. All 25 memory buffers reached 128 entries; only 2/62 original seed
  memories survive. Found 55 invalid-plan fallbacks and 8 failed reflections.
  The 25 completed ambiguous attempts changed only the actor projection and
  recorded no wider confirmed outcome. No additional provider calls were made.
- The campaign scorer also misses Sam's message to Adam about considering a
  mayoral run and Adam's encouragement. Its reported zero is narrow retained
  phrase evidence, not proof that nobody knew. Preserve historical numbers and
  explicitly plan a better evidence/recall measurement before comparative claims.
- Step 3: saved `reports/REALISM_AUDIT.md`, reproducible diagnostic script/data,
  and `REALISM_PLAN.md`. The plan prioritizes measurement repair, active goals,
  contextual memory, richer live personas, real conversations and consequential
  actions before broader institutions, Graphiti/30-day runs and population scale.
- Defined offline invariants, labeled behavioral cases, controlled pilot/paired
  runs, human ratings and survey/time-use validation as separate acceptance gates.
  No new provider calls, services, upstream code, or simulation behavior changes.
- Next proposed implementation boundary: R0 and core R1 from `REALISM_PLAN.md`.
  This turn delivered the requested investigation and plan; later stages are
  recommendations, not completed or automatically scheduled work.
- Step 4: the audit rerun produces byte-identical JSON. Checked its totals against
  the saved acceptance report and verified the original event-log checksum is
  unchanged. Ruff/format/whitespace checks and all local audit/plan links pass.
  Production simulation code is unchanged; no full simulation/test rerun needed
  for this read-only investigation and documentation task.

## Current status — Phase 3 completed and verified
- The optimized real-model run completed all 4,320 minutes with 25 residents.
  Both optimized three-day offline scenarios (25 and 100 residents) also completed;
  83 tests pass offline. Final real-run event/cache replay and viewer checks pass.
- Interpreted "number thing" as item 1, performance/planning improvements, after
  optional clarification received no answer. No later phase is included.
- The full real experiment used 3,342 provider attempts, including two requests
  whose usage was lost during an environment restart, at $0 published free-route
  prices. Recovery reused 1,500 responses without repeating completed API calls.
- Preserve every interrupted attempt and cost record. No further inference is
  needed, no paid service was added, and Phase 4 has not started.

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

### Resumption step 3 — Exact optimized replay and live inference
- All 14,679 optimized original-cohort events reproduce identical state and JSONL
  bytes. Every resident accounts for all 4,320 minutes; all conservation audits pass.
- The fresh authorized API experiment has begun with real overlapping requests,
  zero recorded USD and no provider failures so far. Timings now distinguish
  provider duration from time waiting for a concurrency slot.
- The expanded optimized 100-person offline scenario is also running. Preserve
  production behavior and retain all earlier diagnostic/interrupted artifacts.

### Resumption step 4 — Expanded optimized scenario completed
- All 100 residents completed 4,320 minutes. The run used 12,141 mock calls
  versus 14,076 previously (13.7% fewer), and 51,851,835 synthetic input tokens
  versus 88,642,393 (41.5% fewer). Wall time was 1,686.868 seconds versus
  2,260.967 under different competing work; timing is descriptive.
- All 19,873,747 town cents remain conserved. The 974 meals reconcile as 468
  consumed and 506 remaining; account/ledger/work-limit audits pass.
- Eleven residents owe 23,081 cents of rent; eleven are hungry without meals.
  Confirmed party attendance: 29 of 49 guests receiving details. These are
  scripted fixtures and attention/timing changes can change their behavior.
- Full expanded event replay is in progress. The live API run continues through
  day one's evening with no provider failures so far and recorded cost $0.

### Resumption step 5 — Expanded replay accepted
- All 59,359 expanded-run events reproduce byte-identical JSONL and identical
  state. All 100 residents account for 4,320 minutes; conservation, account,
  ledger and work-limit audits pass. No inference during verification.
- Retained all reports and hashes. The live first evening reached 21:00 after
  approximately 36 minutes, compared with 84 for the previous interrupted run.
  Different responses, attention cadence and in-flight work prevent a controlled
  speed claim; `optimized-live-first-evening.json` preserves the actual sample.
- Remaining: finish the live three-day horizon, verify complete cached/event
  replay, capture the final viewer and publish final timing/cost/behavior results.

### Resumption step 6 — Viewer source labels
- Corrected the research viewer footer to distinguish recorded live-model
  decisions from MockLLM fixtures. It still discloses unvalidated believability.
  No inference, scheduler or world rule changed from `8e2b410`.
- System Chromium verified 25 resident controls, live-source wording and the
  inspector with no page errors or external requests. Final completion and
  party-time screenshots will replace the interim capture after the run ends.
- The live experiment has entered its second day, with $0 recorded cost and no
  provider failures so far. No additional paid service or later-phase work.

### Resumption step 7 — Populated history/privacy regression
- Strengthened the compact-context case with twelve own sent messages, twenty
  future appointments, a past appointment and another person's private inbox.
  It verifies the exact retained messages, appointment limit and inbox isolation.
- The targeted offline check passes in 0.79 seconds; the complete preceding
  83-case suite remains recorded. No simulation or inference code changed.
- The live run has reached the Valentine's party window on day two. Attendance
  will use completed, confirmed actions rather than intentions or co-location.

### Resumption step 8 — Environment interruption and guarded recovery
- The execution environment restarted and killed the live process at minute
  2,490 (day 2, 17:30). Preserved 1,500 successful responses and two in-flight
  requests with unknown usage, all at $0 published prices. Finalized that attempt
  as interrupted; no completed outcome or token usage was invented.
- Saved the committed world-state checksum before finalizing the interruption.
  Inference/scheduler/GM code is still byte-identical to `8e2b410`.
- Prepare a fresh run using a copied response cache. Before its first new API
  request, require all 1,500 cached decisions, the same simulated minute and an
  identical world-state checksum. Preserve the old journal and separately sum
  prior/new actual requests; no paid budget is reset or new service added.
- The environment is ready again. Recovery will re-execute the cached prefix
  locally, not repeat its completed API calls. Direct scheduler checkpoints
  remain a later architectural task.

### Resumption step 9 — Cached recovery verified; live run continued
- Reconstructed all 1,500 cached decisions with zero new provider dispatches.
  At minute 2,490, every world projection matched the pre-interruption checksum
  `b001482b9390874fd7fb865260deef1c12e95b5bc77aa1868fb95a147b1c93f9`.
- The guard passed before forwarding the first new request. The same free model
  is continuing in `runs/phase3-resumed-live-25/`; old journals/cache are retained.
- Whole-experiment accounting will add prior and new actual usage once and keep
  the two unknown interrupted requests visible. The new attempt's cache hits do
  not represent new provider calls. Both attempts retain the $0 cap.

### Resumption step 10 — Live council outcome and viewer wording
- The real-model council vote closed on day 3 at noon: 21 yes, 3 no, no explicit
  abstentions; 24 of 25 eligible residents voted. The passed policy spent 30,000
  town cents moving 100 existing wholesale meals to the market. Cash stays conserved.
- The party window completed with three confirmed guests (Maria, Ryan, Tamara),
  with Isabella hosting. The final evening and end-of-run audits remain pending.
- Changed the viewer label to "Recorded plan", so an end-of-window midnight
  snapshot does not imply that a new day has already been planned. Presentation
  only; simulation behavior remains unchanged at `8e2b410`.

### Resumption step 11 — Three-day real run completed
- Verified the saved report after resumption: status completed, 25 residents,
  4,320 minutes, no run problem. Known usage across both attempts is 13,105,152
  input tokens and 794,401 output tokens. Total published-rate cost and cost per
  resident-day are $0; two interrupted requests have unknown usage.
- Three of four invited guests attended (Maria, Ryan, Tamara). The 21–3 council
  vote funded 100 meals; all saved economy audits pass, with no rent arrears and
  three residents hungry without meals at the endpoint.
- No simulation or viewer process remained active when checked. Started fresh,
  provider-forbidden cache verification and independent event import. Final
  screenshots, timing exports and consolidated reporting follow those checks.

### Resumption step 12 — Final viewer and latency evidence
- Chromium verified the completed real-model viewer and party-time replay: 25
  resident controls, correct source label, no page errors or external requests.
  Saved and visually inspected both screenshots; the viewer remains schematic.
- Combined both provider journals for 3,340 successful request timings, excluding
  cache hits and the two uncertain requests. Median 3.62 seconds, p95 10.18,
  mean 4.50. Saved CSV, PNG, SVG and summary; visually checked the figure.
- Updated the final progress record and consolidated report with completed
  outcomes, whole-experiment cost, interrupted history and realism limitations.
  Independent event/cache verification is still running; no provider is available
  to the cache verifier. README now reflects the authorized Phase 3 stop boundary.

### Resumption step 13 — Final acceptance and stop
- Imported all 16,149 real-run events into a fresh destination. Every projection
  and the JSONL bytes match; SHA-256 is
  `00f977f2ae32d08c58b1369726bb2c26011e4bc2bbfb0217c22e35bf5b98b452`.
  All 25 residents account for 4,320 minutes; all five economic audits pass.
- Re-executed the entire real-model scenario using 3,340/3,340 cache hits with a
  backend that forbids provider access. Every world table matches except the
  explicit replay flag; zero provider calls, 180.432 wall seconds.
- Retained final reports, cost/latency data, screenshots, cache/event verification
  and earlier incomplete attempts. Ruff and whitespace checks pass. No further
  simulation, interviews, paid service or Phase 4 development is scheduled.
- Stopped the temporary viewer after browser verification and confirmed that no
  simulation, verification or viewer processes remain active. Final evidence
  statuses pass; tracked/proposed files contain no supplied-key patterns.
- Next: no work until a new instruction. Remaining research issues are the
  report's planning/coordination failures, unvalidated human realism, snapshot
  storage costs and later-phase memory/scale work; Phase 3 acceptance is complete.

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
