from odoo import api, fields, models, _
from datetime import timedelta, datetime
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


class VehicleGatePass(models.Model):
    _name = 'vehicle.gate.pass'
    _description = "Vehicle Gate Pass"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', size=256, tracking=True, required=True, copy=False,
                       index=True, default=lambda self: _('/'),
                       help='A unique sequence number for the Indent')
    vehicle_out_id_for_ref = fields.Char(string='Approved')
    refer_vehicle_out_id = fields.Many2one('vehicle.gate.pass', string='Approved',
                                           domain="[('pass_state', '=', 'out'),('out_pass_check', '=', False)]")
    vehicle_out_id = fields.Many2one('vehicle.gate.pass', string='Approved',
                                     domain="[('pass_state', '=', 'out'),('out_pass_check', '=', False)]")
    approval_id = fields.Many2one('approval.request', string='Approved',
                                  domain="[('request_status', '=', 'approved'), ('approval_fleet_status', '=', 'open'),"
                                  # "('veh_driv_assign', '=', True),"
                                         " ]"
                                  )
    vehicle_travel_id = fields.Many2one('hr.employee', string='Request Raised For')
    request_owner_id = fields.Many2one('res.users', string='Request Owner')
    persons_list = fields.Many2many('hr.employee', string="Persons List")
    person_count = fields.Integer(string="Person Count", default=0)
    type_of_vehicle = fields.Selection([
        ('company', 'Company Owned'),
        ('employee', 'Employee Owned'),
        ('rental', 'Rental'),
    ], default='company', string='Vechicle Type')
    rental_vehicle_num = fields.Char(string="vehicle Number")
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
    ], string='Vechicle Category')
    vehicle_driver = fields.Many2one('hr.employee', string='Driver')
    emp_vechicle = fields.Many2one('fleet.vehicle', string="Vechicles")
    emp_own_vechicle = fields.Char(string="Vechicles")
    approval_detail_ids = fields.One2many('approval.details', 'approval_approved_id')
    travel_detail_ids = fields.One2many('vehicle.travel.details', 'vechile_approval_id')
    # taken_by = fields.Many2one('hr.employee', string='Taken By')
    place = fields.Char(string="Place")
    approved = fields.Char(string="Approved By")
    time_out = fields.Datetime(string="Time Out", default=lambda self: fields.Datetime.now())
    time_in = fields.Datetime(string="Time In", default=lambda self: fields.Datetime.now())
    out_time_verified = fields.Datetime(string="Time Out", related='vehicle_out_id.verified_time_out')
    opening_km = fields.Float(string="Opening KM")
    in_opening_km = fields.Float(string="Opening KM")
    closing_km = fields.Float(string="Closing KM", default=False)
    net_km = fields.Float(string="Net Km")
    employee_sign = fields.Binary(string="Employee Sign ")
    security_sign = fields.Binary(string="Security Sign ")
    # name = fields.Char(string='Reference', size=256, tracking=True, required=True, copy=False,
    #                    index=True, default=lambda self: _('/'),
    #                    help='A unique sequence number for the Indent')
    vehicle_pass_state = fields.Selection([('out', 'Out'), ('in', 'In')],
                                          string='Movement', readonly=True, tracking=True)
    pass_state = fields.Selection([('draft', 'Draft'), ('out', 'Out'), ('in', 'In')],
                                  default='draft', string='Pass State', readonly=True, tracking=True)
    verified_time_out = fields.Datetime(string="Verified Out Time")
    verified_time_in = fields.Datetime(string="Verified In Time")
    out_verified_by = fields.Many2one('hr.employee', string='Out Security')
    in_verified_by = fields.Many2one('hr.employee', string='In Security')
    security_name = fields.Char(string='Security')
    pass_check = fields.Boolean(string='Check')
    duration_update = fields.Boolean(string='Update')
    beta_duration = fields.Float(string='Duration', store=True)
    total_kilometer = fields.Float(string='Total Distance', store=True)

    unit_from = fields.Many2one('stock.location', string="Unit From")
    unit_to = fields.Many2one('stock.location', string="Inward Unit")
    widget_check = fields.Boolean(string='widget Check')
    out_pass_check = fields.Boolean(string='Out Pass Check')

    attachment = fields.Binary(String="Attachments")
    attachment_detail = fields.Char(string="Attachment")
    gate_pass_remark = fields.Text(string="Remarks")
    type_of_vehicle = fields.Selection([
        ('company', 'Company Owned'),
        ('employee', 'Employee Owned'),
        ('rental', 'Rental'),
    ], default='company', string='Vechicle Type')

    approval_trip_type = fields.Selection([
        ('one_way', 'One Way Trip'),
        ('rounded_trip', 'Rounded Trip')], string="Trip Type")

    username = fields.Many2one("gate.user.registration")

    pass_type = fields.Selection([
        ("single", "Single"),
        ("multiple", "Multiple")], default='single', string='State')
    multiple_approval_id = fields.Many2one("fleet.multiple.assign.vehicle", string='Multiple Approval',
                                           domain="[('state', '=', 'assign'),('pass_status_gate', '=', 'open')]")

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

        # def name_get(self):
        #     result = []
        #     for rec in self:
        #         name = str(rec.name) + ' [' + str(rec.approval_id.name) +']'
        #         result.append((rec.id, name))
        #     return result

    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = list(args or [])
    #     if name:
    #         args += ['|', ('approval_id', operator, name), ('vehicle_out_id', operator, name)]
    #     return self._search(args, limit=limit, access_rights_uid=name_get_uid)
    # def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
    #     args = args or []
    #     domain = []
    #     domain = [('approval_id',operator, name)]
    #     return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    # @api.onchange('unit_from')
    # def _get_unit_from_warning(self):
    #     if self.approval_id:
    #         raise ValidationError("Alert.! You can't change the Unit Form.")

    def vehicle_trip_complete_remark(self):
        if self.widget_check:
            raise ValidationError(
                "Alert.! The Reference of %s For the Vehicle of %s Trip has been Closed." % (
                    self.vehicle_out_id.approval_id.name, self.emp_vechicle.name))

    def vehicle_trip_complete(self):
        vehicle = self.env['fleet.vehicle'].search([('vehicle_full_name', '=', self.emp_vechicle.name)])
        approval = self.env['approval.request'].search([('name', '=', self.vehicle_out_id.approval_id.name)])
        multi = self.env['fleet.multiple.assign.vehicle'].search([('name', '=', self.vehicle_out_id.multiple_approval_id.name)])
        employee = self.env['hr.employee'].search([('name', '=', self.vehicle_driver.name)])
        if not self.widget_check:
            self.write({
                'widget_check': True
            })
            approval.write({
                'approval_fleet_status': 'close',
            })
            multi.write({
                'pass_status_gate': 'close',
            })
            employee.write({
                'driver_state': 'un_reserved'
            })
            vehicle.write({
                'vehicle_state': 'un_reserved'
            })

        else:
            self.write({
                'widget_check': False
            })

    def vehicle_pass_out_verify(self):
        approval = self.env['approval.request'].search([('name', '=', self.approval_id.name)])
        employee = self.env['hr.employee'].search([('name', '=', self.vehicle_driver.name)])
        if self.pass_type == 'single':
            employee_history = self.env['driver.trip.history'].search(
                [('driver_name', '=', self.vehicle_driver.name), ('source_document', '=', self.approval_id.name)])
            vehicle_history = self.env['vehicle.trip.history'].search(
                [('vehicle_name', '=', self.emp_vechicle.name), ('source_document', '=', self.approval_id.name)])
        if self.pass_type == 'multiple':
            employee_history = self.env['driver.trip.history'].search(
                [('driver_name', '=', self.vehicle_driver.name),
                 ('source_document', '=', self.multiple_approval_id.name)])
            vehicle_history = self.env['vehicle.trip.history'].search(
                [('vehicle_name', '=', self.emp_vechicle.name),
                 ('source_document', '=', self.multiple_approval_id.name)])
        vehicle = self.env['fleet.vehicle'].search([('vehicle_full_name', '=', self.emp_vechicle.name)])
        self.write({'pass_state': 'out', 'out_verified_by': self._uid, 'verified_time_out': datetime.now()})
        vehicle.write({'vehicle_position': 'out'})
        employee.write({'driver_position': 'out'})
        employee_history.write(
            {'opening_km': self.opening_km, 'closing_km': self.closing_km, 'total_kilometer': self.total_kilometer,
             'driver_position': 'out', 'driver_state': 'reserved'})
        approval.write(
            {'approval_position': 'out', 'gate_pass_out_by': self.env.user.id, 'gate_pass_out_time': datetime.now()})
        vehicle_history.write(
            {'opening_km': self.opening_km, 'closing_km': self.closing_km, 'total_kilometer': self.total_kilometer,
             'vehicle_position': 'out', 'vehicle_state': 'reserved'})
        line_vals = []
        vals = {
            'reference': self.approval_id.name or self.multiple_approval_id.name,
            'ref_name': self.id,
            'out_time': self.verified_time_out,
            'out_verified_by': self.username.id,
            'out_security': self.security_name,
            'unit_from': self.unit_from.id,
            'opening_km': self.opening_km,
        }
        line_vals.append((0, 0, vals))
        # employee.driver_in_out_list_ids = line_vals
        employee_history.driver_beta_sheet_ids = line_vals

    def _prepare_vehicle_odometer_history(self):
        return {
            'vehicle_id': self.emp_vechicle.id and self.emp_vechicle.id or False,
            'date': self.verified_time_in and self.verified_time_in or False,
            'driver_name': self.vehicle_driver.id and self.vehicle_driver.id or False,
            'driver_list': self.vehicle_driver.id and self.vehicle_driver.id or False,
            'value': self.closing_km and self.closing_km or False,
            'total_km': self.total_kilometer and self.total_kilometer or False,
            'start_km': self.vehicle_out_id.opening_km and self.vehicle_out_id.opening_km or False,
        }

    def vehicle_pass_in_verify(self):
        if self.closing_km != 0.00:
            vehicle_trip_history_obj = self.env['fleet.vehicle.odometer']
            approval = self.env['approval.request'].search([('name', '=', self.vehicle_out_id.approval_id.name)])
            employee = self.env['hr.employee'].search([('name', '=', self.vehicle_driver.name)])

            if self.vehicle_out_id.pass_type == 'single':
                employee_history = self.env['driver.trip.history'].search(
                    [('driver_name', '=', self.vehicle_driver.name), ('source_document', '=', self.approval_id.name)])
                vehicle_history = self.env['vehicle.trip.history'].search(
                    [('vehicle_name', '=', self.emp_vechicle.name), ('source_document', '=', self.approval_id.name)])
            if self.vehicle_out_id.pass_type == 'multiple':
                employee_history = self.env['driver.trip.history'].search(
                    [('driver_name', '=', self.vehicle_driver.name),
                     ('source_document', '=', self.vehicle_out_id.multiple_approval_id.name)])
                vehicle_history = self.env['vehicle.trip.history'].search(
                    [('vehicle_name', '=', self.emp_vechicle.name),
                     ('source_document', '=', self.vehicle_out_id.multiple_approval_id.name)])

            # employee_history = self.env['driver.trip.history'].search([('driver_name', '=', self.vehicle_driver.name), (
            #     'source_document', '=', self.vehicle_out_id.approval_id.name)])
            # vehicle_history = self.env['vehicle.trip.history'].search(
            #     [('vehicle_name', '=', self.emp_vechicle.name),
            #      ('source_document', '=', self.vehicle_out_id.approval_id.name)])
            employee_record = self.env['driver.check.in.out.details'].search(
                [('ref_name', '=', self.vehicle_out_id.name)])
            # employee_history_record = self.env['driver.check.in.out.details'].search([('ref_name', '=', self.vehicle_out_id.approval_id.name)])
            vehicle = self.env['fleet.vehicle'].search([('vehicle_full_name', '=', self.emp_vechicle.name)])
            self.write({
                'pass_check': False,
                'pass_state': 'in',
                'opening_km': self.in_opening_km,
                # 'beta_duration': float(duration_hour),
                'in_verified_by': self.username.id,
                'verified_time_in': datetime.now()
            })
            if self.vehicle_out_id.verified_time_out:
                date1 = str(self.vehicle_out_id.verified_time_out)
                datetimeFormat = '%Y-%m-%d %H:%M:%S'
                date2 = str(datetime.today())
                date11 = datetime.strptime(str(self.vehicle_out_id.verified_time_out).split(".")[0],
                                           '%Y-%m-%d %H:%M:%S')
                date12 = datetime.strptime(str(datetime.today()).split(".")[0], '%Y-%m-%d %H:%M:%S')
                timedelta = date12 - date11
                tot_sec = timedelta.total_seconds()
                h = tot_sec // 3600
                m = (tot_sec % 3600) // 60
                duration_hour = ("%d.%d" % (h, m))
                self.beta_duration = duration_hour
                self.opening_km = self.vehicle_out_id.opening_km
                totl_km = self.closing_km - self.vehicle_out_id.opening_km
                if self.closing_km < self.vehicle_out_id.opening_km:
                    raise ValidationError(
                        "Alert.! Closing Odometer must be Greater than Opening Odoometer.")
                self.total_kilometer = totl_km

            employee_history.write({
                'opening_km': self.opening_km,
                'closing_km': self.closing_km,
                'total_kilometer': self.total_kilometer,
                'driver_position': 'in',
                # 'driver_state' : 'un_reserved',
            })
            employee.write({
                'driver_position': 'in',
                # 'driver_state': 'un_reserved'
            })
            vehicle.write({
                'vehicle_position': 'in',
                'odometer': self.closing_km,
            })
            vehicle_history.write({
                'opening_km': self.opening_km,
                'closing_km': self.closing_km,
                'total_kilometer': self.total_kilometer,
                'vehicle_position': 'in',
                # 'vehicle_state': 'un_reserved',
            })
            employee_history_record = self.env['driver.check.in.out.details'].search(
                [('ref_name', '=', self.vehicle_out_id.name)])

            employee_record.write({
                'in_verified_by': self.in_verified_by.id,
                'in_time': self.verified_time_in,
                'unit_to': self.unit_to.id,
                'duration': self.beta_duration,
            })
            if self.beta_duration >= 0.00:
                employee_history_record.write({
                    'in_verified_by': self.in_verified_by.id,
                    'in_security': self.security_name,
                    'in_time': self.verified_time_in,
                    'duration': self.beta_duration,
                    'unit_to': self.unit_to.id,
                    'closing_km': self.closing_km,
                    'total_kilometer': self.total_kilometer,
                })
            approval.write(
                {'approval_position': 'in', 'gate_pass_in_by': self.env.user.id, 'gate_pass_in_time': datetime.now()})
            self.vehicle_out_id.out_pass_check = True
            # self._compute_duration_driver_beta_calculation()

            # for order in self:
            #     if self.type_of_vehicle == 'company':
            #         vehicle_trip_history_data = order._prepare_vehicle_odometer_history()
            #         vehicle_trip_history_data_id = vehicle_trip_history_obj.create(vehicle_trip_history_data)
        else:
            raise ValidationError(
                "Alert.! Closing Odometer is Empty , Please Enter The Exact Closing Odometer Value    .")

    @api.onchange('vehicle_out_id')
    def _get_out_approval_details(self):
        line_vals = [(5, 0, 0)]
        approvals = self.env['vehicle.gate.pass'].search([('name', '=', self.vehicle_out_id.name)])
        if self.vehicle_out_id.approval_id.approval_position == 'finish':
            raise ValidationError(
                "Alert.This Approval Number (%s) already Registered in Gate In Pass. You can't Select This Approval Number Again." % (
                    self.vehicle_out_id.approval_id.name))

        if self.vehicle_out_id:
            if self.vehicle_out_id.pass_type == 'single':
                # crt_name = self.vehicle_out_id.name.split('[')
                self.sudo().write({
                    'request_owner_id': approvals.approval_id.request_owner_id.id,
                    'persons_list': approvals.approval_id.persons_list,
                    'person_count': approvals.approval_id.person_count,
                    'type_of_vehicle': approvals.approval_id.type_of_vehicle,
                    'vehicle_category': approvals.approval_id.vehicle_category,
                    'vehicle_driver': approvals.approval_id.vehicle_driver.id or approvals.approval_id.emp_vehicle_driver.id,
                    'emp_vechicle': approvals.approval_id.vechicle_list.id,
                    'emp_own_vechicle': approvals.approval_id.emp_vechicle,
                    'unit_from': approvals.unit_from,
                    'in_opening_km': approvals.opening_km,
                })
            if self.vehicle_out_id.pass_type == 'multiple':
                self.sudo().write({
                    'type_of_vehicle': approvals.type_of_vehicle,
                    'vehicle_category': approvals.vehicle_category,
                    'vehicle_driver': approvals.vehicle_driver.id or approvals.emp_vehicle_driver.id,
                    'emp_vechicle': approvals.emp_vechicle.id,
                    'unit_from': approvals.unit_from,
                })
                self.in_opening_km = approvals.opening_km

        for travel in approvals.approval_detail_ids:
            if self.vehicle_out_id:
                vals = {
                    'source': travel.source,
                    'distination': travel.distination,
                    'start_date': travel.start_date,
                    'end_date': travel.end_date,
                    'duration': travel.duration,
                    'name': travel.name,
                }
                line_vals.append((0, 0, vals))
                self.approval_detail_ids = line_vals

    @api.onchange('multiple_approval_id')
    def get_multiple_approval_details(self):
        if self.multiple_approval_id:
            employee_record = self.env['driver.trip.history'].search(
                [('source_document', '=', self.multiple_approval_id.name)])
            # for values in employee_record.driver_beta_sheet_ids.unit_to:
            #     self.unit_from = values.id
            self.sudo().write({
                'vehicle_category': self.multiple_approval_id.vehicle_category,
                'vehicle_driver': self.multiple_approval_id.vehicle_driver.id,
                'emp_vechicle': self.multiple_approval_id.vechicle_list.id,
                'opening_km': self.multiple_approval_id.vechicle_list.odometer,
            })

        self.write({'approval_detail_ids': False})

        # approvals = self.env['fleet.multiple.assign.vehicle'].search([('name', '=', self.multiple_approval_id.name)])
        # approvals = self.env['approval.request'].search([('id', '=', self.approval_ids.ids)])
        for travel in self.multiple_approval_id.approval_ids:
            b_list = [[0, 0, {
                'name': travel.name,
                'display_type': 'line_section',
            }]]
            for line in travel.approval_travel_ids:
                b_list.append([0, 0, {
                    'start_date': line.start_date or False,
                    'end_date': line.end_date or False,
                    'source': line.source or False,
                    'distination': line.distination or False,
                    'duration': line.duration or False,
                }])
            self.write({'approval_detail_ids': b_list})
        # b_list = [[0, 0, {
        #     'name': approvals.name,
        #     'display_type': 'line_section',
        # }]]
        # line_vals = []
        # for travel in approvals.trip_details_id:
        #     vals = {
        #         'source': travel.travel_from,
        #         'distination': travel.travel_to,
        #         'start_date': travel.start_date,
        #         'end_date': travel.end_date,
        #         'duration': travel.duration,
        #     }
        #     line_vals.append((0, 0, vals))
        #     self.approval_detail_ids = line_vals

    @api.onchange('approval_id')
    def get_approval_details(self):
        line_vals = [(5, 0, 0)]
        crt_datetime = datetime.now()
        crt_date = crt_datetime.date()
        for str_date in self.approval_id.approval_travel_ids:
            start_from = str_date.start_date
            break
            if start_from:
                start_date = start_from.date()

            if self.approval_id.approval_position == 'out':
                raise ValidationError(
                    "Alert.This Approval Number (%s) already Registered in Gate Out Pass. You can't Select This Approval Number Again." % (
                        self.approval_id.name))
            if self.approval_id:
                if crt_date != start_date:
                    raise ValidationError(
                        "Alert.! Mr. %s.This Approval Number of (%s) Scheduled Trip Planned for %s . Today can't generate The Vehicle Out Pass." %
                        (self.env.user.name, self.approval_id.name, start_from))

        if self.approval_id:
            employee_record = self.env['driver.trip.history'].search([('source_document', '=', self.approval_id.name)])
            for values in employee_record.driver_beta_sheet_ids.unit_to:
                self.unit_from = values.id
            self.sudo().write({
                'request_owner_id': self.approval_id.request_owner_id,
                'persons_list': self.approval_id.persons_list,
                'person_count': self.approval_id.person_count,
                'type_of_vehicle': self.approval_id.type_of_vehicle,
                'vehicle_category': self.approval_id.vehicle_category,
                'vehicle_driver': self.approval_id.vehicle_driver.id or self.approval_id.emp_vehicle_driver.id,
                'emp_vechicle': self.approval_id.vechicle_list.id,
                'emp_own_vechicle': self.approval_id.emp_vechicle,
                'opening_km': self.approval_id.vechicle_list.odometer,
                'approval_trip_type': self.approval_id.approval_trip_type,
                'type_of_vehicle': self.approval_id.type_of_vehicle,
            })

        approvals = self.env['approval.request'].search([('name', '=', self.approval_id.name)])
        for travel in approvals.approval_travel_ids:
            if self.approval_id:
                vals = {
                    'source': travel.source,
                    'distination': travel.distination,
                    'start_date': travel.start_date,
                    'end_date': travel.end_date,
                    'duration': travel.duration,
                }
                line_vals.append((0, 0, vals))
                self.approval_detail_ids = line_vals

    @api.onchange('vehicle_travel_id')
    def get__employee_travel_details(self):
        line_vals = [(5, 0, 0)]
        employee_travel = self.env['two.wheeler.usage'].search([('taken_by', '=', self.vehicle_travel_id.name)])
        for rex in employee_travel:
            if self.vehicle_travel_id:
                vals = {
                    'time_out': rex.time_out,
                    'time_in': rex.time_in,
                    'opening_km': rex.opening_km,
                    'closing_km': rex.closing_km,
                    'total_km': rex.closing_km - rex.opening_km,
                    'total_amount': (rex.closing_km - rex.opening_km) * 3,
                }
            line_vals.append((0, 0, vals))
            self.travel_detail_ids = line_vals

    @api.model
    def create(self, values):
        if not values['pass_check']:
            values['name'] = self.sudo().env['ir.sequence'].get('vehicle.gate.pass') or '/'
            res = super(VehicleGatePass, self).create(values)
        if values['pass_check']:
            values['name'] = self.sudo().env['ir.sequence'].get('vehicle.gate.in.pass') or '/'
            res = super(VehicleGatePass, self).create(values)
        return res


class ApprovalDetails(models.Model):
    _name = "approval.details"
    _description = "Approval Details"

    name = fields.Char(string="Name")
    source = fields.Char(string="From")
    distination = fields.Char(string="To")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    duration = fields.Float(string="Duration")
    approval_approved_id = fields.Many2one('vehicle.gate.pass', string="Approvals")
    name = fields.Char(string="Name", invisible=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")


class VehicleTravelDetails(models.Model):
    _name = "vehicle.travel.details"
    _description = "Vehicle Travel Details"

    name = fields.Char(string="Name")
    time_out = fields.Datetime(string="Time Out")
    time_in = fields.Datetime(string="Time In")
    opening_km = fields.Float(string="Opening KM")
    closing_km = fields.Float(string="Closing KM")
    total_km = fields.Float(string="Total KM")
    total_amount = fields.Float(string="Total Amount")
    vechile_approval_id = fields.Many2one('vehicle.gate.pass', string="Approvals")


class FleetVehicleOdometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'

    driver_name = fields.Many2one('hr.employee', string='Driver')
    driver_list = fields.Char(string='Driver')
    total_km = fields.Float(string='Total KM')
    start_km = fields.Float(string='Open KM')
