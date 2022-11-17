#-*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class UserLogin(models.TransientModel):
    """
        Created this as a Transient model as we don't need to save this information anywhere,
        username and password are common fields that are declared here to grant the access to the
        user [ provided he has been registered by the admin ( class declared below)].
        Login function is triggred when the `Login` button is clicked and it has parameters saying
        which model has to used to render the page. Username is also passed in the context so that
        we will be knowing who was there at that point.
    """
    _name = "gate.user.login"
    _description = "gate_user_login"
    _rec_name = 'username'

    username = fields.Char(string='Username')
    password  = fields.Char(string='Password')
    
    def login(self):
        u_name = self.env['gate.user.registration'].search([('username', '=', self.username)])
        if u_name['username'] == self.username and u_name['password'] == self.password:
            return {
                'name': ('gate_entry_login_form_view_valid'),
                'view_mode': 'form',
                'res_model': 'gate.user.login_display',
                'type': 'ir.actions.act_window',
                'target':'inline',
                'context':{ 'default_username': u_name.id,
                            'default_warehouse_id':u_name.warehouse_id.id, },
            }
        else:
            raise ValidationError("Incorrect username or password!!")   

class UserRegistration(models.Model):
    """
        Class used to register the users at the gate, 
        `username` and `password` are used to register the user and also _sql_constraints 
        are added to avoid the duplicate values [ say avoid users with same username ].
        Also _rec_name is given to display the username of the registered person[ It is displayed in the breadcrumbs at top].
    """
    _name = "gate.user.registration"
    _description = "gate_user_registration"
    _rec_name = 'username'

    username= fields.Char(string='Username')
    password  = fields.Char(string='Password')
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(username)',
         "Username already exists"),
    ]

class LoginDisplay(models.TransientModel):
    """
        Model created to show the buttons at the gate entry to select either Inward or Outward
        hence the two variables and they are made as 'function' because they inturn have to be
        connected to the created model gate_entry where all the logic has been written.
        A field usename has been declared to hold the value coming in the context from the 
        above function `UserLogin`s Login function and furthur passed on to gate.entry model. 
    """
    _name="gate.user.login_display"
    _description="gate_user_login_display"
    _rec_name = 'Gate_Entry'

    Gate_Entry = fields.Char(default="Gate Entry Type")
    username = fields.Integer()
    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse')

    def Inward(self):
        return {
            'name': ('Inward'),
            'view_mode': 'tree,form',
            'res_model': 'gate.entry',
            'type': 'ir.actions.act_window',
            'domain':[('entry_type','=','in'),('username','=',self.username)],
            'context':{'default_entry_type': 'in', 'default_username': self.username,'default_warehouse_id':self.warehouse_id.id,},
        }

    def Outward(self):
        return {
            'name': ('Outward'),
            'view_mode': 'tree,form',
            'res_model': 'gate.entry',
            'type': 'ir.actions.act_window',
            'domain':[('entry_type','=','out'),('username','=',self.username)],
            'context':{'default_entry_type': 'out', 'default_username': self.username,'default_warehouse_id':self.warehouse_id.id,},
        }