# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ItemGroup(models.Model):
    _name = "make.name.group"
    _description = "Make name Group"
    _sql_constraints = [('code_unique', 'unique(code)', 'code already exists!')]

    name = fields.Char()
    code = fields.Char()

class Make_Item_View(models.Model):
    _inherit = "product.template"

    make_item = fields.Many2one('make.name.group', ondelete='restrict', string="Make Name")

# class StockPicking(models.Model):
#     _inherit= 'stock.picking'
#
#     order_sale_id = fields.Integer(compute='set_order_acc',store=True)
#     # z_order_types = fields.Char(string='Order Type',store=True)
#     # order_types = fields.Char(string="Document Type")
#
#     @api.depends('sale_id')
#     def set_order_acc(self):
#         for rec in self:
#             if rec.sale_id:
#                 rec.order_sale_id = rec.sale_id.id
#             else:
#                 rec.order_sale_id = False

# class PurchaseOrder(models.Model):
#     _inherit = 'purchase.order'

#     order_type = fields.Many2one('purchase.order.type','Document Type')

#     def _prepare_picking(self):
#     	data = super(PurchaseOrder, self)._prepare_picking()
#     	data['order_types'] = self.order_type.name
#     	return data