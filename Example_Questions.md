## Example questions

RAG retrieval:

> How many remote-working days are normally permitted during probation?

Structured tool use:

> Compare the Standard and Premium benefit plans.

Multi-agent collaboration using employee `NS-1042`, or as a hypothetical scenario with no employee selected:

> I joined on 15 June and have already taken four days off. How much annual leave is available to me today?

Expense policy and threshold analysis:

> A taxi home after a client dinner cost HKD 620 at 22:45. Is it reimbursable and who must approve it?

Mandatory escalation:

> I want to report repeated inappropriate comments from my manager.

### Multi-turn clarification examples

Use each sequence in one chat so the follow-up can complete or correct the earlier request.

1. **Complete a hypothetical leave calculation**

   > User: I started on 15 June. Can you estimate my annual-leave balance?
   >
   > Follow-up: The year was 2025, and I have taken four approved days.

   Expected behavior: the assistant asks for missing calculation facts, remembers the original
   scenario, and reruns the shared leave calculator with the completed start date and leave usage.

2. **Supply missing expense evidence and context**

   > User: I paid HKD 620 for a taxi. Can I claim it?
   >
   > Follow-up: It was a taxi home after a client dinner at 22:45, and I have the itemized receipt.

   Expected behavior: the assistant carries the amount and category into the follow-up, retrieves
   the expense policy, and checks the completed scenario against the taxi limit and approval rules.

3. **Complete an international remote-work request**

   > User: Can I work remotely from Japan?
   >
   > Follow-up: I am employee NS-1077, and the working dates would be 2–6 November 2026.

   Expected behavior: the assistant requests the missing employee and date information, then uses
   the remembered destination to run the remote-work pre-check and explain any approval requirements.
