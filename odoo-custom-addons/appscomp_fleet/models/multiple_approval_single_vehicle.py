from odoo import fields, models, api, _


class FleetMultipleAssignVehicle(models.Model):
    _name = 'fleet.multiple.assign.vehicle'
    _description = 'Fleet Multiple Assign Vehicle'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    state = fields.Selection([
        ("draft", "Draft"),
        ("assign", "Assign"),
        ("cancel", "Cancel")], default='draft', string='State')
    pass_status_gate = fields.Selection([
        ("open", "Open"),
        ("close", "Close")], default='open', string='State')

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
    approval_ids = fields.Many2many('approval.request', string='Approvals ID',
                                    domain="[('vehi_divr_assigned_status', '=', 'un_assigned'), "
                                           "('request_status', '=', 'approved')]")
    model_id = fields.Many2one('fleet.vehicle.model', 'Allocated Vehicle',
                               tracking=True, help='Model of the vehicle',
                               domain="[('vehicle_type', '=', vehicle_category)]")
    vechicle_list = fields.Many2one('fleet.vehicle', string="Vechicles",
                                    domain="[('state_id', '=', 'Ready to Trip'),"
                                           "('vehicle_state', '=', 'un_reserved'),"
                                           "('model_id', '=', model_id),"
                                           "('vehicle_category', '=', vehicle_category)]")
    vehicle_driver = fields.Many2one('hr.employee', string='Driver',
                                     domain="[('emp_diver', '=', True),('driver_state', '=', 'un_reserved')]")
    trip_details_id = fields.One2many('fleet.multiple.assign.vehicle.line', 'multiple_approval_id', string='Detail ID')
    person_list = fields.Text(string='Persons List')
    multi_approval_driver_history_count = fields.Integer(string='Driver Scheduled Trip',
                                                         compute='multi_approval_driver_history_count_record')
    multi_approval_vehicle_history_count = fields.Integer(string='Vehicle Scheduled Trip',
                                                          compute='multi_approval_vehicle_history_count_record')

    def multi_approval_driver_history_count_record(self):
        self.multi_approval_driver_history_count = self.env['driver.trip.history'].sudo(). \
            search_count([('source_document', '=', self.name)])

    def multi_approval_vehicle_history_count_record(self):
        self.multi_approval_vehicle_history_count = self.env['vehicle.trip.history'].sudo().search_count(
            [('source_document', '=', self.name)])

    def multi_approval_driver_history_record(self):
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

    def multi_approval_vehicle_history_record(self):
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

    @api.onchange('approval_ids')
    def multiple_approval_trip_details(self):
        b_list = []
        person_list = ''
        self.write({'trip_details_id': False})
        # product_ids = self.env['product.product'].search([('id', '=', self.product_id.ids)])

        approvals = self.env['approval.request'].search([('id', '=', self.approval_ids.ids)])
        for travel in approvals:

            b_list = [[0, 0, {
                'name': travel.name,
                'display_type': 'line_section',
            }]]
            person_list = ', '.join([str(partner) for partner in
                                     approvals.persons_list.mapped('name')])
            person_list += ', '.join([str(partner) for partner in
                                      approvals.mapped('out_persons_list')])
            for line in travel.approval_travel_ids:
                b_list.append([0, 0, {
                    'start_date': line.start_date or False,
                    'end_date': line.end_date or False,
                    'travel_from': line.source or False,
                    'travel_to': line.distination or False,
                    'duration': line.duration or False,
                    'duration': line.duration or False,
                }])
            self.write({'trip_details_id': b_list})
        self.person_list = person_list
        # line_vals = []
        # line_vals_23 = []
        # person_list = ''
        # approvals = self.env['approval.request'].search([('id', '=', self.approval_ids.ids)])
        # if not approvals:
        #     self.trip_details_id = False
        # for travel in approvals:
        #     person_list = ', '.join([str(partner) for partner in
        #                              approvals.persons_list.mapped('name')])
        #     person_list += ', '.join([str(partner) for partner in
        #                               approvals.mapped('out_persons_list')])
        #     self.trip_details_id = False
        #     for line in travel.approval_travel_ids:
        #         vals = [0, 0, {
        #             'start_date': line.start_date or False,
        #             'end_date': line.end_date or False,
        #             'travel_from': line.source or False,
        #             'travel_to': line.distination or False,
        #             'duration': line.duration or False,
        #         }]
        #         line_vals.append(vals)
        #         for i in line_vals:
        #             if i not in line_vals_23:
        #                 line_vals_23.append(i)
        # print('=====================================', line_vals_23)
        # self.trip_details_id = line_vals_23

    def fleet_multiple_assign_vehicle(self):
        driver_history = self.env['driver.trip.history']
        vehicle_history = self.env['vehicle.trip.history']
        id_list = []
        driver_history.create({
            'driver_name': self.vehicle_driver.id,
            'vehicle_name': self.vechicle_list.id,
            'vehicle_category': self.vehicle_category,
            'source_document': self.name,
        })
        vehicle_history.create({
            'driver_name': self.vehicle_driver.id,
            'vehicle_name': self.vechicle_list.id,
            'opening_km': self.vechicle_list.odometer,
            'source_document': self.name,
        })
        if self.vechicle_list.vehicle_state == 'un_reserved':
            self.vechicle_list.write({
                'vehicle_state': 'reserved',
                'vehicle_position': 'in',
            })
        if self.vehicle_driver.driver_state == 'un_reserved':
            self.vehicle_driver.write({
                'driver_state': 'reserved',
                'driver_position': 'in',
            })
        driver_history_id = self.env['driver.trip.history'].search([('source_document', '=', self.name)])
        vehicle_history_id = self.env['vehicle.trip.history'].search([('source_document', '=', self.name)])
        for i in self.approval_ids:
            i.write({
                'model_id': self.model_id.id,
                'vechicle_list': self.vechicle_list.id,
                'vehicle_category': self.vehicle_category,
                'vehicle_driver': self.vehicle_driver.id,
                'vehi_divr_assigned_status': 'assigned',
            })
            b_list = [[0, 0, {
                'name': i.name,
                'display_type': 'line_section',
            }]]
            for line in i.approval_travel_ids:
                b_list.append([0, 0, {
                    'start_date': line.start_date or False,
                    'end_date': line.end_date or False,
                    'travel_from': line.source or False,
                    'travel_to': line.distination or False,
                    'duration': line.duration or False,
                }])
            driver_history_id.write({'driver_travel_detail_ids': b_list})
            vehicle_history_id.write({'vehicle_travel_detail_ids': b_list})
            # line_vals = []
            # for line in i.approval_travel_ids:
            #     vals = [0, 0, {
            #         'start_date': line.start_date or False,
            #         'end_date': line.end_date or False,
            #         'travel_from': line.source or False,
            #         'travel_to': line.distination or False,
            #         'duration': line.duration or False,
            #     }]
            #     line_vals.append(vals)
            # for product in product_ids:
            #     b_list = [[0, 0, {
            #         'name': product.name,
            #         'display_type': 'line_section',
            #     }]]
            #     for line in product.boutique_id:
            #         b_list.append([0, 0, {
            #             'product_id': line.product_id.id,
            #             'boutique_uom': line.uom_id.id,
            #             'boutique_measurement': line.measurement,
            #             'boutique_name': line.boutique_feature_id.name,
            #         }])
            #     self.write({'boutique_ids': b_list})
            # driver_history_id.driver_travel_detail_ids = line_vals
            # vehicle_history_id.vehicle_travel_detail_ids = line_vals
        self.write({
            'state': 'assign',
        })

    @api.model
    def create(self, values):
        values['name'] = self.sudo().env['ir.sequence'].get('fleet.multiple.assign.vehicle') or '/'
        res = super(FleetMultipleAssignVehicle, self).create(values)
        return res


class FleetMultipleAssignVehicleLine(models.Model):
    _name = 'fleet.multiple.assign.vehicle.line'
    _description = 'Fleet Multiple Assign Vehicle'

    multiple_approval_id = fields.Many2one('fleet.multiple.assign.vehicle', string='Multiple Approval ID')
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    travel_from = fields.Char(string='From')
    travel_to = fields.Char(string='To')
    duration = fields.Char(string='Duration')
    name = fields.Char(string="Name", invisible=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
