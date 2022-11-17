from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError



class DriverOTSheet(models.Model):
    _name = 'driver.ot.sheet'
    _description = "Store Driver Over Time Sheet Information"

    driver_name = fields.Many2one('hr.employee', string='Driver')
    emp_id = fields.Char(string="Employee ID")
    driver_department = fields.Many2one('hr.department', string="Department")
    driver_job_id = fields.Many2one('hr.job', string="Job Position")
    driver_doj = fields.Date(string="DOJ")

    # driver_ot_detail_ids = fields.One2many('driver.ot.detail', 'driver_ot_detail_id')

    @api.onchange('driver_name')
    def _get_driver_ot_details(self):
        line_vals = [(5, 0, 0)]
        driver = self.env['driver.trip.history'].search([('driver_name', '=', self.driver_name.name)])
        for data in driver:
            self.sudo().write({
                'emp_id': self.driver_name.driver_ref,
                'driver_department': self.driver_name.department_id.id,
                'driver_job_id': self.driver_name.job_id.id,
                # 'driver_doj': self.driver_name.job_id.id,
            })



class DriverOTDetail(models.Model):
    _name = 'driver.ot.detail'
    _description = "Driver Over Time Detail"

    # driver_ot_detail_id = fields.Many2one('driver.ot.sheet', string="OT Sheet")
    # reference = fields.Char(string='Reference')
    # in_time = fields.Datetime(string='In Time')
    # out_time = fields.Datetime(string='Out Time')
    # out_verified_by = fields.Many2one('hr.employee', string='Out Verified By')
    # in_verified_by = fields.Many2one('hr.employee', string='In Verified By')
    # duration = fields.Float(string='Duration')
    # str_duration = fields.Char(string="Durations")
    # total_kilometer = fields.Float(string='Total Distance')
    #
    # unit_from = fields.Many2one('stock.location', string="Unit From")
    # unit_to = fields.Many2one('stock.location', string="Unit to")
    # ref_name = fields.Many2one('vehicle.gate.pass', string='Name')
    # opening_km = fields.Float(string="Opening KM")
    # closing_km = fields.Float(string="Closing KM")
    # vehicle_name = fields.Many2one('fleet.vehicle', string="Vechicle")




class OTDepartmentConfig(models.Model):
    _name = 'ot.department.config'
    _description = 'OT Department Config'

    name = fields.Char(string='Name')
    ho_department = fields.Many2one('ho.department', string='Department')
    approximate_time_delay_mrng = fields.Char(string='Mrng Time')
    approximate_time_delay_eve = fields.Char(string='Eve Time')
    work_end_time = fields.Char(string='Work End Time')
    work_start_time = fields.Char(string='Work Start Time')

    holiday_ot_amount_one = fields.Float('1 to 3 Hours')
    holiday_ot_amount_two = fields.Float('3 to 5 Hours')
    holiday_ot_amount_three = fields.Float('Above 5 Hours')

    department_ot_detail_ids = fields.One2many('ot.time.amount.details', 'department_ot_detail_id')
    department_ot_detail_two_ids = fields.One2many('ot.time.amount.details.two', 'department_ot_detail_two_id')
    department_ot_detail_holiday_ids = fields.One2many('ot.time.amount.details.holiday', 'department_ot_detail_holiday_id')




class OTTimeAmountDetail(models.Model):
    _name = 'ot.time.amount.details'
    _description = "OT Time Amount Detail"

    department_ot_detail_id = fields.Many2one('ot.department.config', string="OT Sheet Config")
    start_time = fields.Selection([
        ('00:00:00', '00:00:00'),
        ('01:00:00', '01:00:00'),
        ('02:00:00', '02:00:00'),
        ('03:00:00', '03:00:00'),
        ('04:00:00', '04:00:00'),
        ('05:00:00', '05:00:00'),
        ('06:00:00', '06:00:00'),
        ('07:00:00', '07:00:00'),
        ('08:00:00', '08:00:00'),
        ('09:00:00', '09:00:00'),
        ('10:00:00', '10:00:00'),
        ('11:00:00', '11:00:00'),
        ('12:00:00', '12:00:00'),
        ('13:00:00', '13:00:00'),
        ('14:00:00', '14:00:00'),
        ('15:00:00', '15:00:00'),
        ('16:00:00', '16:00:00'),
        ('17:00:00', '17:00:00'),
        ('18:00:00', '18:00:00'),
        ('19:00:00', '19:00:00'),
        ('20:00:00', '20:00:00'),
        ('21:00:00', '21:00:00'),
        ('22:00:00', '22:00:00'),
        ('23:00:00', '23:00:00'),
    ], string="Start Time")
    end_time = fields.Selection([
        ('00:00:00', '00:00:00'),
        ('01:00:00', '01:00:00'),
        ('02:00:00', '02:00:00'),
        ('03:00:00', '03:00:00'),
        ('04:00:00', '04:00:00'),
        ('05:00:00', '05:00:00'),
        ('06:00:00', '06:00:00'),
        ('07:00:00', '07:00:00'),
        ('08:00:00', '08:00:00'),
        ('09:00:00', '09:00:00'),
        ('10:00:00', '10:00:00'),
        ('11:00:00', '11:00:00'),
        ('12:00:00', '12:00:00'),
        ('13:00:00', '13:00:00'),
        ('14:00:00', '14:00:00'),
        ('15:00:00', '15:00:00'),
        ('16:00:00', '16:00:00'),
        ('17:00:00', '17:00:00'),
        ('18:00:00', '18:00:00'),
        ('19:00:00', '19:00:00'),
        ('20:00:00', '20:00:00'),
        ('21:00:00', '21:00:00'),
        ('22:00:00', '22:00:00'),
        ('23:00:00', '23:00:00'),
    ], string="Start Time")
    ot_amount = fields.Float(string='Amount')


class OTTimeAmountDetailTwo(models.Model):
    _name = 'ot.time.amount.details.two'
    _description = "OT Time Amount Detail Two"

    department_ot_detail_two_id = fields.Many2one('ot.department.config', string="OT Sheet Config")
    start_time = fields.Selection([
        ('00:00:00', '00:00:00'),
        ('01:00:00', '01:00:00'),
        ('02:00:00', '02:00:00'),
        ('03:00:00', '03:00:00'),
        ('04:00:00', '04:00:00'),
        ('05:00:00', '05:00:00'),
        ('06:00:00', '06:00:00'),
        ('07:00:00', '07:00:00'),
        ('08:00:00', '08:00:00'),
        ('09:00:00', '09:00:00'),
        ('10:00:00', '10:00:00'),
        ('11:00:00', '11:00:00'),
        ('12:00:00', '12:00:00'),
        ('13:00:00', '13:00:00'),
        ('14:00:00', '14:00:00'),
        ('15:00:00', '15:00:00'),
        ('16:00:00', '16:00:00'),
        ('17:00:00', '17:00:00'),
        ('18:00:00', '18:00:00'),
        ('19:00:00', '19:00:00'),
        ('20:00:00', '20:00:00'),
        ('21:00:00', '21:00:00'),
        ('22:00:00', '22:00:00'),
        ('23:00:00', '23:00:00'),
        ('23:59:59', '23:59:59'),
    ], string="Start Time")
    end_time = fields.Selection([
        ('00:00:00', '00:00:00'),
        ('01:00:00', '01:00:00'),
        ('02:00:00', '02:00:00'),
        ('03:00:00', '03:00:00'),
        ('04:00:00', '04:00:00'),
        ('05:00:00', '05:00:00'),
        ('06:00:00', '06:00:00'),
        ('07:00:00', '07:00:00'),
        ('08:00:00', '08:00:00'),
        ('09:00:00', '09:00:00'),
        ('10:00:00', '10:00:00'),
        ('11:00:00', '11:00:00'),
        ('12:00:00', '12:00:00'),
        ('13:00:00', '13:00:00'),
        ('14:00:00', '14:00:00'),
        ('15:00:00', '15:00:00'),
        ('16:00:00', '16:00:00'),
        ('17:00:00', '17:00:00'),
        ('18:00:00', '18:00:00'),
        ('19:00:00', '19:00:00'),
        ('20:00:00', '20:00:00'),
        ('21:00:00', '21:00:00'),
        ('22:00:00', '22:00:00'),
        ('23:00:00', '23:00:00'),
        ('23:59:59', '23:59:59'),
    ], string="Start Time")
    ot_amount = fields.Float(string='Amount')

class OTTimeAmountHolidays(models.Model):
    _name = 'ot.time.amount.details.holiday'
    _description = "OT Time Amount Detail Holiday"

    department_ot_detail_holiday_id = fields.Many2one('ot.department.config', string="OT Sheet Config")
    holiday_date = fields.Date(string="Date")
    holiday_name = fields.Char(string='Name')

