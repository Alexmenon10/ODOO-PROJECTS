from odoo import models, fields, api


class DateReport(models.AbstractModel):
    _name = 'report.maintenance_extended.maintenance_equipment_template'


    @api.model
    def _get_report_values(self, docids, data=None):
        print(data)
        start_date = data['form']['assign_date']
        end_date = data['form']['date_end']
        print(start_date)
        print(end_date)

        category_ids = self.env['maintenance_extended.maintenance.equipment'].search(
            [('assign_date', '>=', start_date), ('assign_date', '<=', end_date)])
        print(category_ids)
        # print("Docs", docs)
        return {
            'docs': docids,
            'category_ids': category_ids,
        }
