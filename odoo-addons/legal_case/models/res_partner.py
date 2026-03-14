from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    line_user_id = fields.Char(string='LINE User ID', index=True)
    line_display_name = fields.Char(string='LINE Display Name', readonly=True)
    line_picture_url = fields.Char(string='LINE Picture URL', readonly=True)
    line_role = fields.Selection([
        ('client', 'Client'),
        ('lawyer', 'Lawyer'),
    ], string='LINE Role', default='client')
