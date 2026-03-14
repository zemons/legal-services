from odoo import models, fields


class LegalDocumentTemplateField(models.Model):
    _name = 'legal.document.template.field'
    _description = 'Template Field Definition'
    _order = 'step, sequence, id'

    template_id = fields.Many2one(
        'legal.document.template', string='Template',
        required=True, ondelete='cascade', index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char('Field Name', required=True,
                       help='ชื่อ placeholder เช่น grantor_name → {{grantor_name}}')
    label = fields.Char('Label', required=True,
                        help='ชื่อที่แสดงในฟอร์ม เช่น ชื่อผู้มอบอำนาจ')
    field_type = fields.Selection([
        ('text', 'ข้อความ'),
        ('number', 'ตัวเลข'),
        ('date', 'วันที่'),
        ('textarea', 'ข้อความยาว'),
        ('select', 'ตัวเลือก'),
        ('boolean', 'ใช่/ไม่ใช่'),
        ('address', 'ที่อยู่ (auto-fill ตำบล/อำเภอ/จังหวัด)'),
        ('repeating', 'กลุ่มข้อมูลซ้ำ (เช่น รายชื่อหลายคน)'),
    ], string='Type', default='text', required=True)
    required = fields.Boolean('จำเป็น', default=True)
    options = fields.Char('Options',
                          help='ตัวเลือก (สำหรับ type=select) คั่นด้วยเครื่องหมาย , เช่น ชาย,หญิง')
    default_value = fields.Char('Default Value',
                                help='ค่าเริ่มต้น เช่น true, 120, วันนี้')
    show_when = fields.Char(
        'Show When',
        help='JSON เงื่อนไขแสดงฟิลด์ เช่น {"มีผู้ค้ำประกัน": true} — แสดงเฉพาะเมื่อเงื่อนไขตรง',
    )

    # ── Guided Interview (multi-step) ──
    step = fields.Integer(
        'Step', default=1,
        help='ลำดับขั้นตอนในฟอร์ม (1=ข้อมูลหลัก, 2=รายละเอียด, 3=เงื่อนไขเพิ่มเติม, ...)',
    )
    step_label = fields.Char(
        'Step Label',
        help='ชื่อขั้นตอน เช่น "ข้อมูลคู่สัญญา", "เงื่อนไขสัญญา"',
    )
    help_text = fields.Char(
        'Help Text',
        help='คำอธิบายเพิ่มเติมแสดงใต้ฟิลด์',
    )
    placeholder = fields.Char(
        'Placeholder',
        help='ข้อความตัวอย่างใน input เช่น "นายสมชาย ใจดี"',
    )

    # ── Repeating group definition ──
    repeating_fields_json = fields.Text(
        'Repeating Fields (JSON)',
        help='สำหรับ type=repeating: กำหนด sub-fields เป็น JSON array '
             'เช่น [{"name":"ชื่อ","type":"text"},{"name":"ที่อยู่","type":"address"}]',
    )
    repeating_min = fields.Integer('Min Rows', default=0)
    repeating_max = fields.Integer('Max Rows', default=10)
