from datetime import datetime, date
from odoo.exceptions import UserError
from odoo import api, fields, models, _

class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    request_status = fields.Selection([
        ('new', 'To Submit'),
        ('pending', 'Submitted'),
        ('approved', 'Approved'),
        ('partial_refused', 'Partially Refused'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], default="new", compute="_compute_request_status",
        store=True, tracking=True,
        group_expand='_read_group_request_status')
    user_status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('partial_refused', 'Partially Refused'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], compute="_compute_user_status")
    approval_expense_state = fields.Selection([
        ('pending', 'Pending'),
        ('closed', 'Closed'),
    ], default='pending')
    my_expense_report_count = fields.Integer(compute='_compute_my_expense_report', string='Expense Report',
                                             default=0)
    permenant_refused_reason = fields.Text('Reason for Parmenant Refused')
    partial_refused_reason = fields.Text('Reason for Partial Refused')

    @api.depends('approver_ids.status')
    def _compute_user_status(self):
        for approval in self:
            approval.user_status = approval.approver_ids.filtered(
                lambda approver: approver.user_id == self.env.user).status

    def _compute_my_expense_report(self):
        self.my_expense_report_count = self.env['hr.expense'].sudo().search_count(
            [('approval_list.name', '=', self.name)])

    def my_expense_report(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('hr_expense.hr_expense_view_form')
        tree_view = self.sudo().env.ref('hr_expense.view_my_expenses_tree')
        return {
            'name': _('My Expense Report'),
            'res_model': 'hr.expense',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('approval_list.name', '=', self.name)],
        }


    def expense_refuse_request(self):
        view_id = self.env['expense.refused.remarks']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense Refused Remarks',
            'res_model': 'expense.refused.remarks',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('approvals_print.expense_refused_remarks_wizard', False).id,
            'target': 'new',
        }


class ApprovalExpense(models.Model):
    _inherit = "hr.expense"

    approval_expense = fields.Boolean(string='Approval Expense')
    approval_list = fields.Many2one('approval.request', string="Approvals")
    approval_amount = fields.Float(string="Approval Amount", related='approval_list.amount', store=True, readonly=False)
    approval_fixed = fields.Float(string="Approval Amount")
    approval_initiated = fields.Float(string="Amount Initiated")
    approval_balance_amount = fields.Float(string="Net Approve Balance", compute='_get_balance_amount', store=True)
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
    units = fields.Many2one('inventry.unit', string="Units")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, change_default=True, tracking=True,
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    close_reason = fields.Text('Reason for  Closed')
    amount_verified = fields.Boolean('Amount Verified...?', default=False)
    alert_message = fields.Text('Is Closed Verified...?',
                                default='Alert Note!,Once it Click..It will be Automatically Posted.')


    # @api.onchange('approval_list')
    # def _get_balance_default(self):
    #     for rec in self:
    #         rec.approval_balance_amount = rec.approval_amount

    @api.depends('approval_initiated','is_closed')
    def _get_balance_amount(self):
        for rec in self:
            if rec.amount_verified == True:
                for rec in self:
                    lc_process = self.env['approval.request'].sudo().search([('name', '=', rec.approval_list.name),
                                                                             ('request_status', '=', 'approved')])
                    # rec.approval_balance_amount = rec.approval_amount - rec.approval_initiated
                    rec.approval_balance_amount = rec.approval_fixed - rec.approval_initiated
                    rec.total_amount = rec.approval_initiated
                    lc_process.amount = rec.approval_balance_amount
            else:
                rec.approval_fixed = rec.approval_amount


    def expense_close_request(self):
        if self.is_closed == 'yes':
            view_id = self.env['close.reason']
            return {
                'type': 'ir.actions.act_window',
                'name': 'Expense Close Remarks',
                'res_model': 'close.reason',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': view_id.id,
                'view_id': self.env.ref('approvals_print.approval_close_reason_view_form', False).id,
                'target': 'new',
            }
        else:
            raise UserError('Please Select [Is Close THis Deal] is YES')

    # Create
    @api.model
    def create(self, vals):
        if vals['approval_amount'] >= 0.00:
            vals['amount_verified'] = True
        else:
            raise UserError(('Alert!,The Approval Amount,should be greater than zero ...., Please check it.'))
        if vals['approval_expense'] == True:
            if vals['approval_initiated'] <= vals['approval_amount']:
                if vals['is_closed'] == 'yes' or vals['approval_amount'] == vals['approval_initiated']:
                    approval_list = self.env['approval.request'].browse([vals['approval_list']])
                    approval_list.write({'approval_expense_state': 'closed'})
            else:
                raise UserError(('Alert!,Initial Amount must be smaller than Approval Amount'))

        return super(ApprovalExpense, self).create(vals)





class ExpenseRefusedRemarks(models.TransientModel):
    _name = 'expense.refused.remarks'
    _description = 'Expense Refused Remarks'
    _inherit = ['mail.thread']

    refused_reason = fields.Selection([
        ('parmenant', 'parmenant'),
        ('partial', 'Partial'),
    ],default="parmenant", string='Refused Reason')
    parmenant_refuse_remarks = fields.Text('Parmenant Remarks', readonly=False)
    partial_refuse_remarks = fields.Text('Partial Remarks', readonly=False)


    def tick_ok(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['approval.request'].search([('id', '=', applicant_id)])
        today = date.today()
        current_date = today.strftime("%d/%m/%Y")
        # current_date = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        current_user = self.env.user.name

        if active_id.request_status == 'pending' and self.refused_reason == 'parmenant':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + '[ ' + self.refused_reason + ' ]' + ' - ' + self.parmenant_refuse_remarks + '\n'
            self.action_refuse()

            active_id.write({'permenant_refused_reason': text,'partial_refused_reason': False})
        if active_id.request_status == 'pending' and self.refused_reason == 'partial':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + '[ ' + self.refused_reason + ' ]' + ' - ' + self.partial_refuse_remarks + '\n'
            self.action_refuse()
            active_id.write({'partial_refused_reason': text,'request_status': 'partial_refused','permenant_refused_reason': False})


        return True

    def action_refuse(self, approver=None):
        for rec in self:
            approval = rec.env['approval.request'].browse(rec.env.context.get('active_ids'))
            if self.refused_reason == 'parmenant':
                if not isinstance(approver, models.BaseModel):
                    approver = approval.mapped('approver_ids').filtered(
                        lambda approver: approver.user_id == approval.env.user
                    )
                approver.write({'status': 'refused'})
            if self.refused_reason == 'partial':
                if not isinstance(approver, models.BaseModel):
                    approver = approval.mapped('approver_ids').filtered(
                        lambda approver: approver.user_id == approval.env.user
                    )
                approver.write({'status': 'partial_refused'})

class ApprovalCloseReason(models.Model):
    _name = 'close.reason'
    _description = " Approval Close Reason"

    closereason = fields.Text(string="Reason")

    def close_reason_tictok(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['hr.expense'].search([('id', '=', applicant_id)])
        today = date.today()
        current_date = today.strftime("%d/%m/%Y")
        # current_date = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        current_user = self.env.user.name

        if active_id.state == 'draft':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + '[ ' + self.closereason + ' ]' + '\n'
            # active_id.expense_close_for_approval()
            active_id.write({'close_reason': text})

        return True


class ApprovalRequest(models.Model):
    _name = "inventry.unit"
    _descripion = "Approval Request Inventory Units"

    name = fields.Char('Units', index=True, required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company,
        index=True, readonly=True, required=True)
    partner_id = fields.Many2one('res.partner', 'Address', default=lambda self: self.env.company.partner_id,
                                 check_company=True)
    active = fields.Boolean('Active', default=True)

    code = fields.Char('Short Name', required=True, size=5, help="Short name used to identify your Units")




class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('partial_refused', 'Partially Refused'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], string="Status", default="new", readonly=True)


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    request_to_partial_refused_validate_count = fields.Integer(compute='_compute_request_to_partial_refused_validate_count',
                                                               string='umber of requests to Partial Refused Validate',
                                             default=0)

    def _compute_request_to_partial_refused_validate_count(self):
        domain = [('request_status', '=', 'partial_refused'), ('request_owner_id', '=', self.env.user.id)]
        requests_data = self.env['approval.request'].read_group(domain, ['category_id'], ['category_id'])
        requests_mapped_data = dict((data['category_id'][0], data['category_id_count']) for data in requests_data)
        for category in self:
            category.request_to_partial_refused_validate_count = requests_mapped_data.get(category.id, 0)
            self.env['approval.request'].write({'request_status': 'new'})

