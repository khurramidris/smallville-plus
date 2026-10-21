# Phase 2 implementation scope

User authorization: “Continue development of next phase.” (2026-10-21).
This advances the phase boundary in `SPEC.md` to Phase 2. The original
specification remains unchanged. Paid-service approval is still required.

## Deliverables

- A versioned persona pipeline producing the original 25 residents plus 75
  residents seeded from the public genagents GSS demographic bank.
- Structured life histories and locked seed facts, with original identities,
  ages, goals and locations preserved. Generated biography is fictional and
  separately attributed from source demographics.
- Three weeks of pre-populated, internally coherent messages, contacts and
  calendar history. Past records use minutes before the simulation epoch and
  must not leak future events or other residents' private state.
- A t=0 categorical/numerical survey against persona facts. Contradictory or
  malformed answers trigger bounded regeneration and a fresh survey; unresolved
  residents prevent the population from entering a simulation.
- Typed survey methods and a Twin-2K-500/GSS fidelity harness with explicit
  profile/held-out separation, coverage, categorical accuracy and numerical error.
  Mock scores are engineering diagnostics, not evidence of human fidelity.
- CLI support for building, validating, running and inspecting a 100-resident
  population; preserve the existing 25-resident Phase 1 workflow and replay.

## Validation

- All existing and new tests pass with internet sockets disabled.
- Build and validate a deterministic 100-resident population with at least
  21 days of phone history on MockLLM, including a tested contradiction-repair path.
- Run 100 residents for a simulated day on MockLLM and inspect the viewer.
- Exercise the fidelity harness on licensed real survey items/response subsets
  when downloadable, retaining source hashes and declaring every exclusion.
- Record costs and source limitations, update progress/decisions after each
  implementation step, use small commits, then stop at Phase 2.

## Out of scope

Jobs/wages/rent/shops, council/news/resource pressure, graph memory, 30-day drift,
1,000-agent inference/batching and social media remain in Phases 3–6.
The unperformed Phase 1 paid-API acceptance remains explicitly pending; a request
to develop Phase 2 does not authorize paid inference.
