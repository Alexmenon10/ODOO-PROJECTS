from datetime import datetime, date
from odoo.exceptions import UserError
from odoo import api, fields, models, _

class ApprovalExpense(models.Model):
    _inherit = "hr.expense"

    approval_expense = fields.Boolean(string='Approval Expense')
    approval_list = fields.Many2one('approval.request', string="Approvals")
    approval_amount = fields.Float(string="Approval Amount", related='approval_list.amount', store=True, readonly=False)
    approval_fixed = fields.Float(string="Approval Amount")
    approval_initiated = fields.Float(string="Amount Initiated")
    approval_balance_amount = fields.Float(string="Net Approve Balance", store=True)
    is_closed = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], default="no", string='Is close This Deal..?')
    reference = fields.Char('Bill Reference/Bill Date')
    product_id = fields.Many2one('product.product', string='Expense Category', readonly=True, tracking=True,
                                 states={'draft': [('readonly', False)], 'reported': [('readonly', False)],
                                         'refused': [('readonly', False)]},
                                 domain="[('can_be_expensed', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 ondelete='restrict')
    expensed_by = fields.Char('Expensed By')
    department = fields.Many2one('hr.department', string="Department")
    units = fields.Many2one('expense.unit', string="Unit/Section")
    expense_payment = fields.Many2one('expense.payment', string="Payment")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, change_default=True, tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    close_reason = fields.Text('Reason for  Closed')
    amount_verified = fields.Boolean('Amount Verified...?', default=False)
    alert_message = fields.Text('Is Closed Verified...?',
                                default='Alert Note!,Once it Click..It will be Automatically Posted.')

    name = fields.Char('Expense Description', compute='_compute_from_product_id_company_id', store=True, required=True,
                       copy=True,
                       states={'draft': [('readonly', False)], 'reported': [('readonly', False)],
                               'refused': [('readonly', False)]})
    subproduct_id = fields.Many2one('vehicle.type', string="Sub Product", required=True, domain="[('product', '=', product_id)]")
    non_vendor = fields.Char('Non Vendor')
    neft_percent = fields.Float(string='Neft')
    neft_cash = fields.Float(string='Cash')
    neft_cash_hide = fields.Boolean('Neft & Cash')

    @api.onchange('expense_payment','neft_percent')
    def expense_payment_mode(self):
        for values in self:
            if values.expense_payment.name == 'Neft+Cash':
                if values.neft_percent > 0.00:
                    total = values.total_amount * (1 - (values.neft_percent or 0.0) / 100.0)
                    values.neft_cash = total
                values.neft_cash_hide = True
            else:
                values.neft_cash_hide = False

class ExpenseUnit(models.Model):
    _name = "expense.unit"
    _description = 'Expense Unit'

    name = fields.Char('Unit', index=True, required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        index=True, readonly=True, required=True)
    partner_id = fields.Many2one('res.partner', 'Address', default=lambda self: self.env.company.partner_id,
                                 check_company=True)
    active = fields.Boolean('Active', default=True)

    code = fields.Char('Short Name', required=True, size=5, help="Short name used to identify your Unit")


class ExpensePayment(models.Model):
    _name = "expense.payment"
    _description = 'Expense Payment'

    name = fields.Char(string='Payment Mode')








