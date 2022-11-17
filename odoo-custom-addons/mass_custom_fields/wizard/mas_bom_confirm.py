# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import pdb


class Mrpbomline_inherit(models.TransientModel):
    _inherit= 'mrp.bom.wizard'


    mrp_bom_id = fields.Many2one('mrp.bom')


    def caliculate_qty_sf(self):
        if self.bom_line_ids:
            # pdb.set_trace()
            for bom_line in self.bom_line_ids:
                curr_length = 0.0
                curr_width = 0.0
                if not self.product_id.id:
                    current_product_id = self.env['product.product'].search([('product_tmpl_id','=',self.product_tmpl_id.id)])
                else:
                    current_product_id = self.product_id


                if bom_line.z_select_board == True:
                    curr_length= current_product_id.product_dimension_ids.length/304.8
                    curr_width= current_product_id.product_dimension_ids.width/304.8
                if bom_line.z_select_board == True and curr_length and curr_width:
                    bom_line.product_qty =curr_length *curr_width * self. product_qty

