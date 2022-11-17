from odoo import api, fields, models, _
from datetime import datetime, date
from datetime import timedelta, datetime


class DriverTripHistory(models.Model):
    _name = 'driver.trip.history'
    _description = "Driver Trip History"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    driver_name = fields.Many2one('hr.employee', string="Driver Name")
    driver_department = fields.Many2one(string='Department', related='driver_name.department_id', tracking=True)
    driver_job_id = fields.Many2one(related='driver_name.job_id', string="Job Position")
    driver_manager = fields.Many2one(related='driver_name.parent_id', string="Reporting Manager")
    driver_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                    'Driver State', tracking=True)
    driver_position = fields.Selection([('out', 'Out'), ('in', 'In')],
                                       'Driver Position', tracking=True)
    driver_approval_request_id = fields.Many2one('approval.request', string="Driver Approval Request")
    source_document = fields.Char(string='Reference')
    vehicle_name = fields.Many2one('fleet.vehicle', string="Vehicle Name ")
    emp_vehicle = fields.Char(string='Vehcicle Name')
    driver_travel_detail_ids = fields.One2many('driver.travel.history', 'driver_trip_id')
    driver_beta_sheet_ids = fields.One2many('driver.check.in.out.details', 'driver_history_id',
                                            string='Driver check In Out List')
    opening_km = fields.Float(string="Opening KM")
    closing_km = fields.Float(string="Closing KM")
    total_kilometer = fields.Float(string='Total Distance')
    persons_list = fields.Many2many('hr.employee', string="Persons List")
    type_of_vehicle = fields.Selection([
        ('company', 'Company Owned'),
        ('employee', 'Employee Owned'),
        ('rental', 'Rental'),
    ], default='company', string='Vehicle Type')
    vehicle_category = fields.Selection([
        ("car", "Car"),
        ("bike", "Bike"),
        ("bus", "Bus"),
        ("jcb", "JCB"),
        ("tractor", "Tractor"),
        ("jeep", "Jeep"),
        ("tanker_lorry", "Tanker Lorry"),
        ("tipper_lorry", "Tipper Lorry"),
        ("load_vehicle", "Load Vehicle"),
    ], string='Vehicle Category')

    multiple_approval_ids = fields.Many2many('approval.request', string='Multiple Approval')

    def name_get(self):
        result = []
        for trip in self:
            name = trip.driver_name.name
            result.append((trip.id, name))
        return result


class DriverTravelHistory(models.Model):
    _name = 'driver.travel.history'
    _description = "Driver Travel History"

    driver_trip_id = fields.Many2one('driver.trip.history', string='Driver Trip')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    travel_from = fields.Char(string='From')
    travel_to = fields.Char(string='To')
    duration = fields.Char(string='Duration')
    driver_name = fields.Many2one('hr.employee', string="Driver Name ")
    driver_department = fields.Many2one(string='Department', related='driver_name.department_id', tracking=True)
    driver_job_id = fields.Many2one(related='driver_name.job_id', string="Job Position")
    driver_manager = fields.Many2one(related='driver_name.parent_id', string="Reporting Manager")
    driver_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                    'Driver State', tracking=True)
    driver_position = fields.Selection([('out', 'Out'), ('in', 'In')],
                                       'Driver Position', tracking=True)
    driver_approval_request_id = fields.Many2one('approval.request', string="Driver Approval Request")
    source_document = fields.Char(string='Reference')
    name = fields.Char(string="Name", invisible=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")


class DriverCheckInOutDetails(models.Model):
    _name = 'driver.check.in.out.details'
    _description = 'Driver Check In Out Details'

    # driver_in_out_details_id = fields.Many2one('hr.employee', string='Driver In/Out Details')
    driver_history_id = fields.Many2one('driver.trip.history', string='Driver History')
    reference = fields.Char(string='Reference')
    in_time = fields.Datetime(string='In Time')
    out_time = fields.Datetime(string='Out Time')
    out_verified_by = fields.Many2one('hr.employee', string='Out Security')
    in_verified_by = fields.Many2one('hr.employee', string='In Security')
    out_security = fields.Char(string='Out Security')
    in_security = fields.Char(string='In Security')
    out_verified_date = fields.Datetime(string='Out Verified Date')
    in_verified_date = fields.Datetime(string='In Verified Date')
    duration = fields.Float(string='Duration')
    str_duration = fields.Char(string="Durations")
    total_kilometer = fields.Float(string='Total Distance')

    unit_from = fields.Many2one('stock.location', string="Unit From")
    unit_to = fields.Many2one('stock.location', string="Unit to")
    ref_name = fields.Many2one('vehicle.gate.pass', string='Name')
    opening_km = fields.Float(string="Opening KM")
    closing_km = fields.Float(string="Closing KM")


class VehicleTripHistory(models.Model):
    _name = 'vehicle.trip.history'
    _description = "Vehicle Trip History"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_name = fields.Many2one('fleet.vehicle', string="Vehicle Name ", required=True)
    vehicle_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                     'Vehicle State', tracking=True)
    vehicle_position = fields.Selection([('out', 'Out'), ('in', 'In')],
                                        'Vehicle Position', tracking=True)
    vehicle_approval_request_id = fields.Many2one('approval.request', string="Vehicle Approval Request")
    source_document = fields.Char(string='Reference')
    driver_name = fields.Many2one('hr.employee', string="Driver Name ")
    vehicle_travel_detail_ids = fields.One2many('vehicle.travel.history', 'vehicle_trip_id')

    opening_km = fields.Float(string="Opening KM")
    closing_km = fields.Float(string="Closing KM")
    total_kilometer = fields.Float(string='Total Distance')

    def name_get(self):
        result = []
        for trip in self:
            name = trip.vehicle_name.name
            result.append((trip.id, name))
        return result


class VehicleTravelHistory(models.Model):
    _name = 'vehicle.travel.history'
    _description = "Vehicle Travel History"

    vehicle_trip_id = fields.Many2one('vehicle.trip.history', string='Driver Trip')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    travel_from = fields.Char(string='From')
    travel_to = fields.Char(string='To')
    duration = fields.Char(string='Duration')
    name = fields.Char(string="Name", invisible=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
