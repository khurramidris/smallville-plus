"""Resident-facing vocabulary checks, applied before cache or provider access."""

import re

# Underscores are boundaries too: an internal `agent_id` key must not leak.
# Match complete terms rather than incidental substrings such as 'villager'.
RESIDENT_META_TERMS = re.compile(
    r"(?<![a-z0-9])(?:game[\s_-]+master|simulations?|simulated|agents?|"
    r"llms?|mockllm|benchmarks?|engine|connected_v1|retrieval_backend)(?![a-z0-9])",
    re.IGNORECASE,
)


def has_meta_terms(prompt: str) -> bool:
    return RESIDENT_META_TERMS.search(prompt) is not None
