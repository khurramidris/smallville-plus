# Decisions

## Phase 3 resumption — Performance and planning
- Resume only the clearly authorized Phase 3 while clarifying the ambiguous
  numbered item. Preserve prior incomplete experiments rather than rewriting them.
- Batch independent decisions at the same simulated minute against a fixed world
  view, then apply intents in scheduler order through the GM. Never advance time
  or publish another person's decision while these decisions are in flight.
- Bound provider concurrency and reserve budget atomically before dispatch.
  Keep timing outside deterministic event payloads; report measured latency
  separately from synthetic fixtures and total wall time.
- Reuse only a person's previously chosen routine for a bounded interval, with
  interruptions for new information, needs, appointments and world rules.

## User-requested stop — Phase 3
- The explicit stop overrides the outstanding three-day live objective. Cancel
  inference, stop the local viewer, preserve partial artifacts and report the
  actual horizon without starting further development, interviews or replay jobs.
- Keep the completed three-day MockLLM runs distinct from the interrupted API
  run. Record its 946 known responses plus one uncertain call; exclude unknown
  usage from measured tokens and keep the zero-dollar published-rate caveat.
- Leave the incomplete live experiment and remaining research limitations visible.
  Phase 4 is not started and no work is scheduled after the stop.

## Phase 3 — Authorized scope and design
- The latest request authorizes Phase 3 and a three-day simulation. Preserve
  earlier reports and run modes; do not begin Phase 4 or add a paid service.
- Use integer cents and explicit conserved account transfers for wages, rent,
  bank transfers and shopping. Arrears are obligations, never negative balances.
- Use fictional, documented economic rates and daily prorated household rent;
  demographic survey data is not evidence of a person's actual finances.
- Make shop supply finite and replenishment funded. Agents retain control over
  work, purchases, voting and reading public news; do not script live success.
- Record municipal proposals, ballots, policy execution and event evidence as
  replayable state. Keep private ballots/balances out of other agents' contexts.
- Correct the invitation parser and validate shared event dates against received
  invitations. Preserve the old live day as an unchanged research artifact.
- Keep population artifact models unchanged: new financial, ballot and event
  links live in separate projections so Phase 2 digests remain valid.
- Seed a host-owned Valentine event from the original benchmark goal. Only its
  host and people who read an invitation can inspect its details. Verify host
  presence and distinguish private calendar time from confirmed shared attendance.
- Recheck shopping funds/stock and ballot eligibility at completion. A scarce
  item claimed by someone else produces a failed outcome with no partial debit.
- Carry fractional wage cents between work periods, cap daily work minutes and
  record unpaid earnings separately when an employer has insufficient cash.
- Keep bank memo text separate from the authoritative transaction purpose, so
  a resident cannot label a personal payment as earned wages in the metrics.
- Report the town's fictional cents separately from real API USD in all views.
  Resource audits reconcile initial goods with both remaining and eaten meals.
- Use the original 25 for live inference, matching the previous experiment, and
  the existing validated 100-resident artifact for the offline three-day test.
  The optional population question received no reply before this default was used.
- Explicitly configure a second-day delivery delay for the pressure scenario.
  Existing stock remains available, supply stays finite, and the council's
  policy can spend only actual treasury funds on remaining wholesale goods.
- Preserve last-observed shop stock with its observation time and source. A
  remote sale does not alter an absent resident's knowledge; reading an older
  bulletin cannot replace a newer personal observation. New supply information
  enters through ordinary perception or the owner's phone, never omniscience.
- Retain the interrupted early runs as diagnostics and use fresh directories
  after the stock-knowledge fix. Their calls/costs stay separate from the final
  three-day measurement. Record cancellation as incomplete, not initialized or
  successfully completed, while retaining uncertain call reservations.
- Prefer explicit source work status over descriptive prose. A professor's
  mention of students does not make her a student; household work does not imply
  freelance income. Treat part-time employment as a four-hour daily contract and
  nonemployment/unknown statuses as disclosed support assumptions.
- Complete the full corrected offline scenario before the final API experiment.
  Keep diagnostic calls visible in the all-stage ledger instead of hiding them
  inside a successful three-day runtime average.
- Use event sequence cursors for unread public news, not timestamps alone:
  multiple posts can commit within one simulated minute. Keep a finite eight-
  notice read limit without dropping later or unselected posts at the same time.
- Reconstruct initial agent state using the last update for each ID in the
  initialization event. Counting each update would double initial awareness in
  Phase 3, even though only one resident exists. Recompute derived reports from
  the immutable history; do not rewrite the underlying events.
- Validate scenario options through Config instead of unchecked model copies,
  and reopen research interviews using the recorded phase's rules and app context.
- Verify both event import and a Phase 3 response-cache rerun. Event history must
  reproduce bytes/state exactly; cached inference must reproduce the same world
  apart from the explicit replay flag. Keep production code frozen for live data.
- Count distinct party guests over the full observation window separately from
  instantaneous venue capacity; turnover can produce more unique visitors than
  available places. Invitation metrics include received shared-event details.
- Use read-only SQLite inspection for completed large-run verification, avoiding
  a writer constructor and its JSONL recovery pass on the source. Replay writes
  only to a fresh destination and is checked by streaming SHA-256 plus state.
- Plot retail stock from committed purchases/replenishment/policy transfers and
  reconcile the endpoint, rather than inferring stock from agent descriptions.
  Label closed-shop stock and scripted-fixture provenance; global remaining food
  alone does not establish that a hungry resident could access or afford it.

## Live API follow-up — Exact free route and zero spending
- The user's latest instruction authorizes OpenRouter calls using the supplied
  model. Keep development at Phase 2 and preserve the earlier mock measurements.
- Use LiteLLM's `openrouter/` provider prefix, with the exact requested `:free`
  model; use `SIM_MAX_USD=0` and catalog-verified zero prices. No paid fallback or
  automatic retries. Also send provider maximum prices of zero.
- Permit zero prices only for explicit OpenRouter `:free` routes. Priced models
  still require a positive cap and conservative token ceilings.
- Read the key through hidden terminal input and inject it into
  `OPENROUTER_API_KEY` only in the active process. Do not save a key file.
- Preserve sanitized HTTP status codes for actionable auth/quota failures;
  provider error strings remain excluded from logs and reports.
- Configure `SIM_REASONING_EFFORT=low` and a 180-second timeout for the fresh
  MiniMax attempt: its catalog declares mandatory reasoning with a `max` default.
  Include the reasoning parameter in cache identity. Preserve the initial failed
  run rather than silently retrying it or claiming full-day completion.
- Real API validation revealed an ambiguous action contract. Clarify the prompt
  (`target=null` except for movement), rather than relaxing GM checks or silently
  rewriting model intentions. Supply readable date/time alongside minute indices
  to avoid morning/evening confusion. Preserve the interrupted attempt as evidence.
- Monitor a running town with the existing read-only viewer/SQLite interface.
  `WorldState` is a writer constructor that runs export recovery; reopening it
  while another process appends is not a supported observation path. Verify the
  finished SQLite/JSONL history and cached replay before claiming acceptance.
- Record the completed 908-request day separately from 42 debugging/probe
  attempts. Both cost $0, but uncertain diagnostic usage must not be described
  as measured tokens. Report published-rate accounting separately from invoices.
- Verify exact event replay and a whole-day response-cache rerun with the provider
  backend disabled. Both pass. Preserve poor diffusion/coordination and model
  validation failures as research findings; do not script successful benchmarks.
- This fulfills the earlier real-API day criterion using the user's specified
  free model. It does not validate paid prices, real-model Twin/GSS fidelity or
  the expanded population on API inference. Stop before Phase 3.

### Live-day narrative review
- Base the resident summary on read-only messages, calendar dates and completed
  action events. An intention or overlapping locations does not establish that
  a conversation or performance happened.
- Preserve original machine metrics and explicitly annotate the invitation
  parser false negative: two actual host invitations use a time format the
  scorer does not recognize. Do not equate a zero detector count with no invites.
- Report Carlos's day-early attendance as a scheduling/GM consistency defect,
  not as successful party coordination or evidence of realistic forgetfulness.
  Document the fix as future work; the user requested a summary, not a new run.

## Phase 2 — Authorization and research boundaries
- The user's new instruction advances development to Phase 2 only. Keep the
  original specification and Phase 1 evidence intact, and add `PHASE2.md` for
  the new work. Paid inference remains unapproved.
- Use only the public demographic agent bank, not the restricted real-interview
  bank. Label expanded life histories and digital messages as fictional.
- Keep held-out human answers outside prompts, persona generation and repair
  feedback. Report missing/invalid predictions and dataset coverage explicitly.
- Preserve the default 25-resident workflow while accepting a versioned validated
  population artifact for expanded runs. Extend the map with residential units
  rather than overfilling the original homes.

### Phase 2 step 1 — Data, time and validation
- Preserve duplicate GSS names and distinguish people by source-based resident
  IDs. Names need not be unique in a realistic town.
- Model new housing as apartment-unit entrances at three accessible map points.
  These are authored map assumptions, not new geometry copied from upstream art.
- Allow past messages, memories and calendar records to use negative epoch
  minutes. Simulation events and runtime app scheduling remain nonnegative.
- Compile reciprocal message exchanges and paired calendars from short style
  templates. Validate ownership, dates, opening hours, capacity and travel gaps;
  prohibit future party/campaign information in pre-populated phone templates.
- Retain source facts and original seed goals independently of generated prose.
  A failed survey/schema check causes bounded regeneration; unresolved profiles
  prevent publishing a population.
- Keep gold and prior test–retest answers in separate scorer fields. Penalize
  invalid/missing predictions rather than reporting accuracy only on successes.
- Read lightweight event fields for metrics instead of retaining every full
  agent snapshot in memory when evaluating the expanded population.

### Phase 2 step 2 — Repair and scoring semantics
- Add the consistency-attempt revision to the survey request. Reusing an old
  failed answer after regenerating an identical biography would defeat repair;
  versioning the request fixes that without sacrificing reproducible caching.
- Validate the immutable source facts and original seed memories again at launch,
  independently of the artifact digest and recorded survey pass flags.
- Preserve human missingness and unsupported catalog encodings. Score only cells
  with a valid human target, but count missing/invalid model answers as failures.
  Report valid-only numerical MAE alongside penalized normalized error.
- Keep human targets and prior repeated answers outside SurveyRunner inputs.
  A regression test changes those values and proves model requests/predictions
  remain identical through response-cache hits.
- Use a separate masked-profile cohort for fidelity evaluation. Giving town
  residents all their source facts is appropriate for consistency checks, but
  would not be a valid held-out prediction benchmark.

### Phase 2 step 3 — Interpretation and stop boundary
- Report preparation, simulation and fidelity as separate ledgers rather than
  mixing setup inference into per-day runtime costs. All measured USD is mock $0.
- The real source subset supports infrastructure validation; MockLLM's hashed
  categorical choices and numerical midpoints are deliberately not a fidelity
  claim. Human test–retest and missingness are reported alongside those fixtures.
- Keep the entire population and large SQLite/JSONL files local under ignored
  `runs/`; retain compact evidence, a sample biography and a viewer screenshot.
- Display readable location names in life stories while preserving canonical IDs
  in artifacts and app requests for exact replay.
- Stop at Phase 2. Paid API compatibility/cost and semantic life-history quality
  remain unvalidated, and the earlier Phase 1 paid-day acceptance remains pending.

## Step 1 — Scope and operating boundaries
- Build only Phase 1. Full life histories, survey-based regeneration, digital histories, financial simulation and external long-term memory remain deferred.
- Use an ordinary local Python package and FastAPI replay viewer; no hosted service is needed.
- No paid calls before user approval. The configured environment currently has no model credentials. Implement and test the LiteLLM boundary offline first.
- Use the available Python 3.12 runtime while requiring Python 3.11 or newer.
- Keep specification, progress, rationale, provenance and acceptance evidence in the repository.

## Step 2 — Sources and research claims
- Keep upstream seed/map files unmodified; implement the adapter and behavior
  code independently. Preserve exact provenance and license notices.
- Use original collision tiles for routes and a schematic viewer; do not fetch
  externally referenced sprite art.
- Treat MockLLM as a deterministic engineering fixture, not evidence of emergent
  social behavior. Paper comparisons must include this caveat and denominators.
- Use a single ordered event writer with SQLite WAL. Atomically persist event
  plus state changes, then mirror JSONL; recover a missing/truncated mirror tail
  from SQLite on reopening. Reject conflicting prefixes.
- Represent time as integer minutes from 2023-02-13 UTC. Action completion
  events precede decision events at the same minute. No wall-clock sleeps.

## Step 3 — World implementation
- Use the map component connecting the most named sectors for accessible location
  representatives. This preserves all source collisions and connects all 19 places.
- Keep immutable events authoritative and projections transactional; replay
  reconstructs state without inference. SQLite append-only triggers plus a hash
  chain detect accidental mutation, not adversarial filesystem rewriting.
- Reserve all future schema slots (objects, inventories, accounts and jobs), but
  do not add wages, rent, market simulation or finance apps in Phase 1.

## Step 4 — Bounded inference
- Require explicit conservative USD/token ceilings for each selected live model.
  Reserve UTF-8 prompt bytes plus framing and the entire output-token limit before
  dispatch. Unknown prices fail closed; no retries or hidden fallbacks.
- Retain the full reservation on timeout/cancellation/failure because a provider
  may have accepted and billed a request. Provider exception bodies are never logged.
- Report token-based accounting separately from provider invoices. The bound
  assumes configured tariffs cover all billed text/reasoning tokens and the
  provider honors output limits; tools, images and external retrieval are unsupported.
- Cache exact responses, not just seeds: live APIs are not guaranteed deterministic.
  Offline replay requires a cache hit or uses the immutable event history.
- Keep mock-specific benchmark behavior entirely inside MockLLM; the engine and
  GM still validate every intent and apply every outcome.

## Step 5 — Minds and apps
- Keep persona generation, weeks of digital history and survey consistency
  regeneration in Phase 2. Phase 1 loads the original seeds with explicit
  synthetic speech/sampling/needs parameters.
- Agent perception exposes only co-located public activity and the owner's phone.
  The researcher viewer can inspect private notebooks; agents cannot use it.
- Resource guards and finite initial food/balances support Phase 1 rule checks;
  wages, rent, shops and a financial economy remain deferred.
- Calendar entries represent intentions. Attendance still requires choosing an
  action, travelling and passing GM checks at the right time.

## Step 6 — Evaluation and final validation
- Count specific campaign evidence rather than mere election-topic mentions.
  Sharing a complete party schedule requires having received its place and time.
- Retain the actual initial relationship density instead of adjusting it to the
  paper's 0.167 baseline; report that experimental mismatch explicitly.
- Compare coarse time-use shape with ATUS 2024, with differences in population
  and activity taxonomy disclosed. Human believability ratings remain uncollected.
- Check agent-specific condition predicates after that agent changes state,
  avoiding expensive town-wide state reads after every event.
- Persist the original run spending cap in the call ledger, so reopening a run
  with a larger environment cap cannot silently increase its budget. Enforce
  one model-gateway writer per run with an OS file lock.
- Replay restores recorded state, not a resumable scheduler. Full event snapshots
  favor inspection in Phase 1; storage and viewer scaling need later load tests.

## Step 7 — Stop boundary and evidence
- Freeze the benchmark measurement before research interviews so simulation call
  counts and subsequent interview costs are distinguishable. Save both artifacts.
- Use a real local Chromium interaction check for the viewer in addition to HTTP
  tests. The browser requests only local resources.
- Keep the large SQLite/JSONL run artifacts out of Git; commit compact research
  reports, provenance and a viewer screenshot instead.
- Stop after Phase 1. The one-day real-API acceptance is not claimed: there are
  no configured models/credentials or approved spending cap. The user's explicit
  instruction to ask before adding a paid service governs any future paid run.
