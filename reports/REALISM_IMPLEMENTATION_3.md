# Connected realism implementation 3: R2 social process

Completed 2026-10-22. This batch implements the R2 engineering scope in
[`REALISM_PLAN.md`](../REALISM_PLAN.md). It establishes working social-process
mechanisms; it does not establish that Smallville+ is more believable than Park
et al.'s study.

## What changed

- Spoken interaction is now an app-mediated, scheduled process. A resident
  proposes a local time window to one to three people; every invitee independently
  accepts, refuses or lets the invitation expire. Accepted residents must remain
  able to reach the scene, and only residents who are present and free enter it.
- Each active participant gets their own budgeted model turn from private context.
  They may speak or leave. Scenes can continue after a departure while two people
  remain. The GM commits the turn and its exact observer list; physical bystanders
  do not receive the words, memories or testimony.
- Phone bodies are no longer read automatically on every connected-profile wake.
  Notification summaries expose sender, time and urgency. A five-minute check
  reads at most two messages, urgent first, and persists attention statistics.
- Social state is directed: trust, affinity, familiarity and obligation belong to
  one resident's view of another. Verified contact may change familiarity. Signed
  changes require an explicit bounded appraisal citing a turn that resident heard.
  Social emotion impulses decay with a six-hour half-life.
- The scheduler reserves conversation time and return travel. Future-plan repair
  includes accepted scenes. Evaluation protocol `realism-eval-v2` reports scene,
  turn, phone-attention and directed-relationship diagnostics. The viewer exposes
  a selected resident's observed thread, social state and phone attention.

## Offline acceptance

The accepted run used Phase 3, the optimized connected profile, MockLLM, seed 42
and the published 25-resident version 3 population with digest
`227c856e91acb3160d61e50b582646b8ec9a40e237bf87cff0bb178a6bc7ccc1`.
It completed 1,440 simulated minutes in 121.248 wall seconds.

| Measurement | Result |
| --- | ---: |
| Model decisions | 955 |
| Action / plan / repair / turn / reflection calls | 735 / 25 / 158 / 12 / 25 |
| Synthetic input / output tokens | 5,629,889 / 43,430 |
| USD total | $0 |
| USD per resident per simulated day | $0 |
| Co-present activations | 686 |
| Conversation proposals | 21 |
| Accepted / refused / expired invitations | 4 / 7 / 29 |
| Scenes started / cancelled at start | 3 / 18 |
| Spoken turns / voluntary departures | 11 / 1 |
| Distinct speakers | 7 |
| Phone checks / messages read in checks | 63 / 84 |
| Runtime messages delivered / unread at horizon | 79 / 1 |
| Evidence-linked relationship appraisals | 3 |

All three admitted scenes produced spoken exchange. Their conversion was still
low: 3 of 21 proposals started, or 0.437 started scenes per 100 co-present
activations under this diagnostic denominator. The 84 reads include older unread
history as well as the 79 messages delivered during the run.

The trace contains concrete independent behavior:

- Eddy Lin invited Arthur Burton and Ayesha Khan. All three attended and took
  four alternating turns. Arthur withheld agreement; Ayesha and Eddy later made
  their own positive, evidence-linked appraisals.
- Jennifer Moore and Jane Moreno exchanged three spoken turns. Jane then chose to
  leave, ending the two-person scene early.
- Yuriko Yamamoto invited Sam Moore and Jane Moreno. Sam accepted, Jane refused,
  and Yuriko and Sam completed four turns. Sam's later appraisal cited Yuriko's
  actual preceding turn.

The run retained Sam-campaign evidence for 8 of 25 residents, matching the paper's
reported count only as an unmatched descriptive result. Party evidence reached 11
of 25. This one-day horizon ends before the Valentine's event on day two, so its
zero attendance is not a party benchmark result. Money, food, ledger and work-limit
audits all passed.

## Verification

- The complete offline suite contains 130 tests and passed in 165.948 seconds. It
  covers willing, busy,
  refusing and silent invitees; three-person turns; false testimony; voluntary
  departure; travel and calendar conflicts; excluded bystanders; bounded phone
  reads; directed appraisal evidence; emotion decay; plan-fragmentation repair;
  scheduler integration; metrics and viewer privacy. A controlled fixture changes
  only directed trust and observes the invitation choice flip.
- Replay reconstructed all 4,820 events and every projection exactly. The source
  and replay JSONL are byte-identical: 53,963,644 bytes, SHA-256
  `9eac01223e75aed37d805c6eb152bb81cf39050d193d6049668ee7c12fd80dce`.
- Local Chromium displayed all 25 residents at an active scene, the selected
  resident's directed relationships, phone attention and heard conversation
  turns. It produced no page error or external request.
- Ruff passes for owned source and tests. Repository-wide formatting still flags
  a retained upstream dataset-card code sample; that provenance file remains
  unchanged.
- No provider, network API, model download, credential or paid service was used.

The compact run report is [`r2/acceptance.json`](r2/acceptance.json), replay
evidence is [`r2/replay-check.json`](r2/replay-check.json), browser evidence is
[`r2/browser-check.json`](r2/browser-check.json), and the viewer capture is
[`r2/viewer.png`](r2/viewer.png).

## Problems found and fixed

1. New neutral runtime fields changed an already published population digest.
   Fingerprinting now excludes only their neutral defaults and still rejects a
   population carrying runtime scene state.
2. Repeated surprise repairs accumulated semantically meaningless block seams
   until a plan exceeded its 32-block bound. Merging now coalesces adjacent
   equivalent blocks; a regression performs 40 repairs.
3. A host could finish an outbound walk before a scene yet lack time to return.
   The GM now reserves both action duration and travel from the projected ending
   location.
4. Residents were offered invitations whose five-minute response could not finish
   before the start. Those invitations now expire silently at that boundary.
5. The deterministic fixture could propose a second overlapping scene while
   already committed. It now refrains from hosting when a commitment is pending.

## What the result does not show

Mock dialogue remains short and formulaic, and some generated goal prose has
awkward grammar. All three accepted appraisals happened to be positive in this
single seed, although negative and asymmetric paths are covered by controlled
tests. Eighteen proposed scenes failed to start, and the opportunity denominator
is correlated repeated activation rather than independent encounters. There are
no human believability ratings, matched ablation, multiple-seed confidence
intervals or real-model R2 run.

The 5.63 million synthetic input tokens and 53.96 MB one-day event log are also
cost and scale warnings. The full-snapshot replay design and repeated large
contexts need later optimization before long or 1,000-resident experiments.

R3 is next: typed causal actions for requests, consent, item/meal transfer,
services, joint appointments and shared tasks. Those consequences are required
before the Carmen shortage chain or richer negotiation can be claimed as a
working social system.
