from odoo import api, fields, models


class LeaseCloseReason(models.Model):
    _name = 'approval.refuse'
    _description = 'Approval Refuse Reason'

    refusetype = fields.Selection([
        ('permanent', 'Permanent'),
        ('partial', 'Partial'),
    ], string="Refuse Type", required=True)
    refusereason = fields.Text(string="Reason")

    def action_refuse(self, approver=None):
        for rec in self:
            approval = rec.env['approval.request'].browse(rec.env.context.get('active_ids'))
            if not isinstance(approver, models.BaseModel):
                approver = approval.mapped('approver_ids').filtered(
                    lambda approver: approver.user_id == approval.env.user
                )
            approver.write({'status': 'refused'})

