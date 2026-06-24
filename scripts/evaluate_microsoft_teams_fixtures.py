#!/usr/bin/env python3
"""Evaluate generated minutes against Microsoft Teams-style fixture minutes.

This is a lightweight semantic regression harness. It does not require exact
wording matches; it checks durable meeting-minutes behaviours such as topic
coverage, action counts, owners, dates/statuses, decisions, and Teams-style
structure.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_ROOT = ROOT / "fixtures" / "microsoft-teams-minutes"
DEFAULT_RUNNER_PATH = ROOT / "colab_experiment_runner.py"
DEFAULT_REPORT_ROOT = ROOT / "reports" / "microsoft-teams-fixtures"

TEAMS_HEADINGS = [
    "summary",
    "discussion points",
    "decisions",
    "action items",
    "follow-up",
]


def _load_runner(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("colab_experiment_runner_eval", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load runner from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _section(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.I | re.M)
    match = pattern.search(markdown)
    if not match:
        return ""
    rest = markdown[match.end() :]
    next_heading = re.search(r"^##\s+", rest, re.M)
    if next_heading:
        return rest[: next_heading.start()]
    return rest


def _parse_table(section: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-"} for cell in cells):
            continue
        if not headers:
            headers = [cell.lower() for cell in cells]
            continue
        row = {headers[index]: cell for index, cell in enumerate(cells) if index < len(headers)}
        rows.append(row)
    return rows


def _normalise_no_value(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered in {"", "none", "not specified", "owner not specified", "n/a"}


def _expected_actions(expected_minutes: str) -> list[dict[str, str]]:
    rows = _parse_table(_section(expected_minutes, "Action Items"))
    actions = []
    for row in rows:
        actions.append(
            {
                "action": row.get("action", ""),
                "owner": row.get("owner", ""),
                "due": row.get("due / status", row.get("deadline/status", "")),
            }
        )
    return actions


def _generated_actions(minutes: str) -> list[dict[str, str]]:
    rows = _parse_table(_section(minutes, "Actions") or _section(minutes, "Action Items"))
    actions = []
    for row in rows:
        actions.append(
            {
                "action": row.get("action", ""),
                "owner": row.get("owner", ""),
                "due": row.get("due / status", row.get("deadline/status", "")),
            }
        )
    return actions


def _decisions(minutes: str) -> list[str]:
    section = _section(minutes, "Decisions")
    decisions = []
    for line in section.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped.startswith("- "):
            continue
        if lowered.startswith(("- none", "- no decisions", "- no final")):
            continue
        decisions.append(stripped[2:].strip())
    return decisions


def _topic_hit(topic: str, generated: str) -> bool:
    lowered = generated.lower()
    topic_lower = topic.lower()
    if topic_lower in lowered:
        return True
    words = [word for word in re.findall(r"[a-z0-9]+", topic_lower) if len(word) > 2]
    return bool(words) and all(word in lowered for word in words)


def _all_values_present(expected_values: list[str], generated: str) -> bool:
    lowered = generated.lower()
    values = [value for value in expected_values if not _normalise_no_value(value)]
    if not values:
        return True
    return all(value.lower() in lowered for value in values)


def _heading_score(minutes: str) -> dict[str, Any]:
    lowered = minutes.lower()
    present = [heading for heading in TEAMS_HEADINGS if heading in lowered]
    return {
        "present": present,
        "missing": [heading for heading in TEAMS_HEADINGS if heading not in present],
        "score": len(present) / len(TEAMS_HEADINGS),
    }


def _score_case(case: dict[str, Any], expected_minutes: str, generated: str) -> dict[str, Any]:
    expected_action_rows = _expected_actions(expected_minutes)
    generated_action_rows = _generated_actions(generated)
    expected_decisions = _decisions(expected_minutes)
    generated_decisions = _decisions(generated)

    topic_hits = [topic for topic in case.get("expectedTopics", []) if _topic_hit(topic, generated)]
    expected_topics = case.get("expectedTopics", [])
    topic_score = 1.0 if not expected_topics else len(topic_hits) / len(expected_topics)

    expected_action_count = case.get("expectedActionCount", len(expected_action_rows))
    generated_action_count = len(generated_action_rows)
    action_count_delta = abs(expected_action_count - generated_action_count)
    if action_count_delta == 0:
        action_count_score = 1.0
    elif action_count_delta == 1:
        action_count_score = 0.5
    else:
        action_count_score = 0.0

    expected_owners = [row["owner"] for row in expected_action_rows]
    expected_dues = [row["due"] for row in expected_action_rows]
    owner_score = 1.0 if _all_values_present(expected_owners, generated) else 0.0
    due_score = 1.0 if _all_values_present(expected_dues, generated) else 0.0

    expected_decision_count = case.get("expectedDecisionCount", len(expected_decisions))
    generated_decision_count = len(generated_decisions)
    decision_score = 1.0 if expected_decision_count == generated_decision_count else 0.0

    no_false_action_score = 1.0
    if expected_action_count == 0 and generated_action_count > 0:
        no_false_action_score = 0.0

    headings = _heading_score(generated)

    weights = {
        "topics": 2.0,
        "action_count": 2.0,
        "owners": 1.0,
        "due_status": 1.0,
        "decisions": 1.0,
        "no_false_actions": 1.0,
        "teams_structure": 1.0,
    }
    scores = {
        "topics": topic_score,
        "action_count": action_count_score,
        "owners": owner_score,
        "due_status": due_score,
        "decisions": decision_score,
        "no_false_actions": no_false_action_score,
        "teams_structure": headings["score"],
    }
    weighted_total = sum(scores[name] * weight for name, weight in weights.items())
    max_total = sum(weights.values())
    overall = weighted_total / max_total

    passes = (
        overall >= 0.75
        and action_count_score >= 0.5
        and decision_score == 1.0
        and headings["score"] >= 0.8
    )

    return {
        "id": case["id"],
        "meetingType": case["meetingType"],
        "overallScore": round(overall, 3),
        "pass": passes,
        "scores": {name: round(score, 3) for name, score in scores.items()},
        "expected": {
            "topics": expected_topics,
            "topicHits": topic_hits,
            "actionCount": expected_action_count,
            "decisionCount": expected_decision_count,
            "owners": expected_owners,
            "dueStatus": expected_dues,
        },
        "generated": {
            "actionCount": generated_action_count,
            "decisionCount": generated_decision_count,
            "teamsHeadingsPresent": headings["present"],
            "teamsHeadingsMissing": headings["missing"],
        },
        "notes": _case_notes(
            expected_topics,
            topic_hits,
            expected_action_count,
            generated_action_count,
            expected_decision_count,
            generated_decision_count,
            headings["missing"],
        ),
    }


def _case_notes(
    expected_topics: list[str],
    topic_hits: list[str],
    expected_action_count: int,
    generated_action_count: int,
    expected_decision_count: int,
    generated_decision_count: int,
    missing_headings: list[str],
) -> list[str]:
    notes: list[str] = []
    missed_topics = [topic for topic in expected_topics if topic not in topic_hits]
    if missed_topics:
        notes.append("Missed topics: " + ", ".join(missed_topics))
    if expected_action_count != generated_action_count:
        notes.append(f"Action count expected {expected_action_count}, generated {generated_action_count}")
    if expected_decision_count != generated_decision_count:
        notes.append(f"Decision count expected {expected_decision_count}, generated {generated_decision_count}")
    if missing_headings:
        notes.append("Missing Teams headings: " + ", ".join(missing_headings))
    if not notes:
        notes.append("Core checks passed.")
    return notes


def _markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Microsoft Teams Fixture Evaluation",
        "",
        f"- Generated at: {report['generatedAt']}",
        f"- Runner: `{report['runnerLabel']}`",
        f"- Runner path: `{report['runnerPath']}`",
        f"- Fixture root: `{report['fixtureRoot']}`",
        f"- Cases: {report['summary']['caseCount']}",
        f"- Passed: {report['summary']['passed']} / {report['summary']['caseCount']}",
        f"- Average score: {report['summary']['averageScore']:.3f}",
        "",
        "## Case Results",
        "",
        "| Case | Type | Score | Pass | Key notes |",
        "|---|---|---:|:---:|---|",
    ]
    for case in report["cases"]:
        notes = "<br>".join(case["notes"])
        passed = "yes" if case["pass"] else "no"
        lines.append(
            f"| `{case['id']}` | {case['meetingType']} | {case['overallScore']:.3f} | {passed} | {notes} |"
        )
    lines.extend(
        [
            "",
            "## Score Categories",
            "",
            "- `topics`: expected topic phrases or their important words appear in generated minutes.",
            "- `action_count`: generated action row count matches, or is within one for partial credit.",
            "- `owners`: expected action owners appear in generated minutes.",
            "- `due_status`: expected due/status values appear in generated minutes.",
            "- `decisions`: generated decision count matches expected decision count.",
            "- `no_false_actions`: no action rows are produced for action-free fixtures.",
            "- `teams_structure`: generated output contains Teams-style sections.",
            "",
            "This is a regression signal, not a full human-quality judgement.",
        ]
    )
    return "\n".join(lines) + "\n"


def evaluate(
    fixture_root: Path,
    runner_path: Path,
    report_root: Path,
    report_name: str,
    runner_label: str | None = None,
) -> dict[str, Any]:
    manifest = json.loads((fixture_root / "manifest.json").read_text())
    runner = _load_runner(runner_path)
    cases = []

    for case in manifest["cases"]:
        case_root = fixture_root / case["id"]
        transcript = (case_root / "transcript.txt").read_text()
        expected_minutes = (case_root / "expected_minutes.md").read_text()
        generated_result = runner.generate_polished_minutes_pass(transcript_text=transcript)
        generated_minutes = generated_result["minutes"]
        scored = _score_case(case, expected_minutes, generated_minutes)
        scored["generatedMinutes"] = generated_minutes
        scored["runnerEvaluation"] = generated_result.get("evaluation", {})
        cases.append(scored)

    passed = sum(1 for case in cases if case["pass"])
    average = sum(case["overallScore"] for case in cases) / len(cases) if cases else 0.0
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "runnerPath": str(runner_path),
        "runnerLabel": runner_label or str(runner_path),
        "fixtureRoot": str(fixture_root),
        "summary": {
            "caseCount": len(cases),
            "passed": passed,
            "failed": len(cases) - passed,
            "averageScore": round(average, 3),
        },
        "cases": cases,
    }

    report_root.mkdir(parents=True, exist_ok=True)
    json_path = report_root / f"{report_name}.json"
    md_path = report_root / f"{report_name}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n")
    md_path.write_text(_markdown_report(report))
    report["reportPaths"] = {"json": str(json_path), "markdown": str(md_path)}
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURE_ROOT)
    parser.add_argument("--runner-path", type=Path, default=DEFAULT_RUNNER_PATH)
    parser.add_argument("--runner-label")
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--report-name", default="baseline_2026-06-24")
    args = parser.parse_args()

    report = evaluate(
        args.fixture_root,
        args.runner_path,
        args.report_root,
        args.report_name,
        args.runner_label,
    )
    print(json.dumps({"summary": report["summary"], "reportPaths": report["reportPaths"]}, indent=2))


if __name__ == "__main__":
    main()
