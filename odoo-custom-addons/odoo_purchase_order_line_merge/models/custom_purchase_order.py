# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.addons.purchase.models.purchase import PurchaseOrderLine, PurchaseOrder


class CustomPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def po_order_lines_merge(self):
        delete_lines = []
        order_lines = []

        for order_ids in self:
            for line in order_ids.order_line:
                order_lines.append(line.id)
                merge_lines = order_ids.order_line.search([('order_id', '=', order_ids.id),
                                                          #('price_unit', '=', line.price_unit),
                                                            ('taxes_id', '=', line.taxes_id.id),
                                                           ('product_id', '=', line.product_id.id),
                                                          ('account_analytic_id', '=', line.account_analytic_id.id),
                                                          ('id', 'not in', order_lines)], limit=1)
                if merge_lines:
                    delete_lines.append(line.id)
                    # line_origin = self.env['sale.order'].search([('id','=',line.order_id.id)]).name
                    # merge_lines_origin = self.env['sale.order'].search([('id','=',merge_lines.order_id.id)]).name
                    merge_lines.write({'product_qty': merge_lines.product_qty + line.product_qty,
                                       'price_unit': merge_lines.price_unit + line.price_unit})
        order_ids.write({'order_line': [(2, x, 0) for x in delete_lines]})


class CustomPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def unlink(self):
        return super(PurchaseOrderLine, self).unlink()


class AutoMergePurchaseOrderLine(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_merge_po = fields.Boolean("AutoMerge Warnings", implied_group='purchase.auto_merge_po',default=True)


class CustomPurchaseOrderLineSaveFun(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order', sequence_date=seq_date) or '/'
        lineorderobj = super(PurchaseOrder, self).create(vals)
        delete_lines = []
        order_lines = []
        checkflag = False
        for i in self.env['res.config.settings'].search([]):
            checkflag = i.auto_merge_po
        if checkflag:
            for order_ids in lineorderobj:
                for line in order_ids.order_line:
                    order_lines.append(line.id)
                    merge_lines = order_ids.order_line.search([('order_id', '=', order_ids.id),
                                                              # ('price_unit', '=', line.price_unit),
                                                               ('taxes_id', '=', line.taxes_id.id),
                                                               ('product_id', '=', line.product_id.id),
                                                              ('account_analytic_id', '=', line.account_analytic_id.id),
                                                              ('id', 'not in', order_lines)], limit=1)
                    if merge_lines:
                        delete_lines.append(line.id)
                        # line_origin = lineorderobj.env['sale.order'].search([('id', '=', line.order_id.id)]).name
                        # merge_lines_origin = lineorderobj.env['sale.order'].search([('id', '=', merge_lines.order_id.id)]).name
                        merge_lines.write({'product_qty': merge_lines.product_qty + line.product_qty,
                                       'price_unit': merge_lines.price_unit + line.price_unit})
            order_ids.write({'order_line': [(2, x, 0) for x in delete_lines]})

        return lineorderobj
