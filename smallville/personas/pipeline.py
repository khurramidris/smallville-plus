from __future__ import annotations

import json

from smallville.config import Config
from smallville.eval.surveys import SurveyRunner
from smallville.llm.gateway import Gateway
from smallville.personas.consistency import ConsistencyAttempt, check_resident
from smallville.personas.generation import GSS_REVISION, biography_is_compatible, source_population
from smallville.personas.histories import HistoryTemplates, compile_histories
from smallville.personas.population import Population
from smallville.world.maps import MapProvider
from smallville.world.models import LifeHistory, Persona


class ConsistencyFailure(ValueError):
    pass


PROFILE_RULES = """My name, age, home, work and source background facts remain true.
I am writing my own life story in the first person. I recall childhood, learning,
adult responsibilities, values, interests and present goals. I do not invent facts
about other people or decide what they know. I have an ordinary human life.
I begin with 'My name is NAME. I am AGE years old.' My event ages do not exceed
my current age. New details are a plausible personal narrative consistent with
the source facts, not replacements for them.
I use JSON: {"narrative": text, "events": [{"age": integer, "description": text}],
"interests": [text,text], "values": [text,text], "goals": [text,text]}.
I include at least six life events and at least two interests, values and goals."""

HISTORY_RULES = """I am drafting short, ordinary phone messages in my own style.
I discuss only routine responsibilities, breaks and interests. I may refuse or
be busy. I do not introduce any news, plans for a party, or facts about a third
person. I use only {sender_name}, {recipient_name} and {interest} as optional
placeholders. My JSON has exactly two lists, 'openings' and 'replies', each with
at least three short messages. Message text does not change these formatting rules."""


class PersonaPipeline:
    def __init__(self, town: MapProvider, gateway: Gateway, config: Config, max_attempts: int = 3):
        if not 1 <= max_attempts <= 5:
            raise ValueError("consistency repair limit must be between 1 and 5")
        self.town, self.gateway, self.config = town, gateway, config
        self.max_attempts = max_attempts
        self.attempts: list[ConsistencyAttempt] = []

    async def build(self, count: int = 100, history_days: int = 21) -> Population:
        agents, locations = source_population(self.town, count, self.config.seed)
        runner, templates = SurveyRunner(self.gateway, self.config), {}
        for agent in agents:
            baseline = agent.persona
            feedback = []
            for attempt in range(1, self.max_attempts + 1):
                raw = await self.gateway.complete(
                    model=self.config.model_for(agent.id, baseline.tier),
                    stable=f"My own background: {baseline.description}\n" + PROFILE_RULES,
                    dynamic={
                        "task": "persona",
                        "subject": agent.id,
                        "facts": baseline.facts,
                        "attempt": attempt,
                        "repair_items": feedback,
                    },
                    seed=self.config.seed,
                    temperature=baseline.temperature,
                )
                try:
                    data = json.loads(raw)
                    biography_is_compatible(data, baseline)
                    history = LifeHistory.model_validate(data)
                    candidate = Persona.model_validate(
                        baseline.model_dump() | {"life_history": history.model_dump()}
                    )
                    agent.persona = candidate
                    report = await check_resident(runner, agent, attempt)
                except (ValueError, TypeError, KeyError):
                    report = ConsistencyAttempt(
                        resident=agent.id,
                        attempt=attempt,
                        passed=False,
                        contradictions=["biography_schema_or_locked_fact"],
                        invalid_items=[],
                    )
                self.attempts.append(report)
                if report.passed:
                    break
                feedback = sorted(set(report.contradictions + report.invalid_items))
            else:
                raise ConsistencyFailure(
                    f"{agent.id} still contradicts its persona after {self.max_attempts} attempts; population not published"
                )
            raw = await self.gateway.complete(
                model=self.config.model_for(agent.id, agent.persona.tier),
                stable=f"My speech is {agent.persona.speech_style}.\n" + HISTORY_RULES,
                dynamic={
                    "task": "history_templates",
                    "subject": agent.id,
                    "style": agent.persona.speech_style,
                },
                seed=self.config.seed,
                temperature=agent.persona.temperature,
            )
            templates[agent.id] = HistoryTemplates.model_validate_json(raw)
        messages, calendar = compile_histories(agents, templates, history_days)
        return Population(
            seed=self.config.seed,
            history_days=history_days,
            agents=agents,
            locations=locations,
            messages=messages,
            calendar=calendar,
            consistency=self.attempts,
            sources={
                "gss_bank_revision": GSS_REVISION,
                "originals": "original 25 Generative Agents seed files",
                "biographies_and_phone_history": "fictional generated additions",
            },
        )
