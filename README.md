# PeopleGuide

PeopleGuide is a small multi-agent HR policy assistant for the fictional company Northstar Systems Ltd. It answers questions about leave, flexible work, expenses, benefits, and HR procedures using policy retrieval, synthetic employee data, deterministic tools, and OpenAI models.

This repository is an interview demonstration. Its policies, contacts, and employee records are synthetic; the assistant does not approve requests, modify records, make employment decisions, or provide legal or medical advice.

## Technology

- FastAPI and Pydantic backend
- LangGraph orchestration
- OpenAI for all LLM and embedding calls
- Qdrant local persistent vector store
- React, TypeScript, and Vite frontend
- Server-Sent Events for workflow progress
- Pytest for backend tests

## Architecture

```text
React chat UI
    |
    | POST /api/chat/stream
    v
FastAPI
    |
    v
Deterministic safety gate
    |
    v
Supervisor HR Agent
    |
    +-- Policy RAG Agent ------> search_policies ------> Qdrant
    |
    +-- Employee Case Analyst -> employee / calculation tools
    |
    +-- both agents in sequence when policy must be applied to a case
    |
    v
Supervisor synthesis and cited response
```

The Supervisor selects the smallest sufficient route. General policy questions normally use only the RAG Agent. Personalized questions can use the RAG Agent followed by the Case Analyst. Sensitive cases are sent to a deterministic escalation branch.

## Agents

### Supervisor HR Agent

Classifies requests, selects specialists, synthesizes evidence, and applies escalation boundaries. It does not perform authoritative calculations.

### Policy RAG Agent

Searches active policy sections, checks scope and precedence, and returns findings with stable policy and section citations. It reports gaps rather than inventing policy.

### Employee Case Analyst

Uses synthetic employee and reference data to calculate leave, evaluate expenses, compare benefits, and pre-check international remote-work requests. When no employee is selected, it can apply the same leave calculator to temporary facts supplied in the conversation. Arithmetic and thresholds live in deterministic code rather than prompts.

## Tools

- `search_policies`
- `get_employee_profile`
- `calculate_leave_balance`
- `check_expense_eligibility`
- `compare_benefit_plans`
- `check_remote_work_request`

`calculate_leave_balance` accepts either a selected synthetic employee ID or temporary scenario facts. It returns a typed `success`, `needs_input`, or `invalid_input` outcome, allowing missing values to flow back through the Case Analyst to the Supervisor instead of terminating the graph.

## RAG design

The ingestion command parses the Markdown front matter, splits each policy on numbered section boundaries, adds citation metadata, creates OpenAI embeddings, and stores 125 chunks in local Qdrant storage.

Retrieval combines OpenAI semantic embeddings with deterministic filters for document status, effective date, location, and policy ID. The tool returns evidence records rather than generating an answer. The RAG Agent evaluates those records and the Supervisor owns the final response.

## Local setup

Prerequisites:

- Python 3.12
- Node.js 20 or later
- An OpenAI API key with access to the configured models

Create the environment file:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. The default models are configurable:

```dotenv
LLM_MODEL=gpt-6-luna
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Install the backend:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e 'backend[dev]'
```

Build the policy index from the repository root:

```bash
cd backend
PYTHONPATH=. ../.venv/bin/python -m app.scripts.ingest_policies
cd ..
```

Start FastAPI:

```bash
cd backend
PYTHONPATH=. ../.venv/bin/uvicorn app.main:app --reload --port 8000
```

In a second terminal, start React:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. FastAPI documentation is available at `http://localhost:8000/docs`.

## Verification

Run backend tests:

```bash
cd backend
PYTHONPATH=. ../.venv/bin/pytest
```

Build and audit the frontend:

```bash
cd frontend
npm run build
npm audit --audit-level=moderate
```

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

## Repository layout

```text
backend/                FastAPI, LangGraph, RAG, tools, and tests
frontend/               React chat interface
data/policies/          Synthetic Markdown policy knowledge base
data/structured/        Synthetic employees and reference tables
docs/policy-matrix.md   Authoritative demo policy rules
docs/project-outline.md Architecture and implementation decisions
```

## Improvements with more time

- Replace in-memory LangGraph checkpoints with PostgreSQL persistence.
- Add authentication and employee-level authorization.
- Add a labeled retrieval and response evaluation suite.
- Pin model snapshots after evaluation for reproducibility.
- Add document-version administration and incremental re-indexing.
- Add production observability, cost tracking, and redaction controls.
- Add a dedicated Compliance Reviewer when the workflow grows beyond three agents.

