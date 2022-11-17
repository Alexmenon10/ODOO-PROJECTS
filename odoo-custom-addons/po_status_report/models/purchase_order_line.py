from odoo import fields,models,api, _

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    z_po_order_date = fields.Datetime(related="order_id.date_order",string="Date Order")
    z_status = fields.Char('Document Status',store=True,compute='_compute_status_type')
    z_currency_id = fields.Many2one('res.currency',' Currency',related="order_id.currency_id")
    remaining_qty = fields.Float("Pending Qty",compute="_qty_remaining",store=True)

    @api.depends('qty_received','product_qty')
    def _qty_remaining(self):
        for each in self:
            if each.product_qty and each.qty_received:
                each.remaining_qty = each.product_qty- each.qty_received
            else:
                each.remaining_qty = 0.0



    @api.depends('qty_received','qty_invoiced','product_qty')
    def _compute_status_type(self):
    	for line in self:
    		if line.qty_received == line.product_qty == line.qty_invoiced:
    			line.z_status = 'GRN & Invoice Done'
    		if line.product_qty == line.qty_received and line.qty_invoiced == 0:
    			line.z_status = 'Pending for Invoice'
    		if line.product_qty == line.qty_received and line.qty_invoiced != 0 and line.qty_received != line.qty_invoiced:
    			line.z_status = 'Partial Invoice Done'
    		if line.product_qty != 0 and line.qty_received == 0:
    			line.z_status = 'Pending for GRN'
    		if line.product_qty != line.qty_received and line.qty_received != 0:
    			line.z_status = 'Partial GRN'



