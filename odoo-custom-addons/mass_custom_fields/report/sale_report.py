from odoo import models, fields, api, _
from odoo import tools

class SaleReport(models.Model):
    _inherit = "sale.report"

    qty_pending = fields.Float(string='Qty Pending')
    open_order_value = fields.Float(string='Open Order Value')
    disptach_value = fields.Float(string='Disptach Value')
    total_order_value = fields.Float(string='Total Order Value')
    partner_state = fields.Many2one('res.country.state',string='State')

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['qty_pending'] = ',(l.product_uom_qty - l.qty_delivered) as qty_pending'
        fields['open_order_value'] = ',(l.price_subtotal - l.untaxed_amount_invoiced) as open_order_value'
        fields['disptach_value'] = ',l.untaxed_amount_invoiced as disptach_value'
        fields['partner_state'] = ',partner.state_id as partner_state'
        fields['total_order_value'] = ',l.price_subtotal as total_order_value'
        groupby += ', l.qty_pending'
        groupby += ', l.product_uom_qty'
        groupby += ', l.qty_delivered'
        groupby += ', l.open_order_value'
        groupby += ', l.price_subtotal'
        groupby += ', l.untaxed_amount_invoiced'
        groupby += ', s.partner_state'
        groupby += ', partner.state_id'
        groupby += ', l.total_order_value'
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

# class ResPartner(models.Model):
#     _inherit = 'res.partner'
#
#     mime_code = fields.Char(string="MSME Code")
