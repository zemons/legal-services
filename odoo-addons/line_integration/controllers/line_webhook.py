import hashlib
import hmac
import base64
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Rich Menu IDs (set via System Parameters or hardcode here)
RICH_MENU_CLIENT = 'richmenu-13aa17513f4c0bfdfd0b497f6e2ee27e'
RICH_MENU_LAWYER = 'richmenu-3d04032231674921bd33f54f1580ab50'


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

    # -----------------------------------------------------------------
    # LINE Profile & Rich Menu helpers
    # -----------------------------------------------------------------

    def _get_line_profile(self, line_user_id):
        """Fetch user profile from LINE API. Returns dict or None."""
        access_token = request.env['ir.config_parameter'].sudo().get_param(
            'line_integration.channel_access_token', '')
        if not access_token:
            return None
        import requests as req
        try:
            resp = req.get(
                f'https://api.line.me/v2/bot/profile/{line_user_id}',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
            _logger.warning('LINE profile fetch failed: %s', resp.status_code)
        except Exception as e:
            _logger.error('LINE profile error: %s', e)
        return None

    def _sync_partner_profile(self, partner, line_user_id):
        """Sync LINE profile (display name, picture) to Odoo partner."""
        profile = self._get_line_profile(line_user_id)
        if not profile:
            return

        vals = {}
        display_name = profile.get('displayName', '')
        picture_url = profile.get('pictureUrl', '')

        if display_name and partner.line_display_name != display_name:
            vals['line_display_name'] = display_name
            # Update partner name if still placeholder
            if partner.name.startswith('LINE User '):
                vals['name'] = display_name

        if picture_url and partner.line_picture_url != picture_url:
            vals['line_picture_url'] = picture_url

        if vals:
            partner.write(vals)
            _logger.info('Synced LINE profile for %s: %s', line_user_id[:8], display_name)

    def _link_rich_menu(self, line_user_id, rich_menu_id):
        """Link a Rich Menu to a specific LINE user."""
        access_token = request.env['ir.config_parameter'].sudo().get_param(
            'line_integration.channel_access_token', '')
        if not access_token:
            return
        import requests as req
        try:
            resp = req.post(
                f'https://api.line.me/v2/bot/user/{line_user_id}/richmenu/{rich_menu_id}',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            if resp.status_code == 200:
                _logger.info('Linked Rich Menu %s to %s', rich_menu_id[-8:], line_user_id[:8])
            else:
                _logger.warning('Rich Menu link failed: %s %s', resp.status_code, resp.text[:100])
        except Exception as e:
            _logger.error('Rich Menu link error: %s', e)

    def _assign_rich_menu_by_role(self, line_user_id, role):
        """Assign the correct Rich Menu based on user role.
        Delegates to res.partner model method for consistency.
        Falls back to controller-level linking if partner not found.
        """
        partner = request.env['res.partner'].sudo().search(
            [('line_user_id', '=', line_user_id)], limit=1)
        if partner:
            partner._link_rich_menu_by_role()
        else:
            # Fallback for edge case where partner doesn't exist yet
            menu_client = request.env['ir.config_parameter'].sudo().get_param(
                'line_integration.rich_menu_client', RICH_MENU_CLIENT)
            menu_lawyer = request.env['ir.config_parameter'].sudo().get_param(
                'line_integration.rich_menu_lawyer', RICH_MENU_LAWYER)
            if role == 'lawyer':
                self._link_rich_menu(line_user_id, menu_lawyer)
            else:
                self._link_rich_menu(line_user_id, menu_client)

    def _get_or_create_partner(self, line_user_id):
        """Find or create partner by LINE user ID, sync profile, assign Rich Menu."""
        partner = request.env['res.partner'].sudo().search(
            [('line_user_id', '=', line_user_id)], limit=1)

        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': f'LINE User {line_user_id[:8]}',
                'line_user_id': line_user_id,
                'line_role': 'client',
            })
            _logger.info('Created partner for LINE user: %s', line_user_id[:8])
            # Sync profile and assign Rich Menu for new users
            self._sync_partner_profile(partner, line_user_id)
            self._assign_rich_menu_by_role(line_user_id, 'client')
        elif not partner.line_display_name:
            # Existing partner without profile — sync once
            self._sync_partner_profile(partner, line_user_id)

        return partner

    # -----------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------

    def _handle_follow(self, event):
        line_user_id = event.get('source', {}).get('userId')
        if not line_user_id:
            return
        self._get_or_create_partner(line_user_id)

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

        # Ensure partner exists and profile is synced
        if line_user_id:
            self._get_or_create_partner(line_user_id)

        if not reply_token:
            return

        if msg_type == 'text' and msg_text:
            # Call ADKcode AI agent
            ai_result = self._call_ai(msg_text, line_user_id)
            if ai_result:
                self._reply_message(reply_token, [
                    {"type": "text", "text": ai_result}
                ])
            else:
                self._reply_message(reply_token, [
                    {
                        "type": "text",
                        "text": (
                            f"ได้รับคำถามของคุณแล้วค่ะ\n"
                            "ขณะนี้ระบบ AI ไม่สามารถตอบได้ "
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
            # Client: แนะนำให้พิมพ์คำถามในแชท
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
        elif data == 'action=ask_question_lawyer':
            # Lawyer: ส่ง quick reply ให้เลือกประเภทงาน
            self._reply_message(reply_token, [
                {
                    "type": "text",
                    "text": (
                        "เลือกประเภทคำถาม หรือพิมพ์คำถามได้เลยค่ะ"
                    ),
                    "quickReply": {
                        "items": [
                            {
                                "type": "action",
                                "action": {
                                    "type": "postback",
                                    "label": "ค้นหาฎีกา/กฎหมาย",
                                    "data": "action=lawyer_search_law",
                                    "displayText": "ค้นหาฎีกา/กฎหมาย"
                                }
                            },
                            {
                                "type": "action",
                                "action": {
                                    "type": "postback",
                                    "label": "วิเคราะห์คดี",
                                    "data": "action=lawyer_analyze_case",
                                    "displayText": "วิเคราะห์คดี"
                                }
                            },
                            {
                                "type": "action",
                                "action": {
                                    "type": "postback",
                                    "label": "ร่างเอกสาร",
                                    "data": "action=lawyer_draft_doc",
                                    "displayText": "ร่างเอกสาร"
                                }
                            },
                            {
                                "type": "action",
                                "action": {
                                    "type": "postback",
                                    "label": "ถามทั่วไป",
                                    "data": "action=lawyer_general_question",
                                    "displayText": "ถามคำถามทั่วไป"
                                }
                            },
                        ]
                    }
                }
            ])
        else:
            _logger.info('Unhandled postback: %s', data)

    # -----------------------------------------------------------------
    # AI & LINE API calls
    # -----------------------------------------------------------------

    def _call_ai(self, text, line_user_id=''):
        """Call ADKcode legal AI agent via HTTP API."""
        import requests as req
        adkcode_url = request.env['ir.config_parameter'].sudo().get_param(
            'line_integration.adkcode_url', 'http://legal-adkcode:8000')
        try:
            resp = req.post(
                f'{adkcode_url}/chat',
                json={'content': text, 'line_user_id': line_user_id or ''},
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                if not data.get('is_error'):
                    result = data.get('result', '')
                    # LINE message limit is 5000 chars
                    if len(result) > 5000:
                        result = result[:4950] + '\n\n... (ข้อความยาวเกินไป)'
                    return result
                _logger.error('AI error: %s', data.get('result'))
            else:
                _logger.error('AI HTTP error: %s %s', resp.status_code, resp.text[:200])
        except req.exceptions.Timeout:
            _logger.error('AI timeout (120s)')
        except Exception as e:
            _logger.error('AI call failed: %s', e)
        return None

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
