# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp.tools.translate import _
from lxml import etree
from openerp.osv.orm import setup_modifiers
import re
from openerp import SUPERUSER_ID

class res_users(osv.osv):
    _inherit = 'res.users'
    
    
    #inheitted to populate default user group for Employee
    def _get_group(self,cr, uid, context=None):
        data_obj = self.pool.get('ir.model.data')
        res = super(res_users, self)._get_group(cr, uid, context)
        print res
        try:
            dummy, groupid = data_obj.get_object_reference(cr, SUPERUSER_ID, 'Praxis', 'group_praxis_user')
            res.append(groupid)
        except ValueError:
            # If these groups does not exists anymore
            pass
              
        return res
    
    
    
    _columns = {
            'class_ids1'        : fields.many2many('hr.class1','users_class1_rel','uid','class_id','Class1'),
            'class_ids2'        : fields.many2many('hr.class2','users_class2_rel','uid','class_id','Class2'),
            'class_ids3'        : fields.many2many('hr.class3','users_class3_rel','uid','class_id','Class3'),
            'class_ids4'        : fields.many2many('hr.class4','users_class4_rel','uid','class_id','Class4'),
            'class_ids5'        : fields.many2many('hr.class5','users_class5_rel','uid','class_id','Class5'),
            'class_ids6'        : fields.many2many('hr.class6','users_class6_rel','uid','class_id','Class6'),
            'class_ids7'        : fields.many2many('hr.class7','users_class7_rel','uid','class_id','Class7'),
            'class_ids8'        : fields.many2many('hr.class8','users_class8_rel','uid','class_id','Class8'),
            'class_ids9'        : fields.many2many('hr.class9','users_class9_rel','uid','class_id','Class9'),
            'class_ids10'       : fields.many2many('hr.class10','users_class10_rel','uid','class_id','Class10'),
            'confirm_password'  : fields.char('Confirm Password', size=256)
            }
    
    _defaults = {
                 'groups_id'      : _get_group
                 }
            
            
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        """
            Add Dynamic Labels based on the class Mappings
        """
        mapping_obj = self.pool.get('hr.class.mapping')
        if not context: context = {}
        res = super(res_users, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form' :
            doc = etree.XML(res['arch'])
            for m in mapping_obj.browse(cr, uid, mapping_obj.search(cr, uid, [])):
                nodes = doc.xpath("//field[@name='"+m.name[0:5]+'_ids'+m.name[5:]+"']")
                for node in nodes:
                    node.set('invisible', '0')
                    node.set('string', m.label)
                    setup_modifiers(node, res['fields'][m.name[0:5]+'_ids'+m.name[5:]])
                     
            res['arch'] = etree.tostring(doc)
        return res
    
#     def create(self, cr, uid, vals, context=None):
#         context = dict(context or {})
#         
#         if vals.get('password') != vals.get('confirm_password'):
#             raise osv.except_osv(_('Warning!'), _('Password Mismatch'))
#         
#         return super(res_user, self).create(cr, uid, vals, context=context)
# 
#     def write(self, cr, uid, ids, vals, context=None):
#         context = dict(context or {})
#          
#         for case in self.browse(cr, uid, ids):
#             if vals.get('password',case.password) != vals.get('confirm_password', case.confirm_password):
#                raise osv.except_osv(_('Warning!'), _('Password Mismatch'))
#         
#         return super(res_users, self).write(cr, uid, ids, vals, context)
         
             
    

        
            
res_users()
    