# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered online law firm platform using LINE OA as main channel. Core AI engine is `adkcode/` (Google ADK + Gemini). See CONCEPT.md for full design.

**Architecture: 2 services only** — Odoo 18 (handles everything: CRM, LINE webhook, LIFF pages) + adkcode (AI agents + RAG).
No separate Node.js backend or React LIFF app. LIFF pages are Odoo website/portal views.

## Key Files

- `CONCEPT.md` — master design doc (UX per role, LIFF pages, Odoo modules, document strategy)
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
- `ocr_legal_doc` — OCR รูปถ่ายเอกสารกฎหมาย → ดึง metadata → จัด format Markdown + YAML frontmatter

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

## Odoo Modules (3 custom modules)

- `legal_case` — extends crm.lead with case_type, case_status, court_id, statute_deadline, court_dates
- `line_integration` — LINE webhook controller, push notifications, LINE user ↔ partner mapping, adkcode API connector
- `legal_liff` — website/portal pages for LIFF (intake form, document viewer, case status, appointment, lawyer dashboard, capture ฎีกา)

## LIFF Pages (Odoo website/portal)

LIFF opens in LINE in-app browser → points to Odoo routes:
- `/liff/intake` — intake form
- `/liff/document/<id>` — document viewer + approve/revise
- `/liff/status/<id>` — case status timeline
- `/liff/appointment` — booking calendar
- `/liff/cases` — lawyer case dashboard
- `/liff/schedule` — lawyer schedule
- `/liff/capture` — ถ่ายรูปฎีกา/เอกสาร → OCR → ตรวจ metadata → เข้า RAG

Uses LIFF SDK via `<script>` tag for LINE profile. Auth via LINE user_id → partner mapping.

## Environment Variables

```bash
GOOGLE_API_KEY=
ADKCODE_MODEL_SMART=gemini-2.5-flash
ADKCODE_MODEL_FAST=gemini-2.0-flash
ADKCODE_URL=http://adkcode:8000
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
LINE_LIFF_ID=
```

## Running adkcode

```bash
cd adkcode
cp .env.example .env   # fill in GOOGLE_API_KEY
pip install -e .
python -m adkcode
```
