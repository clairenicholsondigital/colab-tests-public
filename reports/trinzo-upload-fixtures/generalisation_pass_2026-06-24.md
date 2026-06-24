# Trinzo Upload Fixture Transfer Evaluation

- Generated at: 2026-06-24T20:00:54.316576+00:00
- Runner: `/root/.openclaw/workspace/colab-tests-public/colab_experiment_runner.py`
- Fixture root: `/root/.openclaw/workspace/trinzo-upload/scripts/transcript-tests`
- Cases: 74
- Passed: 14 / 74
- Total failures: 215

## Failures

| Case | Counts | Failure count | First failures |
|---|---|---:|---|
| `001_status_review` | actions=8, decisions=1, discussionPoints=13 | 6 | expected 5 actions, got 8<br>expected 0 decisions, got 1<br>missing discussion topic concepts ['routing']<br>missing discussion topic concepts ['sales input'] |
| `002_validation_decision` | actions=0, decisions=0, discussionPoints=6 | 2 | expected 1 decisions, got 0<br>missing decision 'remain broad rather than validation-specific' |
| `003_webinar_rehearsal` | actions=6, decisions=3, discussionPoints=36 | 2 | expected 0 decisions, got 3<br>missing discussion topic concepts ['workshop'] |
| `004_contract_renewal` | actions=1, decisions=0, discussionPoints=4 | 4 | expected 0 actions, got 1<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['renew with the existing supplier']<br>missing decision 'renew with the existing supplier' |
| `005_office_relocation` | actions=3, decisions=0, discussionPoints=7 | 1 | expected 2 actions, got 3 |
| `006_product_bug_triage` | actions=2, decisions=1, discussionPoints=3 | 1 | expected 0 decisions, got 1 |
| `007_client_onboarding` | actions=1, decisions=0, discussionPoints=4 | 4 | expected 0 actions, got 1<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['finance first']<br>missing decision 'begin onboarding with finance first' |
| `008_event_planning` | actions=0, decisions=0, discussionPoints=4 | 2 | expected 1 decisions, got 0<br>missing decision 'switch the workshop to the larger auditorium' |
| `009_supplier_risk_review` | actions=1, decisions=1, discussionPoints=3 | 2 | expected 0 actions, got 1<br>missing discussion topic concepts ['buffer stock'] |
| `010_finance_budget_review` | actions=1, decisions=1, discussionPoints=2 | 1 | missing discussion topic concepts ['defer the analytics hire until Q4'] |
| `011_hiring_interview_debrief` | actions=1, decisions=0, discussionPoints=2 | 4 | expected 0 actions, got 1<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['make an offer to Priya']<br>missing decision 'make an offer to Priya' |
| `012_training_rollout` | actions=2, decisions=1, discussionPoints=3 | 3 | expected 0 decisions, got 1<br>missing discussion topic concepts ['pilot group to the Manchester site']<br>missing action 'split the material into two forty-five minute sessions' |
| `014_request_acceptance` | actions=1, decisions=0, discussionPoints=1 | 1 | missing action 'send the updated floor plan this afternoon' |
| `015_ownership_assignment` | actions=0, decisions=0, discussionPoints=2 | 2 | expected 1 actions, got 0<br>missing action 'handle the negotiation' |
| `018_sales_pipeline_review` | actions=2, decisions=0, discussionPoints=5 | 5 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['retail', 'logistics accounts']<br>missing action 'update the forecast by Tuesday' |
| `019_supplier_review` | actions=1, decisions=0, discussionPoints=4 | 3 | expected 1 decisions, got 0<br>missing action 'send the revised SLA notes this afternoon'<br>missing decision 'stay with the current supplier for Q1' |
| `020_contract_negotiation` | actions=1, decisions=1, discussionPoints=2 | 4 | missing discussion topic concepts ['contract term length']<br>missing action 'redline the exit clause by Friday'<br>missing decision 'sign the one-year extension'<br>forbidden decision present 'three-year commitment' |
| `021_hiring_interview_debrief` | actions=1, decisions=0, discussionPoints=2 | 2 | expected 1 decisions, got 0<br>missing decision 'invite Maya to the final interview' |
| `022_candidate_screening` | actions=1, decisions=0, discussionPoints=1 | 2 | expected 1 decisions, got 0<br>missing decision 'not progress Ben to interview this round' |
| `024_board_update` | actions=0, decisions=1, discussionPoints=2 | 2 | expected 1 actions, got 0<br>missing action 'tighten the churn narrative before Thursday' |
| `026_product_bug_triage` | actions=1, decisions=0, discussionPoints=2 | 3 | expected 1 decisions, got 0<br>missing action 'verify the checkout flow before release'<br>missing decision 'ship the hotfix behind a feature flag' |
| `027_customer_complaint_review` | actions=2, decisions=0, discussionPoints=2 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'refund the last invoice' |
| `028_customer_onboarding` | actions=2, decisions=0, discussionPoints=4 | 4 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['defer SSO until phase two']<br>missing decision 'begin onboarding with CSV import first' |
| `029_office_relocation` | actions=2, decisions=0, discussionPoints=4 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'move the office relocation to 19 September instead' |
| `030_webinar_rehearsal` | actions=0, decisions=1, discussionPoints=4 | 3 | expected 1 actions, got 0<br>missing discussion topic concepts ['keep the live demo to seven minutes']<br>missing action 'remove two bullets from the registration slide' |
| `031_event_planning` | actions=2, decisions=0, discussionPoints=2 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'move the breakout to the main hall' |
| `032_training_rollout` | actions=2, decisions=1, discussionPoints=3 | 2 | missing discussion topic concepts ['pilot group to the Manchester site']<br>missing action 'split the material into two forty-minute sessions' |
| `035_procurement_discussion` | actions=2, decisions=0, discussionPoints=2 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'buy the lower-volume option first' |
| `037_partnership_discussion` | actions=2, decisions=0, discussionPoints=3 | 4 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['ninety-day pilot']<br>missing decision 'run a ninety-day pilot' |
| `038_grant_application_review` | actions=3, decisions=1, discussionPoints=4 | 2 | expected 1 actions, got 3<br>forbidden decision present 'keep the carbon angle' |
| `039_risk_review` | actions=2, decisions=0, discussionPoints=2 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'escalate that dependency to red' |
| `040_governance_review` | actions=3, decisions=0, discussionPoints=3 | 3 | expected 1 actions, got 3<br>expected 1 decisions, got 0<br>missing decision 'hold the rollout until policy sign-off' |
| `042_support_escalation_review` | actions=2, decisions=0, discussionPoints=2 | 4 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing discussion topic concepts ['replace the workaround article with a direct escalation path']<br>missing decision 'replace the workaround article with a direct escalation path' |
| `043_release_go_no_go` | actions=2, decisions=1, discussionPoints=2 | 2 | expected 1 actions, got 2<br>forbidden decision present 'ship the Friday release' |
| `045_board_launch_delay` | actions=2, decisions=1, discussionPoints=2 | 3 | expected 1 actions, got 2<br>missing discussion topic concepts ['partner paperwork']<br>missing decision 'move the Spain launch to September' |
| `046_customer_onboarding_split_rollout` | actions=1, decisions=1, discussionPoints=3 | 1 | forbidden decision present 'start warehouse onboarding first' |
| `047_supplier_renewal_rejection` | actions=2, decisions=0, discussionPoints=3 | 3 | expected 1 actions, got 2<br>expected 1 decisions, got 0<br>missing decision 'renew with the existing supplier' |
| `048_status_review_pending_leadership` | actions=1, decisions=0, discussionPoints=6 | 4 | expected 4 actions, got 1<br>missing action 'review stage gate templates'<br>missing action 'confirm AI pipeline dependencies with sales'<br>missing action 'follow up innovation grant feedback' |
| `049_low_substance_noise` | actions=0, decisions=0, discussionPoints=1 | 1 | forbidden content present 'run through the agenda' |
| `050_partnership_mou_enablement` | actions=4, decisions=0, discussionPoints=4 | 3 | expected 2 actions, got 4<br>expected 1 decisions, got 0<br>missing decision 'sign only the marketing MOU this month and defer the reseller clause to legal' |
| `051_real_webinar_rehearsal` | actions=6, decisions=3, discussionPoints=36 | 22 | missing discussion point 'The team reviewed the webinar agenda, including the introduction, AI discovery workshop methodology, case study, and live demonstration.'<br>missing discussion point 'The importance of starting AI initiatives with clearly defined business problems was discussed as a key factor in improving adoption.'<br>missing discussion point 'The AI discovery workshop approach was reviewed, including Define, Measure, Analyse, Improve and Control stages.'<br>missing discussion point 'Workshop delivery was discussed as a highly collaborative process driven by employees who perform the work and understand the workflow.' |
| `052_status_update_meeting` | actions=1, decisions=0, discussionPoints=4 | 1 | expected 0 actions, got 1 |
| `053_hidden_decision_meeting` | actions=2, decisions=1, discussionPoints=3 | 4 | expected 1 actions, got 2<br>missing discussion topic concepts ['grace', 'offsite']<br>missing action 'reschedule the weekly check-in'<br>forbidden decision present 'cancel the weekly check-in' |
| `054_document_review_meeting` | actions=0, decisions=1, discussionPoints=4 | 1 | expected 0 decisions, got 1 |
| `055_dependency_risk_meeting` | actions=1, decisions=0, discussionPoints=4 | 1 | expected 0 actions, got 1 |
| `056_progress_dashboard_meeting` | actions=0, decisions=0, discussionPoints=4 | 2 | expected 1 actions, got 0<br>missing action 'keep the tracker updated' |
| `057_rehearsal_banter_filter` | actions=1, decisions=0, discussionPoints=2 | 4 | expected 0 actions, got 1<br>forbidden content present 'take your top off'<br>forbidden content present 'vape'<br>forbidden content present 'talk french' |
| `058_submission_date_priority` | actions=0, decisions=1, discussionPoints=3 | 2 | expected 0 decisions, got 1<br>forbidden decision present 'delay the submission date' |
| `059_partial_completion_allowed` | actions=2, decisions=0, discussionPoints=3 | 1 | expected 1 actions, got 2 |
| `060_external_review_optional` | actions=1, decisions=0, discussionPoints=2 | 2 | expected 0 actions, got 1<br>missing discussion topic concepts ['external', 'cer', 'review'] |
| `061_no_major_impact_dependency` | actions=1, decisions=0, discussionPoints=3 | 1 | expected 0 actions, got 1 |
| `062_completed_and_approved_status` | actions=0, decisions=1, discussionPoints=2 | 3 | expected 0 decisions, got 1<br>missing discussion topic concepts ['stability', 'transport reports', 'complete']<br>missing discussion topic concepts ['approved', 'ea numbers'] |
| `064_analytics_review` | actions=12, decisions=1, discussionPoints=22 | 32 | missing discussion point 'The team discussed pressure from ONT to provide clearer analytics, including historic data from London 2024 and 2025, despite gaps caused by GDPR-related analytics deletion.'<br>missing discussion point 'Time on platform remains difficult to define because some delegates leave tabs open while others show zero recorded duration despite clear platform activity.'<br>missing discussion point 'A more accurate engagement-time method has been created using first click, last click and inactivity thresholds, giving an estimated average of around 45 minutes per person.'<br>missing discussion point 'The current eight-hour time-on-platform figure remains useful for comparability with previous years.' |
| `064_status_setup_clause_rejected` | actions=0, decisions=0, discussionPoints=1 | 1 | forbidden content present "The I've got the latest report open remains" |
| `066_status_misrecognized_setup_rejected` | actions=0, decisions=0, discussionPoints=1 | 1 | forbidden content present 'The I got report open remains blocked' |
| `067_banana_falcon_client_ready` | actions=1, decisions=2, discussionPoints=3 | 9 | expected at least 3 actions, got 1<br>missing discussion topic concepts ['dashboard']<br>missing discussion topic concepts ['server', 'restart']<br>missing discussion topic concepts ['feature', 'Smart Search'] |
| `068_noisy_low_substance_sparse` | actions=1, decisions=0, discussionPoints=1 | 2 | expected 0 actions, got 1<br>forbidden content present 'red light' |
| `069_decision_heavy_internal` | actions=0, decisions=2, discussionPoints=0 | 2 | missing discussion topic concepts ['legacy', 'read-only']<br>missing discussion topic concepts ['support', 'overloaded'] |
| `072_action_free_information_briefing` | actions=0, decisions=0, discussionPoints=0 | 3 | missing discussion topic concepts ['travel', 'policy']<br>missing discussion topic concepts ['mileage', 'July']<br>missing discussion topic concepts ['guidance', 'intranet'] |
| `073_support_metrics_actions` | actions=0, decisions=0, discussionPoints=1 | 11 | expected at least 3 actions, got 0<br>expected at least 2 discussion points, got 1<br>missing discussion topic concepts ['support metrics']<br>missing discussion topic concepts ['complex cases', 'simple requests'] |
