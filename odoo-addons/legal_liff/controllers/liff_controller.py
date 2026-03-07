import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

CASE_TYPES = [
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
]


class LiffController(http.Controller):

    @http.route('/liff/intake', type='http', auth='public', methods=['GET'], csrf=False)
    def liff_intake(self, **kwargs):
        return request.render('legal_liff.liff_intake_page', {
            'case_types': CASE_TYPES,
            'error': '',
            'values': {},
        })

    @http.route('/liff/intake/submit', type='http', auth='public', methods=['POST'], csrf=True)
    def liff_intake_submit(self, **post):
        name = post.get('name', '').strip()
        phone = post.get('phone', '').strip()
        case_type = post.get('case_type', '')
        description = post.get('description', '').strip()
        line_user_id = post.get('line_user_id', '').strip()

        if not name or not case_type or not description:
            return request.render('legal_liff.liff_intake_page', {
                'case_types': CASE_TYPES,
                'error': 'กรุณากรอกข้อมูลให้ครบ: ชื่อ, ประเภทคดี, รายละเอียด',
                'values': post,
            })

        # Find or create partner
        Partner = request.env['res.partner'].sudo()
        partner = None
        if line_user_id:
            partner = Partner.search([('line_user_id', '=', line_user_id)], limit=1)
        if not partner and phone:
            partner = Partner.search([('phone', '=', phone)], limit=1)
        if not partner:
            partner = Partner.create({
                'name': name,
                'phone': phone,
                'line_user_id': line_user_id or False,
            })
        elif not partner.phone and phone:
            partner.write({'phone': phone})

        # Create CRM Lead
        case_type_labels = dict(CASE_TYPES)
        lead_name = f"{case_type_labels.get(case_type, case_type)} - {name}"
        lead = request.env['crm.lead'].sudo().create({
            'name': lead_name,
            'partner_id': partner.id,
            'phone': phone,
            'case_type': case_type,
            'case_status': 'intake',
            'description': description,
            'type': 'opportunity',
        })

        _logger.info('LIFF intake: created lead #%s for %s', lead.id, name)

        # Send LINE push notification
        if line_user_id:
            self._send_line_push(line_user_id, lead, name)

        return request.render('legal_liff.liff_intake_success', {
            'lead': lead,
            'name': name,
        })

    def _send_line_push(self, line_user_id, lead, name):
        try:
            import requests as req
            access_token = request.env['ir.config_parameter'].sudo().get_param(
                'line_integration.channel_access_token', '')
            if not access_token:
                return
            case_label = dict(CASE_TYPES).get(lead.case_type, '')
            resp = req.post(
                'https://api.line.me/v2/bot/message/push',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                },
                json={
                    'to': line_user_id,
                    'messages': [{
                        'type': 'text',
                        'text': (
                            f"รับเรื่องของคุณแล้วค่ะ (เลขที่ {lead.id})\n"
                            f"ประเภท: {case_label}\n\n"
                            "ทนายความจะตรวจสอบและติดต่อกลับโดยเร็วค่ะ"
                        ),
                    }],
                },
            )
            if resp.status_code != 200:
                _logger.error('LINE push failed: %s', resp.text)
        except Exception as e:
            _logger.error('LINE push error: %s', e)
