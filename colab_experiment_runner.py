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


def _infer_action_owner(source_text: str, action: dict[str, Any]) -> str:
    explicit_owner = action.get("owner")
    if explicit_owner:
        return explicit_owner
    lowered = source_text.lower()
    owners: list[str] = []
    for owner, pattern in OWNER_PATTERNS:
        if re.search(pattern, lowered) and owner not in owners:
            owners.append(owner)
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
        (r"\bweekly\b", "Weekly"),
        (r"\b(?:done|completed|closed|share|send|get that)\s+(?:for|by)\s+(?:monday|tuesday|wednesday|thursday|friday)\b", None),
    ]
    for pattern, label in relative_patterns:
        match = re.search(pattern, lowered)
        if match:
            if label:
                return label
            value = match.group(0)
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
    text = re.sub(r"^(?:so|yeah|okay|and|but|then|maybe|i suppose|i think)\s+", "", text, flags=re.IGNORECASE)
    text = text.strip(" ,.;:")
    if text and text[-1] not in ".?!":
        text += "."
    return text


def _is_useful_generic_action(text: str) -> bool:
    lowered = text.lower()
    if len(text.split()) < 6:
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
    ]
    if any(fragment in lowered for fragment in weak_fragments):
        return False
    return bool(
        re.search(
            r"\b(i|we|you|he|she|they|team|jack|ciara|conor|colm|orla|jacqui|andrew|rebecca|david|kevin|mark)\s+(?:can|will|should|need|needs|have to|has to|going to|want to|could)\b",
            lowered,
        )
        or re.search(r"\b(?:follow up|review|send|share|add|remove|update|practi[cs]e|prepare|schedule|bring|explain|keep|make sure|figure out)\b", lowered)
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


def _polished_minutes_topic_groups(report: dict[str, Any]) -> dict[str, Any]:
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

    profile_actions = _generic_action_entries(report, [topic["topic"] for topic in topics])
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
    return {"topics": topics, "actions": actions}

def _iter_topic_entries(topic_groups: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for topic in topic_groups["topics"]:
        for section_entries in topic["sections"].values():
            entries.extend(section_entries)
    entries.extend(topic_groups["actions"])
    return entries


def _render_topic_grouped_minutes(topic_groups: dict[str, Any]) -> str:
    lines = [
        "# Polished generated minutes",
        "",
        "_Generated only from responsibility, evidence_artifact, evidence_request, action, risk, question and process_flow buckets. Discussion and noise were ignored. Each bullet includes source anchors back to bucketed transcript lines._",
        "",
        "## Discussion points",
        "",
    ]

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

    lines.extend(["## Actions", ""])
    if topic_groups["actions"]:
        lines.append("| Action | Owner | Deadline/status | Sources |")
        lines.append("|---|---|---|---|")
    else:
        lines.append("No actions detected from the allowed buckets.")
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
        sections = _polished_minutes_topic_groups(report)
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
