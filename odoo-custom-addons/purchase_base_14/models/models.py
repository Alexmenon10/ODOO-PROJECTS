# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

class PurchaseDocType(models.Model):
    _name = 'purchase.doc.type'
    _description = 'Purchase Order Document Type'

    name = fields.Char()
    description = fields.Char()
    sequence_id = fields.Many2one('ir.sequence')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    revision_count = fields.Integer(default=0,copy=False)
    origin_order_id = fields.Many2one('purchase.order',copy=False)
    revision_order_ids = fields.One2many('purchase.order', 'origin_order_id')
    doc_type_id = fields.Many2one('purchase.doc.type', string="Document Type", ondelete="restrict")
    quotation_number = fields.Char(copy=False)
    state = fields.Selection(selection_add=[('revn','Revision')])

    def button_confirm(self):
        for rec in self:
            if not rec.doc_type_id:
                raise ValidationError(_("""Mapping Document type is required to confirm a Purchase Quotation"""))
            self.revision_count += 1
            rec.quotation_number = rec.name
            rec.copy({
                'name': rec.name,
                'origin_order_id': rec.id
                })
            rec.name = self.env['ir.sequence'].next_by_code(rec.doc_type_id.sequence_id.code)
        return super(PurchaseOrder, self).button_confirm()

    def unlink(self):
        for rec in self:
            if rec.origin_order_id:
                raise ValidationError(_("""Can not delete Purchase Order Revision"""))
        return super(PurchaseOrder, self).unlink()

    def restore_revision(self):
        if self.origin_order_id.state != 'draft':
            raise ValidationError(_("""Can only restore to a draft Quotation"""))
        old_origin = self.origin_order_id
        self.origin_order_id.create_revisions()
        new_origin = self.copy({
            'name':self.origin_order_id.name,
            'revision_count':self.origin_order_id.revision_count,
            'revision_order_ids':[(6, 0, self.origin_order_id.revision_order_ids.ids)]
        })
        old_origin.button_cancel()
        old_origin.unlink()
        return {
            'name': new_origin.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': new_origin.id
        }
    
    def create_revisions(self):
        for rec in self:
            if rec.origin_order_id:
                raise ValidationError(_("""Can not revise Revisions"""))
            if rec.state in ("purchase","done","cancel"):
                raise ValidationError(_("""Only draft Quotations can be revised"""))
            rec.revision_count += 1
            rec.copy({
                'state': 'revn',
                'name': "{}-{}".format(rec.name,rec.revision_count),
                'origin_order_id': rec.id
                })
    
    def view_previous_versions(self):
        return {
            'name': 'Quotation/Revisions',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('origin_order_id', '=', self.id)],
            'context': dict(self._context, create=False, edit=False)
        }
    
    def action_create_invoice(self):
        for order in self:
            if order.origin_order_id:
                raise ValidationError(_("""Can not create a bill of a Revision"""))
        return super(PurchaseOrder, self).action_create_invoice()
    
    def _send_reminder_mail(self, send_single=False):
        for order in self:
            if order.origin_order_id:
                raise ValidationError(_("""Can not send reminder mail of a Revision"""))
        return super(PurchaseOrder, self)._send_reminder_mail(send_single)
    
    #def button_draft(self):
        #raise ValidationError(_("""Invalid Action"""))

# class SalePaymentLink(models.TransientModel):
#     _inherit = "payment.link.wizard"

#     @api.model
#     def default_get(self, fields):
#         res = super(SalePaymentLink, self).default_get(fields)
#         if res['res_id'] and res['res_model'] == 'sale.order':
#             record = self.env[res['res_model']].browse(res['res_id'])
#             if record.origin_order_id:
#                 raise ValidationError(_("""Can not Create Payment Link for a Revision"""))
#         return res

class PortalMixin(models.AbstractModel):
    _inherit = "portal.mixin"

    @api.model
    def action_share(self):
        # print('\n\n',self.env.context['active_id'],'\n',self.env.context['active_model'],'\n\n')
        if self.env.context['active_model'] == 'purchase.order':
            if self.env['purchase.order'].browse(self.env.context['active_id']).origin_order_id:
                raise ValidationError(_("""Can not Share a Revision"""))
        return super(PortalMixin, self).action_share()




# class SaleReport(models.Model):
#     _inherit = "sale.report"

#     item_group = fields.Many2one('item.group')
#     product_group_1 = fields.Many2one('product.group.1')
#     product_group_2 = fields.Many2one('product.group.2')
#     product_group_3 = fields.Many2one('product.group.3')

#     def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
#         fields['item_group'] = ",t.item_group as item_group"
#         fields['product_group_1'] = ",t.product_group_1 as product_group_1"
#         fields['product_group_2'] = ",t.product_group_2 as product_group_2"
#         fields['product_group_3'] = ",t.product_group_2 as product_group_3"

#         groupby += ', t.item_group'
#         groupby += ', t.product_group_1'
#         groupby += ', t.product_group_2'
#         groupby += ', t.product_group_3'

#         return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
