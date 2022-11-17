# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, api

class analyze_quotation_report(models.AbstractModel):
    _name = 'report.sh_po_tender_management.report_analyze_quotations'
    _description = "analyze quotations report abstract model"  

    @api.model
    def _get_report_values(self, docids, data=None):
        quotation_obj = self.env["purchase.order"]
        partner_quote_dic={}
        report_model = self.env['ir.actions.report']._get_report_from_name('sh_po_tender_management.report_analyze_quotations')
        tender_obj = self.env['purchase.agreement'].browse(docids)
        partners = self.env['res.partner'].sudo().search([])
        for partner in partners:
            partner_list = []
            domain = [
                    ("partner_id", "=", partner.id),
                    ("state", "in", ['draft']),
                    ('agreement_id','=',tender_obj.id)
                    ]
            search_quotations = quotation_obj.search(domain)
            if search_quotations:
                
                for quotation in search_quotations:
                    if quotation.partner_id.id not in partner_list:
                        partner_list.append(quotation.partner_id.id)
                        
            search_partner = self.env['res.partner'].search([
                                        ('id', 'in', partner_list)
                                        ], limit=1)
            
            if search_partner:
                partner_quote_dic.update({search_partner.id : {"orders": search_quotations, "partner_name": search_partner.name}})
        return {
            'docs':tender_obj,
            'doc_model':report_model.model,
            'partner_quote_dic':partner_quote_dic
            }