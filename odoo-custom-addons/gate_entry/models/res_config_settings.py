#-*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    inward_sequence = fields.Many2one("ir.sequence", string="Inward Sequence")
    outward_sequence = fields.Many2one("ir.sequence", string="Outward Sequence")
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            inward_sequence = int(params.get_param('gate_entry.inward_sequence')),
            outward_sequence = int(params.get_param('gate_entry.outward_sequence')),
        )
        return res

    def set_values(self):
        super(ResConfigSettings,self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('gate_entry.inward_sequence',self.inward_sequence.id)
        self.env['ir.config_parameter'].sudo().set_param('gate_entry.outward_sequence',self.outward_sequence.id)

