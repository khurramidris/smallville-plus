# External audit guide

Smallville+ is public so researchers, engineers, and automated reviewers can
inspect the implementation, reproduce deterministic runs, challenge the
measurements, and propose corrections. The stable R2 audit snapshot is tagged
`audit-r2-2026-10-23` at
[github.com/khurramidris/smallville-plus](https://github.com/khurramidris/smallville-plus).
The tag's GitHub release carries the independently checksummed source archive,
full-history Git bundle, and artifact manifest.

The repository contains the complete tracked source, tests, Smallville map and
persona inputs, Phase 2 public research inputs, provenance records, compact
results, and viewer captures. It does not contain credentials or local runtime
databases. `runs/` is generated output and is intentionally ignored.

## Claim boundary

This is functioning research infrastructure through Phase 3 plus the R0-R2
connected-realism engineering gates. It has more explicit mechanisms than the
original Smallville implementation in several areas, including partial
observability, authoritative outcomes, needs, phone attention, directed social
state, money, food, work, rent, council voting, and listener-scoped
conversations. That does **not** establish greater human realism. There are no
matched human believability ratings, multi-seed confidence intervals, or
controlled real-model comparison against Park et al.

Start with these review surfaces:

| Question | Evidence |
| --- | --- |
| What was implemented and what remains? | `README.md`, `PROGRESS.md`, `REALISM_PLAN.md` |
| Are realism claims supported? | `reports/REALISM_AUDIT.md`, `reports/REALISM_IMPLEMENTATION_3.md` |
| Can state be replayed exactly? | `smallville/engine/`, `tests/test_world_engine.py`, `tests/test_integration.py`, `reports/r2/replay-check.json` |
| Are outcomes authoritative and observations scoped? | `smallville/gm/`, `smallville/apps/conversations.py`, relevant tests |
| Are cost limits enforced? | `smallville/llm/`, `tests/test_llm.py`, `reports/LIVE_API_REPORT.md` |
| Where did retained research material come from? | `THIRD_PARTY.md`, `references/sources.json`, `references/phase2/sources.json` |
| What did the accepted R2 run do? | `reports/r2/acceptance.json`, `reports/r2/viewer.png` |

## Reproduce offline

Use Python 3.11 or newer. Dependency installation can contact the package index;
the test and MockLLM commands themselves deny internet sockets and need no key.

```bash
git clone https://github.com/khurramidris/smallville-plus.git
cd smallville-plus
git checkout audit-r2-2026-10-23
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest
ruff check smallville tests scripts
```

Create the validated 25-resident connected cohort and run the accepted R2 shape:

```bash
python -m smallville populate --out runs/audit-population \
  --residents 25 --history-days 21
python -m smallville run --phase 3 --optimized --realism --days 1 \
  --population runs/audit-population/population.json --out runs/audit-r2
python -m smallville replay --source runs/audit-r2/events.jsonl \
  --out runs/audit-r2-replay
python -m smallville evaluate --run runs/audit-r2
python -m smallville serve --run runs/audit-r2
```

Run the two-day Valentine's benchmark separately:

```bash
python -m smallville benchmark valentine --days 2 --out runs/audit-valentine
```

The deterministic R2 acceptance run completed 1,440 simulated minutes for 25
residents with 955 MockLLM decisions. The complete suite passed 130 tests in the
recorded environment. Its replay reconstructed all 4,820 events; the source and
replay JSONL files were byte-identical at 53,963,644 bytes with SHA-256
`9eac01223e75aed37d805c6eb152bb81cf39050d193d6049668ee7c12fd80dce`.
These are recorded results, not a remote attestation; auditors should rerun them.

## Generated artifacts

Development runs currently occupy about 14 GB locally because event snapshots
favor transparency over storage efficiency. Publishing them in Git would make
the repository difficult to clone and would duplicate deterministic output.
They are excluded by `.gitignore`; the compact JSON/Markdown reports, plots,
checksums, and screenshots needed to inspect the reported conclusions are under
`reports/`. Every documented run can be regenerated with MockLLM without network
access. Live provider responses are not redistributed as a public dataset.

The tag's release assets are built locally under `dist/`: a source archive, a
cloneable full-history Git bundle, an artifact manifest, and `SHA256SUMS`. These
files are intentionally ignored so publishing them cannot recursively add the
bundle to itself.

Each new run writes `world.sqlite3`, `events.jsonl`, `calls.sqlite3`,
`cache.sqlite3`, `report.json`, and `report.md`. Treat the viewer as a local,
read-only research interface; it has no authentication layer for internet
hosting.

## Security and privacy review

- `.env`, runtime output, caches, and scratch inputs are ignored.
- A publication scan found no API-key, GitHub-token, cloud-key, or private-key
  signatures in the tracked tree or Git history.
- The deterministic backend and tests require no credentials or remote models.
- Live inference is explicitly gated by `--allow-paid`, a per-run cost cap, and
  configured per-token price ceilings. Reviewers should test failure and
  reservation paths as well as successful calls.
- Agent information boundaries are a research property, not a guarantee for
  real personal data. The included residents and histories are fictional or
  public research inputs; do not import confidential personal records.

Please open a GitHub issue for reproducibility, methodology, licensing, or code
findings. Use the private vulnerability-reporting link described in
`SECURITY.md` for a finding that could expose credentials, files, or a host.

High-value independent checks include prompt information leakage, event/state
atomicity under interruption, replay completeness, cost-cap races, private
message and conversation visibility, GM rule bypasses, evaluator construct
validity, multiple-seed behavioral stability, and the legal/provenance boundary
for every retained dataset file.
