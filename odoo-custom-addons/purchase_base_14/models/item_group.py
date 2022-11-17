from odoo import models, fields, api, _
import itertools

class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    item_group = fields.Many2one('item.group')
    product_group_1 = fields.Many2one('product.group.1')
    product_group_2 = fields.Many2one('product.group.2')
    product_group_3 = fields.Many2one('product.group.3')

    def _select(self):
        return super(PurchaseReport, self)._select() + ", t.item_group as item_group,t.product_group_1 as product_group_1,t.product_group_2 as product_group_2,t.product_group_3 as product_group_3"
    
    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ",t.item_group ,t.product_group_1,t.product_group_2 ,t.product_group_3"
