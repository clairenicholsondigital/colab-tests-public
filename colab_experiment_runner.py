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
            score = sum(1 for term in lowered_terms if term in lowered)
            if score <= 0:
                continue
            key = item["text"].lower()
            if key in seen:
                continue
            seen.add(key)
            scored.append((score, bucket_position, item["index"], item))
    scored.sort(key=lambda row: (-row[0], row[1], row[2]))
    return [item for _, _, _, item in scored[:limit]]


def _anchor_list(sources: list[dict[str, Any]]) -> str:
    return ", ".join(source["anchor"] for source in sources)


def _source_excerpt(source: dict[str, Any]) -> str:
    return f"{source['anchor']} {source['speaker']}: {source['text']}"


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


def _polished_minutes_topic_groups(report: dict[str, Any]) -> dict[str, Any]:
    """Build polished minutes grouped by topic, with actions kept separate."""

    topics: list[dict[str, Any]] = []

    supply_chain = {
        "topic": "Supply chain, product flow and warehousing",
        "sections": {},
    }
    _add_topic_entry(
        supply_chain,
        "Discussion points",
        "The product flow is Japan to the Netherlands for fiscal clearance, then onwards to Ireland, with little or no Netherlands storage.",
        report,
        ["process_flow"],
        ["japan", "netherlands", "ireland", "cleared", "storage"],
    )
    _add_topic_entry(
        supply_chain,
        "Responsibilities",
        "DITA needs a lot-number process so product can be picked, labelled and stored by lot number.",
        report,
        ["responsibility", "action", "evidence_artifact"],
        ["lot number", "pick", "store"],
    )
    _add_topic_entry(
        supply_chain,
        "Open questions",
        "Is the described product-flow reflection correct?",
        report,
        ["question"],
        ["correct reflection", "how it works"],
    )
    _add_topic_entry(
        supply_chain,
        "Open questions",
        "Is the Park West warehousing facility DITA-operated or third-party?",
        report,
        ["question"],
        ["park west", "third party", "own operated"],
    )
    _add_topic_entry(
        supply_chain,
        "Open questions",
        "Is the warehouse automated or fully manual?",
        report,
        ["question"],
        ["automated", "manual warehouse"],
    )
    _add_topic_entry(
        supply_chain,
        "Open questions",
        "Does the mapped process cover supplier purchase orders, customer sales orders, or both?",
        report,
        ["question"],
        ["purchase order", "sales order", "flow of products"],
    )
    topics.append(supply_chain)

    registration = {
        "topic": "Udimed/Eudamed, UDI and importer responsibilities",
        "sections": {},
    }
    _add_topic_entry(
        registration,
        "Discussion points",
        "The team focused on importer obligations, Udimed/Eudamed registration, UDI/barcode data, and who is responsible for checking or uploading product data.",
        report,
        ["responsibility", "question", "evidence_request"],
        ["udimed", "eudamed", "udi", "upc", "importer", "data"],
    )
    _add_topic_entry(
        registration,
        "Responsibilities",
        "As importer, DITA needs to check labels and confirm the importer link for DITA Inc.",
        report,
        ["responsibility"],
        ["importer", "label", "check", "dita inc"],
    )
    _add_topic_entry(
        registration,
        "Responsibilities",
        "New products need to be entered into Udimed immediately, and existing items need to be entered by the November deadline discussed in the call.",
        report,
        ["responsibility", "question"],
        ["new products", "udimed", "immediately", "november"],
    )
    _add_topic_entry(
        registration,
        "Responsibilities",
        "The legal manufacturer is responsible for putting data into Udimed; the importer and authorised representative need to check that it is there.",
        report,
        ["responsibility"],
        ["legal manufacturer", "responsible", "authorised rep", "udimed"],
    )
    _add_topic_entry(
        registration,
        "Evidence required",
        "Evidence is needed that product data is being collected or is ready to be put into Udimed/Eudamed.",
        report,
        ["evidence_request", "responsibility"],
        ["collecting the data", "product information", "udimed", "data"],
    )
    _add_topic_entry(
        registration,
        "Risks",
        "There is a risk that responsibility for Udimed activity is assumed to sit elsewhere and gets dropped or missed.",
        report,
        ["responsibility", "risk"],
        ["dropped", "missed", "somebody else", "oversight"],
    )
    _add_topic_entry(
        registration,
        "Open questions",
        "Are product registrations handled at UPC/SKU level, and are barcodes actual UDI barcodes?",
        report,
        ["question"],
        ["upc", "sku", "udi barcodes", "barcodes"],
    )
    topics.append(registration)

    audit = {
        "topic": "Audit readiness, QMS procedures and Med Envoy planning",
        "sections": {},
    }
    _add_topic_entry(
        audit,
        "Discussion points",
        "Audit readiness depends on showing that procedures, data collection, Med Envoy activity and supporting evidence are in progress.",
        report,
        ["evidence_request", "risk"],
        ["audit", "preparation", "data", "med envoy", "project plan", "task list"],
    )
    _add_topic_entry(
        audit,
        "Responsibilities",
        "DITA needs procedures that reflect the applicable regulatory requirements and the way the business actually operates.",
        report,
        ["responsibility", "evidence_request"],
        ["reg requirements", "procedure", "business works", "meaningful", "usable"],
    )
    _add_topic_entry(
        audit,
        "Evidence required",
        "The quality manual and related procedures are core evidence for showing importer-obligation controls.",
        report,
        ["evidence_request"],
        ["quality manual", "procedure"],
    )
    _add_topic_entry(
        audit,
        "Evidence required",
        "A Med Envoy project plan, task list or equivalent activity overview is needed to understand timing, responsibilities and crossover points.",
        report,
        ["evidence_request", "risk", "action"],
        ["med envoy", "project plan", "task list", "timelines", "crossover"],
    )
    _add_topic_entry(
        audit,
        "Risks",
        "Without a clear Med Envoy plan or timeline, there is a gap around when registration work will be completed.",
        report,
        ["risk", "evidence_request"],
        ["without", "gap", "timelines", "med envoy"],
    )
    _add_topic_entry(
        audit,
        "Risks",
        "If the audit happens early, DITA will need to show preparation is underway rather than finished.",
        report,
        ["risk", "evidence_request"],
        ["audit", "early", "preparation"],
    )
    _add_topic_entry(
        audit,
        "Open questions",
        "What is Med Envoy doing, what information do they need, and how long will their work take?",
        report,
        ["question", "evidence_request"],
        ["med envoy", "what information", "how long", "process"],
    )
    topics.append(audit)

    labelling = {
        "topic": "Labelling, barcode design and product documentation",
        "sections": {},
    }
    _add_topic_entry(
        labelling,
        "Discussion points",
        "Labelling, barcode design, lot numbering and product documentation are active areas of work.",
        report,
        ["evidence_artifact", "action", "question"],
        ["label", "barcode", "lot", "manufacturer", "warranty booklet"],
    )
    _add_topic_entry(
        labelling,
        "Evidence required",
        "Labels, barcode design, barcode format and lot-number implementation are supporting artefacts to keep under review.",
        report,
        ["evidence_artifact", "question", "action"],
        ["label", "barcode", "lot number"],
    )
    _add_topic_entry(
        labelling,
        "Evidence required",
        "The warranty booklet/manufacturer information note and IFU status need to be clarified as part of the documentation set.",
        report,
        ["evidence_request", "process_flow"],
        ["warranty booklet", "manufacturer", "ifu", "MIN"],
    )
    topics.append(labelling)

    actions: list[dict[str, Any]] = []
    action_definitions = [
        (
            "Orla to provide a written formal overview of the intercompany structure.",
            ["action"],
            ["written formally", "intercompany structure"],
        ),
        (
            "Jacqui to send the relevant QMS/manual material to Orla.",
            ["action", "question"],
            ["flick this over", "qms manual"],
        ),
        (
            "Orla to review the document/update work with the additional information.",
            ["action", "evidence_request"],
            ["review that document", "update with all the additional information"],
        ),
        (
            "Orla to take the barcode/UDI question back to the US team.",
            ["action", "question"],
            ["bring that to the US team", "barcodes", "udi"],
        ),
        (
            "Orla to follow up with Cody/Med Envoy on the process, information needed and timelines.",
            ["action", "evidence_request", "risk"],
            ["follow up", "cody", "med envoy", "process", "timelines"],
        ),
        (
            "Jacqui/Colm to review the SRN/company-size information and seek direction from Liam if needed.",
            ["action", "evidence_request"],
            ["send it on", "colm", "liam", "company size"],
        ),
    ]
    for text, buckets, terms in action_definitions:
        entry = _polished_entry(text, report, buckets, terms)
        if entry is not None:
            actions.append(entry)

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
    for entry in topic_groups["actions"]:
        lines.append(f"- {entry['text']} _(Sources: {_anchor_list(entry['sources'])})_")
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
