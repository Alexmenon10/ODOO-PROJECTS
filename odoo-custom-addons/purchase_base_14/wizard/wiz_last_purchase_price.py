from datetime import datetime

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError, AccessError
import pdb



class prevurchaselinewiz(models.TransientModel):
    _name = "purchaseline.prev"
    _order = 'date desc'
    _description = 'Purchaseline'
    
    wiz_id = fields.Many2one('purchaseline.wizard')
    po_order = fields.Many2one('purchase.order',string="Purchase Order")
    unit_price = fields.Float(string="Unit Price")
    vendor = fields.Many2one('res.partner',string="Vendor")
    quantity = fields.Float(string="Quantity")
    po_date =fields.Datetime(string="Purchase Date")
    
    
class PurchaseOrderlinewiz(models.TransientModel):
    _name = "purchaseline.wizard"
    _description = 'Purchaseline Wizard'
        
    @api.model
    def _get_purchase_lines(self):
        lines = self.env['purchase.order.line']
        PurchaseOrderLines = lines.browse(self._context.get('active_ids'))[0]
        product_id=PurchaseOrderLines.product_id.id
        PurchaseHistoryLines=lines.search([('product_id','=',product_id)])
        vals = []
        for line in PurchaseHistoryLines:
            purchase_id=line.order_id
            if purchase_id.state in ['purchase','done']:
                po_order_id=line.order_id.id
                vendor=purchase_id.partner_id.id
                quantity=line.product_qty
                date=line.date_order
                price_unit=line.price_unit
                vals.append((0, 0, {'po_order':po_order_id,
                                    'unit_price':price_unit,
                                    'vendor':vendor,
                                    'quantity':quantity,
                                    'po_date':date,
                                    }))
        return vals
    
    purchase_lines=fields.One2many('purchaseline.prev','wiz_id',string="Purchases" ,default=_get_purchase_lines)
    
    




class Requisitionremarks(models.TransientModel):
    _name = 'requisition.approval.remarks'
    _description = 'requisition.approval.remarks'

    remarks = fields.Char( string='Remaks', required=True)
    
   

    def reject_order(self):
        active_id =self.env.context['active_id']
        
        current_id=self.env['purchase.requisition.line'].search([('id','=',active_id)])
        # for new_id in  current_id.requisition_id:
        approval_ids = self.env['requisition.approval'].search([('warehouse_id','=',current_id.requisition_id.picking_type_id.warehouse_id.id),('document_type_id','=',current_id.requisition_id.request_type_id.id)])
        if approval_ids:
            for each in approval_ids.approval_lines:
                if self.env.user.id in each.user_ids.ids:
                    if each.approval_one:
                        user_approve = 1
                    elif each.approval_two:
                        user_approve = 2
                    elif each.approval_three:
                        user_approve = 3
                    approval_level =int(each.requisition_id.approval_method)
                    if user_approve == 1:
                        if user_approve == 1 and not current_id.approval_one :
                            current_id.approval_one = '2'
                            msg = """
                            <div style="color:red;">%s-%s</div>
                            """ %(current_id.product_id.name, self.remarks)
                            current_id.requisition_id.message_post(body=msg)
                        else:
                            raise UserError (_("Oops!!!! You can't  Reject !!! This Product is approved/Rejected"))

                    elif user_approve == 2:
                        if not current_id.approval_one in ['1','2']:
                            raise UserError (_("Oops!!!! You can't  Reject "))
                        else:
                            if user_approve == 2 and not current_id.approval_two:
                                current_id.approval_two ='2'
                                msg = """
                                <div style="color:red;">%s-%s</div>
                                """ %(current_id.product_id.name,self.remarks)
                                current_id.requisition_id.message_post(body=msg)
                            else:
                                raise UserError (_("Oops!!!! You can't  Reject !!! This Product is approved/Rejected"))

                    elif user_approve == 3:
                        if not current_id.approval_two in ['1','2']:
                            raise UserError (_("Oops!!!! You can't Reject"))
                        else:
                            if user_approve == 3 and not current_id.approval_three:
                                current_id.approval_three ='2'
                                msg = """
                                <div style=color:red;">%s-%s</div>
                                """ %(current_id.product_id.name,self.remarks)
                                current_id.requisition_id.message_post(body=msg)
                            else:
                                raise UserError (_("Oops!!!! You can't  Reject !!! This Product is approved/Rejected"))
        else:
            raise UserError (_("Oops!!!! You can't approve the order Create "))

