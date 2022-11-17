from odoo import api, fields, models, _


class ApprovalTravel(models.Model):
    _name = "approval.travel"
    _description = 'Approval Travel'

    source = fields.Char(string="From")
    distination = fields.Char(string="To")
    travel_date = fields.Date(string="Travel Date")
    approval_list_id = fields.Many2one('approval.request', string="Approvals")

    pre_approval_from = fields.Char(string='From')
    pre_approval_to = fields.Char(string='To')
    pre_approval_travel_date = fields.Date(string="Date")


class ApprovalTravelWizard(models.Model):
    _name = "approval.travel.wizard"
    _description = 'Approval Travel Wizard'


    source = fields.Char(string="From", store=True)
    distination = fields.Char(string="To", store=True)
    travel_date = fields.Date(string="Travel Date", store=True)

class VehicleType(models.Model):
    """Model Vehicle Type."""

    _name = 'vehicle.type'
    _description = 'Vehicle Type'

    code = fields.Char(string='Code', translate=True)
    name = fields.Char(string='Sub Product', required=True)
    product = fields.Many2one('product.product',string='Product', required=True)
