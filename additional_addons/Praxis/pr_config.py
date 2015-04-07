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

_logger = logging.getLogger(__name__)


class hr_salutation(osv.osv):
    _name = 'hr.salutation'
    _description = "Salutation"
    
    _columns =  {
                 'name'  : fields.char('Name')
                 }
hr_salutation()

class hr_ethnic_origin(osv.osv):
    _name = 'hr.ethnic.origin'
    _description = "Ethnic Origin"
    _columns = {
                'name' : fields.char('Name')
                }

hr_ethnic_origin()

class hr_employee_type(osv.osv):
    _name  = 'hr.employee.type'
    _description = 'Employee Type'
    
    _columns = {
                'name'  : fields.char('Name')
                }
    
hr_employee_type()

class hr_job_description(osv.osv):
    _name = 'hr.job.desc'
    _description = 'Job Description'
    _columns = {
                'name'  : fields.char('Name')
                }
hr_job_description()

class hr_job_code(osv.osv):
    _name = 'hr.job.code'
    _description = 'Job Code'
    _columns = {
                'name'  : fields.char('Name')
                }
hr_job_code()

class hr_pay_group(osv.osv):
    _name = 'hr.pay.group'
    _description = 'Pay Group'
    _columns = {
                'name'  : fields.char('Name')
                }
hr_pay_group()


class hr_shift(osv.osv):
    _name = 'hr.shift'
    _description = 'Shifts'
    _columns = {
                'name'  : fields.char('Name')
                }
hr_shift()



class hr_class1(osv.osv):
    _name = 'hr.class1'
    _description = 'Class1'
    _columns = {
                'name'  : fields.char('Name')
                 }
hr_class1()


class hr_class2(osv.osv):
    _name = 'hr.class2'
    _description = 'Class2'
    _columns = {
                'name'  : fields.char('Name'),
                'class_id' : fields.many2one('hr.class1','Class 1')
                 }
hr_class2()


class hr_class3(osv.osv):
    _name = 'hr.class3'
    _description = 'Class3'
    _columns = {
                'name'  : fields.char('Name'),
                'class_id' : fields.many2one('hr.class2','Class 2')
                 }
hr_class3()


class hr_class4(osv.osv):
    _name = 'hr.class4'
    _description = 'Class4'
    _columns = {
                'name'  : fields.char('Name'),
                'class_id' : fields.many2one('hr.class3','Class 3')
                 }
hr_class4()


class hr_class5(osv.osv):
    _name = 'hr.class5'
    _description = 'Class5'
    _columns = {
                'name'  : fields.char('Name'),
                'class_id' : fields.many2one('hr.class4','Class 4')
                 }
hr_class5()


class hr_class6(osv.osv):
    _name = 'hr.class6'
    _description = 'Class6'
    _columns = {
                'name'  : fields.char('Name'),
                'class_id' : fields.many2one('hr.class5','Class 5')
                 }
hr_class6()


class hr_class7(osv.osv):
    _name = 'hr.class7'
    _description = 'Class7'
    _columns = {
                'name'  : fields.char('Name'),
                'class_id' : fields.many2one('hr.class6','Class 6')
                 }
hr_class7()


class hr_class8(osv.osv):
    _name = 'hr.class8'
    _description = 'Class8'
    _columns = {
                'name'  : fields.char('Name'),
                'class_id' : fields.many2one('hr.class7','Class 7')
                 }
hr_class8()


class hr_class9(osv.osv):
    _name = 'hr.class9'
    _description = 'Class9'
    _columns = {
                'name'  : fields.char('Name'),
                'class_id' : fields.many2one('hr.class8','Class 8')
                 }
hr_class9()


class hr_class10(osv.osv):
    _name = 'hr.class10'
    _description = 'Class10'
    _columns = {
                'name'  : fields.char('Name'),
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