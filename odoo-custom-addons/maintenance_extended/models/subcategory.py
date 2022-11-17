from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from datetime import date
import re


class SubCate(models.Model):
    _name = "subcate.details"

    @api.depends('equipment_ids')
    def _compute_fold(self):
        self.fold = False
        for category in self:
            category.fold = False if category.equipment_count else True

    name = fields.Char(string="Sub Category ", help='hi hell0')
    code = fields.Char(string="Code")
    category_id = fields.Many2one('maintenance.equipment.category', string="Catgegory")
    image = fields.Image(string="Image")
    equipment_count = fields.Integer(string="Equipment", compute='_subcategory_count')
    equipment_ids = fields.One2many('maintenance.equipment', 'subcategory_id', string='Equipments', copy=False)

    #
    # @api.depends('category_id')
    # def _equipments_count(self):
    #     for rec in self:
    #         equipment = self.env['maintenance.equipment'].search_count([('subcategory_id', '=', self.ids)])
    #         rec.equipment_count = equipment

    def _subcategory_count(self):
        equipment_data = self.env['maintenance.equipment'].read_group([('subcategory_id', 'in', self.ids)],
                                                                      ['subcategory_id'], ['subcategory_id'])
        mapped_data = dict([(m['subcategory_id'][0], m['subcategory_id_count']) for m in equipment_data])
        for category in self:
            category.equipment_count = mapped_data.get(category.id, 0)

    def action_equipment_category(self):
        # self.sudo().ensure_one()
        # context = dict(self._context or {})
        # active_model = context.get('active_model')
        # form_view = self.sudo().env.ref('maintenance.hr_equipment_view_form')
        # tree_view = self.sudo().env.ref('maintenance.hr_equipment_category_view_tree')
        # kanban_view = self.sudo().env.ref('	maintenance.hr_equipment_view_kanban')
        return {
            'name': 'Equipment',
            'view_mode': 'tree,form,kanban,graph',
            'domain': [('subcategory_id', '=', self.ids)],
            'res_model': 'maintenance.equipment',
            'type': 'ir.actions.act_window',
            'context': {'create': True, 'active_test': False},
            # 'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
        }

#
# def action_equipment_category(self):
#     print("===================",self.category_id)
#     self.sudo().ensure_one()
#     context = dict(self._context or {})
#     active_model = context.get('active_model')
#     form_view = self.sudo().env.ref('maintenance.hr_equipment_view_form')
#     tree_view = self.sudo().env.ref('maintenance.hr_equipment_category_view_tree')
#     kanban_view = self.sudo().env.ref('	maintenance.view_maintenance_equipment_category_kanban')
#     return {
#         'name': _(' Equipment '),
#         'res_model': 'maintenance.equipment',
#         'type': 'ir.actions.act_window',
#         'view_mode': 'kanban,tree,form',
#         'views': [(kanban_view.id, 'kanban'), (tree_view.id, 'tree'), (form_view.id, 'form')],
#         'domain': [('category_id', '=', self.category_id.id)],
#         # 'domain': [('name', '=', self.name), ('request_owner_id', '=', self.user_id.id)],
#     }
