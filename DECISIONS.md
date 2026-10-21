# Decisions

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
