# Phase 3 — Economy, town government and three-day validation

The user authorized the next phase and a three-day simulation on 2026-10-21.
Preserve the original `SPEC.md`; implement Phase 3 only.

## Scope

- Integer-cent accounts and an auditable transfer ledger; no implicit money
  creation or overdrafts. Jobs pay only for completed eligible work minutes.
- Household rent, arrears, finite shop inventory, priced portable meals and
  funded replenishment. Resource shortages and failed transactions are outcomes.
- Owner-scoped bank app, a public notice board/local news and one-person-one-vote
  council decisions with quorum, closing time and a funded policy effect.
- Sparse scheduled economic/civic events; all effects enter the immutable event
  log and replay through SQLite projections.
- Shared event invitations and calendar validation, plus the invitation time
  parser correction discovered in the last live-day review.
- Prompts, MockLLM, metrics and viewer support for the new systems. Offline tests
  cover conservation, authority, time, privacy, scarcity, voting and replay.

Economic rates and initial funds are explicit fictional town assumptions, not
estimates inferred from a resident's real survey responses. Monthly housing costs
are represented by daily prorated charges so a three-day experiment observes
their effects. Public stock and prices are visible at the shop or in published
reports; private balances, ballots and notebooks remain owner-scoped.

## Validation and run

- Preserve Phase 1/2 modes and all offline checks. Verify the expanded population
  on MockLLM and run a three-day Phase 3 scenario.
- Continue using only the already authorized
  `openrouter/minimax/minimax-m3.1-flash:free` route for live inference, if used,
  with `SIM_MAX_USD=0`, no paid fallbacks/retries and env-only credentials.
- Default live population is the original 25, matching the previous API run;
  the optional population question received no reply. No new paid service is authorized.
- Record completed days, costs per resident/day, economic conservation, food
  pressure, rent, wages, votes, news and party coordination. Preserve failed or
  partial runs honestly; a blocked API will not be bypassed.
- Stop after Phase 3 and the requested run. Graphiti, 30-day drift, 1,000-agent
  scaling and social media remain deferred.

## Authorized resumption

The user resumed Phase 3 after the interrupted 21-hour live run. Add bounded
same-time inference concurrency, safe reuse of chosen routine blocks, bounded
context, explicit known planning constraints and per-call latency measurements.
Keep provider waiting outside the budget lock, reserve in-flight costs before
dispatch and settle all tasks on cancellation. Decision completion order cannot
publish tentative outcomes or change the GM's ordered resource reservations.
Use fresh run directories and preserve earlier experiments. Finish the three-day
live experiment if the authorized endpoint permits it; do not bypass any block.
No Phase 4/5/6 work is authorized by the ambiguous "number thing" without clarification.
