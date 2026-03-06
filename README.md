# Legal Services — AI-Powered Online Law Firm

สำนักงานทนายความออนไลน์ที่ใช้ AI ช่วยอำนวยความสะดวกตลอด workflow
ตั้งแต่รับปรึกษา ตอบคำถาม ร่างเอกสาร จนถึงส่งต่อทนายจริง ผ่าน LINE OA เป็นช่องทางหลัก

## เอกสาร

| ไฟล์ | เนื้อหา |
|------|---------|
| [CONCEPT.md](CONCEPT.md) | Concept รวม: vision, UX per role, LIFF apps, Odoo modules, document strategy |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System diagram, data flows, agent roles, env vars |
| [AGENTS.md](AGENTS.md) | AI agent instructions สำหรับ adkcode |
| [ROADMAP.md](ROADMAP.md) | Development phases และ pending decisions |
| [RAG_QUESTIONS.md](RAG_QUESTIONS.md) | ประเด็นที่ต้องตัดสินใจก่อนพัฒนา RAG |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agent | adkcode (Google ADK + Gemini) |
| RAG Engine | adkcode/rag.py (ดัดแปลงรองรับ PDF กฎหมาย) |
| LINE Bot | Node.js + @line/bot-sdk |
| LIFF | React |
| Backend API | Node.js (Express) |
| CRM / Billing | Odoo (+ 2 custom modules) |
| Deploy | Docker Compose |

## Repository Structure

```
legal-services/
├── adkcode/          ← AI agent engine (cloned from monthop-gmail/adkcode)
├── CONCEPT.md        ← Design concept ทั้งหมด (อ่านตรงนี้ก่อน)
├── ARCHITECTURE.md   ← System architecture
├── AGENTS.md         ← Legal AI agent instructions
├── ROADMAP.md        ← Development roadmap
└── RAG_QUESTIONS.md  ← Pending RAG design decisions
```

## Development Phases

- **Phase 1** — RAG Core (adapt rag.py for legal PDFs)
- **Phase 2** — Legal Agents (legal_advisor, doc_drafter, intake_analyst)
- **Phase 3** — LINE Bot (webhook + messaging)
- **Phase 4** — LIFF Apps (React, client + lawyer)
- **Phase 5** — Odoo Integration (legal_case + line_integration modules)
- **Phase 6** — Production (Docker, auth, monitoring)
