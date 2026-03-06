# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered online law firm platform using LINE OA as main channel. Core AI engine is `adkcode/` (Google ADK + Gemini). See CONCEPT.md for full design.

## Key Files

- `CONCEPT.md` — master design doc (UX per role, LIFF plan, Odoo modules, document strategy)
- `ARCHITECTURE.md` — system diagram and data flows
- `AGENTS.md` — legal AI agent instructions loaded by adkcode
- `RAG_QUESTIONS.md` — pending decisions before RAG development starts
- `adkcode/adkcode/rag.py` — RAG engine (needs modification for PDF legal docs)
- `adkcode/adkcode/agent.py` — multi-agent orchestrator

## adkcode Architecture

adkcode is a multi-agent system built on Google ADK:
- `agent.py` — builds agents from AGENTS.md + plugins, runs ADK session loop
- `rag.py` — embedding (gemini-embedding-001, 768-dim), cosine similarity, JSON index storage
- `tools.py` — 11 tools: read_file, write_file, edit_file, list_files, grep, shell, web_fetch, web_search, read_image, index_codebase, semantic_search
- `guardrails.py` — ALLOWED_DIRS whitelist, BLOCKED_COMMANDS, audit_log
- `plugin_loader.py` — loads plugins from `plugins/` (plugin.json + SKILL.md + commands/*.md)

## Legal Agents (to be built)

Replace coder/reviewer/tester with:
- `orchestrator` — route to sub-agents
- `legal_advisor` — answer questions using RAG, cite ฎีกา/กฎหมาย
- `doc_drafter` — draft contracts/documents from templates
- `intake_analyst` — analyze case intake → create Odoo lead

## RAG Modification Plan

Current `rag.py` only handles code files. Needs:
1. PDF extraction via pdfplumber
2. Legal document chunking (by section/มาตรา)
3. YAML frontmatter metadata support (type, case_no, court, year, category, topic)
4. Separate collections: dika, statute, regulation, contract, firm

## Document Storage

```
data/
├── knowledge/  ← semantic search (ฎีกา, กฎหมาย) — Markdown + YAML frontmatter
├── templates/  ← read_file + fill {{field}} placeholders (สัญญา, คำร้อง)
└── cases/      ← per case_id, not indexed in RAG
```

## Odoo Modules

Two custom modules to write:
- `legal_case` — extends crm.lead with case_type, case_status, court_id, statute_deadline, court_dates, line_user_id
- `line_integration` — LINE webhook endpoint, push notifications, LINE user ↔ partner mapping

## Environment Variables

```bash
GOOGLE_API_KEY=
ADKCODE_MODEL_SMART=gemini-2.5-flash
ADKCODE_MODEL_FAST=gemini-2.0-flash
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
ODOO_URL=
ODOO_DB=
ODOO_USER=
ODOO_PASSWORD=
RAG_COLLECTION_PATH=./data/legal_index
```

## Running adkcode

```bash
cd adkcode
cp .env.example .env   # fill in GOOGLE_API_KEY
pip install -e .
python -m adkcode
```
