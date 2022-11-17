# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        if self.picking_type_code == 'incoming' and self.env.user.has_group('grn_validation_access.disallow_grn_validation'):
            raise ValidationError(_("""You are not authorized to Validate"""))
        return super(StockPicking, self).button_validate()
