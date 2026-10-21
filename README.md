# Smallville+

Phase 1 of a research town simulation, with the original 25 residents and
Smallville tile map. Python 3.11+, asyncio, Pydantic, SQLite WAL and LiteLLM.
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

The embedding model variable is reserved and validated for live configuration;
Phase 1 retrieval uses local lexical relevance. Full life histories, digital
history generation, GSS/Twin-2K-500 validation, wages/rent/shops, councils, graph
memory, 1,000-agent batching and social media remain deferred. Initial food and
account balances exercise resource guards, but no financial economy is simulated.

`SPEC.md` is the complete original request. `PROGRESS.md` records completion and
open issues, and `DECISIONS.md` records the rationale. Only Phase 1 is implemented.
The saved [Phase 1 report](reports/PHASE1_REPORT.md) contains acceptance evidence,
mock benchmark measurements, browser verification and the remaining API blocker.
