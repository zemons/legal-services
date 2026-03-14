# Roadmap

## Phase 1 — RAG Core
- [x] ดัดแปลง `adkcode/rag.py` รองรับ PDF เอกสารกฎหมาย
- [x] PDF text extraction (pdfplumber)
- [x] Legal document chunking strategy (แบ่งตามมาตรา/ส่วน)
- [x] YAML frontmatter parser — อ่าน/เขียน metadata ในรูปแบบ YAML frontmatter
- [x] Metadata tagging — ฎีกา: ประเภท, เลขคดี, ปี, ศาล, result, legal_basis, key_facts, ruling_principle
- [x] Metadata tagging — กฎหมาย/ระเบียบ: ประเภท, เลขมาตรา, หมวด, วันบังคับใช้
- [x] แยก collections: dika, statute, regulation, contract, firm, strategy_patterns
- [x] สร้างโครงสร้าง `data/knowledge/` + ตัวอย่างเอกสาร (ฎีกา, กฎหมาย อย่างละ 2-3 ฉบับ)
- [x] สร้าง strategy_patterns collection schema (เตรียมโครงสร้างรอ Phase 2)
- [x] Similarity search by key_facts — ค้นฎีกาจากข้อเท็จจริงที่คล้ายกัน
- [ ] ทดสอบ search คุณภาพกับเอกสารจริง (ทั้ง keyword + semantic) ← ต้องรอ GOOGLE_API_KEY + เอกสารจริง
- [x] ตอบคำถาม RAG_QUESTIONS.md

## Phase 2 — Legal Agents
- [x] สร้าง agents ใหม่: legal_advisor, doc_drafter, intake_analyst, ocr_legal_doc, case_strategist
- [x] สร้าง `plugins/legal/` พร้อม SKILL.md + commands
- [x] case_strategist: IRAC reasoning chain + strategy_patterns lookup + feedback loop
- [ ] ทดสอบ chat กับ adkcode web UI ← ต้องรอ GOOGLE_API_KEY + install google-adk

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

## Phase 6 — Document Sync (Resilio)
- [ ] ติดตั้ง Resilio Sync บน server + ทดสอบกับเครื่อง client
- [ ] Case folder structure: _ai/, intake/, evidence/, drafts/, correspondence/
- [ ] Resilio API → Odoo file-event controller (event-driven)
- [ ] AI Watch: เอกสารใหม่ → adkcode อ่าน/สรุป → อัปเดต _ai/ folder
- [ ] Selective Sync ตาม collaborator_ids ใน legal_case
- [ ] LINE push แจ้งทนายเมื่อ AI อัปเดตแนวคดี

## Phase 7 — Production
- [ ] Docker Compose setup (Odoo + adkcode)
- [ ] Auth / security
- [ ] Multi-user support
- [ ] Monitoring / audit log

---

## Decisions Made (ดู RAG_QUESTIONS.md)

- ✅ Embedding model: **Gemini** (gemini-embedding-001, 768-dim)
- ✅ Vector storage: **JSON file** (แยกต่อ collection, อัปเกรด Qdrant เมื่อเกิน 10k chunks)
- ✅ Document metadata schema: **YAML frontmatter** (ดู RAG_QUESTIONS.md #3)
- ✅ Chunking strategy: **แบ่งตามโครงสร้างเอกสาร** ไม่ใช่ตามจำนวนบรรทัด
- ✅ Collection architecture: **แยก index file ต่อ collection**
- ✅ Template เอกสาร: **ทนายเขียน/รวบรวม** เก็บใน `data/templates/`
