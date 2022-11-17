{
    'name': 'Goods Receipt Note Report Template',
    'version': '14.0.08',
    'description': """This module consists, the goods receipt note report Templates""",
    'category': 'Localization',
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'company': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'depends': ['purchase', 'l10n_in', 'web', 'base'],
    'data': [
        'reports/goods_receiptnote_report.xml',
        'views/header_footer.xml', 
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
