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
| LINE Bot | Node.js + @line/bot-sdk |
| LIFF | React |
| Backend API | Node.js (Express) |
| CRM / Billing | Odoo |
| Deploy | Docker Compose |

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
→ อยากปรึกษาทนาย กด button → LIFF Intake Form (4-5 ฟิลด์)
→ ถ่ายรูปเอกสาร (optional) / ส่งไฟล์ใน LINE ทีหลัง
→ รับ push notification ใน LINE
→ ดู status กด link → LIFF Case Status
```

### ทนายความ (Lawyer)
- อยู่ศาลบ่อย → ใช้มือถือเป็นหลักระหว่างวัน
- ต้องการ AI summary ของ case ทันที
- นั่ง PC ที่สำนักงานได้ช่วงเช้า/เย็น

```
มี lead ใหม่ → LINE push + AI summary 3 บรรทัด
→ [รับเคส] [ส่งต่อ] [นัดปรึกษา] (Quick Reply)
→ [ดูรายละเอียด] → LIFF Case Dashboard
→ update status / นัดหมาย → sync Odoo → bot แจ้งลูกค้าเอง
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
| 3 | กรอกข้อมูลคดี | LIFF Intake Form |
| 4 | ถ่ายรูปเอกสารกระดาษ | LIFF camera input |
| 5 | ส่งไฟล์ PDF/รูป | LINE Chat (forward file) |
| 6 | ยืนยัน/ขอแก้ไข draft เอกสาร | LIFF Document Viewer + ปุ่ม |
| 7 | จองนัดหมาย | LIFF Appointment (ปฏิทิน) |
| 8 | ชำระเงิน | LIFF Payment (QR PromptPay) |
| 9 | ตอบ yes/no | LINE Quick Reply |

### ทนายความ
| # | Interface | เครื่องมือ |
|---|-----------|-----------|
| 10 | รับ/ปฏิเสธเคสใหม่ | LINE Quick Reply |
| 11 | ดู list คดี + รับเคส | LIFF Case Dashboard |
| 12 | Update status คดี | LIFF Case Dashboard |
| 13 | นัดหมายลูกค้า/ศาล | LIFF Schedule |
| 14 | ตรวจสอบ/แก้ไข draft เอกสาร | Odoo Web (PC) |
| 15 | Billing / invoice | Odoo Web (PC) |

### Admin / Staff
| # | Interface | เครื่องมือ |
|---|-----------|-----------|
| 16 | Upload ฎีกา/กฎหมายเข้า RAG | Web Admin Portal (PC) |
| 17 | Tag metadata เอกสาร | Web Admin Portal form |
| 18 | จัดการ template สัญญา | Web Admin Portal (PC) |
| 19 | ดู/assign lead ให้ทนาย | Odoo CRM |
| 20 | ส่ง draft กลับลูกค้า | Odoo / Web Portal |

---

## LIFF Apps (ตาม Role)

### Client LIFF
| # | ชื่อ | หน้าที่ | Phase |
|---|------|---------|-------|
| 1 | Intake Form | กรอกข้อมูลคดี + ถ่ายรูปเอกสาร (optional) | 1 |
| 2 | Document Viewer | ดู draft, ยืนยัน/ขอแก้ไข, download PDF | 1 |
| 3 | Case Status | timeline คดี, วันนัดศาล | 2 |
| 4 | Appointment | จองนัดปรึกษา, sync Odoo Calendar | 2 |
| 5 | Payment | ดู invoice, ชำระ PromptPay | 3 |

### Lawyer LIFF
| # | ชื่อ | หน้าที่ | Phase |
|---|------|---------|-------|
| 6 | Case Dashboard | ดู list คดี, รับเคส, update status | 2 |
| 7 | Schedule | นัดลูกค้า, บันทึกวันนัดศาล | 2 |

**Admin → Web Admin Portal (PC) ไม่ใช่ LIFF**

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

### Custom Modules (เขียนเพิ่ม 2 modules)

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
# - ส่ง push notification เมื่อ status เปลี่ยน
# - ส่ง push เมื่อมีนัดหมายใหม่
# - map LINE user_id ↔ res.partner
# - log ประวัติการแจ้งเตือน
```

---

## Pending Decisions

ดู `RAG_QUESTIONS.md` สำหรับประเด็นที่ต้องตัดสินใจก่อนพัฒนา RAG
