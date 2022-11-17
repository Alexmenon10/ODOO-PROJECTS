
{
    "name": "Petty Cash",
    "version": "15.0.1.1.0",
    "category": "Human Resources",
    "author": "appscop",
   
    "website": "appscomps",
    "depends": ["hr_expense"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_expense_sheet_views.xml",
        "views/hr_expense_views.xml",
        "views/petty_cash_views.xml",
        "wizard/expense_report.xml",
    ],
    "installable": True,
    'license': 'LGPL-3',
}
