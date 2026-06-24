#!/usr/bin/env python3
"""Compare the Colab minutes runner with trinzo-upload's final golden suite."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNNER = ROOT / "colab_experiment_runner.py"
DEFAULT_GOLDEN_EVAL = ROOT.parent / "trinzo-upload" / "scripts" / "run_meeting_minutes_final_golden_eval.py"
DEFAULT_PACK = ROOT.parent / "trinzo-upload" / "scripts" / "meeting-minutes-final-golden"
DEFAULT_REPORT_ROOT = ROOT / "reports" / "meeting-minutes-final-golden"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def section(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.I | re.M)
    match = pattern.search(markdown)
    if not match:
        return ""
    rest = markdown[match.end() :]
    next_heading = re.search(r"^##\s+", rest, re.M)
    return rest[: next_heading.start()] if next_heading else rest


def clean_line(value: str) -> str:
    value = re.sub(r"_\(Sources?:.*?\)_", "", value)
    return value.strip(" -")


def bullets(section_text: str) -> list[str]:
    values: list[str] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped.startswith("- "):
            continue
        if lowered.startswith(("- none", "- no decisions", "- no action", "- no substantive")):
            continue
        values.append(clean_line(stripped))
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


def parse_colab_minutes(markdown: str) -> dict[str, Any]:
    summary = bullets(section(markdown, "Summary"))
    discussion = bullets(section(markdown, "Discussion Points"))
    follow_up = bullets(section(markdown, "Follow-up / Open Questions"))
    decisions = bullets(section(markdown, "Decisions"))
    rows = table_rows(section(markdown, "Action Items"))
    actions = [
        {
            "meetingActionPoint": row.get("action", ""),
            "meetingActionPointOwner": row.get("owner", ""),
            "meetingActionPointDeadline": row.get("deadline / status", "") or row.get("deadline", ""),
        }
        for row in rows
        if row.get("action")
    ]
    return {
        "meetingTitle": "",
        "participants": [],
        "executiveSummary": " ".join(summary),
        "meetingObjectives": [],
        "discussionPoints": discussion + follow_up,
        "decisions": decisions,
        "actions": actions,
    }


def find_cases(pack_dir: Path) -> list[Path]:
    return [
        folder
        for folder in sorted(pack_dir.iterdir())
        if folder.is_dir() and (folder / "transcript.txt").exists() and (folder / "expected.json").exists()
    ]


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Meeting Minutes Final Golden Comparison",
        "",
        f"- Runner: `{summary['runner']}`",
        f"- Golden pack: `{summary['packDir']}`",
        f"- Generated: `{summary['generatedAt']}`",
        f"- Cases: {summary['caseCount']}",
        f"- Passed: {summary['passed']} / {summary['caseCount']}",
        f"- Average score: {summary['averageScore']:.3f}",
        "",
        "## Category Averages",
        "",
    ]
    for category, score in summary["categoryAverages"].items():
        lines.append(f"- {category}: {score:.3f}")
    lines.extend(["", "## Failure Themes", ""])
    for label, count in summary["failureThemes"]:
        lines.append(f"- {count}: {label}")
    lines.extend(["", "## Cases", ""])
    for case in report["cases"]:
        status = "PASS" if case["passed"] else "FAIL"
        lines.append(
            f"### {case['case']} - {status} - score {case['score']:.3f} "
            f"(threshold {case['passThreshold']:.2f})"
        )
        counts = case.get("counts", {})
        lines.append(
            f"- Counts: decisions={counts.get('decisions', 0)}, "
            f"actions={counts.get('actions', 0)}, discussion={counts.get('discussionPoints', 0)}"
        )
        if case["failures"]:
            for failure in case["failures"][:10]:
                lines.append(f"- {failure}")
        else:
            lines.append("- No failures.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def theme_for_failure(failure: str) -> str:
    if failure.startswith("decisions:"):
        return "decision capture/count"
    if failure.startswith("actions:"):
        return "action capture/count"
    if failure.startswith("abstention:"):
        return "abstention/count discipline"
    if failure.startswith("hallucinations:"):
        return "forbidden/hallucinated content"
    if failure.startswith("quality:"):
        return failure.split(":", 2)[1].strip()
    return failure.split(":", 1)[0]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", default=str(DEFAULT_RUNNER))
    parser.add_argument("--golden-eval", default=str(DEFAULT_GOLDEN_EVAL))
    parser.add_argument("--pack-dir", default=str(DEFAULT_PACK))
    parser.add_argument("--report-root", default=str(DEFAULT_REPORT_ROOT))
    parser.add_argument("--report-name", default="colab_runner_2026-06-24")
    parser.add_argument("--cases", nargs="+")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runner_path = Path(args.runner)
    pack_dir = Path(args.pack_dir)
    report_root = Path(args.report_root)
    runner = load_module(runner_path, "colab_runner_for_final_golden_eval")
    golden_eval = load_module(Path(args.golden_eval), "meeting_minutes_final_golden_eval")

    cases = find_cases(pack_dir)
    if args.cases:
        wanted = set(args.cases)
        cases = [case for case in cases if case.name in wanted]
    if not cases:
        raise SystemExit("No golden cases found")

    case_reports: list[dict[str, Any]] = []
    for case in cases:
        transcript = (case / "transcript.txt").read_text(encoding="utf-8")
        expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
        result = runner.generate_polished_minutes_pass(transcript_text=transcript)
        output = parse_colab_minutes(result["minutes"])
        evaluation = golden_eval.evaluate_case(case.name, output, expected)
        case_reports.append(evaluation)

    passed = sum(1 for case in case_reports if case["passed"])
    average = sum(float(case["score"]) for case in case_reports) / len(case_reports)
    category_totals: dict[str, list[float]] = {}
    failure_themes: dict[str, int] = {}
    for case in case_reports:
        for category, score in case.get("categoryScores", {}).items():
            category_totals.setdefault(category, []).append(float(score))
        for failure in case.get("failures", []):
            theme = theme_for_failure(str(failure))
            failure_themes[theme] = failure_themes.get(theme, 0) + 1

    report = {
        "summary": {
            "runner": str(runner_path),
            "packDir": str(pack_dir),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "caseCount": len(case_reports),
            "passed": passed,
            "failed": len(case_reports) - passed,
            "averageScore": round(average, 4),
            "categoryAverages": {
                category: round(sum(scores) / len(scores), 4)
                for category, scores in sorted(category_totals.items())
            },
            "failureThemes": sorted(failure_themes.items(), key=lambda item: (-item[1], item[0])),
        },
        "cases": case_reports,
    }

    report_root.mkdir(parents=True, exist_ok=True)
    json_path = report_root / f"{args.report_name}.json"
    md_path = report_root / f"{args.report_name}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": {
                    key: value
                    for key, value in report["summary"].items()
                    if key in {"caseCount", "passed", "failed", "averageScore", "categoryAverages"}
                },
                "reports": {"json": str(json_path), "markdown": str(md_path)},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
