# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, ValidationError
import base64
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pdb

MATERIAL_REQUISITION_STATES = [
    ('draft', 'Draft'),
    ('ongoing', 'Ongoing'),
    ('in_progress', 'Confirmed'),
    ('to_be_approved', 'Waiting Approval'),
    ('leader_approval', 'Waiting 1st Approval'),
    ('manager_approval', 'Waiting 2nd Approval'),
    ('director_approval', 'Waiting 3rd Approval'),
    ('open', 'Approved'),
    ('done', 'Closed'),
    ('cancel', 'Cancelled'),
    ('rejection', 'Rejected')
]


class material_approval_config(models.Model):
    _name = 'material.approval.config'
    _description = 'Material Approval Configuration'
    # _rec_name = 'type_of_material'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    def _default_seq_id(self):
        return self.env['ir.sequence'].search([('code', '=', 'material.requisition.indent')], limit=1).id

    def _default_journal(self):
        return self.env['account.journal'].search([('type', '=', 'sale')], limit=1).id

    @api.onchange('approval_levels')
    def onchange_approvals(self):
        if self.approval_levels:
            if self.approval_levels == 'first_level':
                self.first_approval = False
                self.second_approval = False
                self.third_approval = False
                self.fourth_approval = False
                self.fifth_approval = False
            elif self.approval_levels == 'second_level':
                self.first_approval = False
                self.second_approval = False
                self.third_approval = False
                self.fourth_approval = False
                self.fifth_approval = False
            elif self.approval_levels == 'third_level':
                self.first_approval = False
                self.second_approval = False
                self.third_approval = False
                self.fourth_approval = False
                self.fifth_approval = False
            elif self.approval_levels == 'fourth_level':
                self.first_approval = False
                self.second_approval = False
                self.third_approval = False
                self.fourth_approval = False
                self.fifth_approval = False
            elif self.approval_levels == 'fifth_level':
                self.first_approval = False
                self.second_approval = False
                self.third_approval = False
                self.fourth_approval = False
                self.fifth_approval = False

    color = fields.Integer('Color')
    approval_type = fields.Selection([
        ('material_request', 'Material Request'),
    ], default='material_request', copy=False, string="Approvals Type", readonly=True, tracking=True)
    type_of_purchase = fields.Char(string="Material Type", tracking=True, copy=False)
    approval_levels = fields.Selection([
        ('first_level', '1'),
        ('second_level', '2'),
        ('third_level', '3'),
        ('fourth_level', '4'),
        ('fifth_level', '5')], default='first_level', copy=False, string="No.of Approvals", tracking=True)
    first_approval = fields.Many2one('res.users', string="First Approval", tracking=True)
    second_approval = fields.Many2one('res.users', string="Second Approval", tracking=True)
    third_approval = fields.Many2one('res.users', string="Third Approval", tracking=True)
    fourth_approval = fields.Many2one('res.users', string="Fourth Approval", tracking=True)
    fifth_approval = fields.Many2one('res.users', string="Fifth Approval", tracking=True)
    first_approval_amount_from = fields.Float(string="", tracking=True)
    first_approval_amount_to = fields.Float(string="", tracking=True)
    second_approval_amount_from = fields.Float(string="", tracking=True)
    second_approval_amount_to = fields.Float(string="", tracking=True)
    third_approval_amount_from = fields.Float(string="", tracking=True)
    third_approval_amount_to = fields.Float(string="", tracking=True)
    fourth_approval_amount_from = fields.Float(string="", tracking=True)
    fourth_approval_amount_to = fields.Float(string="", tracking=True)
    fifth_approval_amount_from = fields.Float(string="", tracking=True)
    fifth_approval_amount_to = fields.Float(string="", tracking=True)
    material_limit = fields.Float(string="Material Value", tracking=True)
    product_categ = fields.Many2many('product.category', string="Product Categories", tracking=True)
    default_type = fields.Boolean(string="Default")
    lc_applicable = fields.Boolean(string="LC Applicable")
    seq_id = fields.Many2one('ir.sequence', string="Sequence", default=_default_seq_id)
    purchase_journal_id = fields.Many2one('account.journal', string="Material Journal",
                                          domain=['|', ('type', '=', 'purchase'), ('company_id', '=', 'company_id')])

    # count_quotations = fields.Integer(compute='_compute_purchase_count', default=0)
    # count_waiting_for_approval = fields.Integer(compute='_compute_purchase_count', default=0)
    # count_confirmed = fields.Integer(compute='_compute_purchase_count', default=0)
    # count_total_po = fields.Integer(compute='_compute_purchase_count', default=0)
    purchase_cancel_users = fields.Many2many('res.users', 'purchase_cancel_user_rel', string='Approved Purchase Cancel')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    material_types = fields.Selection([
        ('local', 'Local'),
        ('import', 'Import'),
        ('general', 'General'),
        ('asset', 'Asset'),
    ], 'Material Types', tracking=True)

    def name_get(self):
        result = []
        for bank in self:
            name = bank.type_of_purchase
            result.append((bank.id, name))
        return result

    # @api.onchange('type_of_purchase')
    # def onchange_stages(self):
    #     if self.type_of_purchase:
    #         app_id = self.env['material.approval.config'].search([('id', '=', self.type_of_purchase.id)])
    #         self.approval_stages = app_id.approval_levels

    @api.model
    def create(self, vals):
        res = super(material_approval_config, self).create(vals)
        if vals.get('approval_levels') in ('first_level', 'second_level', 'third_level'):
            if vals.get('first_approval') == False:
                raise UserError(_('Kindly set the First Approval.'))
        if vals.get('approval_levels') in ('second_level', 'third_level'):
            if vals.get('second_approval') == False:
                raise UserError(_('Kindly set the Second Approval.'))
        if vals.get('approval_levels') == 'third_level':
            if vals.get('third_approval') == False:
                raise UserError(_('Kindly set the Third Approval.'))
        if vals.get('approval_levels') == 'fourth_level':
            if vals.get('fourth_approval') == False:
                raise UserError(_('Kindly set the Fourth Approval.'))
        if vals.get('approval_levels') == 'fifth_level':
            if vals.get('fifth_approval') == False:
                raise UserError(_('Kindly set the Fifth Approval.'))
        return res

    def write(self, vals):
        res = super(material_approval_config, self).write(vals)
        if vals.get('approval_levels') in ('first_level', 'second_level', 'third_level') or \
                self.approval_levels in ('first_level', 'second_level', 'third_level'):
            if vals.get('first_approval') == False or self.first_approval == False:
                raise UserError(_('Kindly set the First Approval.'))
        if vals.get('approval_levels') in ('second_level', 'third_level') or \
                self.approval_levels in ('second_level', 'third_level'):
            if vals.get('second_approval') == False or self.second_approval == False:
                raise UserError(_('Kindly set the Second Approval.'))
        if vals.get('approval_levels') == 'third_level' or \
                self.approval_levels == 'third_level':
            if vals.get('third_approval') == False or self.third_approval == False:
                raise UserError(_('Kindly set the Third Approval.'))
        if vals.get('approval_levels') == 'fourth_level' or \
                self.approval_levels == 'fourth_level':
            if vals.get('fourth_approval') == False or self.fourth_approval == False:
                raise UserError(_('Kindly set the Fourth Approval.'))
        if vals.get('approval_levels') == 'fifth_level' or \
                self.approval_levels == 'fifth_level':
            if vals.get('fifth_approval') == False or self.fifth_approval == False:
                raise UserError(_('Kindly set the Fifth Approval.'))
        return res


class MaterialRequisitionIndent(models.Model):
    _inherit = 'material.requisition.indent'

    def _default_approval_levels(self):
        app_id = self.env['material.approval.config'].search(
            [('default_type', '=', True), ('approval_type', '=', 'material_request')], limit=1)
        return app_id.approval_levels

    type_of_purchase = fields.Many2one('material.approval.config', string="Type Of Material", copy=False,
                                       domain="[('approval_type','=', 'material_request')]",
                                       tracking=True)
    approval_responsible = fields.Many2one('res.users', copy=False, store=True, compute="compute_approver",
                                           string="Approval Responsible", tracking=True)
    approver1 = fields.Many2one('res.users', string="Approver 1", copy=False, tracking=True,
                                related='type_of_purchase.first_approval')
    approver2 = fields.Many2one('res.users', string="Approver 2", copy=False, tracking=True,
                                related='type_of_purchase.second_approval')
    approver3 = fields.Many2one('res.users', string="Approver 3", copy=False, tracking=True,
                                related='type_of_purchase.third_approval')
    approver4 = fields.Many2one('res.users', string="Approver 4", copy=False, tracking=True,
                                related='type_of_purchase.fourth_approval')
    approver5 = fields.Many2one('res.users', string="Approver 5", copy=False, tracking=True,
                                related='type_of_purchase.fifth_approval')
    approval_stages = fields.Selection(string="No.of Approvals", related='type_of_purchase.approval_levels')
    # ('first_level', '1'),
    # ('second_level', '2'),
    # ('third_level', '3'),
    # ('fourth_level', '4'),
    # ('fifth_level', '5')], copy=False, default='fourth_level', string="No.of Approvals")
    approval_checked = fields.Boolean(string="Approval Checked", copy=False)
    is_request_approval = fields.Boolean(string="Request Approval", copy=False, default=False)
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('to_be_approved', 'Waiting 1st Level Approval'),
        ('leader_approval', 'Waiting 2nd Level Approval'),
        ('manager_approval', 'Waiting 3rd Level Approval'),
        ('director_approval', 'Waiting 4th Level Approval'),
        ('ceo_approval', 'Waiting 5th Level Approval'),
        ('request_rfq', 'Request For RFQ'),
        ('rfq_create', 'RFQ Created'),
        ('tender_create', 'Tender Created'),
        ('done', 'Done'),
        ('request_for_store_approval', 'Request for Store Verify'),
        ('request_approved_store', 'Request Verified By Store Team'),
    ], string='Status', readonly=True, index=True, copy=False, tracking=True)
    automated_sequence = fields.Boolean('Automated Sequence?',
                                        help="If checked, the Approval Requests will have an automated generated name based on the given code.")

    request_to_validate_count = fields.Integer("Number of requests to validate",
                                               compute="_compute_request_to_validate_count")

    def _compute_request_to_validate_count(self):
        self.request_to_validate_count = self.env['material.requisition.indent'].sudo().search_count(
            [('state', '=', 'to_be_approved'), ('approver1', '=', self.env.user.id)])

    # def _compute_request_to_validate_count(self):
    #     print('151515')
    #     domain = [('state', '=', 'to_be_approved'), ('approver1', '=', self.env.user.id)]
    #     requests_data = self.env['material.requisition.indent'].read_group(domain, ['name'], ['name'])
    #     requests_mapped_data = dict((data['name'][0], data['name_count']) for data in requests_data)
    #     for category in self:
    #         category.request_to_validate_count = requests_mapped_data.get(category.name, 0)

    def indent_request_for_store_approval(self):
        date = datetime.now()
        self.current_date = date
        hour = date + timedelta(hours=1)
        self.add_hour_date = hour
        if self.add_hour_date:
            self.write({
                'cron_Boolean': True})
        for indent in self:
            indent.write({
                'state': 'draft', 'store_request': True, 'ribbon_state': 'store_to_verify'})

    def cron_approve_store_approval_manually(self):
        cron_store = self.sudo().env['material.requisition.indent'].search([('cron_Boolean', '=', True),('store_request', '=', True),
                                                                            ('state', '!=','request_approved_store')])
        for record in cron_store:
            from datetime import datetime, date
            from dateutil.relativedelta import relativedelta
            today = datetime.today().date()
            import datetime
            today_print = today.strftime("%d/%m/%Y")
            # data = self.lead_attachment_report_excel()
            body = """
                              Dear Team,
                              <br/>
                              <br/>
                              The Purchase Indent(Material Requisiton) of %s is not approved by Store Team, SO System automatically approved the request.
                                  <br/>
                                  <br/>
                              Regards,<br/>
                              ODOO
                              <p align="center">----------------------------------This is a system generated email----------------------------------------------</p>"""% (record.name),
            import datetime
            today_print = today.strftime("%d/%m/%Y")
            mail_value = {
                'subject': 'The Purchase Indent(Material Requisiton) of %s, is not approved by Store Team (%s)' % (record.name,today_print),
                'body_html': body,
                'email_cc': record.request_raised_for.work_email,
                'email_to': record.approver1.employee_id.work_email,
                'email_from': record.responsible.work_email,
                # 'attachment_ids': [(6, 0, [data_id.id])],
            }
            self.env['mail.mail'].create(mail_value).send()

            record.write({'state': 'request_approved_store', 'ribbon_state': 'store_verified'})


    def indent_request_approved_store(self):
        view_id = self.env['store.verified.remark']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Store Verified Remark',
            'res_model': 'store.verified.remark',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('material_requisition.view_store_verified_remark_form', False).id,
            'target': 'new',
        }
        # for indent in self:
        #     indent.write({
        #         'state': 'request_approved_store', 'store_approval': True, 'ribbon_state': 'store_verified'})

    @api.onchange('type_of_purchase')
    def approval_details(self):
        if self.type_of_purchase:
            self.sudo().write({
                'approval_stages': self.type_of_purchase.approval_levels,
                # 'requester_department_id': self.request_raised_for.department_id.id,
                # 'requester_current_job_id': self.request_raised_for.job_id.id,
            })

    @api.depends('state')
    def compute_approver(self):
        for order in self:
            # if not order.approval_stages == 'zero_level':
            if order.approval_stages == 'first_level':
                order.approval_responsible = order.approver1
            elif order.approval_stages == 'second_level':
                if order.state in ('draft', 'to_be_approved'):
                    order.approval_responsible = order.approver1
                elif order.state == 'leader_approval':
                    order.approval_responsible = order.approver2
            elif order.approval_stages == 'third_level':
                if order.state in ('draft', 'to_be_approved'):
                    order.approval_responsible = order.approver1
                elif order.state == 'leader_approval':
                    order.approval_responsible = order.approver2
                elif order.state == 'manager_approval':
                    order.approval_responsible = order.approver3

    def button_approval(self):
        # if not self.approval_stages == 'zero_level' and self.state == 'to_be_approved':
        if self.state == 'to_be_approved' or self.state == 'rfq_create' or self.state == 'tender_create':
            if self.approval_stages == 'first_level':
                if self.approver1.id == self._uid:
                    self.set_approval()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed For the First approval of %s Material Requisition.') %
                        (self.env.user.name, self.name))
            # else:
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'leader_approval':
            if self.approval_stages == 'second_level':
                if self.approver2.id == self._uid:
                    self.set_approval()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed For the Second approval of %s Material Requisition.') %
                        (self.env.user.name, self.name))
            # else:
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'manager_approval':
            if self.approval_stages == 'third_level':
                if self.approver3.id == self._uid:
                    self.set_approval()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed For the Third approval of %s Material Requisition.') %
                        (self.env.user.name, self.name))
                    #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'director_approval':
            if self.approval_stages == 'fourth_level':
                if self.approver4.id == self._uid:
                    self.set_approval()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed For the Fourth approval of %s Material Requisition.') %
                        (self.env.user.name, self.name))

    def button_leader_approval(self):
        if self.state == 'to_be_approved' or self.state == 'rfq_create' or self.state == 'tender_create':
            if self.approval_stages == 'first_level':
                self.button_approval()
            # elif self.approval_stages == 'second_level':
            #     self.button_approval()
            # elif self.approval_stages == 'third_level':
            #     self.button_approval()
            # elif self.approval_stages == 'fourth_level':
            #     self.button_approval()
            elif self.approval_stages != ('first_level', 'second_level', 'third_level', 'fourth_level'):
                if self.approver1.id == self._uid or self.approver2.id == self._uid \
                        or self.approver3.id == self._uid or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    if self.approver1.id == self._uid:
                        self.write({'state': 'leader_approval'})
                    elif self.approver2.id == self._uid:
                        self.state = 'manager_approval'
                    elif self.approver3.id == self._uid:
                        self.state = 'director_approval'
                    elif self.approver4.id == self._uid:
                        self.state = 'ceo_approval'
                    elif self.approver5.id == self._uid:
                        self.state = 'request_approved'
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'leader_approval':
            if self.approval_stages == 'second_level':
                self.button_approval()
            elif self.approval_stages != ('second_level', 'third_level', 'fourth_level'):
                if self.approver2.id == self._uid or self.approver3.id == self._uid \
                        or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    self.state = 'manager_approval'
                elif self.approver3.id == self._uid:
                    self.state = 'director_approval'
                elif self.approver4.id == self._uid:
                    self.state = 'ceo_approval'
                elif self.approver5.id == self._uid:
                    self.state = 'request_approved'
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'manager_approval':
            if self.approval_stages == 'third_level':
                self.button_approval()
            elif self.approval_stages != ('third_level', 'fourth_level'):
                if self.approver3.id == self._uid or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    self.state = 'director_approval'
                elif self.approver4.id == self._uid:
                    self.state = 'ceo_approval'
                elif self.approver5.id == self._uid:
                    self.state = 'request_approved'
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'director_approval':
            if self.approval_stages == 'fourth_level':
                self.button_approval()
            elif self.approval_stages != ('fourth_level'):
                if self.approver4.id == self._uid or self.approver5.id == self._uid:
                    if self.approver4.id:
                        self.state = 'ceo_approval'
                    elif self.approver5.id == self._uid:
                        self.state = 'request_approved'
                # elif self.approver5.id == self._uid:
                #     self.state = 'request_approved'
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'ceo_approval':
            if self.approver5.id == self._uid:
                self.state = 'request_approved'
            else:
                raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                (self.env.user.name, self.name))
        return True

    def button_reject(self):
        # if not self.approval_stages == 'zero_level' and self.state == 'to_be_approved':
        if self.state == 'to_be_approved' or self.state == 'rfq_create' or self.state == 'tender_create':
            if self.approval_stages == 'first_level':
                if self.approver1.id == self._uid:
                    self.indent_reject()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
            # else:
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'leader_approval':
            if self.approval_stages == 'second_level':
                if self.approver2.id == self._uid:
                    self.indent_reject()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                        (self.env.user.name, self.name))
            # else:
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'manager_approval':
            if self.approval_stages == 'third_level':
                if self.approver3.id == self._uid:
                    self.indent_reject()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                        (self.env.user.name, self.name))
                    #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'director_approval':
            if self.approval_stages == 'fourth_level':
                if self.approver4.id == self._uid:
                    self.indent_reject()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                        (self.env.user.name, self.name))

    def button_leader_reject(self):
        if self.state == 'to_be_approved' or self.state == 'rfq_create' or self.state == 'tender_create':
            if self.approval_stages == 'first_level':
                self.button_reject()
            # elif self.approval_stages == 'second_level':
            #     self.button_approval()
            # elif self.approval_stages == 'third_level':
            #     self.button_approval()
            # elif self.approval_stages == 'fourth_level':
            #     self.button_approval()
            elif self.approval_stages != ('first_level', 'second_level', 'third_level', 'fourth_level'):
                if self.approver1.id == self._uid or self.approver2.id == self._uid \
                        or self.approver3.id == self._uid or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    if self.approver1.id == self._uid:
                        self.indent_reject()
                    elif self.approver2.id == self._uid:
                        self.indent_reject()
                    elif self.approver3.id == self._uid:
                        self.indent_reject()
                    elif self.approver4.id == self._uid:
                        self.indent_reject()
                    elif self.approver5.id == self._uid:
                        self.indent_reject()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'leader_approval':
            if self.approval_stages == 'second_level':
                self.button_reject()
            elif self.approval_stages != ('second_level', 'third_level', 'fourth_level'):
                if self.approver2.id == self._uid or self.approver3.id == self._uid \
                        or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    self.indent_reject()
                elif self.approver3.id == self._uid:
                    self.indent_reject()
                elif self.approver4.id == self._uid:
                    self.indent_reject()
                elif self.approver5.id == self._uid:
                    self.indent_reject()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'manager_approval':
            if self.approval_stages == 'third_level':
                self.indent_reject()
            elif self.approval_stages != ('third_level', 'fourth_level'):
                if self.approver3.id == self._uid or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    self.indent_reject()
                elif self.approver4.id == self._uid:
                    self.indent_reject()
                elif self.approver5.id == self._uid:
                    self.indent_reject()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'director_approval':
            if self.approval_stages == 'fourth_level':
                self.button_reject()
            elif self.approval_stages != ('fourth_level'):
                if self.approver4.id == self._uid or self.approver5.id == self._uid:
                    self.indent_reject()
                elif self.approver5.id == self._uid:
                    self.indent_reject()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'ceo_approval':
            if self.approver5.id == self._uid:
                self.button_reject()
            else:
                raise UserError(_('Alert !, Mr.%s You Cannot allowed to Reject The %s Material Requisition.') %
                                (self.env.user.name, self.name))
        return True

    def button_cancels(self):
        # if not self.approval_stages == 'zero_level' and self.state == 'to_be_approved':
        if self.state == 'to_be_approved' or self.state == 'rfq_create' or self.state == 'tender_create':
            if self.approval_stages == 'first_level':
                if self.approver1.id == self._uid:
                    self.indent_cancel()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
            # else:
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'leader_approval':
            if self.approval_stages == 'second_level':
                if self.approver2.id == self._uid:
                    self.indent_cancel()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                        (self.env.user.name, self.name))
            # else:
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'manager_approval':
            if self.approval_stages == 'third_level':
                if self.approver3.id == self._uid:
                    self.indent_cancel()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                        (self.env.user.name, self.name))
                    #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'director_approval':
            if self.approval_stages == 'fourth_level':
                if self.approver4.id == self._uid:
                    self.indent_cancel()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                        (self.env.user.name, self.name))

    def button_leader_cancel(self):
        if self.state == 'to_be_approved' or self.state == 'rfq_create' or self.state == 'tender_create':
            if self.approval_stages == 'first_level':
                self.button_cancels()
            # elif self.approval_stages == 'second_level':
            #     self.button_approval()
            # elif self.approval_stages == 'third_level':
            #     self.button_approval()
            # elif self.approval_stages == 'fourth_level':
            #     self.button_approval()
            elif self.approval_stages != ('first_level', 'second_level', 'third_level', 'fourth_level'):
                if self.approver1.id == self._uid or self.approver2.id == self._uid \
                        or self.approver3.id == self._uid or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    if self.approver1.id == self._uid:
                        self.indent_cancel()
                    elif self.approver2.id == self._uid:
                        self.indent_cancel()
                    elif self.approver3.id == self._uid:
                        self.indent_cancel()
                    elif self.approver4.id == self._uid:
                        self.indent_cancel()
                    elif self.approver5.id == self._uid:
                        self.indent_cancel()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'leader_approval':
            if self.approval_stages == 'second_level':
                self.button_cancels()
            elif self.approval_stages != ('second_level', 'third_level', 'fourth_level'):
                if self.approver2.id == self._uid or self.approver3.id == self._uid \
                        or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    self.indent_cancel()
                elif self.approver3.id == self._uid:
                    self.indent_cancel()
                elif self.approver4.id == self._uid:
                    self.indent_cancel()
                elif self.approver5.id == self._uid:
                    self.indent_cancel()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'manager_approval':
            if self.approval_stages == 'third_level':
                self.indent_cancel()
            elif self.approval_stages != ('third_level', 'fourth_level'):
                if self.approver3.id == self._uid or self.approver4.id == self._uid or self.approver5.id == self._uid:
                    self.indent_cancel()
                elif self.approver4.id == self._uid:
                    self.indent_cancel()
                elif self.approver5.id == self._uid:
                    self.indent_cancel()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'director_approval':
            if self.approval_stages == 'fourth_level':
                self.button_cancels()
            elif self.approval_stages != ('fourth_level'):
                if self.approver4.id == self._uid or self.approver5.id == self._uid:
                    self.indent_cancel()
                elif self.approver5.id == self._uid:
                    self.indent_cancel()
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'ceo_approval':
            if self.approver5.id == self._uid:
                self.button_cancels()
            else:
                raise UserError(_('Alert !, Mr.%s You Cannot allowed to Cancel The %s Material Requisition.') %
                                (self.env.user.name, self.name))
        return True

    @api.model
    def create(self, vals):
        # vals['state'] = 'to_be_approved'
        if vals.get('automated_sequence'):
            sequence = self.env['ir.sequence'].create({
                'name': _('Sequence') + ' ' + vals['sequence_code'],
                'padding': 5,
                'prefix': vals['sequence_code'],
                'company_id': vals.get('company_id'),
            })
            vals['sequence_id'] = sequence.id
        po_type = self.env['material.approval.config'].browse(vals.get('type_of_purchase'))
        if po_type:
            vals['approval_stages'] = po_type.approval_levels
            if vals['approval_stages'] == 'first_level':
                vals['approver1'] = po_type.first_approval.id or False
            elif vals['approval_stages'] == 'second_level':
                vals['approver1'] = po_type.first_approval.id or False
                vals['approver2'] = po_type.second_approval.id or False
            elif vals['approval_stages'] == 'third_level':
                vals['approver1'] = po_type.first_approval.id or False
                vals['approver2'] = po_type.second_approval.id or False
                vals['approver3'] = po_type.third_approval.id or False
            elif vals['approval_stages'] == 'fourth_level':
                vals['approver1'] = po_type.first_approval.id or False
                vals['approver2'] = po_type.second_approval.id or False
                vals['approver3'] = po_type.third_approval.id or False
                vals['approver4'] = po_type.fourth_approval.id or False
            elif vals['approval_stages'] == 'fifth_level':
                vals['approver1'] = po_type.first_approval.id or False
                vals['approver2'] = po_type.second_approval.id or False
                vals['approver3'] = po_type.third_approval.id or False
                vals['approver4'] = po_type.fourth_approval.id or False
                vals['approver5'] = po_type.fifth_approval.id or False
        return super(MaterialRequisitionIndent, self).create(vals)

    def create_material_request(self):
        self.ensure_one()
        # If category uses sequence, set next sequence as name
        # (if not, set category name as default name).
        if self.automated_sequence:
            name = self.sequence_id.next_by_id()
        else:
            name = self.name
        return {
            "type": "ir.actions.act_window",
            "res_model": "material.requisition.indent",
            "views": [[False, "form"]],
            "context": {
                'form_view_initial_mode': 'edit',
                'default_name': name,
                # 'default_category_id': self.id,
                'default_responsible': self.env.user.id,
                'default_state': 'draft'
            },
        }

    def indent_reject(self):
        for indent in self:
            indent.write({
                'state': 'reject',
                'ribbon_state': 'rejected',
            })

    def indent_cancel(self):
        for indent in self:
            indent.write({
                'state': 'cancel',
                'ribbon_state': 'cancelled'
            })

    # def check_product_confirm(self):
    #     approved_product = self.env['material.requisition.product.lines']
    #     print("a------------------------------------------",approved_product)
    #     approved_product.write({
    #         'product_id': self.request_product_lines.product_id.id
    #     })
    #     print("=0-000000000000000000000000=--9=-09-0880990-",self.request_product_lines.product_id.id)
    #     print("=0-46464646=--9=-09-0880990-",approved_product.write({
    #         'product_id': self.request_product_lines.product_id.id
    #     }))
    #     print("approved product id=================================",approved_product.product_id.id)
    #     self.product_lines = approved_product

    # def check_product_confirm(self):
    #     print('11111111111')
    #     line_vals = []
    #     # product = self.env['material.requisition.indent']
    #     for new in self.request_product_lines:
    #         print('2222222222222')
    #         vals = {
    #             'product_id': new.product_id.id,
    #             # 'pre_approval_to': travel.distination,
    #             # 'pre_approval_travel_date': travel.travel_date,
    #         }
    #         self.product_lines = [(0, 0, vals)]
    #         print(vals)
    #     return line_vals

    def get_line_items(self):
        line_vals = []
        for line in self:
            if line.request_product_lines:
                for pro in line.request_product_lines:
                    if pro.short_close == True:
                        print('99999999999999999999999999999')
                        vals = [0, 0, {
                            'product_id': pro.original_product_id.id,
                            'product_uom_qty': pro.approved_product_uom_qty,
                            'product_uom': pro.approved_product_uom.id,
                            'product_available': pro.approved_product_available,
                            'product_category': pro.approved_product_category.id,
                            'product_type': pro.approved_product_type,
                        }]
                        line_vals.append(vals)
                    else:
                        vals = [0, 0, {
                            'product_id': pro.product_id.id,
                            'product_uom_qty': pro.product_uom_qty,
                            'product_uom': pro.product_uom.id,
                            'product_available': pro.product_available,
                            'product_category': pro.product_category.id,
                            'product_type': pro.product_type,
                        }]
                        line_vals.append(vals)
        return line_vals

    def check_product_confirm(self):
        requisition_created = False
        for line in self:
            if line.request_product_lines:
                print('99999999999999999999999999999')
                requisition_created = line.update({
                    # 'source': False,
                    # 'distination': False,
                    'product_lines': line.get_line_items(),
                })

    def indent_confirm(self):
        for indent in self:
            indent.check_product_confirm()
            if not indent.product_lines:
                raise ValidationError('Alert!!,Mr.%s. You cannot confirm an indent %s which has no line.' % (
                    indent.env.user.name, indent.name))
            else:
                if indent.product_lines:
                    indent.write({
                        'state': 'to_be_approved',
                        'verified_date': fields.Datetime.now()})

    def set_draft(self):
        for indent in self:
            state = indent.state = 'draft'
            self.write({
                'approver1_reject_reason': False,
                'approver2_reject_reason': False,
                'approver3_reject_reason': False,
                'approver4_reject_reason': False,
                'approver5_reject_reason': False,
                'approver1_cancel_reason': False,
                'approver2_cancel_reason': False,
                'approver3_cancel_reason': False,
                'approver4_cancel_reason': False,
                'approver5_cancel_reason': False,
                'product_lines': False,
            })
            return state

    def apply_approval(self):
        for indent in self:
            indent.button_leader_approval()

    def apply_rejection(self):
        for indent in self:
            indent.button_leader_reject()

    def apply_cancellation(self):
        for indent in self:
            indent.button_leader_cancel()

    def request_create_rfq(self):
        for indent in self:
            state = indent.state = 'request_rfq'
            return state

    # @api.multi
    def write(self, vals):
        res = super(MaterialRequisitionIndent, self).write(vals)
        po_type = self.env['material.approval.config'].browse(vals.get('type_of_purchase'))
        if po_type:
            self.approval_stages = po_type.approval_levels
            if self.approval_stages == 'first_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = False
                self.approver3 = False
                self.approver4 = False
                self.approver5 = False
            elif self.approval_stages == 'second_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = po_type.second_approval or False
                self.approver3 = False
                self.approver4 = False
                self.approver5 = False
            elif self.approval_stages == 'third_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = po_type.second_approval or False
                self.approver3 = po_type.third_approval or False
                self.approver4 = False
                self.approver5 = False
            elif self.approval_stages == 'fourth_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = po_type.second_approval or False
                self.approver3 = po_type.third_approval or False
                self.approver4 = po_type.fourth_approval or False
                self.approver5 = False
            elif self.approval_stages == 'fifth_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = po_type.second_approval or False
                self.approver3 = po_type.third_approval or False
                self.approver4 = po_type.fourth_approval or False
                self.approver5 = po_type.fifth_approval or False
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _default_approval_levels(self):
        app_id = self.env['purchase.order'].search(
            [('default_type', '=', True), ('approval_type', '=', 'material_request')], limit=1)
        return app_id.approval_levels

    type_of_purchase = fields.Many2one('purchase.order', string="Type Of Material", copy=False,
                                       domain="[('approval_type','=', 'material_request')]",
                                       tracking=True)
    approval_responsible = fields.Many2one('res.users', copy=False, store=True, compute="compute_approver",
                                           string="Approval Responsible", tracking=True)
    final_approver = fields.Many2one('res.users', string="Final Approver", tracking=True)
    approver1 = fields.Many2one('res.users', string="Approver 1", copy=False, tracking=True)
    approver2 = fields.Many2one('res.users', string="Approver 2", copy=False, tracking=True)
    approver3 = fields.Many2one('res.users', string="Approver 3", copy=False, tracking=True)
    approver4 = fields.Many2one('res.users', string="Approver 4", copy=False, tracking=True)
    approver5 = fields.Many2one('res.users', string="Approver 5", copy=False, tracking=True)
    approval_stages = fields.Selection([
        ('first_level', '1'),
        ('second_level', '2'),
        ('third_level', '3'),
        ('fourth_level', '4'),
        ('fifth_level', '5')], copy=False, string="No.of Approvals", default='first_level')
    approval_checked = fields.Boolean(string="Approval Checked", copy=False)
    is_request_approval = fields.Boolean(string="Request Approval", copy=False, default=False)
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('request_to_approve', 'Request To Approve'),
        ('to_be_approved', 'Waiting 1st Level Approval'),
        ('leader_approval', 'Waiting 2nd Level Approval'),
        ('manager_approval', 'Waiting 3rd Level Approval'),
        ('director_approval', 'Waiting 4th Level Approval'),
        ('ceo_approval', 'Waiting 5th Level Approval'),
        ('final_approval', 'Waiting Final Approval'),
        ('request_approved', 'Approved'),('reject', 'Rejected'),
    ], string='Status', readonly=True, index=True, copy=False, tracking=True)
    approval_type = fields.Selection([
        ('material_request', 'Material Request'),
    ], default='material_request', copy=False, string="Approvals Type", readonly=True, tracking=True)
    purachse_rfq_request = fields.Boolean(string="Material RFQ Request", copy=False)
    enable_rfq_to_po = fields.Boolean(string="Enable RFQ", copy=False)

    def button_product_confirm(self):
        for order in self:
            for pro in order.order_line:
                if pro.product_id and  pro.price_unit == 0.00:
                    raise UserError('Alert!!,  Mr.%s ,  '
                                    '\nPlease Enter the Unit Price For the Product %s .' % (
                                        self.env.user.name, pro.product_id.name))
            # order.action_wait()
            return super(PurchaseOrder, self).button_confirm()
        return True

    def confirm_purchase_order(self):
        for order in self:
            # if order.purachse_rfq_request == True:
            order.button_confirm()

    def final_approver_purchase(self):
        for po in self:
            material_requisition_sr = po.env['material.requisition.indent'].search([('name', '=', self.origin)])
            if po.final_approver:
                po.write({'state': 'final_approval',
                          })
                for material in material_requisition_sr:
                    material.write({'po_approved_by': self.env.user.name,
                                    })
                # po.set_approval()

    def final_approver_purchase_state(self):
        for rec in self:
            print("final approver===============================",rec.final_approver.id,rec._uid)
            if rec.final_approver.id == rec._uid:
                rec.set_approval()
            else:
                raise UserError(
                    _('Alert !, Mr.%s You are not allowed For the PO Final approval of %s.') %
                    (rec.env.user.name, rec.name))

    @api.onchange('type_of_purchase')
    def approval_details(self):
        if self.type_of_purchase:
            self.sudo().write({
                'approval_stages': self.type_of_purchase.approval_levels,
                # 'requester_department_id': self.request_raised_for.department_id.id,
                # 'requester_current_job_id': self.request_raised_for.job_id.id,
            })

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'request_approved']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def set_approval(self):
        self.write({'state': 'request_approved'})

    @api.depends('state')
    def compute_approver(self):
        for order in self:
            # if not order.approval_stages == 'zero_level':
            if order.approval_stages == 'first_level':
                order.approval_responsible = order.approver1
            elif order.approval_stages == 'second_level':
                if order.state in ('draft', 'to_be_approved'):
                    order.approval_responsible = order.approver1
                elif order.state == 'leader_approval':
                    order.approval_responsible = order.approver2
            elif order.approval_stages == 'third_level':
                if order.state in ('draft', 'to_be_approved'):
                    order.approval_responsible = order.approver1
                elif order.state == 'leader_approval':
                    order.approval_responsible = order.approver2
                elif order.state == 'manager_approval':
                    order.approval_responsible = order.approver3

    def button_approval(self):
        # if not self.approval_stages == 'zero_level' and self.state == 'to_be_approved':
        if self.state == 'to_be_approved':
            if self.approval_stages == 'first_level':
                if self.approver1.id == self._uid or self.final_approver.id == self._uid:
                    self.final_approver_purchase()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed For the First approval of %s Material Requisition.') %
                        (self.env.user.name, self.name))
            # else:
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'leader_approval':
            if self.approval_stages == 'second_level':
                if self.approver2.id == self._uid:
                    self.final_approver_purchase()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed For the Second approval of %s Material Requisition.') %
                        (self.env.user.name, self.name))
            # else:
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
            #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'manager_approval':
            if self.approval_stages == 'third_level':
                if self.approver3.id == self._uid:
                    self.final_approver_purchase()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed For the Third approval of %s Material Requisition.') %
                        (self.env.user.name, self.name))
                    #     raise UserError(_('You are not allowed to approve this Purchase Order, First Level Approval is Pending'))
        if self.state == 'director_approval':
            if self.approval_stages == 'fourth_level':
                if self.approver4.id == self._uid:
                    self.final_approver_purchase()
                else:
                    raise UserError(
                        _('Alert !, Mr.%s You Cannot allowed For the Fourth approval of %s Material Requisition.') %
                        (self.env.user.name, self.name))

    def button_leader_approval(self):
        if self.state == 'to_be_approved':
            if self.approval_stages == 'first_level':
                self.button_approval()
            # elif self.approval_stages == 'second_level':
            #     self.button_approval()
            # elif self.approval_stages == 'third_level':
            #     self.button_approval()
            # elif self.approval_stages == 'fourth_level':
            #     self.button_approval()
            elif self.approval_stages != ('first_level', 'second_level', 'third_level', 'fourth_level'):
                if self.approver1.id == self._uid:
                    self.write({'state': 'leader_approval'})
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'leader_approval':
            if self.approval_stages == 'second_level':
                self.button_approval()
            elif self.approval_stages != ('second_level', 'third_level', 'fourth_level'):
                if self.approver2.id == self._uid:
                    self.state = 'manager_approval'
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'manager_approval':
            if self.approval_stages == 'third_level':
                self.button_approval()
            elif self.approval_stages != ('third_level', 'fourth_level'):
                if self.approver3.id == self._uid:
                    self.state = 'director_approval'
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'director_approval':
            if self.approval_stages == 'fourth_level':
                self.button_approval()
            elif self.approval_stages != ('fourth_level'):
                if self.approver4.id == self._uid:
                    self.state = 'ceo_approval'
                else:
                    raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                    (self.env.user.name, self.name))
        elif self.state == 'ceo_approval':
            if self.approver5.id == self._uid:
                self.state = 'final_approval'
            else:
                raise UserError(_('Alert !, Mr.%s You Cannot allowed to approve this %s Material Requisition.') %
                                (self.env.user.name, self.name))
        return True

    # def action_wait(self):
    #     print('1111111111111111111111')
    #     for purchase in self:
    #         print('1111111111111111111111')
    #         quo = purchase.name
    #         if purchase.state == 'purchase':
    #             print('1111111111111111111111')
    #             purchase.write({
    #                 'origin': quo,
    #                 'name': self.env['ir.sequence'].next_by_code('purchase.order') or 'New'
    #             })
    #     return True

    @api.model
    def create(self, vals):
        # if vals.get('enable_rfq_to_po') == True:
        #     print("RFQ Enable is working================================")
            # if vals.get('state') == 'draft' or 'sent':
            #     vals['name'] = self.env['ir.sequence'].next_by_code(
            #         'purchase.rfq') or '/'
        po_type = self.env['purchase.order'].browse(vals.get('type_of_purchase'))
        if po_type:
            vals['approval_stages'] = po_type.approval_levels
            if vals['approval_stages'] == 'first_level':
                vals['approver1'] = po_type.first_approval.id or False
            elif vals['approval_stages'] == 'second_level':
                vals['approver1'] = po_type.first_approval.id or False
                vals['approver2'] = po_type.second_approval.id or False
            elif vals['approval_stages'] == 'third_level':
                vals['approver1'] = po_type.first_approval.id or False
                vals['approver2'] = po_type.second_approval.id or False
                vals['approver3'] = po_type.third_approval.id or False
            elif vals['approval_stages'] == 'fourth_level':
                vals['approver1'] = po_type.first_approval.id or False
                vals['approver2'] = po_type.second_approval.id or False
                vals['approver3'] = po_type.third_approval.id or False
                vals['approver4'] = po_type.fourth_approval.id or False
            elif vals['approval_stages'] == 'fifth_level':
                vals['approver1'] = po_type.first_approval.id or False
                vals['approver2'] = po_type.second_approval.id or False
                vals['approver3'] = po_type.third_approval.id or False
                vals['approver4'] = po_type.fourth_approval.id or False
                vals['approver5'] = po_type.fifth_approval.id or False
        # else:
        #     raise ValidationError('Alert!. Without RFQ, you cannot create Direct PO. Please Create RFQ to proceed further.')
        return super(PurchaseOrder, self).create(vals)

    def indent_reject(self):
        for indent in self:
            indent.write({
                'state': 'reject', })

    def indent_cancel(self):
        for indent in self:
            indent.write({
                'state': 'cancel',})

    def indent_confirm(self):
        for indent in self:
            for pro in indent.order_line:
                if pro.product_id and pro.price_unit == 0.00:
                    raise UserError('Alert!!,  Mr.%s ,  \nPlease Enter the Unit Price For the Product %s .' % (
                        self.env.user.name, pro.product_id.name))
                    # raise Warning('Alert!!, You cannot confirm an indent %s which has no order line.' % (indent.name))
            if not indent.order_line:
                raise Warning('Alert!!, You cannot confirm an indent %s which has no order line.' % (indent.name))
            else:
                if indent.order_line:
                    self.write({
                        'state': 'to_be_approved'
                    })

    def set_draft(self):
        for indent in self:
            state = indent.state = 'draft'
            self.write({
                'approver1_reject_reason': False,
                'approver2_reject_reason': False,
                'approver3_reject_reason': False,
                'approver4_reject_reason': False,
                'approver5_reject_reason': False,
                'approver1_cancel_reason': False,
                'approver2_cancel_reason': False,
                'approver3_cancel_reason': False,
                'approver4_cancel_reason': False,
                'approver5_cancel_reason': False,
            })
            return state

    def request_create_rfq(self):
        for indent in self:
            state = indent.state = 'request_rfq'
            return state

    # @api.multi
    def write(self, vals):
        # if vals.get('enable_rfq_to_po') == True:
        res = super(PurchaseOrder, self).write(vals)
        if vals.get('state') == 'draft' or 'sent':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'purchase.rfq') or '/'
        po_type = self.env['purchase.order'].browse(vals.get('type_of_purchase'))
        if po_type:
            self.approval_stages = po_type.approval_levels
            if self.approval_stages == 'first_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = False
                self.approver3 = False
                self.approver4 = False
                self.approver5 = False
            elif self.approval_stages == 'second_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = po_type.second_approval or False
                self.approver3 = False
                self.approver4 = False
                self.approver5 = False
            elif self.approval_stages == 'third_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = po_type.second_approval or False
                self.approver3 = po_type.third_approval or False
                self.approver4 = False
                self.approver5 = False
            elif self.approval_stages == 'fourth_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = po_type.second_approval or False
                self.approver3 = po_type.third_approval or False
                self.approver4 = po_type.fourth_approval or False
                self.approver5 = False
            elif self.approval_stages == 'fifth_level':
                self.approver1 = po_type.first_approval or False
                self.approver2 = po_type.second_approval or False
                self.approver3 = po_type.third_approval or False
                self.approver4 = po_type.fourth_approval or False
                self.approver5 = po_type.fifth_approval or False
        # else:
        #     raise ValidationError('Alert!. Without RFQ, you cannot create Direct PO. Please Create RFQ to proceed further.')
        return res


class ShPurchaseAgreement(models.Model):
    _inherit = 'purchase.agreement'

    indent_id = fields.Many2one('material.requisition.indent', 'Indent')


# class PurchaseApprovalConfig(models.Model):
#     _name = 'purchase.approval.config'
#     _description = 'Purchase Approval Configuration'
#     # _rec_name = 'type_of_material'
#     _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
#
#     def _default_seq_id(self):
#         return self.env['ir.sequence'].search([('code', '=', 'purchase.order')], limit=1).id
#
#     def _default_journal(self):
#         return self.env['account.journal'].search([('type', '=', 'sale')], limit=1).id
#
#     @api.onchange('approval_levels')
#     def onchange_approvals(self):
#         if self.approval_levels:
#             if self.approval_levels == 'first_level':
#                 self.first_approval = False
#                 self.second_approval = False
#                 self.third_approval = False
#                 self.fourth_approval = False
#                 self.fifth_approval = False
#             elif self.approval_levels == 'second_level':
#                 self.first_approval = False
#                 self.second_approval = False
#                 self.third_approval = False
#                 self.fourth_approval = False
#                 self.fifth_approval = False
#             elif self.approval_levels == 'third_level':
#                 self.first_approval = False
#                 self.second_approval = False
#                 self.third_approval = False
#                 self.fourth_approval = False
#                 self.fifth_approval = False
#             elif self.approval_levels == 'fourth_level':
#                 self.first_approval = False
#                 self.second_approval = False
#                 self.third_approval = False
#                 self.fourth_approval = False
#                 self.fifth_approval = False
#             elif self.approval_levels == 'fifth_level':
#                 self.first_approval = False
#                 self.second_approval = False
#                 self.third_approval = False
#                 self.fourth_approval = False
#                 self.fifth_approval = False
#
#     color = fields.Integer('Color')
#     approval_type = fields.Selection([
#         ('purchase_request', 'Purchase Request'),
#     ], default='purchase_request', copy=False, string="Approvals Type", readonly=True, tracking=True)
#     type_of_purchase = fields.Char(string="Purchase Approval Type", tracking=True, copy=False)
#     approval_levels = fields.Selection([
#         ('first_level', '1'),
#         ('second_level', '2'),
#         ('third_level', '3'),
#         ('fourth_level', '4'),
#         ('fifth_level', '5')], default='first_level', copy=False, string="No.of Approvals", tracking=True)
#     first_approval = fields.Many2one('res.users', string="First Approval", tracking=True)
#     second_approval = fields.Many2one('res.users', string="Second Approval", tracking=True)
#     third_approval = fields.Many2one('res.users', string="Third Approval", tracking=True)
#     fourth_approval = fields.Many2one('res.users', string="Fourth Approval", tracking=True)
#     fifth_approval = fields.Many2one('res.users', string="Fifth Approval", tracking=True)
#     first_approval_amount_from = fields.Float(string="", tracking=True)
#     first_approval_amount_to = fields.Float(string="", tracking=True)
#     second_approval_amount_from = fields.Float(string="", tracking=True)
#     second_approval_amount_to = fields.Float(string="", tracking=True)
#     third_approval_amount_from = fields.Float(string="", tracking=True)
#     third_approval_amount_to = fields.Float(string="", tracking=True)
#     fourth_approval_amount_from = fields.Float(string="", tracking=True)
#     fourth_approval_amount_to = fields.Float(string="", tracking=True)
#     fifth_approval_amount_from = fields.Float(string="", tracking=True)
#     fifth_approval_amount_to = fields.Float(string="", tracking=True)
#     material_limit = fields.Float(string="Material Value", tracking=True)
#     product_categ = fields.Many2many('product.category', string="Product Categories", tracking=True)
#     default_type = fields.Boolean(string="Default")
#     lc_applicable = fields.Boolean(string="LC Applicable")
#     seq_id = fields.Many2one('ir.sequence', string="Sequence", default=_default_seq_id)
#     purchase_journal_id = fields.Many2one('account.journal', string="Material Journal",
#                                           domain=['|', ('type', '=', 'purchase'), ('company_id', '=', 'company_id')])
#
#     # count_quotations = fields.Integer(compute='_compute_purchase_count', default=0)
#     # count_waiting_for_approval = fields.Integer(compute='_compute_purchase_count', default=0)
#     # count_confirmed = fields.Integer(compute='_compute_purchase_count', default=0)
#     # count_total_po = fields.Integer(compute='_compute_purchase_count', default=0)
#     purchase_cancel_users = fields.Many2many('res.users', 'purchase_cancel_user_rel', string='Approved Purchase Cancel')
#     company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
#     material_types = fields.Selection([
#         ('local', 'Local'),
#         ('import', 'Import'),
#         ('general', 'General'),
#         ('asset', 'Asset'),
#     ], 'Material Types', tracking=True)
#
#     def name_get(self):
#         result = []
#         for bank in self:
#             name = bank.type_of_purchase
#             result.append((bank.id, name))
#         return result
#
#     # @api.onchange('type_of_purchase')
#     # def onchange_stages(self):
#     #     if self.type_of_purchase:
#     #         app_id = self.env['material.approval.config'].search([('id', '=', self.type_of_purchase.id)])
#     #         self.approval_stages = app_id.approval_levels
#
#     @api.model
#     def create(self, vals):
#         res = super(PurchaseApprovalConfig, self).create(vals)
#         if vals.get('approval_levels') in ('first_level', 'second_level', 'third_level'):
#             if vals.get('first_approval') == False:
#                 raise UserError(_('Kindly set the First Approval.'))
#         if vals.get('approval_levels') in ('second_level', 'third_level'):
#             if vals.get('second_approval') == False:
#                 raise UserError(_('Kindly set the Second Approval.'))
#         if vals.get('approval_levels') == 'third_level':
#             if vals.get('third_approval') == False:
#                 raise UserError(_('Kindly set the Third Approval.'))
#         if vals.get('approval_levels') == 'fourth_level':
#             if vals.get('fourth_approval') == False:
#                 raise UserError(_('Kindly set the Fourth Approval.'))
#         if vals.get('approval_levels') == 'fifth_level':
#             if vals.get('fifth_approval') == False:
#                 raise UserError(_('Kindly set the Fifth Approval.'))
#         return res
#
#     def write(self, vals):
#         res = super(PurchaseApprovalConfig, self).write(vals)
#         if vals.get('approval_levels') in ('first_level', 'second_level', 'third_level') or \
#                 self.approval_levels in ('first_level', 'second_level', 'third_level'):
#             if vals.get('first_approval') == False or self.first_approval == False:
#                 raise UserError(_('Kindly set the First Approval.'))
#         if vals.get('approval_levels') in ('second_level', 'third_level') or \
#                 self.approval_levels in ('second_level', 'third_level'):
#             if vals.get('second_approval') == False or self.second_approval == False:
#                 raise UserError(_('Kindly set the Second Approval.'))
#         if vals.get('approval_levels') == 'third_level' or \
#                 self.approval_levels == 'third_level':
#             if vals.get('third_approval') == False or self.third_approval == False:
#                 raise UserError(_('Kindly set the Third Approval.'))
#         if vals.get('approval_levels') == 'fourth_level' or \
#                 self.approval_levels == 'fourth_level':
#             if vals.get('fourth_approval') == False or self.fourth_approval == False:
#                 raise UserError(_('Kindly set the Fourth Approval.'))
#         if vals.get('approval_levels') == 'fifth_level' or \
#                 self.approval_levels == 'fifth_level':
#             if vals.get('fifth_approval') == False or self.fifth_approval == False:
#                 raise UserError(_('Kindly set the Fifth Approval.'))
#         return res
