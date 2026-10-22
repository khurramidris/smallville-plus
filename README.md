# Smallville+

Research town simulation with the original 25 residents and Smallville map,
plus a Phase 2 pipeline for 100 residents, digital histories and survey evaluation,
and a Phase 3 economy, town council and local news.
Python 3.11+, asyncio, Pydantic, SQLite WAL and LiteLLM.
This is working research infrastructure, **not evidence that realism exceeds
Park et al.** MockLLM is a deterministic, partly scenario-specific test fixture.

```bash
python -m pip install -e '.[test]'
python -m pytest
python -m smallville benchmark valentine --out runs/valentine --days 2
python -m smallville serve --run runs/valentine
```

Open http://127.0.0.1:8000. Move the time slider, play the history, and click a
resident to inspect their memories, needs, emotions, plans, calendar and messages.
The dashboard reports requests, cached responses and cost at the selected time.
The viewer is read-only and intended for local researcher use.

Tests disable internet sockets by default; Unix sockets remain available solely
for asyncio's local wakeup mechanism. Dependencies must first be installed.
Neither tests nor MockLLM require keys, model downloads, telemetry or network calls.

```bash
python -m smallville replay --source runs/valentine/events.jsonl --out runs/replayed
python -m smallville evaluate --run runs/replayed
python -m smallville interview --run runs/valentine --agent all
```

Each run produces `world.sqlite3`, `events.jsonl`, `calls.sqlite3`,
`cache.sqlite3`, `report.json` and `report.md`. Interviews additionally produce
`interviews.json`. Use a fresh output directory for every simulation.
Replay restores exact recorded state and events without inference; it does not
resume an interrupted scheduler. The same mock seed yields deterministic histories.
Use `--cache PATH` to share responses between runs and `--replay-only` to refuse
inference on a cache miss. Request hashes include prompt, sampling and output limit.

The event log is hash chained and append-only in SQLite. State changes and their
events commit together; JSONL is mirrored after commit. Reopening recovers missing
or torn JSONL tails from SQLite and rejects a conflicting complete prefix.
There is one authoritative writer per run. Full agent snapshots favor transparent
replay over storage efficiency in Phase 1; this is not yet a 1,000-agent load test.
Inspect an active run through the read-only viewer or a read-only SQLite
connection. `WorldState` opens a writer and performs JSONL recovery; do not use
another instance as a live monitoring reader.
Reopening a run preserves its original spending cap; a larger environment value
cannot silently increase that run's allowance. Tested direct dependency versions
are recorded in `requirements-tested.txt`.

The map provider turns the retained Tiled geometry/collision matrices into named
locations with paths, synthetic addresses, opening hours and capacities. The
viewer uses a schematic, not unbundled external artwork. A replacement provider
implements `locations`, `route()`, `travel_minutes()` and `view()`; a new city's
persona seeds must map to its locations. See `THIRD_PARTY.md` for provenance.

Only due residents act. The rules-first GM owns outcomes, checks physical
constraints and delays effects until actions complete. Messages and calendar
entries are typed private app records; a message affects the recipient's memory
only after they read it. Needs decay with elapsed simulated time, even while
traveling or sleeping. All five needs, emotions and relationship closeness have
explicit, uncalibrated update rules. Minds use finite episodic memory, evidence-
linked reflections, daily plans, hourly decomposition and replanning on surprises.
Deep and standard tiers retrieve different memory limits and may use different
models. Stable persona/rule content precedes dynamic context in prompts.

The benchmark report compares retained awareness, mutual-knowledge density and
time-bounded party attendance with [Park et al. §7.1](https://arxiv.org/html/2304.03442v2#S7.SS1).
It also reports behavior variance and a rough time-use shape comparison with
[BLS ATUS 2024](https://www.bls.gov/news.release/archives/atus_06262025.htm).
Starting seed relationships, communication channel, activity taxonomy and
population composition differ; the figures are descriptive, not matched replication.
Interviews cover self-knowledge, memory, planning, reactions and reflection.
Human ratings remain null until collected; synthetic opinion variance is not
survey fidelity.

Paid validation is opt-in. Run `python -m smallville preflight` to inspect
configuration **without making calls or printing secrets**. Set the four model
variables, `SIM_MAX_USD`, verified conservative per-token `SIM_MODEL_PRICES`,
and the provider's API key in the environment. `.env.example` describes the
format; the application does not automatically load `.env` files.

After spending has been approved:

```bash
python -m smallville run --backend litellm --allow-paid --days 1 --out runs/live-day
```

Every paid call goes through LiteLLM, with no retries. Before dispatch the gateway
reserves the UTF-8 prompt-token upper bound plus the output limit at configured
prices. It blocks a request if the reservation would exceed the remaining cap.
Errors/timeouts retain their full reservation and stop the run because they may
already have been billed. No remote exception text or API keys enter the audit log.
The cap assumes rates cover all billed tokens and the provider respects requested
limits; only text completions are supported. Ledger USD uses conservative configured
rates, not an invoice. A budget stop is reported as **incomplete**, never as a
successful one-day acceptance run. No paid API day has yet been validated.
The requested MiniMax free-route day **has** completed: 25 residents, 908 real
requests, $0 within a $0 cap, and a complete cached rerun with no provider calls.
See the [live API report](reports/LIVE_API_REPORT.md) for measured usage,
validation failures and remaining research limits.

Explicit OpenRouter `:free` models can run with a hard **$0** cap after API use
is authorized. Verify the exact route's published rates first, then configure:

```bash
export SIM_MODEL_DEEP=openrouter/minimax/minimax-m3.1-flash:free
export SIM_MODEL_FAST="$SIM_MODEL_DEEP"
export SIM_MODEL_GM="$SIM_MODEL_DEEP"
export SIM_EMBED_MODEL=local/lexical
export SIM_MAX_USD=0
export SIM_TIMEOUT_SECONDS=180
export SIM_REASONING_EFFORT=low
export SIM_MODEL_PRICES='{"openrouter/minimax/minimax-m3.1-flash:free":{"input":"0","output":"0"}}'
python -m smallville preflight
python -m smallville run --backend litellm --allow-paid --days 1 --out runs/free-live-day
```

Inject `OPENROUTER_API_KEY` into the process environment through your secret
manager or hidden terminal input; do not put a key in source or a command line.
The existing `--allow-paid` flag opts into live calls; the zero cap and explicit
free route keep this example at $0. The adapter also disallows provider fallbacks
and requires zero provider prompt/completion prices. Authentication, quotas,
timeouts or route availability can still stop a free run. A partial run does not
meet full-day acceptance. No other model is selected automatically.

The embedding model variable is reserved and validated for live configuration;
retrieval uses local lexical relevance. Graph memory, 1,000-agent batching and
social media remain deferred.

## Phase 3: economy and town government

Use `--optimized` for up to four independent decisions at the same simulated
minute, bounded continuation of a person's chosen routine and shorter phone
history/address context. Outcomes still commit in scheduler order through the GM.

```bash
python -m smallville run --phase 3 --optimized --days 3 --supply-delay-day 1 --out runs/phase3-fast
```

The equivalent environment settings are `SIM_DECISION_CONCURRENCY=4`,
`SIM_ROUTINE_ACTIONS=1` and `SIM_COMPACT_CONTEXT=1`. The default remains the earlier
single-decision mode. Concurrency is limited to 1–16; it does not bypass budgets
or provider limits. Routines stop for new messages, needs, appointments or changed
rules, expire after two simulated hours and check in at least hourly. They reuse
chosen work/sleep/leisure; social decisions remain model decisions.

Per-provider timings are stored separately in `calls.sqlite3.call_timings` and
reported under `inference_timing`. They include network/generation and may overlap
under concurrency. Timing is excluded from deterministic events and cache keys.
Cache-hit token counters remain zero; previous measured usage is retained in the
original call ledger. This is an optimization mode, not a realism score.

```bash
python -m smallville run --phase 3 --days 3 --out runs/phase3
# Use an existing validated Phase 2 population for all 100 residents:
python -m smallville run --phase 3 --days 3 \
  --population runs/population/population.json --out runs/phase3-100
# Optional authored supply-pressure scenario (day 0 is February 13):
python -m smallville run --phase 3 --days 3 --supply-delay-day 1 --out runs/phase3-delay
python -m smallville serve --run runs/phase3
```

Add `--backend litellm --allow-paid` with the authorized model/environment settings
above to use real inference. The same budget and credential rules apply.
Omitting `--phase 3` preserves the earlier phase workflows.

Phase 3 uses integer cents and explicit account transfers. Paid work accrues only
for completed minutes within a personal contract's shift and daily limit;
fractional cents carry forward. Study and household activity may be unpaid.
Pensions/support, freelance demand, initial cash and employer capital are authored
scenario assumptions, not inferred real survey finances. Employer or town funds
can run out; unpaid earnings and rent remain obligations rather than overdrafts.
Each household owes $36/day of prorated rent, split among its residents and
charged at 21:00. There is no eviction or debt-interest model in this phase.

Meals cost $6 at the market, $8 at the cafe or $10 at the pub. A resident must
travel to an open shop and spend ten minutes purchasing finite stock. Meals are
portable and eating consumes one. Shops replenish at 06:00, paying $3/meal to a
finite wholesaler. `--supply-delay-day 1` explicitly delays the second day's
delivery; it does not destroy goods or manufacture a shortage outcome.
Residents retain dated stock observations from their own visits and from supply
bulletins they read. These are last-known values, not live remote inventory.
An older bulletin cannot overwrite a more recent visit.

Residents can read/post on the town notice board and vote once in a secret
council poll from February 13 08:00 until February 15 12:00. The food-stock
proposal requires half the adult electorate for quorum and more yes than no
votes. If passed, it spends up to $300 of available treasury funds on additional
wholesale meals; actual spending is limited by available stock. Institutional
news cites recorded public events. Resident posts are labelled opinions and
cannot change funds, votes or physical outcomes by assertion.

The host's Valentine event has a shared identity. Read invitations expose its
actual date/venue to their recipients; private calendar entries cannot create a
party. Confirmed attendance requires a linked event, correct time and host
presence. Complete written AM/PM invitation ranges are recognized by the scorer.

The viewer adds historical balances, transactions, contracts, rent, shop stock,
council results and public notices. Researcher inspection remains separate from
agent perception: personal bank statements and ballots never enter other minds.
The report audits every account against initial balances and transfers, verifies
money/meal conservation and reports arrears, scarcity and policy execution.
Town money is fictional and always separate from real API USD.
Cancelling a run records its elapsed time and `interrupted` status; an in-flight
model request retains its uncertain reservation. Replay does not resume it.

These systems are deliberately small and uncalibrated: no product variety,
labor market, market-clearing prices, credit, Graphiti or social-media platform.
Phase 4 remains deferred.

Phase 2 adds an explicit preparation step. It uses 75 licensed public GSS
demographic seeds alongside the original 25. New biographies and messages are
fictional. The public bank is distinct from Stanford's restricted interview agents.
Duplicate full names remain distinct people with separate IDs and addresses.

```bash
python -m smallville populate --out runs/population100 --residents 100 --history-days 21
python -m smallville validate-population --population runs/population100/population.json
python -m smallville run --population runs/population100/population.json --out runs/town100 --days 1
python -m smallville serve --run runs/town100
python -m smallville fidelity --dataset all --out runs/fidelity
```

Preparation creates a versioned population artifact with source facts, six dated
life events, interests, values, goals, 21 prior calendar days of reciprocal phone
messages, contacts and past appointments. New homes are authored apartment-unit
overlays at accessible entrances; source geometry is retained. Historical records
use negative epoch minutes. Runtime app scheduling still starts at minute zero.
Opening hours, capacity, calendar ownership and travel gaps are validated.

Every resident answers a t=0 categorical/numerical survey about locked identity
and demographic facts. A contradiction regenerates the biography and triggers a
fresh survey, up to `--max-attempts` (default 3). A failed population is not
published. Its preparation report and call ledger still record spent/reserved
costs. Each repair attempt has its own request revision to prevent accidentally
reusing a cached failed answer. Use `--cache PATH --replay-only` to reproduce an
entire preparation sequence without new inference.

The fidelity harness uses separate masked profiles. The bundled Twin sample has
20 of 2,058 participants and 122 supported held-out items from the official wave 4
catalog. It excludes all wave-4 QuestionIDs from the 32-field wave 1–3 profiles.
Prior responses to held-out items are scorer-only human test–retest baselines.
The GSS harness holds out age, political views, party identification and religion
from 75 public demographic-bank profiles. The model receives questions and valid
scales; answer keys and prior target responses stay in the scorer.
Coverage and source missingness are explicit; invalid/missing predictions count
as errors. Numerical reports include valid-only MAE and penalized normalized MAE.
Mock scores exercise the adapters and scorer and do not measure human fidelity.
The bounded sample and supported encodings do not reproduce the complete paper
protocol, and model-training contamination is unassessed.

To normalize a larger locally supplied official Twin catalog/CSV set offline:

```bash
python -m smallville import-twin --catalog PATH_TO_CATALOG --train PATH_TO_WAVE1_3_CSV --test PATH_TO_WAVE4_CSV --revision SOURCE_COMMIT --subjects 100 --out runs/twin100.json
python -m smallville fidelity --dataset twin --twin-data runs/twin100.json --out runs/fidelity100
```

Preparation, simulation and fidelity commands each maintain their own cost ledger
and cap. All default to MockLLM. Paid use still requires explicit spending
approval, environment configuration and `--allow-paid`; no paid Phase 2 run has
been validated. Human gold data is kept outside persona repair feedback.

`SPEC.md` is the complete original request. `PROGRESS.md` records completion and
open issues, and `DECISIONS.md` records the rationale. `PHASE2.md` records the
authorized extension; `PHASE3.md` records the subsequent scope. Development stops
at Phase 3. The [Phase 3 report](reports/PHASE3_REPORT.md) contains the completed
three-day real-model experiment, optimized offline runs and remaining limits.
The [Phase 2 report](reports/PHASE2_REPORT.md) contains the 100-resident run,
consistency/cache checks, fidelity measurements and known limitations.
The saved [Phase 1 report](reports/PHASE1_REPORT.md) contains acceptance evidence,
mock benchmark measurements, browser verification and the remaining API blocker.
That historical API blocker is now resolved for the requested free route in the
[live API follow-up](reports/LIVE_API_REPORT.md); the original report is preserved.
