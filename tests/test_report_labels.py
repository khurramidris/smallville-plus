import json
from copy import deepcopy
from pathlib import Path

import pytest

from smallville.cli import write_report
from smallville.eval.reporting import label_report


@pytest.fixture
def legacy_report():
    # Exercise the archived schema as well as new runs. All these values are
    # synthetic formatter fixtures, including the litellm parameterization below.
    return {
        "backend": "mock",
        "interpretation": "Test report.",
        "run": {"phase": 3, "status": "completed", "completed_minutes": 1440},
        "agents": 25,
        "cost": {"usd": "0", "usd_per_agent_per_simulated_day": "0", "calls": 9, "cache_hits": 1},
        "paper_reference": {"party_attending_guests": 5},
        "diffusion": {
            "sam": {"initial": 1, "retained_final": 8, "paper_final": 8},
            "party": {"initial": 1, "retained_final": 11, "paper_final": 13},
        },
        "relationships": {"initial_density": 0.2, "final_density": 0.3},
        "party": {
            "invited_attending_guests": 0,
            "invited_guests": 4,
            "paper_attendance_rate": 5 / 12,
        },
    }


def test_fixture_labels_preserve_scores_without_paper_comparisons(legacy_report, tmp_path):
    original = deepcopy(legacy_report)
    labeled = label_report(legacy_report)
    assert legacy_report == original
    assert labeled["diffusion"]["sam"]["retained_final"] == 8
    assert labeled["relationships"] == original["relationships"]
    assert labeled["cost"] == original["cost"]
    assert labeled["evidence_label"] == "fixture only"
    assert "paper_reference" not in labeled
    assert "paper_final" not in labeled["diffusion"]["sam"]
    assert "paper_attendance_rate" not in labeled["party"]
    assert label_report(labeled) == labeled
    write_report(tmp_path, legacy_report)
    markdown = (tmp_path / "report.md").read_text()
    assert "| Measurement | fixture only |" in markdown
    assert "| Paper |" not in markdown and "| 8/25 | 8/25 |" not in markdown
    assert json.loads((tmp_path / "report.json").read_text()) == labeled


def test_live_report_is_exploratory_and_retains_reference(legacy_report, tmp_path):
    legacy_report["backend"] = "litellm"
    write_report(tmp_path, legacy_report)
    data = json.loads((tmp_path / "report.json").read_text())
    assert data["evidence_label"] == "real-model exploratory"
    assert data["paper_comparison_allowed"] is True
    assert data["paper_reference"] == legacy_report["paper_reference"]
    assert "| Paper |" in (tmp_path / "report.md").read_text()


def test_unknown_provenance_cannot_silently_create_paper_comparison(legacy_report, tmp_path):
    legacy_report.pop("backend")
    write_report(tmp_path, legacy_report)
    assert "| Paper |" not in (tmp_path / "report.md").read_text()
    assert json.loads((tmp_path / "report.json").read_text())["evidence_label"] == "unclassified"


def test_saved_mock_run_reports_carry_fixture_label():
    checked = 0
    for path in Path("reports").rglob("*.json"):
        data = json.loads(path.read_text())
        if isinstance(data, dict) and data.get("backend") == "mock":
            assert data["evidence_label"] == "fixture only", path
            assert "paper_reference" not in data, path
            assert data.get("paper_comparison_allowed") is False, path
            checked += 1
    assert checked > 0
