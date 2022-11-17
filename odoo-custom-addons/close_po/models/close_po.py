# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.exceptions import UserError
from odoo import api, fields, models, _
import pdb
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from datetime import datetime, timedelta,date

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

  
    open_close_po = fields.Selection([
        ('open_po', 'Open PO'),
        ('close_po', 'Close PO')],string="PO Status",store=True,default='open_po')
    po_entry_done = fields.Boolean(compute="check_po_close_check",store=True, copy=False)

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
        ('request_approved', 'Approved'),
    ], string='Status', readonly=True, index=True, copy=False, tracking=True)
    approval_type = fields.Selection([
        ('material_request', 'Material Request'),
    ], default='material_request', copy=False, string="Approvals Type", readonly=True, tracking=True)
    purachse_rfq_request = fields.Boolean(string="Material RFQ Request", copy=False)

    def confirm_purchase_order(self):
        for order in self:
            if order.purachse_rfq_request == True:
                self.button_confirm()

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
            rec.set_approval()

    @api.onchange('type_of_purchase')
    def approval_details(self):
        if self.type_of_purchase:
            self.sudo().write({
                'approval_stages': self.type_of_purchase.approval_levels,
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
                if self.approver1.id == self._uid:
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

    @api.model
    def create(self, vals):
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
        return super(PurchaseOrder, self).create(vals)

    def indent_reject(self):
        for indent in self:
            self.indent({
                'state': 'reject', })

    def indent_cancel(self):
        for indent in self:
            self.indent({
                'state': 'cancel', })

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
            return state

    def request_create_rfq(self):
        for indent in self:
            state = indent.state = 'request_rfq'
            return state

    # @api.multi
    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
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
        return res

    # def get_button(self):
    #     for mi in self:
    #         print("Yes im in ====================================")
    #         mr_id =  mi.env['material.requisition.indent']
    #         print("000000000000000000000000000000000mr id ",mr_id)
    #         mr_id.button_leader_approval()

    def close_po(self):
        for line in self.order_line:
            if line.po_done == False:
                line.write({'po_done':True})

    @api.depends('order_line.po_done')
    def check_po_close_check(self):
        for rec in self:
            if rec.order_line:
                if any(rec.order_line.filtered(lambda e:e.po_done == False)):
                    rec.po_entry_done = False
                    rec.open_close_po = 'open_po'
                else:
                    rec.po_entry_done = True
                    rec.open_close_po = 'close_po'
            else:
                rec.po_entry_done = None

class ClosePoLine(models.Model):
    _inherit = 'purchase.order.line'

    po_done = fields.Boolean('PO Done',store=True,compute='get_open_close',inverse='get_inverse_po')

    @api.depends('qty_received')
    def get_open_close(self):
        for line in self:
            if line.qty_received:
                if line.qty_received >= line.product_uom_qty:
                    line.update({'po_done':True,})
                else:
                    line.update({'po_done':False,})
            else:
                line.update({'po_done':False,})

    def get_inverse_po(self):
        pass
