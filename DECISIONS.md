# Decisions

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
