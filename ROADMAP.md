# Roadmap

## Phase 1 — RAG Core
- [ ] ดัดแปลง `adkcode/rag.py` รองรับ PDF เอกสารกฎหมาย
- [ ] PDF text extraction (pdfplumber)
- [ ] Metadata tagging (ประเภท, เลขคดี, ปี, ศาล)
- [ ] Legal document chunking strategy
- [ ] ทดสอบ search คุณภาพกับเอกสารจริง
- [ ] ตอบคำถาม RAG_QUESTIONS.md

## Phase 2 — Legal Agents
- [ ] สร้าง agents ใหม่: legal_advisor, doc_drafter, intake_analyst
- [ ] สร้าง `plugins/legal/` พร้อม SKILL.md
- [ ] ทดสอบ chat กับ adkcode web UI

## Phase 3 — LINE Bot
- [ ] Node.js webhook server
- [ ] LINE Messaging API integration
- [ ] เชื่อม LINE → adkcode API server
- [ ] ทดสอบ flow ตอบคำถาม

## Phase 4 — LIFF
- [ ] Intake form (React)
- [ ] File upload
- [ ] Admin upload portal (เพิ่มเอกสารกฎหมายเข้า RAG)

## Phase 5 — Odoo
- [ ] XML-RPC connector
- [ ] Auto-create CRM lead จาก intake
- [ ] Calendar / นัดหมาย
- [ ] Billing

## Phase 6 — Production
- [ ] Docker Compose setup
- [ ] Auth / security
- [ ] Multi-user support
- [ ] Monitoring / audit log

---

## Pending Decisions (ดู RAG_QUESTIONS.md)

- Embedding model: Gemini vs OpenAI
- Vector storage: JSON file vs Qdrant
- Admin upload interface
- Document metadata schema
- Template เอกสาร: หา template คำร้อง / สัญญา มาเก็บใน RAG
