import asyncio
import json

import pytest

from smallville.apps.conversations import ProposeConversation, RespondConversation
from smallville.config import Config
from smallville.engine.simulation import Simulation
from smallville.eval.interviews import interview
from smallville.llm.gateway import Gateway, ResidentPromptViolation
from smallville.llm.mock import MockLLM
from smallville.llm.prompts import has_meta_terms
from smallville.personas.pipeline import PersonaPipeline
from smallville.world.maps import SmallvilleMap
from smallville.world.models import change


class PromptCheckingMock(MockLLM):
    """Inspect actual assembled provider requests, not just stable constants."""

    def __init__(self):
        self.tasks = set()
        self.calls = 0

    async def complete(self, **kwargs):
        prompt = kwargs["prompt"]
        assert not has_meta_terms(prompt), "resident request contains engine terminology"
        context = json.loads(prompt.rsplit("\n\nCURRENT CONTEXT:\n", 1)[1])
        assert not {"phase", "retrieval_backend", "retrieval_query"} & context.keys()
        assert all("storage" not in memory for memory in context.get("memories", []))
        self.tasks.add(context["task"])
        self.calls += 1
        return await super().complete(**kwargs)


@pytest.fixture(scope="module")
def rich_population(tmp_path_factory):
    config = Config()
    backend = PromptCheckingMock()
    gateway = Gateway(tmp_path_factory.mktemp("prompt-population"), config, backend)
    try:
        population = asyncio.run(PersonaPipeline(SmallvilleMap(), gateway, config).build(100, 21))
        assert backend.tasks == {"persona", "survey", "history_templates"}
        return population
    finally:
        gateway.close()


@pytest.mark.parametrize("phase,connected", [(1, False), (2, False), (3, False), (3, True)])
async def test_all_resident_prompt_paths_are_personal(tmp_path, rich_population, phase, connected):
    config = Config(
        phase=phase,
        realism_profile="connected_v1" if connected else "baseline",
        compact_context=connected,
        routine_actions=connected,
    )
    sim = Simulation(tmp_path / "town", config, population=rich_population if phase >= 2 else None)
    backend = PromptCheckingMock()
    sim.gateway.backend = backend
    # These direct mind calls exercise prompt construction, not the scheduler's
    # clock. Keep their call journal without recording scheduler-timed events.
    sim.gateway.on_call = None
    try:
        # Original seeds and all richer public-bank residents, both tiers, with
        # populated private history rather than empty dynamic contexts.
        for actor in sim.world.agents():
            await sim.mind.decide(actor, 600)
            if connected:
                actor.surprise = True
                await sim.mind.decide(actor, 605)
            await sim.mind.reflect(actor, 610)
        await interview(sim.mind, "john_lin", 615)
        assert {"plan", "action", "reflection", "interview"} <= backend.tasks
        if connected:
            assert "repair_plan" in backend.tasks

            # Real private-scene context and an independent conversation turn.
            actors = [sim.world.agent(owner) for owner in ("john_lin", "mei_lin")]
            for actor in actors:
                actor.location = "johnson_park"
                actor.pending = None
                actor.busy_until = 0
                actor.activity = "wait"
            sim.world.log.append(
                620, "prompt_fixture", changes=[change("agents", a.id, a) for a in actors]
            )
            scene, changes = sim.gm.conversations.proposal_changes(
                actors[0],
                ProposeConversation(
                    participants=[actors[1].id],
                    topic="our plans for this afternoon",
                    start=650,
                    end=670,
                    location="johnson_park",
                ),
                620,
            )
            sim.world.log.append(620, "conversation_proposed", actors[0].id, changes=changes)
            _, changes = sim.gm.conversations.response_changes(
                actors[1],
                RespondConversation(
                    conversation_id=scene.id, response="accept", reason="I have time."
                ),
                625,
            )
            sim.world.log.append(625, "conversation_accepted", actors[1].id, changes=changes)
            sim.gm.conversations.start(scene.id, 650)
            await sim.mind.conversation_turn(sim.world.agent(actors[0].id), scene.id, 650)
            assert "conversation_turn" in backend.tasks
    finally:
        sim.close()


@pytest.mark.parametrize(
    "word", ["Game Master", "simulation", "agent", "LLM", "benchmark", "AGENT_ID"]
)
@pytest.mark.parametrize("part", ["stable", "dynamic", "key"])
async def test_resident_meta_leaks_stop_before_cache_budget_or_dispatch(tmp_path, word, part):
    backend = PromptCheckingMock()
    gateway = Gateway(tmp_path, Config(), backend)
    stable = "I am planning my morning."
    dynamic = {"task": "interview", "question": "What will I do?"}
    if part == "stable":
        stable += " " + word
    elif part == "dynamic":
        dynamic["memories"] = [{"text": "A private message mentions " + word}]
    else:
        dynamic[word] = "internal field"
    try:
        with pytest.raises(ResidentPromptViolation) as failure:
            await gateway.complete(
                model="mock-fast", stable=stable, dynamic=dynamic, seed=42, resident=True
            )
        assert "private message" not in str(failure.value)
        assert backend.calls == gateway.summary()["calls"] == 0
        assert gateway.spent == 0
        assert gateway.cache.execute("SELECT count(*) FROM responses").fetchone()[0] == 0
    finally:
        gateway.close()


async def test_internal_adjudication_is_outside_resident_boundary(tmp_path):
    gateway = Gateway(tmp_path, Config(), MockLLM())
    try:
        response = await gateway.complete(
            model="mock-gm",
            stable="The Game Master adjudicates an agent intent.",
            dynamic={"task": "adjudicate", "intent": {"text": "I want to wave."}},
            seed=42,
        )
        assert json.loads(response)["plausible"] is True
    finally:
        gateway.close()
