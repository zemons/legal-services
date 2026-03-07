# Roadmap

## Phase 1 — RAG Core
- [ ] ดัดแปลง `adkcode/rag.py` รองรับ PDF เอกสารกฎหมาย
- [ ] PDF text extraction (pdfplumber)
- [ ] Metadata tagging (ประเภท, เลขคดี, ปี, ศาล)
- [ ] Legal document chunking strategy
- [ ] ทดสอบ search คุณภาพกับเอกสารจริง
- [ ] ตอบคำถาม RAG_QUESTIONS.md

## Phase 2 — Legal Agents
- [ ] สร้าง agents ใหม่: legal_advisor, doc_drafter, intake_analyst, ocr_legal_doc
- [ ] สร้าง `plugins/legal/` พร้อม SKILL.md
- [ ] ทดสอบ chat กับ adkcode web UI

## Phase 3 — LINE Bot (Odoo controller)
- [ ] LINE webhook controller ใน `line_integration` module
- [ ] เรียก adkcode API จาก Odoo controller
- [ ] LINE Messaging API (reply, push, quick reply)
- [ ] รับรูปจากทนาย → ถาม [เก็บเข้าคลัง] → OCR → RAG
- [ ] ทดสอบ flow ตอบคำถาม

## Phase 4 — LIFF Pages (Odoo website/portal)
- [ ] สร้าง `legal_liff` module
- [ ] Intake form (QWeb template, mobile-responsive)
- [ ] File upload (ir.attachment)
- [ ] Document viewer + approve/revise
- [ ] Capture page (ถ่ายรูปฎีกา → OCR → ตรวจ metadata → เข้า RAG)
- [ ] LIFF SDK integration (LINE profile)
- [ ] LINE user_id → partner auth

## Phase 5 — Odoo CRM + Billing
- [ ] Auto-create CRM lead จาก intake (ผ่าน ORM ตรง)
- [ ] Calendar / นัดหมาย
- [ ] Billing / invoice
- [ ] Lawyer case dashboard (LIFF page)

## Phase 6 — Production
- [ ] Docker Compose setup (Odoo + adkcode)
- [ ] Auth / security
- [ ] Multi-user support
- [ ] Monitoring / audit log

---

## Pending Decisions (ดู RAG_QUESTIONS.md)

- Embedding model: Gemini vs OpenAI
- Vector storage: JSON file vs Qdrant
- Document metadata schema
- Template เอกสาร: หา template คำร้อง / สัญญา มาเก็บใน RAG
