# PeopleGuide

PeopleGuide is a small multi-agent HR policy assistant for the fictional company Northstar Systems Ltd. It answers questions about leave, flexible work, expenses, benefits, and HR procedures using policy retrieval, synthetic employee data, deterministic tools, and OpenAI models.

## Technology

- FastAPI and Pydantic backend
- LangGraph orchestration
- OpenAI for all LLM and embedding calls
- Qdrant local persistent vector store
- React, TypeScript, and Vite frontend
- Server-Sent Events for workflow progress
- Pytest for backend tests

## Repository layout

```text
backend/                FastAPI, LangGraph, RAG, tools, and tests
frontend/               React chat interface
data/policies/          Synthetic Markdown policy knowledge base
data/structured/        Synthetic employees and reference tables
docs/policy-matrix.md   Authoritative demo policy rules
docs/project-outline.md Architecture and implementation decisions
Example_Questions.md    A set of demo questions, with expected outcome
```

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

### Prerequisites

- Python 3.12 or later
- Node.js 20 or later
- An OpenAI API key with access to the configured chat and embedding models

### Quick start

From the repository root, create the local environment file:

```bash
cp .env.example .env
```

Add your API key to `.env`:

```dotenv
OPENAI_API_KEY=your-api-key
LLM_MODEL=gpt-6-luna
LLM_TEMPERATURE=0
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Then run:

```bash
./setup.sh
```

The setup script:

- creates a Python virtual environment in `.venv`
- installs the backend and frontend dependencies
- builds the local Qdrant policy index if it does not exist
- starts FastAPI at `http://localhost:8000`
- starts the React application at `http://localhost:5173`

Open `http://localhost:5173` in a browser. Interactive API documentation is available at
`http://localhost:8000/docs`. Press `Ctrl+C` in the setup terminal to stop both servers.

The script is safe to run again. To force a rebuild of the policy index after changing documents,
use:

```bash
./setup.sh --reindex
```

By default, the script uses `python3.12`. If Python 3.12 or later is installed under another command
name, provide it when starting the script:

```bash
PEOPLEGUIDE_PYTHON_BIN=python3.13 ./setup.sh
```

### Manual setup

Create the environment and install the backend dependencies:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e 'backend[dev]'
```

Install the frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

Build the policy index:

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
npm run dev
```
## Improvements with more time

- Replace in-memory LangGraph checkpoints with PostgreSQL persistence.
- Add authentication and employee-level authorization.
- Add a labeled retrieval and response evaluation suite.
- Pin model snapshots after evaluation for reproducibility.
- Add document-version administration and incremental re-indexing.
- Add production observability, cost tracking, and redaction controls.
- Add a dedicated Compliance Reviewer when the workflow grows beyond three agents.

