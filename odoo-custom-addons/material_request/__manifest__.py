# -*- coding: utf-8 -*-
{
    'name': "Material Requisition",

    'summary': """
        Material Requisition""",

    'description': """
        Material Requisition
    """,

    'author': "Deva",

    'category': 'Customization',
    'version': '14.0.4.6',

    'depends': ['base','stock','purchase','purchase_base_14','purchase_requisition'],

    'data': [
        'security/ir.model.access.csv',
        'views/material_request.xml',
    ],
    'license': 'LGPL-3',
}
