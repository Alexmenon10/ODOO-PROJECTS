from odoo.exceptions import UserError
from odoo import api, fields, models, _
from num2words import num2words
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from functools import partial

class purchaseorderline(models.Model):
	_inherit = 'purchase.order'




class Stockpicking(models.Model):
	_inherit = 'stock.picking'

	def amt_in_words_grn(self, poamount):
		amount1=str(poamount)
		amt= amount1.split(".")
		print(amt[1],amt[0],poamount)
		if int(amt[1]) > 0:
			second_part = ' and '+ num2words(int(amt[1]), lang='en_IN') + ' Paise only '
			print(amt[1],'*****************************************************************')
		else:
			second_part = ' Only '

		return ' Rupees ' + num2words(int(amt[0]), lang='en_IN') + second_part

	def return_taxes(self):
		for picking in self:
			currency = picking.purchase_id or picking.company_id
			fmt = partial(formatLang, self.with_context(lang=picking.partner_id.lang).env, currency_obj=currency)
			res = []
			for line in picking.move_ids_without_package:
				price_reduce = line.purchase_line_id.price_after_discount * (1.0 - line.purchase_line_id.discount / 100.0)
				taxes = line.purchase_line_id.taxes_id.compute_all(price_reduce, quantity=line.quantity_done, product=line.product_id)['taxes']
				print(taxes,'********************\n')
				for each in taxes:
					res.append(each)
				
			# res = sorted(res.items(), key=lambda l: l[0].sequence)
			print(res,'********************************')
			# amount_by_group = [(
   #              l[0].name, l[1]['amount'], l[1]['base'],
   #              fmt(l[1]['amount']), fmt(l[1]['base']),
   #              len(res),
   #          ) for l in res]
			return res

	def get_taxes(self):

		# gst_lit= []
		tax_name =[]
		for line in self.move_ids_without_package:
			for each_line in line.purchase_line_id.taxes_id:
				if each_line:
					# if each_line.tax_group_id:
					tax_name.append(each_line)
		tax_name = list(set(tax_name))


		taxes = []
		for each_line in self.move_ids_without_package:
		    if each_line.product_id:
		        # pdb.set_trace()
		        curr_val = each_line.purchase_line_id.price_after_discount * each_line.quantity_done
		        tot_rax_rate =0.0
		        igst_val =0.0

		        sgst_rate =0.0
		        sgst_val = 0.0

		        cgst_rate = 0.0
		        cgst_val =0.0

		        tcs_rate =0.0
		        tcs_val =0.0
		        group =''
		        # cgst_val = 0.0
		        for each_tax in each_line.tax_id:
		        	if each_tax.amount_type == 'group':
		        		if each_tax.tax_group_id.name == 'GST':
			        		for each_group_line in  each_tax.children_tax_ids:
			        			group = each_tax.tax_group_id.name
			        			if each_group_line.tax_group_id.name == 'SGST' or each_group_line.tax_group_id.name == 'CGST' :
			        				tot_rax_rate +=each_group_line.amount
			        				sgst_val =curr_val * (each_group_line.amount/100)
			        			elif each_group_line.tax_group_id.name == 'TCS':
			        				tcs_rate = each_group_line.amount
			        				tcs_val = (curr_val+sgst_val*2) * (each_group_line.amount/100)

        				elif each_tax.tax_group_id.name == 'IGST':
	        				for each_group_line in  each_tax.children_tax_ids:
	        					group = each_tax.tax_group_id.name
	        					if each_group_line.tax_group_id.name != 'TCS':
	        						tot_rax_rate  += each_tax.amount
	        						igst_val =curr_val * (each_tax.amount/100)
	        					elif each_group_line.tax_group_id.name == 'TCS':
	        						tcs_rate = each_group_line.amount
	        						tcs_val = (curr_val+igst_val) * (each_group_line.amount/100)
        			else:
        				group = each_tax.tax_group_id.name
        				tot_rax_rate +=each_tax.amount
        				igst_val =curr_val * (each_tax.amount/100)

		        taxes.append({'tax':each_line.tax_id,'tax_rate':tot_rax_rate,'igst':igst_val,'sgst':sgst_val,'tcs':tcs_val,'tcs_rate':tcs_rate, 'tax_group':group})


		sorted_tax =[]
		for each_tax_id in tax_name:
			tot_rax_rate =0.0
			igst_val =0.0
			sgst_val =0.0
			tcs_val =0.0
			tcs_rate =0.0
			group =''

			for each_rec in taxes:
				if each_tax_id.id == each_rec['tax'].id:
					tot_rax_rate = each_rec['tax_rate']
					tcs_rate = each_rec['tcs_rate']
					igst_val+=each_rec['igst']
					sgst_val+=each_rec['sgst']
					tcs_val+=each_rec['tcs']
					group=each_rec['tax_group']
				else:
					# tot_rax_rate = each_rec['tax_rate']
					# igst_val = each_rec['igst']
					# sgst_val = each_rec['sgst']
					# tcs_val = each_rec['tcs']
					# group = each_rec['tax_group']
					continue

			sorted_tax.append({'tax':each_tax_id,'tax_rate':tot_rax_rate,'igst':igst_val,'sgst':sgst_val,'tcs':tcs_val,'tcs_rate':tcs_rate,'tax_group':group})

		return sorted_tax


	


	







 
		
 







