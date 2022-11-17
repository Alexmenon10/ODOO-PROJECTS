import base64
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models


class DriverTripDetails(models.TransientModel):
    _name = 'driver.trip.details'
    _description = 'Driver Trip Details'

    remarks = fields.Text('Warning')
    remark_reason = fields.Text('Warning')
    name = fields.Many2one('approval.request', string='Reference')
    reference = fields.Char('Reference')
    total_duration = fields.Float('Duration')
    driver_trip_list_ids = fields.One2many('driver.trip.list', 'driver_trip_details_id',
                                           string='Driver Trip List')

    vechicle_list = fields.Many2one('fleet.vehicle', string="Vechicles",
                                    domain="[('state_id', '=', 'Ready to Trip'),"
                                           "('vehicle_state', '=', 'un_reserved'),"
                                           "('model_id', '=', model_id),"
                                           "('vehicle_category', '=', vehicle_category)]")
    vehicle_driver = fields.Many2one('hr.employee', string='Driver',
                                     domain="[('emp_diver', '=', True),('driver_state', '=', 'un_reserved')]")
    driver_trip_available_ids = fields.One2many('driver.trip.available', 'driver_trip_available_id',
                                                string='Driver Trip List')
    driver_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                    'Driver State', tracking=True, related='vehicle_driver.driver_state')
    vehicle_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                     'Vehicle State', tracking=True, related='vechicle_list.vehicle_state')
    driver_vechile_update = fields.Selection([('driver', 'Driver'), ('vehicle', 'Vehicle')],
                                             'Vehicle / Driver Update', tracking=True)

    def driver_trip_update(self):
        approval = self.env['approval.request'].search([('name', '=', self.reference)])
        employee = self.env['hr.employee'].search([('name', '=', self.vehicle_driver.name)])
        vehicle = self.env['fleet.vehicle'].search([('vehicle_full_name', '=', self.vechicle_list.name)])
        ctx = self.env.context.copy()
        current_user = self.env.user.name
        current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        current_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        cc = ''
        ctx = self.env.context.copy()
        if not self.driver_vechile_update:
            if vehicle.vehicle_state == 'reserved' and employee.driver_state == 'reserved':
                raise ValidationError(
                    "The Selected Driver -%s and Vehicle - %s is already allocated, Mr.%s, you cannot allocate for this %s" %
                    (self.vehicle_driver.name, self.vechicle_list.name, self.env.user.name, self.reference))
            else:
                approval.vehi_divr_assigned_status = 'assigned'
                approval.write({
                    'vehi_divr_assigned_status': 'assigned',
                    'assigned_by': self.env.user.name,
                    'assigned_date': datetime.now(),
                    'veh_driv_assign': True,
                })

            if employee.driver_state == 'un_reserved':
                employee.write({
                    'driver_state': 'reserved',
                    'driver_position': 'in',
                })
                approval.create_sheduled_driver_trip()
            else:
                raise ValidationError(
                    "The Selected Driver -%s is already allocated, Mr.%s, you cannot allocate for this %s" %
                    (self.vehicle_driver.name, self.env.user.name, self.reference))
            if vehicle.vehicle_state == 'un_reserved':
                vehicle.write({
                    'vehicle_state': 'reserved',
                    'vehicle_position': 'in',
                    'duration': self.total_duration,
                })
                approval.create_sheduled_vehicle_trip()
            else:
                raise ValidationError(
                    "The Selected Vehicle -%s is already allocated, Mr.%s, you cannot allocate for this %s" %
                    (self.vechicle_list.name, self.env.user.name, self.reference))

        if self.driver_vechile_update == 'driver':
            if employee.driver_state == 'un_reserved':
                employee.write({
                    'driver_state': 'reserved',
                    'driver_position': 'in',
                })
                approval.create_sheduled_driver_trip()
        if self.driver_vechile_update == 'vehicle':
            if vehicle.vehicle_state == 'un_reserved':
                vehicle.write({
                    'vehicle_state': 'reserved',
                    'vehicle_position': 'in',
                    'duration': self.total_duration,
                })
                approval.create_sheduled_vehicle_trip()

        template = self.env.ref('appscomp_fleet.email_template_request_for_travel_planning_approvals',
                                False)
        template.send_mail(self.id, force_send=True)


class DriverTripList(models.TransientModel):
    _name = 'driver.trip.list'
    _description = 'Driver Trip List'

    driver_trip_details_id = fields.Many2one('driver.trip.details', string='Driver Trip Details')
    source = fields.Char(string="From")
    distination = fields.Char(string="To")
    duration = fields.Float(string="Duration")
    start_date = fields.Datetime(string="Start Date")
    end_date = fields.Datetime(string="End Date")


class DriverTripAvailable(models.TransientModel):
    _name = 'driver.trip.available'
    _description = 'Driver Trip Available'

    driver_trip_available_id = fields.Many2one('driver.trip.details', string='Driver Trip Available')
    date = fields.Datetime(string="Date")
    available_hour = fields.Float(string="Available Hour")
    trip_status = fields.Selection([('available', 'Available'), ('un_available', 'Un_Available')],
                                   default='available', string='Trip Status', tracking=True)


class AssignedVehDriUpdate(models.TransientModel):
    _name = 'update.vehicle.driver'
    _description = 'Assigned Vehicle Driver Update'

    driver_list = fields.Many2one('hr.employee', string='Driver',
                                  domain="[('emp_diver', '=', True),('driver_state', '=', 'un_reserved')]")
    vechicle_list = fields.Many2one('fleet.vehicle', string="Vechicles",
                                    domain="[('state_id', '=', 'Ready to Trip'),"
                                           "('vehicle_state', '=', 'un_reserved')]")
    vehicle_remark = fields.Text('Remark')
    driver_remark = fields.Text('Remark')
    name = fields.Many2one('approval.request', string='Reference')
    vehicle_select = fields.Boolean('Vehicle')
    driver_select = fields.Boolean('Driver')

    def get_driver_vehicle_update(self):
        approval = self.env['approval.request'].search([('name', '=', self.name.name)])
        if self.vechicle_list:
            approval.write({
                'vechicle_list': self.vechicle_list,
                'vehicle_remark': self.vehicle_remark,
            })
        if self.driver_list:
            approval.write({
                'vehicle_driver': self.driver_list,
                'driver_remark': self.driver_remark,
            })

# class SetContractEmployee(models.TransientModel):
#     _name = 'set.contract.employee'
#     _description = 'Set Contract Employee'
#
#     name = fields.Many2one('hr.employee', string='Reference')
#     contract_employee_remark = fields.Text('Remark', default='The Employee Type Still not Selected. Do you want set as Contract Employee ?')
#     contract_employee = fields.Boolean(string='Contract Employee..?')
#
#     def set_contract_employee(self):
#         applicant_id = self._context.get('active_ids')[0]
#         active_id = self.env['hr.employee'].search([('id', '=', applicant_id)])
#         active_id.write({'contract_employee': self.contract_employee})
