# Trinzo Upload Fixture Transfer Evaluation

- Generated at: 2026-06-24T22:38:01.131456+00:00
- Runner: `/root/.openclaw/workspace/colab-tests-public/colab_experiment_runner.py`
- Fixture root: `/root/.openclaw/workspace/trinzo-upload/scripts/transcript-tests`
- Cases: 74
- Passed: 49 / 74
- Total failures: 96

## Failures

| Case | Counts | Failure count | First failures |
|---|---|---:|---|
| `001_status_review` | actions=5, decisions=1, discussionPoints=23 | 4 | expected 0 decisions, got 1<br>missing discussion topic concepts ['sales input']<br>missing discussion topic concepts ['vendor strategy']<br>missing discussion topic concepts ['leadership review'] |
| `002_validation_decision` | actions=0, decisions=0, discussionPoints=5 | 3 | expected 1 decisions, got 0<br>missing discussion topic concepts ['validation-specific', 'broad']<br>missing decision 'remain broad rather than validation-specific' |
| `003_webinar_rehearsal` | actions=6, decisions=1, discussionPoints=23 | 1 | expected 0 decisions, got 1 |
| `005_office_relocation` | actions=3, decisions=0, discussionPoints=5 | 1 | expected 2 actions, got 3 |
| `006_product_bug_triage` | actions=2, decisions=1, discussionPoints=4 | 1 | expected 0 decisions, got 1 |
| `007_client_onboarding` | actions=0, decisions=2, discussionPoints=6 | 1 | expected 1 decisions, got 2 |
| `012_training_rollout` | actions=2, decisions=1, discussionPoints=4 | 1 | expected 0 decisions, got 1 |
| `026_product_bug_triage` | actions=0, decisions=1, discussionPoints=3 | 2 | expected 1 actions, got 0<br>missing action 'verify the checkout flow before release' |
| `028_customer_onboarding` | actions=1, decisions=2, discussionPoints=4 | 1 | expected 1 decisions, got 2 |
| `043_release_go_no_go` | actions=2, decisions=1, discussionPoints=3 | 2 | expected 1 actions, got 2<br>forbidden decision present 'ship the Friday release' |
| `046_customer_onboarding_split_rollout` | actions=1, decisions=1, discussionPoints=4 | 1 | forbidden decision present 'start warehouse onboarding first' |
| `049_low_substance_noise` | actions=0, decisions=1, discussionPoints=1 | 3 | expected 0 decisions, got 1<br>forbidden content present 'run through the agenda'<br>forbidden decision present 'run through the agenda' |
| `050_partnership_mou_enablement` | actions=2, decisions=1, discussionPoints=5 | 1 | forbidden decision present 'sign the reseller clause this month' |
| `051_real_webinar_rehearsal` | actions=6, decisions=1, discussionPoints=23 | 24 | missing discussion point 'The team reviewed the webinar agenda, including the introduction, AI discovery workshop methodology, case study, and live demonstration.'<br>missing discussion point 'The importance of starting AI initiatives with clearly defined business problems was discussed as a key factor in improving adoption.'<br>missing discussion point 'The AI discovery workshop approach was reviewed, including Define, Measure, Analyse, Improve and Control stages.'<br>missing discussion point 'Workshop delivery was discussed as a highly collaborative process driven by employees who perform the work and understand the workflow.' |
| `053_hidden_decision_meeting` | actions=1, decisions=2, discussionPoints=6 | 2 | expected 1 decisions, got 2<br>forbidden decision present 'cancel the weekly check-in' |
| `056_progress_dashboard_meeting` | actions=0, decisions=0, discussionPoints=4 | 2 | expected 1 actions, got 0<br>missing action 'keep the tracker updated' |
| `057_rehearsal_banter_filter` | actions=1, decisions=0, discussionPoints=2 | 4 | expected 0 actions, got 1<br>forbidden content present 'take your top off'<br>forbidden content present 'vape'<br>forbidden content present 'talk french' |
| `059_partial_completion_allowed` | actions=1, decisions=0, discussionPoints=2 | 1 | missing action 'share the updated clinical trace matrix and related documents for review, even if not fully complete' |
| `060_external_review_optional` | actions=0, decisions=0, discussionPoints=2 | 1 | missing discussion topic concepts ['external', 'cer', 'review'] |
| `061_no_major_impact_dependency` | actions=1, decisions=0, discussionPoints=3 | 1 | expected 0 actions, got 1 |
| `063_rejection_test` | actions=0, decisions=0, discussionPoints=1 | 1 | missing discussion topic concepts ['slides', 'friday'] |
| `064_analytics_review` | actions=11, decisions=1, discussionPoints=14 | 32 | missing discussion point 'The team discussed pressure from ONT to provide clearer analytics, including historic data from London 2024 and 2025, despite gaps caused by GDPR-related analytics deletion.'<br>missing discussion point 'Time on platform remains difficult to define because some delegates leave tabs open while others show zero recorded duration despite clear platform activity.'<br>missing discussion point 'A more accurate engagement-time method has been created using first click, last click and inactivity thresholds, giving an estimated average of around 45 minutes per person.'<br>missing discussion point 'The current eight-hour time-on-platform figure remains useful for comparability with previous years.' |
| `064_status_setup_clause_rejected` | actions=0, decisions=0, discussionPoints=1 | 1 | forbidden content present "The I've got the latest report open remains" |
| `066_status_misrecognized_setup_rejected` | actions=0, decisions=0, discussionPoints=1 | 1 | forbidden content present 'The I got report open remains blocked' |
| `067_banana_falcon_client_ready` | actions=0, decisions=2, discussionPoints=14 | 4 | expected at least 3 actions, got 0<br>missing action 'work out which dashboard'<br>missing action 'investigate server restart'<br>missing action 'investigate API numbers' |
