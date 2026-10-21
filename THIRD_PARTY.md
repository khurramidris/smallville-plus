# Third-party provenance

Licenses were downloaded and read before taking reference material (2026-10-20).
Copies are in `references/licenses/`; exact upstream commits, paths and SHA-256
digests are in `references/sources.json`. No reference engine code is vendored.

| Source | License inspected | Material used in Phase 1 |
| --- | --- | --- |
| [Generative Agents](https://github.com/joonspk-research/generative_agents) | Apache-2.0; Copyright 2023 Joon Sung Park | Unmodified `the_ville.tmx`, collision/sector matrices, sector names, map metadata, 25 original `scratch.json` persona seeds and initial relationship whispers. Original implementation of limited recency × importance × lexical relevance retrieval, reflection and hierarchical planning. |
| [Concordia](https://github.com/google-deepmind/concordia) | Apache-2.0 | Studied current v2-style `EventResolution`, `SendEventToRelevantPlayers` and `SceneTracker`; ported the conceptual split between intent, authoritative resolution and filtered observations. No source code copied. |
| [ARE](https://github.com/facebookresearch/meta-agents-research-environments) | MIT; Meta Platforms, Inc. and affiliates | Studied events and notifications documentation; independently implemented discrete time, scheduled/condition events, append-only history and typed phone APIs. Universe histories deferred to Phase 2. |
| [HumanoidAgents](https://github.com/HumanoidAgents/HumanoidAgents) | Apache-2.0 | Needs/emotion/closeness concepts; independent continuous-time update rules, with explicitly uncalibrated coefficients. No code copied. |
| [genagents](https://github.com/StanfordHCI/genagents) | MIT; Copyright 2024 Joon Sung Park | Inspected persona/memory organization; no code or agent bank copied. Survey pipeline deferred. |
| [Emergence World](https://github.com/EmergenceAI/Emergence-World) | CC BY-NC 4.0 research-only notice | Ideas only: episodic memory and relationship state. No profiles, datasets, prompts or engine code copied. Diary/resource/self-governance work deferred. |

The Tiled source is retained for provenance and portability. The viewer renders
a schematic from the collision and sector matrices; external tileset art is not
bundled or downloaded. Addresses, hours, capacities, travel speed, numeric traits
and needs coefficients are Smallville+ modeling assumptions, not upstream facts.
Original names/seed text are retained, including upstream spelling inconsistencies;
the loader normalizes a small, documented alias list for relationship matching.

Reference source snippets used for study are outside the tracked tree in
`scratch/references/`. The provenance manifest records them even though they are
not redistributed. No upstream NOTICE file was present in the inspected roots.

Benchmark numbers are factual results from Park et al., *Generative Agents:
Interactive Simulacra of Human Behavior*, UIST 2023,
[arXiv:2304.03442v2 §7.1](https://arxiv.org/html/2304.03442v2#S7.SS1):
Sam awareness 8/25, party awareness 13/25, attendance 5/12 invited guests,
mutual-knowledge density 0.167 → 0.74. This is a comparison target, not a claim
of experimental equivalence.

Twin-2K-500/GSS and all later-phase repositories are not imported, redistributed
or used in Phase 1. Their licenses and data terms must be checked when their
respective phases are authorized.

## Phase 2 additions (authorized 2026-10-21)

- **genagents public GSS demographic bank — MIT.** Retained 75 unmodified
  `agent_bank/populations/gss_agents/*/scratch.json` files at commit
  `96854071ef4c2d79c93144c973c7820722d52bab` under `smallville/data/gss/`.
  The existing MIT notice is in `references/licenses/StanfordHCI__genagents.txt`.
  Selection is the first 75 paths ordered by SHA-256 of
  `smallville-phase2:` plus upstream path. Names/addresses in this bank are
  fictional; two full names occur twice and distinct source IDs are retained.
  These are demographic proxies, not the restricted interview-based agent bank.
  Source city/state become previous residence; new Smallville homes are authored
  overlays. Life histories and digital messages are fictional additions.
- **Twin-2K-500 — CC BY 4.0.** Read the dataset card and license declaration
  before downloading source survey material. Source revision:
  `f883165a3026fde855dfd448e0cd16443ab257b6`. Retained a normalized, bounded
  sample under `smallville/data/surveys/twin_sample.json`, derived from the
  official question catalog and wave 1–3/wave 4 numerical response CSVs.
  Source card and catalog documentation are retained in `references/phase2/`.
  The 20 participants are chosen by SHA-256 of `smallville-twin:` plus pid.
  The adapter supports single-choice, matrix, slider and explicitly bounded
  numerical items. Exclusions and missingness are preserved in dataset metadata.
  Every wave-4 QuestionID is excluded from profile evidence; prior responses to
  targets are used only by the scorer. No dataset-generation code was copied.

Attribution: **Twin-2K-500**, Olivier Toubia, George Z. Gui, Tianyi Peng,
Daniel J. Merlau, Ang Li and Haozhe Chen (2025).
Source: https://huggingface.co/datasets/LLM-Digital-Twin/Twin-2K-500
Paper: https://arxiv.org/abs/2505.17479
License: https://creativecommons.org/licenses/by/4.0/
Changes: normalization into typed items and evidence/target splits, bounded
subject selection, and explicit unsupported-item exclusions. No endorsement is implied.

Exact Phase 2 URLs, revisions and original-file SHA-256 hashes are recorded in
`references/phase2/sources.json`. Full response CSVs are not vendored; they remain
local preparation inputs in `scratch/phase2/`. No Phase 3–6 sources were added.

## Phase 3 additions (authorized 2026-10-21)

The ledger, contracts, shops, council, news and shared-event code are original
implementations. Resource pressure and local self-governance extend the previously
studied Emergence World ideas; no additional upstream code, prompts, profiles or
datasets were copied. Its inspected CC BY-NC notice remains applicable to that
conceptual research reference. Economic amounts, initial capital, supply-delay
scenario and council proposal are Smallville+ fictional modeling assumptions.
No Phase 4–6 source or dependency was added.
