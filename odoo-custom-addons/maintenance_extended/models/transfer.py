from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.osv import expression

from odoo.exceptions import ValidationError


class Transfer(models.Model):
    _name = 'transfer.details'
    _description = 'Equipment Transfer Details'

    def name_get(self):
        result = []
        for rec in self:
            name = rec.name_id
            result.append((rec.id, name))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [('name_id', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    name_id = fields.Many2one('maintenance.equipment', string="Source Location ", required=True)
    contact = fields.Many2one('res.partner', string="Contact", required=True)
    eid = fields.Char(string="Equipment Name ", related='name_id.name')
    date = fields.Datetime(string='Scheduled Date ', default=datetime.today(), readonly=True)
    sdoc = fields.Char(string="Source Document", help="Reference of the document")
    ref = fields.Char(string="Responsible")
    source_location = fields.Many2one('build.details', string="Building", required=True)
    traid = fields.Char(string="Transfer ID", default=lambda self: 'new', readonly=True)
    note = fields.Html('Notes')
    category_id = fields.Char(string='Equipment Category', related='name_id.category_id.name')
    cate_id = fields.Char(string='Equipment Category', related='name_id.category_id.code')
    machine_id = fields.Char(string='Machine Id', related='name_id.Equipmentcode')
    source_block = fields.Many2one('block.details', string="Block", required=True)
    source_floor = fields.Many2one('floor.details', string="Floor", required=True)
    source_division = fields.Many2one('division.details', string="Division", required=True)
    source_section = fields.Many2one('section.details', string="Section", required=True)
    selction = fields.Selection(related='name_id.newmachine', string=' Machine type')
    des = fields.Char(compute="_compute_total", string="Designation Location", store=True)

    # @api.onchange('name_id')
    # def _onchange_name_id(self):
    #     if self.name_id:
    #         self.ref = self.name_id.employee_id.name

    @api.depends('source_location', 'source_block', 'source_floor', 'source_division', 'source_section')
    def _compute_total(self):
        for record in self:
            mechine = self.env['maintenance.equipment'].search([('codefor', '=', record.name_id.name)])
            print(mechine.name)
            if record.source_location and record.source_block and record.source_floor and record.source_division and record.source_section and record.machine_id:
                codefirst = \
                    record.machine_id + '/' + \
                    record.source_location.buildcode + '/' + \
                    record.source_block.blockcode + '/' + \
                    record.source_floor.floorcode

                codelast = \
                    record.source_division.divisioncode + '/' + \
                    record.source_section.sectioncode
                if self.selction == 'existing':
                    record.des = \
                        record.cate_id + '-' + '[EM]' + \
                        codefirst + '/' + \
                        codelast

                else:

                    record.des = \
                        record.cate_id + '-' + \
                        codefirst + '/' + \
                        codelast

                mechine.update(
                    {'codefor': record.des}
                )

    @api.model
    def create(self, vals):
        if vals.get('traid', 'new') == 'new':
            vals['traid'] = self.env['ir.sequence'].next_by_code('maintenance_extended.transfer.details') or 'new'

        return super(Transfer, self).create(vals)


class Scarp(models.Model):
    _name = 'scarp.details'
    _description = 'Equipment Scrap Details'

    scrapitem = fields.Char(related='move_id.equipment_id.codefor', string="Equipment Id")
    move_id = fields.Many2one('maintenance.request', string="Reason")
    date = fields.Datetime(string='Scarp Date ', default=datetime.today(), readonly=True)
    sdoc = fields.Char(string="Source Document")
    scarpid = fields.Char(string="Scarp ID", default=lambda self: 'new', readonly=True)

    # name_id = fields.Many2one('maintenance.equipment', string="Equipment ID ", required=True)
    # eid = fields.Char(string="Equipment Name", readonly=True, related='name_id.name')
    # scrap_location_id = fields.Many2one('location.details', string='Scrap Location')
    # location_id = fields.Many2one('location.details', string='Source Location')
    # category_id = fields.Char(string=" Equipment Category ", related='name_id.category_id.name')
    # state = fields.Selection([('draft', "Draft"), ('done', "Done")], default="draft", string="Status")

    @api.model
    def create(self, vals):
        if vals.get('scarpid', 'new') == 'new':
            vals['scarpid'] = self.env['ir.sequence'].next_by_code('maintenance_extended.scarp.details') or 'new'
            print(vals['scarpid'])
        return super(Scarp, self).create(vals)

    # @api.onchange('name_id')
    # def _onchange_name_id(self):
    #     print("category")
    #     if self.name_id:
    #         self.category = self.name_id.category_id.name
    #         self.eid = self.name_id.name
    #         self.ref = self.name_id.employee_id.name

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done(self):
        if 'done' in self.mapped('state'):
            raise UserError(_('You cannot delete a scrap which is done...!'))

    def action_validate(self):
        self.state = 'done'


