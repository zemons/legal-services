from odoo import models, fields, api


class LegalDocumentVersion(models.Model):
    _name = 'legal.document.version'
    _description = 'Document Version History'
    _order = 'version_number desc'

    draft_id = fields.Many2one(
        'legal.document.draft', string='Document',
        required=True, ondelete='cascade', index=True,
    )
    version_number = fields.Integer('Version', required=True)
    state_at_save = fields.Char('State at Save')
    content = fields.Text('Content Snapshot')
    docx_file = fields.Binary('DOCX Snapshot', attachment=True)
    docx_filename = fields.Char('DOCX Filename')
    field_values = fields.Text('Field Values (JSON)')
    change_summary = fields.Char('Change Summary',
                                 help='e.g. "ทนายแก้ข้อ 3", "ลูกค้าขอเพิ่มข้อ 5"')
    changed_by = fields.Many2one('res.partner', string='Changed By')
    change_type = fields.Selection([
        ('auto_generated', 'AI สร้างอัตโนมัติ'),
        ('lawyer_edit', 'ทนายแก้ไข'),
        ('client_revision', 'ลูกค้าขอแก้ไข'),
        ('finalized', 'ยืนยันฉบับสมบูรณ์'),
        ('signed', 'ลงนาม'),
    ], string='Change Type')
    create_date = fields.Datetime('Created', readonly=True)
