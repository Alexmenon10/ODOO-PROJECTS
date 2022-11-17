# -*- coding: utf-8 -*-

from collections import namedtuple
import json
import time

from itertools import groupby
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from operator import itemgetter
import pdb
class Picking(models.Model):
    _inherit = "stock.picking"

    z_show_supplier = fields.Boolean(compute="_compute_show")


    @api.depends('origin')
    def _compute_show(self):
        for line in self:
            if line.purchase_id:
                line.z_show_supplier = True
            else:
                line.z_show_supplier = False


    def button_validate(self):
        if self.purchase_id:
            for move_line in self.move_lines:
                for po_line in self.purchase_id.order_line:
                    if move_line.quantity_done != 0:
                        if po_line.discount == 0:
                            if move_line.product_id.id == po_line.product_id.id and move_line.z_supplier_rate != po_line.price_unit :
                                raise UserError(_('Purchase Order price and supplier invoice price are not matching , kindly revise the PO price .'))
                        else:
                            if move_line.product_id.id == po_line.product_id.id and move_line.z_supplier_rate != round(po_line.price_subtotal / po_line.product_qty,2) :
                                raise UserError(_('Purchase Order price and supplier invoice price are not matching , kindly revise the PO price .'))
        
        return super(Picking, self).button_validate()
