{
    'name': 'Real Estate',
    'version': '1.0',
    'depends': [
        'base',
        'web',
        'mail',
    ],
    'author': 'Your Name',
    'category': 'Real Estate',
    'description': """
        Real Estate Management Module
        ===========================
        Manage real estate properties and their sales process.
    """,
    'data': [
        'security/estate_security.xml',
        'security/ir.model.access.csv',
        'data/estate_sequence.xml',
        'data/mail_data.xml',
        'views/estate_property_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_property_offer_views.xml',
        'views/res_users_views.xml',
        'views/estate_menus.xml',
        'report/estate_property_reports.xml',
    ],
    'demo': [
        'demo/estate_demo.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'sequence': -100,
    'license': 'LGPL-3',
} 