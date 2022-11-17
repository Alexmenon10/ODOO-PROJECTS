import base64
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models


class OneWayTripWizard(models.TransientModel):
    _name = 'one.way.trip'
    _description = 'One Way Trip Wizard'

    remarks = fields.Text('Warning')
    odometer_value = fields.Float('Odometer')
    one_way_attachment = fields.Binary(String="Attachments")
    one_way_attachment_detail = fields.Char(string="Attachment")


    def one_way_trip_remark(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['vehicle.gate.pass'].search([('id', '=', applicant_id)])
        active_id.approval_id.write({
            'one_way_trip_reamrk': self.remarks,
            'one_way_attachment': self.one_way_attachment,
            'one_way_attachment_detail': self.one_way_attachment_detail,
        })



class ExpenseBetaSheet(models.TransientModel):
    _name = 'expense.beta.sheet'
    _description = 'ExpenseBetaSheet'

    product_id = fields.Many2one('product.product', string='Expense Category')
    subproduct_id = fields.Many2one('vehicle.type', string="Sub Product", required=True)


    def _prepare_expense_deta(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['driver.beta.sheet'].search([('id', '=', applicant_id)])
        return {
            'employee_id': active_id.driver_name.id,
            'payment_mode': 'petty_cash',
            'name': active_id.driver_name.name + ' - Beta Sheet Payment',
            'unit_amount': False,
            'product_id': self.product_id.id,
            'subproduct_id': self.subproduct_id.id,
            'reference': active_id.name,
        }

    def set_expense_beta_sheet(self):
        applicant_id = self._context.get('active_ids')[0]
        active_id = self.env['driver.beta.sheet'].search([('id', '=', applicant_id)])
        expense_beta_sheet_history_obj = self.env['hr.expense']
        for order in self:
            expense_beta_sheet_data = order._prepare_expense_deta()
            expense_beta_sheet_data_id = expense_beta_sheet_history_obj.create(expense_beta_sheet_data)
        active_id.write({'enable_expense_beta_sheet': True})


