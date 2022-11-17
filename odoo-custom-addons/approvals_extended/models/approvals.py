# -*- coding: utf-8 -*-
from odoo import api,Command, fields, models
from collections import defaultdict
from odoo.exceptions import UserError,ValidationError


class ApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'

    approve_level = fields.Selection([('level1', '1st Approve'), ('level2', '2nd Approve'), ('level3', '3rd Approve')],
                                      string="Approve Level",required='1')

    required = fields.Boolean(default=True)

class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    approve_level = fields.Selection([('level1', '1st Approve'), ('level2', '2nd Approve'), ('level3', '3rd Approve')],
                                     string="Approve Level", required='1')


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'


    def action_approve(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            )
        approvers = self.mapped('approver_ids')
        if approver.approve_level == 'level1':
            approver.write({'status': 'approved'})

        for users in approvers:
            if approver.approve_level in ('level2','level3'):
                if users.approve_level == 'level1'  and users.status != 'approved':
                    raise ValidationError("You Cannot Approve this before %s"%(dict(users._fields['approve_level'].selection).get(users.approve_level)))
                if users.approve_level == 'level2' and  approver.approve_level not in ('level1','level2') and users.status != 'approved':
                    raise ValidationError("You Cannot Approve this before %s"%(dict(users._fields['approve_level'].selection).get(users.approve_level)))
        approver.write({'status': 'approved'})
        self.sudo()._get_user_approval_activities(user=self.env.user).action_feedback()

    @api.depends('category_id', 'request_owner_id')
    def _compute_approver_ids(self):
        for request in self:
            # Don't remove manually added approvers
            users_to_approver = defaultdict(lambda: self.env['approval.approver'])
            for approver in request.approver_ids:
                users_to_approver[approver.user_id.id] |= approver
            users_to_category_approver = defaultdict(lambda: self.env['approval.category.approver'])
            for approver in request.category_id.approver_ids:
                users_to_category_approver[approver.user_id.id] |= approver
            new_users = request.category_id.user_ids
            manager_user = 0
            if request.category_id.manager_approval:
                employee = self.env['hr.employee'].search([('user_id', '=', request.request_owner_id.id)], limit=1)
                if employee.parent_id.user_id:
                    new_users |= employee.parent_id.user_id
                    manager_user = employee.parent_id.user_id.id
            approver_id_vals = []
            for user in new_users:
                # Force require on the manager if he is explicitely in the list
                required = users_to_category_approver[user.id].required or \
                           (request.category_id.manager_approval == 'required' if manager_user == user.id else False)
                current_approver = users_to_approver[user.id]
                if current_approver and current_approver.required != required:
                    approver_id_vals.append(Command.update(current_approver.id, {'required': required}))
                    print(approver_id_vals,"=======================pppppppppppppppppp")
                elif not current_approver:
                    approver_id_vals.append(Command.create({
                        'user_id': user.id,
                        'approve_level':request.category_id.approver_ids.filtered(lambda l:l.user_id.id == user.id).approve_level,
                        'status': 'new',
                        'required': required,
                    }))
            request.update({'approver_ids': approver_id_vals})

