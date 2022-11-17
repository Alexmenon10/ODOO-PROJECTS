# -*- coding: utf-8 -*-
{
    'name': "Inventory Base Summary",

    'summary': """
        Inventory Base Summary""",

    'description': """
        Inventory Base Summary
    """,

    'author': "Deva R",
    'category': 'Inventory',
    'version': '14.0.1.5',

    'depends': ['base','product','stock','stock_account','inventory_base'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'license': 'LGPL-3',
}