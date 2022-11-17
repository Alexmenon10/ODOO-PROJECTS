# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MergePaleOrder(models.TransientModel):
    _name = 'merge.purchase.order'
    _description = 'Merge Purchase Order'

    date_order = fields.Datetime(string='Date', required=True, default=datetime.datetime.now())
    merge_action = fields.Selection(selection=[
            ('remove', 'Remove Selected Orders'),
            ('cancel', 'Cancel Selected Orders'),
        ], string='Merge Action', required=True, default='cancel')

    @api.model
    def default_get(self, fields):
        active_ids = self._context.get('active_ids')
        partners = []
        payment_terms = []
        requisition_ids = []
        if active_ids:
            if len(active_ids) < 2:
                raise UserError(_('Please select at least two orders'))
            for active_id in active_ids:
                po_rec = self.env['purchase.order'].browse(active_id)
                if po_rec:
                    if po_rec.state != 'draft':
                        raise UserError(_("The Status must be Draft"))
                    if po_rec.partner_id.id not in partners:
                        partners.append(po_rec.partner_id.id)
                    if po_rec.requisition_id and po_rec.requisition_id.id not in requisition_ids:
                        requisition_ids.append(po_rec.requisition_id.id)
                    if po_rec.payment_term_id and po_rec.payment_term_id.id not in payment_terms:
                        payment_terms.append(po_rec.payment_term_id.id)
        if partners:
            if len(partners) > 1:
                raise UserError(_("The Vendor must be Same"))
        if requisition_ids:
            if len(requisition_ids) > 1:
                raise UserError(_("The Purchase Agreement must be Same"))
        
        if payment_terms:
            if len(payment_terms) > 1:
                raise UserError(_("The Payment-Terms must be Same"))
        return super(MergePaleOrder, self).default_get(fields)
        
    def create_merge_po(self):
        active_ids = self._context.get('active_ids')
        po_dict = {}
        po_line_list = []
        partner_ref = []
        payment_terms = []
        if active_ids:
            for active_id in active_ids:
                po_rec = self.env['purchase.order'].browse(active_id)
                po_dict.update({'partner_id':po_rec.partner_id.id,
                              'company_id':po_rec.company_id.id,
                              'currency_id':po_rec.currency_id.id,
                              'date_order':self.date_order,
                              'user_id':po_rec.user_id.id,
                              })
                if po_rec.payment_term_id and po_rec.payment_term_id.id not in payment_terms:
                    payment_terms.append(po_rec.payment_term_id.id)
                if po_rec.partner_ref and po_rec.partner_ref not in partner_ref:
                    partner_ref.append(po_rec.partner_ref)
                for line in po_rec.order_line:
                    po_line_list.append([0, 0, {
                                        'product_id': line.product_id.id,
                                        'name': line.name,
                                        'taxes_id': [(6, 0, line.taxes_id.ids)],
                                        'product_qty': line.product_uom_qty,
                                        'product_uom': line.product_uom.id,
                                        'price_unit': line.price_unit,
                                        'date_planned': line.date_planned,
                                        'account_analytic_id': line.account_analytic_id and line.account_analytic_id.id or False,
                                        'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                                    }])
        old_po_rec = self.env['purchase.order'].browse(active_ids)
        ###old record name
        old_po_name = False
        if old_po_rec:
            old_po_name = ','.join(old_po_rec.mapped('name'))
        if partner_ref:
            partner_ref_val = ','.join(partner_ref)
            po_dict.update({'partner_ref':partner_ref_val})
        if payment_terms:
            po_dict.update({'payment_term_id':payment_terms[0]})
        if po_line_list:
            po_dict.update({'order_line':po_line_list})
        new_po = self.env['purchase.order'].create(po_dict)
        if old_po_rec and self.merge_action == 'cancel':
            old_po_rec.button_cancel()
            new_po._message_log(body=_("This <b>%s</b> is created from '%s' and those had been cancelled based on user choice.") % (new_po.name,old_po_name))
        elif old_po_rec and self.merge_action == 'remove':
            old_po_rec.button_cancel()
            old_po_rec.unlink()
            new_po._message_log(body=_("This <b>%s</b> is created from '%s' and those had been removed based on user choice.") % (new_po.name,old_po_name))
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
