# Meeting Minutes Final Golden Comparison

- Runner: `/root/.openclaw/workspace/colab-tests-public/colab_experiment_runner.py`
- Golden pack: `/root/.openclaw/workspace/trinzo-upload/scripts/meeting-minutes-final-golden`
- Generated: `2026-06-24T20:08:13.685203+00:00`
- Cases: 20
- Passed: 0 / 20
- Average score: 0.671

## Category Averages

- abstention: 0.750
- actions: 0.417
- decisions: 0.733
- hallucinations: 0.877

## Failure Themes

- 25: action capture/count
- 19: abstention/count discipline
- 10: decision capture/count
- 8: forbidden/hallucinated content
- 5: visible output contains first-person wording
- 1: visible output contains timestamp/timecode

## Cases

### 001_decision_heavy_no_actions - FAIL - score 0.900 (threshold 0.90)
- Counts: decisions=2, actions=0, discussion=0
- decisions: missing 'legacy portal read-only for four weeks'

### 002_incident_actions_decision - FAIL - score 0.767 (threshold 0.85)
- Counts: decisions=1, actions=2, discussion=4
- actions: missing {'text': 'patch the mapper', 'owner': 'Liam', 'deadline': 'Today'}
- actions: missing {'text': 'notify customer success', 'owner': 'Noah'}
- quality: visible output contains first-person wording

### 003_low_substance_noise_abstention - FAIL - score 0.540 (threshold 1.00)
- Counts: decisions=0, actions=1, discussion=1
- actions: expected at most 0 items, got 1
- hallucinations: forbidden content present 'red light'
- abstention: expected actions <= 0, got 1
- abstention: expected discussion <= 0, got 1
- quality: visible output contains first-person wording

### 004_action_free_information_briefing - FAIL - score 0.767 (threshold 0.90)
- Counts: decisions=0, actions=0, discussion=0
- abstention: expected discussion >= 1, got 0
- abstention: missing discussion topic concepts ['travel', 'policy']
- abstention: missing discussion topic concepts ['mileage', 'July']
- abstention: missing discussion topic concepts ['guidance', 'intranet']

### 005_project_status_pending_leadership - FAIL - score 0.650 (threshold 0.85)
- Counts: decisions=0, actions=1, discussion=6
- actions: expected at least 4 items, got 1
- actions: missing 'review stage gate templates'
- actions: missing 'confirm AI pipeline dependencies with sales'
- actions: missing 'draft vendor strategy document'
- actions: missing 'follow up innovation grant feedback'

### 006_client_onboarding_split_rollout - FAIL - score 0.850 (threshold 0.85)
- Counts: decisions=1, actions=1, discussion=3
- actions: missing {'text': 'send the missing-field list', 'owner': 'Mina', 'deadline': 'Today'}

### 007_operations_review_internal_cover - FAIL - score 0.917 (threshold 0.85)
- Counts: decisions=1, actions=1, discussion=3
- hallucinations: forbidden content present 'hire temporary cover'
- quality: visible output contains first-person wording

### 008_sales_pipeline_review - FAIL - score 0.417 (threshold 0.85)
- Counts: decisions=0, actions=2, discussion=5
- decisions: expected at least 1 items, got 0
- decisions: missing 'focus on the retail and logistics accounts'
- actions: missing {'text': 'update the forecast', 'owner': 'Omar', 'deadline': 'Tuesday'}
- hallucinations: forbidden content present 'healthcare prospect this quarter'
- abstention: missing discussion topic concepts ['retail', 'logistics']

### 009_board_launch_delay - FAIL - score 0.567 (threshold 0.85)
- Counts: decisions=1, actions=2, discussion=2
- decisions: missing 'move the Spain launch to September'
- actions: missing {'text': 'update the board pack', 'owner': 'Leah', 'deadline': 'Tonight'}
- hallucinations: forbidden content present 'announce the Spain launch in July'
- abstention: missing discussion topic concepts ['partner paperwork']

### 010_webinar_rehearsal_trim - FAIL - score 0.683 (threshold 0.85)
- Counts: decisions=1, actions=0, discussion=4
- actions: expected at least 1 items, got 0
- actions: missing {'text': 'remove two bullets from the registration slide', 'owner': 'Jack'}
- abstention: missing discussion topic concepts ['live demo', 'seven minutes']

### 011_finance_budget_review - FAIL - score 0.850 (threshold 0.85)
- Counts: decisions=1, actions=1, discussion=2
- actions: missing {'text': 'send the revised forecast', 'owner': 'Hannah', 'deadline': 'Before lunch'}
- quality: visible output contains first-person wording

### 012_hiring_interview_debrief - FAIL - score 0.383 (threshold 0.90)
- Counts: decisions=0, actions=1, discussion=2
- decisions: expected at least 1 items, got 0
- decisions: missing 'invite Maya to the final interview'
- actions: expected at most 0 items, got 1
- abstention: expected actions <= 0, got 1

### 013_messy_speaker_timestamp_formats - FAIL - score 0.787 (threshold 0.85)
- Counts: decisions=1, actions=2, discussion=4
- actions: missing {'text': 'request the insurance certificate', 'owner': 'Ravi', 'deadline': 'Friday'}
- hallucinations: forbidden content present '09:00'
- quality: visible output contains timestamp/timecode
- quality: visible output contains first-person wording

### 014_status_update_discussion_only - FAIL - score 0.750 (threshold 0.90)
- Counts: decisions=0, actions=1, discussion=4
- actions: expected at most 0 items, got 1
- abstention: expected actions <= 0, got 1

### 015_hidden_decision_meeting - FAIL - score 0.717 (threshold 0.85)
- Counts: decisions=1, actions=2, discussion=3
- actions: missing {'text': 'reschedule the weekly check-in', 'owner': 'David', 'deadline': 'Today'}
- hallucinations: forbidden content present 'Grace will attend the usual check-in'
- abstention: missing discussion topic concepts ['Grace', 'offsite']

### 016_document_review_discussion_only - FAIL - score 0.742 (threshold 0.90)
- Counts: decisions=1, actions=0, discussion=4
- decisions: expected at most 0 items, got 1
- abstention: expected decisions <= 0, got 1

### 017_dependency_risk_discussion_only - FAIL - score 0.730 (threshold 0.90)
- Counts: decisions=0, actions=1, discussion=4
- actions: expected at most 0 items, got 1
- abstention: expected actions <= 0, got 1

### 018_support_metrics_action_heavy - FAIL - score 0.400 (threshold 0.85)
- Counts: decisions=0, actions=0, discussion=1
- actions: expected at least 3 items, got 0
- actions: missing 'separate triage categories'
- actions: missing 'monitor the results weekly'
- actions: missing 'set up a dashboard'
- abstention: expected discussion >= 2, got 1
- abstention: missing discussion topic concepts ['support metrics']
- abstention: missing discussion topic concepts ['complex cases', 'simple requests']
- abstention: missing discussion topic concepts ['onboarding guide']

### 019_contract_negotiation_review - FAIL - score 0.458 (threshold 0.85)
- Counts: decisions=1, actions=1, discussion=2
- decisions: missing 'sign the one-year extension'
- actions: missing {'text': 'redline the exit clause', 'owner': 'Jon', 'deadline': 'Friday'}
- hallucinations: forbidden content present 'three-year commitment'
- hallucinations: forbidden content present 'exit clause unchanged'
- abstention: missing discussion topic concepts ['contract term length']

### 020_customer_complaint_review - FAIL - score 0.550 (threshold 0.85)
- Counts: decisions=0, actions=2, discussion=2
- decisions: expected at least 1 items, got 0
- decisions: missing 'refund the last invoice'
- actions: missing {'text': 'call the customer', 'owner': 'Dan', 'deadline': 'Noon'}
