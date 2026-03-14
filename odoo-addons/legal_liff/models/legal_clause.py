from odoo import models, fields, api


class LegalClauseCategory(models.Model):
    _name = 'legal.clause.category'
    _description = 'Legal Clause Category'
    _order = 'sequence, name'

    name = fields.Char('Category Name', required=True)
    code = fields.Char('Code', required=True,
                       help='e.g. guarantee, penalty, termination, delivery')
    sequence = fields.Integer(default=10)
    parent_id = fields.Many2one('legal.clause.category', string='Parent Category')
    child_ids = fields.One2many('legal.clause.category', 'parent_id', string='Subcategories')
    clause_ids = fields.One2many('legal.clause', 'category_id', string='Clauses')
    clause_count = fields.Integer(compute='_compute_clause_count')
    description = fields.Text('Description')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Clause category code must be unique'),
    ]

    @api.depends('clause_ids')
    def _compute_clause_count(self):
        for rec in self:
            rec.clause_count = len(rec.clause_ids)


class LegalClause(models.Model):
    _name = 'legal.clause'
    _description = 'Legal Clause Library'
    _order = 'category_id, risk_level, sequence, name'

    name = fields.Char('Clause Name', required=True,
                       help='e.g. ข้อหลักประกัน (มาตรฐาน)')
    code = fields.Char('Code', required=True,
                       help='e.g. guarantee-standard')
    category_id = fields.Many2one(
        'legal.clause.category', string='Category',
        required=True, index=True,
    )
    sequence = fields.Integer(default=10)
    content = fields.Text('Clause Content', required=True,
                          help='เนื้อหาข้อสัญญา รองรับ {{placeholder}} และ Jinja2 syntax')
    content_html = fields.Html('Preview', compute='_compute_content_html', store=False)
    risk_level = fields.Selection([
        ('conservative', 'Conservative (ปลอดภัย)'),
        ('standard', 'Standard (มาตรฐาน)'),
        ('aggressive', 'Aggressive (เข้มงวด)'),
    ], string='Risk Level', default='standard', required=True, index=True)
    document_types = fields.Selection([
        ('contract', 'สัญญา'),
        ('letter', 'หนังสือ'),
        ('petition', 'คำร้อง/คำฟ้อง'),
        ('will', 'พินัยกรรม'),
        ('court_form', 'แบบพิมพ์ศาล'),
        ('all', 'ทุกประเภท'),
    ], string='Document Type', default='all')
    jurisdiction = fields.Selection([
        ('thailand', 'ไทย'),
        ('international', 'International'),
    ], string='Jurisdiction', default='thailand')
    legal_reference = fields.Char('Legal Reference',
                                  help='อ้างอิงกฎหมาย เช่น ป.พ.พ. มาตรา 538')
    version = fields.Integer('Version', default=1, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', index=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    approved_date = fields.Datetime('Approved Date', readonly=True)
    template_ids = fields.Many2many(
        'legal.document.template', 'clause_template_rel',
        'clause_id', 'template_id',
        string='Compatible Templates',
    )
    tags = fields.Char('Tags', help='คั่นด้วย comma เช่น ค้ำประกัน,หลักทรัพย์,สินเชื่อ')
    notes = fields.Text('Internal Notes')
    usage_count = fields.Integer('Times Used', default=0, readonly=True)

    _sql_constraints = [
        ('code_version_uniq', 'unique(code, version)', 'Clause code + version must be unique'),
    ]

    @api.depends('content')
    def _compute_content_html(self):
        for rec in self:
            if rec.content:
                # Simple markdown-like rendering for preview
                html = rec.content.replace('\n', '<br/>')
                rec.content_html = f'<div style="font-family: serif;">{html}</div>'
            else:
                rec.content_html = ''

    def action_submit_review(self):
        self.write({'state': 'review'})

    def action_approve(self):
        self.write({
            'state': 'approved',
            'approved_by': self.env.uid,
            'approved_date': fields.Datetime.now(),
        })

    def action_archive(self):
        self.write({'state': 'archived'})

    def action_back_to_draft(self):
        self.write({'state': 'draft'})

    def action_new_version(self):
        """Create a new version of this clause."""
        self.ensure_one()
        new_version = self.version + 1
        new_clause = self.copy({
            'version': new_version,
            'state': 'draft',
            'approved_by': False,
            'approved_date': False,
            'usage_count': 0,
        })
        # Archive old version
        self.action_archive()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'legal.clause',
            'res_id': new_clause.id,
            'view_mode': 'form',
        }

    def increment_usage(self):
        """Increment usage counter (called when clause is used in a document)."""
        self.sudo().write({'usage_count': self.usage_count + 1})
