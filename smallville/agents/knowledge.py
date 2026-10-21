"""Narrow benchmark evidence checks; do not infer facts from a topic mention."""

import re


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
        and ("february 14" in lower or "february 14th" in lower)
        and clock_time_evidence(text, 17)
    )
