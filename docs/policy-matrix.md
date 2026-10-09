# Northstar Systems HR Policy Matrix

> **Demo data only.** Northstar Systems Ltd. is a fictional company. These rules are designed for an AI-assistant demonstration and are not legal or HR advice.

## 1. Company and policy scope

| Field | Value |
|---|---|
| Company | Northstar Systems Ltd. |
| Industry | Enterprise software and managed services |
| Approximate size | 500 employees |
| Primary demo location | Hong Kong |
| Other locations referenced | Singapore and United Kingdom |
| Policy baseline | Global policies with location-specific addenda |
| Policy effective date | 1 January 2026 unless stated otherwise |
| Policy year | 1 January–31 December |
| Working week | Monday–Friday |
| Standard working day | 8 hours |
| Authoritative source | The applicable policy and location addendum; structured data supports calculations but does not override policy text |
| Ambiguity rule | If policies conflict or do not cover a case, do not infer an entitlement; escalate to People Operations |

## 2. Employee attributes that affect policy decisions

These fields will later form the synthetic employee profiles queried by tools.

| Attribute | Example values | Used by |
|---|---|---|
| `employee_id` | `NS-1042` | All personalized requests |
| `work_location` | `HK`, `SG`, `UK` | Leave, holidays, benefits, remote work, expenses |
| `employment_type` | Permanent, fixed-term, intern | Leave, benefits, expenses |
| `work_schedule` | Full-time, part-time percentage | Leave accrual and benefits |
| `start_date` | `2026-06-15` | Proration, probation, eligibility |
| `probation_end_date` | `2026-09-14` | Leave approval and remote work |
| `manager_id` | `NS-0088` | Approval routing |
| `department` | Engineering, Sales, Operations | Expense limits and on-call rules |
| `job_level` | Individual contributor, manager, director | Approval routing; not base entitlement |
| `benefit_plan` | Standard, Premium | Benefit comparisons |
| `leave_taken` | Days by leave type and date | Balance calculations |
| `remote_work_days` | Dates and countries | Remote-work limits |

## 3. Rule precedence

Apply rules in this order:

1. Mandatory location addendum
2. Policy-specific exception explicitly approved by People Operations
3. Global policy
4. Employee handbook summary

If a lower-priority document conflicts with a higher-priority source, use the higher-priority source and report the conflict. A manager may approve requests within a policy but cannot waive an eligibility rule, statutory requirement, or People Operations approval.

## 4. Policy summary matrix

| Policy ID | Policy | Primary audience | Main decision variables | Normal approver | Mandatory escalation |
|---|---|---|---|---|---|
| HR-CORE-001 | Employee Handbook | All employees | Location, employment type | N/A | Conflicting policies or undefined employment status |
| HR-LEAVE-001 | Annual Leave | Permanent and fixed-term employees | Location, start date, schedule, balance | Manager | Negative balance, exception, or disputed record |
| HR-LEAVE-002 | Sick and Medical Leave | All employees | Location, consecutive days, documentation | Manager / People Operations | Extended absence, recurring pattern, sensitive medical details |
| HR-LEAVE-003 | Parental Leave | Eligible employees | Location, tenure, caregiver type, dates | People Operations | Eligibility uncertainty or overlapping leave types |
| HR-WORK-001 | Flexible and Remote Work | Eligible employees | Probation, role, requested frequency | Manager | Accessibility, medical accommodation, or exception |
| HR-WORK-002 | International Remote Work | Eligible employees | Destination, duration, role, data access | Manager + People Operations | Restricted destination, tax/visa uncertainty, over-limit request |
| HR-EXP-001 | Travel and Expenses | Employees with business purpose | Category, amount, currency, receipt, approver | Manager / Department head | Missing evidence, policy exception, suspected duplicate |
| HR-BEN-001 | Employee Benefits | Eligible employees | Location, employment type, plan, tenure | People Operations | Coverage dispute or protected health information |
| HR-CONDUCT-001 | Code of Conduct | Everyone | Concern type and urgency | Designated channel | Harassment, discrimination, retaliation, safety, fraud |
| HR-SUPPORT-001 | HR Support and Escalation | Everyone | Topic, sensitivity, urgency | People Operations | Emergency or high-risk report |

## 5. Annual leave rules — HR-LEAVE-001

| Rule | Global baseline | Hong Kong addendum | System behavior / edge case |
|---|---|---|---|
| Full-time annual allowance | 20 working days per policy year | Same | Excludes public holidays |
| Part-time allowance | Full-time allowance × contracted work percentage | Same | Round final annual entitlement to nearest half-day |
| First-year entitlement | Prorated by calendar days employed in the policy year | Same | Formula below; round to nearest half-day |
| Accrual timing | Monthly, credited on the final day of each month | Same | New starter can see projected entitlement separately from accrued balance |
| Use during probation | Up to 3 days from accrued balance | Up to 3 days | More than 3 days requires People Operations approval |
| Minimum unit | Half-day | Same | Reject requests below half-day |
| Standard approval | Manager approval | Same | Approval does not change the balance until request is confirmed |
| Advance notice | 5 working days | Same | Guidance, not an automatic rejection |
| Requests of 5+ consecutive days | 20 calendar days' notice | Same | Late request may still be approved by manager |
| Carryover | Up to 5 unused days | Same | Must be used by 31 March of following year |
| Carryover expiry | 1 April | Same | Expired days cannot be restored by a manager |
| Negative balance | Not normally allowed | Same | People Operations may approve up to 3 days in exceptional cases |
| Termination treatment | Calculated by People Operations | Same | Assistant must not give a final payout amount |

### Annual leave calculation

```text
full_year_entitlement = 20 × work_schedule_percentage
first_year_entitlement = full_year_entitlement × employed_calendar_days / days_in_policy_year
available_balance = accrued_leave + valid_carryover - approved_leave_taken - approved_future_leave
```

Round the first-year entitlement once, at the end, to the nearest 0.5 day. Do not round intermediate values. A balance answer must state its `as_of_date` and distinguish accrued balance from projected year-end entitlement.

## 6. Sick and medical leave rules — HR-LEAVE-002

| Rule | Global baseline | Hong Kong addendum | System behavior / edge case |
|---|---|---|---|
| Notification | Notify manager as soon as reasonably possible and normally before scheduled start | Same | Do not treat a missed notification as proof of misconduct |
| Self-certification | Permitted for 1 consecutive working day | Permitted | Count consecutive scheduled working days, not calendar days |
| Medical certificate | Required from the 2nd consecutive working day | Required | Only confirm requirement; do not request diagnosis details |
| Paid sick leave | Defined by location addendum and employee record | Use structured HK entitlement data | Never infer remaining entitlement from annual leave data |
| Extended absence | 5 or more consecutive working days | Same | Refer to People Operations for case management |
| Repeated short absences | Manager may request an attendance conversation | Same | No automated judgment or disciplinary recommendation |
| Medical privacy | Collect only documentation needed to administer leave | Same | Do not expose diagnosis or medical documents in chat |
| Emergency | Contact local emergency services first | Same | Assistant provides escalation guidance only |

## 7. Parental leave rules — HR-LEAVE-003

| Rule | Global baseline | Hong Kong addendum | System behavior / edge case |
|---|---|---|---|
| Eligibility | Permanent or fixed-term employee with 26 weeks' service by expected event date | Same demo rule | Refer uncertain service breaks to People Operations |
| Primary caregiver leave | 16 weeks company-paid | Same demo rule | Subject to eligibility verification |
| Supporting caregiver leave | 4 weeks company-paid | Same demo rule | Cannot overlap with primary-caregiver classification for the same event |
| Notice | 8 weeks before intended start, where practicable | Same | Late notice does not automatically remove eligibility |
| Start-date changes | Notify People Operations promptly | Same | Tool may identify deadlines but cannot approve change |
| Annual leave interaction | Continues to accrue during company-paid parental leave | Same | Calculation tool may project accrual |
| Multiple births/adoptions | One entitlement per event | Same | Escalate unusual circumstances |
| Sensitive information | Documentation handled only by People Operations | Same | Chat should not request medical evidence |

All parental-leave results must be framed as preliminary eligibility guidance pending People Operations confirmation.

## 8. Flexible and domestic remote work — HR-WORK-001

| Rule | Global baseline | Hong Kong addendum | System behavior / edge case |
|---|---|---|---|
| Office-based hybrid allowance | Up to 2 remote days per working week | Same | Not a guaranteed entitlement |
| Fully remote roles | As specified in employment record | Same | Profile value overrides hybrid default |
| During probation | Up to 1 remote day per week | Same | Manager may approve less, not more, without People Operations |
| Manager approval | Required for recurring schedule | Same | Ad hoc day follows team process |
| Core collaboration hours | 10:00–16:00 local office time | Same | Flexible scheduling outside core hours |
| Equipment | Standard laptop and approved accessories | Same | Home-office upgrades need separate approval |
| Security | Company device, approved network controls, no unauthorized shared device | Same | Security concerns route to IT, not HR |
| Role restriction | On-site operational duties may be ineligible | Same | Use employee profile; do not infer from job title alone |
| Accommodation requests | Separate confidential process | Same | Immediately refer to People Operations; do not evaluate medical need |

## 9. International remote work — HR-WORK-002

| Rule | Global baseline | Hong Kong addendum | System behavior / edge case |
|---|---|---|---|
| Annual limit | Up to 20 working days per policy year | Same | Count approved international remote working days only |
| Maximum single trip | 10 working days | Same | Longer request requires formal exception review |
| Minimum notice | 30 calendar days | Same | Tool calculates deadline |
| Required approvals | Manager and People Operations | Same | IT Security review may also be required |
| Eligible employees | Permanent employees who completed probation | Same | Fixed-term employees require exception review |
| Destination check | Must be on approved destination list | Same | Approved list is structured data with effective dates |
| Immigration and tax | Employee confirms right to work; company assesses risk | Same | Assistant never confirms visa or tax compliance |
| Data access | Restricted-data roles need IT Security approval | Same | Profile/data classification triggers review |
| Combining with leave | Permitted if dates are clearly separated | Same | Do not count annual-leave days toward 20-day limit |
| Business travel | Governed separately | Same | Do not classify employer-directed travel as remote work |

Any answer about a proposed international arrangement must state that approval is not guaranteed and must not provide legal, tax, or immigration advice.

## 10. Travel and expense rules — HR-EXP-001

All monetary thresholds below are demo values. Use the exchange rate recorded on the transaction date; if unavailable, use the finance dataset's monthly reference rate and disclose that assumption.

| Category | Standard limit | Approval rule | Required evidence | Important exception |
|---|---:|---|---|---|
| Local public transport | Actual reasonable cost | Manager | Receipt when available | No receipt required where operator does not issue one |
| Taxi / ride-hailing | HKD 500 per trip | Manager; department head above limit | Itemized receipt and business purpose | Allowed after 22:00 for work-related journey home |
| Domestic meal while travelling | HKD 350 per day | Manager | Itemized receipt | Alcohol excluded unless part of approved client entertainment |
| International meal while travelling | HKD 600 per day | Manager | Itemized receipt | Destination-specific lower cap may apply |
| Hong Kong hotel | HKD 1,800 per night | Manager; department head above limit | Hotel invoice | Conference hotel may exceed cap with pre-approval |
| International hotel | Destination rate table | Manager | Hotel invoice | Use destination and travel date |
| Client entertainment | HKD 1,500 per event | Manager; department head above limit | Attendee names, business purpose, itemized receipt | Employee's share still counts toward event limit |
| Home-office accessory | HKD 1,500 per policy year | Manager | Receipt | Must be on approved-equipment list |
| Mobile/data roaming | Actual reasonable business use | Manager | Provider statement | Avoid displaying personal call details |

General rules:

- Claims should be submitted within 30 calendar days of the expense date.
- A receipt is normally required for any item of HKD 200 or more unless the table defines a stricter rule.
- The claimant cannot approve their own expense.
- A manager cannot approve their own expense; it routes to the next-level manager.
- Splitting one purchase into multiple claims to avoid a threshold is prohibited.
- Duplicate-looking transactions must be flagged for human review, not automatically rejected as fraud.
- Personal expenses are not reimbursable even if below a category limit.
- Missing-receipt declarations may be accepted by Finance for exceptional cases; the assistant cannot approve them.

## 11. Benefits rules — HR-BEN-001

| Feature | Standard plan | Premium plan | Eligibility / notes |
|---|---:|---:|---|
| Employee monthly contribution | HKD 0 | HKD 420 | Deducted through payroll |
| Outpatient annual limit | HKD 6,000 | HKD 12,000 | Subject to insurer terms |
| Specialist co-pay | HKD 250 | HKD 100 | Per eligible visit |
| Dental annual limit | HKD 1,500 | HKD 4,000 | Routine and emergency treatment |
| Vision annual limit | Not included | HKD 1,500 | Once per policy year |
| Dependants | Employee-paid add-on | One dependant subsidized at 50% | Enrollment required |
| Coverage start | First day of month after start date | Same | If start date is first of month, coverage starts that day |
| Plan selection | Standard by default | Employee may elect Premium | Election due within 30 days of eligibility |
| Plan change | Annual enrollment window | Same | Qualifying life events handled by People Operations |

The assistant may compare published plan features but must not recommend medical treatment, interpret insurer decisions, or access claim diagnoses.

## 12. Code of conduct and sensitive-case routing — HR-CONDUCT-001

| Topic | Assistant may do | Assistant must not do | Route |
|---|---|---|---|
| General conduct question | Retrieve and summarize policy | Make a finding against a person | People Operations if facts are disputed |
| Harassment or discrimination report | Acknowledge, provide reporting channels, preserve the user's wording | Investigate, challenge credibility, or promise confidentiality/outcome | Designated People Partner / ethics channel |
| Retaliation concern | Explain anti-retaliation policy and urgent contacts | Notify the named manager automatically | Ethics channel / People Operations |
| Immediate safety risk | Advise contacting local emergency services and company security | Attempt crisis counseling or delay urgent help | Emergency services / Security |
| Suspected fraud | Provide confidential reporting route | Accuse a person or expose the report | Ethics channel |
| Interpersonal disagreement | Explain informal and formal options | Diagnose intent or assign blame | Manager or People Partner |
| Disciplinary process | Explain process at a high level | Predict outcome or recommend sanction | People Operations |

## 13. HR escalation rules — HR-SUPPORT-001

The assistant must stop substantive automated analysis and provide a human route when any of the following apply:

- A user reports harassment, discrimination, retaliation, violence, self-harm, fraud, or an immediate safety concern.
- The request asks the assistant to decide hiring, promotion, discipline, termination, compensation, or performance outcomes.
- The case requires legal, immigration, tax, or medical judgment.
- The user disputes an official leave, payroll, expense, or benefits record.
- Applicable policies conflict, required profile data is missing, or the requested exception exceeds documented authority.
- The user provides unnecessary sensitive personal data. The assistant should advise them not to share more in chat.

| Severity | Example | Response expectation |
|---|---|---|
| Emergency | Immediate threat to safety | Direct user to local emergency services and company security immediately |
| Urgent | Active harassment or retaliation concern | Provide priority reporting routes and encourage prompt human contact |
| Standard | Policy exception or record correction | Create or recommend a People Operations case |
| Informational | General explanation | Answer with sources; no escalation required |

## 14. Agent decision matrix

| Request type | Policy Specialist | Case Analyst | Compliance Reviewer | Likely tools |
|---|---|---|---|---|
| General policy definition | Required | Not normally needed | Only if ambiguous or sensitive | Policy search |
| Personalized leave balance | Required | Required | Required when exception or low confidence | Policy search, employee profile, leave calculator |
| Expense eligibility | Required | Required | Required above threshold or with missing evidence | Policy search, expense checker, exchange-rate lookup |
| Benefits comparison | Required | Required for employee-specific eligibility | Optional | Policy search, benefit comparison, employee profile |
| Domestic remote-work request | Required | Required if employee-specific | Required for exception/accommodation | Policy search, employee profile |
| International remote-work request | Required | Required | Always required | Policy search, profile, destination checker, date calculator |
| Conduct or grievance report | Limited to safe retrieval | Not used | Always required; route to human | Escalation directory only |

The supervisor chooses agents based on request classification, required personalization, sensitivity, conflicting evidence, and confidence. It should not run every agent for every question.

## 15. Designed demo scenarios

| Scenario | Rules exercised | Expected collaboration |
|---|---|---|
| New starter asks whether seven December leave days are available | Proration, monthly accrual, probation cap, existing leave | Policy Specialist retrieves rules; Case Analyst calculates; reviewer checks assumptions |
| Employee wants to work from Japan for three weeks | Annual and trip limits, destination status, probation, notice, approvals | Policy + profile + destination/date tools; mandatory review |
| Taxi home after late client dinner costs HKD 620 | Late-night exception, taxi cap, business purpose, over-limit approval | Policy retrieval + expense checker; reviewer explains approval requirement |
| Employee compares Standard and Premium plans after joining mid-month | Coverage start, enrollment deadline, plan features | Benefit comparison + date calculation; optional review |
| Employee reports repeated inappropriate comments | Sensitive-case routing | Immediate safe response and human escalation; no autonomous investigation |

## 16. Intentional complexity boundaries

Included in the demo:

- Effective dates and rule precedence
- Global rules with a Hong Kong addendum
- Proration and balance calculations
- Structured thresholds and approval routing
- Employee-specific eligibility
- Sensitive-case detection and human escalation
- Evidence-backed answers with policy-section citations

Excluded from the demo:

- Real employee information
- Payroll calculations and tax treatment
- Legal determination of statutory entitlements
- Automated employment decisions
- Direct integration with production HR systems
- Approval or rejection of requests by the assistant

These boundaries keep the dataset complex enough to demonstrate RAG, tools, and agent coordination without turning the prototype into an HR information system or a legal-compliance product.
