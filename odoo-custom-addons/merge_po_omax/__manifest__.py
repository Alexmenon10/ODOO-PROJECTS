# -*- coding: utf-8 -*-
{
    "name":"Merge Purchase Orders",
    "author": "Alex",
    "version": "15.0.1.0",
    "website": " ",
    "category": "Purchase",
    'summary': """
        Merge Purchase Orders
        Merge Purchase Order
        Merge RFQ
        Merge Request For Quotation
        Merge PO
    """,
    'description': """
        This module use to merge Purchase orders when they have Vendor, 
        Purchase-Agreement and Payment-Terms are same and Purchase order must be in Draft state. 
    """,
    "depends": [
        "purchase", 
        "purchase_requisition",],
    "data": [
        "security/ir.model.access.csv",
        "wizard/merge_purchase_order.xml",
    ],
    'demo': [],
    'test':[],
    # "images": ["static/description/merge_banner.jpg",],
    'license': 'AGPL-3',
    'currency':'USD',
    'price': 10.0,
    'installable' : True,
    "auto_install" : False,
    "application" : True,
    "pre_init_hook": "pre_init_check",
}
