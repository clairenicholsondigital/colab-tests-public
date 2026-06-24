# Microsoft Teams Fixture Evaluation

- Generated at: 2026-06-24T20:02:48.898462+00:00
- Runner: `/root/.openclaw/workspace/colab-tests-public/colab_experiment_runner.py`
- Runner path: `/root/.openclaw/workspace/colab-tests-public/colab_experiment_runner.py`
- Fixture root: `/root/.openclaw/workspace/colab-tests-public/fixtures/microsoft-teams-minutes`
- Cases: 10
- Passed: 6 / 10
- Average score: 0.830

## Case Results

| Case | Type | Score | Pass | Key notes |
|---|---|---:|:---:|---|
| `001_status_review` | project_status_review | 0.500 | no | Missed topics: sales dependency<br>Action count expected 5, generated 7 |
| `002_decision_only_validation` | decision_review | 0.778 | no | Missed topics: validation positioning<br>Decision count expected 2, generated 1 |
| `003_bug_triage` | incident_bug_triage | 0.889 | yes | Core checks passed. |
| `004_webinar_rehearsal` | webinar_rehearsal | 0.500 | no | Missed topics: demo framing<br>Action count expected 6, generated 10 |
| `005_finance_budget` | finance_budget_review | 0.926 | yes | Missed topics: contractor spend |
| `006_client_onboarding` | client_onboarding | 1.000 | yes | Core checks passed. |
| `007_support_metrics` | support_metrics_review | 0.889 | yes | Action count expected 3, generated 4 |
| `008_action_free_briefing` | information_briefing | 1.000 | yes | Core checks passed. |
| `009_noisy_low_substance` | low_substance | 1.000 | yes | Core checks passed. |
| `010_supplier_risk` | supplier_risk_review | 0.815 | no | Missed topics: SLA update<br>Decision count expected 2, generated 1 |

## Score Categories

- `topics`: expected topic phrases or their important words appear in generated minutes.
- `action_count`: generated action row count matches, or is within one for partial credit.
- `owners`: expected action owners appear in generated minutes.
- `due_status`: expected due/status values appear in generated minutes.
- `decisions`: generated decision count matches expected decision count.
- `no_false_actions`: no action rows are produced for action-free fixtures.
- `teams_structure`: generated output contains Teams-style sections.

This is a regression signal, not a full human-quality judgement.
