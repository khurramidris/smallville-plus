# Connected realism implementation: batch 2

**Evidence label: fixture only.** Every MockLLM-derived behavioral, cost, token,
runtime and storage number in this report is fixture only. Tests demonstrate
engineering correctness; no paid-model milestone is completed by these results.
Historical implementation status below predates the [M0–M4 rules](../MILESTONES.md).

Date: 2026-10-22

Scope: complete the R1 engineering gate

Inference: deterministic MockLLM only; no network or provider API

## Connected histories and commitments

Population artifacts now default to version 3. Version 2 remains readable for
legacy baseline runs, while `connected_v1` requires version 3. Each resident's
history cycles among available household, workplace and friendship peers rather
than using one generic ring relationship for every day. Messages remain private,
reciprocal and chronologically ordered.

The last pre-epoch thread contains a bounded request about one of the requester's
interests and an explicit acceptance from the other resident. Only that acceptance
creates the accepter's private promise memory. Population validation checks the
future deadline, acceptance message, sender identity, reciprocal contacts and
history coverage. These are fictional additions, not source or interview facts.

At launch, accepted promises become owner-scoped commitment goals with deadline,
priority, progress and evidence. A resident may spend five simulated minutes to
revise, block, reactivate, complete or abandon a goal. The GM checks ownership,
terminal status, prerequisites, deadline and evidence. Completion requires one of
the resident's own memories. `goal_history` records each transition separately
from the current goal projection.

## Memory and planning

When the 128-entry working stream evicts an episode, the same event transaction
writes it to an owner-indexed archive. `local_lexical_v1` ranks working and archive
candidates for the current task, goal, place, people, needs and appointments, then
returns only the tier's existing bounded limit. Prompt context labels whether a
result came from working memory or archive. Other residents cannot query it.

In the connected profile, a surprise no longer requests a replacement for the
whole day. A `repair_plan` response begins at the current minute and covers only
the remaining day. Validation preserves elapsed blocks, known locations, privacy,
opening hours, walking time and feasible appointments. A conflicting later
appointment is exposed as deferred. Invalid patches receive a deterministic
future-only repair and an explicit fallback diagnostic.

The decision context also lists actions feasible from the resident's known money,
inventory, location, work hours, contacts, calendar and public app state. It does
not reveal remote stock, destination capacity or concurrent actions; the GM still
owns those outcomes.

## Verification

- Ruff, formatting and whitespace checks pass.
- All **122 tests pass offline** with network sockets disabled.
- A 500-event flood preserves source identity and an earlier unfinished promise.
- A separately evicted low-priority episode is retrieved from the private archive
  under the same bounded limit and is unavailable to another resident.
- Goal tests cover evidenced completion through the GM, explicit abandonment,
  transition history and cross-owner rejection.
- Plan tests preserve the first 1,000 elapsed minutes, replace a block at a known
  closed market, reserve walking time for an appointment and defer an overlapping
  appointment. Every resulting location is known to the resident.
- Baseline Phase 1–3, population, economy, viewer and exact-replay tests continue
  to pass. Version 2 population data remains accepted outside `connected_v1`.

## Measured connected-profile run

The fresh artifact contains 25 residents, 21 history days, 1,050 messages,
75 calendar entries and 25 accepted unfinished commitments. Its digest is:

`227c856e91acb3160d61e50b582646b8ec9a40e237bf87cff0bb178a6bc7ccc1`

The optimized Phase 3 run completed all 1,440 requested minutes in 45.466 seconds.
It made 748 MockLLM calls: 594 actions, 25 full plans, 104 future-plan repairs and
25 reflections. The engine reused a plan for 675 activations. Full-plan fallback
and repair fallback rates were both 0%. There were no uncertain calls and cost was
$0. Synthetic fixture usage was 3,670,953 input and 33,133 output tokens; these
figures do not estimate provider billing.

The run contains 100 active goals: 75 generated life-history goals and 25 accepted
commitments. MockLLM did not choose a goal-transition action during this one-day
trace; transition behavior is covered by the GM scenario test. No resident reached
the 128-entry limit during the day, so the archive stayed empty; the explicit
500-event pressure test covers archive creation, privacy and retrieval.

The run generated 3,993 events and a 42,995,236-byte JSONL file. Replay produced
identical event bytes with SHA-256:

`408d147c2a0af53b6612dcbb1882d1ca1751e3768d83e2cf7048c66567286150`

Agent, goal, goal-history, archive, knowledge, message, calendar and metadata
projections all match. The full-snapshot log remains a material scaling problem.

## Research boundary and next work

This completes the R1 engineering gate, not the realism claim. MockLLM is scripted,
the histories are fictional, and the run is neither matched to Park et al. nor
human-rated. Sam's retained-awareness count is fixture only and is excluded from
comparisons with the paper; the mock explicitly scripts campaign messages.

R2 remains next: consent-based multi-turn conversations, independently chosen
responses, interruption, bounded phone attention, private listener routing and
asymmetric trust/affinity/obligation updates. Controlled real-model comparisons
and human believability ratings should follow those mechanics.
