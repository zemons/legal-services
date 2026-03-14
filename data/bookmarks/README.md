# Bookmarks — แหล่งข้อมูลกฎหมายและทรัพยากรที่เกี่ยวข้อง

ระบบ bookmark แหล่งข้อมูลสำหรับโครงการ Legal Services
ใช้อ้างอิง, ดาวน์โหลดเพิ่ม, และให้ AI agent ค้นหาข้อมูล

## ไฟล์

| ไฟล์ | เนื้อหา | จำนวน |
|---|---|---|
| `court_forms.yaml` | แบบพิมพ์ศาล (ดาวน์โหลด .doc/.docx) | 15 แหล่ง |
| `court_info.yaml` | ข้อมูลศาล (คำพิพากษา, บทความ, ห้องสมุด) | 10 แหล่ง |
| `legal_db.yaml` | ฐานข้อมูลกฎหมาย (ราชกิจจาฯ, กฤษฎีกา, ฎีกา) | 4 แหล่ง |
| `gov_services.yaml` | บริการรัฐ (e-Filing, e-Court, CIOS) | 3 แหล่ง |
| `odoo_modules.yaml` | Odoo modules จาก apps.odoo.com | 14 modules |
| `references.yaml` | เว็บอ้างอิงอื่น (FormThai, FormV97 ฯลฯ) | 6 แหล่ง |

## Status Legend

| Status | ความหมาย |
|---|---|
| `downloaded` | ดาวน์โหลดแล้ว อยู่ใน `data/templates/` |
| `downloaded_partial` | ดาวน์โหลดบางส่วน |
| `pending` | ยังไม่ได้ดาวน์โหลด (timeout/รอ) |
| `blocked` | ถูก block (Incapsula/security) |
| `bookmarked` | บันทึก URL ไว้อ้างอิง |

## Download Summary

รวม 134 ไฟล์ .doc (12MB):
- coj.go.th ศาลยุติธรรม: 67 files (11 subdirs)
- siamlegalinter ศาลแรงงาน: 17 files
- siamlegalinter ศาลล้มละลาย: 21 files
- siamlegalinter ศาลปกครอง: 9 files
- siamlegalinter ศาลผู้บริโภค: 21 files
