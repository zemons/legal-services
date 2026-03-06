import hashlib
import hmac
import base64
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class LineWebhookController(http.Controller):

    @http.route('/line/webhook', type='json', auth='none', methods=['POST'], csrf=False)
    def line_webhook(self):
        body = request.httprequest.get_data(as_text=True)
        signature = request.httprequest.headers.get('X-Line-Signature', '')

        channel_secret = request.env['ir.config_parameter'].sudo().get_param(
            'line_integration.channel_secret', '')

        if not self._verify_signature(body, signature, channel_secret):
            _logger.warning('LINE webhook: invalid signature')
            return {'status': 'error', 'message': 'Invalid signature'}

        data = json.loads(body)
        events = data.get('events', [])

        for event in events:
            event_type = event.get('type')
            if event_type == 'follow':
                self._handle_follow(event)
            elif event_type == 'message':
                self._handle_message(event)

        return {'status': 'ok'}

    def _verify_signature(self, body, signature, channel_secret):
        if not channel_secret:
            _logger.warning('LINE channel secret not configured')
            return False
        hash_value = hmac.new(
            channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected = base64.b64encode(hash_value).decode('utf-8')
        return hmac.compare_digest(signature, expected)

    def _handle_follow(self, event):
        line_user_id = event.get('source', {}).get('userId')
        if not line_user_id:
            return
        partner = request.env['res.partner'].sudo().search(
            [('line_user_id', '=', line_user_id)], limit=1)
        if not partner:
            request.env['res.partner'].sudo().create({
                'name': f'LINE User {line_user_id[:8]}',
                'line_user_id': line_user_id,
            })
            _logger.info('Created partner for LINE user: %s', line_user_id[:8])

    def _handle_message(self, event):
        line_user_id = event.get('source', {}).get('userId')
        message = event.get('message', {})
        _logger.info(
            'LINE message from %s: type=%s',
            line_user_id[:8] if line_user_id else 'unknown',
            message.get('type'),
        )
