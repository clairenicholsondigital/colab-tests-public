# Microsoft Teams Minutes Fixtures

This fixture pack is for testing whether generated meeting minutes transfer
across meeting types instead of overfitting to a small set of Trinzo examples.

Each case contains:

- `transcript.txt`: a Teams-style transcript.
- `expected_minutes.md`: a human-readable expected output in Microsoft Teams
  minutes style.

The expected minutes use a consistent structure:

- Meeting details
- Attendees
- Summary
- Discussion points
- Decisions
- Action items
- Follow-up / open questions

Use these fixtures as semantic regression tests. The generated output does not
need to match the wording exactly, but it should preserve the meeting purpose,
important topics, decisions, actions, owners and dates.

