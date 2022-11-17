from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
import itertools
from operator import itemgetter
from odoo.exceptions import Warning
from odoo import tools
from odoo.exceptions import UserError, ValidationError
from xlwt import easyxf
import datetime
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pdb

cell = easyxf('pattern: pattern solid, fore_colour yellow')
ADDONS_PATH = tools.config['addons_path'].split(",")[-1]

MONTH_LIST = [('1', 'Jan'), ('2', 'Feb'), ('3', 'Mar'),
              ('4', 'Apr'), ('5', 'May'), ('6', 'Jun'),
              ('7', 'Jul'), ('8', 'Aug'), ('9', 'Sep'),
              ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')]


class FourWheelerUsageReport(models.TransientModel):
    _name = 'driver.ot.report.wizard'
    _description = 'Driver OT Report Wizard'

    start_date = fields.Datetime('Start date', required=True)
    end_date = fields.Datetime('End date', required=True)
    attachment = fields.Binary('File')
    attach_name = fields.Char('Attachment Name')
    summary_file = fields.Binary('Fleet Vehicle  Usage Report')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Fleet Vehicle  Usage Report')
    current_time = fields.Date('Current Time', default=lambda self: fields.Datetime.now())
    ams_time = datetime.now() + timedelta(hours=5, minutes=30)
    date = ams_time.strftime('%d-%m-%Y %H:%M:%S')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)

    driver_name = fields.Many2one('hr.employee', string='Driver Name')
    emp_id = fields.Char(string="Employee ID")
    driver_department = fields.Many2one('hr.department', string="Department")
    driver_job_id = fields.Many2one('hr.job', string="Job Position")
    driver_doj = fields.Date(string="DOJ")
    ho_department = fields.Many2one('ho.department', string='Department')

    @api.onchange('driver_name')
    def _get_driver_ot_details(self):
        if self.driver_name:
            self.sudo().write({
                # 'emp_id': self.driver_name.driver_ref,
                'driver_department': self.driver_name.department_id.id,
                'driver_job_id': self.driver_name.job_id.id,
                # 'driver_doj': self.driver_name.job_id.id,
            })

    def action_get_driver_ot_report(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('Fleet Vehicle  Usage Report')

        design_6 = easyxf('align: horiz left;font: bold 1;')
        design_7 = easyxf('align: horiz center;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_13 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')

        for record in self:
            start_date = record.start_date
            end_date = record.end_date
            import datetime
            d11 = str(start_date)
            dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d %H:%M:%S')
            starts_process = dt21.strftime("%d/%m/%Y %H:%M:%S")
            d22 = str(end_date)
            dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
            ends_process = dt22.strftime("%d/%m/%Y %H:%M:%S")
            domain = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.driver_name', '=', record.driver_name.id),
            ]
            domain1 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
            ]
            department_config = self.env['ot.department.config'].sudo().search(
                [('ho_department', '=', self.ho_department.name)])

        rows = 0
        cols = 0
        # row_pq = 7

        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.set_remove_splits(True)

        col_1 = 0
        worksheet1.write_merge(rows, rows, 2, 6, 'DRIVER OT PAYMENT INFORMATION', design_13)
        rows += 1
        worksheet1.write(rows, 3, 'START DATE', design_13)
        worksheet1.write(rows, 4, self.start_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, 3, 'END DATE', design_13)
        worksheet1.write(rows, 4, self.end_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        if self.driver_name:
            row_pq = 7
            worksheet1.col(0).width = 1800
            worksheet1.col(1).width = 6000
            worksheet1.col(2).width = 5000
            worksheet1.col(3).width = 5000
            worksheet1.col(4).width = 3000
            worksheet1.col(5).width = 3000
            worksheet1.col(6).width = 4800
            worksheet1.col(7).width = 6000
            worksheet1.col(8).width = 4000
            worksheet1.col(9).width = 4500
            worksheet1.col(10).width = 5500
            worksheet1.col(11).width = 4500
            worksheet1.col(12).width = 3500
            worksheet1.col(13).width = 5000
            worksheet1.col(14).width = 5000
            worksheet1.col(15).width = 5000
            worksheet1.write(rows, 3, 'HO DEPARTMET', design_13)
            worksheet1.write(rows, 4, self.ho_department.name, design_7)
            rows += 1
            worksheet1.write(rows, 3, 'WORK START', design_13)
            worksheet1.write(rows, 4, department_config.work_start_time, design_7)
            rows += 1
            worksheet1.write(rows, 3, 'WORK END', design_13)
            worksheet1.write(rows, 4, department_config.work_end_time, design_7)
            rows += 1

            # rows = 1
            # worksheet1.write(rows, 6, 'EMPLOYEE ID', design_13)
            # worksheet1.write(rows, 7, self.emp_id, design_8)
            rows += 1
            worksheet1.write(rows, 6, 'EMPLOYEE NAME', design_13)
            worksheet1.write(rows, 7, self.driver_name.name, design_8)
            rows += 1
            worksheet1.write(rows, 6, 'DEPARTMENT', design_13)
            worksheet1.write(rows, 7, self.driver_department.name, design_8)
            rows += 1
            worksheet1.write(rows, 6, 'JOB POSITION', design_13)
            worksheet1.write(rows, 7, self.driver_job_id.name, design_8)
            rows += 2

            worksheet1.write(rows, col_1, _('Sl.No'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('DATE'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('VEHICLE NAME'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('APPROVAL NUMBER'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OUT TIME'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('IN TIME'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT TIME (MRNG)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT AMOUNT (MRNG)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT TIME (EVE)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT AMOUNT (EVE)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT AMOUNT (HOLIDAY)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('FIXED AMOUNT'), design_13)
            col_1 += 1

            sl_no = 1
            row_pq = row_pq + 1
            mr_num = []
            res = []
            driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain)
            if driver_beta:
                for record in driver_beta:
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if record.out_time and record.in_time:
                        datetime_out = (record.out_time + timedelta(hours=5, minutes=30))
                        datetime_in = (record.in_time + timedelta(hours=5, minutes=30))
                        ot_datetime_check_one = timedelta(hours=3, minutes=00)
                        ot_datetime_check_two = timedelta(hours=5, minutes=00)
                        out_date = datetime_out.date()
                        in_date = datetime_in.date()
                        out_hour = str(datetime_out.time()).split(".")[0]
                        in_hour = str(datetime_in.time()).split(".")[0]
                        ot_start_hour = timedelta(hours=4, minutes=00)
                        sample = timedelta(hours=00, minutes=00)
                        ot_stat_time = (datetime.datetime.strptime(str(ot_start_hour), '%H:%M:%S')).time()
                        sample_time = (datetime.datetime.strptime(str(sample), '%H:%M:%S'))
                        work_out_hour = datetime.datetime.strptime(out_hour, '%H:%M:%S').time()
                        work_in_hour = datetime.datetime.strptime(in_hour, '%H:%M:%S')
                        d22 = str(out_date).split(".")[0]
                        dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d')
                        out_day_name = dt22.weekday()
                        last_out_date = dt22.strftime("%d/%m/%Y")
                        d11 = str(in_date).split(".")[0]
                        dt11 = datetime.datetime.strptime(d11, '%Y-%m-%d')
                        in_day_name = dt11.weekday()
                        last_in_date = dt11.strftime("%d/%m/%Y")
                        ot_amount_mrg = 0
                        ot_amount_eve = 0
                        holiday_amount = 0
                        for ot_config in department_config.department_ot_detail_ids:
                            config_start = (datetime.datetime.strptime(ot_config.start_time, '%H:%M:%S')).time()
                            config_end = (datetime.datetime.strptime(ot_config.end_time, '%H:%M:%S')).time()
                            config_work_start = (
                                datetime.datetime.strptime(department_config.work_start_time, '%H:%M:%S'))
                            config_work_delay_start = (
                                datetime.datetime.strptime(department_config.approximate_time_delay_mrng, '%H:%M:%S'))
                            mrng_ot_availble = config_work_start - config_work_delay_start
                            work_out_hour_final = str(work_out_hour).split(':')
                            ot_hour = str(config_work_start - timedelta(hours=int(work_out_hour_final[0]),
                                                                        minutes=int(work_out_hour_final[1]))).split(
                                ' ')[1].split(', ')[-1]
                            mrng_ot_availble_final = datetime.datetime.strptime(str(mrng_ot_availble),
                                                                                '%H:%M:%S').time()
                            if out_day_name == 6:
                                holiday_hour = datetime_in - datetime_out
                                if holiday_hour < ot_datetime_check_one:
                                    holiday_amount = department_config.holiday_ot_amount_one
                                elif ot_datetime_check_one < holiday_hour and ot_datetime_check_two > holiday_hour:
                                    holiday_amount = department_config.holiday_ot_amount_two
                                elif ot_datetime_check_two + timedelta(hours=3,
                                                                       minutes=00) > holiday_hour and holiday_hour > ot_datetime_check_two:
                                    holiday_amount = department_config.holiday_ot_amount_three
                            else:
                                if work_out_hour:
                                    if work_out_hour <= mrng_ot_availble_final:
                                        conf_start = ot_config.start_time
                                        my_datetime_start = \
                                        str(datetime.datetime.strptime(conf_start, "%H:%M:%S")).split(' ')[1]
                                        conf_end = ot_config.end_time
                                        my_datetime_end = \
                                        str(datetime.datetime.strptime(conf_end, "%H:%M:%S")).split(' ')[1]
                                        if (out_hour > my_datetime_start) and (out_hour < my_datetime_end):
                                            ot_amount_mrg = ot_config.ot_amount

                        for ot_config_two in department_config.department_ot_detail_two_ids:
                            config_work_end = (datetime.datetime.strptime(department_config.work_end_time, '%H:%M:%S'))
                            config_work_delay_end = department_config.approximate_time_delay_eve.split(':')
                            hour = int(config_work_delay_end[0])
                            min = int(config_work_delay_end[1])
                            second = config_work_delay_end[2]
                            sample_time_eve = (config_work_end + timedelta(hours=hour, minutes=min))
                            work_in_hour_final = (str(work_in_hour).split(' ')[1]).split(':')
                            ot_hour_eve = str(work_in_hour - config_work_end).split(', ')[-1]
                            eve_ot_availble = datetime.datetime.strptime(str(sample_time_eve).split(' ')[1], '%H:%M:%S')
                            if in_day_name == 6:
                                holiday_hour = datetime_in - datetime_out
                                if holiday_hour < ot_datetime_check_one:
                                    holiday_amount = department_config.holiday_ot_amount_one
                                elif ot_datetime_check_one < holiday_hour and ot_datetime_check_two > holiday_hour:
                                    holiday_amount = department_config.holiday_ot_amount_two
                                elif ot_datetime_check_two + timedelta(hours=3,
                                                                       minutes=00) > holiday_hour and holiday_hour > ot_datetime_check_two:
                                    holiday_amount = department_config.holiday_ot_amount_three
                            else:
                                if work_in_hour:
                                    if work_in_hour > eve_ot_availble:
                                        conf_start_two = ot_config_two.start_time
                                        my_datetime_start_two = \
                                        str(datetime.datetime.strptime(conf_start_two, "%H:%M:%S")).split(' ')[1]
                                        conf_end_two = ot_config_two.end_time
                                        my_datetime_end_two = \
                                        str(datetime.datetime.strptime(conf_end_two, "%H:%M:%S")).split(' ')[1]
                                        if (in_hour > my_datetime_start_two) and (in_hour < my_datetime_end_two):
                                            ot_amount_eve = ot_config_two.ot_amount

                        ot_amount_fulll = ot_amount_mrg + ot_amount_eve + holiday_amount
                        if out_date == in_date:
                            worksheet1.write(row_pq, 1, str(out_date), design_8)
                        else:
                            worksheet1.write(row_pq, 1, str(out_date) + ' to ' + str(in_date), design_8)
                        if record.driver_history_id.vehicle_name:
                            worksheet1.write(row_pq, 2, record.driver_history_id.vehicle_name.name, design_8)
                        elif record.driver_history_id.emp_vehicle:
                            worksheet1.write(row_pq, 2, record.driver_history_id.emp_vehicle, design_8)
                        else:
                            worksheet1.write(row_pq, 2, '-', design_7)
                        if record.reference:
                            worksheet1.write(row_pq, 3, record.reference, design_8)
                        else:
                            worksheet1.write(row_pq, 3, '-', design_7)
                        if out_hour:
                            worksheet1.write(row_pq, 4, out_hour, design_9)
                        else:
                            worksheet1.write(row_pq, 4, '-', design_7)
                        if in_hour:
                            worksheet1.write(row_pq, 5, in_hour, design_9)
                        else:
                            worksheet1.write(row_pq, 5, '-', design_7)
                        if ot_amount_mrg:
                            worksheet1.write(row_pq, 6, str(ot_hour), design_9)
                        else:
                            worksheet1.write(row_pq, 6, '-', design_7)
                        if ot_amount_mrg:
                            worksheet1.write(row_pq, 7, ot_amount_mrg, design_9)
                        else:
                            worksheet1.write(row_pq, 7, '-', design_7)
                        if ot_amount_eve:
                            worksheet1.write(row_pq, 8, str(ot_hour_eve), design_9)
                        else:
                            worksheet1.write(row_pq, 8, '-', design_7)
                        if ot_amount_eve:
                            worksheet1.write(row_pq, 9, ot_amount_eve, design_9)
                        else:
                            worksheet1.write(row_pq, 9, '-', design_7)
                        if holiday_amount:
                            worksheet1.write(row_pq, 10, holiday_amount, design_9)
                        else:
                            worksheet1.write(row_pq, 10, '-', design_7)
                        if ot_amount_fulll:
                            worksheet1.write(row_pq, 11, ot_amount_fulll, design_9)
                        else:
                            worksheet1.write(row_pq, 11, '-', design_7)
                        sl_no += 1
                        row_pq += 1

            else:
                raise ValidationError('No Record')


        elif not self.driver_name:
            row_pq = 5
            worksheet1.col(0).width = 1400
            worksheet1.col(1).width = 6000
            worksheet1.col(2).width = 5000
            worksheet1.col(3).width = 5000
            worksheet1.col(4).width = 5500
            worksheet1.col(5).width = 4000
            worksheet1.col(6).width = 5000
            worksheet1.col(7).width = 5000
            worksheet1.col(8).width = 4000
            worksheet1.col(9).width = 3000
            worksheet1.col(10).width = 3000
            worksheet1.col(11).width = 4000
            worksheet1.col(12).width = 4800
            worksheet1.col(13).width = 4000
            worksheet1.col(14).width = 4500
            worksheet1.col(15).width = 5500
            worksheet1.col(16).width = 4500

            worksheet1.write(rows, 3, 'WORK START', design_13)
            worksheet1.write(rows, 4, department_config.work_start_time, design_7)
            rows += 1
            worksheet1.write(rows, 3, 'WORK END', design_13)
            worksheet1.write(rows, 4, department_config.work_end_time, design_7)
            rows += 1

            worksheet1.write(rows, col_1, _('Sl.No'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('DATE'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('EMPLOYEE ID'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('EMPLOYEE NAME'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('DEPARTMET'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('JOB POSITION'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('VEHICLE NAME'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('APPROVAL NUMBER'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('HO DEPARTMET'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OUT TIME'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('IN TIME'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT TIME (MRNG)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT AMOUNT (MRNG)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT TIME (EVE)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT AMOUNT (EVE)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('OT AMOUNT (HOLIDAY)'), design_13)
            col_1 += 1
            worksheet1.write(rows, col_1, _('FIXED AMOUNT'), design_13)
            col_1 += 1

            sl_no = 1
            row_pq = row_pq + 1
            mr_num = []
            res = []
            driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain1)
            department_config = record.env['ot.department.config'].sudo().search(
                [('ho_department', '=', record.ho_department.name)])
            if driver_beta:
                for record in driver_beta:
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if record.out_time and record.in_time:
                        datetime_out = (record.out_time + timedelta(hours=5, minutes=30))
                        datetime_in = (record.in_time + timedelta(hours=5, minutes=30))
                        ot_datetime_check_one = timedelta(hours=3, minutes=00)
                        ot_datetime_check_two = timedelta(hours=5, minutes=00)
                        out_date = datetime_out.date()
                        in_date = datetime_in.date()
                        out_hour = str(datetime_out.time()).split(".")[0]
                        in_hour = str(datetime_in.time()).split(".")[0]
                        ot_start_hour = timedelta(hours=4, minutes=00)
                        sample = timedelta(hours=00, minutes=00)
                        ot_stat_time = (datetime.datetime.strptime(str(ot_start_hour), '%H:%M:%S')).time()
                        sample_time = (datetime.datetime.strptime(str(sample), '%H:%M:%S'))
                        work_out_hour = datetime.datetime.strptime(out_hour, '%H:%M:%S').time()
                        work_in_hour = datetime.datetime.strptime(in_hour, '%H:%M:%S')
                        d22 = str(out_date).split(".")[0]
                        dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d')
                        out_day_name = dt22.weekday()
                        last_out_date = dt22.strftime("%d/%m/%Y")
                        d11 = str(in_date).split(".")[0]
                        dt11 = datetime.datetime.strptime(d11, '%Y-%m-%d')
                        in_day_name = dt11.weekday()
                        last_in_date = dt11.strftime("%d/%m/%Y")
                        ot_amount_mrg = 0
                        ot_amount_eve = 0
                        holiday_amount = 0
                        for ot_config in department_config.department_ot_detail_ids:
                            config_start = (datetime.datetime.strptime(ot_config.start_time, '%H:%M:%S')).time()
                            config_end = (datetime.datetime.strptime(ot_config.end_time, '%H:%M:%S')).time()
                            config_work_start = (
                                datetime.datetime.strptime(department_config.work_start_time, '%H:%M:%S'))
                            config_work_delay_start = (
                                datetime.datetime.strptime(department_config.approximate_time_delay_mrng, '%H:%M:%S'))
                            mrng_ot_availble = config_work_start - config_work_delay_start
                            work_out_hour_final = str(work_out_hour).split(':')
                            ot_hour = str(config_work_start - timedelta(hours=int(work_out_hour_final[0]),
                                                                        minutes=int(work_out_hour_final[1]))).split(
                                ' ')[1].split(', ')[-1]
                            mrng_ot_availble_final = datetime.datetime.strptime(str(mrng_ot_availble),
                                                                                '%H:%M:%S').time()
                            if out_day_name == 6:
                                holiday_hour = datetime_in - datetime_out
                                if holiday_hour < ot_datetime_check_one:
                                    holiday_amount = department_config.holiday_ot_amount_one
                                elif ot_datetime_check_one < holiday_hour and ot_datetime_check_two > holiday_hour:
                                    holiday_amount = department_config.holiday_ot_amount_two
                                elif ot_datetime_check_two + timedelta(hours=3,
                                                                       minutes=00) > holiday_hour and holiday_hour > ot_datetime_check_two:
                                    holiday_amount = department_config.holiday_ot_amount_three
                            else:
                                if work_out_hour:
                                    if work_out_hour <= mrng_ot_availble_final:
                                        conf_start = ot_config.start_time
                                        my_datetime_start = \
                                            str(datetime.datetime.strptime(conf_start, "%H:%M:%S")).split(' ')[1]
                                        conf_end = ot_config.end_time
                                        my_datetime_end = \
                                            str(datetime.datetime.strptime(conf_end, "%H:%M:%S")).split(' ')[1]
                                        if (out_hour > my_datetime_start) and (out_hour < my_datetime_end):
                                            ot_amount_mrg = ot_config.ot_amount

                        for ot_config_two in department_config.department_ot_detail_two_ids:
                            config_work_end = (datetime.datetime.strptime(department_config.work_end_time, '%H:%M:%S'))
                            config_work_delay_end = department_config.approximate_time_delay_eve.split(':')
                            hour = int(config_work_delay_end[0])
                            min = int(config_work_delay_end[1])
                            second = config_work_delay_end[2]
                            sample_time_eve = (config_work_end + timedelta(hours=hour, minutes=min))
                            work_in_hour_final = (str(work_in_hour).split(' ')[1]).split(':')
                            ot_hour_eve = str(work_in_hour - config_work_end).split(', ')[-1]
                            eve_ot_availble = datetime.datetime.strptime(str(sample_time_eve).split(' ')[1], '%H:%M:%S')
                            if in_day_name == 6:
                                holiday_hour = datetime_in - datetime_out
                                if holiday_hour < ot_datetime_check_one:
                                    holiday_amount = department_config.holiday_ot_amount_one
                                elif ot_datetime_check_one < holiday_hour and ot_datetime_check_two > holiday_hour:
                                    holiday_amount = department_config.holiday_ot_amount_two
                                elif ot_datetime_check_two + timedelta(hours=3,
                                                                       minutes=00) > holiday_hour and holiday_hour > ot_datetime_check_two:
                                    holiday_amount = department_config.holiday_ot_amount_three
                            else:
                                if work_in_hour:
                                    if work_in_hour > eve_ot_availble:
                                        conf_start_two = ot_config_two.start_time
                                        my_datetime_start_two = \
                                            str(datetime.datetime.strptime(conf_start_two, "%H:%M:%S")).split(' ')[1]
                                        conf_end_two = ot_config_two.end_time
                                        my_datetime_end_two = \
                                            str(datetime.datetime.strptime(conf_end_two, "%H:%M:%S")).split(' ')[1]
                                        if (in_hour > my_datetime_start_two) and (in_hour < my_datetime_end_two):
                                            ot_amount_eve = ot_config_two.ot_amount

                        ot_amount_fulll = ot_amount_mrg + ot_amount_eve + holiday_amount
                    if out_date == in_date:
                        worksheet1.write(row_pq, 1, str(out_date), design_8)
                    else:
                        worksheet1.write(row_pq, 1, str(out_date) + ' to ' + str(in_date), design_8)
                    # if record.driver_history_id.driver_name.driver_ref:
                    #     worksheet1.write(row_pq, 2, record.driver_history_id.driver_name.driver_ref, design_8)
                    # else:
                    #     worksheet1.write(row_pq, 2, ' - ', design_7)
                    if record.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 3, record.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, ' - ', design_7)
                    if record.driver_history_id.driver_name.department_id.name:
                        worksheet1.write(row_pq, 4, record.driver_history_id.driver_name.department_id.name, design_8)
                    else:
                        worksheet1.write(row_pq, 4, ' - ', design_7)
                    if record.driver_history_id.driver_name.job_id.name:
                        worksheet1.write(row_pq, 5, record.driver_history_id.driver_name.job_id.name, design_8)
                    else:
                        worksheet1.write(row_pq, 5, ' - ', design_7)
                    if record.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 6, record.driver_history_id.vehicle_name.name, design_8)
                    elif record.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 6, record.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if record.reference:
                        worksheet1.write(row_pq, 7, record.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if self.ho_department.name:
                        worksheet1.write(row_pq, 8, self.ho_department.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if out_hour:
                        worksheet1.write(row_pq, 9, out_hour, design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if in_hour:
                        worksheet1.write(row_pq, 10, in_hour, design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if ot_amount_mrg:
                        worksheet1.write(row_pq, 11, str(ot_hour), design_9)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if ot_amount_mrg:
                        worksheet1.write(row_pq, 12, ot_amount_mrg, design_9)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    if ot_amount_eve:
                        worksheet1.write(row_pq, 13, str(ot_hour_eve), design_9)
                    else:
                        worksheet1.write(row_pq, 13, '-', design_7)
                    if ot_amount_eve:
                        worksheet1.write(row_pq, 14, ot_amount_eve, design_9)
                    else:
                        worksheet1.write(row_pq, 14, '-', design_7)
                    if holiday_amount:
                        worksheet1.write(row_pq, 15, holiday_amount, design_9)
                    else:
                        worksheet1.write(row_pq, 15, '-', design_7)
                    if ot_amount_fulll:
                        worksheet1.write(row_pq, 16, ot_amount_fulll, design_9)
                    else:
                        worksheet1.write(row_pq, 16, '-', design_7)
                    sl_no += 1
                    row_pq += 1

            else:
                raise ValidationError('No Record')

        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': 'Driver OT Report - [ %s ].xls' % self.date,
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'driver.ot.report.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }
