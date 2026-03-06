{
    'name': 'Legal Case Management',
    'version': '18.0.1.0.0',
    'category': 'Services/Legal',
    'summary': 'Extend CRM leads with legal case management fields',
    'description': """
        Extends crm.lead with:
        - Case type (แพ่ง/อาญา/ครอบครัว/ที่ดิน/แรงงาน...)
        - Case status tracking
        - Court information
        - Statute of limitations deadline
        - Court dates scheduling
        - LINE user mapping
    """,
    'author': 'Zemons',
    'depends': ['crm', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'data/case_type_data.xml',
        'views/crm_lead_views.xml',
        'views/court_views.xml',
        'views/court_date_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
