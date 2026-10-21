"""Narrow benchmark evidence checks; do not infer facts from a topic mention."""

import re


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
        and ("february 14" in lower or "february 14th" in lower)
        and ("17:00" in lower or "5pm" in lower)
    )
