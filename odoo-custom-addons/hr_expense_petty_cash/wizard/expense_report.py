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
from odoo.exceptions import Warning, ValidationError, UserError
import pdb

cell = easyxf('pattern: pattern solid, fore_colour yellow')
ADDONS_PATH = tools.config['addons_path'].split(",")[-1]

MONTH_LIST = [('1', 'Jan'), ('2', 'Feb'), ('3', 'Mar'),
              ('4', 'Apr'), ('5', 'May'), ('6', 'Jun'),
              ('7', 'Jul'), ('8', 'Aug'), ('9', 'Sep'),
              ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')]


class ExpensesReport(models.TransientModel):
    _name = 'expense.report.wizard'
    _description = 'Expenses  Wizard Report'

    start_date = fields.Date('Start date')
    end_date = fields.Date('End date')
    attachment = fields.Binary('File')
    attach_name = fields.Char('Attachment Name')
    summary_file = fields.Binary('Expenses Summary Report')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Expenses Report')
    current_time = fields.Date('Current Time', default=lambda self: fields.Datetime.now())
    ams_time = datetime.now() + timedelta(hours=5, minutes=30)
    date = ams_time.strftime('%d-%m-%Y %H:%M:%S')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    expense_id = fields.Many2one('hr.expense', string='Expense')
    week_boolean = fields.Boolean('Previous Week')
    all_records = fields.Boolean(' All Records')
    approved_records = fields.Boolean('Approved Records')
    week_days = fields.Char('Previous Week ')
    current_week_days = fields.Char(string=' Current Week ')

    @api.onchange('week_boolean', 'start_date', 'approved_records')
    def week_days_find(self):
        import datetime
        now = datetime.datetime.now()
        now_time = datetime.datetime.today()
        now_day_1 = now - datetime.timedelta(days=now.weekday(), weeks=+1)
        now_day_2 = now_day_1 + datetime.timedelta(days=6)
        week_now = now_day_1.isocalendar()
        current_week = now.isocalendar()
        if self.start_date:
            self.current_week_days = str(current_week).split(',')[1] + "WeeK"
        if self.approved_records:
            self.current_week_days = str(current_week).split(',')[1] + "WeeK"
        if self.week_boolean:
            self.start_date = now_day_1
            self.end_date = now_day_2
            self.week_days = str(week_now).split(',')[1] + "WeeK"
            self.current_week_days = str(current_week).split(',')[1] + "WeeK"

    def action_get_hr_payroll_excel_report(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('EXPENSE SUMMARY REPORT')
        design_6 = easyxf('align: horiz left;font: bold 1;')
        design_7 = easyxf('align: horiz center;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_13 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_14 = easyxf('align: horiz left;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_15 = easyxf('align: horiz right;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_16 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_17 = easyxf("pattern: pattern solid, fore_color black; font: color white; align: horiz center")
        worksheet1.col(0).width = 2000
        worksheet1.col(1).width = 3500
        worksheet1.col(2).width = 7000
        worksheet1.col(3).width = 15000
        worksheet1.col(4).width = 3000
        worksheet1.col(5).width = 3500
        worksheet1.col(6).width = 4500
        worksheet1.col(7).width = 4000
        worksheet1.col(8).width = 3000
        worksheet1.col(9).width = 3000
        worksheet1.col(10).width = 3000
        worksheet1.col(11).width = 3000
        worksheet1.col(12).width = 3500
        worksheet1.col(13).width = 3000
        worksheet1.col(14).width = 3000
        worksheet1.col(15).width = 3000
        worksheet1.col(16).width = 3000
        worksheet1.col(17).width = 3000
        worksheet1.col(18).width = 3000
        worksheet1.col(19).width = 3000

        rows = 0
        cols = 0
        row_pq = 5
        col_pq = 5

        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)

        import datetime
        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ]
        domain1 = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('state', '=', 'approved')]

        col_1 = 0
        worksheet1.write_merge(rows, rows, 2, 3, 'EXPENSES SUMMARY  REPORT', design_16)
        rows += 1
        worksheet1.write(rows, 2, 'START DATE', design_14)
        worksheet1.write(rows, 3, self.start_date.strftime('%d-%m-%Y'), design_13)
        rows += 1
        worksheet1.write(rows, 2, 'END DATE', design_14)
        worksheet1.write(rows, 3, self.end_date.strftime('%d-%m-%Y'), design_13)
        if self.week_boolean and self.approved_records:
            row_pq = 5 + 1
            rows += 1
            worksheet1.write(rows, 2, 'WEEK', design_14)
            worksheet1.write(rows, 3, self.week_days, design_13)
        elif self.week_boolean:
            row_pq = 5 + 1
            rows += 1
            worksheet1.write(rows, 2, 'WEEK', design_14)
            worksheet1.write(rows, 3, self.week_days, design_13)
        rows += 1
        worksheet1.write(rows, 2, 'REPORT GENERATED BY', design_14)
        worksheet1.write(rows, 3, self.user_id.name, design_13)
        rows += 2
        worksheet1.write(rows, col_1, _('S.NO'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Expense DATE'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Expense Category'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _(' Expense Description'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Total'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Status'), design_13)
        col_1 += 1
        sl_no = 1
        row_pq = row_pq + 1
        mr_num = []
        res = []
        total = 0
        if self.start_date and self.end_date and self.approved_records:
            stock_valuation = self.env['hr.expense'].sudo().search(domain1, order=' product_id asc')
            for record in stock_valuation:
                total += record.total_amount
                worksheet1.write(row_pq, 0, sl_no, design_7)
                if record.create_date:
                    worksheet1.write(row_pq, 1, record.date.strftime('%d-%m-%Y'), design_8)
                else:
                    worksheet1.write(row_pq, 1, '-', design_7)

                if record.product_id.name:
                    worksheet1.write(row_pq, 2, record.product_id.name, design_8)
                else:
                    worksheet1.write(row_pq, 2, '-', design_7)

                if record.name:
                    worksheet1.write(row_pq, 3, record.name, design_8)
                else:
                    worksheet1.write(row_pq, 3, '-', design_7)

                if record.total_amount:
                    worksheet1.write(row_pq, 4,
                                     record.company_id.currency_id.symbol + str(record.total_amount)
                                     , design_9)
                else:
                    worksheet1.write(row_pq, 4, '-', design_7)
                if record:
                    state = ''
                    if record.state == 'draft':
                        state = 'To Submit'
                    elif record.state == 'reported':
                        state = 'Submitted'
                    elif record.state == 'approved':
                        state = 'Approved'
                    elif record.state == 'post':
                        state = 'Posted'
                    elif record.state == 'done':
                        state = 'Paid'
                    elif record.state == 'refused':
                        state = 'Refused'
                    pdc_status = state

                    worksheet1.write(row_pq, 5, pdc_status, design_8)
                else:
                    worksheet1.write(row_pq, 5, '-', design_7)

                sl_no += 1
                row_pq += 1
            worksheet1.write(row_pq, 3, 'Total Value', design_7)
            worksheet1.write(row_pq, 4, self.company_id.currency_id.symbol + str(total), design_9)
        else:
            stock_valuation = self.env['hr.expense'].sudo().search(domain, order=' product_id asc')
            for record in stock_valuation:
                total += record.total_amount
                worksheet1.write(row_pq, 0, sl_no, design_7)
                if record.create_date:
                    worksheet1.write(row_pq, 1, record.date.strftime('%d-%m-%Y'), design_8)
                else:
                    worksheet1.write(row_pq, 1, '-', design_7)
                if record.product_id.name:
                    worksheet1.write(row_pq, 2, record.product_id.name, design_8)
                else:
                    worksheet1.write(row_pq, 2, '-', design_7)
                if record.name:
                    worksheet1.write(row_pq, 3, record.name, design_8)
                else:
                    worksheet1.write(row_pq, 3, '-', design_7)
                if record.total_amount:
                    worksheet1.write(row_pq, 4,
                                     record.company_id.currency_id.symbol + str(record.total_amount),
                                     design_9)
                else:
                    worksheet1.write(row_pq, 4, '-', design_7)
                if record:
                    state = ''
                    if record.state == 'draft':
                        state = 'To Submit'
                    elif record.state == 'reported':
                        state = 'Submitted'
                    elif record.state == 'approved':
                        state = 'Approved'
                    elif record.state == 'post':
                        state = 'Posted'
                    elif record.state == 'done':
                        state = 'Paid'
                    elif record.state == 'refused':
                        state = 'Refused'
                    pdc_status = state

                    worksheet1.write(row_pq, 5, pdc_status, design_8)
                else:
                    worksheet1.write(row_pq, 5, '-', design_7)
                sl_no += 1
                row_pq += 1
            worksheet1.write(row_pq, 3, 'Total Value', design_7)
            worksheet1.write(row_pq, 4, self.company_id.currency_id.symbol + str(total), design_9)
        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': 'Expenses Summary Report -[ %s ] [ %s ].xls' % (
            self.start_date.strftime('%d-%m-%Y'), self.end_date.strftime('%d-%m-%Y')),
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'expense.report.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }
