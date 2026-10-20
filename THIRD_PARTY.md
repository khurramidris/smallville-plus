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
