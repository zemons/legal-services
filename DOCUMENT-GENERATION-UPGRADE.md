# Document Generation System — Upgrade Summary

วันที่: 2026-03-12

## สิ่งที่ปรับปรุง (6 รายการ)

---

### 1. Conditional Logic ใน Templates

**ก่อน:** template ตายตัว แสดงทุก clause เหมือนกัน
**หลัง:** ใช้ Jinja2 `{% if %}` เลือกแสดง clause ตามเงื่อนไข

**ตัวอย่าง:** สัญญาเช่า
- ถ้า `มีเงินประกัน = true` → แสดงข้อเงินประกัน
- ถ้า `เช่าเกิน3ปี = true` → แสดงหมายเหตุจดทะเบียน (ป.พ.พ. ม.538)
- ถ้า `อนุญาตเช่าช่วง = true` → เปลี่ยนข้อห้ามเป็นเงื่อนไข
- ข้อสัญญาจะเลขที่อัตโนมัติถูกต้อง ไม่ข้ามเลข

**ไฟล์ที่แก้:** `data/templates/` — ทั้ง 12 ไฟล์ .md

---

### 2. Repeating Sections

**ก่อน:** `{{ชื่อผู้เช่า}}` รองรับแค่ 1 คน
**หลัง:** ใช้ `{% for person in ผู้เช่าร่วม %}` รองรับหลายคน

**ตัวอย่างที่เพิ่ม:**
- สัญญาเช่า: ผู้เช่าร่วมหลายคน, ผู้ค้ำประกันหลายคน
- สัญญาซื้อขาย: รายการทรัพย์สินหลายรายการ (ตาราง), งวดชำระเงิน
- สัญญากู้ยืม: ผู้ค้ำประกันหลายคน
- พินัยกรรม: ผู้รับพินัยกรรมหลายคน, รายการทรัพย์สิน (ตาราง)
- คำฟ้อง: โจทก์ร่วม, จำเลยหลายคน, คำขอท้ายฟ้อง, พยานเอกสาร

**ไฟล์ที่แก้:** `data/templates/` — ทั้ง 12 ไฟล์ .md + controller Jinja2 renderer

---

### 3. Markdown Jinja2 Renderer (Code)

**ก่อน:** `content.replace('{{key}}', value)` — simple string replace
**หลัง:** `_render_md_jinja2()` — full Jinja2 engine

**Features:**
- `{% if %}` / `{% else %}` / `{% endif %}`
- `{% for item in list %}` / `{% endfor %}`
- `{% set clause_no = namespace(n=1) %}` สำหรับเลขข้ออัตโนมัติ
- `SilentUndefined` — ถ้า field ไม่มีค่าจะไม่ error แต่แสดงว่าง
- Auto-parse JSON arrays สำหรับ repeating fields
- Auto-enrich `_text` (ตัวหนังสือไทย), `_baht` (เงินบาท)
- Fallback: ถ้า Jinja2 render ล้มเหลว ใช้ simple replace แทน

**ไฟล์ที่แก้:** `controllers/liff_controller.py` — method `_render_md_jinja2()`

---

### 4. Clause Library

**Models ใหม่:**
- `legal.clause.category` — หมวดหมู่ข้อสัญญา (10 หมวด)
- `legal.clause` — คลังข้อสัญญาที่ทนายอนุมัติแล้ว

**Features:**
- Risk Level: Conservative / Standard / Aggressive
- Approval Workflow: Draft → Review → Approved → Archived
- Version Control ของ clause (สร้าง version ใหม่ได้)
- Usage Counter (นับจำนวนครั้งที่ใช้)
- Tags & Search
- เชื่อม Template ที่ compatible ได้

**Seed Data (9 clauses):**
| Category | Clauses |
|----------|---------|
| หลักประกัน | มาตรฐาน, เข้มงวด |
| เบี้ยปรับ | มาตรฐาน |
| เลิกสัญญา | มาตรฐาน |
| เหตุสุดวิสัย | มาตรฐาน |
| ข้อพิพาท | ศาลไทย, อนุญาโตตุลาการ |
| ความลับ | มาตรฐาน |
| กฎหมายที่ใช้บังคับ | ไทย |

**ไฟล์ใหม่:**
- `models/legal_clause.py`
- `views/legal_clause_views.xml`
- `data/clause_data.xml`

---

### 5. Guided Interview (Multi-step Form)

**ก่อน:** ฟอร์มเดียว แสดงทุก field พร้อมกัน
**หลัง:** แบ่งเป็น steps ตามขั้นตอน

**Fields ใหม่ใน `legal.document.template.field`:**
- `step` — ลำดับขั้นตอน (1, 2, 3...)
- `step_label` — ชื่อขั้นตอน เช่น "ข้อมูลคู่สัญญา"
- `field_type` เพิ่ม: `boolean` (ใช่/ไม่ใช่), `repeating` (กลุ่มข้อมูลซ้ำ)
- `default_value` — ค่าเริ่มต้น
- `help_text` — คำอธิบายใต้ field
- `placeholder` — ข้อความตัวอย่าง
- `repeating_fields_json` — sub-fields สำหรับ repeating group
- `repeating_min`, `repeating_max` — จำกัดจำนวน rows

**API Response ใหม่:**
`/liff/document/create/data` ตอนนี้ return `steps` array:
```json
{
  "steps": [
    {"step": 1, "label": "ข้อมูลคู่สัญญา", "fields": [...]},
    {"step": 2, "label": "เงื่อนไขสัญญา", "fields": [...]}
  ]
}
```

**ไฟล์ที่แก้:**
- `models/document_template_field.py`
- `controllers/liff_controller.py` — method `_get_template_steps()`

---

### 6. Document Version Control

**Model ใหม่:** `legal.document.version`
- เก็บ snapshot ของเอกสารทุก version
- บันทึก: content, DOCX file, field values, ใครแก้, แก้อะไร

**Auto-save version เมื่อ:**
- AI สร้างเอกสารเสร็จ (v1 — auto_generated)
- ทนายส่งให้ลูกค้า (lawyer_edit)
- ลูกค้าขอแก้ไข (client_revision)
- ยืนยันฉบับสมบูรณ์ (finalized)
- ลงนาม (signed)

**Features:**
- ดู history ทุก version ผ่าน API `/liff/document/draft/<id>/versions`
- ย้อนกลับไป version เก่าได้ (`action_restore_version`)
- บันทึก version ปัจจุบันก่อนย้อนกลับเสมอ (ไม่หาย)

**ไฟล์ใหม่:**
- `models/document_version.py`

---

### 7. AI-Suggested Clauses

**API Endpoints ใหม่:**

| Endpoint | ใช้ทำอะไร |
|----------|----------|
| `POST /liff/clause/suggest` | ค้นหา clause จาก library ตาม document_type, category, risk_level |
| `POST /liff/clause/use` | บันทึกว่าใช้ clause นี้ (เพิ่ม counter) |
| `POST /liff/clause/ai-suggest` | Hybrid: ค้นจาก library + AI สร้างข้อสัญญาใหม่ |
| `POST /liff/document/draft/<id>/versions` | ดูประวัติ version ของเอกสาร |

**AI Suggestion Flow:**
1. ค้นหาจาก clause library ก่อน (กรองตาม document_type, topic, risk_level)
2. Return ได้สูงสุด 3 clauses จาก library (แยกตาม risk level)
3. ส่ง prompt ไป adkcode → Gemini สร้าง clause ใหม่ตามบริบท
4. Return ทั้ง library clauses + AI suggestion ให้ทนายเลือก

---

## สรุปไฟล์ที่เปลี่ยน

### ไฟล์ใหม่ (4 ไฟล์)
- `models/legal_clause.py` — Clause Library model
- `models/document_version.py` — Version Control model
- `views/legal_clause_views.xml` — Clause Library UI
- `data/clause_data.xml` — Seed data (10 categories + 9 clauses)

### ไฟล์ที่แก้ไข
- `models/__init__.py` — เพิ่ม import
- `models/document_template_field.py` — เพิ่ม step, boolean, repeating fields
- `models/document_draft.py` — เพิ่ม version control + auto-save
- `controllers/liff_controller.py` — Jinja2 renderer, step API, clause API, version API
- `security/ir.model.access.csv` — เพิ่ม ACL สำหรับ models ใหม่
- `__manifest__.py` — เพิ่ม data files

### Templates ที่ปรับปรุง (12 ไฟล์)
- `data/templates/contract/rental-agreement.md`
- `data/templates/contract/sale-agreement.md`
- `data/templates/contract/loan-agreement.md`
- `data/templates/contract/employment-contract.md`
- `data/templates/contract/guarantee-agreement.md`
- `data/templates/letter/demand-letter.md`
- `data/templates/letter/termination-notice.md`
- `data/templates/letter/power-of-attorney.md`
- `data/templates/letter/consent-letter.md`
- `data/templates/petition/civil-complaint.md`
- `data/templates/petition/defense-statement.md`
- `data/templates/will/testament.md`
