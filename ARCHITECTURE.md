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
│    LINE OA Bot       │      │         LIFF App              │
│  (Messaging API)     │      │  - Intake form (คดีใหม่)      │
│                      │      │  - Upload เอกสาร              │
│  ตอบ chat            │      │  - ดู status คดี              │
│  ส่ง quick reply     │      │  - จองนัดหมาย                 │
│  push notification   │      │                               │
└──────────┬───────────┘      └──────────────┬────────────────┘
           │                                  │
           └────────────────┬─────────────────┘
                            │ webhook / REST API
                            ▼
┌───────────────────────────────────────────────────────────────┐
│                    Backend API  (Node.js)                      │
│                                                               │
│   /webhook/line    ← รับ event จาก LINE                       │
│   /api/chat        ← ส่ง message ไป AI agent                  │
│   /api/intake      ← รับ form data จาก LIFF                   │
│   /api/upload      ← รับไฟล์ เอกสารคดี                        │
│   /api/admin/*     ← upload เอกสารกฎหมายเข้า RAG              │
└───────────────────────────────┬───────────────────────────────┘
                                │
               ┌────────────────┴───────────────┐
               │                                │
               ▼                                ▼
┌──────────────────────────┐    ┌───────────────────────────────┐
│   AI Agent (adkcode)     │    │         Odoo                  │
│   Google ADK + Gemini    │    │                               │
│                          │    │  CRM  — leads, cases          │
│   orchestrator           │    │  Calendar — นัดหมาย           │
│     ├── legal_advisor    │    │  Billing — invoice            │
│     ├── doc_drafter      │    │  Documents — file storage     │
│     └── intake_analyst   │    │  Staff — ทนาย / admin         │
│                          │    │                               │
│   RAG Tool ←──────────┐  │    └───────────────────────────────┘
└──────────────────────┬─┘  │
                       │    │ XML-RPC / REST
                       │    └──────────────────────────────────┐
                       ▼                                       │
┌──────────────────────────────────────────────┐              │
│             RAG Engine (rag.py)              │◄─────────────┘
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

## Data Flow: ลูกค้าถามคำถาม

```
1. ลูกค้าพิมพ์ใน LINE
2. LINE → webhook → Backend API
3. Backend → adkcode orchestrator
4. orchestrator → legal_advisor agent
5. legal_advisor → RAG tool → ค้นหาฎีกา/กฎหมายที่เกี่ยวข้อง
6. RAG → top-K chunks → ส่งกลับ agent
7. agent + context → Gemini → สร้างคำตอบ
8. คำตอบ + แหล่งอ้างอิง → LINE reply
```

## Data Flow: รับ Case ใหม่

```
1. ลูกค้ากด "ปรึกษาทนาย" → เปิด LIFF
2. กรอก: ชื่อ, เบอร์, ประเภทคดี, รายละเอียด, แนบไฟล์
3. LIFF POST → Backend API /api/intake
4. Backend → intake_analyst agent → วิเคราะห์ + สรุป
5. Backend → Odoo XML-RPC → สร้าง CRM Lead
6. LINE push → แจ้งลูกค้าว่ารับเรื่องแล้ว
7. ทนายดู lead ใน Odoo → รับเคส → นัดหมาย
8. LINE push → แจ้งวัน/เวลานัด
```

## Data Flow: Admin Upload เอกสารกฎหมาย

```
1. Admin upload PDF ผ่าน web portal
2. Backend → extract text (pdfplumber)
3. Tag metadata (ประเภท, เลขคดี, ปี, ศาล)
4. Chunk → Embed (Gemini) → เพิ่มเข้า index
5. ระบบพร้อมใช้งานทันที
```

---

## Agent Roles (Legal)

| Agent | หน้าที่ | Tools |
|-------|---------|-------|
| **orchestrator** | รับ request, route ไป sub-agent | web_search, web_fetch, rag_search |
| **legal_advisor** | ตอบคำถามกฎหมาย + อ้างอิง | rag_search, web_search |
| **doc_drafter** | Draft สัญญา / เอกสาร | rag_search, write_file |
| **intake_analyst** | วิเคราะห์คดี + สรุป | rag_search, odoo_create_lead |

---

## Environment Variables

```bash
# AI
GOOGLE_API_KEY=...
ADKCODE_MODEL_SMART=gemini-2.5-flash
ADKCODE_MODEL_FAST=gemini-2.0-flash

# LINE
LINE_CHANNEL_ACCESS_TOKEN=...
LINE_CHANNEL_SECRET=...

# Odoo
ODOO_URL=https://...
ODOO_DB=...
ODOO_USER=...
ODOO_PASSWORD=...

# RAG
RAG_COLLECTION_PATH=./data/legal_index
```
