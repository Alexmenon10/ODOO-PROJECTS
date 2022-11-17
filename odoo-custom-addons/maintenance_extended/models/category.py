from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from datetime import date
import re


class Maintenancecategory(models.Model):
    _inherit = "maintenance.equipment.category"

    @api.depends('subcategory_id')
    def _compute_fold(self):
        self.fold = False
        for category in self:
            category.fold = False if category.sub_count else True

    image = fields.Image(string="Image")
    code = fields.Char(string="code")
    subcategory_id = fields.Many2one('subcate.details', string="Sub Category")
    sub_count = fields.Integer(string="Equipment", compute='_subcategory_count')

    # @api.depends('subcategory_id')
    # def _subcategory_count(self):
    #     for rec in self:
    #         equipment = self.env['subcate.details'].search_count(
    #             [('category_id', '=', self.ids)])
    #     rec.sub_count = equipment

    def _subcategory_count(self):
        equipment_data = self.env['subcate.details'].read_group([('category_id', 'in', self.ids)], ['category_id'],
                                                                ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in equipment_data])
        for category in self:
            category.sub_count = mapped_data.get(category.id, 0)

    @api.onchange('equipment_id')
    def onchange_category_id(self):
        print('equipment_id')
        if self.equipment_id:
            if self.equipment_id.image:
                self.image = self.equipment_id.image

    # def action_equipments_subcategory(self):
    #     return {
    #         'name': 'Equipment',
    #         'view_mode': 'tree,form',
    #         'domain': [('subcategory_id', 'in', self.subcategory_id.id)],
    #         'res_model': 'maintenance.equipment',
    #         'type': 'ir.actions.act_window',
    #         'context': {'create': False, 'active_test': False},
    #     }

    # def _subcategory_count(self):
    #     # print("===================",self.activity_user_id.name)
    #     self.sub_count = self.env['maintenance.equipment.category'].sudo().search_count(
    #         [('subcategory_id', '=', self.subcategory_id)])

    def action_equipments_subcategory(self):
        print("===================", self.subcategory_id)
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('maintenance_extended.view_subcate_form')
        tree_view = self.sudo().env.ref('maintenance_extended.view_subcate_tree')
        kanban_view = self.sudo().env.ref('maintenance_extended.view_subcate_kanban')
        return {
            'name': _('My Equipment Sub Category'),
            'res_model': 'subcate.details',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'views': [(kanban_view.id, 'kanban'), (tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('category_id', '=', self.ids)],
            # 'domain': [('name', '=', self.name), ('request_owner_id', '=', self.user_id.id)],
        }

    # domain = "[('category_id', '=?', category_id)]"
