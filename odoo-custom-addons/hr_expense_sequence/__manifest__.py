

{
    "name": "HR expense sequence",
    "version": "15.0.1.0.0",
    "category": "Human Resources",
    "author": "apps",
    "website": "apps",
    "depends": ["hr_expense"],
    "data": [
        "data/hr_expense_data.xml",
        "views/hr_expense_expense_view.xml",
        "report/report_expense_sheet.xml",
    ],
    "installable": True,
    "post_init_hook": "assign_old_sequences",
    'license': 'LGPL-3',
}
