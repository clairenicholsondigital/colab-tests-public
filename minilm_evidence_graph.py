#!/usr/bin/env python3
"""MiniLM meeting evidence graph extractor.

This is a Colab-friendly script for turning a meeting transcript into a
structured evidence graph that can later be rewritten into polished minutes.

The important classifier changes in this version are:
- responsibility statements always beat action wording
- open questions are separated from risks
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


OPEN_QUESTION_WORDS = [
    "what if",
    "what happens",
    "can i ask",
    "do we know",
    "have we",
    "are we",
    "when will",
    "what's the consequence",
    "what is the consequence",
    "what is the status",
    "what's the status",
]

RESPONSIBILITY_WORDS = [
    "responsibility",
    "responsible",
    "obligation",
    "obliged",
    "must",
    "have to",
    "has to",
    "need to",
    "needs to",
    "required to",
    "supposed to",
    "should",
    "shall",
    "ensure",
    "verify",
    "check",
]

ACTION_WORDS = [
    "follow up",
    "send",
    "share",
    "provide",
    "obtain",
    "request",
    "review",
    "update",
    "confirm",
    "prepare",
    "collect",
    "schedule",
    "book",
    "create",
    "draft",
    "upload",
    "submit",
]

EVIDENCE_WORDS = [
    "evidence",
    "document",
    "documents",
    "record",
    "records",
    "status",
    "timeline",
    "plan",
    "task list",
    "project plan",
    "invoice",
    "email",
    "registration",
    "declaration",
    "label",
    "labels",
    "translation",
    "translations",
]

RISK_WORDS = [
    "risk",
    "gap",
    "issue",
    "consequence",
    "concern",
    "blocker",
    "not in place",
    "don't have",
    "do not have",
    "audit",
    "late",
    "delay",
]

DECISION_WORDS = [
    "agreed",
    "decided",
    "decision",
    "confirmed",
    "accepted",
    "approved",
]

NOISE_WORDS = {
    "yeah",
    "yes",
    "no",
    "okay",
    "ok",
    "mhm",
    "mm",
    "right",
    "thanks",
    "thank you",
}


@dataclass
class EvidenceItem:
    bucket: str
    speaker: str
    text: str


def has_any(text: str, phrases: Iterable[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def is_noise(sentence: str) -> bool:
    lowered = normalise(sentence).lower().strip(".,!? ")
    if not lowered:
        return True
    if lowered in NOISE_WORDS:
        return True
    return len(lowered.split()) <= 2 and all(word in NOISE_WORDS for word in lowered.split())


def classify_sentence(sentence: str) -> str:
    """Classify one sentence into an evidence bucket.

    Responsibility deliberately wins over action. In compliance meetings,
    statements such as "the importer should verify registration" contain
    action-like modal verbs, but they describe an obligation rather than a
    concrete task.
    """

    text = normalise(sentence).lower()
    if is_noise(text):
        return "noise"

    question = "?" in sentence or has_any(text, OPEN_QUESTION_WORDS)
    responsibility = has_any(text, RESPONSIBILITY_WORDS)
    evidence = has_any(text, EVIDENCE_WORDS)
    decision = has_any(text, DECISION_WORDS)
    risk = has_any(text, RISK_WORDS)
    strong_action = has_any(text, ACTION_WORDS)

    if question:
        return "question"
    if responsibility:
        return "responsibility"
    if decision:
        return "decision"
    if evidence:
        return "evidence_needed"
    if risk:
        return "risk"
    if strong_action:
        return "action"
    return "discussion"


def parse_turns(transcript: str) -> list[tuple[str, str]]:
    """Parse Teams-style speaker turns from a transcript."""

    speaker_line = re.compile(r"^(.+?)\s+(\d{1,2}:\d{2})\s*$")
    turns: list[tuple[str, str]] = []
    current_speaker = "Unknown"
    current_lines: list[str] = []

    for raw_line in transcript.splitlines():
        line = raw_line.strip()
        match = speaker_line.match(line)
        if match:
            if current_lines:
                turns.append((current_speaker, normalise(" ".join(current_lines))))
            current_speaker = match.group(1).strip()
            current_lines = []
        elif line:
            current_lines.append(line)

    if current_lines:
        turns.append((current_speaker, normalise(" ".join(current_lines))))

    return turns


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [normalise(chunk) for chunk in chunks if normalise(chunk)]


def extract_items(transcript: str) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for speaker, turn_text in parse_turns(transcript):
        for sentence in split_sentences(turn_text):
            bucket = classify_sentence(sentence)
            if bucket != "noise":
                items.append(EvidenceItem(bucket=bucket, speaker=speaker, text=sentence))
    return items


def keyword_summary(items: list[EvidenceItem], limit: int = 12) -> list[str]:
    stop = {
        "the",
        "and",
        "that",
        "this",
        "with",
        "have",
        "from",
        "they",
        "there",
        "will",
        "would",
        "should",
        "could",
        "about",
        "because",
        "just",
        "what",
        "when",
        "where",
        "which",
        "your",
        "you",
        "for",
        "are",
    }
    words: list[str] = []
    for item in items:
        words.extend(re.findall(r"[a-zA-Z][a-zA-Z'-]{3,}", item.text.lower()))
    counts = Counter(word for word in words if word not in stop)
    return [word for word, _ in counts.most_common(limit)]


def build_report(items: list[EvidenceItem]) -> dict:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        buckets[item.bucket].append(asdict(item))

    return {
        "scorecard": {bucket: len(values) for bucket, values in sorted(buckets.items())},
        "keywords": keyword_summary(items),
        "buckets": buckets,
    }


def render_markdown(report: dict) -> str:
    scorecard = report["scorecard"]
    lines = [
        "# MiniLM evidence graph",
        "",
        "This output separates compliance responsibilities, actions, risks and open questions.",
        "",
        "## Scorecard",
        "",
    ]
    for bucket, count in scorecard.items():
        lines.append(f"- {bucket.replace('_', ' ').title()}: {count}")

    lines.extend(["", "## Keywords", "", ", ".join(report["keywords"]), ""])

    preferred_order = [
        "responsibility",
        "evidence_needed",
        "action",
        "risk",
        "question",
        "decision",
        "discussion",
    ]

    for bucket in preferred_order:
        values = report["buckets"].get(bucket, [])
        lines.extend(["", f"## {bucket.replace('_', ' ').title()}", ""])
        if not values:
            lines.append("- None detected.")
            continue
        for value in values[:80]:
            speaker = value["speaker"]
            text = value["text"]
            lines.append(f"- **{speaker}:** {text}")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--json-out", type=Path, default=Path("minilm_evidence_graph_report.json"))
    parser.add_argument("--md-out", type=Path, default=Path("minilm_evidence_graph_minutes.md"))
    args = parser.parse_args()

    transcript = args.transcript.read_text(encoding="utf-8", errors="replace")
    items = extract_items(transcript)
    report = build_report(items)

    args.json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.md_out.write_text(render_markdown(report), encoding="utf-8")

    print(json.dumps(report["scorecard"], indent=2))
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")


if __name__ == "__main__":
    main()
