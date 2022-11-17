# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductCategory(models.Model):
    _inherit = "product.category"

    internal_reference_sequence_id = fields.Many2one('ir.sequence')


class ProductTemplate(models.Model):
    _inherit = "product.template"

    internal_reference_sequence = fields.Boolean(store=True,compute='compute_internal_reference')
    default_code = fields.Char(tracking=True)
    list_price = fields.Float(tracking=True)
    standard_price = fields.Float(tracking=True)
    categ_id = fields.Many2one(tracking=True)

    @api.depends('categ_id')
    def compute_internal_reference(self):
    	for line in self:
    		if line.categ_id.internal_reference_sequence_id:
    			line.internal_reference_sequence = True
    		else:
    			line.internal_reference_sequence = False

    @api.model
    def create(self,vals):
        sequence = self.env['product.category'].browse(vals.get('categ_id')).internal_reference_sequence_id
        if sequence:
            vals['default_code'] = sequence.next_by_id()
        
        return super(ProductTemplate,self).create(vals)