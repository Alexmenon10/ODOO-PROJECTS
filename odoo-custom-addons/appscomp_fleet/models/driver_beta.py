from odoo import api, fields, models, _
from datetime import datetime


class DriverMPSheet(models.Model):
    _name = 'driver.beta.sheet'
    _description = "Store Driver Man Power Sheet Information"

    driver_name = fields.Many2one('hr.employee', string='Driver')
    Id_no = fields.Integer(string="ID NO")
    today_date = fields.Datetime(string='Date', default=datetime.today())
    vehicle = fields.Char(string="Vehicle")
    admin_name = fields.Char(string="Admin Name")
    approved_by = fields.Char(string="Approved By")
    time_from = fields.Datetime(string="Time From")
    time_to = fields.Datetime(string="Time To")
    location = fields.Char(string="Location")
    front_office = fields.Char(string="Front Office")
    amount = fields.Float(string="Amount")
    department_sign = fields.Binary(string="Department Sign ")
    name = fields.Char(string='Reference', size=256, tracking=True, required=True, copy=False,
                       index=True, default=lambda self: _('/'),
                       help='A unique sequence number for the Indent')
    state = fields.Selection([('draft', 'Draft'), ('cancel', 'Cancelled'),('approve', 'Approved'),
                              ('reject', 'Rejected')], 'State', default="draft",  tracking=True)
    driver_beta_detail_ids = fields.One2many('driver.beta.detail', 'driver_beta_detail_id')

    total_working_time = fields.Float(string='Total Working Time')
    total_working_distance = fields.Float(string='Working Distance')
    enable_expense_beta_sheet = fields.Boolean(string="Expense Beta Sheet")

    working_time = fields.Float(string='Working Time')
    beta_sheet_type = fields.Selection([('time_base', 'Time'), ('km_base', 'KM')],
                                       'BETA Based', tracking=True)

    my_expense_beta_count = fields.Integer(compute='compute_expense_beta_sheet', string='Expense Beta',
                                             default=0)

    def compute_expense_beta_sheet(self):
        self.my_expense_beta_count = self.env['hr.expense'].sudo().search_count(
            [('reference', '=', self.name)])

    def expense_beta_sheet_list(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('hr_expense.hr_expense_view_form')
        tree_view = self.sudo().env.ref('hr_expense.view_my_expenses_tree')
        return {
            'name': _('My Expense Report'),
            'res_model': 'hr.expense',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('reference', '=', self.name)],
        }

    @api.onchange('driver_name')
    def _get_driver_beta_details(self):
        line_vals = [(5, 0, 0)]
        driver = self.env['driver.trip.history'].search([('driver_name', '=', self.driver_name.name)])
        for data in driver:
            for info in data.driver_beta_sheet_ids:
                vals = {
                    'ref_name': info.ref_name,
                    'reference': info.reference,
                    'unit_from': info.unit_from,
                    'out_time': info.out_time,
                    'out_verified_by': info.out_verified_by,
                    'unit_to': info.unit_to,
                    'in_time': info.in_time,
                    'in_verified_by': info.in_verified_by,
                    'duration': info.duration,
                    'total_kilometer': info.total_kilometer,
                    'opening_km': info.opening_km,
                    'closing_km': info.closing_km,
                    'vehicle_name': data.vehicle_name,
                }
                line_vals.append((0, 0, vals))
                self.driver_beta_detail_ids = line_vals
        for rec in self.driver_beta_detail_ids:
            self.total_working_time += rec.duration
            self.total_working_distance += rec.total_kilometer
            trip_out_time = rec.out_time.date()
            trip_in_time = rec.in_time.date()
            if trip_in_time == trip_out_time:
                pass

    def driver_beta_approve(self):
        self.write({'state': 'approve', 'approved_by': self._uid})

    def driver_beta_cancel(self):
        self.write({'state': 'cancel'})

    def driver_beta_reject(self):
        self.write({'state': 'reject'})

    def get_driver_beta_expense(self):
        view_id = self.env['expense.beta.sheet']
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense Beta Sheet',
            'res_model': 'expense.beta.sheet',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': view_id.id,
            'view_id': self.env.ref('appscomp_fleet.expense_beta_sheet_wizard_form', False).id,
            'target': 'new',
        }


    @api.model
    def create(self, values):
        values['name'] = self.sudo().env['ir.sequence'].get('driver.beta.sheet') or '/'
        res = super(DriverMPSheet, self).create(values)
        return res


class DriverBetaDetail(models.Model):
    _name = 'driver.beta.detail'
    _description = "Driver Beta Detail"

    driver_beta_detail_id = fields.Many2one('driver.beta.sheet', string="Vehicle Name ")
    reference = fields.Char(string='Reference')
    in_time = fields.Datetime(string='In Time')
    out_time = fields.Datetime(string='Out Time')
    out_verified_by = fields.Many2one('hr.employee', string='Out Verified By')
    in_verified_by = fields.Many2one('hr.employee', string='In Verified By')
    duration = fields.Float(string='Duration')
    str_duration = fields.Char(string="Durations")
    total_kilometer = fields.Float(string='Total Distance')

    unit_from = fields.Many2one('stock.location', string="Unit From")
    unit_to = fields.Many2one('stock.location', string="Unit to")
    ref_name = fields.Many2one('vehicle.gate.pass', string='Name')
    opening_km = fields.Float(string="Opening KM")
    closing_km = fields.Float(string="Closing KM")
    vehicle_name = fields.Many2one('fleet.vehicle', string="Vechicle")


class DriverTrackingStatus(models.Model):
    _name = 'driver.tracking.status'
    _description = "Driver Tracking Status"

    driver_name = fields.Many2one('hr.employee', string="Driver Name")
    driver_id = fields.Char(string='Driver Id')
    driver_department = fields.Many2one(string='Department', related='driver_name.department_id', tracking=True)
    driver_job_id = fields.Many2one(related='driver_name.job_id', string="Job Position")
    driver_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                    'Driver State', tracking=True)
    driver_position = fields.Selection([('out', 'Out'), ('in', 'In')],
                                       'Driver Position', tracking=True)
    curnt_status = fields.Char(string='Current Status')


    def driver_tracking(self):
        driver = self.env['driver.trip.history'].search([('driver_name', '=', self.driver_name.name)])
        cur_date = datetime.now()
        for rec in driver.driver_travel_detail_ids:
            start_date = rec.start_date
            end_date = rec.end_date
            if start_date < cur_date < end_date:
                from_to_state = rec.travel_from + '  -  ' + rec.travel_to
                self.curnt_status = from_to_state
            if not start_date < cur_date < end_date:
                self.curnt_status = False
        self.write({
            'driver_department': self.driver_name.department_id,
            'driver_job_id': self.driver_name.job_id,
            'driver_state': self.driver_name.driver_state,
            'driver_position': self.driver_name.driver_position,
        })

    def driver_history(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('appscomp_fleet.view_driver_trip_history_form')
        tree_view = self.sudo().env.ref('appscomp_fleet.view_driver_trip_history_tree')
        return {
            'name': _('Driver History'),
            'res_model': 'driver.trip.history',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'),(form_view.id, 'form')],
            'domain': [('driver_name.id', '=', self.driver_name.id)],
        }


class VehicleTrackingStatus(models.Model):
    _name = 'vehicle.tracking.status'
    _description = "Vehicle Tracking Status"

    vehicle_name = fields.Many2one('fleet.vehicle', string="Vehicle Name ", required=True)
    vehicle_state = fields.Selection([('un_reserved', 'Available'), ('reserved', 'Un Available')],
                                     'Vechicle State', tracking=True)
    vehicle_position = fields.Selection([('out', 'Out'), ('in', 'In')],
                                        'Vehicle Position', tracking=True)


    def vehicle_tracking(self):
        self.write({
            'vehicle_state': self.vehicle_name.vehicle_state,
            'vehicle_position': self.vehicle_name.vehicle_position,
        })

    def vehicle_history(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        tree_view = self.sudo().env.ref('appscomp_fleet.view_vehicle_trip_history_tree')
        form_view = self.sudo().env.ref('appscomp_fleet.view_vehicle_trip_history_form')
        return {
            'name': _('Driver History'),
            'res_model': 'vehicle.trip.history',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('vehicle_name.id', '=', self.vehicle_name.id)],
        }