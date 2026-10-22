# Realism audit: why Smallville+ still falls short

Date: 2026-10-22. Baseline: `b042d8d`; simulation behavior: `8e2b410`.
Scope: source review, retained pinned upstream material, and read-only inspection
of the completed 25-person three-day real-model run. No new model calls or later
phase implementation. [Machine-readable evidence](realism/phase3-audit.json).

**The original ambition was to surpass Smallville's realism. We have not delivered
that research outcome.** Phases 1–3 delivered working infrastructure and selected
mechanisms, but many mechanisms are shallow or poorly connected. Completion was
judged mainly by correctness, replay and runnable scenarios. Those are necessary
engineering gates; they do not establish believable people or an emergent society.
The earlier completion reports should be read as functional milestones, not
completion of the realism goal. This is a design/integration gap we need to own.

There is more explicit economic accounting than the original setup, but adding
accounts, needs and a ballot does not ensure that motives, relationships and
institutions influence one another. Several links in that chain are currently
missing. Some were deferred by the phase plan; others were oversimplified within
features already described as implemented.

## Demonstrated gaps

| Finding | Evidence in the implementation/run | Consequence |
| --- | --- | --- |
| Important memories are erased by routine activity | `memory.py` retains only the newest 128 entries. All 25 buffers reached the cap; original seed memories fell from 62 to 2. 2,718 of the final 3,200 entries are generic GM outcomes. | Salient life context competes with “I finished…” records. Fallible memory has become indiscriminate deletion. |
| Retrieval barely uses the current situation | One fixed query containing “plans today work family party Valentine mayor needs messages”; keyword overlap; only 5/8 retrieved entries. `SIM_EMBED_MODEL` is configured but not used for embeddings. | A relevant promise, relationship or event may never reach the decision prompt, even when stored. Benchmark names are built into everyday retrieval. |
| Richer residents were not activated in the live experiment | 0/25 live personas have a full `life_history`; zero pre-epoch messages; no population artifact. The Phase 2 full-history cohort was exercised with MockLLM. | The demonstrated real-model town does not combine the Phase 2 universe/persona work with Phase 3 behavior. |
| People cannot conduct a proper local conversation | No conversation action/session. Leisure can describe talking, but completion only records finishing leisure. Messages exist and can be substantive; a local multi-turn encounter does not. | Co-location and invitations often fail to become information exchange, negotiation or relationship development. |
| The general GM has almost no meaningful general effects | Its ambiguous-action LLM returns only `plausible`. All 25 completed `attempt` actions updated only the actor and recorded “no confirmed wider outcome.” | Natural-language intentions outside the narrow action menu cannot produce richer causal world changes. |
| Relationships are weakly connected to choices | Scores are a single scalar changed by four negative substrings; otherwise messages add closeness. Numeric relationship state is absent from decision context. Some relational content can still enter through remembered text. | Trust, affection, conflict, obligations and reputation are conflated; changing a score alone need not alter a decision. |
| Emotion is transient and simplistic | Emotion is recomputed directly from needs, even at zero elapsed time. A copied-resident probe classifies “I do not disagree” negatively and an upset refusal positively. | Interpersonal events do not have a durable, reliably interpreted emotional effect. |
| Goals and plans are too weak | No active goal/commitment state machine; daily blocks allow only sleep/eat/work/leisure. “Hour planning” clips a block to the next hour, without a separate purposeful task decomposition. 55 invalid-plan fallbacks among 378 plan responses; 8/72 reflection failures. | Personal projects, promises and conflicting priorities tend to collapse into generic routines. |
| Institutions are mostly an authored scenario | One fixed food proposal, fixed jobs/prices, one meal commodity and scheduled bulletins. Residents can vote and post statements, but cannot initiate a new policy, hire someone, negotiate a contract or transfer a meal. | Voting is real choice within a narrow poll; it is not yet broad self-governance or a developing economy. |
| Visual/physical detail is coarse | Original tile geometry, 19 named seed-cohort locations, fixed travel speed and opening hours; schematic dots. Room/object affordances and service queues are absent. | People have few things to do at a location, and the display cannot show detailed social activity that the engine has not represented. |
| Evaluation does not yet support the research claim | One real model/seed, no blinded ratings, mock-only survey fidelity, unmatched original-paper comparisons. Opinion variance measures seeded numbers. | Passing tests and higher feature counts cannot establish greater realism. |

Source pointers: [memory](../smallville/agents/memory.py),
[mind and prompts](../smallville/agents/mind.py),
[action/plan schemas](../smallville/world/models.py),
[GM](../smallville/gm/master.py), [drives](../smallville/agents/drives.py),
[phone](../smallville/apps/phone.py), [council](../smallville/apps/civic.py),
[history generator](../smallville/personas/histories.py),
[metrics](../smallville/eval/metrics.py).

## Concrete examples from the trace

At minute 535 Hailey chose leisure with the intention to see whether someone was
open to a friendly conversation. At minute 1,070 Latoya chose leisure to chat
with Rajiv about the election and food proposal. The engine records a leisure
activity; it does not ask the other resident to respond or deliver spoken turns.
This is an engine affordance gap, not proof that the model refused to socialize.

Carmen's public request for spare meals is visible in the completed run. The town
supports bank transfers and retail purchases but no peer-to-peer meal handover.
A potentially interesting chain—shortage, asking for help, refusal or help,
obligation, later repayment—cannot be completed through the current action API.

Sam sent Adam: “I am thinking of running for local mayor…” at minute 523. Adam
read it at 525 and replied with encouragement at 550, then suggested developing
a campaign message. The current scorer does not recognize this first-person,
qualified testimony. Sam's original campaign seed disappears at minute 3,780
(day 3, 15:00); the later campaign-planning reply remains in his final memories.
**The reported campaign score of zero does not mean no campaign communication
occurred, or that all relevant knowledge disappeared.** Exposure, considering
candidacy, declared candidacy, retained evidence and successful recall must be
measured separately. The audit reuses the narrow detector only to expose its
limits, not to create a corrected human-awareness score.

Relationships grew from 70 to 73 mutually recorded pairs (density 0.233 to 0.243).
There were 89 phone messages across 33 pairs, three confirmed party guests, and
an executed council vote. These are genuine recorded interactions and outcomes.
They coexist with weak interaction depth; they do not support a blanket claim
that nothing social happened.

## What we actually took from the reference projects

This table audits the retained versions described in [THIRD_PARTY.md](../THIRD_PARTY.md)
and [source manifests](../references/sources.json), not the latest upstream releases.
No new upstream code was copied for this audit.

| Reference | Present | Missing or simplified | Next useful contribution |
| --- | --- | --- | --- |
| [Generative Agents](https://github.com/joonspk-research/generative_agents) | Actual map/seeds/relationship whispers; limited retrieval, daily planning, reflection; benchmark harness | Lexical rather than semantic recall; destructive FIFO; little observation memory; weak task decomposition; no local conversation process | Salient contextual recall, persistent motives, observation-to-reflection-to-plan feedback, consensual conversation |
| [Concordia](https://github.com/google-deepmind/concordia) | Intent/outcome authority and filtered private observations | GM mostly validates a fixed menu; scene is essentially location/time, not a persistent social episode | Scene participants, evidence-grounded event resolution, bounded typed effects and participant-specific observations |
| [ARE](https://github.com/facebookresearch/meta-agents-research-environments) | Clock, ordered events, conditions, notifications, replay; phone history pipeline | Histories are template/ring based and absent from live cohort; no direct scheduler resume; no dedicated email/contact-management API | Causally connected digital histories, meaningful unfinished obligations, durable execution state and richer app contracts |
| [HumanoidAgents](https://github.com/HumanoidAgents/HumanoidAgents) | Five needs, emotion labels and relationship updates | Global uncalibrated decay coefficients; substring sentiment; weak lasting effects | Event appraisal and distinct, persistent social state that actually influences plans |
| [genagents](https://github.com/StanfordHCI/genagents) | Public demographic seeds, persona generation/consistency and typed survey interfaces | Mock template biographies, narrow t=0 checks, no restricted interview bank and no real-model fidelity result | Source-grounded richer histories and blinded, held-out evaluation; never imply demographic proxies are interview twins |
| [Twin-2K-500](https://huggingface.co/datasets/LLM-Digital-Twin/Twin-2K-500) | Licensed bounded survey subset, held-out scorer and human test–retest references | Only fixture predictions tested; not linked to longitudinal town behavior | Real-model held-out fidelity and drift evaluation, with matched denominators and contamination caveats |
| [Emergence World](https://github.com/EmergenceAI/Emergence-World) | Resource pressure and council ideas; episodes and simple relationship state | No reflective diary, meaningful general resource dependence or agent-initiated governance | Connect diary/relationships to competing goals, cooperation, institutions and consequences; ideas only under original scope |
| Graphiti, OASIS, AgentTorch, AgentSociety, MobileCity | Deferred by the original phase plan | Not imported or integrated | Temporal memory, later social media/crowd scale, and studied mobility/economy/batching patterns after behavioral foundations pass |

The combination so far is mostly independent implementations of selected patterns.
Importing the remaining engines wholesale would not resolve the missing causal
links or establish correctness. Each borrowed mechanism needs a defined input,
world effect, observation path and behavioral test.

## Why speed work did not solve realism

The successful run used 2,865 action responses, 378 plans, 72 reflections and 25
GM adjudications: **44.53 successful responses per resident-day**. Most inference
was spent selecting short activities, not sustaining social interaction. Exactly
345 of 3,210 intentions continued a chosen routine without another action call.

Four-way concurrency and compact context reduce some overhead; only decisions
at the same simulated minute can overlap. The model's median successful request
was 3.62 seconds, p95 10.18 seconds. Recorded active wall time was at least about
three hours, excluding the outage. A richer conversation system will add calls
unless routine scheduling, incremental planning and context selection improve.
There is no evidence from this single-model run that merely buying a stronger
model would repair missing actions, memory loss or disconnected state.

## What remains uncertain

The code and trace establish the structural gaps above. They do not quantify the
causal share of each gap, isolate the effect of context compression, validate a
psychological model, or establish how another model family would behave. Test
these through controlled ablations and human assessment. Neither reproducing a
paper's attendance number nor maximizing disagreement is sufficient realism.

The next work should repair and connect existing mechanisms before scaling the
population or running 30 days. The proposed sequence and acceptance gates are
in [REALISM_PLAN.md](../REALISM_PLAN.md).

Reproduce the read-only audit:

```bash
python scripts/audit_realism.py --run runs/phase3-resumed-live-25 --out reports/realism/phase3-audit.json
```

The script checks final projections against all recorded agent snapshots, reads
exact cached outputs, hashes the immutable JSONL and runs isolated heuristic
probes on copied residents. It makes zero network/model calls and does not mutate
the run. Original run artifacts and numerical results remain preserved.
