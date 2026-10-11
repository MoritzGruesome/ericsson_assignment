---
title: Policy Governance and Interpretation
policy_id: HR-GOV-001
version: "1.0"
effective_date: 2026-01-01
review_date: 2026-12-01
owner: People Operations
applies_to:
  - all_policies
locations:
  - global
document_status: active
---

# Policy Governance and Interpretation

## 1. Purpose

This document defines how Northstar policies are identified, versioned, interpreted, and used by the HR assistant. It is the governing source for resolving document priority and handling ambiguity.

## 2. Policy identifiers and versions

Every controlled policy has a stable `policy_id`, version, effective date, owner, scope, and status. A version is authoritative only when its status is `active` and its effective date is on or before the date relevant to the question.

Future policies may be retrieved for planning but must be clearly described as not yet effective. Superseded policies may be used to explain a historical event occurring while they were active, but they must not determine a current entitlement.

## 3. Source precedence

Use this order when sources overlap:

1. Mandatory location addendum.
2. Written, case-specific exception approved by People Operations.
3. Detailed global policy.
4. Employee Handbook summary.

Structured reference data—such as destination statuses, expense rates, holiday calendars, benefit tables, and employee profiles—provides facts used to apply a policy. It does not override policy text unless the policy explicitly delegates a value to an effective-dated table.

## 4. Choosing the relevant date

The relevant date depends on the question:

- For current eligibility, use the requested `as_of_date` or today's date.
- For an expense, use the transaction date.
- For a leave request, use both the request date and proposed leave dates where notice or accrual matters.
- For a historical dispute, use the policy and records effective at the event date.
- For planned policy changes, separate current rules from future rules.

If the question provides no date and the answer could vary by date, the assistant should request or state an `as_of_date` before calculating.

## 5. Interpretation rules

Policy wording should be applied according to its defined scope. The assistant must not treat an example as an exhaustive rule, turn guidance such as “normally” into an absolute prohibition, or convert a maximum into an entitlement.

Where a policy assigns discretion to a manager or People Operations, the assistant may identify relevant factors and the required approver but may not predict or make the decision.

If a missing fact could change eligibility, entitlement, an approval route, or risk classification, the assistant should obtain the fact from an authorized tool or escalate rather than guess.

## 6. Calculations

Calculations must preserve input values and identify the policy formula used. Do not round intermediate values unless a policy instructs otherwise. Results should state units, currency where applicable, relevant dates, and whether the value is official, estimated, accrued, or projected.

When a structured record conflicts with a calculation, report the discrepancy and refer it for correction. The assistant's calculation does not overwrite the official record.

## 7. Citations and evidence

A policy answer should cite the policy ID and numbered section supporting the main conclusion. Personalized answers should separately identify the employee or reference data used without exposing unnecessary personal information.

Retrieval similarity alone is not evidence that a policy applies. The assistant must check document status, effective date, location, audience, and any cross-referenced exceptions.

## 8. Policy conflicts and gaps

If two active documents at the same precedence level conflict, or no active source covers a material issue, the assistant must not manufacture a rule. It should describe the conflict or gap, provide any uncontested guidance, and refer the matter to the policy owner.

Typographical differences that cannot affect the result may be noted without stopping the answer. A difference affecting eligibility, money, leave, safety, or required approval is material.

## 9. Human decision boundaries

The HR assistant provides information and decision support. It must not:

- Approve or reject leave, expenses, remote work, or benefits enrollment.
- Make or recommend hiring, promotion, compensation, discipline, performance, or termination decisions.
- Determine legal rights, immigration permission, tax status, or medical necessity.
- Investigate allegations or decide credibility.
- Change an official employee record.

Cases crossing these boundaries must follow HR-SUPPORT-001.

## 10. Data minimization

Use only the employee attributes needed for the question. Avoid displaying medical details, government identifiers, bank information, personal contact data, or allegation details.

Synthetic employee IDs may be shown in the demo to make tool use transparent. The production design would apply authorization checks, audit access, and redact unnecessary fields.

## 11. Ownership and review

The owner listed in a policy's metadata is responsible for its content and review. Review dates trigger reassessment; they do not automatically expire an otherwise active policy.

Material changes require a new version and effective date. Related structured rules and evaluation cases should be updated in the same change.

## 12. Related documents

- HR-CORE-001 — Employee Handbook
- HR-SUPPORT-001 — HR Support and Escalation Guide
- HR-LOC-HK-001 — Hong Kong Location Addendum

