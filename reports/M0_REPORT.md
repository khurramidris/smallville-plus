# M0 cleanup — implementation ready, paid validation pending

Date: 2026-10-25. Milestone status: **incomplete** under the new paid-model rule.
The active scope and stop conditions are in [MILESTONES.md](../MILESTONES.md).
Only M0 has been implemented in this pass; M1–M4 have not started.

## Built

- Replaced the resident prompt's “Game Master” wording with first-person uncertainty
  about whether an intention can succeed. Phase number, retrieval backend/query
  diagnostics and working/archive storage labels stay outside resident requests.
- Added a full-request vocabulary check before cache access, budget reservation or
  provider dispatch. It applies to planning, repair, actions, reflection, interviews,
  private conversation turns, biographies, digital-history preparation and surveys.
  Internal adjudication can still use engine vocabulary. Private text is never
  echoed in the failure or silently rewritten.
- Added prompt tests using original seeds and the rich public 100-resident cohort,
  both tiers, populated private history and an active conversation. Negative cases
  cover the prohibited words in stable text, nested memory content and JSON keys.
- Separately changed report presentation: mock results say **fixture only**, mock
  JSON and Markdown contain no Park comparison figures/table, and unknown backend
  provenance cannot silently produce a paper comparison. Formulas are unchanged.
- Applied explicit labels to historical mock JSON, Markdown, interviews, personas,
  and stock CSV; [EVIDENCE.md](EVIDENCE.md) also labels the preserved screenshot/
  figure files. Every numeric observation in the 27 edited JSON artifacts and
  207 stock rows was checked against its prior value. Only paper reference fields
  were removed. Raw logs, source data and the published audit tag remain unchanged.

## Verification and paid results

Offline checks are recorded in [m0/offline-checks.json](m0/offline-checks.json):
**157 tests passed in 128.94 seconds**, with internet sockets disabled. Ruff and
diff whitespace checks pass. The existing replay, privacy, conservation and budget
tests remain green. Mock behavior exercised by tests is **fixture only**.
Machine-readable milestone status is in [m0/status.json](m0/status.json).

[Configuration preflight](m0/preflight.json) made no network request and found
no paid model selections, verified model prices, cap or provider credential in the
environment. A paid model and an M0 USD cap were requested. The M3 $25 allowance
does not silently authorize spending on this earlier milestone.

| Required milestone field | M0 result |
| --- | --- |
| Real paid-model result | Not run; model, price configuration, credential and cap pending |
| USD per resident per simulated day | Not measured |
| Input tokens per resident-day | Not measured |
| Event bytes per resident-day | Not measured |
| Total persistent bytes per resident-day | Not measured |
| New provider calls / paid spend | None / $0; this is not a resident-day cost result |

## Open problems and next boundary

M0 remains incomplete until the capped paid check runs and its actual measurements
are recorded. Stop here before M1. The old free MiniMax experiment, cached reruns,
and the independent review's exact fixture reproduction do not satisfy this gate.

The vocabulary rule deliberately applies to dynamic content as well as instructions.
An ordinary use of a forbidden word (for example, the occupation “agent”) will
stop a resident request without billing it. This follows the specified strict
rule; any contextual exception requires an explicit later policy change. The
guard prevents known terminology leaks, not every possible form of self-awareness.

Changed prompt text has new request hashes, so new inference must not be mistaken
for an exact cached rerun of the earlier audit. Historical event replay remains
compatible. Researcher-only data and source identifiers retain their existing
schema; citation IDs and privacy checks are preserved.

Memory is still lexical with heuristic importance and daily reflections; causal
`attempt` still has its old limitations; histories remain repetitive. Those are
M1/M2 and later validation issues, not claims repaired by this cleanup. No new
institutions, economy feature, social media, graph backend or scale work was added.
