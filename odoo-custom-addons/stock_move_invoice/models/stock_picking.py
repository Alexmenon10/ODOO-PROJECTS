# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.float_utils import float_is_zero, float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _default_employee(self):
        emp_ids = self.sudo().env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')
    operation_code = fields.Selection(related='picking_type_id.code')
    is_return = fields.Boolean()
    returnable = fields.Boolean('Returnable')
    non_returnable = fields.Boolean('Non Returnable')
    verify_stock = fields.Boolean('stock Verify')
    return_type = fields.Selection([
        ('returnable', 'Returnable to Supplier'),
        ('non_returnable', 'Non Returnable'),
        ('re_returnable', 'Returnable from Supplier')
    ], copy=False, string="Return Type", default='non_returnable')
    material_shipment = fields.Boolean('Is Shipment', copy=False)
    remarks = fields.Text(string='Remarks')
    purpose = fields.Text(string='Purpose')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    delivery_issue_person = fields.Many2one('hr.employee', string='Issue P')
    delivery_sender = fields.Many2one('hr.employee', string='Delivery Raised By', default=_default_employee,
                                      readonly=True,
                                      help="Responsible person for the Direct Delivery Request")
    delivery_receiver = fields.Many2one('hr.employee', string='Request Raised For',
                                        help="Delivery Receiver of the Stock", )
    direct_delivery_type = fields.Selection([
        ('internal', 'Internal Delivery'),
        ('external', 'External Delivery'),
    ], copy=False, string="Delivery Type", default='internal')
    direct_delivery = fields.Boolean(string='Direct Delivery', default=False, compute='_enable_direct_delivery')
    collected_by = fields.Text(string='Collected By')
    received_date = fields.Datetime(string='Received Date')
    direct_delivery = fields.Boolean(string='Direct Delivery', default=False, compute='_enable_direct_delivery')
    direct_picking_type_id = fields.Many2one('stock.picking.type', 'Direct Delivery Picking Type',
                                             help="This will determine picking type of incoming shipment")
    direct_delivery_indent_count = fields.Integer(compute='_compute_direct_delivery_indent',
                                                  string='Picking',
                                                  default=0)

    def _compute_direct_delivery_indent(self):
        self.direct_delivery_indent_count = self.env['direct.delivery.indent'].sudo().search_count(
            [('origin', '=', self.name)])

    def direct_delivery_indent_view(self):
        self.sudo().ensure_one()
        context = dict(self._context or {})
        active_model = context.get('active_model')
        form_view = self.sudo().env.ref('material_requisition.view_direct_delivery_indent_form')
        tree_view = self.sudo().env.ref('material_requisition.view_direct_delivery_tree')
        return {
            'name': _('Direct Delivery Indent'),
            'res_model': 'direct.delivery.indent',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('origin', '=', self.name)],
        }

    def get_service_order_line_items(self):
        line_vals = []
        for line in self.move_ids_without_package:
            if line:
                vals = [0, 0, {
                    'product_id': line.product_id.id,
                    'product_required_qty': line.product_uom_qty,
                    'qty_shipped': line.quantity_done,
                    'product_uom': line.product_uom.id,
                    'product_available': line.product_id.qty_available,
                }]
                line_vals.append(vals)
        return line_vals

    def create_direct_delivery_indent(self):
        for pick in self:
            contract = pick.sudo().env['direct.delivery.indent'].sudo().create({
                'purpose': pick.purpose,
                'delivery_responsible': pick.env.uid,
                'picking_type_id': pick.direct_picking_type_id.id,
                'origin': pick.name,
                'state': 'draft',
                'delivery_product_lines': pick.get_service_order_line_items(),
            })
            return contract

    @api.depends('picking_type_id', 'direct_delivery')
    @api.onchange('picking_type_id', 'direct_delivery')
    def _enable_direct_delivery(self):
        if self.picking_type_id.name == 'Direct Delivery':
            self.write({'direct_delivery': True})
        else:
            self.write({'direct_delivery': False})

    @api.onchange("direct_delivery")
    def on_change_location_dest_id(self):
        self.location_dest_id = False
        res = {}
        if self.direct_delivery:
            res = {'domain': {'location_dest_id': [('usage', '=', 'Internal Location')]}}
        elif not self.direct_delivery:
            res = {'domain': {'location_dest_id': [('usage', '!=', 'Internal Location')]}}
        else:
            res = {'domain': {'partner_id': [(0, '=', 0)]}}
        return res

    def _compute_invoice_count(self):
        """This compute function used to count the number of invoice for the picking"""
        for picking_id in self:
            move_ids = picking_id.env['account.move'].search([('invoice_origin', '=', picking_id.name)])
            if move_ids:
                self.invoice_count = len(move_ids)
            else:
                self.invoice_count = 0

    def create_invoice(self):
        """This is the function for creating customer invoice
        from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'outgoing':
                customer_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.customer_journal_id') or False
                if not customer_journal_id:
                    raise UserError(_("Please configure the journal from settings"))
                invoice_line_list = []
                for move_ids_without_package in picking_id.move_ids_without_package:
                    vals = (0, 0, {
                        'name': move_ids_without_package.description_picking,
                        'product_id': move_ids_without_package.product_id.id,
                        'price_unit': move_ids_without_package.product_id.lst_price,
                        'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
                        else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
                        'tax_ids': [(6, 0, [picking_id.company_id.account_sale_tax_id.id])],
                        'quantity': move_ids_without_package.quantity_done,
                        # 'quantity': move_ids_without_package.qty_done,
                    })
                    picking_id.create_qty()
                    invoice_line_list.append(vals)
                invoice = picking_id.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'invoice_origin': picking_id.name,
                    'invoice_user_id': current_user,
                    'narration': picking_id.name,
                    'l10n_in_gst_treatment': 'unregistered',
                    'partner_id': picking_id.partner_id.id,
                    'currency_id': picking_id.env.user.company_id.currency_id.id,
                    'journal_id': int(customer_journal_id),
                    'payment_reference': picking_id.name,
                    'picking_id': picking_id.id,
                    'invoice_line_ids': invoice_line_list
                })
                # self.create_qty_material()
                # print("material requisiton qty updation///////////////////////////////////////////////")
                return invoice

    def button_verify(self):
        if self.move_line_nosuggest_ids.qty_done > self.move_line_nosuggest_ids.product_uom_qty:
            raise UserError(_('Alert!, The %s Done Quantity should be equal or less than Demand Quantity. \n '
                              'Please Check it.') % self.name)
        else:
            self.write({'verify_stock': True})

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)
        # Sanity checks.
        pickings_without_moves = self.browse()
        pickings_without_quantities = self.browse()
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        for picking in self:
            if not picking.move_lines and not picking.move_line_ids:
                pickings_without_moves |= picking

            picking.message_subscribe([self.env.user.partner_id.id])
            picking_type = picking.picking_type_id
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            no_quantities_done = all(
                float_is_zero(move_line.qty_done, precision_digits=precision_digits) for move_line in
                picking.move_line_ids.filtered(lambda m: m.state not in ('done', 'cancel')))
            no_reserved_quantities = all(
                float_is_zero(move_line.product_qty, precision_rounding=move_line.product_uom_id.rounding) for move_line
                in picking.move_line_ids)
            if no_reserved_quantities and no_quantities_done:
                pickings_without_quantities |= picking

            if picking_type.use_create_lots or picking_type.use_existing_lots:
                lines_to_check = picking.move_line_ids
                if not no_quantities_done:
                    lines_to_check = lines_to_check.filtered(
                        lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))
                for line in lines_to_check:
                    product = line.product_id
                    if product and product.tracking != 'none':
                        if not line.lot_name and not line.lot_id:
                            pickings_without_lots |= picking
                            products_without_lots |= product

        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(_('Please add some items to move.'))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                raise UserError(_('You need to supply a Lot/Serial number for products %s.') % ', '.join(
                    products_without_lots.mapped('display_name')))
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.') % ', '.join(
                    pickings_without_moves.mapped('name'))
            if pickings_without_quantities:
                message += _(
                    '\n\nTransfers %s: You cannot validate these transfers if no quantities are reserved nor done. To '
                    'force these transfers, switch in edit more and encode the done quantities.') % ', '.join(
                    pickings_without_quantities.mapped('name'))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.') % (
                    ', '.join(pickings_without_lots.mapped('name')),
                    ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res
        # Call `_action_done`.
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder = self.browse(self.env.context['picking_ids_not_to_backorder'])
            pickings_to_backorder = self - pickings_not_to_backorder
        else:
            pickings_not_to_backorder = self.env['stock.picking']
            pickings_to_backorder = self
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

        if self.user_has_groups('stock.group_reception_report') \
                and self.user_has_groups('stock.group_auto_reception_report') \
                and self.filtered(lambda p: p.picking_type_id.code != 'outgoing'):
            lines = self.move_lines.filtered(lambda
                                                 m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
            if lines:
                # don't show reception report if all already assigned/nothing to assign
                wh_location_ids = self.env['stock.location']._search(
                    [('id', 'child_of', self.picking_type_id.warehouse_id.view_location_id.id),
                     ('usage', '!=', 'supplier')])
                if self.env['stock.move'].search([
                    ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                    ('product_qty', '>', 0),
                    ('location_id', 'in', wh_location_ids),
                    ('move_orig_ids', '=', False),
                    ('picking_id', 'not in', self.ids),
                    ('product_id', 'in', lines.product_id.ids)], limit=1):
                    action = self.action_view_reception_report()
                    action['context'] = {'default_picking_ids': self.ids}
                    return action
        # self.create_material_shipped()
        self.create_qty_material()
        return True

    def create_qty(self):
        sale_sr = self.env['sale.order'].search([('name', '=', self.origin)])
        del_obj = self.env['stock.picking'].search([('origin', '=', self.origin), ('state', '=', 'done')])
        added_qty = 0.0
        for line in sale_sr.order_line:
            added_qty = 0.0
            for val in del_obj:
                for qty in val.move_ids_without_package:
                    if qty.product_id.id == line.product_id.id:
                        added_qty += qty.quantity_done
                        product_id = qty.product_id
            if product_id.id == line.product_id.id:
                line.update({
                    'qty_invoiced': added_qty,
                })
        return True

    def create_shipped(self):
        sale_sr = self.env['sale.order'].search([('name', '=', self.name)])
        stock_pic = self.env['stock.picking'].search([('origin', '=', self.origin)])
        for num in stock_pic:
            for line in sale_sr.order_line:
                if num.state == 'done':
                    sale_sr.update({
                        # 'shipped': True,
                        'state': 'done'
                    })
                else:
                    sale_sr.update({
                        # 'shipped': False,
                    })
            return True

    def create_qty_pur(self):
        purchase_sr = self.env['purchase.order'].search([('name', '=', self.origin)])
        stock_pic = self.env['stock.picking'].search([('origin', '=', self.origin)])
        for num in stock_pic:
            for line in purchase_sr.order_line:
                if num.state == 'done':
                    purchase_sr.update({
                        'state': 'done'
                    })
            added_qty = 0.0
            for line in purchase_sr.order_line:
                added_qty = 0.0
                for val in stock_pic:
                    for qty in val.move_ids_without_package:
                        if qty.product_id.id == line.product_id.ids:
                            added_qty += qty.quantity_done
                            product_id = qty.product_id
                if stock_pic.product_id.ids == line.product_id.ids:
                    line.update({
                        'qty_invoiced': added_qty,
                    })
            return True

    def create_qty_material(self):
        material_requisition_sr = self.env['material.requisition.indent'].search([('name', '=', self.origin)])
        stock_pic = self.env['stock.picking'].search([('origin', '=', self.origin)])
        for num in stock_pic:
            for line in material_requisition_sr.product_lines:
                if num.state == 'done':
                    material_requisition_sr.update({
                        'state': 'done',
                        'stock_transferred': True,
                        'issued_date': num.write_date,
                        'inward_date': num.scheduled_date,
                        'store_incharge': self.env.user.name,
                    })
            added_qty = 0.0
            for line in material_requisition_sr.product_lines:
                added_qty = 0.0
                for val in stock_pic:
                    for qty in val.move_ids_without_package:
                        if qty.product_id.id == line.product_id.ids:
                            added_qty += qty.quantity_done
                            product_id = qty.product_id
                if stock_pic.product_id.ids == line.product_id.ids:
                    line.update({
                        'qty_shipped': added_qty,
                    })
            return True

    def create_bill(self):
        """This is the function for creating vendor bill
                from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'incoming':
                vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.vendor_journal_id') or False
                if not vendor_journal_id:
                    raise UserError(_("Please configure the journal from the settings."))
                invoice_line_list = []
                for move_ids_without_package in picking_id.move_ids_without_package:
                    vals = (0, 0, {
                        'name': move_ids_without_package.description_picking,
                        'product_id': move_ids_without_package.product_id.id,
                        # 'price_unit': move_ids_without_package.product_id.lst_price,
                        'price_unit': move_ids_without_package.price_unit,
                        'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
                        else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
                        'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
                        'quantity': move_ids_without_package.quantity_done,
                        # 'quantity': move_ids_without_package.qty_done,
                    })
                    picking_id.create_qty_pur()
                    invoice_line_list.append(vals)
                invoice = picking_id.env['account.move'].create({
                    'move_type': 'in_invoice',
                    'invoice_origin': picking_id.name,
                    'invoice_user_id': current_user,
                    'l10n_in_gst_treatment': 'unregistered',
                    'narration': picking_id.name,
                    'partner_id': picking_id.partner_id.id,
                    'currency_id': picking_id.env.user.company_id.currency_id.id,
                    'journal_id': int(vendor_journal_id),
                    'payment_reference': picking_id.name,
                    'picking_id': picking_id.id,
                    'invoice_line_ids': invoice_line_list
                })
                return invoice

    def create_customer_credit(self):
        """This is the function for creating customer credit note
                from the picking"""
        for picking_id in self:
            current_user = picking_id.env.uid
            if picking_id.picking_type_id.code == 'incoming':
                customer_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.customer_journal_id') or False
                if not customer_journal_id:
                    raise UserError(_("Please configure the journal from settings"))
                invoice_line_list = []
                for move_ids_without_package in picking_id.move_ids_without_package:
                    vals = (0, 0, {
                        'name': move_ids_without_package.description_picking,
                        'product_id': move_ids_without_package.product_id.id,
                        # 'price_unit': move_ids_without_package.product_id.lst_price,
                        'price_unit': move_ids_without_package.price_unit,
                        'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
                        else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
                        'tax_ids': [(6, 0, [picking_id.company_id.account_sale_tax_id.id])],
                        'quantity': move_ids_without_package.quantity_done,
                        # 'quantity': move_ids_without_package.qty_done,
                    })
                    invoice_line_list.append(vals)
                    invoice = picking_id.env['account.move'].create({
                        'move_type': 'out_refund',
                        'invoice_origin': picking_id.name,
                        'invoice_user_id': current_user,
                        'l10n_in_gst_treatment': 'unregistered',
                        'narration': picking_id.name,
                        'partner_id': picking_id.partner_id.id,
                        'currency_id': picking_id.env.user.company_id.currency_id.id,
                        'journal_id': int(customer_journal_id),
                        'payment_reference': picking_id.name,
                        'picking_id': picking_id.id,
                        'invoice_line_ids': invoice_line_list
                    })
                    return invoice

    def create_vendor_credit(self):
        """This is the function for creating refund
                from the picking"""
        for picking_id in self:
            current_user = self.env.uid
            if picking_id.picking_type_id.code == 'outgoing':
                vendor_journal_id = picking_id.env['ir.config_parameter'].sudo().get_param(
                    'stock_move_invoice.vendor_journal_id') or False
                if not vendor_journal_id:
                    raise UserError(_("Please configure the journal from the settings."))
                invoice_line_list = []
                for move_ids_without_package in picking_id.move_ids_without_package:
                    vals = (0, 0, {
                        'name': move_ids_without_package.description_picking,
                        'product_id': move_ids_without_package.product_id.id,
                        # 'price_unit': move_ids_without_package.product_id.lst_price,
                        'price_unit': move_ids_without_package.price_unit,
                        'account_id': move_ids_without_package.product_id.property_account_income_id.id if move_ids_without_package.product_id.property_account_income_id
                        else move_ids_without_package.product_id.categ_id.property_account_income_categ_id.id,
                        'tax_ids': [(6, 0, [picking_id.company_id.account_purchase_tax_id.id])],
                        'quantity': move_ids_without_package.quantity_done,
                        # 'quantity': move_ids_without_package.qty_done,
                    })
                    invoice_line_list.append(vals)
                    invoice = picking_id.env['account.move'].create({
                        'move_type': 'in_refund',
                        'invoice_origin': picking_id.name,
                        'invoice_user_id': current_user,
                        'l10n_in_gst_treatment': 'unregistered',
                        'narration': picking_id.name,
                        'partner_id': picking_id.partner_id.id,
                        'currency_id': picking_id.env.user.company_id.currency_id.id,
                        'journal_id': int(vendor_journal_id),
                        'payment_reference': picking_id.name,
                        'picking_id': picking_id.id,
                        'invoice_line_ids': invoice_line_list
                    })
                    return invoice

    def action_open_picking_invoice(self):
        """This is the function of the smart button which redirect to the
        invoice related to the current picking"""
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('invoice_origin', '=', self.name)],
            'context': {'create': False},
            'target': 'current'
        }


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.onchange('move_line_nosuggest_ids.qty_done')
    def validation_quantity(self):
        if self.move_line_nosuggest_ids.qty_done:
            pass


class StockReturnInvoicePicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        """in this function the picking is marked as return"""
        new_picking, pick_type_id = super(StockReturnInvoicePicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        picking.write({'is_return': True})
        return new_picking, pick_type_id
