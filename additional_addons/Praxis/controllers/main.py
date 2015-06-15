# coding: utf-8
from openerp.http import request
import simplejson
from openerp import http
import jinja2
import openerp
import operator
from openerp.tools.translate import _
import itertools
import os
import glob
import werkzeug.utils
import werkzeug.wrappers
# from authy.api import AuthyApiClient
from openerp.modules.registry import RegistryManager
from openerp import SUPERUSER_ID
from datetime import datetime
import re
from openerp.http import request, serialize_exception as _serialize_exception
from openerp.addons import web
import time
from openerp.addons.web.controllers import main as web_main
import base64
import socket
# import dns.resolver

env = jinja2.Environment(
    loader=jinja2.PackageLoader('openerp.addons.web', "views"),
    autoescape=True
)
env.filters["json"] = simplejson.dumps
import logging
_logger = logging.getLogger(__name__)


class Reports(openerp.addons.web.controllers.main.Reports):
    POLLING_DELAY = 0.25
    TYPES_MAPPING = {
        'doc': 'application/vnd.ms-word',
        'html': 'text/html',
        'odt': 'application/vnd.oasis.opendocument.text',
        'pdf': 'application/pdf',
        'sxw': 'application/vnd.sun.xml.writer',
        'xls': 'application/vnd.ms-excel',
    }

    @http.route('/web/report', type='http', auth="user")
    @web_main.serialize_exception
    def index(self, action, token):
        cr, uid, suid = request.cr, request.session.uid, openerp.SUPERUSER_ID
        action = simplejson.loads(action)

        report_srv = request.session.proxy("report")
        context = dict(request.context)
        context.update(action["context"])

        report_data = {}
        report_ids = context.get("active_ids", None)
        if 'report_type' in action:
            report_data['report_type'] = action['report_type']
        if 'datas' in action:
            if 'ids' in action['datas']:
                report_ids = action['datas'].pop('ids')
            report_data.update(action['datas'])

        report_id = report_srv.report(
            request.session.db, request.session.uid, request.session.password,
            action["report_name"], report_ids,
            report_data, context)

        report_struct = None
        while True:
            report_struct = report_srv.report_get(
                request.session.db, request.session.uid, request.session.password, report_id)
            if report_struct["state"]:
                break

            time.sleep(self.POLLING_DELAY)

        report = base64.b64decode(report_struct['result'])
        if report_struct.get('code') == 'zlib':
            report = zlib.decompress(report)
        report_mimetype = self.TYPES_MAPPING.get(
            report_struct['format'], 'octet-stream')
        file_name = action.get('name', 'report')
        if 'name' not in action:
            reports = request.session.model('ir.actions.report.xml')
            res_id = reports.search([('report_name', '=', action['report_name']),],
                                    0, False, False, context)
            if len(res_id) > 0:
                file_name = reports.read(res_id[0], ['name'], context)['name']
            else:
                file_name = action['report_name']
        file_name = '%s.%s' % (file_name, report_struct['format'])
        
        # Customized to execute an excel report instead of dummy penthao report(sale sumary)
        if action['report_name'] == 'test':
            ts_obj = request.session.model('hr.emp.timesheet')
            print 'Report data............', report_data, action
            file_name = 'test.xlsx'
            #report = ss_obj.generate_xls(cr, uid, action['datas'])
            report = ts_obj.get_file(report_data)
            report_mimetype = 'application/vnd.ms-excel'
            #
                
        return request.make_response(report,
             headers=[
                 ('Content-Disposition', web_main.content_disposition(file_name)),
                 ('Content-Type', report_mimetype),
                 ('Content-Length', len(report))],
             cookies={'fileToken': token})
        
        