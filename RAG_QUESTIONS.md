# RAG Questions & Decisions

ประเด็นที่ต้องตัดสินใจก่อนพัฒนา RAG — บันทึกคำตอบไว้เป็น reference

---

## 1. Embedding Model

**คำถาม:** ใช้ Gemini หรือ OpenAI?

**คำตอบ:** ✅ **Gemini** (gemini-embedding-001, 768 dimensions)

**เหตุผล:**
- adkcode ใช้ Gemini อยู่แล้ว ไม่ต้องเพิ่ม API key
- รองรับภาษาไทยได้ดี
- ราคาถูกกว่า OpenAI embedding
- task_type แยกได้ (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY)

---

## 2. Vector Storage

**คำถาม:** JSON file หรือ Qdrant?

**คำตอบ:** ✅ **JSON file** (เริ่มต้น) → อัปเกรดเป็น Qdrant เมื่อข้อมูลเกิน 10,000 chunks

**เหตุผล:**
- ปริมาณเอกสารช่วงแรกไม่เกินหลักพัน — JSON เพียงพอ
- ไม่ต้องเพิ่ม service ใน Docker Compose
- cosine similarity ใน Python เร็วพอสำหรับ < 10k vectors
- เก็บแยกไฟล์ต่อ collection (เช่น `.index_dika.json`, `.index_statute.json`)

**เงื่อนไขอัปเกรด:**
- เอกสารเกิน 10,000 chunks
- search latency > 2 วินาที
- ต้องการ metadata filtering แบบซับซ้อน

---

## 3. Document Metadata Schema

**คำถาม:** metadata ของแต่ละประเภทเอกสารมีอะไรบ้าง?

**คำตอบ:** ✅ ใช้ YAML frontmatter ในไฟล์ Markdown

### ฎีกา (dika)
```yaml
type: dika
case_no: "1234/2566"
court: ศาลฎีกา
year: 2566
category: แพ่ง
topic: [สัญญาเช่า, ผิดนัด]
summary: สรุป 1-2 ประโยค
result: โจทก์ชนะ | จำเลยชนะ | เจรจา
legal_basis: [ป.พ.พ. ม.560, ป.พ.พ. ม.387]
key_facts: [ข้อเท็จจริงสำคัญที่ศาลใช้ตัดสิน]
ruling_principle: หลักกฎหมายที่ศาลวางไว้
```

### กฎหมาย (statute)
```yaml
type: statute
code: ป.พ.พ.
book: บรรพ 3 เอกเทศสัญญา
title: ลักษณะ 4 เช่าทรัพย์
sections: [537, 538, 560]
category: แพ่งและพาณิชย์
topic: [เช่าทรัพย์, สัญญาเช่า]
effective_date: "2468-01-01"
```

### กฎกระทรวง / ระเบียบ (regulation)
```yaml
type: regulation
name: กฎกระทรวง ฉบับที่...
ministry: กระทรวง...
gazette_no: เล่ม... ตอนที่...
topic: [...]
effective_date: "2566-01-01"
```

### Strategy Pattern
```yaml
type: strategy_pattern
case_type: แพ่ง-สัญญาเช่า
facts_pattern: [ข้อเท็จจริงที่คล้ายกัน]
winning_angle: มุมที่ชนะ
losing_angles: [มุมที่ไม่ได้ผล]
result: ชนะ | แพ้ | เจรจา
related_dika: ["1234/2566"]
lawyer_notes: "บันทึกทนาย"
```

---

## 4. Template เอกสาร

**คำถาม:** หา template คำร้อง / สัญญา มาเก็บใน RAG ที่ไหน?

**คำตอบ:** ✅ เขียนเอง + ให้ทนายตรวจ

**แหล่ง template:**
- ทนายเจ้าของสำนักงานเขียน/รวบรวมจากงานจริง
- ปรับจาก template ที่ใช้งานอยู่แล้ว
- เก็บใน `data/templates/` แยกตามประเภท (contract, petition, letter, will)

**Format:**
```markdown
---
type: template
name: สัญญาเช่าทรัพย์สิน
category: contract
required_fields: [ชื่อผู้ให้เช่า, ชื่อผู้เช่า, ค่าเช่า, วันเริ่ม, วันสิ้นสุด]
---

เนื้อหา template พร้อม {{field}} placeholder
```

**สำคัญ:** template ทุกชิ้นต้องผ่านทนายตรวจก่อนใช้งาน

---

## 5. Chunking Strategy

**คำถาม:** แบ่ง chunk อย่างไรสำหรับเอกสารกฎหมาย?

**คำตอบ:** ✅ แบ่งตามโครงสร้างเอกสาร ไม่ใช่ตามจำนวนบรรทัด

| ประเภท | วิธี chunk |
|--------|-----------|
| ฎีกา | 1 ฎีกา = 1 chunk (ส่วนมากไม่เกิน 2-3 หน้า) |
| กฎหมาย | แบ่งตามมาตรา หรือ กลุ่มมาตราที่เกี่ยวข้อง |
| ระเบียบ | แบ่งตามข้อ/หมวด |
| Strategy Pattern | 1 pattern = 1 chunk |
| Template | 1 template = 1 chunk (ไม่แบ่ง) |

**หลักการ:** เก็บ metadata (frontmatter) ไว้กับทุก chunk — เมื่อ search เจอ chunk ต้องรู้ว่ามาจากเอกสารอะไร

---

## 6. Collection Architecture

**คำถาม:** แยก collection อย่างไร?

**คำตอบ:** ✅ แยก index file ต่อ collection

```
data/
├── .index_dika.json
├── .index_statute.json
├── .index_regulation.json
├── .index_strategy_patterns.json
├── .index_templates.json
└── knowledge/
    ├── dika/
    ├── statute/
    ├── regulation/
    ├── article/
    └── strategy_patterns/
```

**เหตุผล:**
- search ได้เฉพาะ collection ที่ต้องการ (เร็วกว่า search ทั้งหมด)
- case_strategist ค้น dika + strategy_patterns
- legal_advisor ค้น dika + statute + regulation
- doc_drafter ค้น templates
- rebuild index ทีละ collection ได้ (ไม่ต้อง rebuild ทั้งหมด)
