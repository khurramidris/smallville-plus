# Build "Smallville+": a realistic simulated town (research project)

You are the lead engineer. First, save this entire prompt as SPEC.md at the repo root. Keep PROGRESS.md (what's done, what's next, open issues) and DECISIONS.md (why you chose things) updated after every step. Build ONLY Phase 1 in this session, then stop and report.

## Goal
A research simulation that beats Park et al.'s original Generative Agents (Smallville) on realism. The setting is an expanded Smallville: the original 25 characters plus new residents, in a town that follows real-world rules. Architecture must scale from 25 to 1,000+ agents, and the map must be a swappable module so a real city can replace it later.

## Hard constraints
- Python 3.11+, asyncio, Pydantic, pytest. SQLite (WAL mode) for world state.
- All LLM calls go through LiteLLM (paid APIs). Models come from env vars: SIM_MODEL_DEEP, SIM_MODEL_FAST, SIM_MODEL_GM, SIM_EMBED_MODEL. API keys only from env, never in code or logs.
- A deterministic MockLLM backend. The full test suite must pass with zero network access.
- Cost control: log every call (model, tokens, USD). SIM_MAX_USD caps each run with a hard stop. Cache LLM responses keyed on (model, prompt hash, seed) for cheap reruns and exact replay.
- Put stable prompt content (persona, world rules) first and dynamic content last, so provider prompt caching works.
- Read each reference repo's LICENSE before copying any code. Record what you took, from where, and under which license in THIRD_PARTY.md. Prefer porting patterns over vendoring large code.
- If the network blocks a download or API, stub it, note it in PROGRESS.md, and tell me. Don't work around it.

## Reference projects: what to take from each
- github.com/joonspk-research/generative_agents: the Smallville map ("the_ville" Tiled files), the 25 character seeds, memory retrieval (recency x importance x relevance), reflection, and day -> hour -> action planning. Also the original paper's experiments (information diffusion of Sam's mayoral run and Isabella's Valentine's party, relationship formation, party coordination) as our benchmarks.
- github.com/google-deepmind/concordia (v2): the Game Master pattern. Agents state intended actions in natural language; the GM checks plausibility against world state and decides outcomes. Study its GM components (event resolution, scene tracking) and port the pattern into our engine. Don't adopt their engine wholesale.
- github.com/facebookresearch/meta-agents-research-environments (ARE): a discrete simulated clock that runs faster than real time, an event queue with scheduled and condition-triggered events, an immutable event log, notifications with verbosity levels, and app APIs that mimic real apps' argument and JSON formats. Also the "universe" idea: each agent starts with weeks of pre-populated messages, calendar and contacts.
- github.com/HumanoidAgents/HumanoidAgents: basic needs (fullness, social, health, fun, energy) that decay over time, emotional state, and relationship closeness updated by conversations.
- github.com/StanfordHCI/genagents: persona format and survey-response methods (categorical and numerical answers). Its GSS-based agent bank is a source for new residents.
- Hugging Face dataset LLM-Digital-Twin/Twin-2K-500: survey items for the validation harness.
- github.com/EmergenceAI/Emergence-World (CC BY-NC; research use is fine): three memory types (episodic, reflective diary, relationship state), resource pressure, and self-governance. Ideas only.
- Later phases only: getzep/graphiti (temporal memory, Kuzu backend), camel-ai/oasis (social media layer), AgentTorch/AgentTorch (archetype background crowd), tsinghua-fib-lab/AgentSociety (economy and mobility modules, replay design), Tony-Yip/MobileCity (daily routines, async batched inference).

## Architecture
- world/
  - MapProvider interface; the Smallville implementation turns tiles into a location graph with addresses, capacity, opening hours and travel times.
  - WorldState store: agents, locations, objects, inventories, bank accounts, jobs, messages, calendar.
- engine/
  - SimClock, EventBus, scheduler.
  - Sparse activation: only agents with something to do call the LLM this tick.
  - Append-only EventLog (JSONL plus SQLite index) and replay.
- gm/
  - GameMaster takes an agent's intent and checks it against the rules first (location, opening hours, money, inventory, time). It calls an LLM only for ambiguous cases.
  - It emits outcome events plus per-agent observations. No agent can declare outcomes itself.
- agents/
  - Mind = Persona + Memory (stream, reflections, relationship state) + Drives (needs, emotion) + Planner (re-plans on surprises) + Perception.
  - Perception covers only the agent's current location plus phone notifications.
  - Two tiers: deep and standard.
- apps/
  - Shared phone apps: messaging, email, calendar, contacts, bank, town notice board.
  - Agent-to-agent communication goes through these apps.
- personas/
  - Expand the 25 seeds into full life histories.
  - Generate pre-populated digital history.
  - Run a t=0 consistency check: survey each agent and regenerate any whose answers contradict its persona.
- eval/: benchmarks and metrics.
- viewer/
  - FastAPI plus one HTML page that replays the event log on the 2D map.
  - Click an agent to see its memories, needs, plan and messages.
  - Includes a cost dashboard.

## Realism rules (non-negotiable)
- Agents are never told they are simulated, AI, or assistants. Prompts are written from the person's own inner perspective.
- Partial observability: agents know only what they perceived, were told, or remember.
- Everything costs time: travel, sleep, work hours. Needs decay. Money flows through wages, rent and prices. Shops close.
- Agents may disagree, refuse, forget, be busy, lie, or have conflicting goals. No default politeness or helpfulness.
- Heterogeneity: varied speech styles, per-agent sampling settings, and a config option to mix model families.
- Memory is fallible: retrieval is limited and nobody is omniscient.

## Phases
Phase 1 (this session):
- Engine, world, GM, the 25 agents with needs and emotions, messaging and calendar apps, MockLLM, cost tracking, and a basic viewer.
- Acceptance:
  - (a) Tests pass offline.
  - (b) 2 simulated days with 25 agents complete on MockLLM.
  - (c) The Valentine's party benchmark is runnable.
  - (d) A real-API run of 1 simulated day stays under SIM_MAX_USD.
- Then STOP and report: what was built, measured cost per agent per simulated day, and problems found.

Phase 2: persona pipeline, 100 residents, digital histories, t=0 validation, Twin-2K-500/GSS fidelity harness.
Phase 3: economy (jobs, wages, rent, shops), town council with votes, local news, resource pressure.
Phase 4: Graphiti long-term memory for deep agents, reflective diaries, 30-day runs, drift measurement.
Phase 5: scale to 1,000+ with tiers, sparse activation, batch API for offline jobs (persona generation, surveys), and an archetype background crowd.
Phase 6: an OASIS-style town social network.

## Evaluation (build the harness in Phase 1, extend it later)
- Replicate the original Smallville results: information diffusion, network density growth, party coordination. Report against the original paper's numbers.
- Believability interviews with agents, in the style of the original paper.
- Anti-homogeneity: variance of opinions and behaviors across agents.
- Daily life realism: hours spent sleeping, working and on leisure, compared with the shape of real time-use survey data.
- Cost per agent per simulated day.

## Working style
Small commits, tests for every module, and nothing built ahead of the current phase. Ask me before adding any paid service.
