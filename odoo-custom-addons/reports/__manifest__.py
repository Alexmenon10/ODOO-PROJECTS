# -*- coding: utf-8 -*-
{
    'name': 'Reports',
    'version': '1.0',
    'sequence': 1,
    'category': 'Generic Modules',
    'description': """  Reports Module helps us to view all the reports in one application """,
    'author': 'Appscomp Widget Pvt Ltd',
    'website': 'https://appscomp.com/',
    'depends': ['sale', 'sales_team', 'purchase', 'account', 'stock', 'hr', 'fleet',
                'hr_expense','sr_price_history_for_product','appscomp_fleet','material_requisition'],
    'data': [
        'views/all_reports.xml'
    ],
    'license': 'LGPL-3',
    'images': ['static/description/image.png'],
    'installable': True,
    'application': True,
    'active': True,
    'auto_install': False,
}
