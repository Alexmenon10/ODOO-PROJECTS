from odoo import api, fields, models, _
from datetime import timedelta, datetime
from odoo.exceptions import UserError, ValidationError


class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    source_location = fields.Selection(related="category_id.source_location")
    fleet_control = fields.Selection(related="category_id.fleet_control")
    vehicle_related_approval = fields.Boolean(related="category_id.vehicle_related_approval")
    is_driver_vehicle_operation_change = fields.Boolean(string='Is Driver(or)Vehicle Change Required ?')

    persons_list = fields.Many2many('hr.employee', string="In Persons List")
    out_persons_list = fields.Char(string="Out Persons List")
    person_count = fields.Integer(string="Person Count", default=0)
    source = fields.Char(string="Source")
    distination = fields.Char(string="Distination")
    vechicle_specification = fields.Selection([
        ('close', 'Closed Type Vehicle'),
        ('open', 'Open Type Vehicle'),
    ], string='Vechicle Specification')
    approval_travel_ids = fields.One2many('approval.travel', 'approval_list_id')

    pre_appreval_list = fields.Boolean("Pre Approval")
    veh_driv_assign = fields.Boolean("Assigned")
    # pre_approval_amount = fields.Float(related='pre_approval.amount')
    # pre_approval_date = fields.Datetime(related='pre_approval.date')

    type_of_vehicle = fields.Selection([
        ('company', 'Company Owned'),
        ('employee', 'Employee Owned'),
        ('rental', 'Rental'),
    ], default='company', string='Vechicle Type')
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
    priority_level = fields.Selection([
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
        ('4', 'Very High')],
        'Priority', tracking=True)
    approval_duration = fields.Float(string='Duration', compute='_compute_duration_travel')
    vechicle_list = fields.Many2one('fleet.vehicle', string="Vechicles",
                                    domain="[('state_id', '=', 'Ready to Trip'),"
                                           "('vehicle_state', '=', 'un_reserved'),"
                                           "('model_id', '=', model_id),"
                                           "('vehicle_category', '=', vehicle_category)]")

    vehicle_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                     'Vehicle Availability', tracking=True, related='vechicle_list.vehicle_state')
    emp_vechicle = fields.Char(string="Vechicles")
    rental_vechicle = fields.Char(string="Vechicles")
    emp_vehicle_driver = fields.Many2one('hr.employee', string='Driver')
    vehicle_driver = fields.Many2one('hr.employee', string='Driver',
                                     domain="[('emp_diver', '=', True),('driver_state', '=', 'un_reserved')]")
    driver_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                    'Driver Availability', tracking=True, related='vehicle_driver.driver_state')
    vehicle_image = fields.Binary(string='Vehicl Image')
    driver_image = fields.Binary(string='Driver Image')
    model_id = fields.Many2one('fleet.vehicle.model', 'Allocated Vehicle',
                               tracking=True, help='Model of the vehicle',
                               domain="[('vehicle_type', '=', vehicle_category)]")
    available_vehicle_count = fields.Float(string='Available Count')
    approval_position = fields.Selection([('out', 'Out'), ('in', 'In'), ('finish', 'Finish')], default='in',
                                         string='Vehicle Position', tracking=True)
    vehi_divr_assigned_status = fields.Selection([('assigned', 'assigned'), ('un_assigned', 'Un Assigned')],
                                                 default='un_assigned',
                                                 string='sheduled Position', tracking=True)
    vehicle_odoometer = fields.Float(string='Odo Meter')
    # start_date = fields.Datetime(string='Start', default=datetime.datetime.now())
    start_date = fields.Datetime(string='Date',
                                 default=lambda self: fields.Datetime.now(timedelta(hours=5, minutes=30)))
    end_date = fields.Datetime(string='End')
    waring = fields.Text(string='Alert :',
                         default='"Please Select The Start date from current Datetime to Extra 15 mints to schedule the Trip."')
    total_duration = fields.Float(string='Total Duration')
    approval_driver_history_count = fields.Integer(string='Driver Scheduled Trip',
                                                   compute='approval_driver_history_count_record')
    approval_vehicle_history_count = fields.Integer(string='Vehicle Scheduled Trip',
                                                    compute='approval_vehicle_history_count_record')

    vehicle_request_reason = fields.Text('Vehicle Request Reason')
    vehicle_internal_notes = fields.Text('Vehicle Internal Notes')

    assigned_by = fields.Char(string='Assigned By')
    assigned_date = fields.Datetime(string='Assigned Date')
    approved_by = fields.Many2one('res.users', string='Approved By')
    approved_date = fields.Datetime(string='Approved Date')
    gate_pass_out_time = fields.Datetime(string='Gate Pass Out Date')
    gate_pass_out_by = fields.Many2one('res.users', string='Gate Pass Out By')
    gate_pass_in_by = fields.Many2one('res.users', string='Gate Pass In By')
    gate_pass_in_time = fields.Datetime(string='Gate Pass In Date')
    vehicle_remark = fields.Text(string='Vehicle Remark')
    driver_remark = fields.Text(string='Driver Remark')
    required_vehicle_and_driver = fields.Text(string='Requested Vehicle')

    is_driver_vehicle_operation_change = fields.Boolean(string='Is Driver(or)Vehicle Change Required ?')

    approval_trip_type = fields.Selection([
        ('one_way', 'One Way Trip'),
        ('rounded_trip', 'Rounded Trip')], string="Trip Status", default='rounded_trip')

    approval_approved_reason = fields.Text('Reason for Approval Approved')
    one_way_trip_reamrk = fields.Text('Remarks')
    one_way_attachment = fields.Binary(String="Attachments")
    one_way_attachment_detail = fields.Char(string="Attachment")

    def action_withdraw(self):
        res = super(ApprovalRequest, self).action_withdraw()
        if self.approval_fleet_status == 'close':
            raise UserError('-----------------')
        return res

    def approval_driver_history_count_record(self):
        self.approval_driver_history_count = self.env['driver.trip.history'].sudo(). \
            search_count([('source_document', '=', self.name)])

    def approval_vehicle_history_count_record(self):
        self.approval_vehicle_history_count = self.env['vehicle.trip.history'].sudo().search_count(
            [('source_document', '=', self.name)])

    @api.onchange('vehicle_driver')
    def get_driver_availability(self):
        driver = self.env['driver.trip.history'].search([('driver_name', '=', self.vehicle_driver.name)])
        for data in driver:
            for info in data.driver_travel_detail_ids:
                for trip in self.approval_travel_ids:
                    if self.vehicle_driver.driver_state == 'reserved':
                        if info.start_date <= trip.start_date <= info.end_date or info.start_date <= trip.end_date <= info.end_date:
                            raise UserError(
                                'Alert!!, You cannot Select this Driver Because this Driver iS Un Available for your Trip Date.')

    @api.onchange('vechicle_list')
    def get_vehicle_availability(self):
        vehicle = self.env['vehicle.trip.history'].search([('vehicle_name', '=', self.vechicle_list.name)])
        for data in vehicle:
            for info in data.vehicle_travel_detail_ids:
                for trip in self.approval_travel_ids:
                    if self.vechicle_list.vehicle_state == 'reserved':
                        if trip.start_date <= info.start_date <= trip.end_date or trip.start_date <= info.end_date <= trip.end_date:
                            raise UserError(
                                'Alert!!, You cannot Select this Vehicle, Because this Vehicle is Un Available for your Trip Date.')

    @api.onchange('model_id')
    def _get_count_of_vehicle(self):
        if self.model_id:
            total_vehicle = self.env['fleet.vehicle'].sudo().search(
                [('model_id.name', '=', self.model_id.name), ('vehicle_state', '=', 'un_reserved')])
            total_vehicle_count = self.env['fleet.vehicle'].sudo().search_count(
                [('model_id.name', '=', self.model_id.name), ('brand_id.name', '=', self.model_id.brand_id.name),
                 ('vehicle_state', '=', 'un_reserved')])
            self.available_vehicle_count = total_vehicle_count
            if self.available_vehicle_count == 0:
                raise UserError('Alert!!, You cannot Select This Model - %s for this Durartion. \n '
                                'All Vehicle are Already Assigned' % (self.model_id.name))

    @api.onchange('start_date', 'end_date')
    def _compute_duration_travel(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                date1 = str(rec.start_date)
                datetimeFormat = '%Y-%m-%d %H:%M:%S'
                date2 = str(rec.end_date)
                date11 = datetime.strptime(date1, datetimeFormat)
                date12 = datetime.strptime(date2, datetimeFormat)
                timedelta = date12 - date11
                tot_sec = timedelta.total_seconds()
                h = tot_sec // 3600
                m = (tot_sec % 3600) // 60
                duration_hour = ("%d.%d" % (h, m))
                rec.approval_duration = float(duration_hour)
            else:
                rec.approval_duration = False

    @api.onchange('persons_list')
    def count_employees(self):
        for employee in self:
            employee.person_count = len(self.persons_list)

    def _get_total_duration(self):
        ttl_duration = 0
        for trip in self.approval_travel_ids:
            ttl_duration += trip.duration
            self.total_duration = ttl_duration

    def get_line_items(self):
        line_vals = []
        for line in self:
            if line.source and line.distination:
                vals = [0, 0, {
                    'start_date': line.start_date,
                    'end_date': line.end_date,
                    'source': line.source,
                    'distination': line.distination,
                    'duration': line.approval_duration,
                }]
                line_vals.append(vals)
        return line_vals

    def action_split_travel(self):
        requisition_created = False
        cur_date = datetime.today()
        for rec in self:
            if rec.start_date:
                datetimeFormat = '%Y-%m-%d %H:%M:%S'
                date2 = str(self.start_date)
                date12 = datetime.strptime(date2, datetimeFormat)
                if rec.start_date <= cur_date:
                    raise ValidationError(("Alert!,Mr. %s. \n Trip Start Date should be Graterthan than Current Date.") \
                                          % (rec.env.user.name))
            if rec.end_date:
                if rec.end_date <= rec.start_date:
                    raise ValidationError(("Alert!,Mr. %s. \n Trip End Date should be Lessthan than Start Date.") \
                                          % (rec.env.user.name))
            for trip in rec.approval_travel_ids:
                if trip.start_date <= rec.start_date <= trip.end_date or trip.start_date <= rec.end_date <= trip.end_date:
                    raise ValidationError(("Alert!,Mr. %s. \n You'r selected Already Scheduled Date, Trip Start & End Date should be Graterthan than Current Datetime.") \
                                          % (rec.env.user.name))
                if rec.start_date < trip.start_date:
                    raise ValidationError(("Alert!,Mr. %s. \n ____________Success___________.") \
                                          % (rec.env.user.name))
        for line in self:
            requisition_created = line.update({
                'source': False,
                'distination': False,
                'start_date': False,
                'end_date': False,
                'approval_travel_ids': line.get_line_items(),
            })
            # self.trip_count = len(self.approval_travel_ids)
            self._get_total_duration()
            return True

    def set_employee_reserved(self):
        view_id = self.env['driver.trip.details']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Driver Trip Details',
            'res_model': 'driver.trip.details',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('appscomp_fleet.driver_trip_details_form', False).id,
            'target': 'new',
        }

    def open_employee_trip_form(self):
        employee = self.env['hr.employee'].search([('name', '=', self.vehicle_driver.name)])
        action = self.env.ref('appscomp_fleet.driver_trip_details_action')
        result = action.read()[0]
        order_line = []
        order_line_available = []
        driver_warning = 'Alert, Mr.' + self.env.user.name + ', The Reference ' + self.name + ', Trip Scheduled cannot be taken forward,' \
                                                                                              'against. The Driver - Mr.' + \
                         self.vehicle_driver.name + ' will not be available for next '

        vehicle_warning = 'Alert, Mr.' + self.env.user.name + ', The Reference ' + self.name + ', Trip Scheduled cannot be taken forward,' \
                                                                                               'against. The Vehicle - Mr.' + self.vechicle_list.name + ' will not be available for next .'
        total_hours = 24.00
        for line in self.approval_travel_ids:
            available_hours = total_hours - line.duration
            order_line.append({
                'start_date': line.start_date or False,
                'end_date': line.end_date or False,
                'source': line.source or False,
                'distination': line.distination or False,
                'duration': line.duration or False,
            })
            if available_hours >= 0.00:
                order_line_available.append({
                    'date': line.start_date or False,
                    'available_hour': available_hours or False,
                })
            else:
                order_line_available.append({
                    'date': line.start_date or False,
                    'available_hour': 0.00,
                })

            result['context'] = {
                'default_remarks': driver_warning,
                'default_remark_reason': vehicle_warning,
                'default_vechicle_list': self.vechicle_list.id,
                'default_vehicle_driver': self.vehicle_driver.id,
                'default_total_duration': self.total_duration,
                'default_reference': self.name,
                'default_name': self.id,
                'default_driver_trip_list_ids': order_line,
                'default_driver_trip_available_ids': order_line_available,
            }
        return result

    def change_assigned_dri_veh(self):
        action = self.env.ref('appscomp_fleet.driver_vehicle_update_action')
        result = action.read()[0]
        for line in self:
            result['context'] = {
                'default_name': self.id,
            }
        return result

    def _prepare_driver_travel_history(self, order_line):
        return {
            'start_date': order_line.start_date or False,
            'end_date': order_line.end_date or False,
            'travel_from': order_line.source or False,
            'travel_to': order_line.distination or False,
            'duration': order_line.duration or False,
        }

    def _prepare_driver_trip_history(self, order, approval_travel_ids):
        return {
            'driver_name': order.vehicle_driver.id and order.vehicle_driver.id or False,
            'vehicle_name': order.vechicle_list.id and order.vechicle_list.id or False,
            'driver_state': order.vehicle_driver.driver_state and order.vehicle_driver.driver_state or False,
            'driver_position': order.vehicle_driver.driver_position and order.vehicle_driver.driver_position or False,
            'driver_approval_request_id': order.id,
            'type_of_vehicle': order.type_of_vehicle,
            'vehicle_category': order.vehicle_category,
            'persons_list': order.persons_list,
            'source_document': order.name and order.name or False,
            # 'opening_km': order.opening_km and order.opening_km or False,
            'driver_travel_detail_ids': [(6, 0, approval_travel_ids)],
        }

    def create_sheduled_driver_trip(self):
        driver_trip_history_obj = self.env['driver.trip.history']
        driver_travel_history_obj = self.env['driver.travel.history']
        res = False
        for order in self:
            driver_travel_history_lines = []
            for so_line in order.approval_travel_ids:
                driver_travel_history = order._prepare_driver_travel_history(so_line)
                driver_travel_history_id = driver_travel_history_obj.create(driver_travel_history)
                driver_travel_history_lines.append(driver_travel_history_id.id)
            driver_trip_history_data = order._prepare_driver_trip_history(order, driver_travel_history_lines)
            driver_trip_history_data_id = driver_trip_history_obj.create(driver_trip_history_data)

    def _prepare_vehicle_trip_history(self, order, approval_travel_ids):
        return {
            'vehicle_name': order.vechicle_list.id and order.vechicle_list.id or False,
            'driver_name': order.vehicle_driver.id and order.vehicle_driver.id or False,
            'vehicle_state': order.vechicle_list.vehicle_state and order.vechicle_list.vehicle_state or False,
            'vehicle_position': order.vechicle_list.vehicle_position and order.vechicle_list.vehicle_position or False,
            'vehicle_approval_request_id': order.id,
            'source_document': order.name and order.name or False,
            'vehicle_travel_detail_ids': [(6, 0, approval_travel_ids)],
        }

    def _prepare_vehicle_travel_history(self, order_line):
        return {
            'start_date': order_line.start_date or False,
            'end_date': order_line.end_date or False,
            'travel_from': order_line.source or False,
            'travel_to': order_line.distination or False,
            'duration': order_line.duration or False,
        }

    def create_sheduled_vehicle_trip(self):
        vehicle_trip_history_obj = self.env['vehicle.trip.history']
        vehicle_travel_history_obj = self.env['vehicle.travel.history']
        res = False
        for order in self:
            vehicle_travel_history_lines = []
            for so_line in order.approval_travel_ids:
                vehicle_travel_history = order._prepare_vehicle_travel_history(so_line)
                vehicle_travel_history_id = vehicle_travel_history_obj.create(vehicle_travel_history)
                vehicle_travel_history_lines.append(vehicle_travel_history_id.id)
            vehicle_trip_history_data = order._prepare_vehicle_trip_history(order, vehicle_travel_history_lines)
            vehicle_trip_history_data_id = vehicle_trip_history_obj.create(vehicle_trip_history_data)

    def employee_vehicle_details(self):
        pass

    def approval_driver_history_record(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('appscomp_fleet.view_driver_trip_history_form')
        tree_view = self.sudo().env.ref('appscomp_fleet.view_driver_trip_history_tree')
        return {
            'name': _('Approval Request Driver Trip History'),
            'res_model': 'driver.trip.history',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('source_document', '=', self.name)],
        }

    def approval_vehicle_history_record(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('appscomp_fleet.view_vehicle_trip_history_form')
        tree_view = self.sudo().env.ref('appscomp_fleet.view_vehicle_trip_history_tree')
        return {
            'name': _('Approval Request Vehicle Trip History'),
            'res_model': 'vehicle.trip.history',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('source_document', '=', self.name)],
        }


class ApprovalTravel(models.Model):
    _name = "approval.travel"
    _description = 'Approval Travel'

    source = fields.Char(string="From")
    distination = fields.Char(string="To")
    duration = fields.Float(string="Duration")
    travel_date = fields.Date(string="Travel Date")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")
    approval_list_id = fields.Many2one('approval.request', string="Approvals")

    pre_approval_from = fields.Char(string='From')
    pre_approval_to = fields.Char(string='To')
    pre_approval_travel_date = fields.Date(string="Date")


class DriverInOutDetails(models.Model):
    _name = 'driver.in.out.details'
    _description = 'Driver In Out Details'

    driver_in_out_details_id = fields.Many2one('hr.employee', string='Driver In/Out Details')
    driver_history_id = fields.Many2one('driver.trip.history', string='Driver History')
    reference = fields.Char(string='Reference')
    in_time = fields.Datetime(string='In Time')
    out_time = fields.Datetime(string='Out Time')
    out_verified_by = fields.Many2one('hr.employee', string='Out Security')
    in_verified_by = fields.Many2one('hr.employee', string='In Security')
    out_verified_date = fields.Datetime(string='Out Verified Date')
    in_verified_date = fields.Datetime(string='In Verified Date')
    duration = fields.Float(string='Duration')

    unit_from = fields.Many2one('stock.location', string="Unit From")
    unit_to = fields.Many2one('stock.location', string="Unit to")
    ref_name = fields.Many2one('vehicle.gate.pass', string='Name')


class Employee(models.Model):
    _inherit = 'hr.employee'

    emp_diver = fields.Boolean(string='Driver')
    driver_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                    default='un_reserved',
                                    string='Driver State', tracking=True)
    driver_position = fields.Selection([('out', 'Out'), ('in', 'In')], default='in',
                                       string='Driver Position', tracking=True)
    contract_employee = fields.Boolean(string='Contract Employee..?')
    driver_licence_registration_date = fields.Date('Licence Registration Date')
    driver_licence_expire_date = fields.Date('Licence Expire Date')
    driver_licence_no = fields.Char('Licence No')

