from . import controllers
from . import models


def _post_init_sync_template_fields(env):
    """Migrate existing required_fields JSON → field_ids records."""
    templates = env['legal.document.template'].search([
        ('required_fields', '!=', False),
        ('required_fields', '!=', '[]'),
    ])
    for tmpl in templates:
        if not tmpl.field_ids:
            tmpl._sync_fields_from_json()
