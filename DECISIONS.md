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
