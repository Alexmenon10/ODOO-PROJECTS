
from odoo import api, fields, models,_


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _add_supplier_to_product(self):
        """ Insert a mapping of products to PO lines to be picked up
        in supplierinfo's create() """
        self.ensure_one()
        po_line_map = {
            line.product_id.product_tmpl_id.id: line for line in self.order_line
        }
        return super(
            PurchaseOrder, self.with_context(po_line_map=po_line_map)
        )._add_supplier_to_product()

    def action_apply_discount_wizard(self):
        view_id = self.env.ref('purchase_discount.purchase_order_discount_wizard_form_view').id

        return {
            'name': _('Update Discount'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order.discount.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
            }
        }

    amount_discount = fields.Float(string="Amount discounted", compute="calculate_amount_discounted", store=1)

    @api.depends('order_line')
    def calculate_amount_discounted(self):
        for r in self:
            sum = 0
            for l in r.order_line:
                #  sum = sum + (l.price_subtotal* l.discount/100)
                sum = sum + l.price_unit * ((l.discount or 0.0) / 100.0) * l.product_qty
                r.amount_discount = sum


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # adding discount to depends
    @api.depends("discount")
    def _compute_amount(self):
        return super()._compute_amount()

    def _prepare_compute_all_values(self):
        vals = super()._prepare_compute_all_values()
        vals.update({"price_unit": self._get_discounted_price_unit()})
        return vals

    discount = fields.Float(string="Dis (%)", digits="Discount")
    discount_amount = fields.Float(string="Dis(Amt)")
    price_after_discount = fields.Float(string="Price after Dis")

    _sql_constraints = [
        (
            "discount_limit",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    @api.onchange('product_qty','price_subtotal')
    def onchange_discount_after_price(self):
        for l in self:
            if l.product_qty>0 and l.price_unit>0: 
                l.price_after_discount = round(l.price_subtotal/l.product_qty,2)

    def _get_discounted_price_unit(self):
        """Inheritable method for getting the unit price after applying
        discount(s).

        :rtype: float
        :return: Unit price after discount(s).
        """
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit

    def _get_stock_move_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.

        HACK: This is needed while https://github.com/odoo/odoo/pull/29983
        is not merged.
        """
        price_unit = False
        price = self._get_discounted_price_unit()
        if price != self.price_unit:
            # Only change value if it's different
            price_unit = self.price_unit
            self.price_unit = price
        price = super()._get_stock_move_price_unit()
        if price_unit:
            self.price_unit = price_unit
        return price

    @api.onchange("product_qty", "product_uom")
    def _onchange_quantity(self):
        """
        Check if a discount is defined into the supplier info and if so then
        apply it to the current purchase order line
        """
        res = super()._onchange_quantity()
        if self.product_id:
            date = None
            if self.order_id.date_order:
                date = self.order_id.date_order.date()
            seller = self.product_id._select_seller(
                partner_id=self.partner_id,
                quantity=self.product_qty,
                date=date,
                uom_id=self.product_uom,
            )
            self._apply_value_from_seller(seller)
        return res

    @api.model
    def _apply_value_from_seller(self, seller):
        """Overload this function to prepare other data from seller,
        like in purchase_triple_discount module"""
        if not seller:
            return
        self.discount = seller.discount

    def _prepare_account_move_line(self, move):
        vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        vals["discount"] = self.discount
        return vals

    @api.onchange('discount')
    def onchange_discount(self):
        if self.discount:
            self.discount_amount = self.price_unit * ((self.discount or 0.0) / 100.0) * self.product_qty
       
            
    @api.onchange('discount_amount')
    def onchange_discount_amount(self):
        if self.discount_amount:
            self.discount = (self.discount_amount / (self.price_unit * self.product_qty))*100

class StockMove(models.Model):
    _inherit = 'stock.move'

    price_after_discount = fields.Float(compute="compute_price_after_discount")

    @api.depends('purchase_line_id')
    def compute_price_after_discount(self):
        for l in self:
            if l.purchase_line_id:
                l.price_after_discount = l.purchase_line_id.price_after_discount
            else:
                l.price_after_discount = False




