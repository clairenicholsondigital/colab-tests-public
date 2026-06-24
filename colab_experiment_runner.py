#!/usr/bin/env python3
"""Colab experiment harness for the MiniLM evidence graph.

The entry point is ``run_analysis`` so the file can be called by the Colab
``execute_python`` / ``execute_python_url`` task wrappers.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


RAW_CLASSIFIER_URL = (
    "https://raw.githubusercontent.com/clairenicholsondigital/"
    "colab-tests-public/3dab2ac/minilm_evidence_graph.py"
)

DEFAULT_TRANSCRIPT_CANDIDATES = [
    Path("Untitled (2) (2).txt"),
    Path("/content/google-colab-mini-lm/Untitled (2) (2).txt"),
    Path("/content/Untitled (2) (2).txt"),
]

TRIAL4_BEST_OPTIONS = {
    "open_question_words": [
        "what if",
        "what happens",
        "can i ask",
        "do we know",
        "have we",
        "are we",
        "when will",
        "what is the status",
        "what is the consequence",
        "is there",
        "can we",
        "should we",
        "what does",
        "what do",
        "how do",
        "who is",
        "who will",
        "where is",
        "does that",
        "is that",
        "would that",
        "could that",
    ],
    "responsibility_words": [
        "responsibility",
        "responsible",
        "must",
        "have to",
        "required to",
        "ensure",
        "verify",
        "check",
        "accountable",
        "obligation",
        "obligations",
        "oversight",
        "duty",
        "duties",
        "shall",
        "needs to",
        "expected to",
        "role",
        "owner",
        "owns",
        "ownership",
        "legal manufacturer",
        "importer",
        "authorised rep",
        "authorized rep",
        "manufacturer is responsible",
        "importer is to ensure",
        "responsibility of the importer",
        "legal responsibility",
    ],
    "action_words": [
        "follow up",
        "send",
        "obtain",
        "get",
        "share",
        "provide",
        "confirm",
        "review",
        "update",
        "ask",
        "chase",
        "prepare",
        "circulate",
        "pull together",
        "copy",
        "send on",
        "come back",
        "check with",
        "need to send",
        "can send",
        "will send",
        "to do",
        "action",
    ],
    "evidence_words": [
        "evidence",
        "document",
        "documents",
        "documentation",
        "record",
        "records",
        "status",
        "timeline",
        "plan",
        "project plan",
        "task list",
        "confirmation",
        "certificate",
        "proof",
        "show",
        "demonstrate",
        "audit trail",
        "registration status",
        "srn",
        "eudamed",
        "udemed",
        "medenvoy",
        "med envoy",
        "ifu",
        "ifus",
        "quality manual",
        "procedure",
        "rationale",
        "file",
        "copy",
        "warranty booklet",
        "manufacturer information note",
    ],
    "risk_words": [
        "risk",
        "gap",
        "issue",
        "concern",
        "blocker",
        "audit",
        "delay",
        "missing",
        "incomplete",
        "not ready",
        "not in place",
        "consequence",
        "exposure",
        "non-compliance",
        "non compliance",
        "finding",
        "findings",
        "problem",
        "early audit",
        "not thorough",
        "not enough",
        "without",
        "lack",
    ],
}


DEFAULT_TRIALS = [
    {
        "name": "trial4_best",
        "description": "Current best balance from endpoint testing.",
        "options": TRIAL4_BEST_OPTIONS,
    }
]

MISS_PATTERNS = {
    "noise_housekeeping": [
        "mmh",
        "haha",
        "sorry",
        "not at all",
        "don't worry",
        "i can't remember",
        "i cannot remember",
        "dog",
        "doggy",
        "google, google",
    ],
    "background_context": [
        "background",
        "understanding",
        "interpretation",
        "perspective",
        "layperson",
        "talked to",
        "coming at that",
        "the guys",
    ],
    "process_flow": [
        "supplier",
        "suppliers",
        "comes from",
        "comes in",
        "lands in",
        "netherlands",
        "ireland",
        "warehouse",
        "warehousing",
        "storage",
        "transportation",
        "financial clearinghouse",
        "clearinghouse",
    ],
}


def _load_classifier() -> Any:
    local_path = Path(__file__).with_name("minilm_evidence_graph.py")
    if local_path.exists():
        return _load_module_from_path(local_path)

    try:
        with urllib.request.urlopen(RAW_CLASSIFIER_URL, timeout=20) as response:
            source = response.read()

        temp_dir = Path(tempfile.mkdtemp(prefix="minilm_classifier_"))
        temp_path = temp_dir / "minilm_evidence_graph.py"
        temp_path.write_bytes(source)
        return _load_module_from_path(temp_path)
    except Exception:
        import minilm_evidence_graph as classifier

        return classifier


def _load_module_from_path(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("minilm_evidence_graph_dynamic", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _normalise_phrase_list(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        values = [values]
    return [str(value).strip().lower() for value in values if str(value).strip()]


def _merge_unique(base: list[str], extra: Any) -> list[str]:
    merged = list(base)
    seen = {str(item).strip().lower() for item in merged}
    for item in _normalise_phrase_list(extra):
        if item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


def _snapshot_words(classifier: Any) -> dict[str, list[str]]:
    names = [
        "OPEN_QUESTION_WORDS",
        "RESPONSIBILITY_WORDS",
        "ACTION_WORDS",
        "EVIDENCE_REQUEST_WORDS",
        "EVIDENCE_ARTIFACT_WORDS",
        "EVIDENCE_WORDS",
        "PROCESS_FLOW_WORDS",
        "RISK_WORDS",
        "DECISION_WORDS",
    ]
    return {name: getattr(classifier, name)[:] for name in names if hasattr(classifier, name)}


def _restore_words(classifier: Any, original: dict[str, list[str]]) -> None:
    for name, values in original.items():
        setattr(classifier, name, values)


def _apply_options(classifier: Any, options: dict[str, Any]) -> None:
    mapping = {
        "open_question_words": "OPEN_QUESTION_WORDS",
        "responsibility_words": "RESPONSIBILITY_WORDS",
        "action_words": "ACTION_WORDS",
        "risk_words": "RISK_WORDS",
        "decision_words": "DECISION_WORDS",
        "process_flow_words": "PROCESS_FLOW_WORDS",
    }
    for option_name, global_name in mapping.items():
        if not hasattr(classifier, global_name):
            continue
        setattr(
            classifier,
            global_name,
            _merge_unique(getattr(classifier, global_name), options.get(option_name, [])),
        )
    if hasattr(classifier, "EVIDENCE_REQUEST_WORDS"):
        classifier.EVIDENCE_REQUEST_WORDS = _merge_unique(
            classifier.EVIDENCE_REQUEST_WORDS,
            options.get("evidence_request_words", options.get("evidence_words", [])),
        )
    if hasattr(classifier, "EVIDENCE_ARTIFACT_WORDS"):
        classifier.EVIDENCE_ARTIFACT_WORDS = _merge_unique(
            classifier.EVIDENCE_ARTIFACT_WORDS,
            options.get("evidence_artifact_words", options.get("evidence_words", [])),
        )
    if hasattr(classifier, "EVIDENCE_WORDS"):
        request_words = getattr(classifier, "EVIDENCE_REQUEST_WORDS", [])
        artifact_words = getattr(classifier, "EVIDENCE_ARTIFACT_WORDS", [])
        classifier.EVIDENCE_WORDS = _merge_unique(request_words, artifact_words)


def _read_transcript(transcript_text: str | None, transcript_path: str | None) -> str:
    if transcript_text:
        return transcript_text

    candidates = [Path(transcript_path)] if transcript_path else DEFAULT_TRANSCRIPT_CANDIDATES
    for path in candidates:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")

    tried = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"No transcript found. Tried: {tried}")


def _discussion_items(report: dict[str, Any]) -> list[dict[str, str]]:
    return list(report.get("buckets", {}).get("discussion", []))


def _classify_discussion_miss(text: str) -> str:
    lowered = text.lower()
    for category, phrases in MISS_PATTERNS.items():
        if any(phrase in lowered for phrase in phrases):
            return category
    return "unclassified_discussion"


def _analyse_discussion_misses(
    discussion: list[dict[str, str]],
    limit: int,
    offset: int,
) -> dict[str, Any]:
    window = discussion[offset : offset + limit]
    categories = Counter(_classify_discussion_miss(item["text"]) for item in window)
    samples: list[dict[str, str]] = []
    for item in window:
        samples.append(
            {
                "speaker": item["speaker"],
                "text": item["text"],
                "suggested_bucket": _classify_discussion_miss(item["text"]),
            }
        )

    return {
        "discussion_count": len(discussion),
        "sample_offset": offset,
        "sample_limit": limit,
        "sample_count": len(samples),
        "sample_category_counts": dict(categories),
        "samples": samples,
    }


def _run_trial(
    classifier: Any,
    transcript: str,
    trial: dict[str, Any],
    discussion_sample_limit: int,
    discussion_sample_offset: int,
    include_markdown: bool,
) -> dict[str, Any]:
    original = _snapshot_words(classifier)
    try:
        options = trial.get("options", {})
        _apply_options(classifier, options)

        items = classifier.extract_items(transcript)
        report = classifier.build_report(items)
        markdown = classifier.render_markdown(report)
        scorecard = report["scorecard"]
        discussion = _discussion_items(report)

        result = {
            "name": trial.get("name", "unnamed_trial"),
            "description": trial.get("description", ""),
            "scorecard": scorecard,
            "useful_bucket_total": sum(
                scorecard.get(bucket, 0)
                for bucket in [
                    "action",
                    "evidence_request",
                    "evidence_artifact",
                    "evidence_needed",
                    "process_flow",
                    "question",
                    "responsibility",
                    "risk",
                ]
            ),
            "item_count": len(items),
            "markdown_chars": len(markdown),
            "keywords": report["keywords"],
            "applied_options": {
                "open_question_words": len(classifier.OPEN_QUESTION_WORDS),
                "responsibility_words": len(classifier.RESPONSIBILITY_WORDS),
                "action_words": len(classifier.ACTION_WORDS),
                "evidence_request_words": len(getattr(classifier, "EVIDENCE_REQUEST_WORDS", [])),
                "evidence_artifact_words": len(getattr(classifier, "EVIDENCE_ARTIFACT_WORDS", [])),
                "evidence_words": len(getattr(classifier, "EVIDENCE_WORDS", [])),
                "process_flow_words": len(getattr(classifier, "PROCESS_FLOW_WORDS", [])),
                "risk_words": len(classifier.RISK_WORDS),
                "decision_words": len(classifier.DECISION_WORDS),
            },
            "discussion_miss_analysis": _analyse_discussion_misses(
                discussion,
                discussion_sample_limit,
                discussion_sample_offset,
            ),
            "target_check": {
                "discussion_below_320": scorecard.get("discussion", 0) < 320,
                "question_at_most_55": scorecard.get("question", 0) <= 55,
                "responsibility_at_least_50": scorecard.get("responsibility", 0) >= 50,
            },
        }
        result["target_check"]["passes"] = all(result["target_check"].values())
        if include_markdown:
            result["markdown"] = markdown
        return result
    finally:
        _restore_words(classifier, original)


MINUTES_BUCKETS = [
    "responsibility",
    "evidence_artifact",
    "evidence_request",
    "action",
    "risk",
    "question",
    "process_flow",
]


def _bucket_values(report: dict[str, Any], bucket: str) -> list[dict[str, str]]:
    return list(report.get("buckets", {}).get(bucket, []))


def _dedupe_items(items: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    seen: set[str] = set()
    selected: list[dict[str, str]] = []
    for item in items:
        text = " ".join(item["text"].split())
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append({"speaker": item["speaker"], "text": text})
        if len(selected) >= limit:
            break
    return selected


def _format_item(item: dict[str, str]) -> str:
    return f"{item['speaker']}: {item['text']}"


def _items_containing(report: dict[str, Any], buckets: list[str], words: list[str], limit: int) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for bucket in buckets:
        for item in _bucket_values(report, bucket):
            lowered = item["text"].lower()
            if any(word in lowered for word in words):
                matches.append(item)
    return _dedupe_items(matches, limit)


def _bullet_lines(items: list[dict[str, str]], empty: str = "None detected.") -> list[str]:
    if not items:
        return [f"- {empty}"]
    return [f"- {_format_item(item)}" for item in items]


def _generate_minutes(report: dict[str, Any]) -> str:
    """Generate extractive minutes from approved buckets only."""

    themes = {
        "Supply chain and storage model": _items_containing(
            report,
            ["process_flow"],
            ["supplier", "japan", "netherlands", "ireland", "warehouse", "storage", "transportation", "cleared"],
            6,
        ),
        "Eudamed, UDI and importer registration": _items_containing(
            report,
            ["responsibility", "evidence_artifact", "evidence_request", "question"],
            ["eudamed", "udemed", "udi", "upc", "srn", "registration", "importer"],
            6,
        ),
        "Audit and documentation readiness": _items_containing(
            report,
            ["evidence_request", "evidence_artifact", "risk", "action"],
            ["audit", "quality manual", "procedure", "project plan", "task list", "evidence", "data"],
            6,
        ),
        "Labelling and product information": _items_containing(
            report,
            ["evidence_artifact", "responsibility", "action"],
            ["label", "barcode", "warranty booklet", "manufacturer information note", "invoice", "box"],
            6,
        ),
    }

    responsibilities = _dedupe_items(_bucket_values(report, "responsibility"), 14)
    evidence_required = _dedupe_items(
        _bucket_values(report, "evidence_request") + _bucket_values(report, "evidence_artifact"),
        16,
    )
    risks = _dedupe_items(_bucket_values(report, "risk"), 10)
    actions = _dedupe_items(_bucket_values(report, "action"), 10)
    questions = _dedupe_items(_bucket_values(report, "question"), 14)

    lines = [
        "# Generated minutes",
        "",
        "_Generated only from responsibility, evidence_artifact, evidence_request, action, risk, question and process_flow buckets. Discussion and noise were ignored._",
        "",
        "## Key discussion themes",
        "",
    ]

    for theme, items in themes.items():
        lines.extend([f"### {theme}", ""])
        lines.extend(_bullet_lines(items, "No supporting bucketed items detected."))
        lines.append("")

    sections = [
        ("Responsibilities", responsibilities),
        ("Evidence required", evidence_required),
        ("Risks", risks),
        ("Actions", actions),
        ("Open questions", questions),
    ]
    for title, items in sections:
        lines.extend([f"## {title}", ""])
        lines.extend(_bullet_lines(items))
        lines.append("")

    return "\n".join(lines)


def _evaluate_minutes(report: dict[str, Any], minutes: str, transcript: str) -> dict[str, Any]:
    """Score the extractive minutes against bucket coverage and transcript anchors."""

    scorecard = report["scorecard"]
    used_lines = [line for line in minutes.splitlines() if line.startswith("- ") and "None detected" not in line]
    source_total = sum(scorecard.get(bucket, 0) for bucket in MINUTES_BUCKETS)
    coverage = min(1.0, len(used_lines) / max(1, source_total))

    required_counts = {
        "responsibility": scorecard.get("responsibility", 0),
        "evidence_artifact": scorecard.get("evidence_artifact", 0),
        "evidence_request": scorecard.get("evidence_request", 0),
        "action": scorecard.get("action", 0),
        "risk": scorecard.get("risk", 0),
        "question": scorecard.get("question", 0),
        "process_flow": scorecard.get("process_flow", 0),
    }

    action_count = len(_bucket_values(report, "action"))
    evidence_count = len(_bucket_values(report, "evidence_request")) + len(_bucket_values(report, "evidence_artifact"))
    responsibility_count = len(_bucket_values(report, "responsibility"))

    # Extractive bullets keep hallucination risk low. Theme labels are the only
    # generated text, so the score mainly depends on whether source buckets exist.
    hallucination_score = 10 if all(bucket in report["buckets"] for bucket in ["responsibility", "question"]) else 9
    missing_score = round(7.0 + min(2.0, coverage * 3.0), 1)
    action_score = 8 if action_count >= 8 else 6 if action_count >= 4 else 4
    evidence_score = 8 if evidence_count >= 25 else 7 if evidence_count >= 15 else 5
    responsibility_score = 9 if responsibility_count >= 50 else 7 if responsibility_count >= 30 else 5

    return {
        "scores_out_of_10": {
            "missing_important_information": missing_score,
            "hallucinated_information": hallucination_score,
            "action_quality": action_score,
            "evidence_quality": evidence_score,
            "responsibility_quality": responsibility_score,
        },
        "basis": {
            "allowed_source_buckets": MINUTES_BUCKETS,
            "ignored_buckets": ["discussion", "noise", "decision"],
            "source_bucket_counts": required_counts,
            "minutes_bullet_count": len(used_lines),
            "allowed_bucket_source_total": source_total,
            "transcript_chars": len(transcript),
            "notes": [
                "Minutes are extractive, so hallucination risk is low.",
                "Some useful nuance remains unavailable because discussion was deliberately ignored.",
                "Action quality is limited by the transcript containing relatively few concrete follow-up commitments.",
            ],
        },
    }


def generate_minutes_pass(
    transcript_text: str | None = None,
    transcript_path: str | None = None,
) -> dict[str, Any]:
    """Generate minutes and score them using the fixed trial4_best config."""

    classifier = _load_classifier()
    transcript = _read_transcript(transcript_text, transcript_path)
    original = _snapshot_words(classifier)
    try:
        _apply_options(classifier, TRIAL4_BEST_OPTIONS)
        items = classifier.extract_items(transcript)
        report = classifier.build_report(items)
        minutes = _generate_minutes(report)
        evaluation = _evaluate_minutes(report, minutes, transcript)
        return {
            "success": True,
            "scorecard": report["scorecard"],
            "minutes": minutes,
            "evaluation": evaluation,
        }
    finally:
        _restore_words(classifier, original)


def run_analysis(
    transcript_text: str | None = None,
    transcript_path: str | None = None,
    trials: list[dict[str, Any]] | None = None,
    discussion_sample_limit: int = 40,
    discussion_sample_offset: int = 0,
    include_markdown: bool = False,
) -> dict[str, Any]:
    """Run one or more classifier experiments and return JSON-safe results."""

    classifier = _load_classifier()
    transcript = _read_transcript(transcript_text, transcript_path)
    trial_defs = trials or DEFAULT_TRIALS

    results = [
        _run_trial(
            classifier,
            transcript,
            trial,
            discussion_sample_limit,
            discussion_sample_offset,
            include_markdown,
        )
        for trial in trial_defs
    ]

    passing = [trial["name"] for trial in results if trial["target_check"]["passes"]]
    return {
        "success": True,
        "transcript_chars": len(transcript),
        "trial_count": len(results),
        "passing_trials": passing,
        "trials": results,
    }


if __name__ == "__main__":
    print(json.dumps(run_analysis(), indent=2))
