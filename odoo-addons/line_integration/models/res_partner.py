import logging

import requests as req

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

RICH_MENU_CLIENT_DEFAULT = 'richmenu-13aa17513f4c0bfdfd0b497f6e2ee27e'
RICH_MENU_LAWYER_DEFAULT = 'richmenu-3d04032231674921bd33f54f1580ab50'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def write(self, vals):
        # Track role changes before write
        if 'line_role' in vals:
            partners_to_relink = self.filtered(
                lambda p: p.line_user_id and p.line_role != vals['line_role']
            )
        else:
            partners_to_relink = self.env['res.partner']

        result = super().write(vals)

        for partner in partners_to_relink:
            partner._link_rich_menu_by_role()
            partner._notify_role_change()

        return result

    def _link_rich_menu_by_role(self):
        """Link the correct Rich Menu based on partner's line_role."""
        self.ensure_one()
        if not self.line_user_id:
            return

        access_token = self.env['ir.config_parameter'].sudo().get_param(
            'line_integration.channel_access_token', '')
        if not access_token:
            _logger.warning('Cannot link rich menu: channel access token not configured')
            return

        if self.line_role == 'lawyer':
            menu_id = self.env['ir.config_parameter'].sudo().get_param(
                'line_integration.rich_menu_lawyer', RICH_MENU_LAWYER_DEFAULT)
        else:
            menu_id = self.env['ir.config_parameter'].sudo().get_param(
                'line_integration.rich_menu_client', RICH_MENU_CLIENT_DEFAULT)

        try:
            resp = req.post(
                f'https://api.line.me/v2/bot/user/{self.line_user_id}/richmenu/{menu_id}',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )
            if resp.status_code == 200:
                _logger.info(
                    'Rich Menu re-linked: %s -> %s (%s)',
                    self.line_user_id[:8], self.line_role, menu_id[-8:],
                )
            else:
                _logger.warning(
                    'Rich Menu re-link failed: %s %s',
                    resp.status_code, resp.text[:100],
                )
        except Exception as e:
            _logger.error('Rich Menu re-link error for %s: %s', self.line_user_id[:8], e)

    def _notify_role_change(self):
        """Send LINE push notification when role changes."""
        self.ensure_one()
        if not self.line_user_id:
            return

        role_labels = {'client': 'ลูกค้า', 'lawyer': 'ทนายความ'}
        role_text = role_labels.get(self.line_role, self.line_role)

        message = f"บทบาทของคุณถูกเปลี่ยนเป็น: {role_text}\nเมนูด้านล่างได้อัปเดตแล้วค่ะ"

        self.env['line.notification'].sudo().create({
            'partner_id': self.id,
            'line_user_id': self.line_user_id,
            'notification_type': 'general',
            'message': message,
        })._send_push_message()

    def action_set_lawyer(self):
        """One-click button: promote partner to lawyer role + create portal user."""
        for partner in self:
            if partner.line_role == 'lawyer':
                continue
            partner.write({'line_role': 'lawyer'})
            partner._ensure_portal_user()

    def action_set_client(self):
        """One-click button: revert partner to client role."""
        for partner in self:
            if partner.line_role == 'client':
                continue
            partner.write({'line_role': 'client'})

    def _ensure_portal_user(self):
        """Create a portal res.users for this partner if none exists."""
        self.ensure_one()
        existing = self.env['res.users'].sudo().search(
            [('partner_id', '=', self.id)], limit=1)
        if existing:
            return existing

        # Generate login from LINE display name or partner name
        login = self.line_user_id or self.email or f'lawyer_{self.id}'
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        if not portal_group:
            _logger.warning('Portal group not found, skipping user creation for %s', self.name)
            return self.env['res.users']

        try:
            user = self.env['res.users'].sudo().create({
                'name': self.name,
                'login': login,
                'partner_id': self.id,
                'groups_id': [(6, 0, [portal_group.id])],
            })
            _logger.info('Created portal user %s for lawyer %s', user.login, self.name)
            return user
        except Exception as e:
            _logger.error('Failed to create portal user for %s: %s', self.name, e)
            return self.env['res.users']
