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

_logger = logging.getLogger(__name__)



class hr_employee(osv.osv):
    _inherit = "hr.employee"
    
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """
            Add Dynamic Labels based on the class Mappings
        """
        mapping_obj = self.pool.get('hr.class.mapping')
        if not context: context = {}
        res = super(hr_employee, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='class_id1']")
        if view_type == 'form' :
            for m in mapping_obj.browse(cr, uid, mapping_obj.search(cr, uid, [])):
                nodes = doc.xpath("//field[@name='"+m.name[0:5]+'_id'+m.name[5:]+"']")
                for node in nodes:
                    print "inside Nodes", 1, m.name[0:5]+'_id'+m.name[5:], m.label
                    node.set('invisible', '0')
                    node.set('string', m.label)
                    setup_modifiers(node, res['fields'][m.name[0:5]+'_id'+m.name[5:]])
                    
            res['arch'] = etree.tostring(doc)
        return res
    
    
    _columns = {
                'org_hire_date'     : fields.date('Original Hire Date'),
                'last_hire_date'    : fields.date('Last Hire Date'),
                'adj_sen_date'      : fields.date('Adjusted Seniority Date'),
                'job_start_date'    : fields.date('Job Start Date'),
                'badge'             : fields.char('Badge'),
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
                'identification_id' : fields.char('Employee Number'),
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
                'no_of_hours'      : fields.float('Hours/Units'),
                'unit_pay_rate'    : fields.float('Unit Pay Rate'),
                'pay_period_sal'   : fields.float('Pay Period Salary'),
                'monthly_pay'      : fields.float('Monthly Pay'),
                'annual_pay'       : fields.float('Annual Pay'),
                'pay_group_id'     : fields.many2one('hr.pay.group','Pay Group')
                  
                
                
                }
    
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
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('birthday',False):
            vals.update({'age' : self.get_age(cr, vals.get('birthday'))})
        return super(hr_employee, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('birthday',False):
            vals.update({'age' : self.get_age(cr, vals.get('birthday'))})
        return super(hr_employee, self).write(cr, uid, ids, vals, context) 

hr_employee()
    