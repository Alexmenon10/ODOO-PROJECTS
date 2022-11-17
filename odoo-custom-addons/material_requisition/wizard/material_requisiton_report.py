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

class MaterialRequisitionReport(models.TransientModel):
    _name = 'material.requisition.excel.report.wizard'
    _description = 'Material Requisition Report'

    start_date = fields.Date('Start date', required=True)
    end_date = fields.Date('End date', required=True)
    attachment = fields.Binary('File')
    attach_name = fields.Char('Attachment Name')
    summary_file = fields.Binary('Purchase Backorder Report')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Purchase Backorder Report')
    current_time = fields.Date('Current Time', default=lambda self: fields.Datetime.now())
    ams_time = datetime.now() + timedelta(hours=5, minutes=30)
    date = ams_time.strftime('%d-%m-%Y %H:%M:%S')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    material_request_raised_for = fields.Many2many('hr.employee', string='Request Raised For')
    material_request_raised_by = fields.Many2one('hr.employee', string='Request Raised By')
    requested = fields.Boolean('Request..?')


    def action_get_material_requisiton_report_excel(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('Material Requisition Report')

        design_6 = easyxf('align: horiz left;font: bold 1;')
        design_7 = easyxf('align: horiz center;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_13 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')

        worksheet1.col(0).width = 1500
        worksheet1.col(1).width = 5500
        worksheet1.col(2).width = 6500
        worksheet1.col(3).width = 6500
        worksheet1.col(4).width = 5800
        worksheet1.col(5).width = 3400
        worksheet1.col(6).width = 3800
        worksheet1.col(7).width = 3800
        worksheet1.col(8).width = 3500
        worksheet1.col(9).width = 3500
        worksheet1.col(10).width = 3500
        worksheet1.col(11).width = 3300
        worksheet1.col(12).width = 4500
        worksheet1.col(13).width = 4500
        worksheet1.col(14).width = 4500
        worksheet1.col(15).width = 4000

        rows = 0
        cols = 0
        row_pq = 5

        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.set_remove_splits(True)

        col_1 = 0
        worksheet1.write_merge(rows, rows, 2, 6, 'MATERIAL REQUISITION REPORT', design_13)
        rows += 1
        worksheet1.write(rows, 3, 'FROM', design_7)
        worksheet1.write(rows, 4, self.start_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, 3, 'TO', design_7)
        worksheet1.write(rows, 4, self.end_date.strftime('%d-%m-%Y'), design_7)
        rows += 2
        worksheet1.write(rows, 3, 'MATERIAL REQUESTED BY', design_7)
        worksheet1.write(rows, 4, self.material_request_raised_by.name, design_7)
        rows += 1
        # worksheet1.write(rows, 3, 'DEPARTMENT', design_7)
        # worksheet1.write(rows, 4, self.material_request_raised_by.department_id.name, design_7)
        # rows += 2
        worksheet1.write(rows, col_1, _('Sl.No'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Requsted Material No'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Requsted Material For'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Department'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Requsted Material  Name'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Requsted Date'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Requested  QTY'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Approved QTY'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Approved Date'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Inward Date'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Issued Date'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Issued QTY'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('MR Approved By'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('PO Approved By'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Stores Incharge'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Status'), design_13)
        col_1 += 1

        sl_no = 1
        row_pq = row_pq + 1
        mr_num = []
        res = []
        for record in self:
            domain09 = [
                ('indent_date', '>=', record.start_date),
                ('required_date', '<=', record.end_date),
                ('responsible', '=', record.material_request_raised_by.name),
                ('request_raised_for', '=', record.material_request_raised_for.ids),
                ('state', 'not in', ('draft', 'cancel', 'reject'))]
            domain10 = [
                ('indent_date', '>=', record.start_date),
                ('required_date', '<=', record.end_date),
                ('state', 'not in', ('draft', 'cancel', 'reject'))]
            domain11 = [
                ('indent_date', '>=', record.start_date),
                ('required_date', '<=', record.end_date),
                ('responsible', '=', record.material_request_raised_by.name),
                ('state', 'not in', ('draft', 'cancel', 'reject'))]
            domain12 = [
                ('indent_date', '>=', record.start_date),
                ('required_date', '<=', record.end_date),
                ('request_raised_for', '=', record.material_request_raised_for.ids),
                ('state', 'not in', ('draft', 'cancel', 'reject'))]
            # domain = [
            #     ('indent_id.indent_date', '>=', record.start_date),
            #     ('indent_id.required_date', '<=', record.end_date),
            #     ('indent_id.responsible', '=', record.material_request_raised_by.name),
            #     ('indent_id.request_raised_for', '=', record.material_request_raised_for.ids),
            #     ('indent_id.state', 'not in', ('draft', 'cancel', 'reject'))]
            # domain1 = [
            #     ('indent_id.indent_date', '>=', record.start_date),
            #     ('indent_id.required_date', '<=', record.end_date),
            #     ('indent_id.responsible', '=', record.material_request_raised_by.name),
            #     ('indent_id.state', 'not in', ('draft', 'cancel', 'reject'))]
            domain2 = [
                ('scheduled_date', '>=', record.end_date),
                ('state', 'not in', ('draft', 'waiting', 'confirmed', 'assigned', 'cancel'))]
            picking = record.env['stock.picking'].sudo().search(domain2)
            if record.start_date and record.end_date and record.material_request_raised_for and record.material_request_raised_by:
                material = record.env['material.requisition.indent'].sudo().search(domain09)
                for invoice in material:
                    ref_date1 = invoice.indent_date
                    updated_date = invoice.required_date
                    verified_date = invoice.verified_date
                    issued_date = invoice.issued_date
                    import datetime
                    if ref_date1:
                        d11 = str(ref_date1)
                        dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d %H:%M:%S')
                        date1 = dt21.strftime("%d/%m/%Y")
                    if updated_date:
                        d22 = str(updated_date)
                        dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                        invoice_updated_date = dt22.strftime("%d/%m/%Y")
                    if verified_date:
                        d33 = str(verified_date)
                        dt23 = datetime.datetime.strptime(d33, '%Y-%m-%d %H:%M:%S')
                        verified_date = dt23.strftime("%d/%m/%Y")
                    worksheet1.write(row_pq, 0, sl_no, design_8)
                    if invoice.name:
                        worksheet1.write(row_pq, 1, invoice.name, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_8)
                    if invoice.request_raised_for.name:
                        worksheet1.write(row_pq, 2, invoice.request_raised_for.name, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_8)
                    if invoice.request_raised_for.department_id.name:
                        worksheet1.write(row_pq, 3, invoice.request_raised_for.department_id.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_8)
                    if ref_date1:
                        worksheet1.write(row_pq, 5, date1, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_8)
                    if invoice.verified_date:
                        worksheet1.write(row_pq, 8, verified_date, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_8)
                    if invoice.inward_date:
                        worksheet1.write(row_pq, 9, invoice.inward_date, design_8)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_8)
                    if invoice.issued_date:
                        worksheet1.write(row_pq, 10, invoice.issued_date, design_8)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_8)
                    if invoice.approved_by:
                        worksheet1.write(row_pq, 12, invoice.approved_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_8)
                    if invoice.po_approved_by:
                        worksheet1.write(row_pq, 13, invoice.po_approved_by, design_8)
                    else:
                        worksheet1.write(row_pq, 13, '-', design_8)
                    if invoice.store_incharge:
                        worksheet1.write(row_pq, 14, invoice.store_incharge, design_8)
                    else:
                        worksheet1.write(row_pq, 14, '-', design_8)
                    worksheet1.write(row_pq, 15, invoice.state, design_9)
                    row_pq_new = row_pq
                    for material in invoice.request_product_lines:
                        worksheet1.write(row_pq_new, 4, material.product_id.name, design_8)
                        worksheet1.write(row_pq_new, 6, material.product_uom_qty, design_9)
                        row_pq_new += 1
                    row_pq_new = row_pq
                    for material_approved in invoice.product_lines:
                        worksheet1.write(row_pq_new, 11, '%.2f' % material_approved.qty_shipped, design_8)
                        worksheet1.write(row_pq_new, 7, material_approved.product_uom_qty, design_9)
                        row_pq_new += 1
                    sl_no += 1
                    row_pq = row_pq_new
            elif record.start_date and record.end_date and record.material_request_raised_for:
                material = record.env['material.requisition.indent'].sudo().search(domain12)
                for invoice in material:
                    ref_date1 = invoice.indent_date
                    updated_date = invoice.required_date
                    verified_date = invoice.verified_date
                    issued_date = invoice.issued_date
                    import datetime
                    if ref_date1:
                        d11 = str(ref_date1)
                        dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d %H:%M:%S')
                        date1 = dt21.strftime("%d/%m/%Y")
                    if updated_date:
                        d22 = str(updated_date)
                        dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                        invoice_updated_date = dt22.strftime("%d/%m/%Y")
                    if verified_date:
                        d33 = str(verified_date)
                        dt23 = datetime.datetime.strptime(d33, '%Y-%m-%d %H:%M:%S')
                        verified_date = dt23.strftime("%d/%m/%Y")
                    worksheet1.write(row_pq, 0, sl_no, design_8)
                    if invoice.name:
                        worksheet1.write(row_pq, 1, invoice.name, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_8)
                    if invoice.request_raised_for.name:
                        worksheet1.write(row_pq, 2, invoice.request_raised_for.name, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_8)
                    if invoice.request_raised_for.department_id.name:
                        worksheet1.write(row_pq, 3, invoice.request_raised_for.department_id.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_8)
                    if ref_date1:
                        worksheet1.write(row_pq, 5, date1, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_8)
                    if invoice.verified_date:
                        worksheet1.write(row_pq, 8, verified_date, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_8)
                    if invoice.inward_date:
                        worksheet1.write(row_pq, 9, invoice.inward_date, design_8)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_8)
                    if invoice.issued_date:
                        worksheet1.write(row_pq, 10, invoice.issued_date, design_8)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_8)
                    if invoice.approved_by:
                        worksheet1.write(row_pq, 12, invoice.approved_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_8)
                    if invoice.po_approved_by:
                        worksheet1.write(row_pq, 13, invoice.po_approved_by, design_8)
                    else:
                        worksheet1.write(row_pq, 13, '-', design_8)
                    if invoice.store_incharge:
                        worksheet1.write(row_pq, 14, invoice.store_incharge, design_8)
                    else:
                        worksheet1.write(row_pq, 14, '-', design_8)
                    worksheet1.write(row_pq, 15, invoice.state, design_9)
                    row_pq_new = row_pq
                    for material in invoice.request_product_lines:
                        worksheet1.write(row_pq_new, 4, material.product_id.name, design_8)
                        worksheet1.write(row_pq_new, 6, material.product_uom_qty, design_9)
                        row_pq_new += 1
                    row_pq_new = row_pq
                    for material_approved in invoice.product_lines:
                        worksheet1.write(row_pq_new, 11, '%.2f' % material_approved.qty_shipped, design_8)
                        worksheet1.write(row_pq_new, 7, material_approved.product_uom_qty, design_9)
                        row_pq_new += 1
                    sl_no += 1
                    row_pq = row_pq_new
            elif record.start_date and record.end_date and record.material_request_raised_by:
                material = record.env['material.requisition.indent'].sudo().search(domain11)
                for invoice in material:
                    ref_date1 = invoice.indent_date
                    updated_date = invoice.required_date
                    verified_date = invoice.verified_date
                    issued_date = invoice.issued_date
                    import datetime
                    if ref_date1:
                        d11 = str(ref_date1)
                        dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d %H:%M:%S')
                        date1 = dt21.strftime("%d/%m/%Y")
                    if updated_date:
                        d22 = str(updated_date)
                        dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                        invoice_updated_date = dt22.strftime("%d/%m/%Y")
                    if verified_date:
                        d33 = str(verified_date)
                        dt23 = datetime.datetime.strptime(d33, '%Y-%m-%d %H:%M:%S')
                        verified_date = dt23.strftime("%d/%m/%Y")
                    worksheet1.write(row_pq, 0, sl_no, design_8)
                    if invoice.name:
                        worksheet1.write(row_pq, 1, invoice.name, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_8)
                    if invoice.request_raised_for.name:
                        worksheet1.write(row_pq, 2, invoice.request_raised_for.name, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_8)
                    if invoice.request_raised_for.department_id.name:
                        worksheet1.write(row_pq, 3, invoice.request_raised_for.department_id.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_8)
                    if ref_date1:
                        worksheet1.write(row_pq, 5, date1, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_8)
                    if invoice.verified_date:
                        worksheet1.write(row_pq, 8, verified_date, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_8)
                    if invoice.inward_date:
                        worksheet1.write(row_pq, 9, invoice.inward_date, design_8)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_8)
                    if invoice.issued_date:
                        worksheet1.write(row_pq, 10, invoice.issued_date, design_8)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_8)
                    if invoice.approved_by:
                        worksheet1.write(row_pq, 12, invoice.approved_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_8)
                    if invoice.po_approved_by:
                        worksheet1.write(row_pq, 13, invoice.po_approved_by, design_8)
                    else:
                        worksheet1.write(row_pq, 13, '-', design_8)
                    if invoice.store_incharge:
                        worksheet1.write(row_pq, 14, invoice.store_incharge, design_8)
                    else:
                        worksheet1.write(row_pq, 14, '-', design_8)
                    worksheet1.write(row_pq, 15, invoice.state, design_9)
                    row_pq_new = row_pq
                    for material in invoice.request_product_lines:
                        worksheet1.write(row_pq_new, 4, material.product_id.name, design_8)
                        worksheet1.write(row_pq_new, 6, material.product_uom_qty, design_9)
                        row_pq_new += 1
                    row_pq_new = row_pq
                    for material_approved in invoice.product_lines:
                        worksheet1.write(row_pq_new, 11, '%.2f' % material_approved.qty_shipped, design_8)
                        worksheet1.write(row_pq_new, 7, material_approved.product_uom_qty, design_9)
                        row_pq_new += 1
                    sl_no += 1
                    row_pq = row_pq_new
            else:
                material = record.env['material.requisition.indent'].sudo().search(domain10)
                for invoice in material:
                    ref_date1 = invoice.indent_date
                    updated_date = invoice.required_date
                    verified_date = invoice.verified_date
                    issued_date = invoice.issued_date
                    import datetime
                    if ref_date1:
                        d11 = str(ref_date1)
                        dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d %H:%M:%S')
                        date1 = dt21.strftime("%d/%m/%Y")
                    if updated_date:
                        d22 = str(updated_date)
                        dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                        invoice_updated_date = dt22.strftime("%d/%m/%Y")
                    if verified_date:
                        d33 = str(verified_date)
                        dt23 = datetime.datetime.strptime(d33, '%Y-%m-%d %H:%M:%S')
                        verified_date = dt23.strftime("%d/%m/%Y")
                    worksheet1.write(row_pq, 0, sl_no, design_8)
                    if invoice.name:
                        worksheet1.write(row_pq, 1, invoice.name, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_8)
                    if invoice.request_raised_for.name:
                        worksheet1.write(row_pq, 2, invoice.request_raised_for.name, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_8)
                    if invoice.request_raised_for.department_id.name:
                        worksheet1.write(row_pq, 3, invoice.request_raised_for.department_id.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_8)
                    if ref_date1:
                        worksheet1.write(row_pq, 5, date1, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_8)
                    if invoice.verified_date:
                        worksheet1.write(row_pq, 8, verified_date, design_8)
                    else:
                        worksheet1.write(row_pq, 8, '-', design_8)
                    if invoice.inward_date:
                        worksheet1.write(row_pq, 9, invoice.inward_date, design_8)
                    else:
                        worksheet1.write(row_pq, 9, '-', design_8)
                    if invoice.issued_date:
                        worksheet1.write(row_pq, 10, invoice.issued_date, design_8)
                    else:
                        worksheet1.write(row_pq, 10, '-', design_8)
                    if invoice.approved_by:
                        worksheet1.write(row_pq, 12, invoice.approved_by.name, design_8)
                    else:
                        worksheet1.write(row_pq, 12, '-', design_8)
                    if invoice.po_approved_by:
                        worksheet1.write(row_pq, 13, invoice.po_approved_by, design_8)
                    else:
                        worksheet1.write(row_pq, 13, '-', design_8)
                    if invoice.store_incharge:
                        worksheet1.write(row_pq, 14, invoice.store_incharge, design_8)
                    else:
                        worksheet1.write(row_pq, 14, '-', design_8)
                    worksheet1.write(row_pq, 15, invoice.state, design_9)
                    row_pq_new = row_pq
                    for material in invoice.request_product_lines:
                        worksheet1.write(row_pq_new, 4, material.product_id.name, design_8)
                        worksheet1.write(row_pq_new, 6, material.product_uom_qty, design_9)
                        row_pq_new += 1
                    row_pq_new = row_pq
                    for material_approved in invoice.product_lines:
                        worksheet1.write(row_pq_new, 11, '%.2f' % material_approved.qty_shipped, design_8)
                        worksheet1.write(row_pq_new, 7, material_approved.product_uom_qty, design_9)
                        row_pq_new += 1
                    sl_no += 1
                    row_pq = row_pq_new

        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': 'Material Requisition Report - [ %s ].xls' % self.date,
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'material.requisition.excel.report.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }


class StockDirectDeliveryTransferWizard(models.TransientModel):
    _name = 'stock.direct.delivery.transfer.wizard'
    _description = "Stock Direct Delivery Transfer Wizard"

    def _get_stock_type_ids(self):
        data = self.env['stock.picking.type'].search([])
        for line in data:
            if line.code == 'outgoing' and line.name == 'Direct Delivery':
                return line

    def _default_employee(self):
        emp_ids = self.sudo().env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    start_date = fields.Date('Start date', required=True)
    end_date = fields.Date('End date', required=True)
    attachment = fields.Binary('File')
    attach_name = fields.Char('Attachment Name')
    summary_file = fields.Binary('Direct Delivery Report')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Direct Delivery Report')
    current_time = fields.Date('Current Time', default=lambda self: fields.Datetime.now())
    picking_type_id = fields.Many2one('stock.picking.type', 'Warehouse',
                                      domain="[('name','=', 'Direct Delivery')]",
                                      help="This will determine picking type of incoming shipment")
    delivery_supplier_ids = fields.Many2many('hr.employee', string='Request Raised For',
                                             help="Delivery Receiver of the Stock", )
    delivery_receiver_from_sender = fields.Many2one('hr.employee', string='Delivery Raised By',
                                                    help="Responsible person for the Direct Delivery Request",
                                                    default=_default_employee, readonly=1)
    product_ids = fields.Many2many('product.product', string="Product")
    ho_department_ids = fields.Many2many('ho.department', string="HO Departments")
    delivery_status = fields.Selection([
        ('delivered', 'Delivered'),
        ('ready', 'Ready To Delivery'),
    ], string="Delivery Status")
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    ams_time = datetime.now() + timedelta(hours=5, minutes=30)
    date = ams_time.strftime('%d-%m-%Y %H:%M:%S')

    def action_get_direct_delivery_report_excel(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('STOCK DEPARTMENT To DEPARTMENT DELIVERY REPORT')

        design_6 = easyxf('align: horiz left;font: bold 1;')
        design_7 = easyxf('align: horiz center;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_13 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')
        design_14 = easyxf('align: horiz center;')

        worksheet1.col(0).width = 1800
        worksheet1.col(1).width = 6000
        worksheet1.col(2).width = 7000
        worksheet1.col(3).width = 4500
        worksheet1.col(4).width = 5000
        worksheet1.col(5).width = 5500
        worksheet1.col(6).width = 10500
        worksheet1.col(7).width = 5500
        worksheet1.col(8).width = 3800
        worksheet1.col(9).width = 3800
        worksheet1.col(10).width = 3800
        worksheet1.col(11).width = 6500
        worksheet1.col(12).width = 4500
        worksheet1.col(13).width = 7000
        worksheet1.col(14).width = 5000
        worksheet1.col(15).width = 5000
        worksheet1.col(16).width = 5000

        rows = 0
        cols = 0
        row_pq = 5

        worksheet1.set_panes_frozen(True)
        worksheet1.set_horz_split_pos(rows + 1)
        worksheet1.set_remove_splits(True)

        col_1 = 0
        worksheet1.write_merge(rows, rows, 2, 6, 'Direct Delivery Stock Report', design_13)
        rows += 1
        worksheet1.write(rows, 3, 'FROM', design_7)
        worksheet1.write(rows, 4, self.start_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, 3, 'TO', design_7)
        worksheet1.write(rows, 4, self.end_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, 3, 'GENERATED BY', design_7)
        worksheet1.write(rows, 4, self.user_id.name, design_7)
        rows += 1
        # worksheet1.write(rows, 3, 'DEPARTMENT', design_7)
        # worksheet1.write(rows, 4, self.material_request_raised_by.department_id.name, design_7)
        # rows += 2
        worksheet1.write(rows, col_1, _('Sl.No'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Reference'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Direct Indent No'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Request Raised For'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Department'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Delivery Date'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Product'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Product Category'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Product Type'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('On Hand Qty'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Demand Qty'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Delivered Qty'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('UOM'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Balance Qty As on Dated'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Delivery Status'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('Collected By'), design_13)
        col_1 += 1

        sl_no = 1
        row_pq = row_pq + 1
        mr_num = []
        res = []
        for record in self:
            domain = [
                ('date_done', '>=', record.start_date),
                ('date_done', '<=', record.end_date),
                ('ho_department', '=', record.ho_department_ids.ids),
                ('delivery_receiver', '=', record.delivery_supplier_ids.ids),
                ('state', '=', 'done'),
                ('picking_type_id', '=', record.picking_type_id.id),
            ]
            domain1 = [
                ('scheduled_date', '>=', record.start_date),
                ('date_done', '<=', record.end_date),
                ('state', '=', 'done'),
                ('picking_type_id', '=', record.picking_type_id.id),
                ('ho_department', '=', record.ho_department_ids.ids),
                ('delivery_receiver', '=', record.delivery_supplier_ids.ids),
            ]
            domain2 = [
                ('scheduled_date', '>=', record.start_date),
                ('date_done', '<=', record.end_date),
                ('state', '!=', 'done'),
                ('picking_type_id', '=', record.picking_type_id.id),
            ]

            domain3 = [
                ('scheduled_date', '>=', record.start_date),
                ('date_done', '<=', record.end_date),
                ('delivery_receiver', '=', record.delivery_supplier_ids.ids),
                ('picking_type_id', '=', record.picking_type_id.id),
                ('state', '=', 'done'),
            ]
            domain4 = [
                ('date_done', '>=', record.start_date),
                ('date_done', '<=', record.end_date),
                ('ho_department', '=', record.ho_department_ids.ids),
                ('picking_type_id', '=', record.picking_type_id.id),
            ]
            domain5 = [
                ('scheduled_date', '>=', record.start_date),
                ('date_done', '<=', record.end_date),
                ('picking_type_id', '=', record.picking_type_id.id),
                ('state', '=', 'done'),
            ]
            if record.start_date and record.end_date and record.ho_department_ids and record.delivery_supplier_ids:
                picking = record.env['stock.picking'].sudo().search(domain)
                for invoice in picking:
                    updated_date = invoice.date_done
                    import datetime
                    d22 = str(updated_date)
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y")
                    worksheet1.write(row_pq, 0, sl_no, design_14)
                    if invoice.delivery_receiver.name:
                        worksheet1.write(row_pq, 1, invoice.name, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_8)
                    if invoice.origin:
                        worksheet1.write(row_pq, 2, invoice.origin, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_14)
                    if invoice.delivery_receiver.name:
                        worksheet1.write(row_pq, 3, invoice.delivery_receiver.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_8)
                    if invoice.ho_department.name:
                        worksheet1.write(row_pq, 4, invoice.ho_department.name, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_8)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_8)
                    for product in invoice.move_ids_without_package:
                        worksheet1.write(row_pq, 6, product.product_id.display_name, design_8)
                        worksheet1.write(row_pq, 7, product.product_id.categ_id.name, design_8)
                        if invoice.product_id.detailed_type == 'product':
                            product_type = 'Storable Product'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        elif invoice.product_id.detailed_type == 'consu':
                            product_type = 'Consumable'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        elif invoice.product_id.detailed_type == 'service':
                            product_type = 'Service'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        on_hand_one = product.quantity_done + product.product_id.qty_available
                        worksheet1.write(row_pq, 9, on_hand_one, design_9)
                        worksheet1.write(row_pq, 10, product.product_uom_qty, design_9)
                        worksheet1.write(row_pq, 11, product.quantity_done, design_9)
                        worksheet1.write(row_pq, 12, product.product_uom.name, design_8)
                        worksheet1.write(row_pq, 13, product.product_id.qty_available, design_9)
                        if invoice.collected_by:
                            worksheet1.write(row_pq, 15, invoice.collected_by, design_8)
                        else:
                            worksheet1.write(row_pq, 15, '-', design_14)
                        if invoice.state == 'done':
                            status = 'Delivered'
                        else:
                            status = 'Ready to Delivery'
                        worksheet1.write(row_pq, 14, status, design_8)
                        row_pq += 1
                    sl_no += 1
            elif record.delivery_supplier_ids:
                picking = record.env['stock.picking'].sudo().search(domain3)
                for invoice in picking:
                    updated_date = invoice.date_done
                    import datetime
                    d22 = str(updated_date)
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y")
                    worksheet1.write(row_pq, 0, sl_no, design_14)
                    if invoice.delivery_receiver.name:
                        worksheet1.write(row_pq, 1, invoice.name, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_8)
                    if invoice.origin:
                        worksheet1.write(row_pq, 2, invoice.origin, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_14)
                    if invoice.delivery_receiver.name:
                        worksheet1.write(row_pq, 3, invoice.delivery_receiver.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_8)
                    if invoice.ho_department.name:
                        worksheet1.write(row_pq, 4, invoice.ho_department.name, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_8)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_8)
                    for product in invoice.move_ids_without_package:
                        worksheet1.write(row_pq, 6, product.product_id.display_name, design_8)
                        worksheet1.write(row_pq, 7, product.product_id.categ_id.name, design_8)
                        if invoice.product_id.detailed_type == 'product':
                            product_type = 'Storable Product'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        elif invoice.product_id.detailed_type == 'consu':
                            product_type = 'Consumable'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        elif invoice.product_id.detailed_type == 'service':
                            product_type = 'Service'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        on_hand_one = product.quantity_done + product.product_id.qty_available
                        worksheet1.write(row_pq, 9, on_hand_one, design_9)
                        worksheet1.write(row_pq, 10, product.product_uom_qty, design_9)
                        worksheet1.write(row_pq, 11, product.quantity_done, design_9)
                        worksheet1.write(row_pq, 12, product.product_uom.name, design_8)
                        worksheet1.write(row_pq, 13, product.product_id.qty_available, design_9)
                        if invoice.collected_by:
                            worksheet1.write(row_pq, 15, invoice.collected_by, design_8)
                        else:
                            worksheet1.write(row_pq, 15, '-', design_14)
                        if invoice.state == 'done':
                            status = 'Delivered'
                        else:
                            status = 'Ready to Delivery'
                        worksheet1.write(row_pq, 14, status, design_8)
                        row_pq += 1
                    sl_no += 1

            elif record.start_date and record.end_date and record.ho_department_ids:
                picking = record.env['stock.picking'].sudo().search(domain4)
                for invoice in picking:
                    updated_date = invoice.date_done
                    import datetime
                    d22 = str(updated_date)
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y")
                    worksheet1.write(row_pq, 0, sl_no, design_14)
                    if invoice.delivery_receiver.name:
                        worksheet1.write(row_pq, 1, invoice.name, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_8)
                    if invoice.origin:
                        worksheet1.write(row_pq, 2, invoice.origin, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_14)
                    if invoice.delivery_receiver.name:
                        worksheet1.write(row_pq, 3, invoice.delivery_receiver.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_8)
                    if invoice.ho_department.name:
                        worksheet1.write(row_pq, 4, invoice.ho_department.name, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_8)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_8)
                    for product in invoice.move_ids_without_package:
                        worksheet1.write(row_pq, 6, product.product_id.display_name, design_8)
                        worksheet1.write(row_pq, 7, product.product_id.categ_id.name, design_8)
                        if invoice.product_id.detailed_type == 'product':
                            product_type = 'Storable Product'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        elif invoice.product_id.detailed_type == 'consu':
                            product_type = 'Consumable'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        elif invoice.product_id.detailed_type == 'service':
                            product_type = 'Service'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        on_hand_one = product.quantity_done + product.product_id.qty_available
                        worksheet1.write(row_pq, 9, on_hand_one, design_9)
                        worksheet1.write(row_pq, 10, product.product_uom_qty, design_9)
                        worksheet1.write(row_pq, 11, product.quantity_done, design_9)
                        worksheet1.write(row_pq, 12, product.product_uom.name, design_8)
                        worksheet1.write(row_pq, 13, product.product_id.qty_available, design_9)
                        if invoice.collected_by:
                            worksheet1.write(row_pq, 15, invoice.collected_by, design_8)
                        else:
                            worksheet1.write(row_pq, 15, '-', design_14)
                        if invoice.state == 'done':
                            status = 'Delivered'
                        else:
                            status = 'Ready to Delivery'
                        worksheet1.write(row_pq, 14, status, design_8)
                        row_pq += 1
                    sl_no += 1
            else:
                picking = record.env['stock.picking'].sudo().search(domain5, order='date_done')
                for invoice in picking:
                    updated_date = invoice.date_done
                    import datetime
                    d22 = str(updated_date)
                    dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d %H:%M:%S')
                    invoice_updated_date = dt22.strftime("%d/%m/%Y")
                    worksheet1.write(row_pq, 0, sl_no, design_14)
                    if invoice.delivery_receiver.name:
                        worksheet1.write(row_pq, 1, invoice.name, design_8)
                    else:
                        worksheet1.write(row_pq, 1, '-', design_8)
                    if invoice.origin:
                        worksheet1.write(row_pq, 2, invoice.origin, design_8)
                    else:
                        worksheet1.write(row_pq, 2, '-', design_14)
                    if invoice.delivery_receiver.name:
                        worksheet1.write(row_pq, 3, invoice.delivery_receiver.name, design_8)
                    else:
                        worksheet1.write(row_pq, 3, '-', design_8)
                    if invoice.ho_department.name:
                        worksheet1.write(row_pq, 4, invoice.ho_department.name, design_8)
                    else:
                        worksheet1.write(row_pq, 4, '-', design_8)
                    if invoice_updated_date:
                        worksheet1.write(row_pq, 5, invoice_updated_date, design_8)
                    else:
                        worksheet1.write(row_pq, 5, '-', design_8)
                    for product in invoice.move_ids_without_package:
                        worksheet1.write(row_pq, 6, product.product_id.display_name, design_8)
                        on_hand_one = product.quantity_done + product.product_id.qty_available
                        worksheet1.write(row_pq, 7, product.product_id.categ_id.name, design_8)
                        if invoice.product_id.detailed_type == 'product':
                            product_type = 'Storable Product'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        elif invoice.product_id.detailed_type == 'consu':
                            product_type = 'Consumable'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        elif invoice.product_id.detailed_type == 'service':
                            product_type = 'Service'
                            worksheet1.write(row_pq, 8, product_type, design_8)
                        worksheet1.write(row_pq, 9, on_hand_one, design_9)
                        worksheet1.write(row_pq, 10, product.product_uom_qty, design_9)
                        worksheet1.write(row_pq, 11, product.quantity_done, design_9)
                        worksheet1.write(row_pq, 12, product.product_uom.name, design_8)
                        worksheet1.write(row_pq, 13, product.product_id.qty_available, design_9)
                        if invoice.collected_by:
                            worksheet1.write(row_pq, 15, invoice.collected_by, design_8)
                        else:
                            worksheet1.write(row_pq, 15, '-', design_14)
                        if invoice.state == 'done':
                            status = 'Delivered'
                        else:
                            status = 'Ready to Delivery'
                        worksheet1.write(row_pq, 14, status, design_8)
                        row_pq += 1
                    sl_no += 1
        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': 'Internal Delivery Report - [ %s ].xls' % self.date,
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'stock.direct.delivery.transfer.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }
