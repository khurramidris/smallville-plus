# Contributing

Bug reports, audit findings, reproducibility results, and focused pull requests
are welcome. Explain the concrete behavior or research claim being tested and
include the smallest useful reproduction.

For a code change:

1. Use Python 3.11 or newer and install `.[test]`.
2. Keep model-free tests deterministic and offline.
3. Run `python -m pytest` and `ruff check smallville tests scripts`.
4. Update `PROGRESS.md` and `DECISIONS.md` when behavior, scope, or a research
   interpretation changes.
5. State what was tested and distinguish MockLLM engineering evidence from live
   model or human-subject evidence.

Do not commit credentials, `.env` files, `runs/`, model caches, raw provider
responses, or private personal data. Do not add a paid service or make a live
model call in a test.

Before retaining anything from another project or dataset, read its license,
pin the exact source revision, record the source path and checksum, preserve the
required notice, and update `THIRD_PARTY.md`. Prefer an independent
implementation of a documented pattern over vendored engine code.

Keep each pull request narrow enough to audit. Mechanism count, synthetic token
volume, or matching one benchmark number is not evidence of human realism;
comparative claims need the evaluation controls described in `REALISM_PLAN.md`.
