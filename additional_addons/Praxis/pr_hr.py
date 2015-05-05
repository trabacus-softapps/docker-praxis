# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

from openerp import SUPERUSER_ID
from openerp import tools
from openerp.modules.module import get_module_resource
from openerp.osv import fields, osv
from openerp.tools.translate import _
from lxml import etree
from openerp.osv.orm import setup_modifiers
import re

_logger = logging.getLogger(__name__)



class hr_employee(osv.osv):
    _inherit = "hr.employee"
    
    def name_get(self, cr, uid, ids, context=None):
        """ TO display the concatenated name (first and last name) """
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['name','last_name'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['last_name']:
                name = record['last_name']+' '+name
            res.append((record['id'], name))
        return res
    
    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        """ TO search name based on last or first name """
        
        ids = []
        if name:
            ids = self.search(cr, uid, [('name','ilike',name)]+ args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, uid, [('last_name','ilike',name)]+ args, limit=limit, context=context)
        result = self.name_get(cr, uid, ids, context=context)
        return result
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """
            Add Dynamic Labels based on the class Mappings
        """
        mapping_obj = self.pool.get('hr.class.mapping')
        if not context: context = {}
        res = super(hr_employee, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' :
            doc = etree.XML(res['arch'])
            for m in mapping_obj.browse(cr, uid, mapping_obj.search(cr, uid, [])):
                nodes = doc.xpath("//field[@name='"+m.name[0:5]+'_id'+m.name[5:]+"']")
                for node in nodes:
                    node.set('invisible', '0')
                    node.set('string', m.label)
                    setup_modifiers(node, res['fields'][m.name[0:5]+'_id'+m.name[5:]])
                     
            res['arch'] = etree.tostring(doc)
        return res
    
    def _display_name_compute(self, cr, uid, ids, name, args, context=None):
        return dict(self.name_get(cr, uid, ids, context=context))

    # indirections to avoid passing a copy of the overridable method when declaring the function field
    _display_name = lambda self, *args, **kwargs: self._display_name_compute(*args, **kwargs)
    
    def get_country(self, cr, uid, *args):
        """ To get the default country as India"""
        country_ids = self.pool.get('res.country').search(cr, uid, [('name','=','India'),('code','=','IN')])
        if country_ids:
            return country_ids[0]
        return False
            
        
    
    
    
    _columns = {
                'org_hire_date'     : fields.date('Original Hire Date'),
                'last_hire_date'    : fields.date('Last Hire Date'),
                'adj_sen_date'      : fields.date('Adjusted Seniority Date'),
                'job_start_date'    : fields.date('Job Start Date'),
                'badge'             : fields.char('Badge', size=16),
                'salutation_id'     : fields.many2one('hr.salutation','Salutation'),
                'ethnic_origin_id'  : fields.many2one('hr.ethnic.origin', 'Ethnic Origin'),
                'age'               : fields.integer('Age'),
                'disability'        : fields.boolean('Disability'),
                'smoker'            : fields.boolean('Smoker'),
                'exempt'            : fields.boolean('Excempt'),
                'salaried'          : fields.boolean('Salaried'),
                'job_desc_id'       : fields.many2one('hr.job.desc', 'Job Description'),
                'job_code_id'       : fields.many2one('hr.job.code','Job Code'),
                'employee_type_id'  : fields.many2one('hr.employee.type','Employee Type'),
                'exempt_status'     : fields.selection([('exempt','Exempt'),('non_exempt','Non-Exempt')], 'Exempt Status'), 
                
                
                #Overidden
                'ssnid'             : fields.char('Aadhar No', help='Aadhar Number', size=16),
                'passport_id'       : fields.char('Passport No', size=16),
                'identification_id' : fields.char('Employee Number', size=16),
                'parent_id'         : fields.many2one('hr.employee', 'Primary Supervisor'),
                'parent_ids'        : fields.many2many('hr.employee','hr_employee_supervisor_rel','employee_id','supervisor_id','Supervisors'),
                
                #mapping Details
                
                'class_id1'        : fields.many2one('hr.class1','Class1'),
                'class_id2'        : fields.many2one('hr.class2','Class2'),
                'class_id3'        : fields.many2one('hr.class3','Class3'),
                'class_id4'        : fields.many2one('hr.class4','Class4'),
                'class_id5'        : fields.many2one('hr.class5','Class5'),
                'class_id6'        : fields.many2one('hr.class6','Class6'),
                'class_id7'        : fields.many2one('hr.class7','Class7'),
                'class_id8'        : fields.many2one('hr.class8','Class8'),
                'class_id9'        : fields.many2one('hr.class9','Class9'),
                'class_id10'       : fields.many2one('hr.class10','Class10'),
                
                #Pay info
                'shift_id'         : fields.many2one('hr.shift','Default Shift'),
                'pay_date'         : fields.date('Pay Effective Date'),
                'pay_frequency'    : fields.selection([('bi_weekly','Bi-Weekly'),('custom','Custom'),('monthly','Monthly'),
                                                       ('semi_monthly','Semi-Monthly'),('weekly','Weekly')], 'Pay Frequency'),
                'days_payable'      : fields.float('Days Payable'),
                'unit_pay_rate'    : fields.float('Unit Pay Rate'),
                'pay_period_sal'   : fields.float('Pay Period Salary'),
                'monthly_pay'      : fields.float('Monthly Pay'),
                'annual_pay'       : fields.float('Annual Pay'),
                'pay_group_id'     : fields.many2one('hr.pay.group','Pay Group'),
                
                'last_name'        : fields.char('Last Name', size = 30),
                'street'           : fields.char('Street'),
                'street2'          : fields.char('Street2'),
                'zip'              : fields.char('Zip', size=24, change_default=True),
                'city'             : fields.char('City'),
                'state_id'         : fields.many2one("res.country.state", 'State', ondelete='restrict'),
                'country_id'       : fields.many2one('res.country', 'Country', ondelete='restrict'),
                'email'            : fields.char('Email'),
                'phone'            : fields.char('Phone'),
                'mobile'           : fields.char('Mobile'),
                'display_name'     : fields.function(_display_name, type='char', string='Name', select=True),
                  
                }
    _defaults = {
                 'country_id'   : get_country,
                 }
    
    def onchange_payinfo(self, cr, uid, ids, f_get , unit_pay_rate, days_payable, monthly_pay, annual_pay):
        """ Pay Info Calculation""" 
        res = {}
       
        if f_get in ('days','rate'):
            res['monthly_pay'] = days_payable * (unit_pay_rate * 8) if (days_payable and unit_pay_rate) else monthly_pay
            res['annual_pay'] = res['monthly_pay'] * 12
            res['unit_pay_rate'] = (monthly_pay / (days_payable * 8))  if days_payable  else unit_pay_rate
            
            if not unit_pay_rate and not days_payable:
                 res['monthly_pay'] = 0.0
                 res['annual_pay'] = 0.0
            
        if f_get == 'monthly':
            res['unit_pay_rate'] = (monthly_pay / (days_payable * 8)) if (monthly_pay and days_payable) else unit_pay_rate 
            res['annual_pay'] = 12 * monthly_pay
        
        if f_get == 'annual':
            res['monthly_pay'] = annual_pay / 12 if annual_pay else  days_payable * (unit_pay_rate * 8)
            res['annual_pay'] = 12 * res['monthly_pay']
        return {'value':res }
            
    
    def onchange_state(self, cr, uid, ids, state_id):
        if state_id:
            state = self.pool.get('res.country.state').browse(cr, uid, state_id)
            return {'value': {'country_id': state.country_id.id}}
        return {}
    
    #to get age from date of birth
    def get_age(self, cr, birthday):
        cr.execute("SELECT EXTRACT(year from AGE(NOW(),'" + birthday + "')) as age")
        age = cr.fetchone()
        return age[0]

    def onchange_birthdate(self, cr, uid, ids, birthday, context=None):
        res = {}
        if birthday:
            res['age'] = self.get_age(cr, birthday)
        return {'value':res}
    
    
    
    def onchange_last_hire_date(self, cr, uid, ids, birthday, last_hire_date, context=None):
        res = {}
        warning = {}
        if last_hire_date and not birthday:
            res={'last_hire_date':False}
            return {'warning': {
                        'title'   : _('Warning!'),
                        'message' : _('Please enter the date of birth ')
                              }
                              ,
                    'value' : res
                    
                    }
        if birthday and last_hire_date:
            cr.execute("SELECT EXTRACT(year from AGE('"+ last_hire_date +"','" + birthday + "')) as age")
            age = cr.fetchone()
            if age and age[0] < 18:
                res.update({'last_hire_date':False})
                warning= {
                        'title'   : _('Warning!'),
                        'message' : _('Employee age should be 18 as on the Last Hire date')
                              }
        return {'value':res, 'warning': warning}
    
    
    
    def check_alphabet(self, cr, uid, ids, field, context=None):
        warning = {}
        if field:
            if re.match("^([a-zA-Z']{0,30})$",field) != None :
                return {}
            else:
                warning = {
                        'title': _('Warning!'),
                        'message': _("Invalid " + ('First Name' if context.get('field')=='name' else 'Last Name') +'\n'+   
                                      "  Please enter valid "+ ('First Name' if context.get('field')=='name' else 'Last Name'))
                    }
            return {'warning': warning, 'value':{context.get('field'):''}}
        
    
    def check_alpha_numeric(self, cr, uid, ids, field, context=None):
        warning = {}
        if field:
            if re.match("^([a-zA-Z0-9']{0,16})$",field) != None :
                return {}
            else:
               warning = {
                        'title': _('Warning!'),
                        'message': _("Invalid " + context.get('string','') +'\n'+   
                                      "  Please enter valid "+ context.get('string',''))
                    }
            return {'warning': warning, 'value':{context.get('field'):''}}
        
        
        
    def onchange_name(self, cr, uid, ids, name, last_name, context):
        res = {}
        context = dict(context or {})
        if name:
            context.update({'field':'name'})
            res = self.check_alphabet(cr, uid, ids, name, context)
        if last_name:
            context.update({'field':'last_name'})
            res = self.check_alphabet(cr, uid, ids, last_name, context)
        return res
    
    
    
    def onchange_emp_no(self, cr, uid, ids,identification_id, context):
        warning = {}
        res = {}
        context = dict(context or {})
        if identification_id:
             context.update({'field':'identification_id', 'string':'Employee Number'})
             res = self.check_alpha_numeric(cr, uid, ids, identification_id, context)
             emp_ids = self.search(cr, uid, [('identification_id','=',identification_id)])
             if emp_ids :
                 res.update({
                             'warning' : {
                                          'title'   : _('Warning!'),
                                          'message' : _('Employee Number  "'+identification_id + '"  already exists')
                                          }
                             })
                 res.update({
                                'value':{'identification_id':''}
                            })
        return res
    
    def onchange_badge(self, cr, uid, ids, badge, context):
        warning = {}
        res = {}
        context = dict(context or {})
        if badge:
             context.update({'field':'badge', 'string':'Badge Number'})
             res = self.check_alpha_numeric(cr, uid, ids, badge, context)
             emp_ids = self.search(cr, uid, [('badge','=',badge)])
             if emp_ids :
                 res.update({
                             'warning' : {
                                          'title'   : _('Warning!'),
                                          'message' : _('Employee Badge Number "'+ badge + '"  already exists')
                                          }
                             })
                 res.update({
                                'value':{'badge':''}
                            })
        return res
    
    def onchange_aadhar_no(self, cr, uid, ids, ssnid, context):
        warning = {}
        res = {}
        context = dict(context or {})
        if ssnid:
             context.update({'field':'ssnid', 'string':'Aadhar No'})
             res = self.check_alpha_numeric(cr, uid, ids, ssnid, context)
             emp_ids = self.search(cr, uid, [('ssnid','=',ssnid)])
             if emp_ids :
                 res.update({
                             'warning' : {
                                          'title'   : _('Warning!'),
                                          'message' : _('Aadhar Number "'+ssnid + '"  already exists')
                                          }
                             })
                 res.update({
                                'value':{'ssnid':''}
                            })
        return res
    
    def onchange_passport_no(self, cr, uid, ids, passport_id, context):
        res = {}
        context = dict(context or {})
        if passport_id:
             context.update({'field':'passport_id', 'string':'Passport No'})
             res = self.check_alpha_numeric(cr, uid, ids, passport_id, context)
        return res
    
        
    
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('birthday',False):
            vals.update({'age' : self.get_age(cr, vals.get('birthday'))})
        
        if not vals.get('class_id1'):
            raise osv.except_osv(_('Warning!'), _('Select atleast one class under Organisation Tab'))
                                 
        return super(hr_employee, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('birthday',False):
            vals.update({'age' : self.get_age(cr, vals.get('birthday'))})
        return super(hr_employee, self).write(cr, uid, ids, vals, context) 

hr_employee()

class resource_resource(osv.osv):
    _inherit = "resource.resource"
    _description = "Resource Detail"
    _columns = {
        'name': fields.char("Name", required=True, size=30)
        }
resource_resource()
    
    
class hr_punch(osv.osv):
    _name = 'hr.punch'
    _description = 'Hr Punch'
    _columns = {
                'punch_date'   : fields.date('Date'),
                'start_time'   : fields.datetime('Start Time'),
                'end_time'     : fields.datetime('End Time'),
                'units'        : fields.float('Units'),
                'notes'        : fields.text('Notes'),
                'punch_timesheet_id' : fields.many2one('hr.emp.timesheet','Time sheet Punch'),
                'daily_timesheet_id' : fields.many2one('hr.emp.timesheet','Daily Time sheet Punch')
                }
hr_punch()
    
class hr_daily_class(osv.osv):
    _name = 'hr.daily.class'
    _description = 'Hr Daily Classes'
    _columns = {
                'daily_date'       : fields.date('Date'),
                'units'            : fields.float('Units'),
                'notes'            : fields.text('Notes'),
                'pay_code_id'      : fields.many2one('hr.pay.codes','Pay Code'),
                'class_id1'        : fields.many2one('hr.class1','Class1'),
                'class_id2'        : fields.many2one('hr.class2','Class2'),
                'class_id3'        : fields.many2one('hr.class3','Class3'),
                'class_id4'        : fields.many2one('hr.class4','Class4'),
                'class_id5'        : fields.many2one('hr.class5','Class5'),
                'class_id6'        : fields.many2one('hr.class6','Class6'),
                'class_id7'        : fields.many2one('hr.class7','Class7'),
                'class_id8'        : fields.many2one('hr.class8','Class8'),
                'class_id9'        : fields.many2one('hr.class9','Class9'),
                'class_id10'       : fields.many2one('hr.class10','Class10'),
                'daily_timesheet_id' : fields.many2one('hr.emp.timesheet','Daily Time Sheets') 
                }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """
            Add Dynamic Labels based on the class Mappings
        """
        mapping_obj = self.pool.get('hr.class.mapping')
        if not context: context = {}
        res = super(hr_daily_class, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree' :
            doc = etree.XML(res['arch'])
            for m in mapping_obj.browse(cr, uid, mapping_obj.search(cr, uid, [])):
                nodes = doc.xpath("//field[@name='"+m.name[0:5]+'_id'+m.name[5:]+"']")
                for node in nodes:
                    node.set('invisible', '0')
                    node.set('string', m.label)
                    setup_modifiers(node, res['fields'][m.name[0:5]+'_id'+m.name[5:]])
                     
            res['arch'] = etree.tostring(doc)
        return res
    
hr_daily_class()

class hr_emp_timesheet(osv.osv):
    _name = 'hr.emp.timesheet'
    _description = 'Hr Employee Timesheets'
    _columns= {
               'employee_id' : fields.many2one('hr.employee','Employee'),
               'period_start_dt' : fields.date('Period Start'),
               'period_end_dt' : fields.date('Period End'),
               'punch_ids' : fields.one2many('hr.punch', 'punch_timesheet_id', 'Punch'),
               'daily_class_ids' : fields.one2many('hr.daily.class','daily_timesheet_id', 'Daily Class')
               }

    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        res = {'period_start_dt' : False,
                            'period_end_dt' : False}
        emp_obj = self.pool.get('hr.employee')
        if employee_id:
            emp = emp_obj.browse(cr, uid, employee_id)
            if emp.pay_group_id:
                res.update({
                            'period_start_dt' : emp.pay_group_id.period_start_dt,
                            'period_end_dt' : emp.pay_group_id.period_end_dt
                            })
        return {'value':res}
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('employee_id'):
            vals.update(self.onchange_employee_id(cr, uid, [], vals.get('employee_id'), context)['value'])
            
        res = super(hr_emp_timesheet, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('employee_id'):
            for case in self.browse(cr, uid, ids):
                vals.update(self.onchange_employee_id(cr, uid, ids, vals.get('employee_id'), context)['value'])
        res = super(hr_emp_timesheet, self).write(cr, uid, ids, vals, context)
        return res
            

hr_emp_timesheet()
     

    