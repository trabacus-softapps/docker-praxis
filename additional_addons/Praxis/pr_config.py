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

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

_logger = logging.getLogger(__name__)


class hr_salutation(osv.osv):
    _name = 'hr.salutation'
    _description = "Salutation"
    
    _columns =  {
                 'code'  : fields.char('Code'),
                 'name'  : fields.char('Description')
                 }
hr_salutation()

class hr_ethnic_origin(osv.osv):
    _name = 'hr.ethnic.origin'
    _description = "Ethnic Origin"
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description')
                }

hr_ethnic_origin()

class hr_employee_type(osv.osv):
    _name  = 'hr.employee.type'
    _description = 'Employee Type'
    
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description')
                }
    
hr_employee_type()

class hr_job_description(osv.osv):
    _name = 'hr.job.desc'
    _description = 'Job Description'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description')
                }
hr_job_description()

class hr_job_code(osv.osv):
    _name = 'hr.job.code'
    _description = 'Job Code'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description')
                }
hr_job_code()

class hr_pay_group(osv.osv):
    _name = 'hr.pay.group'
    _description = 'Pay Group'
    
    def get_next_dates(self, cr, uid, ids, field_name, args, context=None):
        """ To Calculate the dates based on period start Date
        
        input : period_start_dt : '2015-04-05'
        outputs: period_end_dt : '2015-04-30'
                 next_start_dt :  '2015-05-01'
                 next_end_dt   :  '2015-05-31'
        """
        res = {}
        for case in self.browse(cr, uid, ids):
            res[case.id]={
                          'period_end_dt': False,
                          'next_start_dt': False,
                          'next_end_dt'  : False,
                          }
            if case.period_start_dt:
                period_date = datetime.strptime(case.period_start_dt, '%Y-%m-%d')
                period_end_dt = period_date.replace(day = calendar.monthrange(period_date.year, period_date.month)[1])
                next_start_dt = period_end_dt + relativedelta(days = 1)
                
                res[case.id]['period_end_dt'] = period_end_dt
                res[case.id]['next_start_dt'] = next_start_dt
                res[case.id]['next_end_dt'] = next_start_dt.replace(day = calendar.monthrange(next_start_dt.year, next_start_dt.month)[1])
                
            
        return res
    
    _columns = {
                'code'         : fields.char('Code'),
                'name'         : fields.char('Description'),
                'period_start_dt' : fields.date('Period Start'),
                'period_end_dt'   : fields.function(get_next_dates, string='Period End', type='date', multi="all"),
                'next_start_dt'   : fields.function(get_next_dates, string='Next Start', type='date',  multi="all"),
                'next_end_dt'     : fields.function(get_next_dates, string='Next End', type='date',  multi="all"),
                'start_week'   : fields.selection([('sun','Sunday'),('mon','Monday'),('tue','Tuesday'),
                                                   ('wed','Sunday'),('thu','Thursday'),('fri','Friday'),
                                                   ('sat','Saturday')], 'Start Week'),
                 
                }
    
    def roll_overpay(self, cr, uid, ids, context=None):
        """ To Update the period start date with next start date"""
        for case in self.browse(cr, uid, ids):
            self.write(cr, uid, [case.id], {'period_start_dt':case.next_start_dt}, context)
        return True
    
hr_pay_group()

class hr_pay_codes(osv.osv):
    _name = 'hr.pay.codes'
    _description = "Pay Codes"
    _columns = {
                'code'         : fields.char('Code'),
                'name'         : fields.char('Description'),
                'post_code'    : fields.char('Postcode'),
                'category'     : fields.selection([('hours_worked','Hours Worked'),('attendance','Attendance'),
                                                   ('on_call','On Call'),('mileage','Mileage'),('unpaid','UnPaid')],'Category'),
                'emp_calc'     : fields.selection([('pay_hour','Pay Hours'),('flat_amount','Flat Amount'),
                                                   ('quantity','Quantity')],'Employee Calc Method'),
                'rate'         : fields.float('Rate'),
                'active'       : fields.boolean('Active')    
                }
hr_pay_codes()

class hr_rounding(osv.osv):
    _name = 'hr.rounding'
    _description = 'Hr Rounding'
    _columns = {
                'code'         : fields.char('Code'),
                'name'         : fields.char('Description'),
                'clock1'       : fields.selection([('clock_in','Clock In'),('clock_out','Clock Out')],'Clock1'),
                'clock2'       : fields.selection([('clock_in','Clock In'),('clock_out','Clock Out')],'Clock2'),
                'type1'        : fields.selection([('round_forward','Round Forward'),('round_back','Round Back'),
                                                   ('round_near','Round Nearest')],'Type1'),
                'type2'        : fields.selection([('round_forward','Round Forward'),('round_back','Round Back'),
                                                   ('round_near','Round Nearest')],'Type2'),
                'hours1'       : fields.char('Hours1'),
                'hours2'       : fields.char('Hours1'),
                }
    _defaults = {
                 'clock1'  : 'clock_in',
                 'clock2'  : 'clock_out'
                 }
hr_rounding()

class hr_lunch(osv.osv):
    _name = 'hr.lunch'
    _description = 'Hr Lunch Details'
    _columns = {
                'code'             : fields.char('Code'),
                'name'             : fields.char('Description'),
                'lunch_hours'      : fields.integer('Standard Lunch of'),
                'after_work_hour'  : fields.integer('After'),
                'automatic'        : fields.boolean('Automatic'),
                'paid_by_employer' : fields.boolean('Paid by Employer'),
                'post'             : fields.boolean('Post as Separate Pay Code'),
                'paycode_id'       : fields.many2one('hr.pay.codes', 'Pay Code')
                }
hr_lunch()

class hr_emp_holiday(osv.osv):
    _name = 'hr.emp.holiday'
    _columns = {
                'code'    : fields.char('Code'),
                'name'    : fields.char('Description'),
                'date'    : fields.date('Date'),
                'min_days_employed' : fields.integer('Minimum Days Employeed'),
                'hours'   : fields.float('Hours'),
                'paycode_id' : fields.many2one('hr.pay.codes', 'Pay Code'),
                'pay_holiday' : fields.selection([('work_day_bef','Work Day Before'),('work_day_aft','Work Day After'),
                                                  ('work_day_bef_aft','Work Day Before or After')
                                                  ,('work_day_aft_bef','Work Day Before and After')],'Pay Holiday when'),
                'recurring' : fields.boolean('Recurring'),    
                }
hr_emp_holiday()



class hr_shift(osv.osv):
    _name = 'hr.shift'
    _description = 'Shifts'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description')
                }
hr_shift()



class hr_class1(osv.osv):
    _name = 'hr.class1'
    _description = 'Class1'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description')
                 }
    
#     def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
#         ids = []
#         if name:
#             ids = self.search(cr, uid, [('name','ilike',name)]+ args, limit=limit, context=context)
#         if not ids:
#             ids = self.search(cr, uid, [('code','ilike',name)]+ args, limit=limit, context=context)
#         result = self.name_get(cr, uid, ids, context=context)
#         return result
hr_class1()


class hr_class2(osv.osv):
    _name = 'hr.class2'
    _description = 'Class2'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class1','Class 1')
                 }
hr_class2()


class hr_class3(osv.osv):
    _name = 'hr.class3'
    _description = 'Class3'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class2','Class 2')
                 }
hr_class3()


class hr_class4(osv.osv):
    _name = 'hr.class4'
    _description = 'Class4'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class3','Class 3')
                 }
hr_class4()


class hr_class5(osv.osv):
    _name = 'hr.class5'
    _description = 'Class5'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class4','Class 4')
                 }
hr_class5()


class hr_class6(osv.osv):
    _name = 'hr.class6'
    _description = 'Class6'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class5','Class 5')
                 }
hr_class6()


class hr_class7(osv.osv):
    _name = 'hr.class7'
    _description = 'Class7'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class6','Class 6')
                 }
hr_class7()


class hr_class8(osv.osv):
    _name = 'hr.class8'
    _description = 'Class8'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class7','Class 7')
                 }
hr_class8()


class hr_class9(osv.osv):
    _name = 'hr.class9'
    _description = 'Class9'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class8','Class 8')
                 }
hr_class9()


class hr_class10(osv.osv):
    _name = 'hr.class10'
    _description = 'Class10'
    _columns = {
                'code'  : fields.char('Code'),
                'name' : fields.char('Description'),
                'class_id' : fields.many2one('hr.class9','Class 9')
                 }
hr_class10()


class hr_class_mapping(osv.osv):
    _name = 'hr.class.mapping'
    _description = 'Mapping'
    _columns = {
                'name'  : fields.selection([('class1','Class 1'),('class2','Class 2'),('class3','Class 3'),
                                            ('class4','Class 4'),('class5','Class 5'),('class6','Class 6'),
                                            ('class7','Class 7'),('class8','Class 8'),('class9','Class 9'),
                                            ('class10','Class 10')],'Class'),
                'label' : fields.char('Label'),
                
                }

hr_class_mapping()