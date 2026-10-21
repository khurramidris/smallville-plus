# Phase 3 — Economy, council and three-day experiments

**Phase 3 has resumed with a performance and planning pass. The optimized
25- and 100-person three-day offline scenarios and all 83 tests pass. A fresh
three-day API experiment is in progress; both expanded and original-cohort
optimized event replays pass.** The previous live
experiment remains preserved as interrupted at 21 hours. No Phase 4 work was
started and no paid service was added.

## Resumption — performance and planning

`--optimized` enables bounded same-time decisions (four for this experiment),
atomic in-flight budget reservations, duplicate-request caching, bounded phone
context, explicit known movement/work constraints and recent rejection feedback.
Only a person's chosen work/sleep/leisure can continue without another model
decision, for at most two hours with hourly checks. New information, needs,
appointments and GM rules interrupt it. Social decisions still use the model.

Decisions read a fixed scene and apply in scheduler order. Per-call provider and
queue timings are separate from deterministic events. All tasks settle before a
cancelled run finishes. Production behavior is frozen at `8e2b410`.

- **83 tests pass offline in 142.49 seconds**, including overlap, in-flight caps,
  cancellation, privacy/ordered capacity checks and cached/event replay.
- Optimized 25-person fixture: **2,870 requests**, versus 3,317 previously
  (13.5% fewer); **332.999 wall seconds**, versus 389.783. Competing work differed,
  so this is not an isolated timing benchmark. Both runs cover three days.
- All **14,679** optimized events replay to byte-identical JSONL and identical
  state. All money, food, ledger, work-limit and elapsed-activity audits pass.
- A fixed-100ms synthetic provider probe measured **4.07x** gateway throughput
  with four concurrent requests. This is not an API or full-engine speed claim.
- Optimized 100-person fixture: **12,141 requests**, versus 14,076 previously
  (13.7% fewer). Synthetic input tokens fell from 88,642,393 to 51,851,835
  (41.5% fewer); wall time was 1,686.868 seconds, versus 2,260.967 under different
  competing work. All financial/resource audits pass. Eleven residents owe
  23,081 town cents; eleven are hungry without meals. Party: 29/49 guests.
- These modes change attention/history limits and action timing, so their
  behavior is not guaranteed identical. Social fixture results remain scripted.
- All **59,359** optimized expanded events reproduce identical state and JSONL
  bytes; every resident accounts for every minute. No inference during replay.
- Fresh live inference results are pending. They use
  separate directories/reports; none overwrite the prior experiments below.

Evidence: [optimized fixture](phase3/optimized-mock-25-simulation.json),
[replay](phase3/optimized-mock-25-verification.json),
[expanded fixture](phase3/optimized-mock-100-simulation.json),
[expanded replay](phase3/optimized-mock-100-verification.json),
[offline checks](phase3/optimized-offline-checks.json),
[synthetic concurrency probe](phase3/concurrency-probe.json).

## Built

- Integer-cent account transfers and a ledger, paid work with shift/daily limits,
  fractional-cent carry, finite employer funds and unpaid-wage obligations.
- Shared household rent, arrears, funded pension/support allowances, three
  priced food shops, portable meals and finite funded wholesale replenishment.
- Private bank transfers/statements, public notices, evidence-backed local news,
  secret council ballots, quorum/deadlines and a funded food-stock policy.
- Shared event invitations and host/date/venue checks for confirmed attendance.
  The earlier written-time invitation parser defect is corrected.
- Private, dated stock observations, new action prompts/MockLLM fixtures,
  economic audits, historical viewer panels and command/report integration.

Economic rates, capital, support and freelance demand are authored assumptions.
The scenario explicitly delays the second day's regular food delivery. Town
cents and real API USD are separate accounting systems.

## Completed offline scenarios

| Measurement | Original 25 | Expanded 100 |
| --- | ---: | ---: |
| Simulated days | 3 | 3 |
| Minutes per resident | 4,320 | 4,320 |
| Mock requests | 3,317 | 14,076 |
| USD / resident / day | $0 | $0 |
| Wall seconds | 389.783 | 2,260.967 |
| Recorded events | 14,528 | 59,768 |
| Rent arrears, town cents | 0 | 27,081 across 11 residents |
| Hungry residents without meals at end | 0 | 14 |
| Failed purchase attempts/completions | 71 | 191 |
| Confirmed party guests / receiving details | 12 / 20 | 31 / 46 |

These are deterministic scripted fixtures, including their social decisions and
synthetic token counts. Wall times include competing validation work. They
demonstrate implementation behavior, not human realism or emergent politics.

Both scenarios conserve all money and meal units, respect work limits, keep
accounts nonnegative and reconcile every account with its transfer ledger.
In the 100-resident run, 19,873,747 cents remain conserved and 974 initial meals
equal 461 consumed plus 513 remaining. Fourteen residents are hungry without
food despite remaining town supply; the fixture exposes access/affordability
pressure rather than automatically solving it.

The council fixture passed its proposal in both towns. The 25-person vote was
15 yes, 5 no, 5 abstentions; the 100-person vote was 67 yes, 22 no, 11 abstentions.
Each policy spent 30,000 town cents on 100 actual remaining wholesale meals.
The policy adds stock while retail prices remain unchanged.

![Recorded retail food stock](phase3/food-stock.png)

Retail stocks emptied before the second-day delivery delay. The regular
third-day replenishment and council purchase added actual stock. The expanded
fixture exhausted its retail supply again. [Vector figure](phase3/food-stock.svg)
and [transaction-derived data](phase3/food-stock.csv) are available for inspection.

Party counts are distinct guests over February 14, 17:00–19:00, with host/time
confirmation. They are not simultaneous occupancy. Receiving full shared-event
details is the invitation metric. A host-owned event is seeded from the original
party goal; this setup, three-day horizon and communication channel differ from
Park et al.'s two-day experiment.

## Verification

- **76 tests pass offline**, 173.06 seconds, with internet sockets disabled.
  Ruff and formatting pass for 59 Python files.
- The additional Phase 3 cache regression uses **443/443 cache hits**, zero
  provider calls and identical world state except the replay configuration flag.
- Both complete event imports reproduce every table and JSONL bytes exactly,
  without inference. All agents account for every simulated minute.
- Chromium checked the historical finance/contract/council interfaces with no
  page errors or external requests. [Viewer screenshot](phase3/viewer.png).

Offline scenarios began at `4525c58`. Later changes correct news read cursors,
CLI validation and derived initial-awareness counting; reports were recomputed
from unchanged event histories. Final production behavior is frozen at
`87778b4` for the API experiment.

## Original live API experiment — interrupted by user

The original 25 residents were scheduled for three days on the authorized
`openrouter/minimax/minimax-m3.1-flash:free` route through LiteLLM. Published
prompt/output rates were zero; the gateway cap and provider price ceiling remain
zero, with no retries or paid fallbacks. Keys enter only the process environment
through hidden input. [Settings](phase3/live-settings.json) contain no key.

The user requested a stop at **minute 1,260 / February 13, 21:00**, before the
requested 4,320-minute horizon. Graceful cancellation recorded `interrupted`,
preserved all committed outcomes and finalized cost accounting. There were
**947 attempts: 946 successful responses and one interrupted request with unknown
usage**, 3,261,849 known input tokens and 252,265 known output tokens. Recorded
published-rate cost is **$0**, or **$0 per resident per simulated day elapsed**;
this is not a completed three-day API measurement. Wall time was 5,041.746 seconds.

Residents completed paid work, shopping and the first rent collection. Wages
totaled 253,480 town cents, purchases 19,200 and rent 46,800. All town money and
food reconcile, accounts remain nonnegative and work limits pass. Eighteen
residents cast ballots, 25 messages were sent and four guests read full party
invitations. The council deadline and Valentine's party were still in the future;
neither a final vote result nor live party attendance was observed. Maria and
Klaus exchanged study-meeting messages; Maria's completed actions place her at
Hobbs Cafe after her later arrival message. A substantive study conversation is
not established by those records.

The GM rejected 38 closed-destination attempts, six out-of-shift work periods,
two daily-work-limit violations, five activities crossing closing time and five
attendance attempts without a matching event. One phone request was invalid.
These are remaining planning/coordination problems, not successful outcomes.

Two early API diagnostics were interrupted while correcting offline-discovered
stock and contract issues: **83 attempts, 81 known responses and two uncertain
interrupted requests, $0**. These remain separate from the final runtime. Unknown
usage for interrupted requests is not reported as measured tokens.

Including diagnostics, Phase 3 used **1,030 attempts, 1,027 known responses and
three uncertain interrupted requests, $0**. Unknown usage is excluded from known
token totals. [Final interrupted report](phase3/live-simulation.json) and
[last progress record](phase3/live-progress.json) are preserved. Full replay of
this partial live run was not performed. Published-rate accounting is not a
provider invoice; partial-day time-use figures are normalized diagnostics.

## Problems found and limits

Fixed lost shop-stock observations, teacher/student and unpaid-work
classification errors, part-time limits, same-minute news loss, duplicate initial
awareness counting, shared-event date validation and incomplete interruption
status. Early diagnostics and their costs remain retained.

Remaining limits include fixed prices and primary contracts, one meal commodity,
automatic prorated rent, simple emotional/relationship heuristics, scarce-venue
retry behavior and a fixed council proposal. There is no labor market, eviction,
credit, full inventory trading or calibrated macroeconomy. Full state snapshots
are expensive: the expanded three-day JSONL is about 954 MiB.

No blinded human ratings, matched paper replication, live 100-resident cohort,
paid-price validation or 1,000-agent load test was performed. These results do not
establish that Smallville+ exceeds the original paper's realism.

That experiment's three-day objective was unfinished at the user's stop. A fresh
experiment is now authorized by the user's resumption; its results are pending.

Evidence: [offline checks](phase3/offline-checks.json),
[25-person report](phase3/mock-25-simulation.json),
[100-person report](phase3/mock-100-simulation.json),
[25-person replay](phase3/mock-25-verification.json),
[100-person replay](phase3/mock-100-verification.json).
