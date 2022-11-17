from odoo import api, fields, models


class Equip(models.TransientModel):
    _name = 'date.wizard'
    _description = 'Date Wizard'

    assign_date = fields.Date(string="Start Date", required=True)
    date_end = fields.Date(string="End Date", required=True)

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'date_start': self.assign_date,
                'date_end': self.date_end,
            },
        }

        return self.env.ref('maintenance_extended.equipment_management_report').report_action(self, data=data)
