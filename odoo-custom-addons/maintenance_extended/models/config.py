from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
from odoo.osv import expression

from odoo.exceptions import ValidationError


class Location(models.Model):
    _name = 'location.details'
    _description = 'Equipment Location Details'

    name = fields.Char(string="Location Name ")


class Build(models.Model):
    _name = 'build.details'
    _description = 'Building Details'

    name = fields.Char(string="Building  ")
    buildcode = fields.Char(string="Code")


class Block(models.Model):
    _name = 'block.details'
    _description = 'Block Details'

    name = fields.Char(string="Block")
    blockcode = fields.Char(string="Code")


class Floor(models.Model):
    _name = 'floor.details'
    _description = 'Floor Details'

    name = fields.Char(string="Floor")
    floorcode = fields.Char(string="Code")


class Division(models.Model):
    _name = 'division.details'
    _description = 'Division Details'

    name = fields.Char(string="Division")
    divisioncode = fields.Char(string="Code")


class Section(models.Model):
    _name = 'section.details'
    _description = 'Section Details'

    name = fields.Char(string="Section")
    sectioncode = fields.Char(string="Code")


class Checklist(models.Model):
    _name = 'check.details'
    _description = 'Check List Details'

    check_id = fields.Many2one('maintenance.equipment', string="Equipment Name ")

