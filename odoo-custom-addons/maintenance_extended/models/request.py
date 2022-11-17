from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from datetime import date
import re


class Request(models.Model):
    _inherit = "maintenance.request"

    image = fields.Image(string="Image")
    machine_id = fields.Char(string="Equipment Name", related='equipment_id.name')
    subcat_id = fields.Many2one('subcate.details', related='equipment_id.subcategory_id', string=' Sub Category',
                                store=True, readonly=True)

    # machine_id = fields.Char(string=' Equipment ID', readonly=True)

    @api.onchange('equipment_id')
    def equipments_id(self):
        if self.equipment_id:
            self.image = self.equipment_id.image
            # self.machine_id = self.equipment_id.codefor.name
