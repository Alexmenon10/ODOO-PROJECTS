# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date


PAYMENT_STATE_SELECTION = [
        ('not_paid', 'Not Paid'),
        ('in_payment', 'Paid'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
]

class AccountMove(models.Model):
    _inherit = 'account.move'

    picking_id = fields.Many2one('stock.picking', string='Picking')
    payment_state = fields.Selection(PAYMENT_STATE_SELECTION, string="Payment Status", store=True,
                                     readonly=True, copy=False, tracking=True, compute='_compute_amount')
    state = fields.Selection(selection_add=[
            ('draft', 'Draft'),
            ('validate', 'Validate'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True, ondelete={'draft': 'set default', 'validate':'set default'})
    account_invoice_validate_reason = fields.Text('Invoice Validation Remarks')
    inovice_validate_date = fields.Char('Invoice Validation Date')


    def action_post(self):
        domain = [('picking_type_id.code', '=', 'incoming'), ('name', '=', self.payment_reference)]
        delivery_ids = self.env['stock.picking'].search(domain)
        if self.payment_id:
            self.payment_id.action_post()
        else:
            self._post(soft=False)
        for delivery in delivery_ids:
            if delivery.state == 'done':
                if delivery.supplier_invoice_no:
                    break
                else:
                    delivery.write({'supplier_invoice_no': self.name,'bill_date':self.invoice_date})
                    break
        return False


    def action_invoice_validate(self):
        for indent in self:
            for pro in indent.invoice_line_ids:
                if pro.product_id and pro.price_unit == 0.00:
                    raise UserError('Alert!!,  Mr.%s ,  \nPlease Enter the Unit Price For the Product %s .' % (
                        self.env.user.name, pro.product_id.name))
                else:
                    self.write({
                        'state': 'validate',
                        # 'account_invoice_validate_reason': self.env.user.name,
                        # 'inovice_validate_date': datetime.now()
                    })


class AccountTax(models.Model):
    _inherit = 'account.tax'

    name = fields.Char(string='Tax Name', required=False)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    disc = fields.Float(string='Discount', digits='Payment Terms')
    disc_percentage = fields.Float(string='Discount Amount')
    discount = fields.Float(string='Disc %', readonly=False)

    @api.onchange('disc')
    def discount_price_subtotal_new(self):
        for val in self:
            try:
                discount_percent = (val.disc / val.price_unit)
                profitpercentage = discount_percent * 100
            except ZeroDivisionError:
                discount_percent = 0.00
                profitpercentage = discount_percent * 100
            val.update({
                'discount': profitpercentage,
            })

    @api.onchange('discount')
    def _price_subtotal_discount(self):
        for val in self:
            try:
                discount_percent = (val.discount / 100)
                profitpercentage = discount_percent * val.price_unit
            except ZeroDivisionError:
                discount_percent = 0.00
                profitpercentage = discount_percent * 100
            val.update({
                'disc': profitpercentage,
            })
