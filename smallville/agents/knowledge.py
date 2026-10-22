"""Benchmark knowledge parsing with explicit attribution and epistemic status.

`campaign_evidence` is retained as the historical Phase 1--3 metric. New code
uses `campaign_claim` and owner-scoped `KnowledgeEvidence` records so exposure is
not silently equated with truth, acceptance, retention, or successful recall.
"""

import re
from dataclasses import dataclass

from smallville.world.models import KnowledgeEvidence, change


@dataclass(frozen=True)
class CampaignClaim:
    subject: str
    status: str


def _campaign_subject(text: str, speaker: str, listener: str | None) -> str | None:
    low = text.lower().replace("_", " ").replace("’", "'")
    if re.search(r"\bsam(?:uel)?(?: moore)?\b", low):
        return "sam_moore"
    if re.search(r"\b(?:i am|i'm|i was|i have|i've|i plan|i intend|i might|i may|i could)\b", low):
        return speaker
    if listener and re.search(
        r"\b(?:you are|you're|you were|your (?:plan|decision|candidacy|willingness))\b", low
    ):
        return listener
    return None


def campaign_claim(text: str, *, speaker: str, listener: str | None = None) -> CampaignClaim | None:
    """Parse an explicit mayoral-candidacy proposition, not general election talk.

    This deliberately bounded parser is evaluated against labeled fixtures. It
    does not claim general semantic understanding and returns ``None`` when the
    attribution or stance is unclear.
    """

    low = " ".join(text.lower().replace("’", "'").split())
    if re.search(r"\b(?:wonder whether|do you know whether)\b", low) or (
        "?" in low
        and re.match(r"^(?:who|what|when|where|why|how|is|are|will|would|could|might|may)\b", low)
    ):
        return None
    subject = _campaign_subject(low, speaker, listener)
    if subject is None or not re.search(r"\b(?:mayor|mayoral)\b", low):
        return None
    denied = (
        r"\b(?:not|isn't|wasn't|won't|will not|never)\b.{0,45}\b(?:run|running|candidate)",
        r"\b(?:don't|do not) think\b.{0,45}\b(?:run|running|candidate)",
        r"\b(?:no plans?|decided not|refused)\b.{0,35}\b(?:run|running)",
        r"\b(?:withdrew|withdrawn|dropped out|ended (?:my|the|his|her) campaign)\b",
    )
    considering = (
        r"\b(?:thinking|considering|weighing)\b.{0,40}\b(?:run|running|candidacy)",
        r"\b(?:might|may|could)\b.{0,35}\b(?:run|running|become a candidate)",
        r"\b(?:possible|potential)\b.{0,25}\b(?:run|candidate|candidacy)",
    )
    declared = (
        r"\b(?:am|is|are|was) running\b.{0,35}\b(?:for (?:local )?mayor|mayoral)",
        r"\b(?:plan|plans|planning|intend|intends|intending|going)\b.{0,35}\b(?:run|running)\b.{0,35}\b(?:mayor|mayoral)",
        r"\b(?:declared|announced|launched)\b.{0,35}\b(?:campaign|candidacy|run)\b.{0,25}\b(?:mayor|mayoral)",
        r"\b(?:candidate|candidacy)\b.{0,20}\b(?:for )?(?:local )?mayor\b",
        r"\b(?:willingness|decision|plan) to (?:stand|run)\b.{0,25}\b(?:mayor|mayoral)",
    )
    if any(re.search(pattern, low) for pattern in denied):
        status = "denied"
    elif any(re.search(pattern, low) for pattern in considering):
        status = "considering"
    elif any(re.search(pattern, low) for pattern in declared):
        status = "declared"
    else:
        return None
    return CampaignClaim(subject, status)


def campaign_knowledge_change(
    *,
    owner: str,
    text: str,
    source_id: str,
    source_kind: str,
    asserted_at: int,
    observed_at: int,
    speaker: str,
    listener: str | None = None,
    retained_memory_id: str | None = None,
):
    claim = campaign_claim(text, speaker=speaker, listener=listener)
    if claim is None:
        return None
    accepted = owner == claim.subject and source_kind in ("seed", "self_report")
    record = KnowledgeEvidence(
        id=f"knowledge:{owner}:{source_id}:mayoral_candidacy:{claim.status}",
        owner=owner,
        subject=claim.subject,
        predicate="mayoral_candidacy",
        claim_status=claim.status,
        epistemic_status="accepted" if accepted else "exposed",
        source_kind=source_kind,
        source_id=source_id,
        asserted_at=asserted_at,
        observed_at=observed_at,
        text=text,
        confidence=1.0 if source_kind == "seed" else 0.75 if accepted else 0.5,
        retained_memory_id=retained_memory_id,
    )
    return change("knowledge", record.id, record)


def clock_time_evidence(text: str, hour: int, minute: int = 0) -> bool:
    """Recognize explicit clock times, including a shared AM/PM range suffix."""
    low = text.lower()
    if re.search(rf"\b{hour:02d}:{minute:02d}\b", low):
        return True
    short, suffix = hour % 12 or 12, "p" if hour >= 12 else "a"
    minutes = rf":{minute:02d}" if minute else r"(?::00)?"
    return bool(
        re.search(
            rf"\b{short}{minutes}(?:\s*(?:to|[-–])\s*\d{{1,2}}(?::\d{{2}})?)?"
            rf"\s*{suffix}\.?\s*m(?=\b|\.)",
            low,
        )
    )


def campaign_evidence(identifier: str, text: str) -> bool:
    if identifier == "sam_moore" and re.search(
        r"(?:I am|Sam (?:Moore )?is) planning on running for local mayor", text
    ):
        return True
    return bool(re.search(r"\bSam[ _]Moore is running for (?:local )?mayor\b", text, re.I))


def party_schedule_evidence(text: str) -> bool:
    lower = text.lower()
    return (
        "valentine" in lower
        and "hobbs" in lower
        and bool(re.search(r"\b(?:feb(?:ruary)?\.?\s+14(?:th)?|2023-02-14)\b", lower))
        and clock_time_evidence(text, 17)
    )
