import json

from smallville.agents.mind import Mind
from smallville.eval.reporting import evidence_labels
from smallville.world.models import change

QUESTIONS = {
    "self_knowledge": "What matters to me in my work and home life?",
    "memory": "What did someone tell me recently, and how sure am I about it?",
    "plans": "What do I intend to do next, and what might prevent it?",
    "reaction": "If the place I planned to visit were closed, what would I do?",
    "reflection": "What have I learned about getting along with the people I know?",
    "campaign_recall": (
        "Has Sam Moore said whether he will run for mayor? State what status I remember "
        "and who told me; say that I do not know if I cannot recall evidence."
    ),
}


async def interview(mind: Mind, identifier: str, minute: int) -> list[dict]:
    agent = mind.world.agent(identifier)
    responses = []
    for category, question in QUESTIONS.items():
        context = mind.context(agent, minute, "interview", query=question)
        context["question"] = question
        raw = await mind.ask(agent, context)
        try:
            answer = json.loads(raw)
            if not isinstance(answer["answer"], str):
                raise ValueError("answer must be text")
            opinion = float(answer["opinion"])
            if not -1 <= opinion <= 1:
                raise ValueError("opinion outside response range")
            answer = {"answer": answer["answer"][:4000], "opinion": opinion}
        except (ValueError, KeyError, TypeError):
            answer = {"answer": "Unusable response", "opinion": None}
        record = {
            "category": category,
            "question": question,
            **answer,
            "available_evidence": [m["id"] for m in context["memories"]],
            "human_rating": None,
            "claim_assessment": None,
        }
        mind.world.log.append(
            minute, "interview", identifier, record, [change("agents", identifier, agent)]
        )
        responses.append(record | evidence_labels(mind.config.backend))
    return responses
