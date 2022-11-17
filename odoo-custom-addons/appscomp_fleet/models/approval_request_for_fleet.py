from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta, datetime


class ApprovalRequest(models.Model):
    _inherit = "approval.request"


    approval_fleet_status = fields.Selection([
        ('open', 'Open'),
        ('close', 'Close')],string="Approval Status",default='open')
    pre_define_purpose = fields.Many2one('pre.define.purpose', string='Pre Defined Purpose')
    manual_purpose = fields.Char(string="Purpose")
    approval_trip_type = fields.Selection([
        ('one_way', 'One Way Trip'),
        ('rounded_trip', 'Rounded Trip')],string="Trip Status",default='rounded_trip')
    one_way_trip_reamrk = fields.Text('Remarks')
    one_way_attachment = fields.Binary(String="Attachments")
    one_way_attachment_detail = fields.Char(string="Attachment")

    def get_one_way_trip_wizard(self):
        view_id = self.env['one.way.trip']
        return {
            'type': 'ir.actions.act_window',
            'name': 'One Way Trip',
            'res_model': 'one.way.trip',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('appscomp_fleet.one_way_trip_wizard', False).id,
            'target': 'new',
        }


class PreDefinePurpose (models.Model):
    _name = 'pre.define.purpose'
    _description = "Pre Define Purpose"

    name = fields.Char(string='Pre Define Purpose')