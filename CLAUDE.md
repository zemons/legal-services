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
- `RAG_QUESTIONS.md` — RAG design decisions (answered)
- `adkcode/adkcode/rag.py` — RAG engine (CodebaseIndex for code, LegalIndex for legal docs)
- `adkcode/adkcode/agent.py` — multi-agent orchestrator

## adkcode Architecture

adkcode is a multi-agent system built on Google ADK:
- `agent.py` — builds agents from AGENTS.md + plugins, runs ADK session loop
- `rag.py` — embedding (gemini-embedding-001, 768-dim), cosine similarity, JSON index storage
- `tools.py` — 14 tools: read_file, write_file, edit_file, list_files, grep, shell, web_fetch, web_search, read_image, index_codebase, semantic_search, index_legal_docs, legal_search, legal_search_by_facts
- `guardrails.py` — ALLOWED_DIRS whitelist, BLOCKED_COMMANDS, audit_log
- `plugin_loader.py` — loads plugins from `plugins/` (plugin.json + SKILL.md + commands/*.md)

## Legal Agents (implemented)

agent.py มี 5 legal sub-agents แทน coder/reviewer/tester:
- `orchestrator` — route ไป sub-agent ที่เหมาะสม + tools: web_search, legal_search
- `legal_advisor` — ตอบคำถามกฎหมาย อ้างอิง RAG + tools: legal_search, legal_search_by_facts
- `doc_drafter` — draft สัญญา/คำร้อง จาก template + tools: read_file, write_file, legal_search
- `intake_analyst` — วิเคราะห์ intake คัดกรองคดี + tools: legal_search
- `ocr_legal_doc` — OCR รูปถ่ายเอกสาร → metadata → RAG + tools: read_image, write_file
- `case_strategist` — IRAC Framework วิเคราะห์มุมต่อสู้ + tools: legal_search, legal_search_by_facts

### Legal Plugin (`plugins/legal/`)
5 skills: legal-advisor, case-strategy, document-drafting, intake-analysis, ocr-legal-doc
5 commands: /analyze-case, /find-dika, /draft, /intake, /ocr

## RAG Architecture (implemented)

`rag.py` มี 2 classes:
- **CodebaseIndex** — index code files (เดิม)
- **LegalIndex** — index legal documents with metadata + collections

### LegalIndex features
- YAML frontmatter parser (built-in, ไม่ต้องพึ่ง lib)
- PDF text extraction via pdfplumber
- แยก collections: dika, statute, regulation, article, strategy_patterns
- แยก index file ต่อ collection (`.index_dika.json`, `.index_statute.json`, etc.)
- `search()` — semantic search across collections + metadata_filter
- `search_by_key_facts()` — ค้นฎีกาจากข้อเท็จจริงที่คล้ายกัน (boost score ตาม overlap)

### Legal tools ใน tools.py
- `index_legal_docs(collection)` — build index
- `legal_search(query, collections)` — semantic search
- `legal_search_by_facts(facts)` — search by key_facts similarity

### RAG design decisions (ดู RAG_QUESTIONS.md)
- Embedding: Gemini (gemini-embedding-001, 768-dim)
- Storage: JSON file per collection (อัปเกรด Qdrant เมื่อเกิน 10k chunks)
- Chunking: ตามโครงสร้างเอกสาร (1 ฎีกา = 1 chunk, กฎหมายแบ่งตามมาตรา)
- IRAC reasoning chain for case_strategist (Phase 2)
- Feedback loop: คดีจบ → บันทึก strategy_pattern → AI เรียนรู้จากคดีจริง (Phase 2)

## Document Storage & Sync

```
data/
├── knowledge/  ← semantic search (ฎีกา, กฎหมาย, strategy_patterns) — Markdown + YAML frontmatter
├── templates/  ← read_file + fill {{field}} placeholders (สัญญา, คำร้อง)
└── cases/      ← per case_id, synced via Resilio Sync (P2P)
    └── {case_id}/
        ├── _ai/          ← AI auto-generated (case_summary.md, strategy.md, related_dika.md)
        ├── intake/       ← client documents
        ├── evidence/     ← evidence files
        ├── drafts/       ← draft documents
        └── correspondence/
```

**Resilio Sync**: P2P file sync ระหว่างเครื่องทนาย ↔ server — event-driven AI watch (Resilio API → Odoo → adkcode)

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
