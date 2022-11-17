# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, http
import pdb
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from werkzeug.urls import url_encode
from odoo.http import request
from odoo.tools import email_re, email_split

# class Mrpbomline_inherit(models.Model):
#     _inherit= 'mrp.bom.line'


#     z_product_category_id = fields.Many2one('product.category',"Product Category",compute="get_product_category",store=True)
#     z_select_board= fields.Boolean("Select Board")

#     @api.depends('product_id')
#     def get_product_category(self):
#         for l in self:
#         	if l.product_id:
#         		l.z_product_category_id = l.product_id.categ_id.id
#         	else:
#         		l.z_product_category_id = False

# class Mrpbom_inherit(models.Model):
#     _inherit= 'mrp.bom'


#     def caliculate_qty_sf(self):
#         if self.bom_line_ids:
#             for bom_line in self.bom_line_ids:
#                 curr_length = 0.0
#                 curr_width = 0.0
#                 if not self.product_tmpl_id.id:
#                     current_product_id = self.env['product.product'].search([('product_tmpl_id','=',self.product_tmpl_id.id)])
#                 else:
#                     current_product_id = self.product_tmpl_id


#                 if bom_line.z_select_board == True:
#                     curr_length= current_product_id.product_dimension_ids.lengthx/304.8
#                     curr_width= current_product_id.product_dimension_ids.width/304.8
#                 if bom_line.z_select_board == True and curr_length and curr_width:
#                     bom_line.product_qty =curr_length *curr_width * self. product_qty

class Picking(models.Model):
    _inherit = "stock.picking"

    amount_total = fields.Float(string='Amount Total',store=True,compute='_amount_all')
    currency_id = fields.Many2one('res.currency', 'Currency Id',
        default=lambda self: self.env.company.currency_id.id)

    @api.depends('move_ids_without_package.quantity_done')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.move_ids_without_package:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_total': amount_untaxed + amount_tax,
            })

    

class StockMove(models.Model):
    _inherit= 'stock.move'

    price_unit = fields.Float(string='Price',store=True)
    tax_id = fields.Many2many('account.tax',string='Tax',store=True)
    price_tax = fields.Float(string='Price Tax',store=True,compute='_compute_amount')
    price_subtotal = fields.Float(string='Price Total',store=True,compute='compute_price_subtotal')
    z_qty_available = fields.Float(string='On Hand Qty',store=True,compute='compute_qty_avaliable')
    serial_no = fields.Integer(string='SL NO',compute="_compute_sl")

    @api.depends('product_id')
    def _compute_sl(self):
        var = 1
        for l in self:
            if l.serial_no == 0:
                l.serial_no = var + l.serial_no
                var += 1
            else:
                l.serial_no = 0


    @api.depends('product_id')
    def compute_qty_avaliable(self):
        self.z_qty_available = False
        for l in self:
            if l.product_id:
                l.z_qty_available = l.product_id.qty_available
            else:
                l.z_qty_available = False

    @api.depends('quantity_done')
    def compute_price_subtotal(self):
        for l in self:
            if l.quantity_done != 0.0:
                l.price_subtotal = l.z_supplier_rate * l.quantity_done
            else:
                l.price_subtotal = 0.0

    @api.depends('quantity_done', 'z_supplier_rate', 'tax_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.tax_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                # 'price_total': taxes['total_included'],
                # 'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        # Hook method to returns the different argument values for the
        # compute_all method, due to the fact that discounts mechanism
        # is not implemented yet on the purchase orders.
        # This method should disappear as soon as this feature is
        # also introduced like in the sales module.
        self.ensure_one()
        return {
            'price_unit': self.z_supplier_rate,
            'currency_id': self.picking_id.currency_id,
            'product_qty': self.quantity_done,
            'product': self.product_id,
            'partner': self.picking_id.partner_id,
        }

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        # apply putaway
        location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id,
            'picking_id': self.picking_id.id,
            'z_demand':self.product_uom_qty,
        }
        if quantity:
            uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom, rounding_method='HALF-UP')
            uom_quantity_back_to_product_uom = self.product_uom._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                vals = dict(vals, product_uom_qty=uom_quantity)
            else:
                vals = dict(vals, product_uom_qty=quantity, product_uom_id=self.product_id.uom_id.id)
        if reserved_quant:
            vals = dict(
                vals,
                location_id=reserved_quant.location_id.id,
                lot_id=reserved_quant.lot_id.id or False,
                package_id=reserved_quant.package_id.id or False,
                owner_id =reserved_quant.owner_id.id or False,
            )
        return vals

class StockMoveLine(models.Model):
    _inherit= 'stock.move.line'

    z_demand = fields.Float(string='Demand')


class StockMoveLines(models.Model):
    _inherit= 'purchase.order'

    z_terms_of_delivery = fields.Many2one('terms.delivery',string='Terms of Delivery')

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    serial_no = fields.Integer(string='SL NO',compute="_compute_sl")

    @api.depends('order_id.order_line')
    def _compute_sl(self):
        var = 1
        for l in self:
            if l.serial_no == 0:
                l.serial_no = var + l.serial_no
                var += 1
            else:
                l.serial_no = 0

    def _prepare_stock_moves(self, picking):
        data = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)

        for rec in data:
            rec['price_unit'] = self.price_unit
            rec['tax_id'] = [(6, 0, self.taxes_id.ids)]

        return data

class StockPicking(models.Model):
    _inherit= 'stock.picking'


    z_transporter = fields.Char(string='Transporter')
    zx_vehicle_no = fields.Char(string='Vehicle No.')
    # z_order_types = fields.Char(string='Order Type',store=True,compute='compute_order_type')
    url = fields.Char('Web link', compute='get_full_url')
    z_requested_by = fields.Many2one('res.users')
    z_requested_emp_id = fields.Many2one('hr.employee')
    invoice_ref = fields.Char(string='Invoice Reference')
    invoice_date = fields.Date(string='Invoice Date')

    
    @api.depends('purchase_id')
    def compute_order_type(self):
        for l in self:
            # l.z_order_types = l.purchase_id.z_order_type.name
            l.z_requested_emp_id = l.purchase_id.z_requested_emp_id.id

    @api.depends('purchase_id')
    def get_full_url(self):
        if self.purchase_id:
            base_url = self.env["ir.config_parameter"].get_param("web.base.url")
            url_params = {
                'id': self.id,
                'view_type': 'form',
                'model': 'stock.picking',
                'menu_id': self.env.ref('stock.all_picking').id,
                'action': self.env.ref('stock.action_picking_tree_all').id,
            }
            params = '/web?#%s' % url_encode(url_params)
            self.url = base_url + params
        else:
            self.url = False

    def button_validate(self):
        res = super(StockPicking,self).button_validate()
        # try:
        #     template_applicant_id = self.env.ref('mass_custom_fields.email_grn_requested_by_template').id
        # except ValueError:
        #     template_applicant_id = False
        # try:
        #     compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        # except ValueError:
        #     compose_form_id = False
        # partner_to = False
        # if self.purchase_id:
        #     partner_to = self.partner_id.id
        #     # partner_to = self.interviewer.ids

        # ctx = {
        #     'default_model': 'stock.picking',
        #     'default_res_id': self.id,
        #     'default_use_template': bool(template_applicant_id),
        #     'default_template_id': template_applicant_id,
        #     'default_composition_mode': 'comment',
        #     'evaluation_form_url': self.url,
        #     'custom_layout': "mail.mail_notification_light",
        #     'partner_to': partner_to  or  False,
        #     'mail_post_autofollow': False,
        #     # 'applicants_name':self.applicant_id.partner_name,
        #     # 'position':self.applicant_id.job_id.name,
        #     # 'stage_name':self.applicant_id.stage_id.name,
        # }
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_mode': 'form',
        #     'res_model': 'mail.compose.message',
        #     'views': [(compose_form_id, 'form')],
        #     'view_id': compose_form_id,
        #     'target': 'new',
        #     'context': ctx,
        # }
        template = self.env.ref('mass_custom_fields.email_grn_requested_by_template', False)
        template.send_mail(self.id , force_send=True)
        return res




class TermsOfDelivery(models.Model):
    _name = 'terms.delivery'
    _description = 'Terms Of Delivery'

    name = fields.Char(string='Description')

class OrderType(models.Model):
    _name = 'order.type'
    _description = 'Order Type'

    name = fields.Char(string='Type')

class ProductTemplate(models.Model):
    _inherit= 'product.template'

    product_reference = fields.Char(string='Product Reference')
    as_equipment = fields.Boolean(string='Is An Equipment')

class ProductProduct(models.Model):
    _inherit= 'product.product'

    product_reference = fields.Char(string='Product Reference')
    as_equipment = fields.Boolean(string='Is An Equipment')


# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     def _remove_delivery_line(self):
#         self.env['sale.order.line'].search([('order_id', 'in', self.ids), ('is_delivery', '=', True)])
#
#     # z_order_type = fields.Many2one('order.type',string='Order Type')
#     partner_state = fields.Many2one('res.country.state',string='State')

# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
#
#     qty_pending = fields.Float(string='Qty Pending')
#     open_order_value = fields.Float(string='Open Order Value')
#     disptach_value = fields.Float(string='Disptach Value')
#     total_order_value = fields.Float(string='Total Order Value')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    z_requested_by = fields.Many2one('res.users',string=' Requested By')
    z_requested_emp_id = fields.Many2one('hr.employee',string='Requested By')
    # z_order_type = fields.Many2one('order.type',string='Order Type')
    delivery_schedule = fields.Char(string='Delivery Schedule')
    required_delivery = fields.Date(string='Required Delivery')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner1 = fields.Char(string='Contact Person 1',default=' ')
    partner2 = fields.Char(string='Contact Person 2',default=' ')
    mobile1 = fields.Char(string=' Mobile',default=' ')
    mobile2 = fields.Char(string='  Mobile',default=' ')

# class MaintenanceEquipment(models.Model):
#     _inherit = "maintenance.equipment"
#
#     asset = fields.Many2one('account.asset',string='Asset')

class TavInvoiceAcc(models.Model):
    _inherit = 'account.move'

    no_of_packages = fields.Char(string='No of Packages')
    vehicle = fields.Many2many('fleet.vehicle',string='Vehicle')
    ext_vehicle_no = fields.Char(string='External Vehicle No')
    z_transporter = fields.Char(string='Transporter')


class AccountLineSlno(models.Model):
    _inherit = 'account.move.line'

    serial_no = fields.Integer(string='SL NO',compute="_compute_sl")

    @api.depends('move_id.invoice_line_ids')
    def _compute_sl(self):
        var = 1
        for l in self:
            if l.serial_no == 0:
                l.serial_no = var + l.serial_no
                var += 1
            else:
                l.serial_no = 0

        

