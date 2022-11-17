# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError, AccessError, ValidationError
import logging
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.osv import expression
import re

_logger = logging.getLogger(__name__)


class GateEntry(models.Model):
    """
       One of Main class for this module, contains purchase_order_ids, sale_order_ids [ split into two  inward/outward because conditions for domain
       is different for inward and outward ].And order type is changed based on the entry_type. [ Ex: If entry_type is "in" then it should show ( purchase, sale return)
       if its "out" it should show(sale, purchase return)].
       Similarly we have fields for rece
    """
    _name = 'gate.entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'gate entry'
    _order = ' id desc, name desc'

    name = fields.Char(string='Name')
    entry_type = fields.Selection(string='Entry Type', selection=[('in', 'Inward'), ('out', 'Outward')])
    order_type_inward = fields.Selection(string=" Order type",
                                         selection=[('sr', 'Purchase/GRN')],default='sr')

    # order_type_inward = fields.Selection(string=" Order type",
    #                                      selection=[('p', 'Purchase'), ('s', 'Sale'), ('sr', 'Return'), (
    #                                      'others', 'Others')])  # p = purchase, sr = sales return, tin = transefer In
    # order_type_outward = fields.Selection(string= "Order type",selection =[ ('s','Sale'), ('pr','Purchase Return'),('others','Others')]) # s = sales, pr = purchase return, t = transefer Out

    username = fields.Many2one("gate.user.registration")
    description = fields.Char()
    # item_description = fields.Char()
    doc_datetime = fields.Datetime("Document Date")
    post_datetime = fields.Datetime("Posting Date")
    lr_rr_no = fields.Char(string="LR/RR No.")
    lr_rr_date = fields.Datetime(string="LR/RR Date")
    vehicle_no = fields.Many2one('fleet.vehicle', string="Internal Vechile No.")
    external_vehicle_no = fields.Char(string="External Vechile No.")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", domain=[('activate_gate_entry', '=', True)])
    # stock_picking_in = fields.Many2many('stock.picking',string ='Transfer')
    purchase_order = fields.Many2many('purchase.order', string='Purchase Order')
    # stock_picking_out = fields.Many2one('stock.picking',string ='Transfer OUT')
    # stock_picking_int = fields.Many2one('stock.picking','Transfer INT')
    gate_line = fields.One2many('gate.entry.line', 'gate_id')
    station_from = fields.Char()
    station_to = fields.Char()
    is_outgoing_gate_entry = fields.Boolean('Outgoing Gate Entry')
    is_incoming_gate_entry = fields.Boolean('Incoming Gate Entry')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('processed', 'Processed'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft')
    supplier_name = fields.Many2one('res.partner', string="Vendor")
    # is_vendor = fields.Boolean('Vendor')
    purchase_ids = fields.One2many('purchase.gate', 'gate_entry_id', string="Purchase Details")
    stock_ids = fields.One2many('stock.picking.gate.entry', 'gate_entry_id', string="Stocking Details")

    # other_inward = fields.Many2one('stock.picking', string=' Others', store=True)
    # other_outward = fields.Many2one('stock.picking', string='Others', store=True)
    # purchase_return_receipt_ids = fields.Many2one("stock.picking", string=" Transfers")
    stock_picking = fields.Many2many("stock.picking", string="Transfers")
    invoice_num = fields.Char(string='Invoice/DC No')
    purchase_no = fields.Many2one('purchase.order',string='Purchase')
    gate_entry_date = fields.Datetime('Date', readonly=True,
                                  default=lambda self: fields.Datetime.now())

    # @api.onchange("is_vendor")
    # def on_change_partner(self):
    #     self.supplier_name = False
    #     res = {}
    #     # if self.is_customer:
    #     #     res = {'domain': {
    #     #         'partner_id': ['1', '1', ('customer', '=', True), ('old_customer', '', True), ('new_customer', '=', True)]}}
    #     if self.is_vendor:
    #         res = {'domain': {
    #         'supplier_name': ['1', '1', ('supplier', '', True)]}}
    #     else:
    #         res = {'domain': {'supplier_name': [(0, '', 0)]}}
    #     return res

    @api.onchange('supplier_name')
    def onchange_supplier_name(self):
        for rec in self:
            return {'domain': {'stock_picking': [('partner_id', '=', rec.supplier_name.id),('state', '=', 'assigned')]}}

    @api.onchange("is_outgoing_gate_entry", "is_incoming_gate_entry")
    def on_change_picking(self):
        self.stock_picking = False
        res = {}
        if self.is_outgoing_gate_entry:
            res = {'domain': {'stock_picking': [('picking_type_code', '!=', 'incoming')]}}
        elif self.is_incoming_gate_entry:
            res = {'domain': {'stock_picking': [('picking_type_code', '=', 'incoming')]}}
        else:
            res = {'domain': {'stock_picking': [(0, '=', 0)]}}
        return res

    def get_stock_items(self):
        stock = []
        picking_sr = self.env['stock.picking'].search([('id', '=', self.stock_picking.ids)])
        for st in self:
            vals = [0, 0, {
                'challan_no': st.invoice_num,
                'challan_date': st.post_datetime,
                'sale_return_receipt_ids': picking_sr.ids,
            }]
            stock.append(vals)
        return stock

    def get_line_items(self):
        line_vals = []
        purchase_sr = self.env['purchase.order'].search([('id', '=', self.purchase_order.ids)])
        for line in self:
            vals = [0, 0, {
                'challan_no': line.invoice_num,
                'challan_date': line.post_datetime,
                'purchase_order_inward_ids': purchase_sr.ids,
            }]
            line_vals.append(vals)
        return line_vals

    def action_split_travel(self):
        requisition_created = False
        for line in self:
            if line.purchase_order:
                requisition_created = line.update({
                    'gate_line': line.get_line_items(),
                })
            if line.stock_picking:
                requisition_created = line.update({
                    'gate_line': line.get_stock_items(),
                })
            self.write({'state': 'confirmed'})
            return True

    @api.onchange('stock_picking')
    def get_sale_return_receipt_details(self):
        self.ensure_one()
        picking_sr = self.env['stock.picking'].search([('id', '=', self.stock_picking.ids)])
        lines = [(5, 0, 0)]
        for line in picking_sr.move_ids_without_package:
            vals = {
                'product': line.product_id.name,
                'product_id': line.product_id.id,
                # 'origin': line.picking_id.name,
                'price_after_discount': line.price_after_discount,
                'product_uom_qty': line.product_uom_qty,
            }
            lines.append((0, 0, vals))
            self.stock_ids = lines

    @api.onchange('purchase_order')
    def get_purchase_details(self):
        self.ensure_one()
        purchase_sr = self.env['purchase.order'].search([('id', '=', self.purchase_order.ids)])
        lines = [(5, 0, 0)]
        for line in purchase_sr.order_line:
            vals = {
                'product': line.product_id.name,
                'product_id': line.product_id.id,
                'origin': line.order_id.name,
                'product_qty': line.product_qty,
                'onhand_quantity': line.on_hand_qty,
                'received': line.qty_received,
                'invoiced': line.qty_invoiced,
                'unity_price': line.price_unit,
                'discount': line.discount,
                'discount_amount': line.discount_amount,
                'price_after_discount': line.price_after_discount,
                'price_subtotal': line.price_subtotal,
            }
            lines.append((0, 0, vals))
            self.purchase_ids = lines

    @api.constrains('warehouse_id')
    def vehicle_number(self):
        if not self.vehicle_no and not self.external_vehicle_no:
            raise UserError(_('Please Select Any Vehicle Number.'))

    @api.constrains('warehouse_id')
    def warehouse_name(self):
        if self.username:
            warehouse = self.warehouse_id
            if self.warehouse_id.id != self.username.warehouse_id.id:
                raise UserError(
                    _('Your Not Authorised To Do Transaction In %s Warehouse.') % ', '.join(warehouse.mapped('name')))

    def unlink(self):
        for each_entry in self:
            if each_entry.state != 'draft':
                raise UserError(_('You cannot delete an entry which has been Processed once.'))
        return super(GateEntry, self).unlink()

    @api.model
    def create(self, vals):
        if (self.env.context['default_entry_type'] == 'in'):
            sequence_type = vals.get('warehouse_id')
            sequence_type = self.env['stock.warehouse'].browse(sequence_type)
            if not sequence_type:
                raise Warning('Inward sequence is not set')
            else:
                vals['name'] = sequence_type.inward_sequence.next_by_id()
                vals['post_datetime'] = fields.Datetime.now()
        else:
            sequence_type = vals.get('warehouse_id')
            sequence_type = self.env['stock.warehouse'].browse(sequence_type)
            if not sequence_type:
                raise Warning('Outward sequence is not set')
            else:
                vals['name'] = sequence_type.outward_sequence.next_by_id()
                vals['post_datetime'] = fields.Datetime.now()

        return super(GateEntry, self).create(vals)

    def process(self):
        for each in self.gate_line:
            if self.entry_type == 'in':
                # if each.order_type_inward == 'p':
                #     for l in each.purchase_order_inward_ids:
                #         for picking in l.picking_ids.filtered(lambda e: e.picking_type_id.code == 'incoming'):
                #             if picking.state != 'done':
                #                 picking.write({
                #                     'gate_entry_id': self.id,
                #                     'invoice_num':self.invoice_num,
                #                     'gate_entry_date':self.post_datetime,
                #                     'vehicle_num': self.vehicle_no.name or self.external_vehicle_no,
                #                 })

                if each.order_type_inward == 'sr':
                    for picking in each.sale_return_receipt_ids:
                        if picking.state != 'done':
                            picking.write({
                                'gate_entry_id': self.id,
                                'invoice_num': self.invoice_num,
                                'gate_entry_date': self.post_datetime,
                                'vehicle_num': self.vehicle_no.name or self.external_vehicle_no,
                            })

                # if each.order_type_inward == 'others':
                #     for l in each.other_inward:
                #         for picking in l.filtered(
                #                 lambda e: e.picking_type_id.code == 'incoming' or e.picking_type_id.code == 'internal' and e.location_id.usage == "inventory"):
                #             if picking.state != 'done':
                #                 picking.write({
                #                     'gate_entry_id': self.id,
                #                     'invoice_num': self.invoice_num,
                #                     'gate_entry_date': self.post_datetime,
                #                     'vehicle_num': self.vehicle_no.name or self.external_vehicle_no,
                #                 })

            elif self.entry_type == 'out':
                # if each.order_type_inward == 'others':
                #     for l in each.other_outward:
                #         for picking in l.filtered(
                #                 lambda e: e.picking_type_id.code == 'outgoing' or e.picking_type_id.code == 'internal' and e.location_dest_id.usage == "inventory"):
                #             if picking.state == 'done':
                #                 if not picking.gate_entry_id:
                #                     picking.write({
                #                         'gate_entry_id': self.id,
                #                         'invoice_num': self.invoice_num,
                #                         'gate_entry_date': self.post_datetime,
                #                         'vehicle_num': self.vehicle_no.name or self.external_vehicle_no,
                #                     })

                # if each.order_type_inward == 's':
                #     for picking in each.purchase_return_receipt_ids:
                #         if picking.state == 'done':
                #             if not picking.gate_entry_id:
                #                 picking.write({
                #                     'gate_entry_id': self.id,
                #                     'invoice_num': self.invoice_num,
                #                     'gate_entry_date': self.post_datetime,
                #                     'vehicle_num': self.vehicle_no.name or self.external_vehicle_no,
                #                 })

                if each.order_type_inward == 'sr':
                    for picking in each.purchase_return_receipt_ids:
                        if picking.state == 'done':
                            picking.write({
                                'gate_entry_id': self.id,
                                'invoice_num': self.invoice_num,
                                'gate_entry_date': self.post_datetime,
                                'vehicle_num': self.vehicle_no.name or self.external_vehicle_no,
                            })
                        # else:
                        #     if picking.id in each.purchase_return_receipt_ids.ids:
                        #         picking.write({'gate_entry_id':self.id})

                # if each.order_type_outward == 'pr':
                #     for picking in each.purchase_return_receipt_ids:
                #         if picking.state == 'done':
                #             picking.write({'gate_entry_purchase_outward_id':self.id})
        return self.write({'state': 'processed'})

    def cancle(self):
        return self.write({'state': 'cancel'})


class GateEntryLine(models.Model):
    _name = 'gate.entry.line'
    _description = 'Gate Entry Line'

    challan_no = fields.Char('Invoice/Dc No')
    challan_date = fields.Datetime('Invoice Date')
    description = fields.Char(string='Item Description')
    purchase_gate_line = fields.Many2one('purchase.gate', string='Purchase Gate Line')

    gate_id = fields.Many2one('gate.entry', string='Gate Id')
    sequence = fields.Integer(default=10)

    # order_type_inward = fields.Selection(string="Order type", selection=[('p','Purchase'),('sr','Sales Return'),('scin','Sub-Contract'),('tout','Transfer')], domain="[('parent.entry_type', '=', 'out')]")
    # order_type_outward = fields.Selection(string= "Order type",selection =[('s','Sale'),('pr','Purchase Return'),('scout','Sub-Contract'),('tout','Transfer')], domain = "[('parent.entry_type', '=', 'in')]")

    entry_type = fields.Selection(related='gate_id.entry_type', store=True, readonly=False)

    order_type_inward = fields.Selection(related='gate_id.order_type_inward', store=True, readonly=False,
                                         string='Order Type')
    # order_type_outward = fields.Selection(related='gate_id.order_type_outward', store=True, readonly=False,string=' Order Type')

    # warehouse_ids = fields.Many2one("stock.warehouse", string="Warehouse",domain=[('activate_gate_entry','=',True)],compute='compute_warehouse')

    purchase_order_inward_ids = fields.Many2many("purchase.order", string="Purchase Order")
    purchase_order_outward_ids = fields.Many2many("purchase.order", relation="purchase_order_outward_ids_rel",
                                                  column1="gate_entry_id", column2="purchase_order_id",
                                                  string=" Purchase Order")

    sale_order_inward_ids = fields.Many2many("sale.order", relation="sale_order_inward_ids_rel",
                                             column1="gate_entry_id", column2="sale_order_id", string="Sale Order")
    sale_order_outward_ids = fields.Many2many("sale.order", relation="sale_order_outward_ids_rel",
                                              column1="gate_entry_id", column2="sale_order_id", string=" Sale Order")

    # purchase_receipt_ids = fields.Many2many("stock.picking", realtion="purchase_receipt_ids_rel", column1="gate_entry_id", column2="stock_picking_id" , string= "Receipts")
    other_inward = fields.Many2one('stock.picking', string=' Others', store=True)
    other_outward = fields.Many2one('stock.picking', string='Others', store=True)
    purchase_return_receipt_ids = fields.Many2one("stock.picking", string=" Transfers")

    # sale_receipt_ids = fields.Many2many("stock.picking", relation="sale_receipt_ids_rel", column1="gate_entry_id", column2="stock_picking_id" , string= "Receipts")
    sale_return_receipt_ids = fields.Many2many("stock.picking", string="Transfers")

    # @api.onchange('purchase_order_inward_ids')
    # def get_purchase_details(self):
    #     purchase_sr = self.env['purchase.order'].search([('id', '=', self.purchase_order_inward_ids.ids)])
    #     print(purchase_sr)
    #     lines = [(5, 0, 0)]
    #     for line in purchase_sr.order_line:
    #         print(line)
    #         vals = {
    #             'origin': line.name,
    #             'product_id': line.product_id.name,
    #             'price_after_discount': line.price_after_discount,
    #             'demand': line.product_qty,
    #             # 'reserved': line.forecast_availability,
    #             # 'done': line.quantity_done,
    #             'suppier_rate': line.price_subtotal,
    #         }
    #         lines.append((0, 0, vals))
    #         self.purchase_gate_line = lines

    def unlink(self):
        for each_entry in self:
            if each_entry.gate_id.state != 'draft':
                raise UserError(_('You cannot delete an entry which has been Processed once.'))
        return super(GateEntryLine, self).unlink()

    @api.onchange('order_type_inward')
    def get_outward_filter(self):
        if self.order_type_inward == 'sr':
            return {'domain': {'purchase_return_receipt_ids': [('purchase_return', '=', True),
                                                               ('picking_type_code', '=', 'outgoing')]}}
        # elif self.order_type_inward == 's':
        #     return {'domain': {
        #         'purchase_return_receipt_ids': [('purchase_return', '!=', True), ('picking_type_code', '=', 'outgoing'),
        #                                         ('gate_entry_id', '=', False), ('state', '=', 'done'),
        #                                         ('sale_id', '!=', False)]}}

    @api.onchange('order_type_inward')
    def get_inward_filter(self):
        if self.order_type_inward == 'sr':
            return {'domain': {
                'sale_return_receipt_ids': [('purchase_return', '=', True), ('picking_type_code', '=', 'incoming'),
                                            ('gate_entry_id', '=', False)]}}

    # @api.depends('gate_id.warehouse_id')
    # def compute_warehouse(self):
    #     for l in self:
    #         for line in l.gate_id:
    #             l.warehouse_ids = line.warehouse_id.id


class GateEntryName(models.Model):
    """
        activate_gate_entry field is true then the gate entry will create other wise gate entry is not allowed.
    """
    _inherit = 'stock.warehouse'

    activate_gate_entry = fields.Boolean()
    inward_sequence = fields.Many2one("ir.sequence", string="Inward Sequence")
    outward_sequence = fields.Many2one("ir.sequence", string="Outward Sequence")

    @api.constrains('activate_gate_entry')
    def warehouse_number(self):
        if self.activate_gate_entry:
            if not self.inward_sequence or not self.outward_sequence:
                raise UserError(_('Please Select Both Inward And Outward Sequence.'))


class PurchaseOrderDone(models.Model):
    _inherit = "purchase.order"

    warehouse_id = fields.Many2one("stock.warehouse", related="picking_type_id.warehouse_id")
    # purchase_entry_inward_done = fields.Boolean( compute="check_gate_entry_check", store=True,copy=False)
    # # purchase_entry_outward_done = fields.Boolean( compute="check_gate_entry_check", store=True,copy=False)

    # is_return =  fields.Boolean(compute='compute_return_grn', store=True)
    # is_return_outward =  fields.Boolean(compute='compute_return_grn_outward', store=True)
    # sale_done = fields.Boolean(compute="done_check", store=True)

    # @api.depends('picking_ids.state')
    # def compute_return_grn(self):
    #     for each in self:
    #         if any(each.picking_ids.filtered(lambda l:l.picking_type_id.code == 'outgoing' and l.state != 'done')):
    #             each.is_return = True
    #         else:
    #             if any(each.picking_ids.filtered(lambda l:l.picking_type_id.code == 'outgoing' and l.state == 'done' and not l.gate_entry_id)):
    #                 each.is_return = True
    #             else:
    #                 each.is_return = False

    # @api.depends('picking_ids.gate_entry_purchase_outward_id')
    # def compute_return_grn_outward(self):
    #     for each in self:
    #         if any(each.picking_ids.filtered(lambda l:l.picking_type_id.code == 'outgoing' and l.state == 'done' and l.gate_entry_purchase_outward_id)):
    #             if any(each.picking_ids.filtered(lambda e:e.picking_type_id.code == 'outgoing' and not e.gate_entry_purchase_outward_id)):
    #                 each.is_return_outward = False
    #             else:
    #                 each.is_return_outward = True
    #         else:
    #             each.is_return_outward = False

    # def close_pos(self):
    #     for line in self.order_line:
    #         if not line.purchase_order_line_done:
    #             line.write({'purchase_order_line_done':True})

    # @api.depends('order_line.purchase_order_line_done')
    # def check_gate_entry_check(self):
    #     for rec in self:
    #         if rec.order_line:
    #             if any(rec.order_line.filtered(lambda e:e.purchase_order_line_done == False)):
    #                 rec.purchase_entry_inward_done = False
    #             else:
    #                 rec.purchase_entry_inward_done = True
    #         else:
    #             rec.purchase_entry_inward_done = None


# class PurchaseOrderLineVerify(models.Model):
#     _inherit = 'purchase.order.line'

#     purchase_order_line_done = fields.Boolean(store=True,copy=False)


# class SaleOrderDone(models.Model):
#     _inherit = "sale.order"

#     # sale_entry_inward_done = fields.Boolean( compute="check_gate_entry_check",store=True, copy=False)
#     sale_entry_outward_done = fields.Boolean( compute="check_gate_entry_check",store=True, copy=False)

#     is_return =  fields.Boolean(compute='compute_return_grn', store=True ,copy=False)
#     sale_done = fields.Boolean(compute="done_check", store=True,copy=False)
#     sale_gate_entry = fields.Boolean(store=True,copy=False)

#     @api.depends('order_line.sale_order_line_done')
#     def check_gate_entry_check(self):
#         for rec in self:
#             if rec.order_line:
#                 if any(rec.order_line.filtered(lambda e:e.sale_order_line_done == False)):
#                     rec.sale_entry_outward_done = False
#                 else:
#                     rec.sale_entry_outward_done = True
#             else:
#                 rec.sale_entry_outward_done = False


#     @api.depends('picking_ids.state')
#     def compute_return_grn(self):
#         for each in self:
#             if any(each.picking_ids.filtered(lambda l:l.picking_type_id.code == 'incoming' and l.state != 'done')):
#                 each.is_return = True
#             else:
#                 each.is_return = False

#     @api.depends('picking_ids.state','picking_ids.gate_entry_id')
#     def done_check(self):
#         for each in self:
#             # print(each.picking_ids.gate_entry_id,each.picking_ids.state,'SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS')
#             # if any(each.picking_ids.filtered(lambda l:l.state == 'done' and l.gate_entry_id)):
#             if any(each.picking_ids.filtered(lambda l: not l.gate_entry_id)):
#                 # print('SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS')
#                 # if any(each.order_line.filtered(lambda e:e.sale_order_line_done == False)):
#                 # print('MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM')
#                 # each.sale_done = False
#                 each.sale_done = False
#             else:
#                 # print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
#                 each.sale_done = True
# else:
#     print('ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ')
#     each.sale_done = False

# @api.depends('picking_ids.gate_entry_id')
# def done_check_gate_entry(self):
#     for each in self:
#         # print(each.picking_ids.gate_entry_id,each.picking_ids.state,'************************************************')
#         if any(each.picking_ids.filtered(lambda l:l.gate_entry_id)):
#             if any(each.order_line.filtered(lambda e:e.sale_order_line_done == True)):
#                 each.sale_gate_entry = True
#             else:
#                 each.sale_gate_entry = False
#         else:
#             each.sale_gate_entry = False

# def close_sos(self):
#     self.write({'sale_gate_entry':True})
#     for line in self.order_line:
#         if not line.sale_order_line_done:
#             line.write({'sale_order_line_done':True})


# class SaleOrderLineVerify(models.Model):
#     _inherit = 'sale.order.line'

#     sale_order_line_done = fields.Boolean(copy=False)
# sale_order_line_inward_done = fields.Boolean(copy=False)

# @api.depends('order_id.picking_ids.gate_entry_id','order_id.picking_ids.state')
# def compute_sale_order_line_done(self):
#     for l in self:
#     # for l in self.order_id:
#         if any(l.order_id.picking_ids.filtered(lambda e:e.gate_entry_id == None and e.state=='done' and e.picking_type_id.code == 'outgoing')):
#             l.write({'sale_order_line_done': False})
#         # if l.picking_ids.picking_type_id.code == 'outgoing':
#         #     for each in l.picking_ids.move_ids_without_package:
#         #         if l.picking_ids.sale_id:
#         #             # if each.sale_line_id.qty_delivered >= each.sale_line_id.product_uom_qty:
#         #             if any(l.picking_ids.filtered(lambda e:e.gate_entry_id == None)):
#         #             else:
#         #                 each.sale_line_id.write({'sale_order_line_done': True})
#         #         else:
#         #             self.write({'sale_order_line_done': False})
#         else:
#             l.write({'sale_order_line_done': True})


class StockPicking(models.Model):
    _inherit = "stock.picking"

    gate_entry_id = fields.Many2one('gate.entry', copy=False)
    # gate_entry_purchase_outward_id = fields.Many2one('gate.entry',copy=False)
    purchase_return = fields.Boolean(store=True, compute='compute_purchase_return')
    purchase_boolean = fields.Boolean(string='Purchase Boolean', store=True, compute='compute_purchase_boolean')
    invoice_num = fields.Char(string='Invoice/DC No')
    gate_entry_date = fields.Datetime('Date', readonly=True)
    supplier_invoice_no = fields.Char(string='Supplier Invoice Number')
    bill_date = fields.Date(string='Bill Date')
    vehicle_num = fields.Char(string='Vehicle Number')
    ho_department = fields.Many2one('ho.department', string='Department')

    def name_get(self):
        result = []
        for rec in self:
            if rec.origin:
                name = '[' + str(rec.origin) + ']' +rec.name
                result.append((rec.id, name))
            else:
                name = rec.name
                result.append((rec.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        # if self.origin:
        #     domain = [('origin', operator, name)]
        if name:
            domain = [('origin', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    @api.depends('move_ids_without_package.origin_returned_move_id')
    def compute_purchase_return(self):
        for l in self:
            for line in l.move_ids_without_package:
                if line.origin_returned_move_id:
                    l.purchase_return = True
                else:
                    l.purchase_return = False

    @api.depends('purchase_id')
    def compute_purchase_boolean(self):
        for l in self:
            if l.purchase_id:
                l.purchase_boolean = True
            else:
                l.purchase_boolean = False

    def button_validate(self):
        for aaa in self.move_ids_without_package:
            if aaa.quantity_done > aaa.product_uom_qty:
                raise UserError(_('Alert!, The %s Done Quantity should be equal or less than Demand Quantity. \n '
                                  'Please Check it.')%self.name)
                self.write({'verify_stock': True})
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        if self.picking_type_id.code != 'outgoing':
            if self.picking_type_id.code != 'internal':
                if self.picking_type_id.code != 'mrp_operation':
                    if self.picking_type_id.code != 'mrp_operation' and not self.gate_entry_id and self.picking_type_id.warehouse_id.activate_gate_entry:
                        raise ValidationError('Gate Entry Not Done')
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(
                float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
                picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(
                float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line
                in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(
                        lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(
                    products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(
                    pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _(
                    '\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To force these transfers, switch in edit more and encode the done quantities.') % ', '.join(
                    pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (
                ', '.join(pickings_without_lots.mapped('name')),
                ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

        if self.user_has_groups('stock.group_reception_report') \
                and self.user_has_groups('stock.group_auto_reception_report') \
                and self.filtered(lambda p: p.picking_type_id.code != 'outgoing'):
            lines = self.move_lines.filtered(lambda
                                                 m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
            if lines:
                # don't show reception report if all already assigned/nothing to assign
                wh_location_ids = self.env['stock.location']._search(
                    [('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id),
                     ('usage', '!=', 'supplier')])
                if self.env['stock.move'].search([
                    ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                    ('product_qty', '>', 0),
                    ('location_id', 'in', wh_location_ids),
                    ('move_orig_ids', '=', False),
                    ('picking_id', 'not in', self.ids),
                    ('product_id', 'in', lines.product_id.ids)], limit=1):
                    action = self.action_view_reception_report()
                    action['context'] = {'default_picking_ids': self.ids}
                    return action
        self.create_qty_material()
        self.create_partial_qty_material()
        return True

    def create_qty_material(self):
        material_requisition_sr = self.env['material.requisition.indent'].search([('name', '=', self.origin)])
        purchase_order = self.env['purchase.order'].search([('name', '=', self.origin)])
        mr_list = self.env['material.requisition.indent'].search([('name', '=', purchase_order.origin)])
        stock_pic = self.env['stock.picking'].search([('origin', '=', self.origin)])
        if self.origin:
            mr_list.update({
                'grn_status': True,
                # 'stock_picking_id': self.id,
                'ribbon_state': 'grn_completed',
            })
        for num in stock_pic:
            for line in material_requisition_sr.product_lines:
                if num.state == 'done':
                    material_requisition_sr.update({
                        'state': 'done',
                        'stock_transferred': True,
                        'ribbon_state': 'delivery_done',
                        'issued_date': num.write_date,
                        'inward_date': num.scheduled_date,
                        'store_incharge': self.env.user.name,
                    })
            added_qty = 0.0
            for line in material_requisition_sr.product_lines:
                added_qty = 0.0
                for val in stock_pic:
                    for qty in val.move_ids_without_package:
                        if qty.product_id.id == line.product_id.id:
                            added_qty += qty.quantity_done
                            product_id = qty.product_id
                    if stock_pic.product_id.id == line.product_id.id:
                        line.update({
                            'qty_shipped': added_qty,
                        })
            return True


    def create_partial_qty_material(self):
        material_requisition_sr = self.env['material.requisition.indent'].search([('name', '=', self.origin)])
        stock_pic = self.env['stock.picking'].search([('origin', '=', self.origin)])
        for num in stock_pic:
            for line in material_requisition_sr.product_lines:
                if num.state == 'confirmed':
                    if num.backorder_id:
                        material_requisition_sr.write({
                            'state': 'partially_received',
                            'partial_delivery': True,
                            'ribbon_state': 'partial_delivery_done',
                        })
            added_qty = 0.0
            for line in material_requisition_sr.product_lines:
                added_qty = 0.0
                for val in stock_pic:
                    for qty in val.move_ids_without_package:
                        if qty.product_id.id == line.product_id.id:
                            added_qty += qty.quantity_done
                            product_id = qty.product_id
                    if stock_pic.product_id.id == line.product_id.id:
                        line.update({
                            'qty_shipped': added_qty,
                        })
            return True




    #
    # def button_verify(self):
    #     if self.move_line_nosuggest_ids.qty_done > self.move_line_nosuggest_ids.product_uom_qty:
    #         raise UserError(_('Alert!, The %s Done Quantity should be equal or less than Demand Quantity. \n '
    #                           'Please Check it.')%self.name)
    #     else:
    #         self.write({'verify_stock': True})

    # def button_validate(self):
    #     if self.picking_type_id.code != 'outgoing':
    #         if self.picking_type_id.code != 'internal':
    #             if self.picking_type_id.code != 'mrp_operation':
    #                 if self.picking_type_id.code != 'mrp_operation' and not self.gate_entry_id and self.picking_type_id.warehouse_id.activate_gate_entry:
    #                     raise ValidationError('Gate Entry Not Done')

    # if self.picking_type_id.code == 'incoming' and self.picking_type_id.warehouse_id.activate_gate_entry:
    #     for each in self.move_ids_without_package:
    #         if self.purchase_id:
    #             if each.purchase_line_id.qty_received >= each.purchase_line_id.product_qty:
    #                 each.purchase_line_id.write({'purchase_order_line_done': True})
    #             else:
    #                 each.purchase_line_id.write({'purchase_order_line_done': False})
    #         # elif self.sale_id:
    #         #     if each.sale_line_id.qty_delivered <= each.sale_line_id.product_uom_qty:
    #         #         each.sale_line_id.write({'sale_order_line_inward_done': True})
    #         #     else:
    #         #         each.sale_line_id.write({'sale_order_line_inward_done': False})

    # if self.picking_type_id.code == 'outgoing':
    #     for each in self.move_ids_without_package:
    #         if self.sale_id:
    #             if each.sale_line_id.qty_delivered >= each.sale_line_id.product_uom_qty:
    #                 each.sale_line_id.write({'sale_order_line_done': True})
    #             else:
    #                 each.sale_line_id.write({'sale_order_line_done': False})
    # res = super(StockPicking,self).button_validate()
    # return res


class StockPicking(models.Model):
    _name = "purchase.gate"
    _description = 'Section Details'

    gate_entry_id = fields.Many2one('gate.entry', copy=False)
    order_id = fields.Many2one('purchase.order', 'Purchase Order')
    picking_id = fields.Many2one('stock.picking', 'Stock Picking')
    product_id = fields.Many2one('product.product', 'Product')
    origin = fields.Char('Origin')
    price_after_discount = fields.Float('Price After Discount')
    product = fields.Char('Product Name')
    product_qty = fields.Float('Quantity')
    received = fields.Float('Received')
    invoiced = fields.Float('Billed')
    onhand_quantity = fields.Float('OnHand Quantity')
    unity_price = fields.Float('Price')
    discount = fields.Float('Discount')
    discount_amount = fields.Float('Discount Amount')
    price_subtotal = fields.Char(string="Sub Total")
    gate_line_id = fields.Many2one('gate.entry.line', string='Gate Line Id')
    purchase_order_inward_ids = fields.Many2many("purchase.order", string="Purchase Entry")

    def unlink(self):
        return super(StockPicking, self).unlink()


class StockPicking(models.Model):
    _name = "stock.picking.gate.entry"
    _description = 'Stock Picking Details'

    gate_entry_id = fields.Many2one('gate.entry', copy=False)
    picking_id = fields.Many2one('stock.picking', 'Stock Picking')
    product = fields.Char('Product Name')
    product_id = fields.Many2one('product.product', 'Product')
    price_after_discount = fields.Float('Price After Discount')
    product_uom_qty = fields.Float('Demand')
    # z_supplier_rate = fields.Float('Supplier Rate')


# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     customer = fields.Boolean(string='Customer')
#     supplier = fields.Boolean(string='Supplier')


# class Partner(models.Model):
#     _name = 'res.partner'
#     _inherit = 'res.partner'
#
#     customer = fields.Boolean(string='Customer')
#     supplier = fields.Boolean(string='Supplier')

class HoDepartment(models.Model):
    _name = "ho.department"
    _description = "Ho Department"

    name = fields.Char(string='Depatment')
