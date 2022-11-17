    # -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import pdb
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    material_request_id = fields.Many2one('material.request')


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    material_request_id = fields.Many2one('material.request')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mr_sequence = fields.Many2one('ir.sequence',string="Material Request Sequence")

    def set_values(self):
        super(ResConfigSettings,self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('material_request.mr_sequence',self.mr_sequence.id)
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            mr_sequence = int(params.get_param('material_request.mr_sequence'))
        )
        return res

class MaterialRequest(models.Model):
    _name = 'material.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Material Request'

    name = fields.Char('Sequence')

    picking_type_id = fields.Many2one('stock.picking.type', string="Operation Type")
    source_location_id = fields.Many2one('stock.location')
    dest_location_id = fields.Many2one('stock.location')

    purchase_request_type_id = fields.Many2one('purchase.requisition.type')

    material_request_line_ids = fields.One2many('material.request.line','material_request_id')

    # mrp_ids = fields.Many2many('mrp.production', string="Manufacturing Orders")

    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('closed','Closed')], default='draft')

    transfer_count = fields.Integer()

    # @api.depends('material_request_line_ids')
    def _count_transfers(self):
        for rec in self:
            transfer_count = len(rec.material_request_line_ids.mapped('transfer_order_ids'))
    
    def action_mr_picking(self):
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action['views'] = [
            (self.env.ref('stock.vpicktree').id, 'tree'),(self.env.ref('stock.view_picking_form').id,'form')
        ]
        action['context'] = self.env.context
        action['domain'] = [('material_request_id', '=', self.id)]
        return action
    
    def action_mr_purchase(self):
        action = self.env["ir.actions.actions"]._for_xml_id("purchase_base_14.action_purchase_requisition_purchase_base")
        action['views'] = [
            (self.env.ref('purchase_requisition.view_purchase_requisition_tree').id, 'tree'),(self.env.ref('purchase_requisition.view_purchase_requisition_form').id,'form')
        ]
        action['context'] = self.env.context
        action['domain'] = [('material_request_id', '=', self.id)]
        return action

    def confirm(self):
        self.state = 'confirmed'
    
    def close(self):
        self.state = 'closed'
    
    def reset(self):
        self.state = 'draft'

    def process_all(self):
        for rec in self:
            if rec.material_request_line_ids:
                for each_line in rec.material_request_line_ids:
                    each_line.write({'request_qty': each_line.planned_qty})


    @api.onchange('picking_type_id')
    def _get_default_location(self):
        self.source_location_id = self.picking_type_id.default_location_src_id.id
        self.dest_location_id = self.picking_type_id.default_location_dest_id.id

    # @api.onchange('mrp_ids')
    # def _get_lines_from_mrp(self):
    #     self.material_request_line_ids = [(2, line.id, 0) for line in self.material_request_line_ids.filtered(lambda req: req.source_id.id != False)]+\
    #         [(0, 0, {
    #             'product_id' : mrp_line.product_id.id,
    #             'planned_qty' : mrp_line.product_uom_qty - mrp_line.reserved_availability,
    #             'source_id' : mrp_line.raw_material_production_id.id
    #         }) for mrp_line in self.mrp_ids.mapped('move_raw_ids').filtered(lambda move: move.reserved_availability != move.product_uom_qty)]
    #

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].browse(int(self.env['ir.config_parameter'].sudo().get_param('material_request.mr_sequence')))
        vals['name'] = self.env['ir.sequence'].next_by_code(sequence.code)
        return super(MaterialRequest, self).create(vals)

    def request_material(self):
        moves = self.material_request_line_ids
       
        operations = []
        for move in moves:
            operations.append((move.picking_type_id.id,move.source_location_id.id,move.dest_location_id.id))
            print(operations)
        operations = set(operations)

        for operation in operations:
            print("operationoperationoperation",operation)
            print(operation[1],"==================source location")
            if operation[0]:
                picking = {
                    'material_request_id' : self.id,
                    'picking_type_id' : operation[0],
                    'location_id' : operation[1],
                    'location_dest_id' : operation[2],
                    'move_ids_without_package' : []
                }
                stock_moves = moves.filtered(lambda mov: mov.picking_type_id.id ==  operation[0] and mov.source_location_id.id == operation[1] and mov.dest_location_id.id == operation[2] and mov.request_qty and not mov.transfer_order_ids)
                for stock_move in stock_moves:
                    picking['move_ids_without_package'].append((0, 0,{
                        'product_id' : stock_move.product_id.id,
                        'name' : stock_move.product_id.partner_ref,
                        'product_uom_qty' : stock_move.request_qty,
                        'product_uom' : stock_move.product_id.uom_id.id,
                        'location_id':operation[1],
                        'location_dest_id':operation[2],
                        'mr_line_id' : stock_move.id
                    }))
                    print(picking['move_ids_without_package'],"===============================ppppp")
                    if stock_move.request_type != 'purchase':
                        stock_move.requested_qty += stock_move.request_qty
                        stock_move.request_qty = 0
            
                if len(stock_moves):
                    picking = self.env['stock.picking'].create(picking)
                    for move in picking.move_ids_without_package:
                        move.mr_line_id.transfer_order_ids = [(4, move.picking_id.id, 0)]
                self._count_transfers

        
        plines = self.material_request_line_ids.filtered(lambda req: req.request_type == 'purchase')
        prequests = []
        for pline in plines:
            prequests.append(pline.purchase_request_type_id.id)
        prequests = set(prequests)

        for prequest in prequests:
            purchase = {
                'material_request_id' : self.id,
                'type_id' : prequest,
                'line_ids' : []
            }
        
            purchase_lines = plines.filtered(lambda lin: lin.purchase_request_type_id.id == prequest and lin.request_qty and not lin.purchase_request_ids ,)
            for purchase_line in purchase_lines:
                purchase['line_ids'].append((0, 0,{
                    'product_id': purchase_line.product_id.id,
                    'product_uom_id' : purchase_line.product_id.uom_id.id,
                    'product_qty' : purchase_line.request_qty,
                    'on_hand_qty_req' : purchase_line.available_qty,
                    'mr_line_id' : purchase_line.id
                }))
                purchase_line.requested_qty += purchase_line.request_qty
                purchase_line.request_qty = 0
            
            if len(purchase_lines) :
                purchase = self.env['purchase.requisition'].create(purchase)
                for line in purchase.line_ids:
                    line.mr_line_id.purchase_request_ids = [(4, line.requisition_id.id, 0)]


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'
    _description = 'Material Request Line'

    material_request_id = fields.Many2one('material.request')

    # source_id = fields.Many2one('mrp.production', string="source id")
    # source = fields.Many2one('mrp.production',compute='_get_src')
    # @api.depends('source_id')
    # def _get_src(self):
    #     for rec in self:
    #         rec.source = rec.source_id.id

    picking_type_id = fields.Many2one('stock.picking.type', string="Operation Type")
    source_location_id = fields.Many2one('stock.location')
    dest_location_id = fields.Many2one('stock.location')
    
    purchase_request_type_id = fields.Many2one('purchase.requisition.type')
    
    product_id = fields.Many2one('product.product')

    available_qty = fields.Float(related='product_id.qty_available')
    forcast_qty = fields.Float(related='product_id.virtual_available')

    planned_qty = fields.Float(string="Qty")
    requested_qty = fields.Float(readonly=True, string="Qty Shipped")
    request_qty = fields.Float(string="Qty To Ship")
    request_type = fields.Selection([('stock','Internal Transfer'),('purchase','Purchase Request')],default='stock')
    
    transfer_order_ids = fields.Many2many('stock.picking', readonly=True)
    purchase_request_ids = fields.Many2many('purchase.requisition', readonly=True)

    def unlink(self):
        for each in self:
            if each.requested_qty:
                raise UserError(_("Keep Calm and don't delete Request after processing"))
        return super(MaterialRequestLine, self).unlink()

    # @api.constrains('request_qty')
    # def _check_something(self):
    #     for rec in self:
    #         if rec.request_qty > rec.planned_qty - rec.requested_qty:
    #             raise ValidationError(_("Keep Calm and don't process more quantity than planned"))


    @api.onchange('picking_type_id')
    def _get_default_location(self):
        if self.request_type == 'stock':
            print("onchangeonchange",self.request_type)
            self.source_location_id = self.picking_type_id.default_location_src_id.id
            self.dest_location_id = self.picking_type_id.default_location_dest_id.id

    
    @api.model
    def create(self, vals):
        mr = self.env['material.request'].browse(vals.get('material_request_id'))
        if not vals['picking_type_id'] and  vals['request_type'] == 'stock':
            vals['picking_type_id'] = mr.picking_type_id.id
        if not vals['source_location_id'] and  vals['request_type'] == 'stock':
            vals['source_location_id'] = mr.source_location_id.id
        if not vals['dest_location_id'] and  vals['request_type'] == 'stock':
            vals['dest_location_id'] = mr.dest_location_id.id
        if vals.get('request_type') == 'purchase':
            if not vals.get('purchase_request_type_id'):
                vals['purchase_request_type_id'] = mr.purchase_request_type_id.id

        return super(MaterialRequestLine, self).create(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    mr_line_id = fields.Many2one('material.request.line')

class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    mr_line_id = fields.Many2one('material.request.line')