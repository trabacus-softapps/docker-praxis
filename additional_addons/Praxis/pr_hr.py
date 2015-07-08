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
from datetime import datetime
from dateutil import parser
import pytz
from pytz import timezone
from dateutil.relativedelta import relativedelta
import calendar
from dateutil import rrule
from xlsxwriter.workbook import Workbook
import time
import os


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
            
        
    def _get_login_status(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        today = datetime.now()
        punch_date = today.strftime('%Y-%m-%d')
        ts_obj = self.pool.get('hr.emp.timesheet')
        punch_obj = self.pool.get('hr.punch')
        
        for case in self.browse(cr, uid, ids):
            res[case.id]={
                          'log_in'   : False,
                          'log_out'  : True,
                          'state' : 'absent'
                          }
            
            sheet_ids = ts_obj.search(cr , uid, [('period_start_dt','<=',punch_date),('period_end_dt','>=',punch_date), 
                                                 ('employee_id','=',case.id)])
            
            for s in ts_obj.browse(cr, uid, sheet_ids):
                p_ids = punch_obj.search(cr, uid, [('punch_date','=',punch_date),('timesheet_id','=',s.id)])
                
                for p in punch_obj.browse(cr, uid, p_ids):
                    
                    if p.end_time :
                        res[case.id]['log_out'] = True
                        res[case.id]['log_in'] = False
                        res[case.id]['state'] = 'logout'
                    
                    if not p.end_time and p.start_time:
                        res[case.id]['log_in'] = True
                        res[case.id]['log_out'] = False
                        res[case.id]['state'] = 'login'
            
        return res
    
    
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
                'time_rule_id'     : fields.many2one('hr.time.rule','Time Rule'),
                'log_in'           : fields.function(_get_login_status, type="boolean", store=False, multi="all", string="Log in"),
                'log_out'          : fields.function(_get_login_status, type="boolean", store=False, multi="all", string="Log out"),
                'state': fields.function(
                        _get_login_status, string="Status", type="selection", multi="all",
                        selection=[('login', 'Login'), ('logout', 'Logout'), ('absent', 'Absent')]), 
                }
    
    
    
    _defaults = {
                 'country_id'   : get_country,
                 'log_in'   : False,
                 'log_out'  : False
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
    _order = 'punch_date , start_time'
    
    
     #inheritted
    # to update the class details of employee
    def default_get(self, cr, uid, fields, context=None):
        emp_obj = self.pool.get('hr.employee')
        context = dict(context or {})
        res = super(hr_punch, self).default_get(cr, uid, fields, context=context)
        
        if context.get('employee_id'):
            emp = emp_obj.browse(cr, uid, context.get('employee_id'))
            res.update({
                           'class_id1' : emp.class_id1 and emp.class_id1.id or False,
                           'class_id2' : emp.class_id2 and emp.class_id2.id or False,
                           'class_id3' : emp.class_id3 and emp.class_id3.id or False,
                           'class_id4' :  emp.class_id4 and emp.class_id4.id or False,
                           'class_id5' : emp.class_id5 and emp.class_id5.id or False,
                           'class_id6' : emp.class_id6 and emp.class_id6.id or False,
                           'class_id7' : emp.class_id7 and emp.class_id7.id or False,
                           'class_id8' : emp.class_id8 and emp.class_id8.id or False,
                           'class_id9' : emp.class_id9 and emp.class_id9.id or False,
                           'class_id10' : emp.class_id10 and emp.class_id10.id or False,
                        })
        return res
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """
            Add Dynamic Labels based on the class Mappings
        """
        mapping_obj = self.pool.get('hr.class.mapping')
        if not context: context = {}
        res = super(hr_punch, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
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
    
    
    _columns = {
                'punch_date'      : fields.date('Date'),
                'act_start_time'  : fields.datetime('Actual Start Time'),
                'start_time'      : fields.datetime('Start Time'),
                'end_time'        : fields.datetime('End Time'),
                'act_end_time'    : fields.datetime('Actual End Time'),
                'units'        : fields.float('Units'),
                'notes'        : fields.text('Notes'),
                'login_time'    : fields.char('Start Time'),
                'logout_time'    : fields.char('End Time'), 
                'paid_hrs'     : fields.float('Paid Units'),
                'paycode_id'       : fields.many2one('hr.pay.codes','Pay Code'),
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
                'timesheet_id' : fields.many2one('hr.emp.timesheet','Time sheet Punch'),
                'type' : fields.selection([('daily','Daily'),('punch','Punch')], 'Type'),
                'check' : fields.boolean('Check'),
                'multi_punch_lines' : fields.one2many("multi.punch", 'punch_id', "Multi Punch Lines"),
                
                }
    
    _defaults = {
                 'type' : 'punch'
                 }
    
    

    def print_formatted(self, dt):
        DATE_FORMAT = '%Y-%m-%d %H:%M:%S %Z%z'
        formatted_date = dt.strftime(DATE_FORMAT)
        print "%s :: %s" % (dt.tzinfo, formatted_date)
        
    def check_local_time(self, cr, uid, ids, time, punch_date, context=None):
        res = {}
        warning = {}
        
        if time:
            time = time[0:5] + ':00 ' + time[6:]
            if int(time[0:2]) > 12 or int(time[3:5]) > 59:
                warning = {
                              'title'   : _('Warning!'),
                              'message' : _('Please enter valid time')
                          }
                if context.get('login'):
                    res.update({'login_time':''})
                else:
                    res.update({'logout_time':''})
                
                return {'value' : res, 'warning': warning}
            
        if time and punch_date:
            start_time = punch_date +' '+time
            
            date = datetime.strptime(start_time, '%Y-%m-%d %I:%M:%S %p')
            users_timezone = timezone("Asia/Kolkata")
            
            date = users_timezone.localize(date)
            date = date.astimezone(users_timezone)
            self.print_formatted(date)
            
            utc_timezone = timezone('UTC')
            date = date.astimezone(utc_timezone)
            self.print_formatted(date)
            
            if context.get('login'):
                res.update({'start_time': date})
            
            else:
                res.update({'end_time': date})
        
        return {'value' : res, 'warning': warning}
     
     

    
    def onchange_login_time(self, cr, uid, ids, chk_which, login_time, logout_time, punch_date, context=None):
        result= {
                 'value' :{},
                 'warning' : {}
                 }
        warning = {}
        context = dict(context or {})
        
        if chk_which in ('p_date', 'login') and login_time:
            context.update({'login':1})
            res = self.check_local_time(cr, uid, ids, login_time, punch_date, context)
            result['value'].update(res['value'])
            result['warning'].update(res['warning'])
        
        if not login_time:
            result['value'].update({'start_time':False})
        
        if not logout_time:
            result['value'].update({'end_time':False})
            
        
        if chk_which in ('p_date', 'log_out') and logout_time:
            context.update({'login':0})
            res = self.check_local_time(cr, uid, ids, logout_time, punch_date, context)
            result['value'].update(res['value'])
            result['warning'].update(res['warning'])
        print "result...", result
        return result
#         zone = self.pool.get('res.users').browse(cr,uid,uid).tz or 'Asia/Kolkata'
#         local_tz = pytz.timezone(zone)
#         
#         if login_time:
#             login_time = login_time[0:5] + ':00 ' + login_time[6:]
#             if int(login_time[0:2]) > 12 or int(login_time[3:5]) > 59:
#                 warning = {
#                               'title'   : _('Warning!'),
#                               'message' : _('Please enter valid time')
#                           }
#                 res.update({'login_time':''})
#             
#         if login_time and punch_date:
#             print "login time", login_time
#             start_time = punch_date +' '+login_time
#             
#             date = datetime.strptime(start_time, '%Y-%m-%d %I:%M:%S %p')
#             users_timezone = timezone("Asia/Kolkata")
#             
#             date = users_timezone.localize(date)
#             date = date.astimezone(users_timezone)
#             self.print_formatted(date)
#             
#             utc_timezone = timezone('UTC')
#             date = date.astimezone(utc_timezone)
#             self.print_formatted(date)
#             res.update({'start_time': date })
#             
#             
# #             start_date = start_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
# #             utc_timezone = timezone('UTC')
# #             date = start_date.astimezone(utc_timezone)
# #             
# #             res.update({'start_time': date })
# #             
# #             print "start dtae", start_time, start_date
#             
#             
#         return {'value' : res, 'warning':warning}
    
    
    def onchange_date(self, cr, uid, ids, punch_date, period_start_dt, period_end_dt, context=None):
        res = {}
        warning = ''
        
        
        if not period_start_dt and not period_end_date:
            raise osv.except_osv(_('Warning!'), _('Please enter the period start and end dates'))
        
        if punch_date and period_start_dt and period_end_dt:
            if period_start_dt <= punch_date <= period_end_dt:
                print 12
            else:
                warning = {
                              'title'   : _('Warning!'),
                              'message' : _('date  "'+ punch_date + '"  not in the between "'+ period_start_dt + '" and "'+ period_end_dt + '"')
                          }
                res.update({
                             'punch_date' : False
                            })
                
        return {'value' : res, 'warning' : warning }
    
    def onchange_time(self, cr, uid, ids, punch_date, start_time, end_time, context=None):
        res = {}
        warning = ''
        
        zone = self.pool.get('res.users').browse(cr,uid,uid).tz or 'Asia/Kolkata'
        local_tz = pytz.timezone(zone)
        
        if (start_time or end_time) and not punch_date:
            raise osv.except_osv(_('Warning!'), _('Please enter the date.'))
        
        if punch_date and start_time:
            
            punch_time = datetime.strptime(punch_date, '%Y-%m-%d')
            punch_time = punch_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
                
            start_date = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            start_date = start_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
            
#             punch_date =(parser.parse(''.join((re.compile('\d')).findall(punch_date)))).strftime('%Y-%m-%d')
#             start_date =(parser.parse(''.join((re.compile('\d')).findall(start_time)))).strftime('%Y-%m-%d')
            
            if punch_time.date() != start_date.date():
                warning = {
                              'title'   : _('Warning!'),
                              'message' : _('Please select the valid time')
                          }
                res.update({ 'start_time' : False })
                
        if punch_date and end_time:
            punch_date = datetime.strptime(punch_date, '%Y-%m-%d')
            punch_time = punch_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
                
            end_date = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            end_date = end_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
#             punch_date =(parser.parse(''.join((re.compile('\d')).findall(punch_date)))).strftime('%Y-%m-%d')
#             end_date =(parser.parse(''.join((re.compile('\d')).findall(end_time)))).strftime('%Y-%m-%d')
            if punch_date.date() != end_date.date():
                warning = {
                              'title'   : _('Warning!'),
                              'message' : _('Please select the valid time')
                          }
                res.update({ 'end_time' : False })
                
        if end_time and start_time:
            
            st_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            start_time = st_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
                
            end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            end_time = end_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
            
            diff = end_time - start_time
            
            if end_time < start_time:
                warning = {
                              'title'   : _('Warning!'),
                              'message' : _('Please select the valid end time')
                          }
                res.update({ 'end_time' : False })
            
        
        return {'value' : res, 'warning' : warning }
    
    def create_audit(self, cr, uid, ids, vals, context=None):
        context = dict(context or {})
        
        audit_vals = {}
        audit_obj = self.pool.get('hr.audit')
        today = datetime.now()
        
        zone = self.pool.get('res.users').browse(cr,uid,uid).tz or 'Asia/Kolkata'
        local_tz = pytz.timezone(zone)
        
        if ids:
            for case in self.browse(cr, uid, ids):
                new_start_date = ''
                old_start_date = ''
                new_end_date = ''
                old_end_date = ''
                old_units = 0.0
                new_units = 0.0
                audit_vals.update({
                               'punch_date' : vals.get('punch_date',case.punch_date),
                               'user_id'    : uid,
                               'event_type' : context.get('event_type'),
                               'timesheet_id' : case.timesheet_id.id,
                               'change_time' : today
                                       
                                       })
                
                if context.get('event_type')=='delete':
                    audit_obj.create(cr, uid, audit_vals)
                    
                
                if 'start_time' in vals:
                    
                    if case.start_time:
                        old_start_date = datetime.strptime(case.start_time, '%Y-%m-%d %H:%M:%S')
                        old_start_date = old_start_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
                        old_start_date = old_start_date.strftime('%I:%M %p')
                    
                    if vals.get('start_time'):
                        new_start_date = datetime.strptime(vals.get('start_time'), '%Y-%m-%d %H:%M:%S')
                        new_start_date = new_start_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
                        new_start_date = new_start_date.strftime('%I:%M %p')
                    
                    if old_start_date != new_start_date :
                            
                                
                        audit_vals.update({
                                           'original_value':old_start_date,
                                           'new_value' : new_start_date,
                                           'column_name' : 'Start Time',
                                           })
                        audit_ids = audit_obj.search(cr, uid, [('punch_date','=', vals.get('punch_date')), ('timesheet_id','=',vals.get('timesheet_id'))
                                                   ,('original_value','=',old_start_date),('new_value','=',new_start_date), ('column_name','=','Start Time')])
                        if not audit_ids:
                            audit_obj.create(cr, uid, audit_vals)
                
                if 'end_time' in vals: 
                    
                    if case.end_time:
                        old_end_date = datetime.strptime(case.end_time, '%Y-%m-%d %H:%M:%S')
                        old_end_date = old_end_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
                        old_end_date = old_end_date.strftime('%I:%M %p')
                    
                    if vals.get('end_time'):
                        new_end_date = datetime.strptime(vals.get('end_time'), '%Y-%m-%d %H:%M:%S')
                        new_end_date = new_end_date.replace(tzinfo=pytz.utc).astimezone(local_tz)
                        new_end_date = new_end_date.strftime('%I:%M %p')
                    
                   
                    if old_end_date != new_end_date :
                        audit_vals.update({
                                           'original_value':old_end_date,
                                           'new_value' : new_end_date,
                                           'column_name' : 'End Time',
                                           
                                           })
                        audit_ids = audit_obj.search(cr, uid, [('punch_date','=', vals.get('punch_date')), ('timesheet_id','=',vals.get('timesheet_id'))
                                                   ,('original_value','=',old_end_date),('new_value','=',new_end_date), ('column_name','=','End Time')])
                        if not audit_ids:
                            audit_obj.create(cr, uid, audit_vals)
                    
                if 'units' in vals:
                    
                    if case.units:
                        old_units = round(case.units,2)
                    
                    if 'units' in vals :
                        new_units = round(vals.get('units'),2)
                    
                    if old_units != new_units:
                        
                        audit_vals.update({
                                       'original_value':old_units or 0.00,
                                       'new_value' : new_units,
                                       'column_name' : 'Units',
                                       
                                       })
                        audit_ids = audit_obj.search(cr, uid, [('punch_date','=', vals.get('punch_date')), ('timesheet_id','=',vals.get('timesheet_id'))
                                                   ,('original_value','=',old_units),('new_value','=',new_units), ('column_name','=','Units')])
                        if not audit_ids:
                            audit_obj.create(cr, uid, audit_vals)
                   
                    
        return True
                
    
    def create(self, cr, uid, vals, context=None):
        context = dict(context or {})
        res = super(hr_punch, self).create(cr, uid, vals, context)
        if uid != 1 :
            context.update({'event_type':'create'})
            self.create_audit(cr, uid, [res], vals, context=context)
        
        return res
    
    
    def write(self, cr, uid, ids, vals, context=None):
        context = dict(context or {})
        if uid != 1 :
            context.update({'event_type':'edit'})
            self.create_audit(cr, uid, ids, vals, context=context)
        return super(hr_punch, self).write(cr, uid, ids, vals, context)
    
    def unlink(self, cr, uid, ids, context=None):
        context = dict(context or {})
        if uid != 1 :
            context.update({'event_type':'delete'})
            self.create_audit(cr, uid, ids, {}, context=context)
        
        return super(hr_punch, self).unlink(cr, uid, ids, context)
        
    
    
             
    
hr_punch()
    
class timesheet_summary(osv.osv):
    _name = 'timesheet.summary'
    _description = 'Time Sheet Summary'
    
   
    _columns = {
                'daily_date'       : fields.date('Date'),
                'units'            : fields.float('Units'),
                'notes'            : fields.text('Notes'),
                'paycode_id'       : fields.many2one('hr.pay.codes','Pay Code'),
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
                'timesheet_id'     : fields.many2one('hr.emp.timesheet','Daily Time Sheets'),
                'paid'             : fields.boolean('Paid'),
                
                }
    
        
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """
            Add Dynamic Labels based on the class Mappings
        """
        mapping_obj = self.pool.get('hr.class.mapping')
        if not context: context = {}
        res = super(timesheet_summary, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
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
    
timesheet_summary()

class hr_emp_timesheet(osv.osv):
    _name = 'hr.emp.timesheet'
    _inherit = ['mail.thread']
    _description = 'Hr Employee Timesheets'
    
    
    def default_get(self, cr, uid, fields, context=None):
        
        emp_obj = self.pool.get('hr.employee')
        context = dict(context or {})
        res = super(hr_emp_timesheet, self).default_get(cr, uid, fields, context)
        emp_ids = emp_obj.search(cr, uid, [('resource_id.user_id','=', uid)])
        
        if emp_ids:
            res.update({'employee_id': emp_ids[0]})
        
        return res
    
    _columns= {
               'employee_id' : fields.many2one('hr.employee','Employee'),
               'period_start_dt' : fields.date('Period Start'),
               'period_end_dt' : fields.date('Period End'),
               'punch_ids' : fields.one2many('hr.punch', 'timesheet_id', 'Punch', track_visibility="onchange"),
               'daily_ids' : fields.one2many('hr.punch', 'timesheet_id', 'Punch', domain=[('type','=','daily')], track_visibility="onchange"),
               'summary_ids' : fields.one2many('timesheet.summary','timesheet_id', 'Summary'),
               'emp_no' : fields.related('employee_id','identification_id', type='char', string='Employee Number'),
               'audit_ids' : fields.one2many('hr.audit','timesheet_id','Audit')
               
               }
    
    def name_get(self, cr, uid, ids, context=None):
        """ TO display the concatenated Period Dates (period_start_dt and period_end_dt) """
        if not ids:
            return []
        reads = self.read(cr, uid, ids, ['emp_no','period_start_dt','period_end_dt'], context=context)
        res = []
        
        for record in reads:
            name = ''
            
            if record['period_start_dt']:
                name = record['period_start_dt']
            
            if record['period_end_dt']:
                name = name + ' - ' + record['period_end_dt']
                
            if not record['period_start_dt'] and not record['period_end_dt'] :
                name = record['emp_no']
            res.append((record['id'], name))
        return res
    

    def onchange_employee_id(self, cr, uid, ids, employee_id, context=None):
        res = {'period_start_dt' : False,
                            'period_end_dt' : False}
        emp_obj = self.pool.get('hr.employee')
        if employee_id:
            emp = emp_obj.browse(cr, uid, employee_id)
            if emp.identification_id:
                res.update({ 'emp_no' : emp.identification_id })
            
            if emp.pay_group_id:
                res.update({
                            'period_start_dt' : emp.pay_group_id.period_start_dt,
                            'period_end_dt' : emp.pay_group_id.period_end_dt
                            })
        return {'value':res}
    
    
    def gettime(self, cr, uid, dates, rounding, minutes, context=None):
        """ to calculate the time round based on conditions and the minutes 
        round forward with 15 mins   :  9:05  -> 9:15
        round backward  with 15 mins :  9:05 ->  9:00
        round near with 15 mins      :  9:07 -> 9:00 and 9:08 -> 9:15
        @time : start or end time
        @rounding is the type
        @return datetime
        """
        context = dict(context or {})
        res = False
        
        zone = self.pool.get('res.users').browse(cr,uid,uid).tz or 'Asia/Kolkata'
        local_tz = pytz.timezone(zone)
        
        dates = datetime.strptime(dates, '%Y-%m-%d %H:%M:%S')
        #dates = dates.replace(tzinfo=pytz.utc).astimezone(local_tz)
        
        if rounding == 'round_forward' :
            dates = dates + relativedelta(minutes = minutes)
            interval = (dates.minute / minutes) * minutes
            dates = dates.replace(minute = interval)
            return dates.strftime('%Y-%m-%d %H:%M:%S')
        
        
        elif rounding == 'round_back':
            interval = (dates.minute / minutes) * minutes
            dates = dates.replace(minute = interval)
            return dates.strftime('%Y-%m-%d %H:%M:%S')
        
        else:
            interval = dates.minute / minutes
            rem = dates.minute % minutes
        
            if rem <= ( minutes / 2 ):
                interval = interval * minutes
            else:
                interval = (interval * minutes) + minutes
           
            dates = dates.replace(minute = 0)
            dates = dates + relativedelta(minutes = interval)
            return dates.strftime('%Y-%m-%d %H:%M:%S')
        
        return res
    
    
    def time_rounding(self, cr, uid, ids, punch_id, context=None):
        """ TO calculate time rounding of time sheet"""
        punch_obj = self.pool.get('hr.punch')
        vals = {}
        
        for case in self.browse(cr, uid, ids):
            if punch_id:
                if punch_id.start_time and case.employee_id.time_rule_id.rounding_id :
                    if case.employee_id.time_rule_id.rounding_id.clock1:
                        round_id = case.employee_id.time_rule_id.rounding_id
                        
                        start_time = self.gettime(cr, uid, punch_id.start_time, round_id.type1, 
                                                  round_id.hours1, context=context)
                        if start_time:
                            locale_date = self.localise_time(cr, uid, ids, datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') ,context=context)
                            vals.update({'login_time': locale_date.strftime('%I:%M %p'),'start_time' : start_time})
                            # to change the original clock time
                            if uid !=1 :
                                vals.update({'act_start_time' : start_time})
                
                if punch_id.end_time and case.employee_id.time_rule_id.rounding_id :
                    if case.employee_id.time_rule_id.rounding_id.clock2:
                        round_id = case.employee_id.time_rule_id.rounding_id
                        
                        end_time = self.gettime(cr, uid, punch_id.end_time, round_id.type2, 
                                                  round_id.hours2, context=context)
                        if end_time:
                            locale_date = self.localise_time(cr, uid, ids, datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S') ,context=context)
                            vals.update({'logout_time': locale_date.strftime('%I:%M %p'),'end_time' : end_time})
                            if uid != 1 :
                                vals.update({'act_end_time' : end_time})
                
                punch_obj.write(cr, uid, [punch_id.id], vals, context)
                 
        
        return True
    
    def localise_time(self, cr, uid, ids, date ,context=None):
        """ Method to convert UTC to Asia/Kolkata Time zone"""
        users_timezone = timezone("Asia/Kolkata")
        utc_timezone = timezone('UTC')
        
        date = utc_timezone.localize(date)
        date = date.astimezone(utc_timezone)
        
        
        date = date.astimezone(users_timezone)
        return date
    
    
    def calculate_timesheet(self, cr, uid, ids, context=None):
        
        """ 
        TO calculate time difference and consolidate the records 
        
        date difference :  diff = end_time - start_time
        Hours" : (diff.seconds) / 3600
        "Minutes" :((diff.seconds) / 60.0) 
        "hours + minutes" : ((diff.seconds) / 60.0) / 60.0  
        """
        
            
        data = []
        sum_obj = self.pool.get('timesheet.summary')
        zone = self.pool.get('res.users').browse(cr,uid,uid).tz or 'Asia/Kolkata'
        local_tz = pytz.timezone(zone)
        punch_obj = self.pool.get('hr.punch')
        lines = {}
        lunch_hrs = 0.0
        tot_units = {}
        
        
        for case in self.browse(cr, uid, ids):
            vals = {}
            lunch_diff = 0.0
            break_hours = 0.0
            master_class = (
                           case.employee_id.class_id1 and case.employee_id.class_id1.id or False,
                           case.employee_id.class_id2 and case.employee_id.class_id2.id or False,
                           case.employee_id.class_id3 and case.employee_id.class_id3.id or False,
                           case.employee_id.class_id4 and case.employee_id.class_id4.id or False,
                           case.employee_id.class_id5 and case.employee_id.class_id5.id or False,
                           case.employee_id.class_id6 and case.employee_id.class_id6.id or False,
                           case.employee_id.class_id7 and case.employee_id.class_id7.id or False,
                           case.employee_id.class_id8 and case.employee_id.class_id8.id or False,
                           case.employee_id.class_id9 and case.employee_id.class_id9.id or False,
                           case.employee_id.class_id10 and case.employee_id.class_id10.id or False,
                         )
            
            for p in case.punch_ids:
                if p.type =='punch' :
                    if case.employee_id.time_rule_id and case.employee_id.time_rule_id.missing_punches in ('unpost','dntcalc'):
                        if not p.start_time or not p.end_time:
                            continue
                    
                    # if post missing entries add or deduct the work hours for missing start or end dates
                    if case.employee_id.time_rule_id and case.employee_id.time_rule_id.missing_punches == 'post':
                        if not p.start_time and not p.end_time:
                            continue
                        
                        elif p.start_time and not p.end_time:
                            end_time = datetime.strptime(p.start_time, '%Y-%m-%d %H:%M:%S') + relativedelta(hours = case.employee_id.time_rule_id.work_hours)
                            locale_date = self.localise_time(cr, uid, ids, end_time ,context=context)
                            punch_obj.write(cr, uid, [p.id], {'logout_time': locale_date.strftime('%I:%M %p'),'end_time':end_time.strftime('%Y-%m-%d %H:%M:%S'), 'act_end_time':end_time.strftime('%Y-%m-%d %H:%M:%S')})
                        
                        elif p.end_time and not p.start_time:
                            start_time = datetime.strptime(p.end_time, '%Y-%m-%d %H:%M:%S') - relativedelta(hours = case.employee_id.time_rule_id.work_hours)
                            locale_date = self.localise_time(cr, uid, ids, start_time ,context=context)
                            punch_obj.write(cr, uid, [p.id], {'login_time':locale_date.strftime('%I:%M %p'),'start_time':start_time.strftime('%Y-%m-%d %H:%M:%S'), 'act_start_time': start_time.strftime('%Y-%m-%d %H:%M:%S')})
                            
                            
                    # to  get the time rounding
                    self.time_rounding(cr, uid, ids, p, context)
                        
                    st_dt = datetime.strptime(p.start_time, '%Y-%m-%d %H:%M:%S')
                    start_time = st_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
                    
                    end_dt = datetime.strptime(p.end_time, '%Y-%m-%d %H:%M:%S')
                    end_time = end_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
                    
                    # to find the difference between start and end time
                    diff = end_time - start_time
                    units = ((diff.seconds) / 60.0) / 60.0
                    vals.update({'units': units})
                    
                    # to check the lunch hours for employee
                    if case.employee_id.time_rule_id and case.employee_id.time_rule_id.lunch_id :
                        lunch_id = case.employee_id.time_rule_id.lunch_id
                        
                        if lunch_id.lunch_hours and lunch_id.after_work_hour:
                            lunch_diff = (datetime.now()+relativedelta(hour=lunch_id.after_work_hour, minute=lunch_id.lunch_hours)) - (datetime.now()+relativedelta(hour=0, minute=0))
                            lunch_diff = ((lunch_diff.seconds) / 60.0) / 60.0
                            
                            
                            if lunch_diff <= units:
                                break_hours = lunch_id.lunch_hours / 60.0 # coverting the minutes to float
                                
                                if case.employee_id.time_rule_id.lunch_id.paid_by_employer :
                                    vals.update({'units': units})
                                
                                else:
                                    vals.update({'units': (units - break_hours)})
                                
                                # to get the difference after the reducing break
                                units = ((diff.seconds - (lunch_id.lunch_hours * 60)) / 60.0) / 60.0
                           
                                        
                                        
                    # for updating the Units
                    punch_obj.write(cr, uid, [p.id], vals, context)
                    
                    # for Punch records
                    # IF OT RULE
                    if case.employee_id.time_rule_id.ot_rule_line:
                        for ot in case.employee_id.time_rule_id.ot_rule_line:
                            days = [str(x.name) for x in ot.weekday_ids]
                            
                            paycode_id = case.employee_id.time_rule_id.paycode_id.id
                            start_day = calendar.day_name[st_dt.weekday()]
                            
                            if 'All Selected' in days or start_day in days:
                                paycode_id = ot.paycode_id.id
                                
                                if units > ot.work_hours:
                                    work_hours = ot.work_hours
                                    units = units - ot.work_hours
                                
                                else:
                                     work_hours = units
                                     units = 0.0
                                     
                                key = (paycode_id, master_class)
                                if key in lines:
                                    lines[key].append(p.id)
                                    tot_units[key] += work_hours
                                else:
                                    lines[key] = [p.id]
                                    tot_units[key] = work_hours
                    
                    # if no OT RULE
                    else:
                        key = (case.employee_id.time_rule_id.paycode_id.id, master_class)
                        if key in lines:
                            lines[key].append(p.id)
                            tot_units[key] += units
                        else:
                            lines[key] = [p.id]
                            tot_units[key] = units
                    
                        
                    # to check if there is lunch hours
                    if break_hours:
                        key = (case.employee_id.time_rule_id.lunch_id.paycode_id.id, master_class)
                        if key in lines:
                            lines[key].append(p.id)
                            tot_units[key] += break_hours
                        else:
                            lines[key] = [p.id]
                            tot_units[key] = break_hours
                        
                elif p.type =='daily' :
                    master_class = (
                               p.class_id1 and p.class_id1.id or False,
                               p.class_id2 and p.class_id2.id or False,
                               p.class_id3 and p.class_id3.id or False,
                               p.class_id4 and p.class_id4.id or False,
                               p.class_id5 and p.class_id5.id or False,
                               p.class_id6 and p.class_id6.id or False,
                               p.class_id7 and p.class_id7.id or False,
                               p.class_id8 and p.class_id8.id or False,
                               p.class_id9 and p.class_id9.id or False,
                               p.class_id10 and p.class_id10.id or False,
                             )
                    key = (p.paycode_id.id, master_class)
                    
                    if key in lines:
                        lines[key].append(p.id)
                        tot_units[key] += p.units
                    else:
                        lines[key] = [p.id]
                        tot_units[key] = p.units
                    
                    
            for l in lines:
                if tot_units[l] > 0 :
                    sum_lines = {
                                 'daily_date' : case.period_end_dt,
                                 'paycode_id' : l[0],
                                 'units'      : tot_units[l],#l[1][10] * len( lines[l] ),
                                 'class_id1' :  l[1][0], 
                                 'class_id2' :  l[1][1], 
                                 'class_id3' :  l[1][2], 
                                 'class_id4' :  l[1][3], 
                                 'class_id5' :  l[1][4], 
                                 'class_id6' :  l[1][5], 
                                 'class_id7' :  l[1][6], 
                                 'class_id8' :  l[1][7], 
                                 'class_id9' :  l[1][8], 
                                 'class_id10':  l[1][9], 
                                 }
                    data.append((0,0, sum_lines))
            # deleting the existing line and creating newline
            summary_ids = sum_obj.search(cr, uid, [('timesheet_id','=', case.id)])
            sum_obj.unlink(cr, uid, summary_ids, context=None) 
            self.write(cr, uid, ids, {'summary_ids' : data}, context)
        return True
    
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('employee_id'):
            vals.update(self.onchange_employee_id(cr, uid, [], vals.get('employee_id'), context)['value'])
            
        res = super(hr_emp_timesheet, self).create(cr, uid, vals, context)
        return res
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('employee_id'):
            for case in self.browse(cr, uid, ids):
                vals.update(self.onchange_employee_id(cr, uid, ids, vals.get('employee_id'), context)['value'])
        
#         if 'punch_ids' in vals:
#             for p in vals.get('punch_ids',[]):
#                 if p and p[2]:
#                     if p[2].get('start_time') and p[2].get('punch_date'):
#                         p[2].update({
#                                      'start_time' : p[2].get('punch_date') +' '+p[2].get('start_time')
#                                      })
#                         print "datesss", p[2]
#         
        res = super(hr_emp_timesheet, self).write(cr, uid, ids, vals, context)
        return res
            
#             
#     def dummy_button(self,cr, uid, ids, context=None):
#         status_obj = self.pool.get("monthly.status")
#         
#         status_obj.generate_montly_status_xls(cr, uid, ids,context)
#         
#         return True
    

    def build_header(self, start_date, end_date, workbook, sheet, datetime, row, text_centre, bold_centre, border_style,slno):
        start_time = datetime.strptime(start_date, '%Y-%m-%d')
        end_time = datetime.strptime(end_date, '%Y-%m-%d')
        
        sheet.write(row, 0, 'Unit')
        sheet.write(row, 5, 'EmployeeType : Temporary')
        sheet.write(row, 15,'Pay Period From : ' + start_time.strftime('%d-%m-%Y') + '   TO   ' + end_time.strftime('%d-%m-%Y'))
        
        row = row + 1
        sheet.write(row, 0, '#', bold_centre)
        sheet.write(row, 1, 'Emp No.', bold_centre)
        sheet.write(row, 2, 'Name', bold_centre)
        sheet.write(row, 3, 'Designation', bold_centre)
        i = 4
        j = 2
        k = 0
        
        for dt in rrule.rrule(rrule.DAILY, dtstart=datetime.strptime(start_date, '%Y-%m-%d'), until=datetime.strptime(end_date, '%Y-%m-%d')):
            sheet.write(row, i, dt.strftime('%d'), bold_centre)
            i = i + 1
        
        sheet.write(row, i, 'Holiday(H)', bold_centre)
        i = i + 1
        sheet.write(row, i, 'Absent(A)', bold_centre)
        i = i + 1
        sheet.write(row, i, 'Present(P)', bold_centre)
        i = i + 1
        sheet.write(row, i, 'Leave(L)', bold_centre)
        i = i + 1
        sheet.write(row, i, 'WeeklyOff(W)', bold_centre)
        i = i + 1
        sheet.write(row, i, 'Payable Days', bold_centre)
        return slno, j, k, row

    def get_file(self, cr, uid, report_data, context=None):
        sheet_ids = report_data['variables']['sheet_ids']
        start_date = report_data['variables']['start_date']
        end_date = report_data['variables']['end_date']
        group_by = report_data['variables']['emp_group_by']
        
        datafile = 'test.xlsx'
        workbook = Workbook(datafile)
        sheet = workbook.add_worksheet()
        punch_obj = self.pool.get('hr.punch')
        holiday_obj = self.pool.get('hr.emp.holiday')
        
        today = datetime.now()
        class_id = False
        row = 0
        header= False
        
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:AF', 5)
        sheet.set_column('AI:AZ', 15)
        
        text_centre = workbook.add_format({'align':'centre', 'valign':'top'})
        bold_centre = workbook.add_format({'align':'centre'})
        bold_centre.set_bg_color('5C70A4')
        bold_centre.set_font_color('white')
        bold_centre.set_border()
        border_style = workbook.add_format({'align':'centre'})
        border_style.set_border()
        
        vals = {}
        row_pos = 2
        for case in self.browse(cr, uid, sheet_ids):
            
            if group_by and not class_id:
                slno = 0
                class_id = case.employee_id[str(group_by)].id
                slno, j, k, row = self.build_header(start_date, end_date, workbook, sheet, datetime, row, text_centre, bold_centre, border_style,slno )
                header = True
            
            if group_by and class_id != case.employee_id[str(group_by)].id :
                slno = 0
                row = row + 2
                row_pos = row + 2
                slno, j, k, row = self.build_header(start_date, end_date, workbook, sheet, datetime, row,text_centre, bold_centre, border_style, slno)
                header = True
            
            
            if not header :
                # for space
                slno = 0
                row = row
                slno, j, k, row = self.build_header(start_date, end_date, workbook, sheet, datetime, row, text_centre, bold_centre, border_style, slno )
                header = True
            
        
        
            p_cnt = 0
            a_cnt = 0
            h_cnt = 0
            l_cnt = 0
            wo_cnt = 0
            slno = slno + 1
            
            col_value = [slno, case.employee_id.identification_id, case.employee_id.name + ' ' +case.employee_id.last_name , '' ]
            
            punch_date = datetime.strptime(case.period_start_dt, '%Y-%m-%d')
            for r in range(1, ((calendar.monthrange(punch_date.year, punch_date.month)[1]) + 1)):
                
                punch_date = punch_date.replace(day = r)
                punch_ids = punch_obj.search(cr, uid, [('timesheet_id','=', case.id),('punch_date','=',punch_date)])
                
                if punch_ids:
                    for p in punch_obj.browse(cr, uid ,punch_ids):
                        if p.type != 'daily':
                            if p.units > 7:
                                status = 'P'
                                p_cnt = p_cnt + 1
                            
                            else:
                                status = 'P \n 1/2'
                                p_cnt = p_cnt + 1
                        else:
                            status = 'L'
                            l_cnt = l_cnt + 1
                else:
                    if punch_date.weekday() == 6:
                        status = 'W'
                        wo_cnt = wo_cnt + 1
                    
                    else:
                        
                        if case.employee_id.time_rule_id and case.employee_id.time_rule_id.paycode_id:
                            holiday_ids = holiday_obj.search(cr, uid, [('paycode_id','=',case.employee_id.time_rule_id.paycode_id.id), ('date','=',punch_date.strftime('%Y-%m-%d'))])
                            
                            if holiday_ids:
                                status = 'H'
                                h_cnt = h_cnt +1
                            else:
                                if punch_date > today:
                                    status = 'X'
                                else:
                                    status = 'A'
                                    a_cnt = a_cnt +1
                                
                col_value.append(status)
            # building The vals
            col_value.extend([h_cnt, a_cnt, p_cnt, l_cnt, wo_cnt, (p_cnt + wo_cnt)])
            vals={}
            vals[case.id] = list(col_value)
            row = row + 1
            
            if group_by:
                class_id = case.employee_id[str(group_by)].id
                
        
             # starting row position
            for v in vals.values():
                if 'P \n 1/2' in v:
                    sheet.set_row(j, 30)
                 
                k = 0 # starting col position
                for data in v:
                    sheet.write(row_pos,k, data, text_centre)
                    k= k+1
                row_pos = row_pos + 1
            
                            
           
        workbook.close()
        fp = open(datafile, 'rb')
        contents = fp.read()
        os.remove(datafile) 
        return contents  


   # Monthly Status Report
    def generate_montly_status_xls(self, cr, uid, report_data, context=None):
        
        tsheet_ids = report_data['variables']['sheet_ids']
        
        from_date = report_data['variables']['start_date']
        to_date = report_data['variables']['end_date']
        
        emp_obj = self.pool.get("hr.employee")
        timesheet_obj = self.pool.get("hr.emp.timesheet")
        punch_obj = self.pool.get("hr.punch")
        hrot_obj = self.pool.get("hr.ot.rule")
        
        zone = self.pool.get('res.users').browse(cr,uid,uid).tz or 'Asia/Kolkata'
        local_tz = pytz.timezone(zone)
        
        
        datafile = 'monthly_status_report.xlsx'
        workbook = Workbook(datafile)
        sheet = workbook.add_worksheet()
        sheet.set_column('A:A',10)
        sheet.set_column('B:ZZ',06)
        
        
        
        bold = workbook.add_format({'bold': True})
        bold.set_font_name('Verdana')
        bold.set_font_size(9)
        
        left = workbook.add_format({'align': 'left'})
        left.set_font_name('Verdana')
        left.set_font_size(8)
        
        left = workbook.add_format({'align': 'center'})
        left.set_font_name('Verdana')
        left.set_font_size(8)
        
        bold_left = workbook.add_format({'align': 'left', 'bold': True})
        bold_left.set_font_name('Verdana')
        bold_left.set_font_size(9)
        
        bold_left_border = workbook.add_format({'align': 'left', 'bold': True})
        bold_left_border.set_font_name('Verdana')
        bold_left_border.set_font_size(9)
        bold_left_border.set_border(1)
        
        
        bold_centre = workbook.add_format({'align': 'centre', 'bold': True})
        bold_centre.set_font_name('Verdana')
        bold_centre.set_font_size(8)
        
        
        bold_centre_colour = workbook.add_format({'align': 'centre', 'bold': True})
        bold_centre_colour.set_font_name('Verdana')
        bold_centre_colour.set_font_size(8)
        bold_centre_colour.set_bg_color('2C4770')
        bold_centre_colour.set_font_color('white')
        bold_centre_colour.set_border(1)  
        
        
        border_bottom = workbook.add_format({'align': 'left'})
        border_bottom.set_font_name('Verdana')
        border_bottom.set_font_size(2)
        border_bottom.set_bottom(1)
        
        border_right = workbook.add_format({'align': 'left'})
        border_right.set_font_name('Verdana')
        border_right.set_font_size(2)
        border_right.set_right(1)
        
        
        
        centre = workbook.add_format({'align': 'centre'})
        centre.set_font_name('Verdana')
        centre.set_font_size(8)
        
        merge_format_color = workbook.add_format({
                    'bold': 1,
                    'align': 'centre',
                    'valign': 'vcenter',
                    })
        merge_format_color.set_font_color('2C4770')
        
        
        merge_format = workbook.add_format({
                    'bold': 1,
                    'align': 'left',
                    'valign': 'vcenter',
                    })
        
        merge_format_centre = workbook.add_format({
                    'bold': 1,
                    'align': 'centre',
                    'valign': 'vcenter',
                    })
        
        
        merge_format_b = workbook.add_format({
                    'align': 'left',
                    'valign': 'vcenter',
                    })
        merge_format_b.set_underline(1)
        
        row = 0
        col = 1
        head = 0
        colcount = 0
        
        z = 2
        row = 5
        if tsheet_ids:  
            for tsheet in self.browse(cr, uid, tsheet_ids):
                
                sheet.set_row(z+2,25)
                
                sheet.merge_range('K1:O1', 'Monthly Status Report',merge_format_color)
                sheet.write(1,0, 'Unit', bold_left)
                period = 'Period' +' '+ str(from_date) +' ' +str(to_date)
                sheet.merge_range('K2:O2', period, merge_format_centre)
                
                emp_no = 'Emp No:' +' '+ str(tsheet.employee_id and tsheet.employee_id.identification_id)
                
                sheet.write(z, 0, emp_no, bold_left)
                
                emp_name = 'Employee Name : ' + ' ' +str(tsheet.employee_id and tsheet.employee_id.name)+str(tsheet.employee_id and tsheet.employee_id.last_name)
                
                sheet.write(z, 4, emp_name, bold_left)
                
                comp_name = 'Company:'+ ' ' + str(tsheet.employee_id and tsheet.employee_id.company_id.name) 
                
                sheet.write(z, 16, comp_name, bold_left)
                
                
                cr.execute("""
                        select gen_date::date from generate_series('"""+str(from_date)+"""',
                          '"""+str(to_date)+"""', '1 day'::interval) gen_date
                        """)
                i = 1
                cnt = cr.dictfetchall()
                dys = len(cnt)
                for d in cnt:
                    dt = datetime.strptime(d['gen_date'], '%Y-%m-%d')
                    week = dt.strftime('%a')
                    day = dt.strftime('%d')
                    
                    week_day = str(day)+ ' \n' + week
                    sheet.write(z+2, i, week_day, bold_centre_colour)
                    i = i+1
                    
                
                sheet.write(z+3, 0, 'Status', bold_left_border)
                sheet.write(z+4, 0, 'In Time', bold_left_border)
                sheet.write(z+5, 0, 'Out Time', bold_left_border)                        
                sheet.write(z+6, 0, 'Duration', bold_left_border)
                sheet.write(z+7, 0, 'Regular', bold_left_border)
                sheet.write(z+8, 0, 'OT ', bold_left_border)
                sheet.write(z+9, 0, 'Shift', bold_left_border)
#                 sheet.write(z+9, 1, '',border_bottom )
#                 sheet.write(z+9, 2, '',border_bottom )
#                 sheet.write(z+9, 3, '',border_bottom )
#                 sheet.write(z+9, 4, '',border_bottom )
#                 sheet.write(z+9, 5, '',border_bottom )
#                 sheet.write(z+9, 6, '',border_bottom )
#                 sheet.write(z+9, 7, '',border_bottom )
#                 sheet.write(z+9, 8, '',border_bottom )
#                 sheet.write(z+9, 9, '',border_bottom )
#                 sheet.write(z+9, 10, '',border_bottom )
#                 sheet.write(z+9, 11, '',border_bottom )
#                 sheet.write(z+9, 12, '',border_bottom )
#                 sheet.write(z+9, 13, '',border_bottom )
#                 sheet.write(z+9, 14, '',border_bottom )
#                 sheet.write(z+9, 15, '',border_bottom )
#                 sheet.write(z+9, 16, '',border_bottom )
#                 sheet.write(z+9, 17, '',border_bottom )
#                 sheet.write(z+9, 18, '',border_bottom )
#                 sheet.write(z+9, 19, '',border_bottom )
#                 sheet.write(z+9, 20, '',border_bottom )
#                 sheet.write(z+9, 21, '',border_bottom )
#                 sheet.write(z+9, 22, '',border_bottom )
#                 sheet.write(z+9, 23, '',border_bottom )
#                 sheet.write(z+9, 24, '',border_bottom )
#                 sheet.write(z+9, 25, '',border_bottom )
#                 sheet.write(z+9, 26, '',border_bottom )
#                 sheet.write(z+9, 27, '',border_bottom )
#                 sheet.write(z+9, 28, '',border_bottom )
#                 print "DYS",dys
#                 if dys >= 29: 
#                     sheet.write(z+9, 29, '',border_bottom )
#                     
#                 if dys == 29: 
#                     sheet.write(z+3, 29, '', border_right)
#                     sheet.write(z+4, 29, '', border_right)
#                     sheet.write(z+5, 29, '', border_right)                        
#                     sheet.write(z+6, 29, '', border_right)
#                     sheet.write(z+7, 29, '', border_right)
#                     sheet.write(z+8, 29, '', border_right)
#                     sheet.write(z+9, 29, '', border_right)
#                     
#                 if dys >= 30:    
#                     sheet.write(z+9, 30, '',border_bottom )
#                     
#                 if dys == 30: 
#                     sheet.write(z+3, 30, '', border_right)
#                     sheet.write(z+4, 30, '', border_right)
#                     sheet.write(z+5, 30, '', border_right)                        
#                     sheet.write(z+6, 30, '', border_right)
#                     sheet.write(z+7, 30, '', border_right)
#                     sheet.write(z+8, 30, '', border_right)
#                     sheet.write(z+9, 30, '', border_right)
#                     
#                 if dys == 31:    
#                     sheet.write(z+9, 31, '',border_bottom )
# #                     sheet.write(z+9, 32, '',border_bottom )
#                 
#                 if dys == 31: 
#                     sheet.write(z+3, 31, '', border_right)
#                     sheet.write(z+4, 31, '', border_right)
#                     sheet.write(z+5, 31, '', border_right)                        
#                     sheet.write(z+6, 31, '', border_right)
#                     sheet.write(z+7, 31, '', border_right)
#                     sheet.write(z+8, 31, '', border_right)
#                     sheet.write(z+9, 31, '', border_right)
# #                     sheet.write(z+3, 32, '', border_right)
#                 
                
                P = 0
                P_half = 0
                L = 0
                W = 0
                A = 0
                
                col = 1 
                cr.execute("""
                        select period_date::date from generate_series('"""+(tsheet.period_start_dt)+"""', 
                          '"""+(tsheet.period_end_dt)+"""', '1 day'::interval) period_date
                        """)

                for r in cr.dictfetchall():
                    date = datetime.strptime(r['period_date'], '%Y-%m-%d')
                    punch_ids = punch_obj.search(cr, uid, [('punch_date','=', date),('timesheet_id','=', tsheet.id)])
                    if punch_ids: 

                        for punch in punch_obj.browse(cr, uid, punch_ids):
                            units = punch.units    
                            # Searching for Paycode in master and updating Regular and OT
                            work_hours = 0.0
                            hrot = 0.00
                            if punch.timesheet_id.employee_id.time_rule_id.ot_rule_line and punch.type != 'daily':
                                st_dt = datetime.strptime(punch.start_time, '%Y-%m-%d %H:%M:%S')
                                start_time = st_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
                                
                                # Considering only first line in OT or Regular Lines (First Line Always should be Regular)
                                for ot in punch.timesheet_id.employee_id.time_rule_id.ot_rule_line[0]:
                                    days = [str(x.name) for x in ot.weekday_ids]
                                    start_day = calendar.day_name[st_dt.weekday()]
                                    
                                    if 'All Selected' in days or start_day in days:
                                        paycode_id = ot.paycode_id.id
                                        
                                        
                                        if punch.units > ot.work_hours:
                                            work_hours = ot.work_hours
                                            hrot = punch.units - ot.work_hours
                                        
                                        else:
                                             work_hours = punch.units
                                             hrot = 0.0
                             
                            if punch.units >6:
                                    sheet.write(row, col, 'P', centre)
                                    P = P+1
                            else:
                                sheet.write(row, col, 'P1/2', centre)
                                P_half = P_half + 1
                                 
                            if punch.type == 'daily':
                                sheet.write(row, col, 'L', centre)
                                L = L+1
                                
                            if punch.start_time:
                                start_time = punch.start_time
                                start_time = datetime.strptime(start_time,'%Y-%m-%d %H:%M:%S')
                                start_time = start_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
                                sheet.write(row+1,col, start_time.strftime('%I:%M'), centre)
                                
                            if punch.end_time:
                                end_time = punch.end_time
                                end_time = datetime.strptime(end_time,'%Y-%m-%d %H:%M:%S' )
                                end_time = end_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
                                sheet.write(row+2,col, end_time.strftime('%I:%M'), centre)
                                
                            if punch.units:
                                sheet.write(row+3,col, punch.units, centre)
                                sheet.write(row+4,col, work_hours, centre)
                                sheet.write(row+5, col, hrot, centre)
                                
                    if date.weekday() == 6: 
                        sheet.write(row,col, 'W', centre)
                        W = W + 1
                        
                    if not punch_ids and not date.weekday() == 6:
                        sheet.write(row, col, 'A', centre)
                        A = A + 1
                    col = col+1        
                present = 'Present : ' +str(P)
                sheet.write(row+8, 1, present, bold_centre )   
                
                P_half = 'Half Day : ' +str(P_half)
                sheet.write(row+8, 3, P_half, bold_centre )
                
                absent = "Absent : " +str(A)
                sheet.write(row+8, 6, absent, bold_centre)
                
                leave = 'Holiday :' + str(L)
                sheet.write(row+8, 9, leave, bold_centre)
                
                week_off = "Weekly Off : " + str(W)
                sheet.write(row+8, 12, week_off, bold_centre)

                sheet.write(row+8, 15, "Days Payable : " +str(P), bold_centre)
                    
                row = row + 14
                z = z+14          
        workbook.close()   
        fp = open(datafile, 'rb')
        contents = fp.read()
        os.remove(datafile) 
        return contents  


hr_emp_timesheet()

class multi_punch(osv.osv):
    _name = "multi.punch"
     
    _columns = {
                'punch_id'  :   fields.many2one("hr.punch", "Punch ID"),
                'multi_punch_time'  :   fields.datetime("Punch Timings"),   
      
                }
    _order = "multi_punch_time"
     
multi_punch()




class hr_holidays(osv.osv):
    _inherit = "hr.holidays"
    _columns = {
                'paycode_id' :  fields.many2one('hr.pay.codes','Pay Code'),
                'units'      :  fields.float('Units') 
                }
    
    #inheritted to update the leaves in timesheet
    def holidays_confirm(self, cr, uid, ids, context=None):
        res = super(hr_holidays, self).holidays_confirm(cr, uid, ids, context)
        empSheet_obj = self.pool.get('hr.emp.timesheet')
        punch_obj = self.pool.get('hr.punch')
        for case in self.browse(cr, uid, ids):
            if case.date_from:
                cr.execute("select id from hr_emp_timesheet where '" + case.date_from +"'::date between period_start_dt and period_end_dt and employee_id = "+ str(case.employee_id and case.employee_id.id or 0))
                sheet_ids = [x[0] for x in cr.fetchall()]
    #             punch_ids = punch_obj.search(cr, uid, [('timesheet_id','in',sheet_ids)])
    #             if punch_ids:
    #                 punch_obj.write(cr, uid, punch_ids, {'units' : case.units, 
    #                                                      'paycode_id': case.paycode_id and case.paycode_id.id or False,
    #                                                      'daily_date' : case.date_from })
                vals = {
                       'units' : case.units, 
                       'paycode_id': case.paycode_id and case.paycode_id.id or False,
                       'punch_date' : case.date_from,
                       'class_id1' : case.employee_id.class_id1 and case.employee_id.class_id1.id or False,
                       'class_id2' : case.employee_id.class_id2 and case.employee_id.class_id2.id or False,
                       'class_id3' : case.employee_id.class_id3 and case.employee_id.class_id3.id or False,
                       'class_id4' : case.employee_id.class_id4 and case.employee_id.class_id4.id or False,
                       'class_id5' : case.employee_id.class_id5 and case.employee_id.class_id5.id or False,
                       'class_id6' : case.employee_id.class_id6 and case.employee_id.class_id6.id or False,
                       'class_id7' : case.employee_id.class_id7 and case.employee_id.class_id7.id or False,
                       'class_id8' : case.employee_id.class_id8 and case.employee_id.class_id8.id or False,
                       'class_id9' : case.employee_id.class_id9 and case.employee_id.class_id9.id or False,
                       'class_id10' : case.employee_id.class_id10 and case.employee_id.class_id10.id or False,
                       'timesheet_id' : sheet_ids and sheet_ids[0] or False,
                       'type' : 'daily',
                       'notes' : 'Created from Leaves'
                        }
                punch_obj.create(cr, uid, vals, context)
        
        return res
        
    #TODO : Refusing the holidays
    def holidays_refuse(self, cr, uid, ids, context=None):
        punch_obj = self.pool.get('hr.punch')
        res = super(hr_holidays, self).holidays_refuse(cr, uid, ids, context)
        for case in self.browse(cr, uid, ids):
            if case.date_from:
                cr.execute("select id from hr_emp_timesheet where '" + case.date_from +"'::date between period_start_dt and period_end_dt and employee_id = "+ str(case.employee_id and case.employee_id.id or 0))
                sheet_ids = [x[0] for x in cr.fetchall()]
                cr.execute("select id from hr_punch where punch_date ='" + case.date_from + "'::date and timesheet_id in %s",(tuple(sheet_ids),))
                punch_ids = [x[0] for x in cr.fetchall()]
                punch_obj.unlink(cr, uid, punch_ids, context)
        return res
        
hr_holidays()


class ir_rule(osv.osv):
    _inherit = 'ir.rule'
    
    def get_user_status(self, cr, uid, ids, context=None):
        
        """ To check the user whether supervisor or manager 
        @return - True if supervisor else False
        """
        context = dict(context or {})
        user_obj = self.pool.get('res.users')
        emp_obj = self.pool.get('hr.employee')
        
        cr.execute("""
                select e.id
                   from hr_employee e 
                   inner join resource_resource r on r.id = e.resource_id
                   inner join res_users ru on ru.id =  r.user_id
                   inner join hr_employee e1 on e1.parent_id = e.id
                   and ru.id = """ + str(uid)
                   )
        user_ids = [x[0] for x in cr.fetchall()]
        if user_ids :
            return True
        
        return False
    
    def class_domain(self, cr, uid, context=None):
        """ to get the domian based on the class mappings"""
        
        vals = []
        for r in range(1, 11):
            cr.execute("select class_id from users_class"+str(r)+"_rel where uid="+str(uid))
            data = [x[0] for x in cr.fetchall()]
            
            if data:
                if context.get('src_model_name') == 'hr.employee':
                    vals.append(('class_id'+str(r), 'in', data))
                else:
                    vals.append(('employee_id.class_id'+str(r), 'in', data))
                    
            
#         cr.execute("select class_id from users_class1_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             if context.get('src_model_name') == 'hr.employee':
#                 vals.update({'class_id1':data})
#             else:
#                 vals.update({'employee_id.class_id1':data})
            

        
#         cr.execute("select class_id from users_class2_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id2':data})
#         
#         cr.execute("select class_id from users_class3_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id3':data})
#         
#         cr.execute("select class_id from users_class4_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id4':data})
#         
#         cr.execute("select class_id from users_class5_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id5':data})
#     
#         cr.execute("select class_id from users_class6_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id6':data})
#         
#         cr.execute("select class_id from users_class7_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id7':data})
#         
#         cr.execute("select class_id from users_class8_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id8':data})
#         
#         
#         cr.execute("select class_id from users_class9_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id9':data})
#     
#         cr.execute("select class_id from users_class10_rel where uid="+str(uid))
#         data = [x[0] for x in cr.fetchall() ]
#         if data:
#             vals.update({'class_id10':data})
        
        
        if vals:
            return vals
        
        return False
    
    #overidden
    def domain_get(self, cr, uid, model_name, mode='read', context=None):
        context = dict(context or {})
        dom = self._compute_domain(cr, uid, model_name, mode)
        if dom:
            if model_name in ('hr.employee', 'hr.holidays', 'hr.emp.timesheet'):
                # to check for the manager 
                cr.execute(""" select distinct uid
                                    from res_groups_users_rel gu 
                                    inner join res_groups g on g.id = gu.gid
                                    inner join res_users ru on ru.id = gu.uid
                                    inner join res_partner rp on rp.id = ru.partner_id
                                    where g.name = 'Manager' and uid = """ + str(uid) +"""
                                    and g.category_id = (select id from ir_module_category where name = 'Praxis HR')
                                    """)
                user_ids = [x[0] for x in cr.fetchall()]
                
                if uid in user_ids:
                    res = self.get_user_status(cr, uid, [], context)
                    if res:
                        # if the user is supervisor 
                        if model_name == 'hr.employee':
                            dom = ['|',('parent_id.user_id','=',uid),('user_id','=',uid)]
                        else:
                            dom = ['|',('employee_id.user_id','=',uid),('employee_id.parent_id.user_id','=',uid)]
                    else:
                        #if users 
                        context.update({'src_model_name':model_name})
                        domain = self.class_domain(cr, uid, context)
                        if domain:
                            dom = domain
                           
                            
                
            # _where_calc is called as superuser. This means that rules can
            # involve objects on which the real uid has no acces rights.
            # This means also there is no implicit restriction (e.g. an object
            # references another object the user can't see).
            query = self.pool[model_name]._where_calc(cr, SUPERUSER_ID, dom, active_test=False)
            return query.where_clause, query.where_clause_params, query.tables
        return [], [], ['"' + self.pool[model_name]._table + '"']
    
ir_rule()


class hr_audit(osv.osv):
    _description = "Hr Audit"
    _name = 'hr.audit'
    _columns = {
                'change_time'   : fields.datetime('Change Date'),
                'user_id'       : fields.many2one('res.users','User'),
                'event_type'    : fields.selection([('create','Create'),('edit','Edit'),('delete','Delete')],'Event Type'),
                'column_name'   : fields.char('Column Name'),
                'original_value' : fields.char('Original Value'),
                'new_value'      : fields.char('New Value'),
                'punch_date'     : fields.date('Punch Date'),
                'timesheet_id'   : fields.many2one('hr.emp.timesheet','Time Sheet')
                }
hr_audit()
                
                


    