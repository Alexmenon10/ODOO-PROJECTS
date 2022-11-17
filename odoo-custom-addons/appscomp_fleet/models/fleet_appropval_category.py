from odoo import api, fields, models, _

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    source_location = fields.Selection(CATEGORY_SELECTION, string="Source Location", default="no", required=True)
    has_trip = fields.Selection(CATEGORY_SELECTION, string="Trip", default="no", required=True)
    fleet_control = fields.Selection(CATEGORY_SELECTION, string="Fleet", default="no", required=True)
    vehicle_related_approval = fields.Boolean(string='Vehicle Related Approval ?')


