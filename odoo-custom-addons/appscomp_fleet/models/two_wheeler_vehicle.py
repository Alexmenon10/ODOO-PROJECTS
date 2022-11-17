from odoo import api, fields, models, _
from datetime import datetime


class TwoWheelerUsage(models.Model):
    _name = 'two.wheeler.usage'
    _description = "Store Vehicle Details"

    taken_by =  fields.Many2one('hr.employee', string='Taken By')
    place = fields.Char(string="Place")
    approved = fields.Char(string="Approved By")
    time_out = fields.Datetime(string="Time Out")
    time_in = fields.Datetime(string="Time In")
    opening_km = fields.Float(string="Opening KM")
    closing_km = fields.Float(string="Taken BY")
    net_km = fields.Float(string="Net Km")
    employee_sign = fields.Binary(string="Employee Sign ")
    security_sign = fields.Binary(string="Security Sign ")
    name = fields.Char(string='Reference', size=256, tracking=True, required=True, copy=False,
                      index=True, default=lambda self: _('/'),
                       help='A unique sequence number for the Indent')
    state = fields.Selection([('draft', 'Draft'), ('cancel', 'Cancelled'), ('approve', 'Approved'),
                              ('reject', 'Rejected')], 'State', default="draft", readonly=True, tracking=True)
    # vehicle_request_id = fields.Many2one('employee.fleet', string='Request')
    # vehicle_request_id = fields.Char(string='Request')


    def driver_beta_approve(self):
        self.write({'state': 'approve', 'approved': self._uid})

    def driver_beta_cancel(self):
        self.write({'state': 'cancel'})

    def driver_beta_reject(self):
        self.write({'state': 'reject'})

    @api.model
    def create(self, values):
        values['name'] = self.sudo().env['ir.sequence'].get('two.wheeler.usage') or '/'
        res = super(TwoWheelerUsage, self).create(values)
        return res

    @api.onchange('vehicle_request_id')
    def get_request_details(self):
        self.sudo().write({
            'taken_by': self.vehicle_request_id.employee.name,
        })




