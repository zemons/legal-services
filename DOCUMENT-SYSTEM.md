# ระบบสร้างเอกสาร (Document Generation System)

> Legal LIFF — ระบบสร้างเอกสารกฎหมายอัตโนมัติ ผ่าน LINE + Odoo 18

---

## สถาปัตยกรรมภาพรวม

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  LINE LIFF  │────▶│  Odoo 18     │────▶│  Gemini AI   │
│  (Frontend) │◀────│  (Backend)   │◀────│  (Template)  │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
                    ┌──────┴───────┐
                    │  PostgreSQL  │
                    └──────────────┘
```

---

## 1. Database Models

### 1.1 `legal.document.template` — Template เอกสาร

| Field | Type | คำอธิบาย |
|-------|------|----------|
| `name` | Char | ชื่อ Template (เช่น สัญญาเช่าทรัพย์สิน) |
| `code` | Char | รหัส (เช่น contract/rental-agreement) |
| `category` | Selection | ประเภท: contract, letter, petition, will |
| `field_ids` | One2many | รายการ fields ที่ต้องกรอก (แก้ไขได้ใน Admin) |
| `required_fields` | Text | JSON array — auto-sync จาก field_ids |
| `template_file_path` | Char | path ไฟล์ template (เช่น docx-masters/contract/rental-agreement.docx) |
| `master_docx` | Binary | ไฟล์ .docx ต้นแบบ (อัพโหลดโดย Admin) |
| `processed_docx` | Binary | ไฟล์ที่ AI สร้าง template แล้ว (มี {{placeholder}}) |
| `processing_state` | Selection | สถานะ: none → uploaded → processing → ready → error |

### 1.2 `legal.document.template.field` — Field ของ Template

| Field | Type | คำอธิบาย |
|-------|------|----------|
| `name` | Char | ชื่อ placeholder (เช่น grantor_name → `{{grantor_name}}`) |
| `label` | Char | ชื่อแสดงในฟอร์ม (เช่น ชื่อผู้มอบอำนาจ) |
| `field_type` | Selection | ประเภท: text, number, date, textarea, select, **address** |
| `required` | Boolean | จำเป็นต้องกรอก หรือไม่ |
| `options` | Char | ตัวเลือก (สำหรับ select) คั่นด้วย `,` |
| `sequence` | Integer | ลำดับ |

### 1.3 `legal.document.draft` — เอกสารที่สร้างแล้ว

| Field | Type | คำอธิบาย |
|-------|------|----------|
| `name` | Char | ชื่อเอกสาร |
| `template_id` | Many2one | Template ที่ใช้สร้าง |
| `lead_id` | Many2one | เคสที่เกี่ยวข้อง (crm.lead) |
| `lawyer_partner_id` | Many2one | ทนายผู้สร้าง |
| `client_partner_id` | Many2one | ลูกค้า |
| `state` | Selection | สถานะเอกสาร (ดู Lifecycle ด้านล่าง) |
| `field_values` | Text | JSON ค่าที่กรอก |
| `draft_content` | Text | เนื้อหา markdown |
| `docx_file` | Binary | ไฟล์ DOCX ที่สร้างแล้ว |

---

## 2. Document Lifecycle (สถานะเอกสาร)

```
generating ──▶ draft ──▶ sent_to_client ──▶ final ──▶ signed
                 │              │
                 │              ▼
                 │         revision ──▶ draft (loop)
                 │
                 ▼
             cancelled ──▶ expired ──▶ [ลบ]
```

| สถานะ | คำอธิบาย | ระยะเวลาก่อนหมดอายุ |
|--------|----------|---------------------|
| `generating` | กำลังสร้าง (background thread) | — |
| `draft` | ร่าง พร้อมแก้ไข | 30 วัน |
| `sent_to_client` | ส่งให้ลูกค้าแล้ว | — |
| `revision` | ลูกค้าขอแก้ไข | — |
| `final` | สมบูรณ์ พร้อมเซ็น | — |
| `signed` | เซ็นแล้ว | 90 วัน |
| `cancelled` | ยกเลิก | 7 วัน |
| `expired` | หมดอายุ (auto) | ลบหลัง 180 วัน |

**State Transitions:**
- `action_send_to_client()` : draft/revision → sent_to_client
- `action_request_revision()` : sent_to_client → revision (พร้อม notes)
- `action_finalize()` : draft/sent_to_client → final
- `action_sign()` : final → signed
- `action_cancel()` : ทุกสถานะ (ยกเว้น signed/expired) → cancelled
- `action_back_to_draft()` : revision/cancelled → draft

---

## 3. Document Generation Flow (ขั้นตอนสร้างเอกสาร)

```
User กรอกฟอร์ม
       │
       ▼
POST /liff/document/create/submit
       │
       ▼
สร้าง Draft (state='generating')
       │
       ▼
Background Thread: _background_generate()
       │
       ├──▶ มี .docx template?
       │       │
       │       ▼ YES
       │    _fill_docx_template()
       │    (docxtpl render {{key}} → values)
       │    Return DOCX bytes ✅
       │
       ├──▶ มี adkcode service?
       │       │
       │       ▼ YES
       │    POST {adkcode_url}/draft-document
       │    Return markdown ✅
       │
       └──▶ Fallback
               │
               ▼
            อ่าน .md template
            replace {{key}} → values
            Return markdown ✅
       │
       ▼
อัพเดต Draft: state='draft'
บันทึก docx_file หรือ draft_content
       │
       ▼
ส่ง LINE Push Notification 🔔
```

### 3.1 DOCX Template Fill (หลัก)

ใช้ **docxtpl** (Jinja2-based) แทน python-docx ดิบ:

```python
from docxtpl import DocxTemplate

doc = DocxTemplate(template_path)
doc.render(field_values)   # {{key}} → values, รองรับ split runs
doc.save(buf)
```

**ข้อดี:**
- แก้ปัญหา Word แบ่ง `{{placeholder}}` เป็นหลาย runs
- Style/format คงอยู่ 100%
- รองรับ `{% for %}`, `{% if %}` ในอนาคต

### 3.2 Auto-Enrich: ตัวเลข → ตัวหนังสือไทย

เมื่อ user กรอก field ที่เป็นตัวเลข ระบบสร้างตัวแปรเพิ่มอัตโนมัติ:

| User กรอก | ตัวแปรที่ได้ | ค่าตัวอย่าง |
|-----------|-------------|------------|
| `ค่าเช่า` = 15000 | `{{ค่าเช่า}}` | 15000 |
| | `{{ค่าเช่า_text}}` | หนึ่งหมื่นห้าพัน |
| | `{{ค่าเช่า_baht}}` | หนึ่งหมื่นห้าพันบาทถ้วน |

**Jinja2 Filters** (ใช้ใน template ได้ด้วย):
```
{{ค่าเช่า|baht_text}}      → หนึ่งหมื่นห้าพันบาทถ้วน
{{ค่าเช่า|number_text}}    → หนึ่งหมื่นห้าพัน
```

Utility: `utils/thai_number.py` — `number_to_thai_text()`, `baht_text()`

### 3.3 Auto-Enrich: ที่อยู่ (Address Auto-fill)

เมื่อ field_type = `address` user กรอกแค่ **เลขที่บ้าน + เลือกตำบล** (autocomplete) ระบบ auto-fill ที่เหลือ:

```
User กรอก:
  เลขที่: 123/45 หมู่ 6
  ค้นหาตำบล: "บางพ" → เลือก "บางพลีใหญ่"
```

| ตัวแปรที่ได้ | ค่า |
|-------------|-----|
| `{{ที่อยู่}}` | 123/45 หมู่ 6 ตำบลบางพลีใหญ่ อำเภอบางพลี จังหวัดสมุทรปราการ 10540 |
| `{{ที่อยู่_เลขที่}}` | 123/45 หมู่ 6 |
| `{{ที่อยู่_ตำบล}}` | บางพลีใหญ่ |
| `{{ที่อยู่_อำเภอ}}` | บางพลี |
| `{{ที่อยู่_จังหวัด}}` | สมุทรปราการ |
| `{{ที่อยู่_รหัสไปรษณีย์}}` | 10540 |

**ข้อมูลอ้างอิง:** `data/thai_address.json` — 7,498 ตำบลทั่วประเทศ
**API:** `POST /liff/address/search` — `{"q": "บางพลี", "limit": 15}` → autocomplete results

### 3.4 Markdown Template Fill (Fallback)

```python
content = open(f'/mnt/templates/{code}.md').read()
for key, val in field_values.items():
    content = content.replace('{{' + key + '}}', str(val))
```

---

## 4. AI Template Analysis (วิเคราะห์ Template อัตโนมัติ)

```
Admin อัพโหลด .docx ต้นแบบ
       │
       ▼
กด "AI วิเคราะห์"
       │
       ▼
อ่าน DOCX → แปลง .doc ถ้าจำเป็น (LibreOffice)
       │
       ▼
ดึงข้อความทุกย่อหน้า: [0] text, [1] text ...
       │
       ▼
ส่ง Prompt ไป Gemini 2.5-flash
  - หาจุด (....),  เส้น (____), ช่องว่าง
  - แปลงเป็น {{placeholder}} ภาษาไทย
  - สร้าง JSON: reconstructed_paragraphs[] + required_fields[]
       │
       ▼
Parse JSON (retry 3 ครั้ง + repair JSON)
       │
       ▼
สร้าง DOCX ใหม่ (แทนที่ย่อหน้าด้วย placeholder)
       │
       ▼
บันทึกไฟล์ → /mnt/templates/docx-masters/{code}.docx
       │
       ▼
Sync required_fields → field_ids (Admin แก้ได้ทันที)
```

**Config:**
| Parameter | ค่า |
|-----------|-----|
| `legal_liff.google_api_key` | Google API Key สำหรับ Gemini |
| `legal_liff.gemini_model` | ชื่อ model (default: gemini-2.5-flash) |

---

## 5. API Endpoints

### 5.1 User-Facing Pages (HTML)

| Route | Method | คำอธิบาย |
|-------|--------|----------|
| `/liff/intake` | GET | ฟอร์มรับเคสใหม่ |
| `/liff/intake/submit` | POST | Submit ฟอร์มรับเคส |
| `/liff/status/<id>` | GET | ดูสถานะเคส + timeline |
| `/liff/cases` | GET | Dashboard ทนาย |
| `/liff/document/create` | GET | หน้าสร้างเอกสาร |
| `/liff/document/draft/<id>` | GET | ดู/แก้ไขเอกสาร |
| `/liff/documents` | GET | รายการเอกสารของ user |

### 5.2 JSON API

| Route | Method | Input | Output |
|-------|--------|-------|--------|
| `/liff/document/create/data` | POST | `{line_user_id}` | `{templates[], cases[]}` |
| `/liff/document/create/submit` | POST | `{template_id, field_values, lead_id}` | `{draft_id, state}` |
| `/liff/document/draft/<id>/status` | POST | `{line_user_id}` | `{state, has_docx}` |
| `/liff/document/draft/<id>/action` | POST | `{action, notes}` | `{success, new_state}` |
| `/liff/documents/data` | POST | `{line_user_id}` | `{documents[]}` |
| `/liff/address/search` | POST | `{q, limit}` | `{results[]}` — autocomplete ที่อยู่ไทย |
| `/api/documents` | GET | `?line_user_id=` | `{documents[]}` |

### 5.3 Download

| Route | Method | Params | Output |
|-------|--------|--------|--------|
| `/liff/document/draft/<id>/download` | GET | `?fmt=pdf\|docx` | Binary file |

**การแปลงไฟล์:**
```
DOCX-based:
  fmt=docx → return ไฟล์ตรงๆ
  fmt=pdf  → DOCX → HTML → wkhtmltopdf → PDF

Markdown-based:
  fmt=pdf  → markdown → HTML → wkhtmltopdf → PDF
  fmt=docx → markdown → python-docx → DOCX
```

---

## 6. LINE Integration

### 6.1 LIFF SDK (Frontend)

- ใช้ LIFF SDK v2 ดึงข้อมูล LINE user
- Config: `line_integration.liff_id`

### 6.2 Push Notifications

| เหตุการณ์ | ข้อความ | รูปแบบ |
|-----------|---------|--------|
| รับเคสใหม่ | Lead ID + ประเภทเคส | Text |
| เอกสารพร้อม | ชื่อ template + ปุ่มดูเอกสาร | Flex Message (สีเขียว) |
| ใกล้หมดอายุ | ชื่อเอกสาร + countdown + link ดาวน์โหลด | Text |

**API:** `POST api.line.me/v2/bot/message/push`
**Config:** `line_integration.channel_access_token`

---

## 7. Admin Interface (Odoo Backend)

### Menu: Legal LIFF → Document Templates

**List View:**
- ลาก sort ลำดับ
- แสดง: ชื่อ, Code, หมวด, สถานะ AI, จำนวน Fields

**Form View — 3 Tabs:**

| Tab | เนื้อหา |
|-----|---------|
| **อัพโหลด & AI วิเคราะห์** | อัพโหลด .docx + ดาวน์โหลด template ที่ AI สร้าง + Log |
| **Template Fields** | ตาราง inline editable: ลาก sort, แก้ชื่อ/label/type, tick จำเป็น/ไม่จำเป็น |
| **JSON (Raw)** | ดู JSON ที่ auto-sync (readonly, debug) |

**Sync 2 ทาง:**
- Admin แก้ตาราง field_ids → JSON อัพเดตอัตโนมัติ
- AI วิเคราะห์เขียน JSON → field_ids สร้างอัตโนมัติ

---

## 8. Auto-Cleanup (Cron Job)

รันอัตโนมัติทุกวัน:

| สถานะ | หมดอายุหลัง | ลบถาวรหลัง | แจ้งเตือนก่อน |
|--------|------------|-----------|-------------|
| draft | 30 วัน | 180 วัน | 7 วัน |
| cancelled | 7 วัน | 180 วัน | 7 วัน |
| signed | 90 วัน | 180 วัน | 7 วัน |

**ขั้นตอน:**
1. หาเอกสารที่เกินระยะเวลา → set state='expired', ล้าง content
2. หา expired > 180 วัน → ลบถาวร (hard delete)
3. ส่ง LINE แจ้งเตือนก่อนหมดอายุ 7 วัน

---

## 9. Template ที่มีในระบบ (Seed Data)

### สัญญา (Contract) — 5 templates
| Template | Code | Fields |
|----------|------|--------|
| สัญญาเช่าทรัพย์สิน | contract/rental-agreement | ผู้ให้เช่า, ผู้เช่า, ทรัพย์สิน, ค่าเช่า, มัดจำ, วันที่ |
| สัญญาซื้อขาย | contract/sale-agreement | ผู้ขาย, ผู้ซื้อ, รายการ, ราคา, การชำระ |
| สัญญากู้ยืมเงิน | contract/loan-agreement | ผู้ให้กู้, ผู้กู้, จำนวนเงิน, ดอกเบี้ย, งวด |
| สัญญาจ้างงาน | contract/employment-contract | นายจ้าง, ลูกจ้าง, ตำแหน่ง, เงินเดือน |
| สัญญาค้ำประกัน | contract/guarantee-agreement | ผู้ค้ำ, ลูกหนี้, เจ้าหนี้, จำนวน |

### หนังสือ (Letter) — 4 templates
| Template | Code | Fields |
|----------|------|--------|
| หนังสือทวงถาม | letter/demand-letter | ผู้ส่ง, ผู้รับ, จำนวนเงิน, กำหนด |
| หนังสือบอกเลิกสัญญา | letter/termination-notice | ผู้ส่ง, ผู้รับ, สัญญาอ้างอิง, เหตุผล |
| หนังสือมอบอำนาจ | letter/power-of-attorney | ผู้มอบ, ผู้รับมอบ, ขอบเขต |
| หนังสือยินยอม | letter/consent-letter | ผู้ยินยอม, รายละเอียด |

### คำร้อง/คำฟ้อง (Petition) — 2 templates
| Template | Code | Fields |
|----------|------|--------|
| คำฟ้องแพ่ง | petition/civil-complaint | ศาล, โจทก์, จำเลย, ข้อเท็จจริง |
| คำให้การ | petition/defense-statement | ศาล, เลขคดี, จำเลย, ข้อต่อสู้ |

### พินัยกรรม (Will) — 1 template
| Template | Code | Fields |
|----------|------|--------|
| พินัยกรรม | will/testament | ผู้ทำ, ผู้รับ, ทรัพย์สิน, ผู้จัดการ |

---

## 10. File Structure

```
legal_liff/
├── __manifest__.py                          # Module metadata + post_init_hook
├── __init__.py                              # Imports + migration hook
├── models/
│   ├── document_template.py                 # Template model + AI analysis
│   ├── document_template_field.py           # Field definitions (inline editable)
│   └── document_draft.py                    # Draft lifecycle + auto-cleanup
├── controllers/
│   └── liff_controller.py                   # All routes + document generation + address search
├── utils/
│   ├── __init__.py
│   └── thai_number.py                       # ตัวเลข → ตัวหนังสือไทย / บาทไทย
├── views/
│   ├── document_template_views.xml          # Admin UI (list + form)
│   └── liff_templates.xml                   # Frontend HTML pages
├── data/
│   ├── document_template_data.xml           # 12 seed templates
│   ├── document_cron.xml                    # Daily cleanup cron
│   └── thai_address.json                    # ฐานข้อมูลที่อยู่ไทย 7,498 ตำบล
├── security/
│   └── ir.model.access.csv                  # Access rights
└── static/src/js/
    ├── liff_common.js                       # Shared LIFF utilities
    ├── liff_document_create.js              # Document creation + address autocomplete
    └── liff_document_draft.js               # Draft view actions
```

---

## 11. Dependencies & Configuration

### Docker (docker-compose.yml)
```yaml
pip install: python-docx docxtpl markdown
apt install: libreoffice-writer
binary: wkhtmltopdf (pre-installed in image)
```

### System Parameters (Odoo Settings)
| Key | คำอธิบาย |
|-----|----------|
| `line_integration.liff_id` | LINE LIFF App ID |
| `line_integration.channel_access_token` | LINE Bot Token |
| `line_integration.adkcode_url` | URL ของ adkcode service (optional) |
| `legal_liff.google_api_key` | Google API Key สำหรับ Gemini |
| `legal_liff.gemini_model` | Gemini model (default: gemini-2.5-flash) |
| `web.base.url` | Base URL ของระบบ |

### Volume Mounts
```
/mnt/extra-addons  → Odoo addons (legal_liff)
/mnt/templates     → Template files (.docx, .md)
```

---

## 12. Frontend Polling (UX)

หลังกด "สร้างเอกสาร":

```javascript
// Poll ทุก 2 วินาที สูงสุด 60 ครั้ง (2 นาที)
setInterval(() => {
    POST /liff/document/draft/{id}/status
    if (state !== 'generating') → แสดงผลสำเร็จ
}, 2000)
```

แสดงปุ่มดาวน์โหลด:
- 📄 ดาวน์โหลด PDF
- 📝 ดาวน์โหลด DOCX
- ดูรายละเอียด → `/liff/document/draft/{id}`
