#-*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import Warning, UserError, AccessError,ValidationError
import logging
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
    entry_type = fields.Selection(string='Entry Type', selection=[('in', 'Inward'),('out','Outward')])
    
    order_type_inward = fields.Selection(string=" Order type", selection=[ ('p','Purchase'), ('sr','Sales Return'),('others','Others')]) # p = purchase, sr = sales return, tin = transefer In
    order_type_outward = fields.Selection(string= "Order type",selection =[ ('s','Sale'), ('pr','Purchase Return'),('others','Others')]) # s = sales, pr = purchase return, t = transefer Out

    username = fields.Many2one("gate.user.registration")
    description = fields.Char()
    # item_description = fields.Char()
    doc_datetime = fields.Datetime("Document Date")
    post_datetime = fields.Datetime("Posting Date")
    lr_rr_no = fields.Char(string="LR/RR No.")
    lr_rr_date = fields.Datetime(string="LR/RR Date")
    vehicle_no = fields.Many2one('fleet.vehicle',string="Internal Vechile No.")
    external_vehicle_no = fields.Char(string="External Vechile No.")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse",domain=[('activate_gate_entry','=',True)])
    
    gate_line = fields.One2many('gate.entry.line', 'gate_id')
    station_from = fields.Char()
    station_to = fields.Char()
    stock_picking_id = fields.Many2one("stock.picking", "Challan No")
    stock_picking_date = fields.Datetime("Challan Date")
    stock_picking_line_ids = fields.One2many(
        "stock.move.inherit", "gate_in_id", "Item Description")
    origin = fields.Char("Source Doc")
    supplier_id = fields.Many2one("res.partner", "Supplier Name")
    location_type_id = fields.Many2one('stock.picking.type', "Operational type-Warehouse")
    dest_location_id = fields.Many2one(
        'stock.location', "Destination Location")
    supplier_phone = fields.Char("Supplier Contact Number", related='supplier_id.phone')
    supplier_email = fields.Char("Supplier Email", related='supplier_id.email')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processed', 'Processed'),
        ('cancel', 'Cancel'),
    ], string='Status', default='draft')

    @api.constrains('warehouse_id')
    def vehicle_number(self):
        if not self.vehicle_no and not self.external_vehicle_no:
            raise UserError(_('Please Select Any Vehicle Number.'))

    @api.constrains('warehouse_id')
    def warehouse_name(self):
        if self.username:
            warehouse = self.warehouse_id
            if self.warehouse_id.id != self.username.warehouse_id.id:
                raise UserError(_('Your Not Authorised To Do Transaction In %s Warehouse.') % ', '.join(warehouse.mapped('name')))

    def unlink(self):
        for each_entry in self:
            if each_entry.state != 'draft':
                raise UserError(_('You cannot delete an entry which has been Processed once.'))
        return super(GateEntry, self).unlink()

    @api.model
    def create(self, vals):
        if (self.env.context['default_entry_type'] == 'in'):
            sequence_type =  vals.get('warehouse_id')
            sequence_type = self.env['stock.warehouse'].browse(sequence_type)
            if not sequence_type:
                raise Warning('Inward sequence is not set')
            else: 
                vals['name'] = sequence_type.inward_sequence.next_by_id()
                vals['post_datetime'] = fields.Datetime.now()
        else:
            sequence_type =  vals.get('warehouse_id')
            sequence_type = self.env['stock.warehouse'].browse(sequence_type)
            if not sequence_type:
                raise Warning('Outward sequence is not set')
            else:
                vals['name'] = sequence_type.outward_sequence.next_by_id()
                vals['post_datetime'] = fields.Datetime.now()

        return super(GateEntry, self).create(vals)


    def process(self):
        self.stock_picking_id.write({
            'gate_entry_id':self.id
        })
        for each in self.gate_line:
            if self.entry_type == 'in':
                if each.order_type_inward == 'p':
                    for l in each.purchase_order_inward_ids:
                        for picking in l.picking_ids.filtered(lambda e: e.picking_type_id.code == 'incoming'):
                            if picking.state != 'done':
                                picking.write({'gate_entry_id':self.id})

                if each.order_type_inward == 'sr':
                        for picking in each.sale_return_receipt_ids:
                            if picking.state != 'done':
                                picking.write({'gate_entry_id':self.id})

                if each.order_type_inward == 'others':
                    for l in each.other_inward:
                        for picking in l.filtered(lambda e: e.picking_type_id.code == 'incoming' or e.picking_type_id.code == 'internal' and e.location_id.usage == "inventory"):
                            if picking.state != 'done':
                                picking.write({'gate_entry_id':self.id})

            elif self.entry_type == 'out':
                if each.order_type_outward == 'others':
                    for l in each.other_outward:
                        for picking in l.filtered(lambda e: e.picking_type_id.code == 'outgoing' or e.picking_type_id.code == 'internal' and e.location_dest_id.usage == "inventory"):
                            if picking.state == 'done':
                                if not picking.gate_entry_id:
                                    picking.write({'gate_entry_id':self.id})

                if each.order_type_outward == 's':
                    for picking in each.purchase_return_receipt_ids:
                        if picking.state == 'done':
                            if not picking.gate_entry_id:
                                picking.write({'gate_entry_id':self.id})

                if each.order_type_outward == 'pr':
                    for picking in each.purchase_return_receipt_ids:
                        if picking.state == 'done':
                            picking.write({'gate_entry_id':self.id})
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

    @api.onchange('stock_picking_id')
    def on_change_select(self):
        values = {
            'stock_picking_date': self.stock_picking_id.scheduled_date or False,
            'supplier_id': self.stock_picking_id.partner_id and self.stock_picking_id.partner_id.id or False,
            'origin': self.stock_picking_id.origin or False,
            'location_type_id': self.stock_picking_id.picking_type_id and self.stock_picking_id.picking_type_id.id or False,
            'dest_location_id': self.stock_picking_id.location_dest_id and self.stock_picking_id.location_dest_id.id or False,
        }
        self.update(values)

    ##Get lines items from stock.picking to gate in form
    @api.onchange('stock_picking_id')
    def on_change_picking(self):
        res = self.env['stock.picking']
        val = res.move_ids_without_package.search([('picking_id', '=', self.stock_picking_id.name)])
        print(val.picking_id.name)
        r = [(5, 0, 0)]
        value = {}

        if self.stock_picking_id:
            for line in val:
                data = {'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_done_qty': line.quantity_done,
                        'product_uom': line.product_uom.name,
                        }
                print(data)
                r.append((0, 0, data))
            value.update(stock_picking_line_ids=r)
            return {'value': value}

class GateEntryLine(models.Model):
    _name = 'gate.entry.line'
    _description = 'Gate Entry Line'

    challan_no = fields.Char()
    challan_date = fields.Datetime()
    description = fields.Char(string='Item Description')
    
    gate_id = fields.Many2one('gate.entry', string='Gate Id')
    sequence = fields.Integer(default=10)
    
    # order_type_inward = fields.Selection(string="Order type", selection=[('p','Purchase'),('sr','Sales Return'),('scin','Sub-Contract'),('tout','Transfer')], domain="[('parent.entry_type', '=', 'out')]")
    # order_type_outward = fields.Selection(string= "Order type",selection =[('s','Sale'),('pr','Purchase Return'),('scout','Sub-Contract'),('tout','Transfer')], domain = "[('parent.entry_type', '=', 'in')]")

    entry_type = fields.Selection(related='gate_id.entry_type', store=True, readonly=False)

    order_type_inward = fields.Selection(related='gate_id.order_type_inward', store=True, readonly=False,string='Order Type')
    order_type_outward = fields.Selection(related='gate_id.order_type_outward', store=True, readonly=False,string=' Order Type')
    

    # warehouse_ids = fields.Many2one("stock.warehouse", string="Warehouse",domain=[('activate_gate_entry','=',True)],compute='compute_warehouse')

    purchase_order_inward_ids = fields.Many2one("purchase.order", string="Purchase Order")
    purchase_order_outward_ids = fields.Many2many("purchase.order", relation="purchase_order_outward_ids_rel", column1="gate_entry_id", column2="purchase_order_id", string=" Purchase Order")
    
    sale_order_inward_ids = fields.Many2many("sale.order", relation="sale_order_inward_ids_rel", column1="gate_entry_id", column2="sale_order_id", string="Sale Order")
    sale_order_outward_ids = fields.Many2many("sale.order", relation="sale_order_outward_ids_rel", column1="gate_entry_id", column2="sale_order_id", string=" Sale Order")
    
    # purchase_receipt_ids = fields.Many2many("stock.picking", realtion="purchase_receipt_ids_rel", column1="gate_entry_id", column2="stock_picking_id" , string= "Receipts")
    other_inward = fields.Many2one('stock.picking',string=' Others',store=True)
    other_outward = fields.Many2one('stock.picking',string='Others',store=True)
    purchase_return_receipt_ids = fields.Many2one("stock.picking", string=" Transfers")
    
    # sale_receipt_ids = fields.Many2many("stock.picking", relation="sale_receipt_ids_rel", column1="gate_entry_id", column2="stock_picking_id" , string= "Receipts")
    sale_return_receipt_ids = fields.Many2one("stock.picking", string= "Transfers")



    def unlink(self):
        for each_entry in self:
            if each_entry.gate_id.state != 'draft':
                raise UserError(_('You cannot delete an entry which has been Processed once.'))
        return super(GateEntryLine, self).unlink()

    @api.onchange('order_type_outward')
    def get_outward_filter(self):
        if self.order_type_outward == 'pr':
            return {'domain': {'purchase_return_receipt_ids':[('purchase_return','=',True),('picking_type_code','=','outgoing')]}}
        elif self.order_type_outward == 's':
            return {'domain': {'purchase_return_receipt_ids':[('purchase_return','!=',True),('picking_type_code','=','outgoing'),('gate_entry_id','=',False),('state','=','done'),('sale_id','!=',False)]}}

    @api.onchange('order_type_inward')
    def get_inward_filter(self):
        if self.order_type_inward == 'sr':
            return {'domain': {'sale_return_receipt_ids':[('purchase_return','=',True),('picking_type_code','=','incoming'),('gate_entry_id','=',False)]}}

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
    _inherit= "purchase.order"

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
    _inherit="stock.picking"

    gate_entry_id = fields.Many2one('gate.entry',copy=False)
    # gate_entry_purchase_outward_id = fields.Many2one('gate.entry',copy=False)
    purchase_return = fields.Boolean(store=True,compute='compute_purchase_return')
    purchase_boolean = fields.Boolean(string='Purchase Boolean',store=True,compute='compute_purchase_boolean')

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
        res = super(StockPicking,self).button_validate()
        if self.picking_type_id.code != 'outgoing': 
            if self.picking_type_id.code != 'internal':
                if self.picking_type_id.code != 'mrp_operation':
                    if self.picking_type_id.code != 'mrp_operation' and not self.gate_entry_id and self.picking_type_id.warehouse_id.activate_gate_entry:
                        raise ValidationError('Gate Entry Not Done')

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
        return res


class StockPickingInherit(models.Model):
    _name = 'stock.move.inherit'

    gate_in_id = fields.Many2one("gate.entry", "Gate In Entries")
    product_id = fields.Many2one(
        'product.product', 'Product', index=True, required=True)
    product_qty = fields.Float(
        'Quantity', default=0.0, required=True)
    product_done_qty = fields.Float(
        'Done Quantity', default=0.0, required=True)
    product_uom = fields.Char(
        'UoM')

