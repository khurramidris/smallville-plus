from pydantic import model_validator

from smallville.eval.surveys import SurveyItem, SurveyResult, SurveyRunner
from smallville.world.models import Agent, Model


class ConsistencyAttempt(Model):
    resident: str
    attempt: int
    passed: bool
    contradictions: list[str]
    invalid_items: list[str]

    @model_validator(mode="after")
    def honest_status(self):
        if self.passed != (not self.contradictions and not self.invalid_items):
            raise ValueError("consistency status disagrees with its recorded errors")
        return self


def consistency_items(agent: Agent) -> list[SurveyItem]:
    p = agent.persona
    items = [
        SurveyItem(
            id="name",
            question="What is my full name?",
            kind="categorical",
            fact_key="name",
            choices=[p.name, "I don't remember", "I prefer not to say"],
        ),
        SurveyItem(
            id="age",
            question="How old am I in years?",
            kind="numerical",
            fact_key="age",
            minimum=0,
            maximum=120,
            integer=True,
        ),
        SurveyItem(
            id="home",
            question="Where do I live?",
            kind="categorical",
            fact_key="home",
            choices=[p.home, "elsewhere", "I don't remember"],
        ),
        SurveyItem(
            id="workplace",
            question="Where are my regular work or study responsibilities?",
            kind="categorical",
            fact_key="workplace",
            choices=[p.workplace, "elsewhere", "I don't remember"],
        ),
    ]
    for field in (
        "marital_status",
        "work_status",
        "highest_degree_received",
        "political_views",
        "religion",
    ):
        if field in p.facts:
            answer = str(p.facts[field])
            choices = list(dict.fromkeys([answer, "I don't remember", "I prefer not to say"]))
            if len(choices) >= 2:
                items.append(
                    SurveyItem(
                        id=field,
                        question=f"How do I describe my {field.replace('_', ' ')}?",
                        kind="categorical",
                        fact_key=field,
                        choices=choices,
                    )
                )
    return items


def contradictions(agent: Agent, result: SurveyResult) -> list[str]:
    return [
        item.id
        for item in consistency_items(agent)
        if result.answers.get(item.id) != agent.persona.facts[item.fact_key]
    ]


async def check_resident(runner: SurveyRunner, agent: Agent, attempt: int) -> ConsistencyAttempt:
    p = agent.persona
    background = f"My name is {p.name}. My life: {p.life_history.narrative}\nMy own background facts: {p.facts}"
    result = await runner.answer(
        agent.id,
        background,
        p.facts,
        consistency_items(agent),
        tier=p.tier,
        temperature=p.temperature,
        revision=f"t0-attempt-{attempt}",
    )
    errors = contradictions(agent, result)
    return ConsistencyAttempt(
        resident=agent.id,
        attempt=attempt,
        passed=not errors and not result.invalid,
        contradictions=errors,
        invalid_items=sorted(result.invalid),
    )
