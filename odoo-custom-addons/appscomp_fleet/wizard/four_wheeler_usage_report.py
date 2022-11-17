from odoo import models, fields, api, _
import xlwt
from io import BytesIO
import base64
import itertools
from operator import itemgetter
from odoo.exceptions import Warning
from odoo import tools
from xlwt import easyxf
import datetime
from odoo.exceptions import UserError
from datetime import datetime
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
    _name = 'four.wheeler.usage.report.wizard'
    _description = 'Fleet Vehicle Usage Report Wizard'

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
    vechicle_list = fields.Many2many('fleet.vehicle', string="Vehicle")
    driver_name = fields.Many2many('hr.employee', string='Driver Name')
    requested = fields.Boolean('Request ?')

    vehicle_category = fields.Selection([
        ('car', 'Car'),
        ('bike', 'Bike'),
        ('truck', 'Truck'),
    ], string='Vechicle Category')

    type_of_vehicle = fields.Selection([
        ('company', 'Company Owned'),
        ('employee', 'Employee Owned'),
        ('rental', 'Rental'),
    ], string='Vechicle Type')

    def get_four_wheeler_usage_report_pdf(self):
        if self.vechicle_list and self.driver_name:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
                ('driver_history_id.vehicle_name', '=', self.vechicle_list.ids),
                ('driver_history_id.driver_name', '=', self.driver_name.ids),
            ]
        elif self.vechicle_list:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
                ('driver_history_id.vehicle_name', '=', self.vechicle_list.ids),
            ]
        elif self.driver_name:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
                ('driver_history_id.driver_name', '=', self.driver_name.ids),
            ]
        elif self.type_of_vehicle:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
                ('driver_history_id.type_of_vehicle', '=', self.type_of_vehicle),
            ]
        elif self.vehicle_category:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
                ('driver_history_id.vehicle_category', '=', self.vehicle_category),
            ]
        elif self.driver_name and self.vehicle_category:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
                ('driver_history_id.driver_name', '=', self.driver_name.ids),
                ('driver_history_id.vehicle_category', '=', self.vehicle_category),
            ]
        elif self.driver_name and self.type_of_vehicle:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
                ('driver_history_id.driver_name', '=', self.driver_name.ids),
                ('driver_history_id.type_of_vehicle', '=', self.type_of_vehicle),
            ]
        elif self.vehicle_category and self.type_of_vehicle:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
                ('driver_history_id.type_of_vehicle', '=', self.type_of_vehicle),
                ('driver_history_id.vehicle_category', '=', self.vehicle_category),
            ]
        else:
            domain = [
                ('out_time', '>=', self.start_date),
                ('in_time', '<=', self.end_date),
            ]
            pass
        b_list = []
        values = self.env['driver.check.in.out.details'].search_read(domain)
        values_id = self.env['driver.check.in.out.details'].search(domain)
        for vals in values_id:
            b_list.append({
                'vehicle_no': vals.driver_history_id.vehicle_name.license_plate or False,
                'vehicle_name': vals.driver_history_id.vehicle_name.name or False,
                'driver_name': vals.driver_history_id.driver_name.name or False,
                'opening_km': vals.opening_km or False,
                'out_time': vals.out_time or False,
                'in_time': vals.in_time or False,
                'closing_km': vals.closing_km or False,
                'out_verified_by': vals.out_verified_by or False,
                'in_verified_by': vals.in_verified_by or False,
                'duration': vals.duration or False,
                'total_kilometer': vals.total_kilometer or False,
                'reference': vals.reference or False,
                # 'person-list': vals.source or False,
            })
        data = {
            'form': self.read()[0],
            'values': values,
            'values_2': b_list,
        }
        return self.env.ref('appscomp_fleet.action_fleet_usage_report_qweb').report_action(self, data=data)

    def action_get_four_wheeler_usage_report(self):
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
        design_14 = easyxf('align: horiz left;font: bold 1;pattern: pattern solid, fore_colour gray25;')

        worksheet1.col(0).width = 1800
        worksheet1.col(1).width = 4300
        worksheet1.col(2).width = 6000
        worksheet1.col(3).width = 4000
        worksheet1.col(4).width = 5000
        worksheet1.col(5).width = 4800
        worksheet1.col(6).width = 4800
        worksheet1.col(7).width = 4300
        worksheet1.col(8).width = 4800
        worksheet1.col(9).width = 3500
        worksheet1.col(10).width = 3500
        worksheet1.col(11).width = 3500
        worksheet1.col(12).width = 3500
        worksheet1.col(13).width = 5000
        worksheet1.col(14).width = 5000
        worksheet1.col(15).width = 5000

        rows = 0
        cols = 0
        row_pq = 5

        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.set_remove_splits(True)

        col_1 = 0
        worksheet1.write_merge(rows, rows, 2, 6, 'AEE (WD)- FLEET VEHICLE WHEELER USAGE REPORT', design_13)
        rows += 1
        worksheet1.write(rows, 3, 'START DATE', design_14)
        worksheet1.write(rows, 4, self.start_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, 3, 'END DATE', design_14)
        worksheet1.write(rows, 4, self.end_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        if self.type_of_vehicle:
            worksheet1.write(rows, 3, 'TYPE OF VEHICLE', design_14)
            worksheet1.write(rows, 4, self.type_of_vehicle, design_7)
            rows += 1
        # worksheet1.write(rows, 3, 'VEHICLE CATEGORY', design_13)
        # worksheet1.write(rows, 4, self.vehicle_category, design_7)
        # rows += 1
        worksheet1.write(rows, 3, 'GENARATED BY', design_14)
        worksheet1.write(rows, 4, self.user_id.name, design_7)
        if self.vehicle_category:
            worksheet1.write(rows, 6, 'VEHICLE CATEGORY', design_14)
            worksheet1.write(rows, 7, self.vehicle_category, design_7)
        rows += 1
        worksheet1.write(rows, col_1, _('Sl.No'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('VEHICLE NO '), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('VEHICLE NAME'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('OPENING KM '), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('TIME OUT'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('TIME IN'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('CLOSING KM'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('OUT SECURITY BY'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('IN SECURITY BY'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('DURATION'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('TOTAL KM'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('DRIVER NAME'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('REFERENCE'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('TRAVELLED BY'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('PLACE & PURPOSE'), design_13)
        col_1 += 1

        sl_no = 1
        row_pq = row_pq + 1
        mr_num = []
        res = []
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
                ('driver_history_id.vehicle_name', '=', record.vechicle_list.ids),
                ('driver_history_id.driver_name', '=', record.driver_name.ids),
            ]
            domain1 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.vehicle_name', '=', record.vechicle_list.ids),
            ]
            domain2 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.driver_name', '=', record.driver_name.ids),
            ]
            domain3 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
            ]
            domain4 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.driver_name', '=', record.driver_name.ids),
                ('driver_history_id.vehicle_name', '=', record.vechicle_list.ids),
            ]
            domain5 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.type_of_vehicle', '=', record.type_of_vehicle),
            ]
            domain6 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.vehicle_category', '=', record.vehicle_category),
            ]
            domain7 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.driver_name', '=', record.driver_name.ids),
                ('driver_history_id.type_of_vehicle', '=', record.type_of_vehicle),
            ]
            domain8 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.driver_name', '=', record.driver_name.ids),
                ('driver_history_id.vehicle_category', '=', record.vehicle_category),
            ]
            domain9 = [
                ('out_time', '>=', record.start_date),
                ('in_time', '<=', record.end_date),
                ('driver_history_id.type_of_vehicle', '=', record.type_of_vehicle),
                ('driver_history_id.vehicle_category', '=', record.vehicle_category),
            ]
            if record.vechicle_list and record.driver_name:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    if invoice.driver_history_id.persons_list:
                        pass_name = ""
                        pass_list = []
                        for pass_id in invoice.driver_history_id.persons_list:
                            if len(pass_list) != 0:
                                pass_name = pass_name + ',' + pass_id.name
                                pass_list.append('pass_name')
                            else:
                                pass_name += pass_id.name
                                pass_list.append('pass_name')

                        # if not self.branch_ids:
                        #         branchs = self.env['res.branch'].search([])
                        #         branch_name = ""
                        #         branch_list = []
                        #         for branch in branchs:
                        #             if len(branch_list) != 0:
                        #                 branch_name = branch_name + ', ' + branch.name
                        #                 branch_list.append('branch_name')
                        #             else:
                        #                 branch_name += branch.name
                        #                 branch_list.append('branch_name')

                        worksheet1.write(row_pq, 13, pass_name, design_8)
                    else:
                        worksheet1.write(row_pq, 13, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            elif record.vechicle_list:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain1, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            elif record.driver_name:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain2, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            elif record.driver_name and record.vechicle_list:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain4, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            elif record.type_of_vehicle:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain5, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            elif record.vehicle_category:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain6, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            elif record.driver_name and record.vehicle_category:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain7, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            elif record.driver_name and record.type_of_vehicle:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain8, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            elif record.vehicle_category and record.type_of_vehicle:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain9, order='out_time asc')
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
            else:
                driver_beta = record.env['driver.check.in.out.details'].sudo().search(domain3)
                for invoice in driver_beta:
                    out_time = invoice.out_time
                    in_time = invoice.in_time
                    import datetime
                    d1 = str(out_time).split(".")[0]
                    dt2 = datetime.datetime.strptime(d1, '%Y-%m-%d %H:%M:%S')
                    out_time_start = dt2.strftime("%d/%m/%Y %H:%M:%S")
                    d22 = str(in_time).split(".")[0]
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y %H:%M:%S")
                    worksheet1.write(row_pq, 0, sl_no, design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 1, invoice.driver_history_id.vehicle_name.license_plate, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_7)
                    if invoice.driver_history_id.vehicle_name:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.vehicle_name.name, design_8)
                    elif invoice.driver_history_id.emp_vehicle:
                        worksheet1.write(row_pq, 2, invoice.driver_history_id.emp_vehicle, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_7)
                    if invoice.opening_km:
                        worksheet1.write(row_pq, 3, str(invoice.opening_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_7)
                    if out_time_start:
                        worksheet1.write(row_pq, 4, out_time_start, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_7)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_7)
                    if invoice.closing_km:
                        worksheet1.write(row_pq, 6, str(invoice.closing_km) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 6, '-', design_7)
                    if invoice.out_verified_by:
                        worksheet1.write(row_pq, 7, invoice.out_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 7, '-', design_7)
                    if invoice.in_verified_by:
                        worksheet1.write(row_pq, 8, invoice.in_verified_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_7)
                    if invoice.duration:
                        worksheet1.write(row_pq, 9, str(invoice.duration) + ' H/M', design_9)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_7)
                    if invoice.total_kilometer:
                        worksheet1.write(row_pq, 10, str(invoice.total_kilometer) + ' /KM', design_9)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_7)
                    if invoice.driver_history_id.driver_name.name:
                        worksheet1.write(row_pq, 11, invoice.driver_history_id.driver_name.name, design_8)
                    else:
                        worksheet1.write(row_pq, 11, '-', design_7)
                    if invoice.reference:
                        worksheet1.write(row_pq, 12, invoice.reference, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_7)
                    sl_no += 1
                    row_pq += 1
        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': 'Fleet Vehicle Usage Report - [ %s ].xls' % self.date,
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'four.wheeler.usage.report.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }
