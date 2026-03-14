import logging
import json
import requests

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    line_notification_ids = fields.One2many(
        'line.notification', 'lead_id', string='LINE Notifications')
    line_notification_count = fields.Integer(
        compute='_compute_line_notification_count')

    @api.depends('line_notification_ids')
    def _compute_line_notification_count(self):
        for lead in self:
            lead.line_notification_count = len(lead.line_notification_ids)

    def write(self, vals):
        old_statuses = {lead.id: lead.case_status for lead in self}
        result = super().write(vals)
        if 'case_status' in vals:
            status_labels = dict(
                self._fields['case_status']._description_selection(self.env))
            for lead in self:
                old_status = old_statuses.get(lead.id)
                if old_status != vals['case_status']:
                    lead._send_line_status_notification()
                    # Create timeline event
                    old_label = status_labels.get(old_status, old_status or '-')
                    new_label = status_labels.get(vals['case_status'], vals['case_status'])
                    self.env['legal.case.event'].sudo().create({
                        'lead_id': lead.id,
                        'event_type': 'status_change',
                        'title': f'สถานะเปลี่ยนเป็น: {new_label}',
                        'description': f'{old_label} \u2192 {new_label}',
                    })
        return result

    def _send_line_status_notification(self):
        self.ensure_one()
        if not self.partner_id or not self.partner_id.line_user_id:
            return

        status_labels = dict(
            self._fields['case_status']._description_selection(self.env))
        status_text = status_labels.get(self.case_status, self.case_status)

        message = (
            f"แจ้งสถานะคดี: {self.name}\n"
            f"สถานะใหม่: {status_text}"
        )

        notification = self.env['line.notification'].create({
            'partner_id': self.partner_id.id,
            'line_user_id': self.partner_id.line_user_id,
            'lead_id': self.id,
            'notification_type': 'status_change',
            'message': message,
        })
        notification._send_push_message()

    def action_view_line_notifications(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'LINE Notifications',
            'res_model': 'line.notification',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }
