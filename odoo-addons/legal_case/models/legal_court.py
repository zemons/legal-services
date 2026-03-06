from odoo import models, fields


class LegalCourt(models.Model):
    _name = 'legal.court'
    _description = 'Court'
    _order = 'name'

    name = fields.Char(string='Court Name', required=True)
    court_type = fields.Selection([
        ('civil', 'ศาลแพ่ง'),
        ('criminal', 'ศาลอาญา'),
        ('family', 'ศาลเยาวชนและครอบครัว'),
        ('labor', 'ศาลแรงงาน'),
        ('tax', 'ศาลภาษีอากร'),
        ('admin', 'ศาลปกครอง'),
        ('ip', 'ศาลทรัพย์สินทางปัญญา'),
        ('appeal', 'ศาลอุทธรณ์'),
        ('supreme', 'ศาลฎีกา'),
    ], string='Court Type')
    address = fields.Text(string='Address')
    phone = fields.Char(string='Phone')
    active = fields.Boolean(default=True)
