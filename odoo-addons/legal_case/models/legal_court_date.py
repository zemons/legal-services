from odoo import models, fields


class LegalCourtDate(models.Model):
    _name = 'legal.court.date'
    _description = 'Court Date'
    _order = 'date_time desc'

    lead_id = fields.Many2one('crm.lead', string='Case', required=True, ondelete='cascade')
    date_time = fields.Datetime(string='Date & Time', required=True)
    court_id = fields.Many2one('legal.court', string='Court')
    purpose = fields.Selection([
        ('hearing', 'นัดพิจารณา'),
        ('witness', 'นัดสืบพยาน'),
        ('mediation', 'นัดไกล่เกลี่ย'),
        ('judgment', 'นัดฟังคำพิพากษา'),
        ('other', 'อื่นๆ'),
    ], string='Purpose', default='hearing')
    room = fields.Char(string='Courtroom')
    notes = fields.Text(string='Notes')
    calendar_event_id = fields.Many2one('calendar.event', string='Calendar Event', readonly=True)
