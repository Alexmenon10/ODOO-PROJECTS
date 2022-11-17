from odoo import api, fields, models, _

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    request_to_partial_refused_validate_count = fields.Integer(compute='_compute_request_to_partial_refused_validate_count',
                                                               string='umber of requests to Partial Refused Validate',
                                             default=0)
    source_location = fields.Selection(CATEGORY_SELECTION, string="Source Location", default="no", required=True)
    has_vechicle = fields.Selection(CATEGORY_SELECTION, string="Vechicle Type", default="no", required=True)
    has_vechicle_specification = fields.Selection(CATEGORY_SELECTION, string="Vechicle Specification", default="no", required=True)
    has_estimate_amount = fields.Selection(CATEGORY_SELECTION, string="Estimate Amount", default="no", required=True)
    has_borrow_approval = fields.Selection(CATEGORY_SELECTION, string="Borrow", default="no", required=True)
    has_priority = fields.Selection(CATEGORY_SELECTION, string="Priority", default="no", required=True)
    has_payment = fields.Selection(CATEGORY_SELECTION, string="Payment Request", default="no", required=True)
    has_procurment = fields.Selection(CATEGORY_SELECTION, string="Procurment", default="no", required=True)
    has_trip = fields.Selection(CATEGORY_SELECTION, string="Trip", default="no", required=True)


    def _compute_request_to_partial_refused_validate_count(self):
        domain = [('request_status', '=', 'partial_refused'), ('request_owner_id', '=', self.env.user.id)]
        requests_data = self.env['approval.request'].read_group(domain, ['category_id'], ['category_id'])
        requests_mapped_data = dict((data['category_id'][0], data['category_id_count']) for data in requests_data)
        for category in self:
            category.request_to_partial_refused_validate_count = requests_mapped_data.get(category.id, 0)
            self.env['approval.request'].write({'request_status': 'new'})

