# Colab tests public

Public Python entry points for Colab experiments that need to be fetched by URL.

This repo is intentionally small and public so a Colab runtime can use `execute_python_url`
without GitHub authentication.

## MiniLM evidence graph experiment

Runner URL:

```text
https://raw.githubusercontent.com/clairenicholsondigital/colab-tests-public/main/colab_experiment_runner.py
```

Pinned tested runner URL:

```text
https://raw.githubusercontent.com/clairenicholsondigital/colab-tests-public/325f5db/colab_experiment_runner.py
```

Classifier dependency URL:

```text
https://raw.githubusercontent.com/clairenicholsondigital/colab-tests-public/main/minilm_evidence_graph.py
```

Example `/process` payload:

```json
{
  "task": "execute_python_url",
  "text": "",
  "options": {
    "url": "https://raw.githubusercontent.com/clairenicholsondigital/colab-tests-public/325f5db/colab_experiment_runner.py",
    "function": "run_analysis",
    "args": [],
    "kwargs": {
      "transcript_text": "PASTE TRANSCRIPT HERE",
      "discussion_sample_limit": 40
    }
  }
}
```

The canonical working repo remains `clairenicholsondigital/google-colab-mini-lm`.
This public repo is the unauthenticated URL mirror for Colab execution.

## Current classifier layer

The default `trial4_best` config is now fixed. The classifier adds a second
layer based on audited examples:

- `noise`
- `process_flow`
- `evidence_request`
- `evidence_artifact`
- stricter `action`

Responsibilities still take priority over action/evidence wording.

## Minutes passes

Two callable minutes entry points are available:

- `generate_minutes_pass` returns extractive minutes from the allowed buckets.
- `generate_polished_minutes_pass` returns cleaner minutes with source anchors
  for each bullet.

Both minutes passes only use these buckets:

- `responsibility`
- `evidence_artifact`
- `evidence_request`
- `action`
- `risk`
- `question`
- `process_flow`

They deliberately ignore `discussion` and `noise`.
