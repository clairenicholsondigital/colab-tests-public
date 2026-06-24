#!/usr/bin/env python3
"""Evaluate the Colab runner against local human-written minutes pairs.

The four transcript/minutes pairs are real client material, so this script keeps
the source texts outside the public repository. It reads the local extracted
texts, writes detailed generated minutes to the local output folder, and emits
only score summaries in the report.
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
WORKSPACE = ROOT.parent
DEFAULT_RUNNER = ROOT / "colab_experiment_runner.py"
DEFAULT_SOURCE_ROOT = (
    WORKSPACE / "outputs" / "minutes_pairings_zip_2026-06-24" / "extracted_text"
)
DEFAULT_OUTPUT_ROOT = (
    WORKSPACE / "outputs" / "minutes_pairings_zip_2026-06-24" / "latest_human_minutes_gate_2026-06-24"
)

CASES = [
    {
        "id": "dita_client",
        "label": "DITA T819 Importer Obligations - Client Connect",
        "transcript": "Client DITA T819 - Importer Obligations - Client connect.txt",
        "human": "T819 Dita Eyewear Importer Obligations -Trinzo Minutes Client Connect_2026.06.17.txt",
    },
    {
        "id": "dita_internal",
        "label": "DITA T819 Importer Obligations - Internal Follow-up",
        "transcript": "Internal DITA T819 - followup and review from client call.txt",
        "human": "T819 Dita Eyewear Importer Obligations -Trinzo Minutes internal Connect_2026.06.17.txt",
    },
    {
        "id": "eakin_t733",
        "label": "Eakin T733/T817 Consultancy Retainer - Client Check-in",
        "transcript": "Client Eakin T733 Consultancy Retainer -Tech File review weekly.txt",
        "human": "T733 Eakin Consultancy Retainer -Trinzo Minutes Client -Checkin TF24 _2026.06.17.txt",
    },
    {
        "id": "eakin_t761",
        "label": "Eakin T761 Tech File Software - Weekly Check-in",
        "transcript": "Client T761 Eakin Tech File SW - Weekly checkin.txt",
        "human": "T761 Eakin Tech File SW -Trinzo Minutes SW Weekly Checkin_2026.06.15.txt",
    },
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalise(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^\w\s/.-]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", normalise(value))
        if len(token) > 2 and token not in STOPWORDS
    }


def word_count(value: str) -> int:
    return len(re.findall(r"\b\w+\b", value))


def section(markdown: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.I | re.M)
    match = pattern.search(markdown)
    if not match:
        return ""
    rest = markdown[match.end() :]
    next_heading = re.search(r"^##\s+", rest, re.M)
    return rest[: next_heading.start()] if next_heading else rest


def bullets(section_text: str) -> list[str]:
    values: list[str] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and not stripped.lower().startswith(("- none", "- no ")):
            values.append(stripped.strip(" -"))
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
            headers = [normalise(cell) for cell in cells]
            continue
        rows.append({headers[index]: cell for index, cell in enumerate(cells) if index < len(headers)})
    return rows


def generated_actions(markdown: str) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for row in table_rows(section(markdown, "Action Items")):
        action = row.get("action", "")
        if not action:
            continue
        actions.append(
            {
                "action": action,
                "owner": row.get("owner", ""),
                "due": row.get("due / status", "")
                or row.get("deadline / status", "")
                or row.get("deadline", ""),
            }
        )
    return actions


def human_minutes_body(text: str) -> str:
    match = re.search(r"\bMeeting Minutes\b", text, re.I)
    if not match:
        return text
    rest = text[match.end() :]
    next_steps = re.search(r"\bNext steps\b", rest, re.I)
    return rest[: next_steps.start()] if next_steps else rest


def human_next_steps(text: str) -> str:
    match = re.search(r"\bNext steps\b", text, re.I)
    return text[match.end() :] if match else ""


def looks_like_heading(line: str) -> bool:
    clean = re.sub(r"\s+", " ", line.strip())
    if not clean or clean.startswith(("•", "o ")):
        return False
    if len(clean) > 70 or len(clean.split()) > 9:
        return False
    if re.search(r"[.!?]$", clean):
        return False
    letters = re.sub(r"[^A-Za-z]", "", clean)
    return bool(letters) and (sum(1 for char in letters if char.isupper()) / len(letters)) > 0.18


def extract_human_topics(text: str) -> list[str]:
    topics: list[str] = []
    pending: str | None = None
    for raw_line in human_minutes_body(text).splitlines():
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line:
            continue
        if looks_like_heading(line):
            if pending:
                topics.append(pending)
            pending = line
            continue
        match = re.match(r"^([A-Z][A-Za-z0-9/&' -]{2,45}?)(?=\s+[A-Z][a-z]+\b)", line)
        if match:
            heading = match.group(1).strip()
            if 1 <= len(heading.split()) <= 6:
                if pending:
                    topics.append(pending)
                    pending = None
                topics.append(heading)
    if pending:
        topics.append(pending)

    deduped: list[str] = []
    seen: set[str] = set()
    for topic in topics:
        key = normalise(topic)
        if key and key not in seen:
            seen.add(key)
            deduped.append(topic)
    return deduped


def extract_human_actions(text: str) -> list[str]:
    steps = human_next_steps(text)
    if not steps:
        return []
    compact = re.sub(r"\s+", " ", steps)
    compact = re.sub(r"\bActions?\s+Owner\s+Deadline\b", " ", compact, flags=re.I)
    date_or_status = r"(?:\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+(?:\s+[‘']?\d{2,4})?|Done|TBC|TBD)"
    pattern = re.compile(
        rf"(.+?\b(?:to|review|share|complete|update|schedule|followup|follow up|trace|generate|outline)\b.+?)\s+"
        rf"([A-Z][A-Za-z'/-]+(?:/[A-Z][A-Za-z'/-]+)?)\s+({date_or_status})",
        re.I,
    )
    actions: list[str] = []
    for match in pattern.finditer(compact):
        action = re.sub(r"\s+", " ", match.group(1)).strip(" -")
        if 8 <= len(action) <= 220:
            actions.append(action)
    if actions:
        return actions
    return [
        line.strip()
        for line in steps.splitlines()
        if re.search(r"\b(to|review|share|complete|update|schedule|follow)\b", line, re.I)
    ]


def coverage_score(expected: list[str], actual_text: str, min_overlap: float = 0.45) -> tuple[float, list[str]]:
    if not expected:
        return 1.0, []
    actual_tokens = tokens(actual_text)
    missed: list[str] = []
    for item in expected:
        item_tokens = tokens(item)
        if not item_tokens:
            continue
        overlap = len(item_tokens & actual_tokens) / len(item_tokens)
        if overlap < min_overlap:
            missed.append(item)
    score = 1.0 - (len(missed) / len(expected))
    return max(0.0, score), missed


def action_match_score(expected_actions: list[str], actual_actions: list[dict[str, str]]) -> tuple[float, list[str]]:
    if not expected_actions:
        return 1.0, []
    actual_texts = [
        " ".join([row.get("action", ""), row.get("owner", ""), row.get("due", "")])
        for row in actual_actions
    ]
    missed: list[str] = []
    for expected in expected_actions:
        expected_tokens = tokens(expected)
        best = 0.0
        for actual in actual_texts:
            actual_tokens = tokens(actual)
            if expected_tokens:
                best = max(best, len(expected_tokens & actual_tokens) / len(expected_tokens))
        if best < 0.42:
            missed.append(expected)
    return 1.0 - (len(missed) / len(expected_actions)), missed


def length_score(human_text: str, generated: str) -> float:
    human_words = max(1, word_count(human_text))
    generated_words = word_count(generated)
    ratio = generated_words / human_words
    if 0.65 <= ratio <= 1.75:
        return 1.0
    if ratio < 0.65:
        return max(0.0, ratio / 0.65)
    return max(0.0, 1.0 - ((ratio - 1.75) / 1.75))


def evaluate_case(case: dict[str, str], human_text: str, generated: str) -> dict[str, Any]:
    topics = extract_human_topics(human_text)
    actions = extract_human_actions(human_text)
    actual_actions = generated_actions(generated)
    topic_score, missed_topics = coverage_score(topics, generated)
    action_score, missed_actions = action_match_score(actions, actual_actions)
    compression = length_score(human_text, generated)
    count_score = 1.0
    if actions:
        count_score = max(0.0, 1.0 - abs(len(actual_actions) - len(actions)) / max(len(actions), 1))
    score = (topic_score * 0.35) + (action_score * 0.35) + (count_score * 0.15) + (compression * 0.15)
    return {
        "case": case["id"],
        "label": case["label"],
        "score": round(score, 4),
        "passed": score >= 0.85,
        "categoryScores": {
            "topicCoverage": round(topic_score, 4),
            "actionCoverage": round(action_score, 4),
            "actionCount": round(count_score, 4),
            "lengthDiscipline": round(compression, 4),
        },
        "counts": {
            "humanTopics": len(topics),
            "humanActions": len(actions),
            "generatedActions": len(actual_actions),
            "humanWords": word_count(human_text),
            "generatedWords": word_count(generated),
        },
        "missedTopics": missed_topics[:8],
        "missedActions": missed_actions[:8],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Human Minutes Pair Gate",
        "",
        "This report is intentionally sanitised: it does not quote the client transcripts or human minutes.",
        "",
        f"- Runner: `{summary['runner']}`",
        f"- Source root: `{summary['sourceRoot']}`",
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
    lines.extend(["", "## Cases", ""])
    for case in report["cases"]:
        status = "PASS" if case["passed"] else "FAIL"
        lines.append(f"### {case['label']} - {status} - {case['score']:.3f}")
        lines.append(
            "- Counts: "
            f"human topics={case['counts']['humanTopics']}, "
            f"human actions={case['counts']['humanActions']}, "
            f"generated actions={case['counts']['generatedActions']}, "
            f"words human/generated={case['counts']['humanWords']}/{case['counts']['generatedWords']}"
        )
        lines.append(f"- Category scores: {case['categoryScores']}")
        if case["missedTopics"]:
            lines.append(f"- Missed topic anchors: {len(case['missedTopics'])}")
        if case["missedActions"]:
            lines.append(f"- Missed action anchors: {len(case['missedActions'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", default=str(DEFAULT_RUNNER))
    parser.add_argument("--source-root", default=str(DEFAULT_SOURCE_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--report-name", default="human_minutes_gate_2026-06-24")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runner_path = Path(args.runner)
    source_root = Path(args.source_root)
    output_root = Path(args.output_root)
    generated_root = output_root / "generated_minutes"
    report_root = output_root / "reports"
    generated_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)

    runner = load_module(runner_path, "colab_runner_for_human_minutes_pairs")
    case_reports: list[dict[str, Any]] = []
    for case in CASES:
        transcript = (source_root / case["transcript"]).read_text(encoding="utf-8")
        human = (source_root / case["human"]).read_text(encoding="utf-8")
        result = runner.generate_polished_minutes_pass(transcript_text=transcript)
        generated = result["minutes"]
        (generated_root / f"{case['id']}.md").write_text(generated, encoding="utf-8")
        case_reports.append(evaluate_case(case, human, generated))

    passed = sum(1 for case in case_reports if case["passed"])
    category_totals: dict[str, list[float]] = {}
    for case in case_reports:
        for category, score in case["categoryScores"].items():
            category_totals.setdefault(category, []).append(float(score))
    report = {
        "summary": {
            "runner": str(runner_path),
            "sourceRoot": str(source_root),
            "outputRoot": str(output_root),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "caseCount": len(case_reports),
            "passed": passed,
            "failed": len(case_reports) - passed,
            "averageScore": round(sum(case["score"] for case in case_reports) / len(case_reports), 4),
            "categoryAverages": {
                category: round(sum(scores) / len(scores), 4)
                for category, scores in sorted(category_totals.items())
            },
        },
        "cases": case_reports,
    }
    json_path = report_root / f"{args.report_name}.json"
    md_path = report_root / f"{args.report_name}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "summary": report["summary"],
                "reports": {"json": str(json_path), "markdown": str(md_path)},
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
