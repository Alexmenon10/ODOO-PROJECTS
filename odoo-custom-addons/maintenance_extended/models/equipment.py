from odoo import fields, models, api, _
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from datetime import date
import re


class Maintenance(models.Model):
    _inherit = "maintenance.equipment"

    def name_get(self):
        result = []
        for rec in self:
            name = rec.codefor
            result.append((rec.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [('codefor', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    mobile = fields.Char(string="Mobile")
    build_id = fields.Many2one('build.details', string="Building Name ", required=True)
    block_id = fields.Many2one('block.details', string="Block", required=True, help="building info")
    floor_id = fields.Many2one('floor.details', string="Floor", required=True)
    division_id = fields.Many2one('division.details', string="Division", required=True)
    section_id = fields.Many2one('section.details', string="Section", required=True)
    image = fields.Binary(string="Image")
    equipment_checklist_ids = fields.One2many('check.details', 'check_id', )
    date = fields.Date(default=fields.Date.today(), readonly=True)
    nextdate = fields.Date(string='Next Maintenance Date')
    # equipment_count = fields.Integer(string="Equipment", compute='_equipments_count')
    codefor = fields.Char(compute="_compute_vehicle_name", string="Equipment Id", store=True)
    Equipmentcode = fields.Char(string='Equipment Code', required=True, copy=False, readonly=True,
                                default=lambda self: _('New'), invisible="1")
    newmachine = fields.Selection([('new', 'New '), ('existing', 'Existing Equipment')], string="Machine Type")
    subcategory_id = fields.Many2one('subcate.details', string="Sub Category", required=True,
                                     domain="[('category_id', '=', category_id)]", )

    @api.model
    def create(self, vals):
        vals['Equipmentcode'] = self.env['ir.sequence'].next_by_code('equipment.code') or _('New')
        rec = super(Maintenance, self).create(vals)
        return rec

    @api.depends('build_id', 'block_id', 'floor_id', 'division_id', 'section_id', 'newmachine')
    def _compute_vehicle_name(self):
        for record in self:
            if record.build_id and record.block_id and record.floor_id and record.division_id and record.section_id:
                mach_id = record.Equipmentcode
                if not record.Equipmentcode:
                    mach_id = ''
                codefirst = \
                    record.build_id.buildcode + '/' + \
                    record.block_id.blockcode + '/' + \
                    record.floor_id.floorcode
                codelast = \
                    record.division_id.divisioncode + '/' + \
                    record.section_id.sectioncode
                if self.newmachine == 'existing':
                    record.codefor = \
                        record.category_id.code + '-' + '[EM]' + \
                        mach_id + '/' + \
                        codefirst + '/' + \
                        codelast

                else:

                    record.codefor = \
                        record.category_id.code + '-' + \
                        mach_id + '/' + \
                        codefirst + '/' + \
                        codelast

    # @api.depends('category_id')
    # def _equipments_count(self):
    #     for rec in self :
    #         equipment = self.env['maintenance.equipment'].search_count([('category_id', '=', self.category_id.ids)])
    #         rec.equipment_count = equipment

    @api.onchange('subcategory_id')
    def onchange_category_id(self):
        if self.subcategory_id:
            if self.subcategory_id.image:
                self.image = self.subcategory_id.image

    # def action_equipment_category(self):
    #     return {
    #         'name': 'Equipment',
    #         'view_mode': 'tree,form,kanban',
    #         'domain': [('category_id', 'in', self.category_id.ids)],
    #         'res_model': 'maintenance.equipment',
    #         'type': 'ir.actions.act_window',
    #         'context': {'create': False, 'active_test': False},
    #     }
