# Take-Home Assignment: Multi-Agent AI Assistant

**Time expectation:** Approximately 3 hours maximum.

## Overview

Build a **multi-agent AI assistant** with a simple chat interface.

Choose any topic you like, such as:

- Travel
- Science
- Products
- Learning
- Technical support
- Research

## Requirements

Your solution should include:

- **An LLM**
- **A small RAG knowledge base**
- **At least 3 tools**
- **At least 2 agents** with different responsibilities
- **An agentic framework**, such as LangGraph, CrewAI, or AutoGen
- **A simple frontend** (React preferred)

### Dynamic Decision-Making

The system should make some decisions dynamically rather than following a fully hard-coded workflow.

For example, it might decide:

- Which agent should handle a task
- Which tool to use
- Whether RAG is needed
- Whether another agent should review or continue the work

Agents should have distinct roles, such as **research**, **analysis**, **planning**, or **verification**.

**At least one example must require multiple agents and/or tools to work together before answering the user.**

## RAG and Tools

Use a small set of documents as the knowledge base.

Provide **at least 3 tools**, for example:

1. Search the knowledge base
2. Perform a calculation
3. Query structured data
4. Call a public API
5. Compare or filter information

## Full-Stack Application

Provide a basic chat UI where users can ask questions and see responses.

The backend should handle:

- LLM calls
- Agent orchestration
- Tool execution
- RAG
- Conversation state

## Deliverables

Please share the following:

### 1. Source Code

A Git repository containing the source code.

### 2. README

A short README explaining:

- How to run the application
- Technologies used
- System architecture
- Agents and their responsibilities
- Tools and RAG implementation
- How agents coordinate
- What you would improve with more time

### 3. Example Questions

A few example questions demonstrating:

- **RAG**
- **Tool use**
- **Multi-agent collaboration**

## Evaluation Criteria

We care more about:

- Good engineering judgment
- Clear architecture
- Your ability to explain your decisions

…than about complexity.

**You may use AI coding tools.**

We will use the assignment as a starting point for discussion during the interview.
