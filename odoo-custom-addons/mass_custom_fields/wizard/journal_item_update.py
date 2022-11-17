# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models
import pdb



    

class Mrp_bom_line(models.TransientModel):
    _name = 'mrp.bom.line.wizard'
    _description = 'Mrp Bom Line'

    bom_id = fields.Many2one(
        comodel_name='mrp.bom',
        string='BOM'
    )

    def product_qty_update(self):
        # pdb.set_trace()
        if self._context.get('active_ids') :
            bom_ids = self._context.get('active_ids')
            for each_bom in bom_ids:
                mrpbomObj = self.env['mrp.bom'].browse(each_bom)
                mrpbomObj.caliculate_qty_sf()
                # journal_id = JournalItemObj.move_id
                # journal_id.button_cancel()
                # JournalItemObj.write({
                #     'account_id': self.account_id.id
                # })
                # journal_id.post()
