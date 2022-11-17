{
    'name': 'Purchase report Template MAS',
    'version': '14.0.0.9',
    'description': """This module consists, the customized purchase order Templates""",
    'category': 'Localization',
    'author': 'Deva R',
    'depends': ['purchase','l10n_in','web','base',],
    'data': [
	'reports/purchaseorder_report.xml',
        'views/header_footer.xml',
        # 'views/fonts.xml',
        # 'views/purchase.xml',
    ],
'assets': {
        'web.assets_backend': [
            'purchase_order_mas/static/src/css/fonts.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',

}
