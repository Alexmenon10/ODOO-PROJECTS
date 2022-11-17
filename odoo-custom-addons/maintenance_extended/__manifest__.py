{
    'name': "Maintenance",
    'version': '1.0',
    'summary': 'Maintenance',
    'sequence': '10',
    'category': 'Productivity',
    'description': """
    My Club PLayers and Coach Management
    """,
    'website': 'www.odoo15.com',
    'depends': ['maintenance',
                'mail', 'web_map', 'approvals'
                ],
    'qweb': [],
    'images': ['static/description/icon.png'],
    # data files always loaded at installation
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'wizard/date_wizard.xml',
        'views/report/report_maintenance_request.xml',
        'views/report/report.xml',
        'views/report/transfer.xml',

        'views/config.xml',
        'views/category.xml',
        'views/subcategory.xml',
        'views/equipment.xml',
        'views/request.xml',
        'views/transfer.xml',
        'views/menu.xml'

    ],
    # data files containing optionally loaded demonstration data
    'demo': [],
    'licence': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
