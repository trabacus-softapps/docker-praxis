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
    
    def _class_id_get(self, cr, uid, context=None):
        mapping_obj = self.pool.get('hr.class.mapping')
        result = []
        for m in mapping_obj.browse(cr, uid, mapping_obj.search(cr, uid, [])):
            result.append((m.name[:-1] + '_id'+ m.name[-1:], m.label))
        return result
    
    def _get_default_class(self, cr, uid, fields, context=None):
        result = {}
        mapping_obj = self.pool.get('hr.class.mapping')
        map_ids = mapping_obj.search(cr, uid, [])
        if map_ids :
            for m in mapping_obj.browse(cr, uid,map_ids[0]):
                return (m.name[:-1] + '_id'+ m.name[-1:])
        return result
        
    
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
                'timegroup_id'     : fields.many2one('hr.time.rule','Time Rule'),
                'pri_supervisor'   : fields.boolean('Primary Supervisor'),
                'supervisor_id'    : fields.many2one('hr.employee','Supervisor'),
                'employee_ids'     : fields.many2many('hr.employee','report_employee_rel','report_id','employee_id',"Employee's"),
                'active'           : fields.boolean('Active'),
                'inactive'         : fields.boolean('In Active'),
                'loa'              : fields.boolean('LOA'),
                'pay_period'       : fields.selection([('current','Current Pay Period'),('next','Next Pay Period'),('range','Date Range')],'Pay Period'),
                'start_date'       : fields.date('From'),
                'end_date'         : fields.date('To'),
                'report_id'        : fields.many2one('ir.actions.report.xml','Report'),
                'emp_sort'         : fields.selection([('emp_no','Employee Number'),('emp_name','Employee Name')],'Sort By'),
                'emp_group_by'     : fields.selection(_class_id_get, 'Group By'),
                }
    _defaults = {
                 'pay_period' : 'current',
                 'active'  : True,
                 'emp_sort' : 'emp_name',
                 'emp_group_by' : _get_default_class,
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
        mapping_obj = self.pool.get("hr.class.mapping")
        group_by = '' 
        sort_by = ''
        order = ''
        cond = ''
        
        for case in self.browse(cr, uid, ids):
            report_name = ''
            name = ''
            data = {}
            sale_obj = self.pool.get("sale.order")
            
           
            
            report_name = case.report_id.name
            data['model'] = context.get('hr.emp.timesheet', 'ir.ui.menu')
            condition = []
            
            for r in range(1, 11):
                if case['class_id'+str(r)]:
                    condition.append(('employee_id.class_id'+str(r),'=',case['class_id'+str(r)].id))
            
            if case.paygroup_id :
                condition.append(('employee_id.pay_group_id','=',case.paygroup_id.id))
            
            if case.timegroup_id :
                condition.append(('employee_id.time_rule_id','=',case.timegroup_id.id))
                
            if case.supervisor_id :
                condition.append(('employee_id.parent_id','=',case.supervisor_id.id))
                
            if case.employee_ids:
                condition.append(('employee_id','in',[x.id for x in case.employee_ids]))
            
            
            
            
            if case.pay_period == 'current':
                condition.extend([('period_start_dt','<=',punch_date),('period_end_dt','>=',punch_date)])
                start_date = today.replace(day=1).strftime('%Y-%m-%d')
                end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1]).strftime('%Y-%m-%d')
                
            
            elif case.pay_period == 'next':
                punch_date = today + relativedelta(months=1)
                start_date = punch_date.replace(day=1).strftime('%Y-%m-%d')
                end_date = punch_date.replace(day=calendar.monthrange(punch_date.year, punch_date.month)[1]).strftime('%Y-%m-%d')
                
                condition.extend([('period_start_dt','<=',punch_date.strftime('%Y-%m-%d')),('period_end_dt','>=',punch_date.strftime('%Y-%m-%d'))])
            
            else:
                if case.report_id.name != 'Late In Early Out':
                    condition.extend([('period_start_dt','>=',case.start_date),('period_end_dt','<=',case.end_date)])
                    start_date = case.start_date
                    end_date = case.end_date
                
                else:
                    case.report_id.name == 'Late In Early Out'
                    st_dt = datetime.strptime(case.start_date, '%Y-%m-%d')
                    from_date = st_dt.replace(day=1).strftime('%Y-%m-%d')
                    to_date = st_dt.replace(day=calendar.monthrange(st_dt.year, st_dt.month)[1]).strftime('%Y-%m-%d')
                    
                    condition.extend([('period_start_dt','>=',from_date),('period_end_dt','>=',to_date)])
                    start_date = case.start_date
                    end_date = case.end_date
             
            
            
            if case.emp_group_by:
                order = 'employee_id.'+case.emp_group_by + ' asc'
                
            
            if case.emp_sort :
                sort_by = 'employee_id.'+case.emp_sort + ' asc'
                if order :
                    order = order + sort_by
                else:
                    order = sort_by
            
            sheet_ids = ts_obj.search(cr , uid, condition)
                    
            
            select = """
            select 
                  t.id as ts_id
                , h.id 
                , h.name_related as emp_name
                , h.identification_id as emp_no
            """
            
            join = """
                    from hr_employee h 
                    inner join resource_resource r on r.id = h.resource_id
                    inner join hr_emp_timesheet t on t.employee_id = h.id """
            
            if len(sheet_ids) > 1:
                cond = """ where t.id in """+ str(tuple(sheet_ids))
            else:
                cond = """ where t.id in ("""+ str(sheet_ids[0]) + """)"""
            
            sheet_ids= []
                    
            map_label = ''
            if  case.emp_group_by:
                select = select + ",c.id as class_id , c.name as class_name"
                join = join + """ left outer join hr_"""+case.emp_group_by.replace('_id','')+" c on c.id = h."+case.emp_group_by
                cond = cond + " order by class_id"
                
                label = str(case.emp_group_by.replace('_id',''))
                map_ids =  mapping_obj.search(cr, uid, [('name','=',label)])
                
                if map_ids:
                    map = mapping_obj.browse(cr, uid, map_ids)
                    map_label = map.label
            
            if case.emp_sort:
                cond = cond + ","+ case.emp_sort if 'order' in cond else  cond+ " order by "+ case.emp_sort
                
            
            sqlstr = select + str(join) + str(cond)
            print "sqlstr", sqlstr
            
            cr.execute(sqlstr)
            for c in cr.fetchall():
                sheet_ids.append(c[0])
                


            data['variables'] = {
                                 'sheet_ids' : sheet_ids ,
                                 'start_date' : start_date,
                                 'end_date'   : end_date,
                                 'emp_group_by' : case.emp_group_by or '',
                                 'emp_sort_by' : case.emp_sort or '',
                                 'groupby_label' : map_label or '',
                                 # for Late In Early Out Report
                                 'tsheet_ids' : str(sheet_ids)[1:-1],
                                 
                                 }
            
            data['ids'] = context.get('active_ids',[])
        
        return {
        'type': 'ir.actions.report.xml',
        'report_name': report_name,
        'name' : report_name,
        'datas': data,
            }
        
    
    
pr_report_wiz()
