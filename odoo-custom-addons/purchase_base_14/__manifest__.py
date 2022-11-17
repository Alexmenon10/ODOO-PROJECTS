# -*- coding: utf-8 -*-
{
    'name': "Purchase Base Odoo 14",

    'summary': """
        Purchase Base Odoo 14""",

    'description': """
        Purchase Base Odoo 14
    """,

    'author': "Deva R",
    'category': 'Purchase',
    'version': '14.0.1.4',

    'depends': ['base','purchase','purchase_requisition','purchase_requisition_stock'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/ir_sequence_data.xml',
        'wizard/wiz_last_purchase_price.xml',
        'views/last_purchase_price.xml',
        'views/purchase_requisition.xml',
        'views/customfields.xml'
    ],
    'license': 'LGPL-3',
}
