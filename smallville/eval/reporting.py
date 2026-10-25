"""Evidence labels and presentation policy; no behavior or scoring rules."""

from copy import deepcopy

FIXTURE_LABEL = "fixture only"
FIXTURE_SCOPE = (
    "All mock-derived behavior, survey predictions, requests, tokens, costs, timing "
    "and storage in this report are fixture only. Source/human reference values and "
    "test counts are not model-validation results. Scripted campaign/party behavior "
    "cannot support a comparison with Park et al."
)


def evidence_labels(backend: str) -> dict:
    if backend == "mock":
        return {"evidence_label": FIXTURE_LABEL, "evidence_scope": FIXTURE_SCOPE}
    return {
        "evidence_label": "real-model exploratory" if backend == "litellm" else "unclassified",
        "evidence_scope": "Model provenance alone does not establish matched or paid validation.",
    }


def label_report(report: dict, backend: str | None = None) -> dict:
    """Also handle saved legacy mock reports without mutating their measurements."""
    result = deepcopy(report)
    backend = backend or result.get("backend", "unknown")
    result.update(evidence_labels(backend))
    result["paper_comparison_allowed"] = backend == "litellm"
    if backend == "mock":
        result.pop("paper_reference", None)
        for topic in result.get("diffusion", {}).values():
            if isinstance(topic, dict):
                topic.pop("paper_final", None)
        result.get("party", {}).pop("paper_attendance_rate", None)
        if "interpretation" in result:
            result["interpretation"] = "Fixture only: " + result["interpretation"].removeprefix(
                "Fixture only: "
            )
    return result
