# Trinzo Upload Fixture Transfer Evaluation

- Generated at: 2026-06-24T20:44:03.244379+00:00
- Runner: `/root/.openclaw/workspace/colab-tests-public/colab_experiment_runner.py`
- Fixture root: `/root/.openclaw/workspace/trinzo-upload/scripts/transcript-tests`
- Cases: 74
- Passed: 30 / 74
- Total failures: 163

## Failures

| Case | Counts | Failure count | First failures |
|---|---|---:|---|
| `001_status_review` | actions=7, decisions=1, discussionPoints=23 | 5 | expected 5 actions, got 7<br>expected 0 decisions, got 1<br>missing discussion topic concepts ['sales input']<br>missing discussion topic concepts ['vendor strategy'] |
| `002_validation_decision` | actions=0, decisions=0, discussionPoints=5 | 3 | expected 1 decisions, got 0<br>missing discussion topic concepts ['validation-specific', 'broad']<br>missing decision 'remain broad rather than validation-specific' |
| `003_webinar_rehearsal` | actions=6, decisions=1, discussionPoints=43 | 1 | expected 0 decisions, got 1 |
| `004_contract_renewal` | actions=1, decisions=0, discussionPoints=4 | 4 | expected 0 actions, got 1<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['renew with the existing supplier']<br>missing decision 'renew with the existing supplier' |
| `005_office_relocation` | actions=4, decisions=0, discussionPoints=5 | 1 | expected 2 actions, got 4 |
| `006_product_bug_triage` | actions=1, decisions=0, discussionPoints=3 | 2 | expected 2 actions, got 1<br>missing action 'reproduce it on Safari and capture logs by 3pm' |
| `007_client_onboarding` | actions=0, decisions=0, discussionPoints=4 | 3 | expected 1 decisions, got 0<br>missing discussion topic concepts ['finance first']<br>missing decision 'begin onboarding with finance first' |
| `008_event_planning` | actions=0, decisions=0, discussionPoints=4 | 2 | expected 1 decisions, got 0<br>missing decision 'switch the workshop to the larger auditorium' |
| `009_supplier_risk_review` | actions=1, decisions=0, discussionPoints=3 | 4 | expected 0 actions, got 1<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['buffer stock']<br>missing decision 'stay with the current supplier for Q4' |
| `011_hiring_interview_debrief` | actions=1, decisions=0, discussionPoints=2 | 4 | expected 0 actions, got 1<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['make an offer to Priya']<br>missing decision 'make an offer to Priya' |
| `012_training_rollout` | actions=1, decisions=1, discussionPoints=4 | 4 | expected 2 actions, got 1<br>expected 0 decisions, got 1<br>missing action 'split the material into two forty-five minute sessions'<br>missing action 'publish the revised timetable by Thursday' |
| `015_ownership_assignment` | actions=0, decisions=0, discussionPoints=1 | 2 | expected 1 actions, got 0<br>missing action 'handle the negotiation' |
| `016_investigation_commitment` | actions=0, decisions=0, discussionPoints=0 | 2 | expected 1 actions, got 0<br>missing action 'reproduce it on safari' |
| `019_supplier_review` | actions=2, decisions=0, discussionPoints=3 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'stay with the current supplier for Q1' |
| `022_candidate_screening` | actions=1, decisions=0, discussionPoints=1 | 2 | expected 1 decisions, got 0<br>missing decision 'not progress Ben to interview this round' |
| `024_board_update` | actions=0, decisions=1, discussionPoints=3 | 2 | expected 1 actions, got 0<br>missing action 'tighten the churn narrative before Thursday' |
| `026_product_bug_triage` | actions=1, decisions=0, discussionPoints=2 | 3 | expected 1 decisions, got 0<br>missing action 'verify the checkout flow before release'<br>missing decision 'ship the hotfix behind a feature flag' |
| `028_customer_onboarding` | actions=2, decisions=0, discussionPoints=2 | 4 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['defer SSO until phase two']<br>missing decision 'begin onboarding with CSV import first' |
| `032_training_rollout` | actions=1, decisions=1, discussionPoints=4 | 3 | expected 2 actions, got 1<br>missing action 'split the material into two forty-minute sessions'<br>missing action 'publish the revised timetable by Thursday' |
| `035_procurement_discussion` | actions=2, decisions=0, discussionPoints=2 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'buy the lower-volume option first' |
| `036_project_retrospective` | actions=1, decisions=0, discussionPoints=2 | 2 | expected 1 decisions, got 0<br>missing decision 'drop the Friday standup' |
| `037_partnership_discussion` | actions=2, decisions=0, discussionPoints=3 | 4 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['ninety-day pilot']<br>missing decision 'run a ninety-day pilot' |
| `038_grant_application_review` | actions=3, decisions=0, discussionPoints=3 | 3 | expected 1 actions, got 3<br>expected 1 decisions, got 0<br>missing decision 'submit the digital-health angle' |
| `039_risk_review` | actions=2, decisions=0, discussionPoints=2 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'escalate that dependency to red' |
| `040_governance_review` | actions=0, decisions=1, discussionPoints=3 | 2 | expected 1 actions, got 0<br>missing action 'circulate the final draft this afternoon' |
| `042_support_escalation_review` | actions=2, decisions=0, discussionPoints=2 | 4 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['replace the workaround article with a direct escalation path']<br>missing decision 'replace the workaround article with a direct escalation path' |
| `043_release_go_no_go` | actions=2, decisions=0, discussionPoints=2 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'delay the Friday release until QA confirms the fix' |
| `046_customer_onboarding_split_rollout` | actions=1, decisions=1, discussionPoints=4 | 1 | forbidden decision present 'start warehouse onboarding first' |
| `047_supplier_renewal_rejection` | actions=2, decisions=0, discussionPoints=3 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'renew with the existing supplier' |
| `049_low_substance_noise` | actions=0, decisions=0, discussionPoints=1 | 1 | forbidden content present 'run through the agenda' |
| `050_partnership_mou_enablement` | actions=3, decisions=1, discussionPoints=5 | 2 | expected 2 actions, got 3<br>forbidden decision present 'sign the reseller clause this month' |
| `051_real_webinar_rehearsal` | actions=6, decisions=1, discussionPoints=43 | 24 | missing discussion point 'The team reviewed the webinar agenda, including the introduction, AI discovery workshop methodology, case study, and live demonstration.'<br>missing discussion point 'The importance of starting AI initiatives with clearly defined business problems was discussed as a key factor in improving adoption.'<br>missing discussion point 'The AI discovery workshop approach was reviewed, including Define, Measure, Analyse, Improve and Control stages.'<br>missing discussion point 'Workshop delivery was discussed as a highly collaborative process driven by employees who perform the work and understand the workflow.' |
| `053_hidden_decision_meeting` | actions=1, decisions=1, discussionPoints=5 | 1 | forbidden decision present 'cancel the weekly check-in' |
| `056_progress_dashboard_meeting` | actions=0, decisions=0, discussionPoints=4 | 2 | expected 1 actions, got 0<br>missing action 'keep the tracker updated' |
| `057_rehearsal_banter_filter` | actions=1, decisions=0, discussionPoints=2 | 4 | expected 0 actions, got 1<br>forbidden content present 'take your top off'<br>forbidden content present 'vape'<br>forbidden content present 'talk french' |
| `059_partial_completion_allowed` | actions=2, decisions=0, discussionPoints=2 | 2 | expected 1 actions, got 2<br>missing action 'share the updated clinical trace matrix and related documents for review, even if not fully complete' |
| `060_external_review_optional` | actions=1, decisions=0, discussionPoints=2 | 2 | expected 0 actions, got 1<br>missing discussion topic concepts ['external', 'cer', 'review'] |
| `061_no_major_impact_dependency` | actions=2, decisions=0, discussionPoints=3 | 1 | expected 0 actions, got 2 |
| `063_rejection_test` | actions=0, decisions=0, discussionPoints=1 | 1 | missing discussion topic concepts ['slides', 'friday'] |
| `064_analytics_review` | actions=12, decisions=1, discussionPoints=23 | 32 | missing discussion point 'The team discussed pressure from ONT to provide clearer analytics, including historic data from London 2024 and 2025, despite gaps caused by GDPR-related analytics deletion.'<br>missing discussion point 'Time on platform remains difficult to define because some delegates leave tabs open while others show zero recorded duration despite clear platform activity.'<br>missing discussion point 'A more accurate engagement-time method has been created using first click, last click and inactivity thresholds, giving an estimated average of around 45 minutes per person.'<br>missing discussion point 'The current eight-hour time-on-platform figure remains useful for comparability with previous years.' |
| `064_status_setup_clause_rejected` | actions=0, decisions=0, discussionPoints=1 | 1 | forbidden content present "The I've got the latest report open remains" |
| `066_status_misrecognized_setup_rejected` | actions=0, decisions=0, discussionPoints=1 | 1 | forbidden content present 'The I got report open remains blocked' |
| `067_banana_falcon_client_ready` | actions=0, decisions=2, discussionPoints=14 | 4 | expected at least 3 actions, got 0<br>missing action 'work out which dashboard'<br>missing action 'investigate server restart'<br>missing action 'investigate API numbers' |
| `073_support_metrics_actions` | actions=4, decisions=0, discussionPoints=15 | 3 | forbidden content present 'James:'<br>forbidden content present 'Rachel:'<br>forbidden content present 'Mark:' |
