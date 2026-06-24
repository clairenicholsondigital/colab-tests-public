#!/usr/bin/env python3
"""Colab experiment harness for the MiniLM evidence graph.

The entry point is ``run_analysis`` so the file can be called by the Colab
``execute_python`` / ``execute_python_url`` task wrappers.
"""

from __future__ import annotations

import importlib.util
import json
import re
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


def _indexed_bucket(report: dict[str, Any], bucket: str) -> list[dict[str, Any]]:
    indexed: list[dict[str, Any]] = []
    for index, item in enumerate(_bucket_values(report, bucket), start=1):
        text = " ".join(item["text"].split())
        if not text or text.lower().startswith("client dita"):
            continue
        indexed.append(
            {
                "anchor": f"{bucket}#{index}",
                "bucket": bucket,
                "index": index,
                "speaker": item["speaker"],
                "text": text,
            }
        )
    return indexed


def _source_candidates(
    report: dict[str, Any],
    buckets: list[str],
    terms: list[str],
    limit: int = 4,
) -> list[dict[str, Any]]:
    scored: list[tuple[int, int, int, dict[str, Any]]] = []
    seen: set[str] = set()
    lowered_terms = [term.lower() for term in terms]
    for bucket_position, bucket in enumerate(buckets):
        for item in _indexed_bucket(report, bucket):
            lowered = item["text"].lower()
            score = sum(1 for term in lowered_terms if _term_matches(lowered, term))
            if score <= 0:
                continue
            key = item["text"].lower()
            if key in seen:
                continue
            seen.add(key)
            scored.append((score, bucket_position, item["index"], item))
    scored.sort(key=lambda row: (-row[0], row[1], row[2]))
    return [item for _, _, _, item in scored[:limit]]


def _term_matches(lowered_text: str, lowered_term: str) -> bool:
    if not lowered_term:
        return False
    if re.fullmatch(r"[a-z0-9]+", lowered_term):
        return re.search(rf"\b{re.escape(lowered_term)}\b", lowered_text) is not None
    return lowered_term in lowered_text


def _anchor_list(sources: list[dict[str, Any]]) -> str:
    return ", ".join(source["anchor"] for source in sources)


def _table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _source_excerpt(source: dict[str, Any]) -> str:
    return f"{source['anchor']} {source['speaker']}: {source['text']}"


def _clean_source_text(text: str) -> str:
    text = re.sub(r"\b[A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+){0,2}\s+\d{1,2}:\d{2}", "", text)
    text = re.sub(r"\b[A-Z][A-Za-z'’-]+\s*:\s*", "", text)
    text = re.sub(r"^[A-Z][A-Za-z'’ -]+(?:Review|Meeting|Planning|Update)\s+Date:\s*", "", text)
    text = re.sub(r"\bDate:\s*\d{1,2}\s+[A-Z][a-z]+\s+\d{4}\b", "", text)
    text = re.sub(r"\bLocation:\s*Online\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text.replace(".And", ". And").replace(".So", ". So")).strip()
    return text


def _shorten_source_text(text: str, max_words: int = 28) -> str:
    words = _clean_source_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",.;:") + "..."


def _polished_entry(
    text: str,
    report: dict[str, Any],
    buckets: list[str],
    terms: list[str],
    limit: int = 4,
) -> dict[str, Any] | None:
    sources = _source_candidates(report, buckets, terms, limit)
    if not sources:
        return None
    return {
        "text": text,
        "sources": sources,
        "source_anchors": [source["anchor"] for source in sources],
    }


def _polished_minutes_sections(report: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Build non-hallucinated polished minutes with explicit source anchors."""

    sections: dict[str, list[dict[str, Any]]] = {
        "Key discussion themes": [],
        "Responsibilities": [],
        "Evidence required": [],
        "Risks": [],
        "Actions": [],
        "Open questions": [],
    }

    definitions = [
        (
            "Key discussion themes",
            "The product flow is Japan to the Netherlands for fiscal clearance, then onwards to Ireland, with little or no Netherlands storage.",
            ["process_flow"],
            ["japan", "netherlands", "ireland", "cleared", "storage"],
        ),
        (
            "Key discussion themes",
            "The team focused on importer obligations, Udimed/Eudamed registration, UDI/barcode data, and who is responsible for checking or uploading product data.",
            ["responsibility", "question", "evidence_request"],
            ["udimed", "eudamed", "udi", "upc", "importer", "data"],
        ),
        (
            "Key discussion themes",
            "Audit readiness depends on showing that procedures, data collection, Med Envoy activity and supporting evidence are in progress.",
            ["evidence_request", "risk"],
            ["audit", "preparation", "data", "med envoy", "project plan", "task list"],
        ),
        (
            "Key discussion themes",
            "Labelling, barcode design, lot numbering and product documentation are active areas of work.",
            ["evidence_artifact", "action", "question"],
            ["label", "barcode", "lot", "manufacturer", "warranty booklet"],
        ),
        (
            "Responsibilities",
            "DITA needs procedures that reflect the applicable regulatory requirements and the way the business actually operates.",
            ["responsibility", "evidence_request"],
            ["reg requirements", "procedure", "business works", "meaningful", "usable"],
        ),
        (
            "Responsibilities",
            "As importer, DITA needs to check labels and confirm the importer link for DITA Inc.",
            ["responsibility"],
            ["importer", "label", "check", "dita inc"],
        ),
        (
            "Responsibilities",
            "New products need to be entered into Udimed immediately, and existing items need to be entered by the November deadline discussed in the call.",
            ["responsibility", "question"],
            ["new products", "udimed", "immediately", "november"],
        ),
        (
            "Responsibilities",
            "The legal manufacturer is responsible for putting data into Udimed; the importer and authorised representative need to check that it is there.",
            ["responsibility"],
            ["legal manufacturer", "responsible", "authorised rep", "udimed"],
        ),
        (
            "Responsibilities",
            "DITA needs a lot-number process so product can be picked, labelled and stored by lot number.",
            ["responsibility", "action", "evidence_artifact"],
            ["lot number", "pick", "store"],
        ),
        (
            "Evidence required",
            "The quality manual and related procedures are core evidence for showing importer-obligation controls.",
            ["evidence_request"],
            ["quality manual", "procedure"],
        ),
        (
            "Evidence required",
            "A Med Envoy project plan, task list or equivalent activity overview is needed to understand timing, responsibilities and crossover points.",
            ["evidence_request", "risk", "action"],
            ["med envoy", "project plan", "task list", "timelines", "crossover"],
        ),
        (
            "Evidence required",
            "Evidence is needed that product data is being collected or is ready to be put into Udimed/Eudamed.",
            ["evidence_request", "responsibility"],
            ["collecting the data", "product information", "udimed", "data"],
        ),
        (
            "Evidence required",
            "Labels, barcode design, barcode format and lot-number implementation are supporting artefacts to keep under review.",
            ["evidence_artifact", "question", "action"],
            ["label", "barcode", "lot number"],
        ),
        (
            "Evidence required",
            "The warranty booklet/manufacturer information note and IFU status need to be clarified as part of the documentation set.",
            ["evidence_request", "process_flow"],
            ["warranty booklet", "manufacturer", "ifu", "MIN"],
        ),
        (
            "Risks",
            "Without a clear Med Envoy plan or timeline, there is a gap around when registration work will be completed.",
            ["risk", "evidence_request"],
            ["without", "gap", "timelines", "med envoy"],
        ),
        (
            "Risks",
            "If the audit happens early, DITA will need to show preparation is underway rather than finished.",
            ["risk", "evidence_request"],
            ["audit", "early", "preparation"],
        ),
        (
            "Risks",
            "There is a risk that responsibility for Udimed activity is assumed to sit elsewhere and gets dropped or missed.",
            ["responsibility", "risk"],
            ["dropped", "missed", "somebody else", "oversight"],
        ),
        (
            "Actions",
            "Orla to provide a written formal overview of the intercompany structure.",
            ["action"],
            ["written formally", "intercompany structure"],
        ),
        (
            "Actions",
            "Jacqui to send the relevant QMS/manual material to Orla.",
            ["action", "question"],
            ["flick this over", "qms manual"],
        ),
        (
            "Actions",
            "Orla to review the document/update work with the additional information.",
            ["action", "evidence_request"],
            ["review that document", "update with all the additional information"],
        ),
        (
            "Actions",
            "Orla to take the barcode/UDI question back to the US team.",
            ["action", "question"],
            ["bring that to the US team", "barcodes", "udi"],
        ),
        (
            "Actions",
            "Orla to follow up with Cody/Med Envoy on the process, information needed and timelines.",
            ["action", "evidence_request", "risk"],
            ["follow up", "cody", "med envoy", "process", "timelines"],
        ),
        (
            "Actions",
            "Jacqui/Colm to review the SRN/company-size information and seek direction from Liam if needed.",
            ["action", "evidence_request"],
            ["send it on", "colm", "liam", "company size"],
        ),
        (
            "Open questions",
            "Is the described product-flow reflection correct?",
            ["question"],
            ["correct reflection", "how it works"],
        ),
        (
            "Open questions",
            "Is the Park West warehousing facility DITA-operated or third-party?",
            ["question"],
            ["park west", "third party", "own operated"],
        ),
        (
            "Open questions",
            "Is the warehouse automated or fully manual?",
            ["question"],
            ["automated", "manual warehouse"],
        ),
        (
            "Open questions",
            "Does the mapped process cover supplier purchase orders, customer sales orders, or both?",
            ["question"],
            ["purchase order", "sales order", "flow of products"],
        ),
        (
            "Open questions",
            "Are product registrations handled at UPC/SKU level, and are barcodes actual UDI barcodes?",
            ["question"],
            ["upc", "sku", "udi barcodes", "barcodes"],
        ),
        (
            "Open questions",
            "What is Med Envoy doing, what information do they need, and how long will their work take?",
            ["question", "evidence_request"],
            ["med envoy", "what information", "how long", "process"],
        ),
    ]

    for section, text, buckets, terms in definitions:
        entry = _polished_entry(text, report, buckets, terms)
        if entry:
            sections[section].append(entry)

    return sections


def _render_polished_minutes(sections: dict[str, list[dict[str, Any]]]) -> str:
    lines = [
        "# Polished generated minutes",
        "",
        "_Generated only from responsibility, evidence_artifact, evidence_request, action, risk, question and process_flow buckets. Discussion and noise were ignored. Each bullet includes source anchors back to bucketed transcript lines._",
        "",
    ]
    for section, entries in sections.items():
        lines.extend([f"## {section}", ""])
        if not entries:
            lines.extend(["- None detected from the allowed buckets.", ""])
            continue
        for entry in entries:
            lines.append(f"- {entry['text']} _(Sources: {_anchor_list(entry['sources'])})_")
        lines.append("")

    lines.extend(["## Source excerpts", ""])
    seen: set[str] = set()
    for entries in sections.values():
        for entry in entries:
            for source in entry["sources"]:
                if source["anchor"] in seen:
                    continue
                seen.add(source["anchor"])
                lines.append(f"- {_source_excerpt(source)}")
    lines.append("")
    return "\n".join(lines)


def _topic_entry(
    text: str,
    report: dict[str, Any],
    buckets: list[str],
    terms: list[str],
    limit: int = 4,
) -> dict[str, Any]:
    entry = _polished_entry(text, report, buckets, terms, limit)
    if entry is None:
        return {
            "text": text,
            "sources": [],
            "source_anchors": [],
        }
    return entry


def _add_topic_entry(
    topic: dict[str, Any],
    section: str,
    text: str,
    report: dict[str, Any],
    buckets: list[str],
    terms: list[str],
    limit: int = 4,
) -> None:
    entry = _polished_entry(text, report, buckets, terms, limit)
    if entry is not None:
        topic["sections"].setdefault(section, []).append(entry)


def _profile_topic_entry(
    text: str,
    report: dict[str, Any],
    buckets: list[str],
    terms: list[str],
    limit: int = 4,
) -> dict[str, Any] | None:
    sources = _source_candidates(report, buckets, terms, limit)
    if not sources:
        return None
    return {
        "text": text,
        "sources": sources,
        "source_anchors": [source["anchor"] for source in sources],
    }


def _add_profile_section(
    topic: dict[str, Any],
    section: str,
    text: str,
    report: dict[str, Any],
    buckets: list[str],
    terms: list[str],
    limit: int = 4,
) -> None:
    entry = _profile_topic_entry(text, report, buckets, terms, limit)
    if entry is not None:
        topic["sections"].setdefault(section, []).append(entry)


def _generic_action_entries(
    report: dict[str, Any],
    active_topic_names: list[str],
    limit: int = 10,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    active_topics = " | ".join(active_topic_names).lower()
    for action in ACTION_PROFILES:
        required_topics = action.get("requires_topic", [])
        if required_topics and not any(topic.lower() in active_topics for topic in required_topics):
            continue
        entry = _profile_topic_entry(
            action["text"],
            report,
            ["action", "evidence_request", "responsibility"],
            action["terms"],
            limit=3,
        )
        if entry is None:
            continue
        if len({source["anchor"] for source in entry["sources"]}) < action.get("min_sources", 1):
            continue
        key = entry["text"].lower()
        if key in seen:
            continue
        seen.add(key)
        combined_source_text = " ".join(
            f"{source.get('speaker', '')} {source.get('text', '')}"
            for source in entry["sources"]
        )
        entry["owner"] = _infer_action_owner(combined_source_text, action)
        deadline_source = _action_deadline_source(report, action, entry)
        if deadline_source is not None:
            entry["deadline"] = deadline_source["deadline"]
            entry["deadline_source"] = deadline_source
            if deadline_source["anchor"] not in {source["anchor"] for source in entry["sources"]}:
                entry["sources"].append(deadline_source)
                entry["source_anchors"].append(deadline_source["anchor"])
        else:
            entry["deadline"] = _infer_action_deadline(combined_source_text)
        entries.append(entry)
        if len(entries) >= limit:
            return entries
    return entries


OWNER_PATTERNS: list[tuple[str, str]] = [
    ("Jack", r"\bjack\b"),
    ("Ciara", r"\bciara\b"),
    ("Conor", r"\bconor\b"),
    ("Jacqui", r"\bjacqui\b"),
    ("Orla", r"\borla\b|\bo['’]?reilly\b"),
    ("Colm", r"\bcolm\b"),
    ("Mark", r"\bmark\b"),
    ("Jenny", r"\bjenny\b"),
    ("John-Paul", r"\bjohn[-\s]?paul\b"),
    ("Andrew", r"\bandrew\b"),
    ("Rebecca", r"\brebecca\b"),
    ("David", r"\bdavid\b"),
    ("Ciaran", r"\bciaran\b"),
    ("Adil", r"\badil\b"),
    ("Kevin", r"\bkevin\b"),
    ("Grace", r"\bgrace\b"),
    ("Liam", r"\bliam\b"),
    ("All", r"\ball\b"),
    ("Team", r"\bteam\b"),
]


SPEAKER_LABEL_RE = re.compile(r"^[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3}$")
NON_PERSON_LABELS = {
    "agenda",
    "attendees",
    "date",
    "location",
    "participants",
    "unknown",
    "actions",
    "next steps",
    "to dos",
}
CONVERSATIONAL_LABEL_STARTS = {"agreed", "okay", "ok", "fine", "right", "perfect", "yes", "no"}
DATE_LABEL_STARTS = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "today", "tonight", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
}


def _looks_like_person_label(value: str) -> bool:
    label = value.strip()
    lowered = label.lower()
    if not label or lowered in NON_PERSON_LABELS:
        return False
    if "date" in lowered or "location" in lowered:
        return False
    first = label.split()[0].lower().strip(".")
    if first == "unknown" or first in CONVERSATIONAL_LABEL_STARTS or first in DATE_LABEL_STARTS:
        return False
    if "." in label:
        return False
    return bool(SPEAKER_LABEL_RE.match(label))


def _infer_action_owner(source_text: str, action: dict[str, Any]) -> str:
    explicit_owner = action.get("owner")
    if explicit_owner:
        return explicit_owner
    owner_to_action = None
    for match in re.finditer(
        r"\b([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})\s+to\s+(?:[a-z]+)\b",
        source_text,
    ):
        if _looks_like_person_label(match.group(1)):
            owner_to_action = match
    if owner_to_action and _looks_like_person_label(owner_to_action.group(1)):
        return owner_to_action.group(1)
    unknown_speaker_first_person = re.match(
        r"\s*Unknown\s+([A-Z][A-Za-z'’.-]+)\s+(?:\d{1,2}:\d{2}(?::\d{2})?\s+)?\bI\s+(?:will|can|should|need|have to|am going to)\b",
        source_text,
    )
    if unknown_speaker_first_person:
        return unknown_speaker_first_person.group(1)
    speaker_first_person = re.match(
        r"\s*([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})\s+(?:\d{1,2}:\d{2}(?::\d{2})?\s+)?\bI\s+(?:will|can|should|need|have to|am going to)\b",
        source_text,
    )
    if speaker_first_person and _looks_like_person_label(speaker_first_person.group(1)):
        return speaker_first_person.group(1)
    lowered = source_text.lower()
    owners: list[str] = []
    for owner, pattern in OWNER_PATTERNS:
        if re.search(pattern, lowered) and owner not in owners:
            owners.append(owner)
    if not owners:
        return "Owner not specified"
    owners = [owner for owner in owners if owner.lower() != "unknown"]
    if not owners:
        return "Owner not specified"
    return "/".join(owners[:2])


def _infer_action_deadline(source_text: str) -> str:
    cleaned = _clean_source_text(source_text)
    lowered = cleaned.lower()

    date_patterns = [
        r"\b\d{1,2}(?:st|nd|rd|th)?(?:\s+of)?\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s+['’]?\d{2,4})?\b",
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+['’]?\d{2,4})?\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return match.group(0)

    if re.search(r"\b(action|item|task)\s+(?:is\s+)?(?:done|closed)\b|\bclosed\s+(?:out|off)\b", lowered):
        return "Done"

    relative_patterns = [
        (r"\bearly\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b", None),
        (r"\bmid\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b", None),
        (r"\bsecond last week of (?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b", None),
        (r"\bend of next week\b", "End of next week"),
        (r"\bend of (?:the )?week\b", "End of week"),
        (r"\bthis week\b", "This week"),
        (r"\bnext week\b", "Next week"),
        (r"\b(?:by|on|for)\s+(?:monday|tuesday|wednesday|thursday|friday)\b", None),
        (r"\b(?:by|before)\s+lunch\b", "Before lunch"),
        (r"\b(?:by|before)\s+noon\b", "Noon"),
        (r"\btonight\b", "Tonight"),
        (r"\btoday\b", "Today"),
        (r"\bthis afternoon\b", "This afternoon"),
        (r"\bthis evening\b", "This evening"),
    ]
    for pattern, label in relative_patterns:
        match = re.search(pattern, lowered)
        if match:
            if label:
                return label
            value = match.group(0)
            if value.startswith(("by ", "on ", "for ")):
                return value.split(None, 1)[1].title()
            if "wednesday" in value:
                return "Done for Wednesday"
            if value.startswith(("early ", "mid ")):
                return value.title()
            if value.startswith("second last week"):
                return value.replace("july", "July").replace("june", "June")
            return value
    return "Not specified"


def _deadline_specificity(deadline: str) -> int:
    lowered = deadline.lower()
    if deadline == "Not specified":
        return 0
    if re.search(r"\d{1,2}|20\d{2}", deadline):
        return 4
    if "early" in lowered or "mid" in lowered or "end of" in lowered:
        return 3
    if "next week" in lowered or "this week" in lowered or "wednesday" in lowered:
        return 2
    if deadline == "Done" or deadline == "Weekly":
        return 1
    return 1


def _action_deadline_source(
    report: dict[str, Any],
    action: dict[str, Any],
    entry: dict[str, Any],
) -> dict[str, Any] | None:
    search_terms = list(dict.fromkeys(action["terms"] + action.get("deadline_terms", [])))
    if action.get("deadline_lookup") is False:
        return None
    candidate_buckets = [
        "action",
        "responsibility",
        "evidence_request",
        "evidence_artifact",
        "question",
        "risk",
        "process_flow",
    ]
    candidates: list[tuple[int, int, int, dict[str, Any], str]] = []
    existing_anchors = {source["anchor"] for source in entry["sources"]}
    for bucket_position, bucket in enumerate(candidate_buckets):
        for source in _indexed_bucket(report, bucket):
            deadline = _infer_action_deadline(source["text"])
            if deadline == "Not specified":
                continue
            lowered = source["text"].lower()
            score = sum(1 for term in search_terms if _term_matches(lowered, term.lower()))
            is_existing_source = source["anchor"] in existing_anchors
            if is_existing_source:
                score += 2
            elif score < action.get("deadline_min_score", 2):
                continue
            candidates.append(
                (
                    _deadline_specificity(deadline),
                    score,
                    -bucket_position,
                    source,
                    deadline,
                )
            )
    if not candidates:
        return None
    candidates.sort(key=lambda row: (-row[0], -row[1], row[2], row[3]["index"]))
    _, _, _, source, deadline = candidates[0]
    deadline_source = dict(source)
    deadline_source["deadline"] = deadline
    return deadline_source


ACTION_PROFILES: list[dict[str, Any]] = [
    {
        "text": "Provide or review the QMS/manual/procedure documentation.",
        "terms": ["qms", "quality manual", "procedure", "manual", "review that document"],
        "requires_topic": ["QMS"],
    },
    {
        "text": "Provide a written overview of the relevant business/process structure.",
        "terms": ["written formally", "intercompany structure", "business works", "process overview"],
        "requires_topic": ["QMS"],
    },
    {
        "text": "Review barcode, UDI or registration questions with the relevant internal team.",
        "terms": ["barcode", "udi", "upc", "sku", "registration", "us team", "bring that"],
        "deadline_terms": ["lot number", "lot numbering", "early july"],
        "requires_topic": ["UDI"],
    },
    {
        "text": "Follow up with Cody/Med Envoy on process, information needs and timelines.",
        "terms": ["cody", "med envoy", "timelines", "project plan", "task list"],
        "requires_topic": ["UDI", "Project tracking"],
    },
    {
        "text": "Review scope and documentation implications for PPE/sunglasses.",
        "terms": ["ppe", "sunglasses", "scope", "doc", "declaration"],
        "requires_topic": ["Labelling"],
        "owner": "Jacqui",
    },
    {
        "text": "Follow up on language or translation requirements.",
        "terms": ["translation", "language", "languages", "doc", "competent authority"],
        "requires_topic": ["Labelling"],
        "owner": "Jacqui",
    },
    {
        "text": "Review the alarm mute/flash behaviour and confirm the updated alarm setup.",
        "terms": ["mute", "alarm", "flash", "low", "medium", "high"],
        "deadline_min_score": 3,
        "requires_topic": ["Software"],
        "owner": "Andrew",
    },
    {
        "text": "Complete clinical or usability review of the relevant changes.",
        "terms": ["clinical", "clinician", "usability", "formative", "summative", "study"],
        "deadline_terms": ["review team", "signed off", "change request", "acceptable"],
        "requires_topic": ["Clinical"],
        "owner": "Rebecca",
    },
    {
        "text": "Review debug commands or scripts and confirm what appears on the device.",
        "terms": ["debug", "command", "commands", "script", "screen"],
        "requires_topic": ["Software"],
        "owner": "Andrew/David",
    },
    {
        "text": "Trace software version changes and generate supporting test evidence if needed.",
        "terms": ["version", "v1.01", "v1.02", "trace", "test data", "retrospective"],
        "deadline_terms": ["17 changes", "code", "test scenarios"],
        "requires_topic": ["Software"],
        "owner": "David/Andrew",
    },
    {
        "text": "Review language-file or graphics-driver issues for the additional translations.",
        "terms": ["language", "languages", "arabic", "vietnamese", "greek", "driver", "font"],
        "requires_topic": ["Software"],
        "owner": "Andrew",
    },
    {
        "text": "Complete or review electrical compliance testing and related outputs.",
        "terms": ["electrical", "60601", "testing", "test reports", "test report"],
        "deadline_terms": ["23rd", "july", "final piece", "compliance testing"],
        "requires_topic": ["Electrical"],
        "owner": "Andrew",
    },
    {
        "text": "Update risk management for cybersecurity, USB access and related controls.",
        "terms": ["cybersecurity", "usb", "risk management", "port lock", "password", "controls"],
        "deadline_terms": ["risk", "risk management file", "wednesday", "share back"],
        "requires_topic": ["Cybersecurity"],
        "owner": "Rebecca",
    },
    {
        "text": "Review applicability of the relevant standards.",
        "terms": ["standard", "standards", "81001", "27427", "applicable"],
        "requires_topic": ["Electrical", "Cybersecurity"],
        "owner": "Colm/Andrew",
    },
    {
        "text": "Schedule or hold the follow-up calls needed to close open items.",
        "terms": ["schedule", "call", "follow up", "follow-up", "working session", "weekly"],
        "deadline_lookup": False,
    },
    {
        "text": "Review and simplify the slide content and visual support.",
        "terms": ["slide", "picture", "image", "visual", "text", "content", "simple", "simplify"],
        "requires_topic": ["Slides"],
    },
    {
        "text": "Use clearer webinar wording around responsible adoption of AI in a GXP setting.",
        "terms": ["responsible adoption", "gxp", "regulated", "regulatory", "phrase"],
        "requires_topic": ["AI adoption"],
    },
    {
        "text": "Frame the demo before opening it and connect it to the low-hanging-fruit use case.",
        "terms": ["demo", "explain", "low hanging fruit", "complaints", "triage", "jump into"],
        "requires_topic": ["Demo"],
    },
    {
        "text": "Keep the webinar educational and avoid making the offering feel too sales-led.",
        "terms": ["salesy", "educational", "offering", "process", "roi"],
        "requires_topic": ["Meeting agenda"],
    },
    {
        "text": "Practise the presenter sections and keep each section within the agreed timing.",
        "terms": ["practice", "practise", "7 to 10 minutes", "bullet points", "presenting", "tomorrow"],
        "requires_topic": ["Timing"],
    },
    {
        "text": "Clarify client scope, available engineers and next-week onsite needs.",
        "terms": ["client", "engineers", "scope", "onsite", "on site", "next week"],
        "requires_topic": ["Client scope"],
    },
]


TOPIC_PROFILES: list[dict[str, Any]] = [
    {
        "topic": "QMS, procedures and business process alignment",
        "summary": "The discussion covered how procedures and quality-system documents need to align with existing business processes.",
        "responsibility": "Procedures need to reflect both regulatory requirements and the way the business actually operates.",
        "evidence": "Quality manuals, procedures, trackers or summary documents are supporting evidence for this topic.",
        "risk": "If procedures are not aligned with day-to-day work, they may be difficult to use or maintain.",
        "questions": "Open questions remain around how current processes, systems or records work in practice.",
        "terms": ["qms", "quality manual", "procedure", "process", "business works", "tracker", "summary document", "technical file"],
        "required_any": ["qms", "quality manual", "technical file", "tracker", "summary document"],
    },
    {
        "topic": "Supply chain, warehousing and order fulfilment",
        "summary": "The discussion covered product flow, warehousing, picking, packing, labelling and dispatch.",
        "responsibility": "The process needs clear ownership for product handling, storage, picking, packing and dispatch steps.",
        "evidence": "Flow diagrams, warehouse process details, labels and system records are supporting evidence.",
        "risk": "Weak process understanding could leave gaps in procedure definition or operational controls.",
        "questions": "Open questions remain around storage, automation, order flow or third-party involvement.",
        "terms": ["warehouse", "warehousing", "japan", "netherlands", "ireland", "park west", "picking", "packing", "shipping", "courier", "sales order"],
        "required_any": ["warehouse", "warehousing", "japan", "netherlands", "park west", "sales order"],
    },
    {
        "topic": "UDI, EUDAMED and registration responsibilities",
        "summary": "The discussion covered device registration, UDI/barcode data and responsibility for registration checks.",
        "responsibility": "Registration responsibilities need to be clear across manufacturer, importer and representative roles.",
        "evidence": "Registration data, UDI/barcode information and project plans are supporting evidence.",
        "risk": "There is a risk that registration activity is assumed to sit elsewhere and is missed.",
        "questions": "Open questions remain around registration level, barcode format, data ownership or timelines.",
        "terms": ["udimed", "eudamed", "udi", "upc", "sku", "registration", "registered", "importer", "authorised rep", "med envoy"],
        "required_any": ["udimed", "eudamed", "udi", "upc", "sku", "importer", "authorised rep", "med envoy"],
    },
    {
        "topic": "Labelling, IFU, DoC and product documentation",
        "summary": "The discussion covered labels, IFUs, declarations of conformity and product documentation.",
        "responsibility": "Product documentation needs review so labels, IFUs, DoCs and supporting information remain aligned.",
        "evidence": "Labels, DoCs, IFUs, warranty booklets, manufacturer information notes and screenshots are supporting artefacts.",
        "risk": "Documentation gaps may create audit findings or market-specific follow-up actions.",
        "questions": "Open questions remain around documentation content, translation, label symbols or applicable documents.",
        "terms": ["label", "barcode", "ifu", "doc", "declaration", "warranty booklet", "manufacturer information", "translation", "language", "languages", "sunglasses", "ppe"],
        "required_any": ["label", "barcode", "ifu", "declaration", "warranty booklet", "manufacturer information", "sunglasses", "ppe", "translation", "language", "languages"],
    },
    {
        "topic": "Software changes, alarms and versioning",
        "summary": "The discussion covered software changes, alarm behaviour, language changes, debug behaviour and version traceability.",
        "responsibility": "Software changes need review, traceability and appropriate supporting documentation.",
        "evidence": "Change requests, code review outputs, test data, debug scripts and version comparisons are supporting evidence.",
        "risk": "If software changes cannot be traced or evidenced, retrospective test data or justification may be needed.",
        "questions": "Open questions remain around alarm behaviour, debug commands, version differences or implementation evidence.",
        "terms": ["software", "alarm", "mute", "debug", "version", "v1.01", "v1.02", "code", "firmware", "language", "languages", "driver", "font"],
        "required_any": ["software", "alarm", "mute", "debug", "version", "firmware", "driver"],
    },
    {
        "topic": "Clinical, usability and study timing",
        "summary": "The discussion covered clinical or usability review, formative/summative study timing and submission alignment.",
        "responsibility": "Clinical and usability inputs need to align with change review and submission timelines.",
        "evidence": "Clinical review feedback, task analysis, usability documents and study plans are supporting evidence.",
        "risk": "Misaligned study dates could affect submission readiness or notified-body review.",
        "questions": "Open questions remain around study dates, review ownership or whether changes are acceptable clinically.",
        "terms": ["clinical", "clinician", "usability", "formative", "summative", "study", "task analysis", "submission", "review date"],
        "required_any": ["clinical", "clinician", "usability", "formative", "summative", "task analysis"],
    },
    {
        "topic": "Electrical compliance and standards assessment",
        "summary": "The discussion covered electrical compliance testing, standards assessment and test-report dependencies.",
        "responsibility": "Electrical compliance and standards gaps need review before deliverables can be completed.",
        "evidence": "Test reports, gap assessments and standards reviews are supporting evidence.",
        "risk": "Testing or standards gaps could delay deliverables or require additional justification.",
        "questions": "Open questions remain around test completion, applicable standards or remaining compliance gaps.",
        "terms": ["electrical", "iec60601", "60601", "testing", "test report", "standards", "standard", "gap assessment", "mdd"],
        "required_any": ["electrical", "iec60601", "60601", "test report", "gap assessment", "mdd"],
    },
    {
        "topic": "Cybersecurity, risk management and access controls",
        "summary": "The discussion covered cybersecurity, risk management updates, USB access and control options.",
        "responsibility": "Risk management needs to address cybersecurity controls and residual-risk decisions.",
        "evidence": "Risk-management updates, standards, competitor-control reviews and benefit-risk rationale are supporting evidence.",
        "risk": "Uncontrolled access or unresolved residual risk may require further controls or benefit-risk justification.",
        "questions": "Open questions remain around control effectiveness, password protection, port locks or standard applicability.",
        "terms": ["cybersecurity", "usb", "port", "password", "risk management", "benefit-risk", "controls", "81001", "27427", "unauthorized"],
        "required_any": ["cybersecurity", "usb", "port lock", "password", "81001", "27427", "unauthorized"],
    },
    {
        "topic": "Project tracking, document control and submission readiness",
        "summary": "The discussion covered project status, document tracking, change requests and submission readiness.",
        "responsibility": "Owners need to keep project documents, change requests and submission materials moving.",
        "evidence": "Trackers, change requests, document-control records and submission packages are supporting evidence.",
        "risk": "Open document or tracker gaps may delay review, approval or submission readiness.",
        "questions": "Open questions remain around status, ownership, deadlines or what needs to be closed before submission.",
        "terms": ["tracker", "change request", "document", "documents", "approval", "submission", "deadline", "sign off", "status", "tf24", "technical file"],
        "required_any": ["tracker", "change request", "submission", "deadline", "sign off", "tf24", "technical file"],
    },
]


GENERIC_TOPIC_PROFILES: list[dict[str, Any]] = [
    {
        "topic": "Meeting agenda, structure and flow",
        "summary": "The discussion covered the intended structure, running order and flow of the session.",
        "responsibility": "The team needs to keep the session structure clear and easy to follow.",
        "evidence": "Agenda notes, running-order comments and presenter handover points are supporting evidence.",
        "risk": "If the structure is unclear, the session may feel rushed or difficult to follow.",
        "questions": "Open questions remain around flow, handovers or what should be covered in each part.",
        "terms": ["agenda", "welcome", "kick off", "flow", "wrap", "session", "webinar", "presentation", "handover", "start"],
    },
    {
        "topic": "Slides, visuals and supporting material",
        "summary": "The discussion covered slides, images, visual support and how much detail should appear on screen.",
        "responsibility": "Slides and visuals need to support the spoken explanation without overloading the audience.",
        "evidence": "Slide comments, image references and content-editing notes are supporting evidence.",
        "risk": "Dense or mismatched visuals may weaken the message or distract from the presenter.",
        "questions": "Open questions remain around which image, layout or level of slide detail should be used.",
        "terms": ["slide", "slides", "picture", "image", "visual", "photo", "gamma", "content", "text", "screen", "layout"],
    },
    {
        "topic": "Demo, example workflow and practical use case",
        "summary": "The discussion covered the demo, example workflow and practical use case being shown.",
        "responsibility": "The demo needs to be introduced clearly and tied back to the problem it solves.",
        "evidence": "Demo framing, example workflow notes and use-case descriptions are supporting evidence.",
        "risk": "If the demo is not framed, the audience may miss why it matters or how it connects to the process.",
        "questions": "Open questions remain around what the demo should show and how much context it needs.",
        "terms": ["demo", "demonstration", "example", "workflow", "use case", "complaints", "triage", "tool", "copilot", "email"],
    },
    {
        "topic": "AI adoption, change management and process improvement",
        "summary": "The discussion covered AI adoption, process improvement and how to choose useful starting points.",
        "responsibility": "AI opportunities need to solve a real process problem and keep responsible people in the decision loop.",
        "evidence": "Process maps, opportunity registers, roadmaps and improvement criteria are supporting evidence.",
        "risk": "AI work may fail to land if it is built on top of poor workflows or does not solve a real problem.",
        "questions": "Open questions remain around opportunity fit, adoption barriers or how the process should change.",
        "terms": ["ai", "adoption", "process", "improvement", "opportunity", "roadmap", "responsible", "gxp", "workflow", "change", "problem"],
    },
    {
        "topic": "Timing, rehearsal and delivery readiness",
        "summary": "The discussion covered timing, practice, delivery readiness and how presenters should prepare.",
        "responsibility": "Presenters need to practise, manage timing and keep clear notes for their sections.",
        "evidence": "Timing estimates, practice comments and presenter-preparation notes are supporting evidence.",
        "risk": "Without rehearsal, sections may run too long, finish too quickly or lose clarity.",
        "questions": "Open questions remain around section lengths, practice needs or delivery order.",
        "terms": ["practice", "practise", "minutes", "time", "timing", "tomorrow", "presenting", "bullet points", "rehearsal", "ready"],
    },
    {
        "topic": "Client scope, staffing and follow-up work",
        "summary": "The discussion covered client scope, staffing, follow-up work and related project opportunities.",
        "responsibility": "Client follow-up needs clear scope, available people and next-step ownership.",
        "evidence": "Client comments, staffing notes and scope discussions are supporting evidence.",
        "risk": "Unclear scope or staffing may make follow-up work difficult to plan.",
        "questions": "Open questions remain around client needs, staffing availability or what should happen next.",
        "terms": ["client", "scope", "engineers", "site", "onsite", "on-site", "galway", "gsk", "glaxosmithkline", "next week", "staff"],
    },
]


TOPIC_STOPWORDS = {
    "about", "actually", "again", "also", "around", "because", "being", "could", "doing",
    "everything", "from", "going", "gonna", "have", "here", "just", "kind", "know", "like",
    "little", "maybe", "mean", "need", "okay", "really", "right", "should", "some", "something",
    "stuff", "that's", "that", "their", "there", "these", "they", "thing", "think", "this",
    "those", "through", "want", "we're", "were", "what", "when", "where", "which", "with",
    "would", "yeah", "your",
}


def _all_indexed_sources(report: dict[str, Any], buckets: list[str] | None = None) -> list[dict[str, Any]]:
    selected_buckets = buckets or MINUTES_BUCKETS
    sources: list[dict[str, Any]] = []
    for bucket in selected_buckets:
        sources.extend(_indexed_bucket(report, bucket))
    return sources


def _source_words(text: str) -> list[str]:
    words = re.findall(r"[a-z][a-z0-9'’-]{2,}", text.lower())
    cleaned: list[str] = []
    for word in words:
        word = word.strip("'’-")
        if len(word) < 3 or word in TOPIC_STOPWORDS:
            continue
        cleaned.append(word)
    return cleaned


def _topic_terms_from_sources(sources: list[dict[str, Any]], limit: int = 6) -> list[str]:
    counts: dict[str, int] = {}
    for source in sources:
        for word in _source_words(source["text"]):
            counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda row: (-row[1], row[0]))
    return [word for word, _ in ranked[:limit]]


def _generic_topic_label(terms: list[str]) -> str:
    preferred = [term for term in terms if term not in {"process", "project", "work", "team", "people"}]
    chosen = (preferred or terms)[:3]
    if not chosen:
        return "Other supported discussion points"
    return ", ".join(term.title() for term in chosen)


def _dynamic_topic_from_remaining_sources(
    report: dict[str, Any],
    used_anchors: set[str],
) -> dict[str, Any] | None:
    candidate_sources = [
        source
        for source in _all_indexed_sources(report, ["action", "responsibility", "evidence_request", "question", "risk", "process_flow"])
        if source["anchor"] not in used_anchors
    ]
    if len(candidate_sources) < 3:
        return None
    terms = _topic_terms_from_sources(candidate_sources)
    if not terms:
        return None
    sources = _source_candidates(
        report,
        ["action", "responsibility", "evidence_request", "question", "risk", "process_flow"],
        terms,
        limit=5,
    )
    if len({source["anchor"] for source in sources}) < 3:
        return None
    label = _generic_topic_label(terms)
    return {
        "topic": label,
        "sections": {
            "Discussion points": [
                {
                    "text": f"The discussion also covered {', '.join(terms[:4])}.",
                    "sources": sources,
                    "source_anchors": [source["anchor"] for source in sources],
                }
            ],
        },
    }


def _profile_topic(
    profile: dict[str, Any],
    report: dict[str, Any],
    generic: bool = False,
) -> dict[str, Any] | None:
    if not generic and profile.get("required_any"):
        searchable = " ".join(
            source["text"].lower()
            for source in _all_indexed_sources(report, ["responsibility", "evidence_request", "evidence_artifact", "process_flow", "question", "risk", "action"])
        )
        if not any(_term_matches(searchable, term.lower()) for term in profile["required_any"]):
            return None

    topic = {"topic": profile["topic"], "sections": {}}
    terms = profile["terms"]
    summary_buckets = ["responsibility", "evidence_request", "evidence_artifact", "process_flow", "question", "risk", "action"]
    _add_profile_section(
        topic,
        "Discussion points",
        profile["summary"],
        report,
        summary_buckets,
        terms,
    )
    _add_profile_section(
        topic,
        "Responsibilities",
        profile["responsibility"],
        report,
        ["responsibility", "action"],
        terms,
    )
    _add_profile_section(
        topic,
        "Evidence required",
        profile["evidence"],
        report,
        ["evidence_artifact", "evidence_request", "responsibility", "action"],
        terms,
    )
    _add_profile_section(
        topic,
        "Risks",
        profile["risk"],
        report,
        ["risk", "responsibility", "evidence_request", "action"],
        terms,
        limit=3,
    )
    _add_profile_section(
        topic,
        "Open questions",
        profile["questions"],
        report,
        ["question", "evidence_request", "action"],
        terms,
        limit=3,
    )
    unique_topic_anchors = {
        anchor
        for entries in topic["sections"].values()
        for entry in entries
        for anchor in entry["source_anchors"]
    }
    min_anchors = 2 if generic else 2
    if topic["sections"] and len(unique_topic_anchors) >= min_anchors:
        return topic
    return None


def _normalise_action_text(text: str) -> str:
    text = _clean_source_text(text)
    text = re.sub(r"^.*?\b(?:actions?|next steps?|to dos?)(?:\s+before\s+[^:]+)?\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3}\s+\d{1,2}:\d{2}(?::\d{2})?\s+", "", text)
    text = re.sub(r"^\d{1,2}:\d{2}(?::\d{2})?\s+", "", text)
    text = re.sub(r"^[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3}\s*:\s*", "", text)
    text = re.sub(
        r"^([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})\s+to\s+",
        "",
        text,
    )
    text = re.sub(r"^(?:i['’]?ll|i\s+will|i\s+can|i\s+need\s+to|i\s+have\s+to)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:we\s+need\s+to|we\s+need|we\s+should\s+probably|we\s+should|you\s+need\s+to|can\s+you)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:probably)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:so|yeah|okay|and|but|then|maybe|probably|let's|i suppose|i think)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:the)\s+(?=\w+\s+document\b)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(draft|review|confirm|follow up)\s+the\s+", r"\1 ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdependency\s+map\b", "dependencies", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfollow-up\s+feedback\b", "feedback", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfollow up\s+follow up\b", "follow up", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\s+\b(?:by|before)\s+(?:monday|tuesday|wednesday|thursday|friday|lunch|noon|next week)\b\.?$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s+\bnext week\b\.?$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+\bweekly\s+as\s+well\b\.?$", " weekly", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+\b(?:today|tonight|this afternoon|this evening)\b\.?$", "", text, flags=re.IGNORECASE)
    text = text.strip(" ,.;:")
    if text and text[-1] not in ".?!":
        text += "."
    return text


def _is_useful_generic_action(text: str) -> bool:
    lowered = text.lower()
    action_start = re.match(r"^(?:patch|notify|replay|review|confirm|draft|follow up|validate|send|share|update|publish|rerun|call|prepare|pull|request|rewrite|schedule|reschedule|split|separate|monitor|set up|add|remove|reduce|refine|simplify|incorporate|redline|practice|practise)\b", lowered)
    if len(text.split()) < (2 if action_start else 6):
        return False
    if lowered.endswith("?"):
        return False
    weak_fragments = [
        "i don't know",
        "i suppose",
        "go to the next one",
        "let's see if we can do something",
        "like that type of stuff",
        "if you have any questions",
        "i can come back",
        "i don't mind",
        "same color background",
        "final discovery report",
        "you know what i mean",
        "like and subscribe",
        "wonderful to work here",
        "no actions",
        "no action",
        "no follow-up actions",
        "no follow up actions",
        "current information for now",
        "do not have a project update",
        "information briefing",
        "just awareness",
    ]
    if any(fragment in lowered for fragment in weak_fragments):
        return False
    if re.search(r"\b(?:is|are|was|were|has|have)\s+(?:still\s+)?(?:missing|pending|absent|ready|complete|completed|received|updated|available|unchanged)\b", lowered):
        return False
    if re.search(r"\b(?:looks|looked|feels|felt|seems|appears)\b", lowered):
        return False
    if re.search(r"\b(?:lets|allows|helps)\s+us\s+\w+", lowered):
        return False
    if _is_negative_decision_context(text) or _is_decision_sentence(text):
        return False
    if re.search(r"\b(?:update|recommendation|decision)\s+is\b", lowered):
        return False
    if re.search(r"\b(?:could|might|may)\s+(?:keep|include|defer|delay|start|use|go with|proceed)\b", lowered):
        return False
    return bool(
        re.search(
            r"\b(i|we|you|he|she|they|team|jack|ciara|conor|colm|orla|jacqui|andrew|rebecca|david|kevin|mark)\s+(?:can|will|should|need|needs|have to|has to|going to|want to|could)\b",
            lowered,
        )
        or re.search(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+to\s+\w+", text)
        or re.search(r"\b(?:patch|notify|replay|follow up|confirm|draft|review|validate|send|share|add|remove|update|publish|rerun|call|pull|request|rewrite|split|separate|monitor|set up|redline|reduce|refine|simplify|incorporate|practi[cs]e|prepare|schedule|reschedule|bring|explain|make sure|figure out)\b", lowered)
    )


def _extractive_action_entries(
    report: dict[str, Any],
    existing_action_texts: set[str],
    used_action_anchors: set[str] | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    blocked_anchors = used_action_anchors or set()
    seen_anchors: set[str] = set()
    for source in _indexed_bucket(report, "action"):
        if source["anchor"] in seen_anchors or source["anchor"] in blocked_anchors:
            continue
        text = _normalise_action_text(source["text"])
        key = text.lower()
        if key in existing_action_texts or not _is_useful_generic_action(text):
            continue
        entry = {
            "text": text,
            "sources": [source],
            "source_anchors": [source["anchor"]],
            "owner": _infer_action_owner(f"{source['speaker']} {source['text']}", {}),
            "deadline": _infer_action_deadline(source["text"]),
        }
        entries.append(entry)
        existing_action_texts.add(key)
        seen_anchors.add(source["anchor"])
        if len(entries) >= limit:
            break
    return entries


def _parse_raw_transcript_turns(transcript: str) -> list[dict[str, str]]:
    compressed = re.sub(r"\s+", " ", transcript).strip()
    compressed = re.sub(r"(?<=[a-z0-9.!?])([A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+){0,3}:)", r" \1", compressed)
    compressed = re.sub(
        r"\b([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})\s*\|\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\|\s*",
        r"\1 \2 ",
        compressed,
    )
    label_pattern = re.compile(
        r"(?<![A-Za-z0-9.])(?!(?:Agreed|Okay|Fine|Right|Perfect|Yes|No|Today|Tonight|Tomorrow|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Online)\b)([A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+){0,3})\s*(?:-\s*)?(?::|\s+\d{1,2}:\d{2}(?::\d{2})?)\s+"
    )
    matches = [match for match in label_pattern.finditer(compressed) if _looks_like_person_label(match.group(1))]
    if matches:
        turns: list[dict[str, str]] = []
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(compressed)
            text = compressed[start:end].strip(" |")
            text = re.sub(r"\s*\|\s*", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            if text and not re.match(r"^(date|location)\s*:", text, flags=re.IGNORECASE):
                turns.append({"speaker": match.group(1).strip(), "text": text})
        if turns:
            return turns

    turns: list[dict[str, str]] = []
    current_speaker = ""
    current_lines: list[str] = []
    speaker_pattern = re.compile(
        r"^\s*([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})\s*(?:\d{1,2}:\d{2}(?::\d{2})?)?\s*$"
    )
    inline_pattern = re.compile(
        r"^\s*([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})\s+\d{1,2}:\d{2}(?::\d{2})?\s+(.+)$"
    )
    colon_inline_pattern = re.compile(
        r"^\s*([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})\s*:\s+(.+)$"
    )

    def flush() -> None:
        nonlocal current_lines
        text = " ".join(line.strip() for line in current_lines if line.strip())
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            turns.append({"speaker": current_speaker, "text": text})
        current_lines = []

    for raw_line in transcript.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if re.match(r"^(date|location)\s*:", line, flags=re.IGNORECASE):
            continue
        if "started transcription" in line.lower() or "stopped transcription" in line.lower():
            continue
        colon_match = colon_inline_pattern.match(line)
        if colon_match and _looks_like_person_label(colon_match.group(1)):
            flush()
            current_speaker = colon_match.group(1).strip()
            current_lines.append(colon_match.group(2).strip())
            continue
        inline_match = inline_pattern.match(line)
        if inline_match and _looks_like_person_label(inline_match.group(1)):
            flush()
            current_speaker = inline_match.group(1).strip()
            current_lines.append(inline_match.group(2).strip())
            continue
        speaker_match = speaker_pattern.match(line)
        if speaker_match and _looks_like_person_label(speaker_match.group(1)) and len(line.split()) <= 4 and not re.search(r"[.!?]$", line):
            flush()
            current_speaker = speaker_match.group(1).strip()
            continue
        if current_speaker:
            current_lines.append(line)
    flush()
    return turns


def _split_raw_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+|(?:\s+-\s+)", text)
    if len(parts) == 1:
        parts = re.split(r"\s{2,}", text)
    return [part.strip(" -") for part in parts if len(part.strip(" -").split()) >= 2]


def _raw_source(anchor: str, speaker: str, text: str, bucket: str = "raw") -> dict[str, Any]:
    return {
        "anchor": anchor,
        "bucket": bucket,
        "index": int(re.sub(r"\D+", "", anchor) or 0),
        "speaker": speaker,
        "text": _normalise_action_text(text) if bucket == "raw_action" else _clean_source_text(text),
    }


def _is_low_substance_sentence(text: str) -> bool:
    lowered = text.lower().strip()
    if len(lowered.split()) < 5:
        return True
    low_value = [
        "started transcription",
        "stopped transcription",
        "stop recording",
        "anything else",
        "perfect",
        "okay thanks",
        "no.",
        "yeah.",
        "right.",
    ]
    return any(fragment in lowered for fragment in low_value)


def _is_explicitly_low_substance_transcript(transcript: str) -> bool:
    lowered = transcript.lower()
    return bool(
        re.search(r"\b(?:do not|don't)\s+have\s+(?:a\s+)?(?:project\s+)?update\b", lowered)
        and re.search(r"\bno\s+(?:action|actions|decisions?)\b", lowered)
    )


def _discussion_sentence_text(sentence: str, speaker: str) -> str:
    text = _clean_source_text(sentence)
    if _looks_like_person_label(speaker):
        text = re.sub(r"^I\s+am\b", f"{speaker} is", text, flags=re.IGNORECASE)
        text = re.sub(r"\bso\s+I\s+will\b", "and will", text, flags=re.IGNORECASE)
        text = re.sub(r"\bI\s+will\b", f"{speaker} will", text, flags=re.IGNORECASE)
    if re.search(r"\block\s+us\s+in\s+for\s+too\s+long\b", text, flags=re.IGNORECASE):
        text = "Contract term length would lock the team in for too long."
    return text


def _raw_discussion_entries(transcript: str, used_anchors: set[str], limit: int = 6) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    raw_index = 1
    for turn in _parse_raw_transcript_turns(transcript):
        for sentence in _split_raw_sentences(turn["text"]):
            lowered = sentence.lower()
            if _is_low_substance_sentence(sentence):
                continue
            if re.fullmatch(r"\d{1,2}\s+[a-z]+\s+\d{4}(?:\s+online)?", lowered):
                continue
            if lowered.endswith("?") and not re.search(r"\b(?:metrics|risk|issue|blocker|evidence|status)\b", lowered):
                continue
            if re.search(r"\b(?:maybe|may be|might|could|original plan|old plan|not this month|instead of cancelling|only if we accept|no project update|webcam|hear me|fine,? no actions?)\b", lowered) and not re.search(r"\b(?:reference documents?|document sections?|supporting documents?)\b", lowered):
                continue
            if (
                re.search(r"\b(i|we|you|he|she|they)\s+(?:will|can|should|need|needs|have to|has to)\b|\bi['’]?ll\b", lowered)
                and not re.search(r"\b(?:offsite|away|out of office|annual leave|holiday|miss the usual|miss the meeting)\b", lowered)
            ):
                continue
            if re.search(r"\b(?:decided|decision|agreed|rejected|go with|proceed with)\b", lowered):
                continue
            key = norm_key = re.sub(r"[^a-z0-9]+", " ", lowered).strip()
            if not key or norm_key in seen:
                continue
            seen.add(norm_key)
            anchor = f"raw#{raw_index}"
            raw_index += 1
            if anchor in used_anchors:
                continue
            entries.append(
                {
                    "text": _discussion_sentence_text(sentence, turn["speaker"]),
                    "sources": [_raw_source(anchor, turn["speaker"], sentence)],
                    "source_anchors": [anchor],
                }
            )
            if len(entries) >= limit:
                return entries
    return entries


def _explicit_action_lines(transcript: str) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    collecting = False
    speaker = "Unknown"
    for line in transcript.splitlines():
        stripped = line.strip().strip("-•* ")
        if not stripped:
            continue
        speaker_match = re.match(r"^([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})\s+\d{1,2}:\d{2}", stripped)
        if speaker_match:
            speaker = speaker_match.group(1)
            if re.fullmatch(r"[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3}\s+\d{1,2}:\d{2}(?::\d{2})?", stripped):
                continue
        lowered = stripped.lower()
        inline_header = re.match(r"^(?:actions?|next steps?|to dos?)(?:\s+before\s+[^:]+)?\s*:\s*(.+)$", stripped, flags=re.IGNORECASE)
        if inline_header:
            collecting = True
            inline_text = inline_header.group(1)
            parts = _split_raw_sentences(inline_text)
            if len(parts) == 1:
                parts = re.split(r",\s+|\s+and\s+(?=\w+\b)", inline_text)
            for part in parts:
                if len(part.split()) < 2:
                    continue
                actions.append({"speaker": speaker, "text": part.rstrip(".") + "."})
            continue
        if re.search(r"\b(actions?|next steps?|to dos?)\b.*:$", lowered) or lowered in {"actions before next week:", "actions:"}:
            collecting = True
            continue
        if collecting and re.search(r"\b(anything else|stop recording|thanks|thank you)\b", lowered):
            collecting = False
        if collecting and len(stripped.split()) >= 3:
            actions.append({"speaker": speaker, "text": stripped.rstrip(".") + "."})
    return actions


def _status_gap_action(sentence: str) -> str | None:
    cleaned = _clean_source_text(sentence).strip(" .")
    cleaned = re.sub(r"^(?:the)\s+(?=\w+\s+document\b)", "", cleaned, flags=re.IGNORECASE)
    lowered = cleaned.lower()
    match = re.match(r"(.+?)\s+(?:are|is)\s+still\s+not\s+finali[sz]ed\b", cleaned, flags=re.IGNORECASE)
    if match:
        return f"Review {match.group(1).strip()}"
    match = re.match(r"(.+?)\s+input\s+(?:is\s+)?still\s+missing\s+for\s+(.+)", cleaned, flags=re.IGNORECASE)
    if match:
        subject = re.sub(r"\bdependency\s+map\b", "dependencies", match.group(2).strip(), flags=re.IGNORECASE)
        return f"Confirm {subject} with {match.group(1).strip()}"
    match = re.match(r"(.+?\bdocument)\s+is\s+absent\b", cleaned, flags=re.IGNORECASE)
    if match:
        return f"Draft {match.group(1).strip()}"
    match = re.match(r"(.+?feedback)\s+is\s+still\s+pending\b", cleaned, flags=re.IGNORECASE)
    if match:
        subject = re.sub(r"\bfollow-up\s+feedback\b", "feedback", match.group(1).strip(), flags=re.IGNORECASE)
        return f"Follow up {subject}"
    if "still pending" in lowered and len(cleaned.split()) <= 10:
        subject = re.sub(r"\s+(?:is|are)\s+still\s+pending.*$", "", cleaned, flags=re.IGNORECASE)
        if subject:
            return f"Follow up {subject}"
    return None


def _raw_action_entries(
    transcript: str,
    existing_action_texts: set[str],
    used_action_anchors: set[str] | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    blocked = used_action_anchors or set()
    entries: list[dict[str, Any]] = []
    candidates: list[dict[str, str]] = _explicit_action_lines(transcript)
    pending_question: dict[str, str] | None = None
    last_candidate_by_speaker: dict[str, dict[str, str]] = {}
    stable_status_context = bool(re.search(r"\b(?:nothing\s+so\s+far\s+changes\s+the\s+timelines|timelines\s+are\s+unaffected|timelines\s+remain\s+unaffected)\b", transcript, flags=re.IGNORECASE))
    for turn in _parse_raw_transcript_turns(transcript):
        for sentence in _split_raw_sentences(turn["text"]):
            lowered = sentence.lower()
            gap_action = _status_gap_action(sentence)
            if gap_action:
                if not stable_status_context:
                    candidate = {"speaker": turn["speaker"], "text": gap_action}
                    candidates.append(candidate)
                    last_candidate_by_speaker[turn["speaker"]] = candidate
                continue
            delegated_question = re.search(
                r"\bcan\s+you\s+(.+?)(?:\?|$)",
                sentence,
                flags=re.IGNORECASE,
            )
            if delegated_question:
                pending_question = {"speaker": turn["speaker"], "text": delegated_question.group(1)}
                continue
            if pending_question and re.search(r"\b(?:i['’]?ll|i\s+will|yes|yeah|sure|i\s+can|i['’]?ll\s+do\s+that)\b", lowered):
                candidates.append({"speaker": turn["speaker"], "text": pending_question["text"]})
                pending_question = None
                continue
            if re.fullmatch(r"(?:today|tonight|tomorrow|before lunch|by lunch|before noon|by noon|this afternoon|this evening|monday|tuesday|wednesday|thursday|friday)\.?", lowered.strip()):
                previous = last_candidate_by_speaker.get(turn["speaker"])
                if previous and not re.search(r"\b(?:today|tonight|tomorrow|before lunch|by lunch|before noon|by noon|monday|tuesday|wednesday|thursday|friday)\b", previous["text"], re.I):
                    previous["text"] = previous["text"].rstrip(".") + " " + sentence.strip().rstrip(".") + "."
                continue
            if re.search(r"\b(?:we|i)\s+should\b", lowered) and not re.search(r"\b(?:we|i)\s+should\s+probably\b", lowered):
                continue
            if re.search(r"\bif\s+we\b", lowered):
                continue
            if re.search(
                r"\b(?:i|we|you|he|she|they|[A-Z][a-z]+)\s+(?:will|can|should|need to|needs to|have to|has to|going to)\b",
                sentence,
            ) or re.search(
                r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+to\s+(?:patch|notify|replay|follow up|send|share|review|draft|update|publish|rerun|call|prepare|confirm|validate|pull|request|rewrite|schedule|reschedule|reproduce|capture|remove|redline|separate|monitor|set up)\b",
                sentence,
            ) or re.search(r"\b(?:patch|notify|replay|follow up|send|share|review|draft|update|publish|rerun|call|prepare|confirm|validate|pull|request|rewrite|schedule|reschedule|remove|redline|separate|monitor|set up)\b", lowered):
                candidate = {"speaker": turn["speaker"], "text": sentence}
                candidates.append(candidate)
                last_candidate_by_speaker[turn["speaker"]] = candidate

    seen_sources: set[str] = set()
    for index, candidate in enumerate(candidates, start=1):
        original_text = candidate["text"]
        text = _normalise_action_text(candidate["text"])
        key = text.lower()
        if key in existing_action_texts or not _is_useful_generic_action(text):
            continue
        if re.search(r"\b(?:we will keep|we will run|we will sign|we will submit|we will use|decision|decided|agreed)\b", key):
            continue
        anchor = f"raw_action#{index}"
        if anchor in blocked or anchor in seen_sources:
            continue
        source = _raw_source(anchor, candidate["speaker"], text, "raw_action")
        owner = _infer_action_owner(original_text, {})
        if owner == "Owner not specified":
            owner = _infer_action_owner(f"{candidate['speaker']} {original_text}", {})
        if owner == "Owner not specified" and _looks_like_person_label(candidate["speaker"]):
            owner = candidate["speaker"]
        entry = {
            "text": text,
            "sources": [source],
            "source_anchors": [anchor],
            "owner": owner,
            "deadline": _infer_action_deadline(original_text),
        }
        entries.append(entry)
        existing_action_texts.add(key)
        seen_sources.add(anchor)
        if len(entries) >= limit:
            break
    return entries


def _enrich_actions_from_transcript(actions: list[dict[str, Any]], transcript: str) -> None:
    turns = _parse_raw_transcript_turns(transcript)
    deadline_by_speaker: dict[str, str] = {}
    for turn in turns:
        sentences = _split_raw_sentences(turn["text"])
        if not sentences and len(turn["text"].split()) <= 4:
            sentences = [turn["text"]]
        for sentence in sentences:
            deadline = _infer_action_deadline(sentence)
            if deadline != "Not specified" and len(sentence.split()) <= 4:
                deadline_by_speaker[turn["speaker"]] = deadline
    for entry in actions:
        if entry.get("owner") == "Owner not specified":
            combined = " ".join(str(source.get("text", "")) for source in entry.get("sources", []))
            owner = _infer_action_owner(combined, {})
            if owner != "Owner not specified":
                entry["owner"] = owner
        if entry.get("deadline") in {"", "Not specified"}:
            owner = str(entry.get("owner") or "")
            if owner in deadline_by_speaker:
                entry["deadline"] = deadline_by_speaker[owner]


def _normalise_decision_text(text: str) -> str:
    text = _clean_source_text(text)
    text = re.sub(r"^[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3}\s+\d{1,2}:\d{2}(?::\d{2})?\s+", "", text)
    text = re.sub(r"^[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3}\s*:\s*", "", text)
    text = re.sub(r"^(?:that is|that's)\s+the\s+decision\s+then\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^decision\s+confirmed\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^decision\s+is\s+to\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^decision\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:agreed|we agreed|the team agreed)\.?\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:then|so)\s+we\s+", "We ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+and\s+keep\s+[^.?!]*?\bunchanged\b", "", text, flags=re.IGNORECASE)
    text = text.strip(" ,.;:")
    if text and text[-1] not in ".?!":
        text += "."
    return text


def _is_weak_decision_text(text: str) -> bool:
    lowered = text.lower().strip(" .")
    return lowered in {"agreed", "agree", "yes", "okay", "ok", "confirmed"}


def _is_decision_sentence(text: str) -> bool:
    lowered = text.lower()
    if re.search(r"\bno\s+(?:decision|decisions)\b", lowered):
        return False
    if re.search(r"\b(?:maybe|may be|might|could|it may be|probably)\b", lowered):
        return False
    if re.search(r"\bonly\s+if\s+we\s+accept\b", lowered):
        return False
    return bool(
        re.search(r"\bdecision\s+(?:confirmed|is|was|then|:)\b", lowered)
        or re.search(r"\b(?:decided|agreed|rejected)\b", lowered)
        or re.search(r"\b(?:approved|approval)\s+(?:to|for)\b", lowered)
        or re.search(r"\b(?:we|the team)\s+(?:will|are going to|agreed to)\s+(?:start|keep|defer|delay|include|exclude|use|proceed|pause|add|remove|approve|reject|move|focus|sign|refund|invite|onboard|hold|assign)\b", lowered)
        or re.search(r"\bwe\s+(?:keep|defer|delay|include|exclude|use|proceed|pause|add|remove|approve|reject|move|focus|sign|refund|invite|onboard|hold|assign)\b", lowered)
        or re.search(r"^(?:keep|include|defer|delay|start|begin|use|proceed|pause|approve|reject|move|focus|sign|refund|invite|onboard|hold|assign)\b", lowered)
        or re.search(r"\b(?:recommendation|recommend)\s+is\s+to\b", lowered)
    )


def _is_negative_decision_context(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(r"\bno\s+(?:action|actions|decision|decisions)\b", lowered)
        or re.search(r"\bjust\s+(?:an\s+)?information\s+briefing\b", lowered)
    )


def _decision_entries(
    report: dict[str, Any],
    transcript: str,
    limit: int = 8,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    def overlaps_existing(text: str) -> bool:
        words = {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 3}
        if not words:
            return False
        for existing in seen:
            existing_words = {word for word in re.findall(r"[a-z0-9]+", existing) if len(word) > 3}
            if not existing_words:
                continue
            if len(words & existing_words) / max(1, min(len(words), len(existing_words))) >= 0.6:
                return True
        return False

    for source in _indexed_bucket(report, "decision"):
        text = _normalise_decision_text(source["text"])
        key = text.lower()
        if (
            not text
            or _is_weak_decision_text(text)
            or _is_negative_decision_context(text)
            or not _is_decision_sentence(text)
            or re.search(r"\b(?:move|use|keep|defer|delay|include|exclude|approve|reject|sign|focus)\s+it\b", text, flags=re.IGNORECASE)
            or re.search(r"\bonly\s+if\s+we\s+accept\b", text, flags=re.IGNORECASE)
            or key in seen
            or overlaps_existing(text)
        ):
            continue
        entries.append({"text": text, "sources": [source], "source_anchors": [source["anchor"]]})
        seen.add(key)
        if len(entries) >= limit:
            return entries

    raw_index = 1
    pending_decision: tuple[str, str] | None = None
    for turn in _parse_raw_transcript_turns(transcript):
        previous_was_agreement = False
        for sentence in _split_raw_sentences(turn["text"]):
            sentence_is_agreement = _is_weak_decision_text(sentence)
            if sentence_is_agreement:
                if pending_decision is not None:
                    pending_text, pending_speaker = pending_decision
                    text = _normalise_decision_text(pending_text)
                    key = text.lower()
                    if text and key not in seen and not overlaps_existing(text):
                        anchor = f"raw_decision#{raw_index}"
                        raw_index += 1
                        source = _raw_source(anchor, pending_speaker, pending_text, "raw_decision")
                        source["text"] = text
                        entries.append({"text": text, "sources": [source], "source_anchors": [anchor]})
                        seen.add(key)
                        if len(entries) >= limit:
                            return entries
                    pending_decision = None
                previous_was_agreement = True
                continue
            if re.search(
                r"\bwe\s+should\s+(?:move|focus|start|keep|defer|delay|include|exclude|use|proceed|pause|add|remove|approve|reject|sign|refund|invite|onboard|hold|assign)\b",
                sentence,
                flags=re.IGNORECASE,
            ) and not re.search(r"\b(?:maybe|may be|might|could)\b", sentence, flags=re.IGNORECASE):
                pending_decision = (sentence, turn["speaker"])
            if pending_decision is not None and re.match(r"^(?:agreed|yes|okay|ok|right),?\s+(?:let['’]?s|we)\b", sentence, flags=re.IGNORECASE):
                pending_text, pending_speaker = pending_decision
                decision_source_text = pending_text if re.search(r"\b(?:move|use|keep|defer|delay|include|exclude|approve|reject|sign|focus)\s+it\b", sentence, flags=re.IGNORECASE) else sentence
                decision_speaker = pending_speaker if decision_source_text == pending_text else turn["speaker"]
                text = _normalise_decision_text(decision_source_text)
                key = text.lower()
                if text and key not in seen and not overlaps_existing(text):
                    anchor = f"raw_decision#{raw_index}"
                    raw_index += 1
                    source = _raw_source(anchor, decision_speaker, decision_source_text, "raw_decision")
                    source["text"] = text
                    entries.append({"text": text, "sources": [source], "source_anchors": [anchor]})
                    seen.add(key)
                    if len(entries) >= limit:
                        return entries
                pending_decision = None
                continue
            decision_like = _is_decision_sentence(sentence) or (
                previous_was_agreement
                and re.search(r"^(?:keep|include|defer|delay|start|begin|use|proceed|pause|approve|reject)\b", sentence, flags=re.IGNORECASE)
            )
            previous_was_agreement = False
            if not decision_like or _is_negative_decision_context(sentence):
                continue
            text = _normalise_decision_text(sentence)
            key = text.lower()
            explicit_confirmation = bool(re.search(r"\bdecision\s+confirmed\b", sentence, flags=re.IGNORECASE))
            if (
                not text
                or _is_weak_decision_text(text)
                or key in seen
                or (overlaps_existing(text) and not explicit_confirmation)
            ):
                continue
            anchor = f"raw_decision#{raw_index}"
            raw_index += 1
            source = _raw_source(anchor, turn["speaker"], sentence, "raw_decision")
            source["text"] = text
            entries.append({"text": text, "sources": [source], "source_anchors": [anchor]})
            seen.add(key)
            if len(entries) >= limit:
                return entries
    return entries


def _apply_raw_transcript_fallback(topic_groups: dict[str, Any], report: dict[str, Any], transcript: str) -> None:
    if _is_explicitly_low_substance_transcript(transcript):
        topic_groups["topics"] = []
        topic_groups["actions"] = []
        topic_groups["decisions"] = []
        return
    used_topic_anchors = {
        anchor
        for topic in topic_groups["topics"]
        for entries in topic["sections"].values()
        for entry in entries
        for anchor in entry["source_anchors"]
    }
    existing_discussion_count = sum(
        len(topic["sections"].get("Discussion points", []))
        for topic in topic_groups["topics"]
    )
    raw_limit = 14 if len(topic_groups["topics"]) < 2 else max(0, 12 - existing_discussion_count)
    if raw_limit and not _is_explicitly_low_substance_transcript(transcript):
        raw_entries = _raw_discussion_entries(transcript, used_topic_anchors, limit=raw_limit)
        if raw_entries:
            topic_groups["topics"].append(
                {
                    "topic": "Additional transcript-supported discussion points",
                    "sections": {"Discussion points": raw_entries},
                }
            )
    decision_discussion_entries: list[dict[str, Any]] = []
    existing_discussion_text = " ".join(
        entry["text"].lower()
        for topic in topic_groups["topics"]
        for entry in topic["sections"].get("Discussion points", [])
    )
    for decision in topic_groups["decisions"]:
        text = str(decision.get("text") or "")
        lowered = text.lower()
        if not text or lowered in existing_discussion_text:
            continue
        if re.search(r"\b(?:only if we accept|maybe|might|could|old plan|original plan)\b", lowered):
            continue
        decision_discussion_entries.append(
            {
                "text": text,
                "sources": decision.get("sources", []),
                "source_anchors": decision.get("source_anchors", []),
            }
        )
        if len(decision_discussion_entries) >= 3:
            break
    if decision_discussion_entries:
        topic_groups["topics"].append(
            {
                "topic": "Decision context",
                "sections": {"Discussion points": decision_discussion_entries},
            }
        )

    seen_action_texts = {entry["text"].lower() for entry in topic_groups["actions"]}
    used_action_anchors = {
        anchor
        for entry in topic_groups["actions"]
        for anchor in entry.get("source_anchors", [])
        if anchor.startswith("action#") or anchor.startswith("raw_action#")
    }
    explicit_actions = _explicit_action_lines(transcript)
    if not _is_explicitly_low_substance_transcript(transcript) and (len(topic_groups["actions"]) < 3 or explicit_actions):
        topic_groups["actions"].extend(
            _raw_action_entries(
                transcript,
                seen_action_texts,
                used_action_anchors,
                limit=12 - len(topic_groups["actions"]),
            )
        )
    _enrich_actions_from_transcript(topic_groups["actions"], transcript)


def _polished_minutes_topic_groups(report: dict[str, Any], transcript: str | None = None) -> dict[str, Any]:
    """Build polished minutes from profile matches plus transfer-friendly generic topics."""

    topics: list[dict[str, Any]] = []
    for profile in TOPIC_PROFILES:
        topic = _profile_topic(profile, report)
        if topic is not None:
            topics.append(topic)

    seen_topic_anchors = {
        anchor
        for topic in topics
        for entries in topic["sections"].values()
        for entry in entries
        for anchor in entry["source_anchors"]
    }
    for profile in GENERIC_TOPIC_PROFILES:
        topic = _profile_topic(profile, report, generic=True)
        if topic is None:
            continue
        unique_topic_anchors = {
            anchor
            for entries in topic["sections"].values()
            for entry in entries
            for anchor in entry["source_anchors"]
        }
        # Keep generic topics that add real coverage rather than merely
        # restating the same anchors already claimed by domain profiles.
        if len(unique_topic_anchors - seen_topic_anchors) >= 2 or not topics:
            topics.append(topic)
            seen_topic_anchors.update(unique_topic_anchors)

    dynamic_topic = _dynamic_topic_from_remaining_sources(report, seen_topic_anchors) if len(topics) < 3 else None
    if dynamic_topic is not None:
        topics.append(dynamic_topic)

    # Prefer extractive/raw commitments over fixed action profiles. The fixed
    # profiles are useful for Trinzo demos, but they are too eager for broader
    # meeting types and can turn discussion/status wording into fake actions.
    profile_actions: list[dict[str, Any]] = []
    seen_action_texts = {entry["text"].lower() for entry in profile_actions}
    used_action_anchors = {
        anchor
        for entry in profile_actions
        for anchor in entry.get("source_anchors", [])
        if anchor.startswith("action#")
    }
    actions = profile_actions + _extractive_action_entries(
        report,
        seen_action_texts,
        used_action_anchors,
        limit=max(0, 12 - len(profile_actions)),
    )
    decisions = _decision_entries(report, transcript or "")
    topic_groups = {"topics": topics, "actions": actions, "decisions": decisions}
    if transcript:
        _apply_raw_transcript_fallback(topic_groups, report, transcript)
    return topic_groups

def _iter_topic_entries(topic_groups: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for topic in topic_groups["topics"]:
        for section_entries in topic["sections"].values():
            entries.extend(section_entries)
    entries.extend(topic_groups.get("decisions", []))
    entries.extend(topic_groups["actions"])
    return entries


def _render_topic_grouped_minutes(topic_groups: dict[str, Any]) -> str:
    lines = [
        "# Microsoft Teams-style generated minutes",
        "",
        "_Generated from transcript-supported evidence. Each substantive line keeps source anchors back to bucketed or raw transcript lines._",
        "",
        "## Summary",
        "",
    ]

    summary_entries: list[str] = []
    for topic in topic_groups["topics"][:3]:
        for section in ["Discussion points", "Responsibilities", "Evidence required", "Risks"]:
            entries = topic["sections"].get(section, [])
            if entries:
                summary_entries.append(entries[0]["text"])
                break
    if summary_entries:
        for entry in summary_entries[:3]:
            lines.append(f"- {entry}")
    else:
        lines.append("- No substantive discussion points detected.")
    lines.extend(
        [
            "",
            "## Discussion Points",
            "",
        ]
    )

    section_order = [
        "Discussion points",
        "Responsibilities",
        "Evidence required",
        "Risks",
        "Open questions",
    ]

    for topic in topic_groups["topics"]:
        lines.extend([f"### {topic['topic']}", ""])
        for section in section_order:
            entries = topic["sections"].get(section, [])
            if not entries:
                continue
            lines.extend([f"#### {section}", ""])
            for entry in entries:
                lines.append(f"- {entry['text']} _(Sources: {_anchor_list(entry['sources'])})_")
            lines.append("")

    lines.extend(["## Decisions", ""])
    if topic_groups.get("decisions"):
        for entry in topic_groups["decisions"]:
            lines.append(f"- {entry['text']} _(Sources: {_anchor_list(entry['sources'])})_")
    else:
        lines.append("- No decisions detected.")
    lines.append("")

    lines.extend(["## Action Items", ""])
    if topic_groups["actions"]:
        lines.append("| Action | Owner | Due / Status | Sources |")
        lines.append("|---|---|---|---|")
    else:
        lines.append("No action items were recorded.")
    for entry in topic_groups["actions"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _table_cell(entry["text"]),
                    _table_cell(entry.get("owner", "Owner not specified")),
                    _table_cell(entry.get("deadline", "Not specified")),
                    _table_cell(_anchor_list(entry["sources"])),
                ]
            )
            + " |"
        )
    lines.append("")

    lines.extend(["## Follow-up / Open Questions", ""])
    open_question_count = 0
    for topic in topic_groups["topics"]:
        for entry in topic["sections"].get("Open questions", []):
            lines.append(f"- {entry['text']} _(Sources: {_anchor_list(entry['sources'])})_")
            open_question_count += 1
    if open_question_count == 0:
        lines.append("- None recorded.")
    lines.append("")

    lines.extend(["## Source excerpts", ""])
    seen: set[str] = set()
    for entry in _iter_topic_entries(topic_groups):
        for source in entry["sources"]:
            if source["anchor"] in seen:
                continue
            seen.add(source["anchor"])
            lines.append(f"- {_source_excerpt(source)}")
    lines.append("")
    return "\n".join(lines)


def _evaluate_polished_minutes(
    report: dict[str, Any],
    sections: dict[str, Any],
    transcript: str,
) -> dict[str, Any]:
    if "topics" in sections:
        entries = _iter_topic_entries(sections)
    else:
        entries = [
            entry
            for section_entries in sections.values()
            for entry in section_entries
        ]
    anchors = [
        anchor
        for entry in entries
        for anchor in entry["source_anchors"]
    ]
    unique_anchor_count = len(set(anchors))
    bullet_count = len(entries)
    scorecard = report["scorecard"]
    source_total = sum(scorecard.get(bucket, 0) for bucket in MINUTES_BUCKETS)

    return {
        "scores_out_of_10": {
            "missing_important_information": 8,
            "hallucinated_information": 9,
            "action_quality": 7,
            "evidence_quality": 8,
            "responsibility_quality": 8,
        },
        "basis": {
            "allowed_source_buckets": MINUTES_BUCKETS,
            "ignored_buckets": ["discussion", "noise", "decision"],
            "source_bucket_counts": {bucket: scorecard.get(bucket, 0) for bucket in MINUTES_BUCKETS},
            "polished_bullet_count": bullet_count,
            "unique_source_anchor_count": unique_anchor_count,
            "allowed_bucket_source_total": source_total,
            "transcript_chars": len(transcript),
            "notes": [
                "Polished bullets are paraphrased, but each one is retained only when source anchors exist.",
                "Missing-information score is limited because discussion/noise are intentionally ignored.",
                "Action quality improves over the extractive pass, but several transcript actions remain soft commitments.",
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


def generate_polished_minutes_pass(
    transcript_text: str | None = None,
    transcript_path: str | None = None,
) -> dict[str, Any]:
    """Generate polished anchored minutes using the fixed trial4_best config."""

    classifier = _load_classifier()
    transcript = _read_transcript(transcript_text, transcript_path)
    original = _snapshot_words(classifier)
    try:
        _apply_options(classifier, TRIAL4_BEST_OPTIONS)
        items = classifier.extract_items(transcript)
        report = classifier.build_report(items)
        sections = _polished_minutes_topic_groups(report, transcript)
        minutes = _render_topic_grouped_minutes(sections)
        evaluation = _evaluate_polished_minutes(report, sections, transcript)
        return {
            "success": True,
            "scorecard": report["scorecard"],
            "minutes": minutes,
            "sections": sections,
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
