# -*- coding: utf-8 -*-


from datetime import date
from odoo import models, fields, api, tools, _
import time
from datetime import timedelta, datetime
import datetime
from odoo.tools import email_split, float_is_zero
from odoo.fields import Date
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import Warning
from odoo import api, SUPERUSER_ID
from odoo.addons.bus.models.bus import TIMEOUT
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from datetime import datetime, timedelta, date


class MaterialRequisitionIndent(models.Model):
    _name = 'material.requisition.indent'
    _description = 'Indent'
    _inherit = ['mail.thread']
    _order = "verified_date desc"

    def _get_stock_type_ids(self):
        data = self.env['stock.picking.type'].search([])
        for line in data:
            if line.code == 'outgoing':
                return line

    def _default_employee(self):
        emp_ids = self.sudo().env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    name = fields.Char(string='Indent Reference', size=256, tracking=True, required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('/'),
                       help='A unique sequence number for the Indent')
    responsible = fields.Many2one('hr.employee', string='Request Raised By', default=_default_employee, readonly=True,
                                  help="Responsible person for the Material Request")
    verified_date = fields.Datetime('Verified Date', readonly=True, tracking=True)
    indent_date = fields.Datetime('Indent Date', required=True, readonly=True,
                                  default=lambda self: fields.Datetime.now(),
                                  states={'draft': [('readonly', False)]})
    required_date = fields.Datetime('Required Date', required=True, readonly=True,
                                    states={'draft': [('readonly', False)]})
    indentor_id = fields.Many2one('res.users', 'Indentor', tracking=True, states={'draft': [('readonly', False)]})
    department_id = fields.Many2one(string='Department', related='responsible.department_id', required=True,
                                    readonly=True, tracking=True)
    current_job_id = fields.Many2one(related='responsible.job_id', string="Job Position", required=True)
    current_reporting_manager = fields.Many2one(related='responsible.parent_id', string="Reporting Manager",
                                                required=True)
    request_raised_for = fields.Many2one('hr.employee', string='Request Raised For',
                                         help="Request person for the Material")
    requester_department_id = fields.Many2one('hr.department', string='Department', required=True, tracking=True)
    requester_current_job_id = fields.Many2one('hr.job', string="Job Position", required=True)
    requester_current_reporting_manager = fields.Many2one('hr.employee', string="Reporting Manager",
                                                          required=True)
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    purpose = fields.Char('Purpose', required=True, readonly=True, tracking=True,
                          states={'draft': [('readonly', False)]})
    location_id = fields.Many2one('stock.location', 'Destination Location', required=True, readonly=True,
                                  tracking=True, states={'draft': [('readonly', False)]})
    analytic_account_id = fields.Many2one('account.analytic.account', 'Project', ondelete="cascade", readonly=True,
                                          tracking=True, states={'draft': [('readonly', False)]})
    requirement = fields.Selection([('1', 'Ordinary'), ('2', 'Urgent')], 'Requirement', readonly=True, required=True,
                                   tracking=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([('stock', 'Stock')], 'Type', default='stock', required=True,
                            tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    product_lines = fields.One2many('material.requisition.product.lines', 'indent_id', 'Products', readonly=True,
                                    states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]})
    request_product_lines = fields.One2many('material.requisition.request.product.lines', 'indent_id', 'Products',
                                            readonly=True,
                                            states={'draft': [('readonly', False)],
                                                    'waiting_approval': [('readonly', False)]})
    picking_id = fields.Many2one('stock.picking', 'Picking')
    in_picking_id = fields.Many2one('stock.picking', 'Picking')
    description = fields.Text('Additional Information', readonly=True, states={'draft': [('readonly', False)]})
    # company_id = fields.Many2one('res.company', 'Company', readonly=True, states={'draft': [('readonly', False)]})
    active = fields.Boolean('Active', default=True)
    item_for = fields.Selection([('store', 'Store'), ('capital', 'Capital')], 'Material Requisition for', readonly=True,
                                states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('cancel', 'Cancelled'),
                              ('waiting_approval', 'Waiting for Approval'),
                              ('request_approved', 'Approved'),
                              ('inprogress', 'In Progress'), ('received', 'Delivered'),
                              ('partially_received', 'Parially Delivered'),
                              ('reject', 'Rejected')], 'State', default="draft", readonly=True, tracking=True)
    ribbon_state = fields.Selection(
        [('not_available', 'Stock Not Available'), ('mr_stock_available', 'Stock Available'),
         ('store_to_verify', 'Store to Verify'),
         ('store_verified', 'Store Verified'),
         ('partial_stock', 'Partially Stock Available'),
         ('partial_stock_delivered', 'Partially Stock Delivery Created'),
         ('stock_delivered', 'Stock Delivery Created'),
         ('delivery_done', 'Delivery Completed'),
         ('partial_delivery_done', 'Partial Delivery Completed'),
         ('rfq_raise', 'RFQ/PO Raised'),
         ('tender_raise', 'Tender Raised'),
         ('grn_completed', 'GRN Completed'),
         ], 'Ribbon State',
        default="store_to_verify", readonly=True, tracking=True)
    approver_id = fields.Many2one('res.users', 'Authority', readonly=True, tracking=True,
                                  states={'draft': [('readonly', False)]}, help="who have approve or reject indent.")
    equipment_id = fields.Many2one('indent.equipment', 'Equipment', readonly=True,
                                   states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    # equipment_section_id = fields.Many2one('indent.equipment.section', 'Section', readonly=True,
    #                                        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', help="default warehose where inward will be taken",
                                   readonly=True,
                                   states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    move_type = fields.Selection([('direct', 'Partial'), ('one', 'All at once')], 'Receive Method', tracking=True,
                                 readonly=True,
                                 states={'draft': [('readonly', False)], 'cancel': [('readonly', True)]},
                                 help="It specifies goods to be deliver partially or all at once")
    manager_id = fields.Many2one('res.users', string='Manager', default=lambda self: self.env.user)
    approved_by = fields.Many2one('res.users', string='Approved By')
    picking_count = fields.Integer(string="Count", copy=False)
    invoice_picking_id = fields.Many2one('stock.picking', string="Picking Id", copy=False)
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type',
                                      default=_get_stock_type_ids,
                                      help="This will determine picking type of incoming shipment")
    material_requisition_notice_period = fields.Integer(compute='_compute_material_requisition_notice_period',
                                                        string='/ Days',
                                                        default=0)
    material_requisition_backorder_count = fields.Integer(compute='_compute_material_requisition_backorder',
                                                          string='Back Order',
                                                          default=0)
    purchase_order_count = fields.Integer(compute='_compute_material_requisition_po', string='Purchase Order',
                                          default=0)
    rfq_total = fields.Integer('My RFQ', compute='compute_order')
    tender_total = fields.Integer('My Tender', compute='compute_order')
    rfq_order_ids = fields.One2many('purchase.order', 'indent_id')
    stock_available = fields.Boolean('Stock')
    partial_stock_available = fields.Boolean('Partial Stock')
    enable_ribbon = fields.Boolean('Ribbon Active')
    stock_transferred = fields.Boolean('Stock Transferred')
    partial_stock_transferred = fields.Boolean('Partial Stock Transferred')
    partial_delivery = fields.Boolean('Partial Delivery')
    store_approval = fields.Boolean('Store Approval')
    store_request = fields.Boolean('Store Request')
    mr_reject = fields.Boolean('MR Reject')
    rfq_raised = fields.Boolean('RFQ Raised', default=False)
    tender_raised = fields.Boolean('Tender Raised', default=False)
    my_tender_report_count = fields.Integer(compute='_compute_my_tender_report', string='PO Tender',
                                            default=0)
    last_poll = fields.Datetime('Last Poll', default=lambda self: fields.Datetime.now())
    issued_date = fields.Datetime('Issued Date')
    inward_date = fields.Datetime('Inward Date')
    po_approved_by = fields.Char('PO Approved By')
    store_incharge = fields.Char('Store In-charge')
    approver1_reject_reason = fields.Text('1st Approver Reject Remarks')
    approver2_reject_reason = fields.Text('2nd Approver Reject Remarks')
    approver3_reject_reason = fields.Text('3rd Approver Reject Remarks')
    approver4_reject_reason = fields.Text('4th Approver Reject Remarks')
    approver5_reject_reason = fields.Text('5th Approver Reject Remarks')
    approver1_cancel_reason = fields.Text('1st Approver Cancel Remarks')
    approver2_cancel_reason = fields.Text('2nd Approver Cancel Remarks')
    approver3_cancel_reason = fields.Text('3rd Approver Cancel Remarks')
    approver4_cancel_reason = fields.Text('4th Approver Cancel Remarks')
    approver5_cancel_reason = fields.Text('5th Approver Cancel Remarks')
    approver1_approve_reason = fields.Text('1st Approver Approval Remarks')
    approver2_approve_reason = fields.Text('2nd Approver Approval Remarks')
    approver3_approve_reason = fields.Text('3rd Approver Approval Remarks')
    approver4_approve_reason = fields.Text('4th Approver Approval Remarks')
    approver5_approve_reason = fields.Text('5th Approver Approval Remarks')
    store_verified_remark = fields.Text('Store Verified Remarks')
    current_date = fields.Datetime(string='Current DateTime' )
    add_hour_date = fields.Datetime(string='One Hour')
    cron_Boolean = fields.Boolean(string='Boolean')
    grn_status = fields.Boolean('GRN Status', default=False)
    @api.onchange('stock_available')
    def get_ribbon_state(self):
        if self.ribbon_state:
            self.update({'ribbon_state': 'mr_stock_available'})

    def material_requisition_approve_remarks(self):
        view_id = self.env['material.requisition.approve.remarks']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Requisition Approval Remarks',
            'res_model': 'material.requisition.approve.remarks',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('material_requisition.material_requisition_approve_remarks_wizard', False).id,
            'target': 'new',
        }

    def material_requisition_reject_remarks(self):
        view_id = self.env['material.requisition.reject.remarks']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Requisition Reject Remarks',
            'res_model': 'material.requisition.reject.remarks',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('material_requisition.material_requisition_reject_remarks_wizard', False).id,
            'target': 'new',
        }

    def material_requisition_cancel_remarks(self):
        view_id = self.env['material.requisition.cancel.remarks']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Requisition Cancel Remarks',
            'res_model': 'material.requisition.cancel.remarks',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('material_requisition.material_requisition_cancel_remarks_wizard', False).id,
            'target': 'new',
        }

    @api.onchange('required_date')
    def get_required_date(self):
        if self.required_date:
            if self.required_date <= self.indent_date:
                raise ValidationError(("Alert!,Mr. %s. \n Required Date should be Graterthan than Current Date.") \
                                      % (self.env.user.name))

    def _compute_material_requisition_backorder(self):
        self.material_requisition_backorder_count = self.env['stock.picking'].sudo().search_count(
            [('origin', '=', self.name), ('backorder_id', '!=', False)])
        stock = self.env['stock.picking']
        # if stock.backorder_id and stock.state == 'assigned':
        #     print("yes backorder condition is calling============================",
        #           stock.backorder_id == True and stock.state == 'assigned')
        #     self.write(
        #         {'state': 'partially_received', 'partial_delivery': True, 'ribbon_state': 'partial_stock_delivered'})

    def _compute_material_requisition_po(self):
        self.purchase_order_count = self.env['purchase.order'].sudo().search_count(
            [('origin', '=', self.name), ('state', '=', 'purchase')])

    def _compute_my_tender_report(self):
        self.my_tender_report_count = self.env['purchase.agreement'].sudo().search_count(
            [('sh_source', '=', self.name)])
        if self.my_tender_report_count and self.stock_available == False:
            self.write({'tender_raised': True, 'ribbon_state': 'tender_raise'})

    def my_tender_report(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('sh_po_tender_management.sh_purchase_agreement_form_view')
        tree_view = self.sudo().env.ref('sh_po_tender_management.sh_purchase_agreement_tree_view')
        return {
            'name': _('My Purchase Tender Report'),
            'res_model': 'purchase.agreement',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('sh_source', '=', self.name)],
        }

    def material_requisition_back_order(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('stock.view_picking_form')
        tree_view = self.sudo().env.ref('stock.vpicktree')
        return {
            'name': _('My Back Order'),
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('origin', '=', self.name), ('backorder_id', '!=', False)],
        }

    ## compute method for count total number of purchase order
    def compute_order(self):
        count = 0
        for employee in self:
            invoices = self.env['purchase.order']
            for record in employee.rfq_order_ids:
                if record.state == 'request_to_approve':
                    count += 1
            employee.rfq_total = count
            if employee.rfq_total:
                employee.write({'rfq_raised': True, 'ribbon_state': 'rfq_raise'})

    ### to display purchase order in oe-button
    def create_RFQ_lines(self):
        return {
            'name': _('Purchase Orders'),
            'domain': [('id', 'in', [x.id for x in self.rfq_order_ids]), ('state', '=', 'request_to_approve')],
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'view_id': False,
            'views': [(self.env.ref('purchase.purchase_order_kpis_tree').id, 'tree'),
                      (self.env.ref('purchase.purchase_order_form').id, 'form')],
            'type': 'ir.actions.act_window'
        }

    @api.onchange('request_raised_for')
    def requester_details(self):
        if self.request_raised_for:
            self.sudo().write({
                'requester_current_reporting_manager': self.request_raised_for.parent_id.id,
                'requester_department_id': self.request_raised_for.department_id.id,
                'requester_current_job_id': self.request_raised_for.job_id.id,
            })

    def create_shipped(self):
        product_onhand = []
        req_product = []
        product_type = []
        res = []
        zero_count = 0.00
        non_zero_count = 0.00
        zero_non_zero_count = 0.00
        req_qun_count = 0.00
        for num in self:
            for l in num.product_lines:
                if l.product_type == 'product':
                    product_onhand.append(l.product_available)
                    req_product.append(l.product_uom_qty)
                    product_type.append(l.product_type)
                    print(req_product)
                    print('Product Type', product_type)
            if l.product_type == 'product':
                for i in product_onhand:
                    if i not in res:
                        res.append(i)
                for product in res:
                    print(product)
                    if product == 0.00:
                        zero_count += 1
                        print('Zero Count', zero_count)
                    if product > 0.00:
                        non_zero_count += 1
                        print('Non Zero Count', non_zero_count)
                for qty in req_product:
                    if qty > product:
                        req_qun_count += 1
                        print("445444444444", )
                    if non_zero_count and req_qun_count or zero_count and non_zero_count:
                        zero_non_zero_count += 1
                        print('Zero Non Zero Count', zero_non_zero_count)
                        num.update({
                            'partial_stock_available': True,
                            'ribbon_state': 'partial_stock',
                            'stock_available': False,
                            'tender_raised': False,
                            'rfq_raised': False,
                        })
                    if non_zero_count and zero_non_zero_count == 0.00 or product == qty:
                        if self.stock_available == False:
                            print('qqqqqqqqqqqqqqqqqqqqqqqq')
                            num.update({
                                'partial_stock_available': False,
                                'stock_available': True,
                                'ribbon_state': 'mr_stock_available',
                                'tender_raised': False,
                                'rfq_raised': False,
                            })
                        if self.stock_available == True:
                            print('wwwwwwwwwwwwwwwwwwwwwwww')
                            num.update({
                                'tender_raised': False,
                            })
            else:
                self.write({'stock_available': True,
                            'ribbon_state': 'mr_stock_available'})
            self.write({'enable_ribbon': True})
            return True

    def open_rfq_form(self):
        action = self.env.ref('material_requisition.open_create_rfq_wizard_action')
        result = action.read()[0]
        order_line = []
        for line in self.product_lines:
            order_line.append({
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'product_uom_id': line.product_uom.id,
                'on_hand_qty': line.product_available,
            })
            result['context'] = {
                'default_material_requisition_ref': self.name,
                'default_order_lines': order_line,
            }
        return result

    def button_purchase_order(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('purchase.purchase_order_form')
        tree_view = self.sudo().env.ref('purchase.purchase_order_view_tree')
        return {
            'name': _('Purchase Order'),
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('origin', '=', self.name), ('state', '=', 'purchase')],
        }

    def set_approval(self):
        self.write({'state': 'request_approved', 'approved_by': self._uid})

    def set_complete(self):
        self.write({'stock_transferred': True})
        material_picking = self.env['stock.picking'].search([('origin', '=', self.name)])
        if material_picking.state == 'done':
            self.write({'state': 'done'})
            material_picking.create_qty_material()
        else:
            raise UserError('Alert!,Mr. %s , \n You cannot complete The %s , Please Complete the Shipment %s.'
                            % (self.env.user.name, self.name, material_picking.name))

    def action_stock_move(self):
        if not self.picking_type_id:
            raise UserError(_(
                " Please select a picking type"))
        for order in self:
            if not self.invoice_picking_id:
                pick = {}
                if self.picking_type_id.code == 'outgoing':
                    pick = {
                        'picking_type_id': order.picking_type_id.id,
                        'partner_id': order.responsible.user_id.partner_id.id,
                        'responsible': order.responsible.user_id.partner_id.id,
                        'requested': order.request_raised_for.user_id.partner_id.id,
                        'material_shipment': True,
                        'origin': order.name,
                        'location_dest_id': order.responsible.address_id.property_stock_customer.id,
                        'location_id': order.picking_type_id.default_location_src_id.id,
                        'move_type': 'direct'
                    }
                # if self.picking_type_id.code == 'incoming':
                #     pick = {
                #         'picking_type_id': self.picking_type_id.id,
                #         'partner_id': self.partner_id.id,
                #         'origin': self.name,
                #         'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                #         'location_id': self.partner_id.property_stock_supplier.id,
                #         'move_type': 'direct'
                #     }
                picking = self.env['stock.picking'].create(pick)
                self.invoice_picking_id = picking.id
                self.picking_count = len(picking)
                moves = order.product_lines.filtered(
                    lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
                move_ids = moves._action_confirm()
                move_ids._action_assign()
                self.write({'state': 'received', 'ribbon_state': 'stock_delivered'})

    def action_partial_stock_move(self):
        if not self.picking_type_id:
            raise UserError(_(
                " Please select a picking type"))
        for order in self:
            if not self.invoice_picking_id:
                pick = {}
                if self.picking_type_id.code == 'outgoing':
                    pick = {
                        'picking_type_id': order.picking_type_id.id,
                        'partner_id': order.responsible.user_id.partner_id.id,
                        'responsible': order.responsible.user_id.partner_id.id,
                        'requested': order.request_raised_for.user_id.partner_id.id,
                        'material_shipment': True,
                        'origin': order.name,
                        'location_dest_id': order.responsible.address_id.property_stock_customer.id,
                        'location_id': order.picking_type_id.default_location_src_id.id,
                        'move_type': 'direct'
                    }
                picking = self.env['stock.picking'].create(pick)
                self.invoice_picking_id = picking.id
                self.picking_count = len(picking)
                moves = order.product_lines.filtered(
                    lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
                move_ids = moves._action_confirm()
                move_ids._action_assign()
                self.write({'state': 'partially_received','partial_delivery':True,'ribbon_state': 'partial_stock_delivered',})

    def _compute_material_requisition_notice_period(self):
        count = 0
        date_from = self.indent_date
        date_to = self.required_date
        import datetime
        d11 = str(date_from)
        dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d %H:%M:%S')
        date1 = dt21.strftime("%d/%m/%Y")
        d22 = str(date_to)
        dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
        date2 = dt22.strftime("%d/%m/%Y")
        notice_days = (date_to - date_from).days
        count = notice_days
        self.material_requisition_notice_period = count

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_ready')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        result['domain'] = [('id', '=', self.invoice_picking_id.id)]
        pick_ids = sum([self.invoice_picking_id.id])
        if pick_ids:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids or False
        return result

    @api.model
    def create(self, values):
        values['name'] = self.sudo().env['ir.sequence'].get('material.requisition.indent') or '/'
        res = super(MaterialRequisitionIndent, self).create(values)
        return res

    def indent_dummy(self):
        return True

    def indent_approved(self):
        current_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        current_user = self.env.user.name
        for indent in self:
            if not indent.product_lines:
                raise ValidationError('Alert!!, You cannot confirm an indent %s which has no line.' % (indent.name))
            else:
                state = self.state = 'inprogress'
                return state

    def check_reject(self):
        current_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        current_user = self.env.user.name
        state = self.state = 'reject'
        # self.write({'ribbon_state': 'rejected'})
        # print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        return state


class IndentProductLines(models.Model):
    _name = 'material.requisition.product.lines'
    _description = 'Indent Product Lines'

    indent_id = fields.Many2one('material.requisition.indent', 'Indent', required=True, ondelete='cascade')
    # approved_product_line = fields.Many2one('material.requisition.request.product.lines', 'Indent')
    indent_type = fields.Selection([('new', 'Purchase Indent'), ('existing', 'Repairing Indent')], 'Type')
    product_id = fields.Many2one('product.product', 'Product')
    original_product_id = fields.Many2one('product.product', 'Product to be Repaired')
    product_uom_qty = fields.Float('Quantity Required', digits='Product UoS', default=1)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure')
    product_uos_qty = fields.Float('Quantity (UoS)', digits='Product UoS')
    product_uos = fields.Many2one('uom.uom', 'Product UoS')
    # price_unit = fields.Float('Price', required=True, help="Price computed based on the last purchase order approved.",digits='Product Price')
    qty_available = fields.Float('In Stock')
    product_available = fields.Float(string='OnHand Qty', related='product_id.qty_available')
    delay = fields.Float('Lead Time')
    qty_shipped = fields.Float('QTY Shipped')
    name = fields.Text('Purpose', required=False)
    specification = fields.Text('Specification')
    sequence = fields.Datetime('Sequence')
    product_category = fields.Many2one('product.category', string='Product Category')
    product_type = fields.Selection(string='Product Type', related='product_id.type')

    # return_type = fields.Selection([('non_return', 'Non-returnable'), ('return', 'Returnable'),
    #                                 ('non_return_old', 'Non-returnable with Receipt of Old Ones')],
    #                                'Return Type')
    # product_returned = fields.Boolean('Product Returned')
    # return_date = fields.Date('Return Date')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for val in self:
            if val.product_id:
                # val.name = val.product_id.description or val.product_id.name
                val.product_uom = val.product_id.uom_id and val.product_id.uom_id.id
                val.product_category = val.product_id.categ_id and val.product_id.categ_id.id
                val.product_type = val.product_id.type and val.product_id.type

    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            # price_unit = line.price_unit
            if picking.picking_type_id.code == 'outgoing':
                template = {
                    # 'partner_id': line.responsible.address_id.id,
                    'name': line.name or '',
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'location_id': picking.picking_type_id.default_location_src_id.id,
                    'location_dest_id': line.indent_id.responsible.address_id.property_stock_customer.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    # 'company_id': line.company_id.id,
                    # 'price_unit': price_unit,
                    'picking_type_id': picking.picking_type_id.id,
                    'route_ids': 1 and [
                        (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                    'warehouse_id': picking.picking_type_id.warehouse_id.id,
                }
            # if picking.picking_type_id.code == 'incoming':
            #     template = {
            #         'name': line.name or '',
            #         'product_id': line.product_id.id,
            #         'product_uom': line.product_uom_id.id,
            #         'location_id': line.move_id.partner_id.property_stock_supplier.id,
            #         'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
            #         'picking_id': picking.id,
            #         'state': 'draft',
            #         'company_id': line.move_id.company_id.id,
            #         'price_unit': price_unit,
            #         'picking_type_id': picking.picking_type_id.id,
            #         'route_ids': 1 and [
            #             (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
            #         'warehouse_id': picking.picking_type_id.warehouse_id.id,
            #     }
            diff_quantity = line.product_uom_qty
            tmp = template.copy()
            tmp.update({
                'product_uom_qty': diff_quantity,
            })
            template['product_uom_qty'] = diff_quantity
            done += moves.create(template)
        return done


class IndentRequestProductLines(models.Model):
    _name = 'material.requisition.request.product.lines'
    _description = 'Indent Request Product Lines'

    indent_id = fields.Many2one('material.requisition.indent', 'Indent', required=True, ondelete='cascade')
    indent_type = fields.Selection([('new', 'Purchase Indent'), ('existing', 'Repairing Indent')], 'Type')
    product_id = fields.Many2one('product.product', 'Product')
    original_product_id = fields.Many2one('product.product', 'Approved Product')
    product_uom_qty = fields.Float('Quantity Required', digits='Product UoS', default=1)
    approved_product_uom_qty = fields.Float('Quantity Approved', required=True, digits='Product UoS')
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure')
    approved_product_uom = fields.Many2one('uom.uom', 'Unit of Measure', related='original_product_id.uom_id')
    product_uos_qty = fields.Float('Quantity (UoS)', digits='Product UoS')
    product_uos = fields.Many2one('uom.uom', 'Product UoS')
    # price_unit = fields.Float('Price', required=True, help="Price computed based on the last purchase order approved.",digits='Product Price')
    qty_available = fields.Float('In Stock')
    product_available = fields.Float(string='OnHand Qty', related='product_id.qty_available')
    approved_product_available = fields.Float(string='Approved OnHand Qty',
                                              related='original_product_id.qty_available', )
    delay = fields.Float('Lead Time')
    name = fields.Text('Purpose')
    specification = fields.Text('Specification')
    sequence = fields.Datetime('Sequence')
    product_category = fields.Many2one('product.category', string='Product Category', related='product_id.categ_id')
    approved_product_category = fields.Many2one('product.category', string='Approved Product Category',
                                                related='original_product_id.categ_id')
    product_type = fields.Selection(string='Product Type', related='product_id.detailed_type')
    approved_product_type = fields.Selection(string='Approved Product Type',
                                             related='original_product_id.detailed_type')
    short_close = fields.Boolean('Short Close')

    # return_type = fields.Selection([('non_return', 'Non-returnable'), ('return', 'Returnable'),
    #                                 ('non_return_old', 'Non-returnable with Receipt of Old Ones')],
    #                                'Return Type')
    # product_returned = fields.Boolean('Product Returned')
    # return_date = fields.Date('Return Date')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for val in self:
            if val.product_id:
                # val.name = val.product_id.description or val.product_id.name
                val.product_uom = val.product_id.uom_id and val.product_id.uom_id.id
                val.product_category = val.product_id.categ_id and val.product_id.categ_id.id
                val.product_type = val.product_id.type and val.product_id.type

    @api.onchange('original_product_id')
    def onchange_original_product_id(self):
        for val in self:
            if val.original_product_id:
                # val.name = val.product_id.description or val.product_id.name
                val.product_uom = val.original_product_id.uom_id and val.original_product_id.uom_id.id
                val.product_category = val.original_product_id.categ_id and val.original_product_id.categ_id.id
                val.product_type = val.original_product_id.type and val.original_product_id.type


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    indent_id = fields.Many2one('material.requisition.indent', 'Indent')
    received = fields.Boolean('Received', readonly=True, copy=False)
    approved = fields.Boolean('Approved', readonly=True, copy=False)
    received_id = fields.Many2one('res.users', 'Received by', readonly=True, copy=False)
    approved_id = fields.Many2one('res.users', 'Approved by', readonly=True, copy=False)
    reversed = fields.Boolean('Reversed', copy=False)
    md_note = fields.Text('MD/GM Notes', tracking=True)
    store_note = fields.Text('Store Notes', tracking=True)
    cancel_reason = fields.Text('Reason for cancellation', tracking=True)
    received_date = fields.Date('Received Date'),
    approved_date = fields.Date('Approved Date')
    responsible = fields.Many2one('res.partner', string='Request Raised By')
    requested = fields.Many2one('res.partner', string='Request Raised For')
    shipment = fields.Boolean('Shipment', copy=False)
    gate_entry_count = fields.Integer(compute='_compute_gate_entry_count', string='Gate Entry',
                                      default=0)

    def _compute_gate_entry_count(self):
        self.gate_entry_count = self.env['gate.entry'].sudo().search_count(
            [('purchase_id.name', '=', self.origin)])

    def create_material_shipped(self):
        material_sr = self.env['material.requisition.indent'].search([('name', '=', self.origin)])
        print('------------------------------------------1111', material_sr)
        stock_pic = self.env['stock.picking'].search([('origin', '=', self.origin)])
        print('22222222222222222222222222222200000000000', stock_pic)
        for num in stock_pic:
            for line in material_sr.product_lines:
                if num.state == 'done':
                    print('0000000000', num.state == 'done')
                    material_sr.update({
                        'stock_transferred': True,
                    })
                else:
                    material_sr.update({
                        'stock_transferred': False,
                    })
            print('09087788===========================================', )
            return True


class StockMove(models.Model):
    _inherit = 'stock.move'

    indent_line_id = fields.Many2one('material.requisition.product.lines', 'Indent Lines')
    department_id = fields.Many2one('hr.department', string='Department')


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    indent_id = fields.Many2one('material.requisition.indent', 'Indent')


class MaterialRequisitionApproveRemarks(models.TransientModel):
    _name = 'material.requisition.approve.remarks'
    _description = 'Material Requisition Approve Remarks'
    _inherit = ['mail.thread']

    remarks = fields.Text('Remarks')
    is_default_remark = fields.Boolean('Enable Default Remark')
    default_remark = fields.Text('Default Remark',
                                 default='Requisition Approval get confirmed Without Remarks')

    # @api.onchange("is_default_remark")
    # def onchange_is_default_remark(self):
    #     for val in self:
    #         if val.is_default_remark == True:
    #             val.remarks = val.default_remark
    #         else:
    #             val.remarks = ''

    @api.onchange("is_default_remark")
    def _onchange_is_default_remark(self):
        for val in self:
            if val.is_default_remark == True:
                val.remarks = val.default_remark
            else:
                val.remarks = ''

    def tick_ok(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['material.requisition.indent'].search([('id', '=', applicant_id)])
        today = date.today()
        current_date = today.strftime("%d/%m/%Y")
        # current_date = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        current_user = self.env.user.name

        if active_id.state == 'to_be_approved':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_approval()
            active_id.write({'approver1_approve_reason': text})
        elif active_id.state == 'leader_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_approval()
            active_id.write({'approver2_approve_reason': text})
        elif active_id.state == 'manager_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_approval()
            active_id.write({'approver3_approve_reason': text})
        elif active_id.state == 'director_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_approval()
            active_id.write({'approver4_approve_reason': text})
        elif active_id.state == 'ceo_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_approval()
            active_id.write({'approver5_approve_reason': text})
        return True


class MaterialRequisitionRejectRemarks(models.TransientModel):
    _name = 'material.requisition.reject.remarks'
    _description = 'Material Requisition Reject Remarks'
    _inherit = ['mail.thread']

    remarks = fields.Text('Remarks')

    def tick_ok(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['material.requisition.indent'].search([('id', '=', applicant_id)])
        today = date.today()
        current_date = today.strftime("%d/%m/%Y")
        # current_date = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        current_user = self.env.user.name

        if active_id.state == 'to_be_approved':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_rejection()
            active_id.write({'approver1_reject_reason': text})
        elif active_id.state == 'leader_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_rejection()
            active_id.write({'approver2_reject_reason': text})
        elif active_id.state == 'manager_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_rejection()
            active_id.write({'approver3_reject_reason': text})
        elif active_id.state == 'director_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_rejection()
            active_id.write({'approver4_reject_reason': text})
        elif active_id.state == 'ceo_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_rejection()
            active_id.write({'approver5_reject_reason': text})
        return True


class MaterialRequisitionCancelRemarks(models.TransientModel):
    _name = 'material.requisition.cancel.remarks'
    _description = 'Material Requisition Cancel Remarks'
    _inherit = ['mail.thread']

    remarks = fields.Text('Remarks')

    def tick_ok(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['material.requisition.indent'].search([('id', '=', applicant_id)])
        today = date.today()
        current_date = today.strftime("%d/%m/%Y")
        # current_date = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        current_user = self.env.user.name

        if active_id.state == 'to_be_approved':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_cancellation()
            active_id.write({'approver1_cancel_reason': text})
        elif active_id.state == 'leader_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_cancellation()
            active_id.write({'approver2_cancel_reason': text})
        elif active_id.state == 'manager_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_cancellation()
            active_id.write({'approver3_cancel_reason': text})
        elif active_id.state == 'director_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_cancellation()
            active_id.write({'approver4_cancel_reason': text})
        elif active_id.state == 'ceo_approval':
            text = '[ ' + current_user + ' ]' + '[ ' + current_date + ' ]' + ' - ' + self.remarks + '\n'
            active_id.apply_cancellation()
            active_id.write({'approver5_cancel_reason': text})
        return True
