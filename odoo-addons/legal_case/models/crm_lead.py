from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    case_type = fields.Selection([
        ('civil', 'แพ่ง'),
        ('criminal', 'อาญา'),
        ('family', 'ครอบครัว'),
        ('inheritance', 'มรดก'),
        ('land', 'ที่ดิน'),
        ('labor', 'แรงงาน'),
        ('admin', 'ปกครอง'),
        ('ip', 'ทรัพย์สินทางปัญญา'),
        ('construction', 'ก่อสร้าง'),
        ('insurance', 'ประกันภัย'),
        ('document', 'งานเอกสาร'),
        ('consult', 'ที่ปรึกษา'),
        ('debt', 'บังคับคดี/ติดตามหนี้'),
    ], string='Case Type')

    case_status = fields.Selection([
        ('intake', 'รับเรื่อง'),
        ('review', 'ทนายกำลังตรวจสอบ'),
        ('in_progress', 'กำลังดำเนินการ'),
        ('court_pending', 'รอนัดศาล'),
        ('court_ongoing', 'อยู่ระหว่างพิจารณา'),
        ('settled', 'ยุติ/ไกล่เกลี่ย'),
        ('closed_won', 'ปิดคดี - ชนะ'),
        ('closed_lost', 'ปิดคดี - แพ้'),
        ('closed_other', 'ปิดคดี - อื่นๆ'),
    ], string='Case Status', default='intake', tracking=True)

    opposing_party = fields.Char(string='Opposing Party')
    court_id = fields.Many2one('legal.court', string='Court')
    statute_deadline = fields.Date(string='Statute of Limitations Deadline', tracking=True)
    court_date_ids = fields.One2many('legal.court.date', 'lead_id', string='Court Dates')
    court_date_count = fields.Integer(string='Court Dates', compute='_compute_court_date_count')
    case_summary = fields.Text(string='AI Case Summary')
    event_ids = fields.One2many('legal.case.event', 'lead_id', string='Events')
    line_user_id = fields.Char(string='LINE User ID', related='partner_id.line_user_id', store=True)
    collaborator_ids = fields.Many2many(
        'res.users', 'crm_lead_collaborator_rel', 'lead_id', 'user_id',
        string='Collaborators',
        help='ทนายที่ร่วมดูแลคดีนี้',
    )

    @api.depends('court_date_ids')
    def _compute_court_date_count(self):
        for lead in self:
            lead.court_date_count = len(lead.court_date_ids)

    def action_view_court_dates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Court Dates',
            'res_model': 'legal.court.date',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }
