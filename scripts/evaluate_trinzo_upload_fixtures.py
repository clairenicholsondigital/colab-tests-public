#!/usr/bin/env python3
"""Run the Colab minutes runner against trinzo-upload transcript fixtures.

The trinzo-upload fixtures were written for a fuller JSON extractor. This
script uses their content assertions only: discussion coverage, action counts,
decision counts, required actions/decisions/topics, and forbidden noisy text.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNNER = ROOT / "colab_experiment_runner.py"
DEFAULT_FIXTURES = ROOT.parent / "trinzo-upload" / "scripts" / "transcript-tests"
DEFAULT_REPORT_ROOT = ROOT / "reports" / "trinzo-upload-fixtures"


def normalise(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def words(value: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "into", "onto",
        "will", "should", "would", "could", "need", "needs", "about", "before",
        "after", "their", "there", "then", "than", "have", "has", "were", "was",
    }
    return {word for word in re.findall(r"[a-z0-9]+", normalise(value)) if len(word) > 2 and word not in stop}


def fuzzy_contains(actual_values: list[str], expected: str) -> bool:
    expected_norm = normalise(expected)
    if not expected_norm:
        return True
    expected_words = words(expected)
    for actual in actual_values:
        actual_norm = normalise(actual)
        if expected_norm in actual_norm or actual_norm in expected_norm:
            return True
        actual_words = words(actual)
        if expected_words and len(expected_words & actual_words) / len(expected_words) >= 0.65:
            return True
        if SequenceMatcher(None, expected_norm, actual_norm).ratio() >= 0.72:
            return True
    return False


def contains_all_concepts(actual_values: list[str], concepts: Any) -> bool:
    if isinstance(concepts, str):
        concepts = [concepts]
    return all(fuzzy_contains(actual_values, concept) for concept in concepts)


def section(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.I | re.M)
    match = pattern.search(markdown)
    if not match:
        return ""
    rest = markdown[match.end():]
    next_heading = re.search(r"^##\s+", rest, re.M)
    return rest[: next_heading.start()] if next_heading else rest


def clean_bullet(text: str) -> str:
    text = re.sub(r"_\(Sources?:.*?\)_", "", text)
    return text.strip(" -")


def bullets(section_text: str) -> list[str]:
    values = []
    for line in section_text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped.startswith("- "):
            continue
        if lowered.startswith(("- none", "- no decisions", "- no action", "- no substantive")):
            continue
        values.append(clean_bullet(stripped))
    return values


def table_rows(section_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-"} for cell in cells):
            continue
        if not headers:
            headers = [cell.lower() for cell in cells]
            continue
        rows.append({headers[index]: cell for index, cell in enumerate(cells) if index < len(headers)})
    return rows


def generated_content(minutes: str) -> dict[str, Any]:
    summary = bullets(section(minutes, "Summary"))
    discussion = bullets(section(minutes, "Discussion Points"))
    decisions = bullets(section(minutes, "Decisions"))
    action_rows = table_rows(section(minutes, "Action Items"))
    actions = [row.get("action", "") for row in action_rows if row.get("action")]
    follow_up = bullets(section(minutes, "Follow-up / Open Questions"))
    return {
        "summary": summary,
        "discussionPoints": discussion + follow_up,
        "decisions": decisions,
        "actions": actions,
        "actionRows": action_rows,
        "combined": summary + discussion + follow_up + decisions + actions,
    }


def load_runner(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("colab_runner_for_trinzo_eval", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load runner from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalise_expected(payload: dict[str, Any]) -> dict[str, Any]:
    if "assertions" in payload and isinstance(payload["assertions"], dict):
        payload = payload["assertions"]
    expected = dict(payload)
    aliases = {
        "discussionPoints": "mustContainDiscussionPoints",
        "decisions": "mustContainDecisions",
        "meetingActionPoint": "mustContainActions",
    }
    for old, new in aliases.items():
        if old in expected and new not in expected:
            expected[new] = expected[old]
    return expected


def expected_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("text") or value.get("meetingActionPoint") or "")
    return str(value)


def check_case(folder: Path, runner: Any) -> dict[str, Any]:
    transcript = (folder / "transcript.txt").read_text()
    expected = normalise_expected(json.loads((folder / "expected.json").read_text()))
    result = runner.generate_polished_minutes_pass(transcript_text=transcript)
    content = generated_content(result["minutes"])
    failures: list[str] = []

    if "expectedActionCount" in expected and len(content["actions"]) != expected["expectedActionCount"]:
        failures.append(f"expected {expected['expectedActionCount']} actions, got {len(content['actions'])}")
    if "expectedActionCountMin" in expected and len(content["actions"]) < expected["expectedActionCountMin"]:
        failures.append(f"expected at least {expected['expectedActionCountMin']} actions, got {len(content['actions'])}")
    if "expectedDecisionCount" in expected and len(content["decisions"]) != expected["expectedDecisionCount"]:
        failures.append(f"expected {expected['expectedDecisionCount']} decisions, got {len(content['decisions'])}")
    if "expectedDecisionCountMin" in expected and len(content["decisions"]) < expected["expectedDecisionCountMin"]:
        failures.append(f"expected at least {expected['expectedDecisionCountMin']} decisions, got {len(content['decisions'])}")
    if "expectedDiscussionCountMin" in expected and len(content["discussionPoints"]) < expected["expectedDiscussionCountMin"]:
        failures.append(
            f"expected at least {expected['expectedDiscussionCountMin']} discussion points, got {len(content['discussionPoints'])}"
        )

    discussion_and_summary = content["discussionPoints"] + content["summary"]
    for concepts in expected.get("mustContainDiscussionTopics", []):
        if not contains_all_concepts(discussion_and_summary, concepts):
            failures.append(f"missing discussion topic concepts {concepts!r}")
    for item in expected.get("mustContainDiscussionPoints", []):
        text = expected_text(item)
        if not fuzzy_contains(content["discussionPoints"], text):
            failures.append(f"missing discussion point {text!r}")
    for item in expected.get("mustContainActions", []):
        text = expected_text(item)
        if not fuzzy_contains(content["actions"], text):
            failures.append(f"missing action {text!r}")
    for item in expected.get("mustContainDecisions", []):
        text = expected_text(item)
        if not fuzzy_contains(content["decisions"], text):
            failures.append(f"missing decision {text!r}")

    for forbidden in expected.get("mustNotContain", []):
        if fuzzy_contains(content["combined"], str(forbidden)):
            failures.append(f"forbidden content present {forbidden!r}")
    for forbidden in expected.get("mustNotContainDiscussionPoints", []):
        if fuzzy_contains(content["discussionPoints"], str(forbidden)):
            failures.append(f"forbidden discussion present {forbidden!r}")
    for forbidden in expected.get("mustNotContainActions", []):
        if fuzzy_contains(content["actions"], str(forbidden)):
            failures.append(f"forbidden action present {forbidden!r}")
    for forbidden in expected.get("mustNotContainDecisions", []):
        if fuzzy_contains(content["decisions"], str(forbidden)):
            failures.append(f"forbidden decision present {forbidden!r}")

    return {
        "id": folder.name,
        "pass": not failures,
        "failureCount": len(failures),
        "failures": failures[:12],
        "counts": {
            "actions": len(content["actions"]),
            "decisions": len(content["decisions"]),
            "discussionPoints": len(content["discussionPoints"]),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Trinzo Upload Fixture Transfer Evaluation",
        "",
        f"- Generated at: {report['generatedAt']}",
        f"- Runner: `{report['runnerPath']}`",
        f"- Fixture root: `{report['fixtureRoot']}`",
        f"- Cases: {report['summary']['caseCount']}",
        f"- Passed: {report['summary']['passed']} / {report['summary']['caseCount']}",
        f"- Total failures: {report['summary']['failureCount']}",
        "",
        "## Failures",
        "",
        "| Case | Counts | Failure count | First failures |",
        "|---|---|---:|---|",
    ]
    for case in report["cases"]:
        if case["pass"]:
            continue
        counts = ", ".join(f"{key}={value}" for key, value in case["counts"].items())
        failures = "<br>".join(case["failures"][:4])
        lines.append(f"| `{case['id']}` | {counts} | {case['failureCount']} | {failures} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-path", type=Path, default=DEFAULT_RUNNER)
    parser.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--report-name", default="generalisation_pass_2026-06-24")
    args = parser.parse_args()

    runner = load_runner(args.runner_path)
    folders = [
        folder for folder in sorted(args.fixture_root.iterdir())
        if folder.is_dir() and (folder / "transcript.txt").exists() and (folder / "expected.json").exists()
    ]
    cases = [check_case(folder, runner) for folder in folders]
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "runnerPath": str(args.runner_path),
        "fixtureRoot": str(args.fixture_root),
        "summary": {
            "caseCount": len(cases),
            "passed": sum(1 for case in cases if case["pass"]),
            "failed": sum(1 for case in cases if not case["pass"]),
            "failureCount": sum(case["failureCount"] for case in cases),
        },
        "cases": cases,
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    json_path = args.report_root / f"{args.report_name}.json"
    md_path = args.report_root / f"{args.report_name}.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n")
    md_path.write_text(render_markdown(report))
    print(json.dumps({"summary": report["summary"], "reports": {"json": str(json_path), "markdown": str(md_path)}}, indent=2))


if __name__ == "__main__":
    main()
