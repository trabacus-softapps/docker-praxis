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
import re
from lxml import etree
from openerp.osv.orm import setup_modifiers

class pr_report_wiz(osv.osv_memory):
    _name = 'pr.report.wiz'
    _columns = {
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
                'paygroup_id'      : fields.many2one('hr.pay.group','Pay Group'),
                'timegroup_id'     : fields.many2one('hr.time.rule','Time Group'),
                'pri_supervisor'   : fields.boolean('Primary Supervisor'),
                'supervisor_id'    : fields.many2one('hr.employee','Supervisor'),
                'employee_id'      : fields.many2many('hr.employee','report_employee_rel','report_id','employee_id',"Employee's"),
                'active'           : fields.boolean('Active'),
                'terminated'       : fields.boolean('Terminated'),
                'loa'              : fields.boolean('LOA'),
                'pay_period'       : fields.selection([('current','Current Pay Period'),('next','Next Pay Period'),('range','Date Range')],'Pay Period'),
                'start_date'       : fields.date('From'),
                'end_date'         : fields.date('To'),
                'report_id'        : fields.many2one('ir.actions.report.xml','Report'),
                }
    _defaults = {
                 'pay_period' : 'current'
                 }
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """
            Add Dynamic Labels based on the class Mappings
        """
        mapping_obj = self.pool.get('hr.class.mapping')
        if not context: context = {}
        res = super(pr_report_wiz, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
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
    
    def print_report(self, cr, uid, ids, context=None):
        today =datetime.now()
        punch_date = today.strftime('%Y-%m-%d')
        ts_obj = self.pool.get('hr.emp.timesheet') 
        
        for case in self.browse(cr, uid, ids):
            report_name = ''
            name = ''
            data = {}
            sale_obj = self.pool.get("sale.order")
            report_name = 'test'
            data['model'] = context.get('hr.emp.timesheet', 'ir.ui.menu')
            condition = []
            
            
            
            if case.pay_period == 'current':
                sheet_ids = ts_obj.search(cr , uid, [('period_start_dt','<=',punch_date),('period_end_dt','>=',punch_date)]) 
            
            data['variables'] = {
                                 'sheet_ids' : sheet_ids ,
                                 }
            
            data['ids'] = context.get('active_ids',[])
        
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : name,
        'datas': data,
            }
        
    
    
pr_report_wiz()
