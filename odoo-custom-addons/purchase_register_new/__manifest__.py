# -*- coding: utf-8 -*-
{
    'name': "New Purchase Register Report",

    'summary': """
        This module is used for the Purchase Register Report 
    """,

    'description': """
        This module is used to capture the Purchase Register Report 
    """,

    'author': "Deva R",
    'category': 'Purchase',
    'version': '14.0.1.14',

    'depends': ['base','account','l10n_in'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_register_new.xml'
    ],
    'license': 'LGPL-3',
}
