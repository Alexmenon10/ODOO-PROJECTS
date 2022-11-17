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


class CurrentStockReport(models.TransientModel):
    _name = 'current.stock.report'
    _description = 'Current Stock Report Wizard'

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

    stock_warehouse = fields.Many2one('stock.warehouse', string='WareHouse')
    product_cat = fields.Many2many('product.category', string="Product Category")
    stock_location = fields.Many2many('stock.location', string="Location")
    all_product_list = fields.Boolean(string='All Product Category')
    zero_value_entry_boolean = fields.Boolean(string='Non Zero')

    def action_get_current_stock_report(self):
        workbook = xlwt.Workbook()
        worksheet1 = workbook.add_sheet('Current Stock Report')
        worksheet2 = workbook.add_sheet('Product Purchase History Report')

        design_6 = easyxf('align: horiz left;font: bold 1;')
        design_7 = easyxf('align: horiz center;font: bold 1;')
        design_8 = easyxf('align: horiz left;')
        design_9 = easyxf('align: horiz right;font: bold 1;')
        design_10 = easyxf('align: horiz right; pattern: pattern solid, fore_colour red;')
        design_11 = easyxf('align: horiz right; pattern: pattern solid, fore_colour green;')
        design_12 = easyxf('align: horiz right; pattern: pattern solid, fore_colour gray25;')
        design_13 = easyxf('align: horiz center;font: bold 1;pattern: pattern solid, fore_colour gray25;')

        worksheet1.col(0).width = 1800
        worksheet1.col(1).width = 7000
        worksheet1.col(2).width = 5000
        worksheet1.col(3).width = 4000
        worksheet1.col(4).width = 4500
        worksheet1.col(5).width = 4000
        worksheet1.col(6).width = 4000
        worksheet1.col(7).width = 4300
        worksheet1.col(8).width = 4500
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
        worksheet1.write_merge(rows, rows, 2, 6, 'CURRENT STOCK REPORT', design_13)
        rows += 1
        worksheet1.write(rows, 3, 'START DATE', design_13)
        worksheet1.write(rows, 4, self.start_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, 3, 'END DATE', design_13)
        worksheet1.write(rows, 4, self.end_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet1.write(rows, 3, 'GENARATED BY', design_13)
        worksheet1.write(rows, 4, self.user_id.name, design_7)
        rows += 2
        worksheet1.write(rows, col_1, _('Sl.No'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('PRODUCT NAME '), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('PRODUCT CATEGORY'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('UOM'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('PRODUCT TYPE'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('ONHAND QTY'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('RECEIVED (IN)'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('DELIVERED (OUT)'), design_13)
        col_1 += 1
        worksheet1.write(rows, col_1, _('ADJUSTMENT'), design_13)
        col_1 += 1

        sl_no = 1
        row_pq = row_pq + 1

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
                ('date', '>=', record.start_date),
                ('date', '<=', record.end_date),
                ('state', '=', 'done'),
            ]
            domain1 = [
                ('categ_id', '=', record.product_cat.ids),
            ]
            domain2 = [
                ('detailed_type', '=', 'product'),
            ]
            if record.stock_location and record.product_cat:
                stock_move = record.env['product.template'].sudo().search(domain1)
                for stock in stock_move:
                    sub_domain1 = [
                        ('date', '>=', record.start_date),
                        ('date', '<=', record.end_date),
                        ('product_id', '=', stock.name),
                        ('state', '=', 'done'),
                    ]
                    stock_line = record.env['stock.move.line'].sudo().search(sub_domain1)
                    row_new = row_pq
                    in_qty = 0
                    out_qty = 0
                    adjust_qty = 0
                    for move_line in stock_line:
                       if move_line:
                                if move_line.picking_code == 'incoming':
                                    in_qty += move_line.qty_done
                                if move_line.picking_code == 'outgoing':
                                    out_qty += move_line.qty_done
                                if not move_line.picking_code:
                                    adjust_qty += move_line.qty_done
                    if record.zero_value_entry_boolean == True:
                        if stock.qty_available > 0:
                            worksheet1.write(row_pq, 6, in_qty, design_9)
                            worksheet1.write(row_pq, 7, out_qty, design_9)
                            worksheet1.write(row_pq, 8, adjust_qty, design_9)
                            worksheet1.write(row_pq, 0, sl_no, design_7)
                            if stock.name:
                                worksheet1.write(row_pq, 1, stock.display_name, design_8)
                            else:
                                worksheet1.write(row_pq, 1, '-', design_7)
                            if stock.categ_id:
                                worksheet1.write(row_pq, 2, stock.categ_id.name, design_8)
                            else:
                                worksheet1.write(row_pq, 2, '-', design_7)
                            if stock.uom_id:
                                worksheet1.write(row_pq, 3, stock.uom_id.name, design_8)
                            else:
                                worksheet1.write(row_pq, 3, '-', design_7)
                            if stock.detailed_type == 'product':
                                worksheet1.write(row_pq, 4, 'Storable Product', design_8)
                            elif stock.detailed_type == 'service':
                                worksheet1.write(row_pq, 4, 'Service', design_8)
                            elif stock.detailed_type == 'consu':
                                worksheet1.write(row_pq, 4, 'Consumable', design_8)
                            else:
                                worksheet1.write(row_pq, 4, '-', design_7)
                            if stock.qty_available:
                                worksheet1.write(row_pq, 5, stock.qty_available, design_9)
                            else:
                                worksheet1.write(row_pq, 5, 0, design_7)
                            sl_no += 1
                            row_pq += 1
                    else:
                        worksheet1.write(row_pq, 6, in_qty, design_9)
                        worksheet1.write(row_pq, 7, out_qty, design_9)
                        worksheet1.write(row_pq, 8, adjust_qty, design_9)
                        worksheet1.write(row_pq, 0, sl_no, design_7)
                        if stock.name:
                            worksheet1.write(row_pq, 1, stock.display_name, design_8)
                        else:
                            worksheet1.write(row_pq, 1, '-', design_7)
                        if stock.categ_id:
                            worksheet1.write(row_pq, 2, stock.categ_id.name, design_8)
                        else:
                            worksheet1.write(row_pq, 2, '-', design_7)
                        if stock.uom_id:
                            worksheet1.write(row_pq, 3, stock.uom_id.name, design_8)
                        else:
                            worksheet1.write(row_pq, 3, '-', design_7)
                        if stock.detailed_type == 'product':
                            worksheet1.write(row_pq, 4, 'Storable Product', design_8)
                        elif stock.detailed_type == 'service':
                            worksheet1.write(row_pq, 4, 'Service', design_8)
                        elif stock.detailed_type == 'consu':
                            worksheet1.write(row_pq, 4, 'Consumable', design_8)
                        else:
                            worksheet1.write(row_pq, 4, '-', design_7)
                        if stock.qty_available:
                            worksheet1.write(row_pq, 5, stock.qty_available, design_9)
                        else:
                            worksheet1.write(row_pq, 5, 0, design_7)
                        sl_no += 1
                        row_pq += 1

            elif record.product_cat:
                stock_move = record.env['product.template'].sudo().search(domain1)
                for stock in stock_move:
                    sub_domain1 = [
                        ('date', '>=', record.start_date),
                        ('date', '<=', record.end_date),
                        ('product_id', '=', stock.name),
                        ('state', '=', 'done'),
                    ]
                    stock_line = record.env['stock.move.line'].sudo().search(sub_domain1)
                    row_new = row_pq
                    in_qty = 0
                    out_qty = 0
                    adjust_qty = 0
                    for move_line in stock_line:
                        if move_line:
                            if move_line.picking_code == 'incoming':
                                in_qty += move_line.qty_done
                            if move_line.picking_code == 'outgoing':
                                out_qty += move_line.qty_done
                            if not move_line.picking_code:
                                adjust_qty += move_line.qty_done
                    if record.zero_value_entry_boolean == True:
                        if stock.qty_available > 0:
                            worksheet1.write(row_pq, 6, in_qty, design_9)
                            worksheet1.write(row_pq, 7, out_qty, design_9)
                            worksheet1.write(row_pq, 8, adjust_qty, design_9)
                            worksheet1.write(row_pq, 0, sl_no, design_7)
                            if stock.name:
                                worksheet1.write(row_pq, 1, stock.display_name, design_8)
                            else:
                                worksheet1.write(row_pq, 1, '-', design_7)
                            if stock.categ_id:
                                worksheet1.write(row_pq, 2, stock.categ_id.name, design_8)
                            else:
                                worksheet1.write(row_pq, 2, '-', design_7)
                            if stock.uom_id:
                                worksheet1.write(row_pq, 3, stock.uom_id.name, design_8)
                            else:
                                worksheet1.write(row_pq, 3, '-', design_7)
                            if stock.detailed_type == 'product':
                                worksheet1.write(row_pq, 4, 'Storable Product', design_8)
                            elif stock.detailed_type == 'service':
                                worksheet1.write(row_pq, 4, 'Service', design_8)
                            elif stock.detailed_type == 'consu':
                                worksheet1.write(row_pq, 4, 'Consumable', design_8)
                            else:
                                worksheet1.write(row_pq, 4, '-', design_7)
                            if stock.qty_available:
                                worksheet1.write(row_pq, 5, stock.qty_available, design_9)
                            else:
                                worksheet1.write(row_pq, 5, 0, design_7)
                            sl_no += 1
                            row_pq += 1
                    else:
                        worksheet1.write(row_pq, 6, in_qty, design_9)
                        worksheet1.write(row_pq, 7, out_qty, design_9)
                        worksheet1.write(row_pq, 8, adjust_qty, design_9)
                        worksheet1.write(row_pq, 0, sl_no, design_7)
                        if stock.name:
                            worksheet1.write(row_pq, 1, stock.display_name, design_8)
                        else:
                            worksheet1.write(row_pq, 1, '-', design_7)
                        if stock.categ_id:
                            worksheet1.write(row_pq, 2, stock.categ_id.name, design_8)
                        else:
                            worksheet1.write(row_pq, 2, '-', design_7)
                        if stock.uom_id:
                            worksheet1.write(row_pq, 3, stock.uom_id.name, design_8)
                        else:
                            worksheet1.write(row_pq, 3, '-', design_7)
                        if stock.detailed_type == 'product':
                            worksheet1.write(row_pq, 4, 'Storable Product', design_8)
                        elif stock.detailed_type == 'service':
                            worksheet1.write(row_pq, 4, 'Service', design_8)
                        elif stock.detailed_type == 'consu':
                            worksheet1.write(row_pq, 4, 'Consumable', design_8)
                        else:
                            worksheet1.write(row_pq, 4, '-', design_7)
                        if stock.qty_available:
                            worksheet1.write(row_pq, 5, stock.qty_available, design_9)
                        else:
                            worksheet1.write(row_pq, 5, 0, design_7)
                        sl_no += 1
                        row_pq += 1

            elif record.stock_location:
                stock_move = record.env['product.template'].sudo().search(domain2)
                for stock in stock_move:
                    sub_domain1 = [
                        ('date', '>=', record.start_date),
                        ('date', '<=', record.end_date),
                        ('product_id', '=', stock.name),
                        ('state', '=', 'done'),
                    ]
                    stock_line = record.env['stock.move.line'].sudo().search(sub_domain1)
                    row_new = row_pq
                    in_qty = 0
                    out_qty = 0
                    adjust_qty = 0
                    for move_line in stock_line:
                       if move_line:
                            if move_line.picking_code == 'incoming':
                                in_qty += move_line.qty_done
                            if move_line.picking_code == 'outgoing':
                                out_qty += move_line.qty_done
                            if not move_line.picking_code:
                                adjust_qty += move_line.qty_done
                    if record.zero_value_entry_boolean == True:
                        if stock.qty_available > 0:
                            worksheet1.write(row_pq, 6, in_qty, design_9)
                            worksheet1.write(row_pq, 7, out_qty, design_9)
                            worksheet1.write(row_pq, 8, adjust_qty, design_9)
                            worksheet1.write(row_pq, 0, sl_no, design_7)
                            if stock.name:
                                worksheet1.write(row_pq, 1, stock.display_name, design_8)
                            else:
                                worksheet1.write(row_pq, 1, '-', design_7)
                            if stock.categ_id:
                                worksheet1.write(row_pq, 2, stock.categ_id.name, design_8)
                            else:
                                worksheet1.write(row_pq, 2, '-', design_7)
                            if stock.uom_id:
                                worksheet1.write(row_pq, 3, stock.uom_id.name, design_8)
                            else:
                                worksheet1.write(row_pq, 3, '-', design_7)
                            if stock.detailed_type == 'product':
                                worksheet1.write(row_pq, 4, 'Storable Product', design_8)
                            elif stock.detailed_type == 'service':
                                worksheet1.write(row_pq, 4, 'Service', design_8)
                            elif stock.detailed_type == 'consu':
                                worksheet1.write(row_pq, 4, 'Consumable', design_8)
                            else:
                                worksheet1.write(row_pq, 4, '-', design_7)
                            if stock.qty_available:
                                worksheet1.write(row_pq, 5, stock.qty_available, design_9)
                            else:
                                worksheet1.write(row_pq, 5, 0, design_7)
                            sl_no += 1
                            row_pq += 1
                    else:
                        worksheet1.write(row_pq, 6, in_qty, design_9)
                        worksheet1.write(row_pq, 7, out_qty, design_9)
                        worksheet1.write(row_pq, 8, adjust_qty, design_9)
                        worksheet1.write(row_pq, 0, sl_no, design_7)
                        if stock.name:
                            worksheet1.write(row_pq, 1, stock.display_name, design_8)
                        else:
                            worksheet1.write(row_pq, 1, '-', design_7)
                        if stock.categ_id:
                            worksheet1.write(row_pq, 2, stock.categ_id.name, design_8)
                        else:
                            worksheet1.write(row_pq, 2, '-', design_7)
                        if stock.uom_id:
                            worksheet1.write(row_pq, 3, stock.uom_id.name, design_8)
                        else:
                            worksheet1.write(row_pq, 3, '-', design_7)
                        if stock.detailed_type == 'product':
                            worksheet1.write(row_pq, 4, 'Storable Product', design_8)
                        elif stock.detailed_type == 'service':
                            worksheet1.write(row_pq, 4, 'Service', design_8)
                        elif stock.detailed_type == 'consu':
                            worksheet1.write(row_pq, 4, 'Consumable', design_8)
                        else:
                            worksheet1.write(row_pq, 4, '-', design_7)
                        if stock.qty_available:
                            worksheet1.write(row_pq, 5, stock.qty_available, design_9)
                        else:
                            worksheet1.write(row_pq, 5, 0, design_7)
                        sl_no += 1
                        row_pq += 1
            else:
                stock_move = record.env['product.template'].sudo().search(domain2)
                for stock in stock_move:
                    sub_domain1 = [
                        ('date', '>=', record.start_date),
                        ('date', '<=', record.end_date),
                        ('product_id', '=', stock.name),
                        ('state', '=', 'done'),
                    ]
                    stock_line = record.env['stock.move.line'].sudo().search(sub_domain1)
                    row_new = row_pq
                    in_qty = 0
                    out_qty = 0
                    adjust_qty = 0
                    for move_line in stock_line:
                        if move_line:
                            if move_line.picking_code == 'incoming':
                                in_qty += move_line.qty_done
                            if move_line.picking_code == 'outgoing':
                                out_qty += move_line.qty_done
                            if not move_line.picking_code:
                                adjust_qty += move_line.qty_done
                    if record.zero_value_entry_boolean == True:
                        if stock.qty_available > 0:
                            worksheet1.write(row_pq, 6, in_qty, design_9)
                            worksheet1.write(row_pq, 7, out_qty, design_9)
                            worksheet1.write(row_pq, 8, adjust_qty, design_9)
                            worksheet1.write(row_pq, 0, sl_no, design_7)
                            if stock.name:
                                worksheet1.write(row_pq, 1, stock.display_name, design_8)
                            else:
                                worksheet1.write(row_pq, 1, '-', design_7)
                            if stock.categ_id:
                                worksheet1.write(row_pq, 2, stock.categ_id.name, design_8)
                            else:
                                worksheet1.write(row_pq, 2, '-', design_7)
                            if stock.uom_id:
                                worksheet1.write(row_pq, 3, stock.uom_id.name, design_8)
                            else:
                                worksheet1.write(row_pq, 3, '-', design_7)
                            if stock.detailed_type == 'product':
                                worksheet1.write(row_pq, 4, 'Storable Product', design_8)
                            elif stock.detailed_type == 'service':
                                worksheet1.write(row_pq, 4, 'Service', design_8)
                            elif stock.detailed_type == 'consu':
                                worksheet1.write(row_pq, 4, 'Consumable', design_8)
                            else:
                                worksheet1.write(row_pq, 4, '-', design_7)
                            if stock.qty_available:
                                worksheet1.write(row_pq, 5, stock.qty_available, design_9)
                            else:
                                worksheet1.write(row_pq, 5, 0, design_7)
                            sl_no += 1
                            row_pq += 1
                    else:
                        worksheet1.write(row_pq, 6, in_qty, design_9)
                        worksheet1.write(row_pq, 7, out_qty, design_9)
                        worksheet1.write(row_pq, 8, adjust_qty, design_9)
                        worksheet1.write(row_pq, 0, sl_no, design_7)
                        if stock.name:
                            worksheet1.write(row_pq, 1, stock.display_name, design_8)
                        else:
                            worksheet1.write(row_pq, 1, '-', design_7)
                        if stock.categ_id:
                            worksheet1.write(row_pq, 2, stock.categ_id.name, design_8)
                        else:
                            worksheet1.write(row_pq, 2, '-', design_7)
                        if stock.uom_id:
                            worksheet1.write(row_pq, 3, stock.uom_id.name, design_8)
                        else:
                            worksheet1.write(row_pq, 3, '-', design_7)
                        if stock.detailed_type == 'product':
                            worksheet1.write(row_pq, 4, 'Storable Product', design_8)
                        elif stock.detailed_type == 'service':
                            worksheet1.write(row_pq, 4, 'Service', design_8)
                        elif stock.detailed_type == 'consu':
                            worksheet1.write(row_pq, 4, 'Consumable', design_8)
                        else:
                            worksheet1.write(row_pq, 4, '-', design_7)
                        if stock.qty_available:
                            worksheet1.write(row_pq, 5, stock.qty_available, design_9)
                        else:
                            worksheet1.write(row_pq, 5, 0, design_7)
                        sl_no += 1
                        row_pq += 1

                    
        # ---------------------------- worksheet Two ---------------------------

        worksheet2.col(0).width = 1800
        worksheet2.col(1).width = 7000
        worksheet2.col(2).width = 5000
        worksheet2.col(3).width = 4000
        worksheet2.col(4).width = 4500
        worksheet2.col(5).width = 4000
        worksheet2.col(6).width = 4000
        worksheet2.col(7).width = 4300
        worksheet2.col(8).width = 4500
        worksheet2.col(9).width = 3500
        worksheet2.col(10).width = 3500
        worksheet2.col(11).width = 3500
        worksheet2.col(12).width = 3500
        worksheet2.col(13).width = 5000
        worksheet2.col(14).width = 5000
        worksheet2.col(15).width = 5000

        rows = 0
        cols = 0
        row_pq = 6

        worksheet2.set_panes_frozen(True)
        worksheet2.set_horz_split_pos(rows + 1)
        worksheet2.set_remove_splits(True)

        col_1 = 0
        worksheet2.write_merge(rows, rows, 2, 6, 'PRODUCT PURCHASE HISTORY REPORT', design_13)
        rows += 1
        worksheet2.write(rows, 3, 'START DATE', design_13)
        worksheet2.write(rows, 4, self.start_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet2.write(rows, 3, 'END DATE', design_13)
        worksheet2.write(rows, 4, self.end_date.strftime('%d-%m-%Y'), design_7)
        rows += 1
        worksheet2.write(rows, 3, 'GENARATED BY', design_13)
        worksheet2.write(rows, 4, self.user_id.name, design_7)
        rows += 2

        worksheet2.write(rows, col_1, _('Sl.No'), design_13)
        col_1 += 1
        worksheet2.write(rows, col_1, _('DATE'), design_13)
        col_1 += 1
        worksheet2.write(rows, col_1, _('PRODUCT NAME'), design_13)
        col_1 += 1
        worksheet2.write(rows, col_1, _('PRODUCT CATEGORY'), design_13)
        col_1 += 1
        worksheet2.write(rows, col_1, _('REFERENCE'), design_13)
        col_1 += 1
        worksheet2.write(rows, col_1, _('SUPPLIER'), design_13)
        col_1 += 1
        worksheet2.write(rows, col_1, _('PRICE'), design_13)
        col_1 += 1

        sl_no = 1
        row_pq = row_pq + 1

        for record2 in self:
            domain11 = [
                ('purchase_order_date', '>=', record2.start_date),
                ('purchase_order_date', '<=', record2.end_date),
            ]
            purchase_history = record2.env['sr.purchase.price.history'].sudo().search(domain11, order='purchase_order_id asc')
            for purchase in purchase_history:
                worksheet2.write(row_pq, 0, sl_no, design_7)
                if purchase.purchase_order_date:
                    worksheet2.write(row_pq, 1, str(purchase.purchase_order_date), design_8)
                else:
                    worksheet2.write(row_pq, 1, '-', design_7)
                if purchase.variant_id:
                    worksheet2.write(row_pq, 2, purchase.variant_id.display_name, design_8)
                else:
                    worksheet2.write(row_pq, 2, '-', design_7)
                if purchase.variant_id.categ_id:
                    worksheet2.write(row_pq, 3, purchase.variant_id.categ_id.name, design_8)
                else:
                    worksheet2.write(row_pq, 3, '-', design_7)
                if purchase.purchase_order_id:
                    worksheet2.write(row_pq, 4, purchase.purchase_order_id.name, design_8)
                else:
                    worksheet2.write(row_pq, 4, '-', design_7)
                if purchase.partner_id:
                    worksheet2.write(row_pq, 5, purchase.partner_id.name, design_8)
                else:
                    worksheet2.write(row_pq, 5, 0, design_7)
                if purchase.unit_price:
                    worksheet2.write(row_pq, 6, purchase.unit_price, design_8)
                else:
                    worksheet2.write(row_pq, 6, 0, design_7)
              
                sl_no += 1
                row_pq += 1


        fp = BytesIO()
        o = workbook.save(fp)
        fp.read()
        excel_file = base64.b64encode(fp.getvalue())
        self.write({'summary_file': excel_file, 'file_name': 'Current Stock Report - [ %s ].xls' % self.date,
                    'report_printed': True})
        fp.close()
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'current.stock.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }
