# -*- coding: utf-8 -*-
{
    'name': "inventory_base_14.0.1",

    'summary': """
        Base Customization On Inventory(stock)""",

    'description': """
        Included Functionalities -
            1) Disallow negative inventory in the product master.-----------------------------(disallow_negative_inv.py/xml)
            2) Product Category Filtered based on 'release' Boolean and Description Field.----(categ_release_and_desc.py/xml)
            3) Product/Item Groups.-----------------------------------------------------------(product_groups.py/.xml)
            4) Update Quantity Button Invisible and 'quantity on hand' readonly.--------------(update_qty.xml)
            5) Product Category Dropdown No Create Edit.--------------------------------------(product_categ_no_create_edit.xml)
            6) Product Internal Reference Sequence Based on Category.-------------------------(prod_internal_ref_on_categ.py/xml)
            7) Product Category, Cost in Log note and Category change authorization-----------(product_cost_categ_track.py, product_categ_change_access.xml)
            8) Product Category, Item Group, Product Group1, Product Group2, Product Group3 is add to the filter and groupby.------------(product_groups.xml)
    """,

    'author': "Deva R",
    'category': 'Customization',
    'version': '14.0.4',

    'depends': ['base','stock','product'],

    'data': [
        'security/ir.model.access.csv',
        'security/product_categ_change_access.xml',
        'views/update_qty.xml',
        'views/product_groups.xml',
        'views/disallow_negative_inv.xml',
        'views/categ_release_and_desc.xml',
        'views/product_categ_no_create_edit.xml',
        'views/prod_internal_ref_on_categ.xml',
    ],
    'license': 'LGPL-3',
}
