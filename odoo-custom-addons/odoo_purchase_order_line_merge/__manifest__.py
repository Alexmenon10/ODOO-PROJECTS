# -*- coding: utf-8 -*-
{
    'name': 'Odoo Purchase Line Merge',
    'version': '14.0',
    'category': 'Accounting',
    'summary': "Merge Duplicate Purchase Order Lines",
    'description':"""
    This module will merger the duplicate purchase lines in an invoice even if the purchase is fully processed.
    """,
    'author': 'Alex',
    'website': ' ',
    'depends': ['purchase'],
    'data': ['views/auto_po_line_merge.xml',
             # 'views/purchase_order_view.xml'
             ],

    'installable': True,
    'license': 'LGPL-3',
    # 'images': [
    #     'static/description/main.jpg',
    # ],
}
