# -*- coding: utf-8 -*-

from odoo import models, fields, api
import pdb

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    journal_type_name = fields.Selection(string="Journal Name",related='move_id.journal_id.type')
    move_type_name = fields.Selection(related='move_id.move_type',store=True)
    account_user_type_id = fields.Char(related='account_id.user_type_id.name',store=True)
    move_invoice_date = fields.Date(compute='get_invoice_date',store=True,string='Bill Date')
    account_tax_name = fields.Char(related='tax_line_id.name')
    partner_name = fields.Char(related='partner_id.name',string="Partner Tag")
    gst_treatment = fields.Selection(related='partner_id.l10n_in_gst_treatment',string="GST Treatment")
    partner_ref = fields.Char(related='partner_id.ref',string="Partner Reference")
    partner_category_name = fields.Char(related='partner_id.category_id.name',string="Partner Category")
    partner_state_name = fields.Char(related='partner_id.state_id.name',string="Partner State")
    partner_country_name = fields.Char(related='partner_id.country_id.name',string="Partner Country")
    product_category = fields.Char(string="Product Category",related='product_id.categ_id.name')
    item_group= fields.Char(string="Item Group",related='product_id.item_group.name')
    product_group_1= fields.Char(string="Product Group 1",related='product_id.product_group_1.name')
    product_group_2 = fields.Char(string="Product Group 2",related='product_id.product_group_1.name')
    product_group_3 = fields.Char(string="Product Group 3",related='product_id.product_group_1.name')
    product_ref = fields.Char(string="Product Reference",related='product_id.default_code')
    # hsn_code_name = fields.Char(string="HSN Code",related='product_id.l10n_in_hsn_code.name')
    gst_name = fields.Char(related='partner_id.vat',string="Partner GST")
    cgst_rate = fields.Float(string="CGST %" ,compute='compute_tax_move_line',copy=False,compute_sudo=True)
    cgst_amount = fields.Float(string="CGST Amount",compute='compute_tax_move_line',copy=False,compute_sudo=True,store=True)
    sgst_rate = fields.Float(string="SGST %",compute='compute_tax_move_line' ,copy=False,compute_sudo=True)
    sgst_amount = fields.Float(string="SGST Amount",compute='compute_tax_move_line' ,copy=False,compute_sudo=True,store=True)
    igst_rate = fields.Float(string="IGST %",compute='compute_tax_move_line' ,copy=False,compute_sudo=True)
    igst_amount = fields.Float(string="IGST Amount",compute='compute_tax_move_line' ,copy=False,compute_sudo=True,store=True)
    tds_rate = fields.Float(string="TDS %",compute='compute_tax_move_line' ,copy=False,compute_sudo=True)
    tds_amount = fields.Float(string="TDS Amount",compute='compute_tax_move_line' ,copy=False,compute_sudo=True,store=True)
    amount_inclusive_tax = fields.Float(string="Amount Inclusive Tax",compute='compute_tax_move_line',store=True,copy=False,compute_sudo=True)
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse',compute='_get_warehouse_date',store=True,copy=False) 
    account_group_id = fields.Many2one(related='account_id.group_id',string='Accoun Group',store=True ,copy=False) 




    @api.depends('move_id')
    def _get_warehouse_date(self):
        for each in self:
            if each.purchase_line_id and each.move_id.move_type in ('in_invoice','in_refund'):
                each.warehouse_id = each.purchase_line_id.order_id.picking_type_id.warehouse_id.id
            elif each.move_id.invoice_origin and  each.move_id.move_type in ('out_invoice','out_refund'):
                sale_id = self.env['sale.order'].search([('name','=',each.move_id.invoice_origin)])
                if sale_id:
                    each.warehouse_id = sale_id.warehouse_id.id
                else:
                    each.warehouse_id = False

            else:
                each.warehouse_id=  False

    @api.depends('move_id')
    def get_invoice_date(self):
        for each in self:
            if each.move_id.invoice_date:
                each.move_invoice_date = each.move_id.invoice_date
            else:
                each.move_invoice_date=  False

    @api.depends('price_subtotal','tax_ids')
    def compute_tax_move_line(self):

        # self.hsn_code_name = False
        for line in self:

            line.cgst_rate = 0.0
            line.cgst_amount = 0.0
            line.sgst_rate = 0.0
            line.sgst_amount = 0.0
            line.igst_rate = 0.0
            line.igst_amount = 0.0

            line.tds_rate = 0.0
            line.tds_amount = 0.0
            line.amount_inclusive_tax = 0.0
            if line.tax_ids:
                for each_line in line.tax_ids:
                    # for line in self:

                    if each_line.amount_type == "group":
                        for each_tcs in each_line.children_tax_ids:
                            
                            if each_tcs.tax_group_id.name == 'IGST':
                                line.igst_rate  = each_tcs.amount if each_tcs.amount else 0.0
                                line.igst_amount  = (line.price_subtotal *line.igst_rate)/100
                            if each_tcs.tax_group_id.name == 'TDS':
                                line.tds_rate  = each_tcs.amount if each_tcs.amount else 0.0
                                line.tds_amount = (line.price_subtotal *line.tds_rate)/100
                            if each_tcs.tax_group_id.name == 'SGST' or each_tcs.tax_group_id.name == 'CGST':
                                line.sgst_rate  = each_tcs.amount if each_tcs.amount else 0
                                line.sgst_amount = (line.price_subtotal *line.sgst_rate)/100
                                line.cgst_rate  = each_tcs.amount if each_tcs.amount else 0
                                line.cgst_amount = (line.price_subtotal *line.cgst_rate)/100
                            # if each_tcs.tax_group_id.name == 'TCS':
                            #     line.tcs_rate  = each_tcs.amount if each_tcs.amount else 0.0
                            #     line.tcs_amount  = (line.price_subtotal *line.tcs_rate)/100
                        # if each_line.tax_group_id.name == 'RCM':
                            
                        #     for rcm_per in each_line.children_tax_ids:
                        #         line.rcm_rate += abs(rcm_per.amount)/2 if rcm_per.amount else 0.0
                        #         line.rcm_amount += line.price_subtotal*line.rcm_rate/100


                    
                    elif each_line.amount_type == "percent":
                        for each_tcs in each_line:
                            
                            if each_tcs.tax_group_id.name == 'IGST':
                                line.igst_rate  = each_tcs.amount if each_tcs.amount else 0.0
                                line.igst_amount  = (line.price_subtotal *line.igst_rate)/100
                            if each_tcs.tax_group_id.name == 'TDS':
                                line.tds_rate  = each_tcs.amount if each_tcs.amount else 0.0
                                line.tds_amount  = (line.price_subtotal *line.tds_rate)/100
                            if each_tcs.tax_group_id.name == 'SGST' or each_tcs.tax_group_id.name == 'CGST':
                                line.sgst_rate  = each_tcs.amount if each_tcs.amount else 0.0
                                line.sgst_amount = (line.price_subtotal *line.sgst_rate)/100
                                line.cgst_rate  = each_tcs.amount if each_tcs.amount else 0
                                line.cgst_amount = (line.price_subtotal *line.cgst_rate)/100
                            # if each_tcs.tax_group_id.name == 'TCS':
                            #     line.tcs_rate  = each_tcs.amount if each_tcs.amount else 0.0
                            #     line.tcs_amount  = (line.price_subtotal *line.tcs_rate)/100

            else:
                line.cgst_rate = 0
                line.cgst_amount = 0
                line.sgst_rate = 0
                line.sgst_amount = 0
                line.igst_rate = 0
                line.igst_amount = 0

                line.tds_rate = 0
                line.tds_amount = 0
                line.amount_inclusive_tax = 0

            line.amount_inclusive_tax = line.price_subtotal + line.cgst_amount + line.sgst_amount + line.igst_amount + line.tds_amount
            # if line.product_id:
            #     line.hsn_code_name = line.product_id.product_tmpl_id.l10n_in_hsn_code.name
            # else:
            #     line.hsn_code_name = False



            # sub_total_amount = line.price_subtotal
            # self.cgst_amount = line.price_subtotal / self.cgst_rate     

    # @api.depends('price_subtotal')
    # def compute_diff_tax(self):
    #     self.amount_inclusive_tax = 0
    #     for line in self:
    #         if line.cgst_rate:
    #             self.amount_inclusive_tax = line.price_subtotal/ line.cgst_rate