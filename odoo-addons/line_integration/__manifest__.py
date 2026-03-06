{
    'name': 'LINE Integration',
    'version': '18.0.1.0.0',
    'category': 'Services/Legal',
    'summary': 'LINE OA integration for legal case notifications and user mapping',
    'description': """
        - REST endpoint for LINE webhook
        - Push notifications on case status change
        - Push notifications for appointments
        - LINE user_id <-> res.partner mapping
        - Notification history log
    """,
    'author': 'Zemons',
    'depends': ['legal_case'],
    'data': [
        'security/ir.model.access.csv',
        'views/line_notification_views.xml',
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
