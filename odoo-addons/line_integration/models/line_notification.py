import json
import logging
import requests

from odoo import models, fields

_logger = logging.getLogger(__name__)


class LineNotification(models.Model):
    _name = 'line.notification'
    _description = 'LINE Notification Log'
    _order = 'create_date desc'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    line_user_id = fields.Char(string='LINE User ID', required=True)
    lead_id = fields.Many2one('crm.lead', string='Related Case')
    notification_type = fields.Selection([
        ('status_change', 'Case Status Change'),
        ('appointment', 'Appointment Reminder'),
        ('court_date', 'Court Date Reminder'),
        ('deadline', 'Statute Deadline Warning'),
        ('document', 'Document Ready'),
        ('general', 'General'),
    ], string='Type', required=True)
    message = fields.Text(string='Message', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', readonly=True)
    error_message = fields.Text(string='Error', readonly=True)
    sent_at = fields.Datetime(string='Sent At', readonly=True)

    def _send_push_message(self):
        self.ensure_one()
        token = self.env['ir.config_parameter'].sudo().get_param(
            'line_integration.channel_access_token', '')
        if not token:
            self.write({'state': 'failed', 'error_message': 'Channel access token not configured'})
            return False

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        }
        payload = {
            'to': self.line_user_id,
            'messages': [{'type': 'text', 'text': self.message}],
        }
        try:
            resp = requests.post(
                'https://api.line.me/v2/bot/message/push',
                headers=headers,
                data=json.dumps(payload),
                timeout=10,
            )
            if resp.status_code == 200:
                self.write({
                    'state': 'sent',
                    'sent_at': fields.Datetime.now(),
                })
                return True
            else:
                self.write({
                    'state': 'failed',
                    'error_message': f'{resp.status_code}: {resp.text}',
                })
                return False
        except Exception as e:
            _logger.exception('LINE push failed for notification %s', self.id)
            self.write({'state': 'failed', 'error_message': str(e)})
            return False
