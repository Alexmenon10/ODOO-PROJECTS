# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DiscountWizard(models.TransientModel):
    _name = 'purchase.order.discount.wizard'
    _description = "Wizard: Apply discount to all purchase order lines"

    purchase_order_id = fields.Many2one('purchase.order', required=True, ondelete="cascade")
    discount = fields.Float(string="Discount (%)", digits="Discount", required=True)

    def button_confirm(self):
        for line in self.purchase_order_id.order_line:
            line.discount = self.discount