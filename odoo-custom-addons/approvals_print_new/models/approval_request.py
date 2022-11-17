from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    request_status = fields.Selection(selection_add=[
        ('new', 'To Submit'),
        ('pending', 'Submitted'),
        ('approved', 'Approved'),
        ('partial_refused', 'Partially Refused'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], default="new", compute="_compute_request_status",
        store=True, tracking=True,
        group_expand='_read_group_request_status')
    user_status = fields.Selection(selection_add=[
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

    source_location = fields.Selection(related="category_id.source_location")
    distination_location = fields.Selection(related="category_id.source_location")
    has_vechicle = fields.Selection(related="category_id.has_vechicle")
    has_vechicle_specification = fields.Selection(related="category_id.has_vechicle_specification")
    has_estimate_amount = fields.Selection(related="category_id.has_estimate_amount")
    has_borrow_approval = fields.Selection(related="category_id.has_borrow_approval")
    has_priority = fields.Selection(related="category_id.has_priority")
    has_payment = fields.Selection(related="category_id.has_payment")
    has_procurment = fields.Selection(related="category_id.has_procurment")
    has_trip = fields.Selection(related="category_id.has_trip")
    # user_id = fields.Many2one('res.users', 'User', help="The user responsible for this journal", default=lambda self: self.env.user)

    source = fields.Char(string="Source", required="True")
    source_from = fields.Char(string="Source")
    source = fields.Char(string="Source")
    travel_boolean = fields.Boolean(string="Travels")
    travel_update = fields.Boolean(string="Travel Update")
    distination = fields.Char(string="Distination")
    travel_date = fields.Date(string="Travel Date")
    vechicle_type = fields.Many2one('vehicle.type', string="Vechicle Type")
    # vechicle_type = fields.Char(string="Vechicle Type")


    estimte_amount = fields.Float(string="Estimate Amount")
    person_count = fields.Integer(string="Person Count",default=0)
    trip_count = fields.Integer(string="Trip Count",default=0)
    persons_list = fields.Many2many('hr.employee',string="Persons List")
    unit_from = fields.Many2one('stock.location', string="Unit From")
    unit_to = fields.Many2one('stock.location', string="Unit to")
    responsbility = fields.Char(string="Responsbility")
    priority = fields.Selection([
        ('high', 'High'),
        ('low', 'Low'),
    ])
    request_person = fields.Char(string="Request Person")
    request_purpose = fields.Text(string="Request Purpose")

    unit = fields.Many2one('stock.location', string="Unit")
    project = fields.Char(string="Project")

    category_id = fields.Many2one('approval.category', string="Category", required=False)

    vechicle_specification = fields.Selection([
        ('close', 'Closed Type Vehicle'),
        ('open', 'Open Type Vehicle'),
    ], string='Vechicle Specification')
    approval_travel_ids = fields.One2many('approval.travel', 'approval_list_id')

    pre_appreval_list = fields.Boolean("Pre Approval")

    pre_approval = fields.Many2one('approval.request', string='Pre_Approval')
    pre_approval_amount = fields.Float(related='pre_approval.amount')
    pre_approval_date = fields.Datetime(related='pre_approval.date')

    approval_pre_travel_ids = fields.One2many('approval.travel', 'approval_list_id')



    # @api.onchange('unit_to')
    # def unit_validation(self):
    #     if self.unit_to == self.unit_from:
    #         raise ValidationError("Unit To must be Differ from Unit From")


    @api.onchange('pre_approval')
    def pre_travel_approval(self):
        line_vals = []
        approvals = self.env['approval.request'].search([('name', '=', self.pre_approval.name)])
        for travel in approvals.approval_travel_ids:
            if self.pre_approval:
                vals = {
                    'pre_approval_from': travel.source,
                    'pre_approval_to': travel.distination,
                    'pre_approval_travel_date': travel.travel_date,
                }
                self.approval_pre_travel_ids = [(0, 0, vals)]
                print(vals)
        return line_vals
        print(travel.source)


    @api.onchange('persons_list')
    def count_employees(self):
        for employee in self:
            employee.person_count = len(self.persons_list)


    def get_line_items(self):
        line_vals = []
        for line in self:
            if line.source and line.distination:
                vals = [0, 0, {
                    'source': line.source,
                    'distination': line.distination,
                    'travel_date': line.travel_date,
                }]
                line_vals.append(vals)
        return line_vals


    def action_split_travel(self):
        requisition_created = False
        for line in self:
            if line.source and line.distination:
                requisition_created = line.update({
                    'source': False,
                    'distination': False,
                    'approval_travel_ids': line.get_line_items(),
                })
            print(len(self.approval_travel_ids))
            self.trip_count = len(self.approval_travel_ids)
            return True


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


    def expense_refuse_request(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approvers = self.mapped('approver_ids')
        if approver.approve_level == 'level1':
            # self.action_refuse_main()
            view_id = self.env['expense.refused.remarks']
            return {
                'type': 'ir.actions.act_window',
                'name': 'Expense Refused Remarks',
                'res_model': 'expense.refused.remarks',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': view_id.id,
                'view_id': self.env.ref('approvals_print_new.expense_refused_remarks_wizard', False).id,
                'target': 'new',
            }
        for users in approvers:
            if approver.approve_level in ('level2','level3'):
                if users.approve_level == 'level1'  and users.status != 'approved':
                    raise ValidationError("You Cannot Approve this before %s"%(dict(users._fields['approve_level'].selection).get(users.approve_level)))
                if users.approve_level == 'level2' and  approver.approve_level not in ('level1','level2') and users.status != 'approved':
                    raise ValidationError("You Cannot Approve this before %s"%(dict(users._fields['approve_level'].selection).get(users.approve_level)))

        # self.action_refuse_main()
        view_id = self.env['expense.refused.remarks']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense Refused Remarks',
            'res_model': 'expense.refused.remarks',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('approvals_print_new.expense_refused_remarks_wizard', False).id,
            'target': 'new',
        }

    def action_confirm(self):
        if self.source and self.distination:
            raise ValidationError("Please Click the + Button to save your Travel Details.")
        else:
            # make sure that the manager is present in the list if he is required
            self.ensure_one()
            if self.category_id.manager_approval == 'required':
                employee = self.env['hr.employee'].search([('user_id', '=', self.request_owner_id.id)], limit=1)
                if not employee.parent_id:
                    raise UserError(
                        _('This request needs to be approved by your manager. There is no manager linked to your employee profile.'))
                if not employee.parent_id.user_id:
                    raise UserError(
                        _('This request needs to be approved by your manager. There is no user linked to your manager.'))
                if not self.approver_ids.filtered(lambda a: a.user_id.id == employee.parent_id.user_id.id):
                    raise UserError(
                        _('This request needs to be approved by your manager. Your manager is not in the approvers list.'))
            if len(self.approver_ids) < self.approval_minimum:
                raise UserError(
                    _("You have to add at least %s approvers to confirm your request.", self.approval_minimum))
            if self.requirer_document == 'required' and not self.attachment_number:
                raise UserError(_("You have to attach at lease one document."))
            approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'new')
            approvers._create_activity()
            approvers.write({'status': 'pending'})
            self.write({'date_confirmed': fields.Datetime.now()})



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


class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    status = fields.Selection(selection_add=[
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('partial_refused', 'Partially Refused'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], string="Status", default="new", readonly=True)

