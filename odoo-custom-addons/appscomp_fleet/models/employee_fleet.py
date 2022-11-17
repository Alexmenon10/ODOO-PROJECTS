from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime

class FleetVehicleInherit(models.Model):
    _inherit = 'fleet.vehicle'

    check_availability = fields.Boolean(default=True, copy=False)
    # reserved_time = fields.One2many('fleet.reserved', 'reserved_obj',
    #                                 string='Reserved Time',
    #                                 readonly=1)
    vehicle_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                     'Vehicle State', default='un_reserved', tracking=True)
    vehicle_position = fields.Selection([('out', 'Out'), ('in', 'In')],default='in',
                                     string='Vehicle Position', tracking=True)
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
    ], string='Vehicle Category', tracking=True)
    fuel_type = fields.Selection(selection_add=[("petrol", "Petrol")])
    start_date = fields.Datetime(string='Trip Starts', store=True, default=lambda self: fields.Datetime.now(), )
    end_date = fields.Datetime(string='Trip Ends', store=True, default=lambda self: fields.Datetime.now(), )
    duration = fields.Float(string='Duration')
    str_duration = fields.Char(string='Duration')
    travel_from = fields.Char(string='From')
    travel_to = fields.Char(string='To')
    vehicle_full_name = fields.Char(string='Vehicle Name')
    trip_scheduled = fields.Boolean(string='Trip Scheduled')

    vehicle_history_count = fields.Integer(string='Vehicle History',
                                                    compute='get_vehicle_history_count_record')
    # vehichle_in_out_list_ids = fields.One2many('vehicle.in.out.details', 'vehicle_in_out_details_id',
    #                                        string = 'Vehicle In Out List')

    acquisition_date = fields.Date('Registration Date', required=False,
                                   default=fields.Date.today, help='Date when the vehicle has been immatriculated')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)',
                         copy=False)
    odometer = fields.Float(compute='_get_odometer', inverse='_set_odometer', string='Last Odometer',
                            help='Odometer measure of the vehicle at the moment of this log')
    odometer_unit = fields.Selection([
        ('kilometers', 'km'),
        ('miles', 'mi')
    ], 'Odometer Unit', default='kilometers', help='Unit of the odometer ', required=True)
    manager_id = fields.Many2one(
        'res.users', 'Fleet Manager',
        domain=lambda self: [('groups_id', 'in', self.env.ref('fleet.fleet_group_manager').id)],
    )
    location = fields.Char(help='Location of the vehicle (garage, ...)')

    license_plate = fields.Char(tracking=True, string='Registration Number',
                                help='License plate number of the vehicle (i = plate number for a car)')
    engine_number = fields.Char(tracking=True, string='Engine Number')

    def _prepare_vehicle_details(self):
        return {
            'vehicle_name': self.id and self.id or False,
        }

    def create_vehicle_details(self):
        vehicle_trip_history_obj = self.env['vehicle.tracking.status']
        for order in self:
            vehicle_trip_history_data = order._prepare_vehicle_details()
            vehicle_trip_history_data_id = vehicle_trip_history_obj.create(vehicle_trip_history_data)

    # find vehicle travel  time duration.
    # @api.onchange('start_date','end_date')
    def _compute_vehicle_duration(self):
        for rec in self:
            # rec.duration = 10
            # if rec.state_id == 'Registered':
            if rec.start_date and rec.end_date:
                date1 = str(rec.start_date)
                datetimeFormat = '%Y-%m-%d %H:%M:%S'
                date2 = str(rec.end_date)
                date11 = datetime.strptime(date1, datetimeFormat)
                date12 = datetime.strptime(date2, datetimeFormat)
                if rec.trip_scheduled:
                    timedelta = date12 - date11
                    tot_sec = timedelta.total_seconds()
                    h = tot_sec // 3600
                    m = (tot_sec % 3600) // 60
                    duration_hour = ("%d.%d" % (h, m))
                    rec.duration = float(duration_hour)
                    rec.str_duration = timedelta
                else:
                    rec.duration = False
                    rec.str_duration = False
            else:
                if rec.start_date and rec.end_date == False:
                    rec.duration = False
                    rec.str_duration = False


    def get_vehicle_history_count_record(self):
        name = str(self.model_id.brand_id.name) + str(self.model_id.name) + '/' + str(self.license_plate)
        self.vehicle_history_count = self.env['vehicle.trip.history'].sudo().search_count(
            [('vehicle_name', '=', self.vehicle_full_name)])

    def get_vehicle_history(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('appscomp_fleet.view_vehicle_trip_history_form')
        tree_view = self.sudo().env.ref('appscomp_fleet.view_vehicle_trip_history_tree')
        return {
            'name': _('Vehicle Trip History'),
            'res_model': 'vehicle.trip.history',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('vehicle_name', '=', self.vehicle_full_name)],
        }

    @api.onchange('model_id', 'license_plate')
    def _onchange_vehicle_name(self):
        name = str(self.model_id.brand_id.name) + '/' + str(self.model_id.name) + '/' + str(self.license_plate)
        self.sudo().write({
            'vehicle_full_name': name,
        })
    @api.onchange('model_id')
    def _onchange_vehicle_category(self):
        self.sudo().write({
            'vehicle_category': self.model_id.vehicle_type,
        })



class FleetVehicleModel(models.Model):
    """Model Fleet Vehicle."""

    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection([
        ("car", "Car"),
        ("bus", "Bus"),
        ("jcb", "JCB"),
        ("tractor", "Tractor"),
        ("jeep", "Jeep"),
        ("tanker_lorry", "Tanker Lorry"),
        ("tipper_lorry", "Tipper Lorry"),
        ("load_vehicle", "Load Vehicle"),
    ])
    default_fuel_type = fields.Selection(selection_add=[("petrol", "Petrol")])


