# -*- coding: utf-8 -*-
##############################################################################

{

    'name': 'Material Requisition Module',
    'version': '15.0.1',
    'category': 'Generic Modules / Account',
    'license': 'LGPL-3',
    'description': """  Material requirements planning (MRP) is a computer-based 
    inventory management system designed to improve productivity for businesses. 
    Companies use material requirements-planning systems to estimate quantities of 
    raw materials and schedule their deliveries. """,
    'author': 'Alex',
    'website': '',
    'depends': [
        'account', 'stock', 'product','purchase','hr',
        'sh_po_tender_management','gate_entry'
    ],
    'data': [
        'security/mrp_security.xml',
        'security/ir.model.access.csv',
        'data/sheduled_action.xml',
        'wizard/add_rfq_view.xml',
        'wizard/material_requisiton_report_view.xml',
        'wizard/purchase_order_excel_report_view.xml',
        'wizard/purchase_bill_view.xml',
        'views/material_requisition_view.xml',
        'views/material_approval_view.xml',
        'views/direct_delivery.xml',
        # 'views/purchase_approval_view.xml',
        'views/report/grn_report.xml',
        'views/report/purchase_order.xml',
        'views/report/material_requisition.xml',

    ],
    'installable': True,
    'active': True,

}
