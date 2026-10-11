# PeopleGuide Project Outline

## 1. Project goal

PeopleGuide is a small multi-agent HR assistant for a fictional company, Northstar Systems Ltd. Employees can ask questions about leave, remote work, expenses, benefits, conduct, and HR procedures through a chat interface.

The assistant combines policy retrieval, synthetic employee data, deterministic calculation tools, and LLM reasoning. It provides policy guidance and explains its evidence, but it does not approve requests, modify HR records, make employment decisions, or provide legal or medical advice.

## 2. Proposed technology stack

### Backend

- Python 3.12
- FastAPI for the HTTP API and streaming responses
- LangGraph for agent orchestration and conversation state
- Pydantic for API contracts, graph state, and structured LLM output
- LangChain model and tool integrations where useful

### Frontend

- React with TypeScript
- Vite for development and builds
- A simple chat interface with answer citations, tool activity, and agent status
- Server-Sent Events for streaming assistant and workflow updates

### Data and retrieval

- Markdown policy documents under `data/policies/`
- Qdrant in local persistent mode for policy chunks, OpenAI embeddings, and retrieval metadata
- Version-controlled JSON for synthetic employee and reference data during the demo
- LangGraph's in-memory checkpointer for thread-scoped demo conversation state

OpenAI is the provider for all learned-model calls, including agent LLM calls and policy embeddings. The initial embedding model is `text-embedding-3-small`, configurable through the environment. Qdrant has been selected as the vector store because it can run locally for the demo while supporting vector retrieval and metadata filters. A persistent PostgreSQL checkpointer is a future production improvement; the demo currently keeps conversation checkpoints in process memory.

## 3. Initial three-agent design

### 3.1 Supervisor HR Agent

The Supervisor is the user-facing coordinator. It does not perform every task itself.

Responsibilities:

- Classify the request and identify missing information.
- Detect sensitive or unsupported requests.
- Decide whether to call the RAG Agent, the Employee Case Analyst, or both.
- Decide whether a second pass is needed after receiving a subagent result.
- Reconcile policy evidence with calculations and structured data.
- Produce the final answer with assumptions, citations, and escalation guidance.
- Stop automated analysis when a mandatory human-escalation rule applies.

Examples handled directly include greetings, capability questions, and requests that must immediately be routed to a human channel.

### 3.2 Policy RAG Agent

The Policy RAG Agent determines what Northstar's documents say.

Responsibilities:

- Reformulate the user's question into an effective retrieval query.
- Search the policy knowledge base.
- Filter results by status, effective date, location, and audience.
- Follow cross-references and rule precedence when multiple policies apply.
- Return concise findings with policy IDs, section numbers, and supporting excerpts.
- Report conflicts, gaps, or insufficient evidence rather than inventing a rule.

Primary tool:

- `search_policies(query, filters)`

The agent returns evidence to the Supervisor; it does not make final personalized entitlement decisions.

### 3.3 Employee Case Analyst

The Employee Case Analyst applies retrieved rules to a specific synthetic employee or scenario.

Responsibilities:

- Query the minimum employee data required for a request.
- Calculate leave accrual, available balance, notice periods, and deadlines.
- Evaluate expenses against category limits and approval requirements.
- Compare benefits plans and determine administrative eligibility dates.
- Check international remote-work duration and destination constraints.
- State inputs, formulas, dates, and assumptions explicitly.
- Return uncertainty or a record discrepancy to the Supervisor for escalation.

Candidate tools:

- `get_employee_profile(employee_id)`
- `calculate_leave_balance(employee_id, as_of_date)`
- `check_expense_eligibility(expense)`
- `compare_benefit_plans(plan_names)`
- `check_remote_work_request(employee_id, destination, dates)`

This agent should use deterministic code for arithmetic and rule checks. The LLM interprets the question and selects tools but should not perform authoritative calculations in free-form text.

## 4. Why the Employee Case Analyst is the recommended second subagent

The RAG Agent answers **“What does the policy say?”** The Case Analyst answers **“How does that policy apply to this employee and these facts?”** This creates a clear separation of responsibilities and makes multi-agent collaboration necessary for personalized questions.

It also provides a natural home for structured-data and calculation tools. The Supervisor can act as a lightweight reviewer by checking whether the analyst's conclusion is supported by the RAG Agent's evidence before producing the final response.

A dedicated Compliance Reviewer is a possible later fourth agent. For the first version, its essential safeguards can be implemented through deterministic routing rules and Supervisor instructions without sacrificing the three-agent design.

## 5. Proposed LangGraph flow

```text
User message
    |
    v
Supervisor: classify, assess risk, plan
    |
    +-- Immediate escalation --------------------------> Final safe response
    |
    +-- General policy question --> Policy RAG Agent --+
    |                                                  |
    +-- Personal/tool question ---> Case Analyst ------+--> Supervisor synthesis
    |                                                  |
    +-- Combined question ----------> RAG Agent --------+        |
                                      then Analyst              v
                                                          Final response
```

The graph is not a fixed sequence. The Supervisor can select one or both subagents, request another retrieval pass, or stop and escalate. Deterministic conditional edges enforce sensitive-case boundaries even if the model proposes a different route.

## 6. Suggested graph state

The shared state is expected to contain:

- Conversation messages and thread ID
- Optional synthetic employee ID
- Classified intent and sensitivity level
- Proposed route and required tools
- Retrieved policy evidence and citations
- Structured tool inputs and results
- Assumptions, missing facts, and policy conflicts
- Draft and final answers
- Escalation status and reason

Only raw evidence and structured results should be stored in shared state. Each agent should format its own prompt from that state when invoked.

## 7. Knowledge base

The repository currently contains 12 synthetic policy documents covering:

- Employee handbook and policy governance
- Annual, sick, medical, and parental leave
- Flexible and international remote work
- Travel and expenses
- Employee benefits
- Code of conduct
- HR support and escalation
- Hong Kong-specific rules

The documents include stable policy IDs, numbered sections, effective dates, scopes, cross-references, and escalation rules to support filtered retrieval and citations.

### 7.1 RAG ingestion

Policy ingestion will run as an explicit offline command rather than during every FastAPI startup or user request. The ingestion pipeline will:

1. Parse each document's YAML front matter.
2. Split documents along numbered Markdown section boundaries.
3. Split only unusually long sections into smaller paragraph-based chunks.
4. Add the policy title and section breadcrumb to each embedded chunk.
5. Generate dense vector representations with the configured OpenAI embedding model.
6. Upsert the chunks into a locally persisted Qdrant collection.

Chunk IDs will be deterministic so re-ingestion updates existing records instead of creating duplicates. Stored metadata will include the policy ID, version, document status, effective date, locations, applicable audiences, section number and title, source path, and chunk index.

### 7.2 Policy retrieval

Retrieval will combine semantic search with explicit structured constraints:

- OpenAI dense embeddings for semantic similarity and paraphrased questions.
- Exact metadata filters for policy IDs, status, location, audience, and effective dates.
- A direct policy-ID filter when a request names a specific policy.

Filters will be applied before ranking wherever possible. Normal filters include active document status, effective date, location, employee type, and optional policy IDs. Policy precedence—such as a Hong Kong addendum overriding a global policy—will be evaluated by the RAG Agent using the retrieved evidence and governance policy.

The initial search will return approximately six evidence chunks. The RAG Agent may refine the query or perform a second search when the first result reveals a relevant cross-reference or evidence gap. Cross-reference expansion will be limited to avoid uncontrolled retrieval loops.

### 7.3 RAG tool boundary

The `search_policies` tool will retrieve evidence rather than generate the final HR answer. Its expected inputs are:

- Search query
- `as_of_date`
- Optional location
- Optional employee type
- Optional policy IDs
- Result limit

Its structured output will contain the applied filters and evidence records with chunk ID, policy ID and title, section number and title, excerpt, effective date, source path, and retrieval score.

The Policy RAG Agent is responsible for query refinement, evidence sufficiency, cross-references, conflicts, and precedence. The Supervisor remains responsible for combining policy evidence with Case Analyst results and presenting the final answer.

### 7.4 Retrieval evaluation

A small labeled evaluation set will map representative questions to expected policy sections. It will cover paraphrases, exact terms, numeric thresholds, cross-policy questions, location and effective-date filters, and questions for which the knowledge base lacks sufficient evidence. Initial retrieval quality will be measured by whether the expected section appears within the top three or top five results.

## 8. Dynamic behavior to demonstrate

The system should make meaningful runtime decisions, including:

- Whether document retrieval is needed.
- Whether employee data or a deterministic tool is needed.
- Which subagent should act next.
- Whether policy evidence is sufficient.
- Whether retrieved rules must be applied by the Case Analyst.
- Whether the request must be escalated to a human.

Not every request should invoke every agent or tool.

## 9. Example demonstration questions

### RAG only

> How many remote-working days are normally permitted during probation?

Expected route: Supervisor to Policy RAG Agent, then final synthesis.

### Tool use

> Compare the Standard and Premium benefit plans.

Expected route: Supervisor to Case Analyst using the benefit comparison tool. Policy retrieval is optional if structured results contain source references.

### Multi-agent collaboration

> I joined the Hong Kong office on 15 June, have already taken four days off, and want another five days in December. Will I have enough annual leave?

Expected route: Policy RAG Agent retrieves proration and accrual rules; Case Analyst loads the synthetic employee record and calculates the balance; Supervisor checks that the calculation uses the retrieved rule and states its assumptions.

### Safety escalation

> I want to report repeated inappropriate comments from my manager.

Expected route: deterministic sensitive-case detection followed by a safe response with human reporting channels. The agents must not investigate or make a finding.

## 10. Near-term implementation steps

1. Define the FastAPI and frontend project structure.
2. Define Pydantic API models and the typed LangGraph state.
3. Build and test section-aware OpenAI embedding ingestion into Qdrant, semantic retrieval, metadata filters, and citations.
4. Create synthetic employee and reference datasets.
5. Implement deterministic tools independently of the agents.
6. Implement the two subagents and Supervisor routing.
7. Add conversation persistence and streaming events.
8. Build the React chat interface.
9. Add unit tests, graph-routing tests, and example end-to-end evaluations.
10. Document setup, architecture, tradeoffs, and future improvements.

