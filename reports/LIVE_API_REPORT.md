# Live API validation — MiniMax M3.1 Flash

The original 25 residents completed one simulated day using the user's requested
`minimax/minimax-m3.1-flash:free` route through LiteLLM. All 908 runtime requests
succeeded and returned usage. **Cost was $0 total and $0 per resident per simulated
day, within `SIM_MAX_USD=0`.** No paid model or later phase was started.

This completes Phase 1's real-API full-day acceptance using the subsequently
authorized free route. It does not validate paid-model pricing, the 100-resident
population on live inference, or an improvement over the original paper.

## Run and cost

| Measurement | Result |
| --- | ---: |
| Residents with actual API calls | 25 / 25 |
| Completed simulated minutes per resident | 1,440 |
| Runtime API requests | 908 |
| Runtime cache hits | 0 |
| Provider input tokens | 1,924,730 |
| Provider output tokens | 163,254 |
| Failed/uncertain runtime requests | 0 |
| USD / run | $0 |
| USD / resident / simulated day | $0 |
| Wall time | 3,201.746 seconds, about 53.36 minutes |

The town ran from 2023-02-13 00:00 to 2023-02-14 00:00 UTC. All residents made
between 23 and 54 requests. The engine's known initial sleep period uses seeded
routines; invalid generated plans use the existing deterministic routine fallback.
No MockLLM response backend was used for live requests.

OpenRouter's public catalog listed zero prompt/completion prices for the exact
route. The adapter also requested zero provider maximum prices, disabled provider
fallbacks and disabled retries. Dollar accounting uses the published/configured
token rates; it is not a provider invoice. Debugging requests below are separate
from the 908-request daily runtime measurement.

| Live stage | Provider attempts | Result | USD |
| --- | ---: | --- | ---: |
| Initial persona smoke question | 1 | Valid JSON answer | $0 |
| Initial town attempt | 1 | Stopped at minute 360 | $0 |
| Low-reasoning smoke question | 1 | Valid JSON answer | $0 |
| Action-format diagnostic town | 39 | 38 responses; one interrupted request | $0 |
| Corrected full day | 908 | Completed; all requests succeeded | $0 |
| **All live stages** | **950** | **948 responses; two uncertain requests** | **$0** |

Usage for the two uncertain debugging requests is unknown, and their zero-dollar
reservations remain recorded. Their token counts are not presented as measured
usage. No failed request was retried internally.

## Configuration and credentials

- Completion model for deep, standard and GM inference:
  `openrouter/minimax/minimax-m3.1-flash:free`.
- Reasoning effort `low`, output limit 4,096 tokens, timeout 180 seconds, seed 42;
  temperatures retain the existing per-resident settings.
- Retrieval remains local lexical retrieval. `SIM_EMBED_MODEL=local/lexical`
  names the reserved local setting; no embedding API was called.
- The key entered through hidden terminal input and existed only in the live
  process environment as `OPENROUTER_API_KEY`. It was not saved in source,
  configuration, reports or application logs. The process removed it on exit.

The user authorized this exact free route. The legacy `--allow-paid` flag is the
application's live-call opt-in; it did not increase the zero-dollar cap or select
any paid route. Reproduction settings are retained without credentials in
[run-settings.json](live-api/run-settings.json). See the free-route example in
[README.md](../README.md).

## Verification

- **45 tests passed offline in 106.21 seconds**, with internet sockets disabled.
  Ruff and formatting checks pass for all 49 source/test files.
- Every resident's recorded activity totals exactly 1,440 minutes.
- All 908 call records use the exact requested model and match the event ledger.
- SQLite and JSONL contain the same 4,053 committed events. Import replay verifies
  the hash chain and produces a byte-identical event log and identical state.
- A complete second simulation used **908/908 response-cache hits** with a
  disabled provider backend and replay-only mode. It reproduced the world state
  exactly except for the configuration's replay flag. No credentials or provider
  requests were needed.
- Chromium verified the completed API-backed viewer: 25 residents, all five
  needs, a generated plan, 908 displayed requests and the $0 cap. There were no
  page errors or external browser requests.

Event-log SHA-256:
`7a915afb9cd7050c4dc26f0b414a2a839812e64bdcf1b69f141cb4e521da4598`.

## Problems found and behavior observed

The first town request failed after 50.294 seconds under the original 45-second
timeout. That run did not retain a specific HTTP status, so its exact remote
failure cause is unconfirmed. The catalog declares mandatory reasoning with a
`max` default. Added environment controls for supported `low` effort and a longer
timeout, including effort in response-cache identity.

The next attempt revealed an ambiguous action prompt: residents supplied their
current location as the target of meals and sleep, which the GM correctly rejected.
Clarified that only movement has a location target, supplied a concrete meal
example, and added readable date/time/day fields. Physical rules were preserved;
intentions were not silently rewritten. Both earlier attempts remain recorded.

During the completed day, validation created **9 routine-plan fallbacks, 1 pause
for an invalid intention and 2 rejected reflections**. These are distinct from
API failures. The GM rejected 30 actions: 12 closed destinations, 11 attempts to
attend without an applicable calendar event, 4 activities crossing closing time,
2 work attempts away from the workplace and 1 unsupported argument set.

A debug monitor also exposed a misuse of the writer constructor while a run was
active. Monitoring now uses read-only SQLite/the viewer. A consistent snapshot
confirmed the event mirror was intact; no repair was needed. The supported read
path is documented.

The residents sent **44 messages**. Retained Sam campaign awareness stayed at
1/25; party awareness grew from 1/25 to 3/25. Mutual-knowledge density grew from
0.2333 to 0.2467. **Manual message review found two complete invitations from
Isabella, to Maria and Carlos; both accepted.** The full-schedule detector's
reported zero is a parsing bug: it recognizes `5pm` and `17:00` but misses
`5:00 to 7:00 p.m.`. Retain the original machine output as evidence, rather
than interpreting it as zero actual invitations. Campaign diffusion was absent
and party reach was limited in this one-day configuration. The real Valentine's
attendance window starts at minute 2,460, outside this run; attendance at that
party was not observed. The paper's two-day results are not a matched comparison.

### Manual behavior review

- Isabella worked at Hobbs Cafe, exchanged seasonal drink ideas with Arthur,
  and invited Maria and Carlos to the next day's party. Carlos accepted the
  request to bring a poem. Drink production and a poetry performance were not
  recorded as separate outcomes.
- Carlos put the party in his own calendar at minutes 1,020–1,140: **February
  13, 17:00–19:00, a day early**. Maria and Isabella used the correct minutes
  2,460–2,580. Carlos travelled to the cafe and completed two `attend` actions
  that evening. The GM accepted his own calendar entry without a matching host
  event. This is a date/coordination validation defect, not evidence that the
  actual Valentine's party took place.
- Maria and Klaus arranged coffee and had overlapping cafe leisure time in
  the morning. Later actions kept returning to the same coffee goal. Ayesha
  and Wolfgang arranged a Shakespeare discussion, but their messages and
  waiting continued beyond the agreed time. Co-location and action descriptions
  alone do not establish a completed conversation.
- Francisco and Hailey tried to arrange a performance collaboration. They
  overlapped at the cafe before closing; Hailey later proposed the pub, while
  Francisco went home for dinner. No completed performance plan was recorded.
- Adam, Yuriko, Carmen, Arthur and Jane exchanged election questions. Jane
  declined to speculate without reliable candidate information. Sam did not
  send a campaign message, and nobody propagated his candidacy.

Repeated meals, repeated cafe/park trips and stale meeting goals also occurred.
These point to action-state and plan-reconciliation problems; they should not
be presented as demonstrated humanlike forgetfulness. Fixing the time parser
and shared-event/date validation remains future work. No additional inference
or simulation was run for this review.

Mean daily hours were 8.441 sleeping, 6.645 working/studying, 3.601 leisure,
0.707 travelling and 4.605 other activity. Needs, scheduling and the broad
"other" category remain uncalibrated. No human believability ratings, real-model
Twin/GSS fidelity evaluation or 100-resident API day were conducted. This run
demonstrates integration and replay, not human realism or superiority to Park
et al. Development remains stopped at Phase 2.

## Evidence

- [Acceptance and all-stage ledgers](live-api/acceptance.json),
  [simulation metrics](live-api/simulation.json),
  [offline checks](live-api/offline-checks.json).
- [Complete event/cache replay checks](live-api/full-replay-check.json),
  [single-response replay check](live-api/replay-check.json).
- [Catalog and published prices](live-api/model-catalog.json),
  [authentication status](live-api/authentication.json) and
  [credential-file scan](live-api/credential-scan.json).
- [Initial failed attempt](live-api/initial-simulation.json),
  [action-format diagnostic attempt](live-api/schema-simulation.json),
  [initial smoke response](live-api/probe.json),
  [low-effort smoke response](live-api/low-reasoning-probe.json).
- [Browser checks](live-api/browser-check.json) and
  [viewer screenshot](live-api/viewer.png).

Complete local run/cache files remain under ignored `runs/live-day-corrected/`.
Use `python -m smallville serve --run runs/live-day-corrected` to inspect the day.
