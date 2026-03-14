from odoo import models, fields


class LegalCaseEvent(models.Model):
    _name = 'legal.case.event'
    _description = 'Case Event Timeline'
    _order = 'date desc, id desc'

    lead_id = fields.Many2one('crm.lead', string='Case', required=True, ondelete='cascade')
    event_type = fields.Selection([
        ('status_change', 'เปลี่ยนสถานะ'),
        ('court_date', 'นัดศาล'),
        ('document', 'เอกสาร'),
        ('note', 'หมายเหตุ'),
    ], string='Event Type', required=True, default='note')
    title = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    icon = fields.Char(string='Icon', compute='_compute_icon')

    def _compute_icon(self):
        icon_map = {
            'status_change': '&#9679;',
            'court_date': '&#9878;',
            'document': '&#128196;',
            'note': '&#128221;',
        }
        for event in self:
            event.icon = icon_map.get(event.event_type, '&#9679;')
