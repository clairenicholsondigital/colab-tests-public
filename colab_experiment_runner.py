#!/usr/bin/env python3
"""Colab experiment harness for the MiniLM evidence graph.

The entry point is ``run_analysis`` so the file can be called by the Colab
``execute_python`` / ``execute_python_url`` task wrappers.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


RAW_CLASSIFIER_URL = (
    "https://raw.githubusercontent.com/clairenicholsondigital/"
    "colab-tests-public/main/minilm_evidence_graph.py"
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
    },
    {
        "name": "trial4_plus_process_flow",
        "description": "Adds operating-model phrases for analysing discussion misses.",
        "options": {
            **TRIAL4_BEST_OPTIONS,
            "process_flow_words": [
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
                "final storage",
            ],
        },
    },
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
    try:
        import minilm_evidence_graph as classifier

        return classifier
    except ModuleNotFoundError:
        pass

    local_path = Path(__file__).with_name("minilm_evidence_graph.py")
    if local_path.exists():
        return _load_module_from_path(local_path)

    with urllib.request.urlopen(RAW_CLASSIFIER_URL, timeout=20) as response:
        source = response.read()

    temp_dir = Path(tempfile.mkdtemp(prefix="minilm_classifier_"))
    temp_path = temp_dir / "minilm_evidence_graph.py"
    temp_path.write_bytes(source)
    return _load_module_from_path(temp_path)


def _load_module_from_path(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("minilm_evidence_graph_dynamic", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
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
        "EVIDENCE_WORDS",
        "RISK_WORDS",
        "DECISION_WORDS",
    ]
    return {name: getattr(classifier, name)[:] for name in names}


def _restore_words(classifier: Any, original: dict[str, list[str]]) -> None:
    for name, values in original.items():
        setattr(classifier, name, values)


def _apply_options(classifier: Any, options: dict[str, Any]) -> None:
    mapping = {
        "open_question_words": "OPEN_QUESTION_WORDS",
        "responsibility_words": "RESPONSIBILITY_WORDS",
        "action_words": "ACTION_WORDS",
        "evidence_words": "EVIDENCE_WORDS",
        "risk_words": "RISK_WORDS",
        "decision_words": "DECISION_WORDS",
    }
    for option_name, global_name in mapping.items():
        setattr(
            classifier,
            global_name,
            _merge_unique(getattr(classifier, global_name), options.get(option_name, [])),
        )


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
                    "evidence_needed",
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
                "evidence_words": len(classifier.EVIDENCE_WORDS),
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
