# Smallville+ independent review and revised milestones

Accepted 2026-10-25. This plan supersedes the delivery order and completion
criteria in the original `SPEC.md` and the historical R0–R6 plan. The original
specification and audit tag remain preserved.

## Review received

The independent reviewer reports that all 130 tests and Ruff pass at
`audit-r2-2026-10-23`, a fresh 25-resident R2 day reproduces the recorded JSONL
SHA-256 (`9eac0122…`) byte-for-byte, replay matches, and history contains no
credentials. These are reviewer-reported engineering checks, not paid-model or
human-realism evidence. Keep the clock, authoritative GM, partial observability,
hash-chained log, exact replay, budget reservation, cache and honest claim boundaries.

## Target and rules

- About **1,000 residents**: about 100 deep residents on a stronger model and
  about 900 standard residents on a cheaper model. Depth precedes breadth.
- No milestone is complete without a real **paid** model run under `SIM_MAX_USD`.
  MockLLM is for tests and the explicit M4 load fixture only. Label all mock-derived
  numbers **fixture only**, and never place them in a comparison table with Park
  et al. The scripted campaign and party behavior is not experimental evidence.
- Freeze new institutions, economy features, social media and Graphiti until M4
  passes. M2's expressly requested transfers/services are within scope.
- Stop after every milestone. Report the implementation, paid-model results,
  USD per resident-day, input tokens per resident-day, storage per resident-day,
  and open problems. Pending or stopped paid validation means an incomplete milestone.
- Ask before a run whose cap exceeds its authorized budget. M3 has a **$25 total**
  budget across both systems, all seeds and preparation. Ask before the real
  1,000-resident M4 run. M0–M2 paid models and caps still need selection; no
  previous free-route permission supplies a paid model or a new spending cap.
- Keep scorer improvements in separate changes from behavior changes.

## M0 — Cleanup

Remove engine/meta terms from resident-facing prompts. A regression must reject
`Game Master`, `simulation`, `agent`, `LLM` or `benchmark` in a complete resident
prompt, including dynamic context. Label every mock-derived reported number
`fixture only`; remove mock/Park comparison tables. Do not change metric formulas.

Status: implementation in progress; paid validation pending model/cap selection.

## M1 — Memory at least as good as Park et al.

Route real embeddings through the existing budgeted gateway, with lexical retrieval
as the offline fallback. Score importance from 1–10 with batched, cached model calls.
Trigger evidence-citing reflection when accumulated importance exceeds a threshold.
Retrieve by recency × importance × semantic relevance to the current situation.

Gate: after 500 routine events, relevant recall still finds identity, an unfinished
promise and a key relationship fact. Retrieval stays bounded and owner-private.
Preserve the existing archive; the 128-entry working limit must not discard
long-term evidence. Run paid validation before declaring this gate complete.

## M2 — Typed causal actions (historical R3)

Implement a GM handler registry with preconditions, duration, resources, allowed
effects and observer routing. Begin with giving/lending meals or items, requesting/
accepting/refusing services, arranging/cancelling joint appointments, and completing
shared tasks. Ambiguous interpretation proposes effects; only handlers validate
and commit them. Each counterpart decides their own consent.

Replace empty `attempt` success with a real effect, explicit failure or unsupported
result. Gate: Carmen's shortage can lead to a transfer, refusal or failed attempt;
items are conserved, memories go to the right people and trust changes cite evidence.
The historical R3 details in `REALISM_PLAN.md` remain design guidance.

## M3 — Paid-model validation

Run 25 residents for two simulated days in `connected_v1`, across three seeds, on
the paid model the user will name. The combined budget is $25; ask before exceeding
it. Validate R1, R2, M1 and M2 together. Run the original
`joonspk-research/generative_agents` code with the same model and score both systems
with identical diffusion, relationship-density, attendance and conversation metrics.
Read licenses before adapting upstream code and record provenance. Do not substitute
our MockLLM for the baseline if installation or API access is blocked.

Prepare a blinded human-rating packet with ten anonymized resident-day excerpts
from each system. Report means and ranges across seeds; no single-seed claims.
Collect human ratings separately from preparing the packet.

## M4 — Scale to 1,000

- Delta events with periodic checkpoints; exact replay remains mandatory.
- Stable cacheable prefixes and only currently relevant addresses/hours;
  target at most 100,000 input tokens per resident-day.
- Freeze a world view for residents due within each five-minute window; decide
  concurrently, then commit in deterministic order and recheck scarce resources.
- Concurrency up to 64 with provider rate limits and sparse activation.
- Separate deep and standard models. Use provider batch APIs for independent
  offline persona/survey work. Keep SQLite unless measurement proves a bottleneck.

Load sequence: mock 1,000 × one day (**fixture only**), paid 100 × one day, then
paid 1,000 × one day. Ask before the last run. Gates: at most 200 KB events per
resident-day, 1,000 × one day in at most four wall hours, exact replay, and reported
USD per resident-day for each tier. Measure both JSONL and total persistent storage
so the event target cannot hide growth in indexes, checkpoints or caches.

## Only after M4

Deep-tier temporal memory and 30-day drift runs (original Phase 4), institutions
created by residents (historical R4), and social media. Repetitive 21-day history
templates remain an acknowledged realism problem; do not claim they provide
three weeks of rich experience or start a separate breadth expansion to hide it.
