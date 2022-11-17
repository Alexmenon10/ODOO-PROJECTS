from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean(string='Customer')
    is_supplier = fields.Boolean(string='Supplier')