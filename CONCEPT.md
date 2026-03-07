# Legal Services — Concept & Design

## Vision

สำนักงานทนายความออนไลน์ที่ใช้ AI ช่วยอำนวยความสะดวกตลอด workflow
ตั้งแต่รับปรึกษา ตอบคำถาม ร่างเอกสาร จนถึงส่งต่อทนายจริง
ผ่าน LINE OA เป็นช่องทางหลัก

---

## ความสามารถของระบบ

### AI ทำได้ทันที
- ตอบคำถามกฎหมายทั่วไป อ้างอิงฎีกา/กฎหมายจริง
- อธิบายขั้นตอน / อายุความ / ค่าธรรมเนียม
- คัดกรองประเภทคดี แนะนำทนายที่เหมาะสม
- Draft เอกสารเบื้องต้น (สัญญา, หนังสือทวงถาม, พินัยกรรม)
- OCR ถ่ายรูปฎีกา/เอกสารกฎหมาย → ดึง metadata → เก็บเข้า RAG

### AI + ทนาย
- รับ intake จากลูกค้า → วิเคราะห์ → สรุป → สร้าง lead ใน Odoo
- จัดการนัดหมาย / แจ้งเตือน deadline

### ทนายเท่านั้น
- ว่าความในศาล
- ลงนามเอกสารทางกฎหมาย
- บังคับคดี

---

## งานของสำนักงานทนายความ

### คดีในศาล
| กลุ่ม | ประเภทคดี |
|-------|----------|
| แพ่ง | สัญญา, หนี้สิน, ละเมิด, เรียกค่าเสียหาย |
| อาญา | ยักยอก, ฉ้อโกง, โจรกรรม, ทำร้ายร่างกาย |
| ครอบครัว | หย่า, แบ่งทรัพย์สิน, อำนาจปกครองบุตร |
| มรดก | ทำพินัยกรรม, แบ่งมรดก, คดีพิพาทมรดก |
| ที่ดิน | กรรมสิทธิ์, บุกรุก, โฉนด |
| แรงงาน | เลิกจ้างไม่เป็นธรรม, ค่าชดเชย |
| ปกครอง | โต้แย้งหน่วยงานรัฐ, ใบอนุญาต |
| ทรัพย์สินทางปัญญา | ลิขสิทธิ์, เครื่องหมายการค้า |
| ก่อสร้าง | ผู้รับเหมาทิ้งงาน, งานบกพร่อง |
| ประกันภัย | รถยนต์, อุบัติเหตุ, ประกันชีวิต |

### งานเอกสาร
- ร่าง / ตรวจสัญญา (ซื้อขาย, เช่า, กู้ยืม, จ้างงาน, รับเหมา)
- หนังสือทวงถาม / บอกเลิกสัญญา / มอบอำนาจ
- พินัยกรรม
- รับรองเอกสาร / Notary / แปลเอกสาร

### งานที่ปรึกษา
- จัดตั้งบริษัท / ข้อบังคับ / ผู้ถือหุ้น
- In-house counsel
- Due diligence ที่ดิน / บริษัท

### งานบังคับคดี / ติดตามหนี้
- สืบทรัพย์ลูกหนี้
- ยึด / อายัดทรัพย์
- เจรจาไกล่เกลี่ย / ประนอมหนี้

---

## Tech Stack

| Layer | เทคโนโลยี |
|-------|-----------|
| AI Agent | adkcode (Google ADK + Gemini) |
| RAG Engine | adkcode rag.py (ดัดแปลงรองรับ PDF) |
| LINE Bot | Odoo controller + LINE Messaging API |
| LIFF | Odoo website/portal pages (OWL + QWeb templates) |
| CRM / Billing | Odoo 18 |
| Deploy | Docker Compose (Odoo + adkcode) |

> **Design Decision**: ไม่ใช้ Node.js backend หรือ React LIFF แยก
> LIFF pages เป็น Odoo website pages — ลดจำนวน service, ใช้ ORM ตรง, auth ผ่าน Odoo session

---

## Document Storage Strategy

เอกสารมี 3 บทบาท → จัดเก็บต่างกัน

```
1. KNOWLEDGE  ← AI ค้นหาอ้างอิง   (ฎีกา, กฎหมาย)
2. TEMPLATE   ← AI เอาไป draft    (สัญญา, คำร้อง)
3. CASE FILE  ← AI วิเคราะห์คดี  (เอกสารลูกค้า)
```

### โครงสร้างโฟลเดอร์

```
data/
├── knowledge/
│   ├── dika/          ← ฎีกาศาลฎีกา
│   ├── statute/       ← ประมวลกฎหมาย
│   ├── regulation/    ← กฎกระทรวง, ระเบียบ
│   └── article/       ← บทความกฎหมาย
├── templates/
│   ├── contract/      ← สัญญาประเภทต่างๆ
│   ├── petition/      ← คำร้อง, คำฟ้อง
│   ├── letter/        ← หนังสือทวงถาม, บอกเลิก
│   └── will/          ← พินัยกรรม
└── cases/
    └── {case_id}/
        ├── intake.json
        └── documents/
```

### Metadata ของ Knowledge (ฎีกา/กฎหมาย)

```markdown
---
type: dika
case_no: 1234/2566
court: ศาลฎีกา
year: 2566
category: แพ่ง
topic: [สัญญาเช่า, ผิดนัด, ค่าเสียหาย]
summary: ผู้เช่าผิดนัดชำระค่าเช่า ผู้ให้เช่าบอกเลิกสัญญาได้
---
```

### โครงสร้าง Template

```markdown
---
type: template
name: สัญญาเช่าทรัพย์สิน
category: contract
required_fields: [ชื่อผู้ให้เช่า, ชื่อผู้เช่า, ค่าเช่า, วันเริ่ม, วันสิ้นสุด]
---

เนื้อหา template พร้อม {{field}} placeholder
⚠️ ต้องให้ทนายตรวจสอบก่อนลงนาม
```

### Index Strategy

| ประเภท | วิธี AI ใช้ | Index |
|--------|-----------|-------|
| ฎีกา / กฎหมาย | semantic search → อ้างอิง | ✓ |
| Template | read_file ทั้งไฟล์ → เติมข้อมูล | ✓ ค้นหาชื่อ |
| เอกสารคดี | read_file ตาม case_id | ✗ แยกต่างหาก |

---

## UX Design ตาม Role

### หลักการ: ออกแบบตามพฤติกรรมจริง ไม่ใช่ตามเทคโนโลยี

### ลูกค้า (Client)
- ใช้ LINE ทุกวัน — เป็น primary channel
- เจอปัญหาแล้วค่อยค้นหา อยู่ในสถานะกังวล/เครียด
- เอกสารส่วนมากเป็นกระดาษ → ถ่ายรูปง่ายกว่า upload PDF
- ไม่ชอบกรอกฟอร์มยาว → แบ่ง intake เป็น 2 ขั้นตอน

```
คุยกับ AI ก่อน (LINE chat)
→ อยากปรึกษาทนาย กด button → LIFF → Odoo /liff/intake (4-5 ฟิลด์)
→ ถ่ายรูปเอกสาร (optional) / ส่งไฟล์ใน LINE ทีหลัง
→ รับ push notification ใน LINE
→ ดู status กด link → LIFF → Odoo /liff/status
```

### ทนายความ (Lawyer)
- อยู่ศาลบ่อย → ใช้มือถือเป็นหลักระหว่างวัน
- ต้องการ AI summary ของ case ทันที
- เจอฎีกาที่ศาล → ถ่ายรูปเก็บเข้าคลังได้ทันที
- นั่ง PC ที่สำนักงานได้ช่วงเช้า/เย็น

```
มี lead ใหม่ → LINE push + AI summary 3 บรรทัด
→ [รับเคส] [ส่งต่อ] [นัดปรึกษา] (Quick Reply)
→ [ดูรายละเอียด] → LIFF → Odoo /liff/cases
→ update status / นัดหมาย → Odoo ORM → bot แจ้งลูกค้าเอง

เจอฎีกา / เอกสารกฎหมาย
→ ส่งรูปใน LINE chat → bot ถาม [เก็บเข้าคลัง] [ไม่ใช่]
→ หรือกด [ถ่ายรูปฎีกา] → LIFF → Odoo /liff/capture
→ OCR + AI ดึง metadata → ทนายตรวจ → เข้า RAG
```

### Admin / Staff
- นั่ง PC ที่สำนักงานตลอด
- Primary channel: Web Admin Portal (PC-first)

---

## Input Interfaces ทั้งระบบ

### ลูกค้า
| # | Interface | เครื่องมือ |
|---|-----------|-----------|
| 1 | พิมพ์ถามคำถามกฎหมาย | LINE Chat |
| 2 | เลือกประเภทคดีเบื้องต้น | LINE Rich Menu / Carousel |
| 3 | กรอกข้อมูลคดี | Odoo /liff/intake (via LIFF) |
| 4 | ถ่ายรูปเอกสารกระดาษ | Odoo /liff/intake camera input |
| 5 | ส่งไฟล์ PDF/รูป | LINE Chat (forward file) |
| 6 | ยืนยัน/ขอแก้ไข draft เอกสาร | Odoo /liff/document (via LIFF) |
| 7 | จองนัดหมาย | Odoo /liff/appointment (via LIFF) |
| 8 | ชำระเงิน | Odoo /liff/payment (via LIFF) |
| 9 | ตอบ yes/no | LINE Quick Reply |

### ทนายความ
| # | Interface | เครื่องมือ |
|---|-----------|-----------|
| 10 | รับ/ปฏิเสธเคสใหม่ | LINE Quick Reply |
| 11 | ดู list คดี + รับเคส | Odoo /liff/cases (via LIFF) |
| 12 | Update status คดี | Odoo /liff/cases (via LIFF) |
| 13 | นัดหมายลูกค้า/ศาล | Odoo /liff/schedule (via LIFF) |
| 14 | ถ่ายรูปฎีกา → OCR → เข้า RAG | Odoo /liff/capture (via LIFF) หรือ LINE chat ส่งรูป |
| 15 | ตรวจสอบ/แก้ไข draft เอกสาร | Odoo Web backend (PC) |
| 16 | Billing / invoice | Odoo Web backend (PC) |

### Admin / Staff
| # | Interface | เครื่องมือ |
|---|-----------|-----------|
| 16 | Upload ฎีกา/กฎหมายเข้า RAG | Odoo Web backend (PC) |
| 17 | Tag metadata เอกสาร | Odoo Web backend (PC) |
| 18 | จัดการ template สัญญา | Odoo Web backend (PC) |
| 19 | ดู/assign lead ให้ทนาย | Odoo CRM |
| 20 | ส่ง draft กลับลูกค้า | Odoo Web backend (PC) |

---

## LIFF Pages (Odoo Website/Portal)

LIFF เปิดใน LINE in-app browser → ชี้ไปหน้า Odoo website/portal
ใช้ LIFF SDK (`@line/liff`) ผ่าน `<script>` tag เพื่อดึง LINE profile

### Client Pages (via LIFF URL)
| # | Route | หน้าที่ | Phase |
|---|-------|---------|-------|
| 1 | `/liff/intake` | กรอกข้อมูลคดี + ถ่ายรูปเอกสาร (optional) | 1 |
| 2 | `/liff/document/<id>` | ดู draft, ยืนยัน/ขอแก้ไข, download PDF | 1 |
| 3 | `/liff/status/<id>` | timeline คดี, วันนัดศาล | 2 |
| 4 | `/liff/appointment` | จองนัดปรึกษา, sync Odoo Calendar | 2 |
| 5 | `/liff/payment/<id>` | ดู invoice, ชำระ PromptPay | 3 |

### Lawyer Pages (via LIFF URL)
| # | Route | หน้าที่ | Phase |
|---|-------|---------|-------|
| 6 | `/liff/cases` | ดู list คดี, รับเคส, update status | 2 |
| 7 | `/liff/schedule` | นัดลูกค้า, บันทึกวันนัดศาล | 2 |
| 8 | `/liff/capture` | ถ่ายรูปฎีกา/เอกสาร → OCR → ตรวจ metadata → เข้า RAG | 2 |

**Admin → Odoo backend views (PC) ไม่ใช่ LIFF**

### Implementation
- Odoo module: `legal_liff`
- Template engine: QWeb (server-side) + OWL (client-side interactivity)
- Mobile-responsive: ออกแบบสำหรับ LINE in-app browser
- Auth: LINE user_id → Odoo partner mapping (ไม่ต้อง login แยก)
- LIFF SDK: โหลดผ่าน `<script>` ใน base template เพื่อ `liff.getProfile()`

### งานที่ใช้ LINE Chat แทน LIFF
| งาน | ช่องทาง |
|-----|--------|
| ถามคำถามกฎหมาย | LINE chat + AI |
| รับแจ้งเตือนนัด | LINE push message |
| ตอบ yes/no | Quick reply button |
| เลือกประเภทคดีเบื้องต้น | Rich menu / Carousel |
| ส่งไฟล์เอกสาร (ทีหลัง) | LINE file message |

---

## Odoo Modules

### Standard Modules (ใช้ได้เลย)
| Module | ใช้ทำอะไร |
|--------|----------|
| CRM | รับ lead จาก LINE intake, assign ทนาย |
| Calendar | นัดหมายลูกค้า, วันนัดศาล |
| Contacts | ข้อมูลลูกค้า, คู่กรณี, ศาล |
| Accounting | invoice, รับชำระ, ค่าธรรมเนียม |
| Documents | เก็บไฟล์เอกสารคดี |
| Discuss | chat ภายในทีม |

### Custom Modules (เขียนเพิ่ม 3 modules)

**Module 1: `legal_case`** — extend crm.lead
```python
# fields เพิ่มเติม
case_type        # ประเภทคดี: แพ่ง/อาญา/ครอบครัว/ที่ดิน/แรงงาน...
case_status      # รับเรื่อง/กำลังดำเนินการ/รอนัดศาล/ปิดคดี
opposing_party   # ชื่อคู่กรณี
court_id         # ศาลที่พิจารณา (many2one)
statute_deadline # วันหมดอายุความ → trigger แจ้งเตือน
court_dates      # one2many วันนัดศาล
line_user_id     # เชื่อม LINE user ↔ res.partner
```

**Module 2: `line_integration`** — เชื่อม Odoo ↔ LINE
```python
# features
# - REST endpoint รับ webhook จาก LINE bot
# - เรียก adkcode AI agent ผ่าน HTTP
# - ส่ง push notification เมื่อ status เปลี่ยน
# - ส่ง push เมื่อมีนัดหมายใหม่
# - map LINE user_id ↔ res.partner
# - log ประวัติการแจ้งเตือน
```

**Module 3: `legal_liff`** — LIFF pages เป็น Odoo website/portal views
```python
# features
# - /liff/intake        — intake form (QWeb template)
# - /liff/document/<id> — document viewer + approve/revise
# - /liff/status/<id>   — case status timeline
# - /liff/appointment   — booking calendar
# - /liff/payment/<id>  — invoice + PromptPay
# - /liff/cases         — lawyer case dashboard
# - /liff/schedule      — lawyer schedule
# - /liff/capture       — ถ่ายรูปฎีกา → OCR → ตรวจ metadata → เข้า RAG
# - LIFF SDK integration via <script> tag
# - Mobile-responsive templates (LINE in-app browser)
# - LINE user_id → partner auth (no separate login)
```

---

## Pending Decisions

ดู `RAG_QUESTIONS.md` สำหรับประเด็นที่ต้องตัดสินใจก่อนพัฒนา RAG
