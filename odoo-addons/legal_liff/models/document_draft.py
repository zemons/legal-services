import logging

from datetime import timedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Auto-cleanup rules: state -> (days_until_expire, days_until_delete)
CLEANUP_RULES = {
    'draft': (30, 180),
    'cancelled': (7, 180),
    'signed': (90, 180),
}


class LegalDocumentDraft(models.Model):
    _name = 'legal.document.draft'
    _description = 'Legal Document Draft'
    _order = 'create_date desc'

    name = fields.Char('Document Title', required=True)
    template_id = fields.Many2one('legal.document.template', string='Template', ondelete='set null')
    lead_id = fields.Many2one('crm.lead', string='Related Case', ondelete='set null')
    lawyer_partner_id = fields.Many2one('res.partner', string='Lawyer', required=True, ondelete='cascade')
    client_partner_id = fields.Many2one('res.partner', string='Client', ondelete='set null')
    state = fields.Selection([
        ('generating', 'กำลังสร้าง'),
        ('draft', 'ร่าง'),
        ('sent_to_client', 'ส่งลูกค้า'),
        ('revision', 'แก้ไข'),
        ('final', 'ฉบับสมบูรณ์'),
        ('signed', 'ลงนามแล้ว'),
        ('cancelled', 'ยกเลิก'),
        ('expired', 'หมดอายุ'),
    ], string='Status', default='generating', required=True, index=True)
    field_values = fields.Text('Field Values (JSON)')
    draft_content = fields.Text('Draft Content')
    docx_file = fields.Binary('DOCX File', attachment=True)
    docx_filename = fields.Char('DOCX Filename')
    revision_notes = fields.Text('Revision Notes')
    revision_count = fields.Integer('Revision Count', default=0)
    last_activity_date = fields.Datetime('Last Activity', default=fields.Datetime.now, index=True)
    signed_date = fields.Datetime('Signed Date')
    expiry_warning_sent = fields.Boolean('Expiry Warning Sent', default=False)

    # ── Version Control ────────────────────────────────────────
    version_ids = fields.One2many('legal.document.version', 'draft_id', string='Version History')
    current_version = fields.Integer('Current Version', default=0)

    def _save_version(self, change_type, change_summary='', changed_by=None):
        """Save current content as a version snapshot."""
        self.ensure_one()
        new_version = self.current_version + 1
        self.env['legal.document.version'].sudo().create({
            'draft_id': self.id,
            'version_number': new_version,
            'state_at_save': self.state,
            'content': self.draft_content,
            'docx_file': self.docx_file,
            'docx_filename': self.docx_filename,
            'field_values': self.field_values,
            'change_summary': change_summary,
            'changed_by': changed_by.id if changed_by else False,
            'change_type': change_type,
        })
        self.current_version = new_version
        return new_version

    # ── State transition methods (with version tracking) ───────

    def action_send_to_client(self):
        """Lawyer sends draft to client."""
        self.ensure_one()
        if self.state not in ('draft', 'revision'):
            return False
        self._save_version('lawyer_edit', 'ส่งให้ลูกค้าตรวจสอบ',
                           self.lawyer_partner_id)
        self.write({
            'state': 'sent_to_client',
            'last_activity_date': fields.Datetime.now(),
        })
        return True

    def action_request_revision(self, notes=''):
        """Client requests revision."""
        self.ensure_one()
        if self.state != 'sent_to_client':
            return False
        self._save_version('client_revision',
                           notes or 'ลูกค้าขอแก้ไข',
                           self.client_partner_id)
        self.write({
            'state': 'revision',
            'revision_notes': notes,
            'revision_count': self.revision_count + 1,
            'last_activity_date': fields.Datetime.now(),
        })
        return True

    def action_finalize(self):
        """Lawyer finalizes document."""
        self.ensure_one()
        if self.state not in ('draft', 'sent_to_client'):
            return False
        self._save_version('finalized', 'ยืนยันฉบับสมบูรณ์',
                           self.lawyer_partner_id)
        self.write({
            'state': 'final',
            'last_activity_date': fields.Datetime.now(),
        })
        return True

    def action_sign(self):
        """Client confirms signed."""
        self.ensure_one()
        if self.state != 'final':
            return False
        now = fields.Datetime.now()
        self._save_version('signed', 'ลงนาม',
                           self.client_partner_id)
        self.write({
            'state': 'signed',
            'signed_date': now,
            'last_activity_date': now,
        })
        return True

    def action_cancel(self):
        """Cancel document (any state except signed/expired)."""
        self.ensure_one()
        if self.state in ('signed', 'expired'):
            return False
        self.write({
            'state': 'cancelled',
            'last_activity_date': fields.Datetime.now(),
        })
        return True

    def action_back_to_draft(self):
        """Revert to draft (from revision/cancelled)."""
        self.ensure_one()
        if self.state not in ('revision', 'cancelled'):
            return False
        self.write({
            'state': 'draft',
            'last_activity_date': fields.Datetime.now(),
        })
        return True

    def action_restore_version(self, version_id):
        """Restore document content from a previous version."""
        self.ensure_one()
        version = self.env['legal.document.version'].browse(version_id)
        if version.draft_id != self:
            return False
        # Save current as version before restoring
        self._save_version('lawyer_edit',
                           f'ก่อนย้อนกลับไป v{version.version_number}',
                           self.env.user.partner_id)
        vals = {'last_activity_date': fields.Datetime.now()}
        if version.content:
            vals['draft_content'] = version.content
        if version.docx_file:
            vals['docx_file'] = version.docx_file
            vals['docx_filename'] = version.docx_filename
        if version.field_values:
            vals['field_values'] = version.field_values
        self.write(vals)
        return True

    # ── Cron: auto-cleanup ────────────────────────────────────

    @api.model
    def _cron_document_cleanup(self):
        """Auto-expire and delete old documents."""
        now = fields.Datetime.now()
        total_expired = 0
        total_deleted = 0

        # 1) Expire documents past their retention period
        for state, (expire_days, _) in CLEANUP_RULES.items():
            cutoff = now - timedelta(days=expire_days)
            docs = self.search([
                ('state', '=', state),
                ('last_activity_date', '<', cutoff),
            ])
            if docs:
                docs.write({
                    'state': 'expired',
                    'draft_content': False,
                    'field_values': False,
                    'last_activity_date': now,
                })
                total_expired += len(docs)
                _logger.info(
                    'Document cleanup: expired %d docs from state=%s (cutoff=%s)',
                    len(docs), state, cutoff,
                )

        # 2) Delete expired records older than 180 days
        delete_cutoff = now - timedelta(days=180)
        old_expired = self.search([
            ('state', '=', 'expired'),
            ('last_activity_date', '<', delete_cutoff),
        ])
        if old_expired:
            total_deleted = len(old_expired)
            old_expired.unlink()
            _logger.info('Document cleanup: deleted %d expired docs', total_deleted)

        # 3) Send expiry warnings (7 days before expiry)
        self._send_expiry_warnings(now)

        _logger.info(
            'Document cleanup done: expired=%d, deleted=%d',
            total_expired, total_deleted,
        )

    @api.model
    def _send_expiry_warnings(self, now):
        """Send LINE push notification 7 days before document expires."""
        for state, (expire_days, _) in CLEANUP_RULES.items():
            warn_cutoff = now - timedelta(days=expire_days - 7)
            docs = self.search([
                ('state', '=', state),
                ('last_activity_date', '<', warn_cutoff),
                ('expiry_warning_sent', '=', False),
            ])
            for doc in docs:
                partner = doc.lawyer_partner_id
                if partner.line_user_id:
                    self._push_expiry_warning(partner.line_user_id, doc)
                    doc.write({'expiry_warning_sent': True})

    @api.model
    def _push_expiry_warning(self, line_user_id, doc):
        """Send LINE push: document expiring soon."""
        import requests as req
        access_token = self.env['ir.config_parameter'].sudo().get_param(
            'line_integration.channel_access_token', '')
        if not access_token:
            return
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', '')
        try:
            req.post(
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
                            f'เอกสาร "{doc.name}" จะหมดอายุใน 7 วัน\n'
                            f'กรุณาดาวน์โหลดก่อนหมดอายุ\n\n'
                            f'{base_url}/liff/document/draft/{doc.id}'
                        ),
                    }],
                },
                timeout=10,
            )
        except Exception as e:
            _logger.error('Expiry warning push failed: %s', e)
