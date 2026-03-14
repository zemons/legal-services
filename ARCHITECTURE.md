# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER (ลูกค้า)                             │
│                LINE App  /  LIFF Browser                         │
└──────────────┬──────────────────────────┬───────────────────────┘
               │ chat / webhook           │ form / upload (LIFF)
               ▼                          ▼
┌──────────────────────┐      ┌───────────────────────────────┐
│    LINE OA Bot       │      │    Odoo Website / Portal       │
│  (Messaging API)     │      │  (LIFF pages served by Odoo)   │
│                      │      │                               │
│  ตอบ chat            │      │  - Intake form (คดีใหม่)      │
│  ส่ง quick reply     │      │  - Upload เอกสาร              │
│  push notification   │      │  - ดู status คดี              │
│                      │      │  - จองนัดหมาย                 │
└──────────┬───────────┘      └──────────────┬────────────────┘
           │                                  │
           └────────────────┬─────────────────┘
                            │ webhook / controller
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                         Odoo 18                               │
│                                                               │
│   line_integration module:                                    │
│     /line/webhook     ← รับ event จาก LINE (รวม image OCR)    │
│                                                               │
│   legal_liff module:                                          │
│     /liff/intake      ← intake form (website page)            │
│     /liff/upload      ← รับไฟล์เอกสารคดี                      │
│     /liff/document    ← ดู draft / ยืนยัน                     │
│     /liff/status      ← ดู status คดี                         │
│     /liff/capture     ← ถ่ายรูปฎีกา → OCR → เข้า RAG          │
│                                                               │
│   legal_case module:                                          │
│     CRM  — leads, cases                                       │
│     Calendar — นัดหมาย                                        │
│     Billing — invoice                                         │
│     Documents — file storage (ir.attachment)                  │
│     Staff — ทนาย / admin                                      │
│                                                               │
│   adkcode connector:                                          │
│     เรียก AI agent ผ่าน HTTP                                   │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────┐
│   AI Agent (adkcode)                         │
│   Google ADK + Gemini                        │
│                                              │
│   orchestrator                               │
│     ├── legal_advisor                        │
│     ├── doc_drafter                          │
│     ├── intake_analyst                       │
│     ├── ocr_legal_doc (OCR + metadata)       │
│     └── case_strategist (แนวคดี + แผนต่อสู้)  │
│                                              │
│   RAG Tool ←─────────────────────────┐       │
└──────────────────────────────────────┤       │
                                       │       │
                                       ▼       │
┌──────────────────────────────────────────────┐
│             RAG Engine (rag.py)              │
│                                              │
│  PDF Ingest Pipeline:                        │
│    upload → extract text → chunk             │
│    → embed (Gemini) → index                  │
│                                              │
│  Search:                                     │
│    query → embed → cosine similarity         │
│    → top-K chunks → context                  │
│                                              │
│  Collections:                                │
│    dika         (ฎีกา)                       │
│    statute      (กฎหมาย)                     │
│    regulation   (ระเบียบ)                    │
│    contract     (สัญญาตัวอย่าง)               │
│    firm         (ความรู้ภายใน)                │
└──────────────────────────────────────────────┘
```

---

## Stack Change: No Separate Backend/LIFF

เดิมออกแบบเป็น 4 services (Backend Node.js, LIFF React, Odoo, adkcode)
เปลี่ยนเป็น 2 services เท่านั้น:

| เดิม | ใหม่ | เหตุผล |
|------|------|--------|
| Backend (Node.js Express) | Odoo controllers | ลด service, data อยู่ใน Odoo อยู่แล้ว |
| LIFF (React + Vite) | Odoo website/portal pages | ลด deploy, ใช้ ORM ตรง |
| Odoo | Odoo | เหมือนเดิม |
| adkcode | adkcode | เหมือนเดิม |

**ประโยชน์:**
- Deploy 2 containers แทน 4
- ไม่ต้อง XML-RPC กลับไปหา Odoo (controller อยู่ใน Odoo เลย)
- LIFF pages เข้าถึง ORM โดยตรง
- Auth ใช้ Odoo session / portal access rights
- File upload ใช้ `ir.attachment` ไม่ต้อง disk storage แยก

---

## Data Flow: ลูกค้าถามคำถาม

```
1. ลูกค้าพิมพ์ใน LINE
2. LINE → /line/webhook → Odoo line_integration controller
3. Controller → HTTP call → adkcode orchestrator
4. orchestrator → legal_advisor agent
5. legal_advisor → RAG tool → ค้นหาฎีกา/กฎหมายที่เกี่ยวข้อง
6. RAG → top-K chunks → ส่งกลับ agent
7. agent + context → Gemini → สร้างคำตอบ
8. คำตอบ + แหล่งอ้างอิง → LINE reply (via controller)
```

## Data Flow: รับ Case ใหม่

```
1. ลูกค้ากด "ปรึกษาทนาย" → เปิด LIFF → Odoo /liff/intake
2. กรอก: ชื่อ, เบอร์, ประเภทคดี, รายละเอียด, แนบไฟล์
3. LIFF form submit → Odoo controller
4. Controller → HTTP call → adkcode intake_analyst → วิเคราะห์ + สรุป
5. Controller → ORM → สร้าง CRM Lead + ir.attachment
6. LINE push → แจ้งลูกค้าว่ารับเรื่องแล้ว
7. ทนายดู lead ใน Odoo → รับเคส → นัดหมาย
8. LINE push → แจ้งวัน/เวลานัด
```

## Data Flow: Admin Upload เอกสารกฎหมาย

```
1. Admin upload PDF ผ่าน Odoo backend view
2. Controller → extract text (pdfplumber)
3. Tag metadata (ประเภท, เลขคดี, ปี, ศาล)
4. Chunk → Embed (Gemini) → เพิ่มเข้า index
5. ระบบพร้อมใช้งานทันที
```

## Data Flow: ทนายถ่ายรูปฎีกา → เข้า RAG

### วิธี A: ส่งรูปใน LINE chat (เร่งด่วน, อยู่ศาล)
```
1. ทนายถ่ายรูปฎีกา → ส่งใน LINE chat
2. LINE image event → Odoo webhook controller
3. Controller ตรวจ role = lawyer
4. bot ถาม "ต้องการเก็บเข้าคลังความรู้ไหม?"
   → Quick Reply: [เก็บเข้าคลัง] [ไม่ใช่]
5. กด [เก็บเข้าคลัง]
6. Controller → OCR (Google Vision API)
7. OCR text → adkcode ocr_legal_doc agent → ดึง metadata อัตโนมัติ
8. สร้าง Markdown + YAML frontmatter → เก็บ data/knowledge/dika/
9. Embed → เข้า RAG index
10. เก็บรูปต้นฉบับ → ir.attachment
11. bot ตอบ "เก็บแล้ว: ฎีกาที่ 1234/2566 เรื่องสัญญาเช่า"
```

### วิธี B: LIFF /liff/capture (มีเวลา, หลายหน้า)
```
1. ทนายกด [ถ่ายรูปฎีกา] ใน Rich Menu → เปิด LIFF /liff/capture
2. ถ่ายรูป / เลือกจาก gallery (หลายรูปได้)
3. Controller → OCR → แสดง preview ข้อความ
4. AI ดึง metadata อัตโนมัติ (เลขฎีกา, ปี, ศาล, หัวข้อ)
5. ทนายตรวจ / แก้ไข metadata → กด [บันทึก]
6. สร้าง Markdown → Embed → เข้า RAG + เก็บรูปต้นฉบับ
```

---

## Agent Roles (Legal)

| Agent | หน้าที่ | Tools |
|-------|---------|-------|
| **orchestrator** | รับ request, route ไป sub-agent | web_search, web_fetch, rag_search |
| **legal_advisor** | ตอบคำถามกฎหมาย + อ้างอิง | rag_search, web_search |
| **doc_drafter** | Draft สัญญา / เอกสาร | rag_search, write_file |
| **intake_analyst** | วิเคราะห์คดี + สรุป | rag_search, odoo_create_lead |
| **ocr_legal_doc** | OCR รูปถ่าย → ดึง metadata → จัด format | ocr_image, rag_index |
| **case_strategist** | วิเคราะห์มุมต่อสู้, ประเมินโอกาสชนะ, วางแผนคดี | rag_search, read_file |

---

## Document Sync (Resilio Sync)

ใช้ Resilio Sync (P2P) สำหรับ sync เอกสารคดีระหว่างเครื่องทนาย ↔ Platform server
ไม่เพิ่ม service ใหม่ — Resilio Client ติดตั้งบน server + เครื่องทนายแต่ละคน

```
ทนาย A (PC)              ทนาย B (PC)              Platform Server
Resilio Client            Resilio Client            Resilio Client
~/cases/2566-0042/        ~/cases/2566-0042/        /data/cases/2566-0042/
     │                         │                         │
     └──────── P2P Sync (AES-128 encrypted) ─────────────┘
                                                         │
                                                    Resilio API
                                                    (file event)
                                                         │
                                                         ▼
                                                  Odoo controller
                                                  POST /case/file-event
                                                         │
                                                         ▼
                                                  adkcode
                                                  case_strategist
```

### Case Folder Structure

```
cases/{case_id}/
├── _ai/                    ← AI เขียนอัตโนมัติ (sync กลับไปเครื่องทนาย)
│   ├── case_summary.md     ← สรุปคดีภาพรวม (อัปเดตเมื่อมีเอกสารใหม่)
│   ├── strategy.md         ← แนวคดี + มุมต่อสู้ + โอกาสชนะ
│   ├── document_index.json ← รายการเอกสาร + สรุปแต่ละชิ้น
│   └── related_dika.md     ← ฎีกาที่เกี่ยวข้อง (ค้นจาก RAG)
│
├── intake/                 ← เอกสารจากลูกค้า
├── evidence/               ← พยานหลักฐาน
├── drafts/                 ← ร่างเอกสาร (ทนายหรือ AI สร้าง)
└── correspondence/         ← หนังสือโต้ตอบ
```

### Sync Flow

```
1. ทนายลากไฟล์ใส่ ~/cases/{case_id}/intake/
2. Resilio sync → server + ทนายคนอื่นในทีม
3. Resilio API (file event) → Odoo controller
4. Odoo → adkcode: OCR/อ่านเอกสาร → สรุป → อัปเดต _ai/
5. _ai/ folder sync กลับ → ทนายเปิดอ่านได้ทันที
6. LINE push → "เอกสารใหม่ในคดี #2566-0042 — AI อัปเดตแนวคดีแล้ว"
```

### Selective Sync

ทนายแต่ละคน sync เฉพาะคดีที่รับผิดชอบ (Resilio Selective Sync)
access control จัดการผ่าน Odoo (collaborator_ids ใน legal_case)

---

## Data Flow: กำหนดแนวคดี (Case Strategy)

### วิธี A: Event-driven (เอกสารใหม่เข้ามา)

```
1. ทนายใส่เอกสารใน folder คดี
2. Resilio sync → server
3. Resilio API → Odoo → adkcode case_strategist
4. AI อ่านเอกสารทั้งหมดในคดี
5. ค้น RAG → หามาตรา/ฎีกาที่เกี่ยวข้อง
6. อัปเดต _ai/strategy.md + _ai/related_dika.md
7. sync กลับ → ทนายเปิดอ่านได้ + LINE push แจ้ง
```

### วิธี B: ทนายสั่งวิเคราะห์ (On-demand)

```
1. ทนายกด [วิเคราะห์แนวคดี] ใน LIFF /liff/cases หรือ Odoo backend
2. Odoo → adkcode case_strategist
3. AI อ่านเอกสารทั้งหมด + ค้น RAG
4. แสดงผล: มุมต่อสู้ 2-4 มุม + โอกาสชนะ + ฎีกาอ้างอิง
5. ทนายเลือกแนวคดี → AI สร้าง Litigation Plan
6. บันทึกลง Odoo + เขียน _ai/strategy.md
```

---

## Odoo Modules (3 modules)

| Module | หน้าที่ |
|--------|---------|
| `legal_case` | Extend crm.lead + court/court_date models |
| `line_integration` | LINE webhook, push notifications, LINE ↔ partner mapping |
| `legal_liff` | Website/portal pages สำหรับ LIFF (intake, document, status, appointment, capture) |

---

## Environment Variables

```bash
# AI
GOOGLE_API_KEY=...
ADKCODE_MODEL_SMART=gemini-2.5-flash
ADKCODE_MODEL_FAST=gemini-2.0-flash
ADKCODE_URL=http://adkcode:8000

# LINE
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_CHANNEL_SECRET=...
LINE_LIFF_ID=...

# Odoo (standard)
# configured via docker-compose / odoo.conf
```
