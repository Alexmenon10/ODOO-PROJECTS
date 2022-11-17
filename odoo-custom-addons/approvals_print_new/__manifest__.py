{
    'name': 'Approval And Expense',
    'version': '15.0.1',
    'category': 'Human Resources/Approvals',
    'summary': 'Approval Requests Print',
    'description': """
Approval Requests Print Report
            """,
    'author': 'appscomp',
    'website': 'www.appscomp.com',
    'depends': ['approvals', 'hr_expense', 'maintenance', 'product'],
    'images': [''],
    'data': [
        'security/ir.model.access.csv',
        'report/approval_requests_report.xml',
        'wizard/approvalrefuse_view.xml',
        'views/expense_approval_view.xml',
        'views/approval_request.xml',
        'views/approval_category.xml',
        'views/approval_travel_view.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
