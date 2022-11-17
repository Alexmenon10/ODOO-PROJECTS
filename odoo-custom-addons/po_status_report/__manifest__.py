{
    'name': 'PO Status Report',
    'author': 'Deva R',
    'version': '14.0.3',
    
    'category': 'Purchase',

    'summary': 'This module is useful to show the purchase order lines with status of GRN and Invoice',

    'description': """This module is useful to show the purchase order lines with status of GRN and Invoice""",
    
    'depends': ['purchase'],
    
    'data': [
        'views/purchase_order_line.xml',
    ],
    
    'auto_install': False,
    'installable' : True,
    'application': True,
    'license': "LGPL-3",
}
