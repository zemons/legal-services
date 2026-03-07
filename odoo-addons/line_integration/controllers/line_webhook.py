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
            elif event_type == 'postback':
                self._handle_postback(event)

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
        reply_token = event.get('replyToken')
        message = event.get('message', {})
        msg_type = message.get('type')
        msg_text = message.get('text', '')

        _logger.info(
            'LINE message from %s: type=%s text=%s',
            line_user_id[:8] if line_user_id else 'unknown',
            msg_type,
            msg_text[:50] if msg_text else '',
        )

        if not reply_token:
            return

        if msg_type == 'text' and msg_text:
            # TODO: เรียก adkcode AI agent เมื่อ deploy แล้ว
            self._reply_message(reply_token, [
                {
                    "type": "text",
                    "text": (
                        f"ได้รับคำถามของคุณแล้วค่ะ:\n\"{msg_text}\"\n\n"
                        "ขณะนี้ระบบ AI กำลังอยู่ระหว่างการพัฒนา "
                        "ทนายความจะติดต่อกลับโดยเร็วค่ะ"
                    )
                }
            ])
        elif msg_type == 'image':
            self._reply_message(reply_token, [
                {
                    "type": "text",
                    "text": "ได้รับรูปภาพแล้วค่ะ ระบบ OCR กำลังอยู่ระหว่างการพัฒนา"
                }
            ])

    def _handle_postback(self, event):
        data = event.get('postback', {}).get('data', '')
        reply_token = event.get('replyToken')
        if not reply_token:
            return

        if data == 'action=ask_question':
            self._reply_message(reply_token, [
                {
                    "type": "text",
                    "text": (
                        "พิมพ์คำถามกฎหมายของคุณลงในช่องแชทด้านล่างได้เลยค่ะ\n"
                        "AI จะตอบพร้อมอ้างอิงกฎหมาย/ฎีกาที่เกี่ยวข้อง\n\n"
                        "ตัวอย่างคำถาม:\n"
                        "- ถูกเลิกจ้างไม่เป็นธรรม เรียกค่าชดเชยได้ไหม\n"
                        "- สัญญาเช่าหมดแล้ว เจ้าของไม่คืนเงินมัดจำ\n"
                        "- อยากทำพินัยกรรม ต้องมีพยานกี่คน"
                    )
                }
            ])
        else:
            _logger.info('Unhandled postback: %s', data)

    def _reply_message(self, reply_token, messages):
        access_token = request.env['ir.config_parameter'].sudo().get_param(
            'line_integration.channel_access_token', '')
        if not access_token:
            _logger.warning('LINE access token not configured')
            return
        import requests as req
        resp = req.post(
            'https://api.line.me/v2/bot/message/reply',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            },
            json={
                'replyToken': reply_token,
                'messages': messages,
            },
        )
        if resp.status_code != 200:
            _logger.error('LINE reply failed: %s %s', resp.status_code, resp.text)
