import time
import datetime
from dateutil.relativedelta import relativedelta

from openerp import tools
from openerp.osv import fields,osv


def _time_get(self, cr, uid, context=None):
    selection = []
    selection[('m1',' Before 9'), ('m2', '9:00 to 9:30'), 
                     ('m3','9:30 to 10:00'), ('m4','10:00 to 11:00'), 
                     ('m5','After 11')]
    return selection


class report_time_analysis(osv.osv):
    _name = "report.time.analysis"
    _description = "In Time Analysis"
    _auto = False
    _columns = {
        'name': fields.selection([('Before 9',' Before 9'), ('9:00 - 9:30', '9:00 to 9:30'), 
                     ('9:30 - 10:30','9:30 to 10:00'), ('10:00 - 11:00','10:00 to 11:00'), 
                     ('After 11','After 11')], readonly=True),
        #'type': fields.selection(_time_get, 'Time Interval', required=True),
        'measure':fields.integer('Measure', readonly=True),
       
    }
    _order = 'name'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_time_analysis')
        cr.execute("""
            create or replace view report_time_analysis as (
                 select min(id) as id
                , case when measure::int = 1 then 'Before 9' else
                  case when a.measure::int = 2 then '9:00 - 9:30' else
                  case when a.measure::int = 3 then '9:30 - 10:30' else
                  case when a.measure::int = 4 then '10:00 - 11:00' else 'After 11' end end end end as name
                , count(a.measure)::integer as measure
            
            from    
            
            (    select 
                      punch_date
                    , id 
                    , timesheet_id
                    , start_time at time zone 'UTC+5:30'
                    , start_time
                    , end_time at time zone 'UTC+5:30' 
                    , end_time
                    , case when start_time at time zone 'UTC+5:30' between now()::date + time '08:00' and now()::date + time '09:00' then 1 else
                      case when start_time at time zone 'UTC+5:30' between now()::date + time '09:00' and now()::date + time '09:30' then 2 else
                      case when start_time at time zone 'UTC+5:30' between now()::date + time '09:30' and now()::date + time '10:00' then 3 else
                      case when start_time at time zone 'UTC+5:30' between now()::date + time '10:00' and now()::date + time '11:00' then 4 else 5
                      end end end end as measure
                from hr_punch where punch_date = now()::date
                order by measure
            )a
            group by a.measure , name
            
            )""")
        
        
class avg_work_hours(osv.osv):
    _name = "avg.work.hours"
    _description = "Average Work Hours"
    _auto = False
    _columns = {
        'name': fields.selection([('Before 7',' Before 7'), ('7:00 - 8:0', '7:00 - 8:0'), 
                     ('8:00 - 9:00','8:00 - 9:00'),('After 9','After 9')], readonly=True),
        #'type': fields.selection(_time_get, 'Time Interval', required=True),
        'measure':fields.integer('Measure', readonly=True),
       
    }
    _order = 'name'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'avg_work_hours')
        cr.execute("""
            create or replace view avg_work_hours as (
                 select min(id) as id
                , case when measure::int = 1 then 'Before 7' else
                  case when a.measure::int = 2 then '7:00 - 8:0' else
                  case when a.measure::int = 3 then '8:00 - 9:00' else 'After 9' end end end as name
                , count(a.measure)::integer as measure 
            from    
            
            (    select 
                      punch_date
                    , id 
                    , timesheet_id
                    , start_time at time zone 'UTC+5:30'
                    , start_time
                    , end_time at time zone 'UTC+5:30' 
                    , end_time
                    , case when (EXTRACT(EPOCH FROM end_time - start_time) / 3600) < 7 then 1 else
                      case when (EXTRACT(EPOCH FROM end_time - start_time) / 3600) between 7 and 8 then 2 else
                      case when (EXTRACT(EPOCH FROM end_time - start_time) / 3600) between 8 and 9 then 3 else 4
                      end end end as measure
                from hr_punch where punch_date >= now() - interval '30 days'
                and start_time is not null and end_time is not null
                order by measure
            )a
            group by a.measure , name
        )""")
        

class report_employee_attendance(osv.osv):
    _name = 'report.employee.attendance'
    _description = "Employee Attendance"
    _auto = False
    _columns = {
        'measure':fields.integer('Measure', readonly=True),
        'name': fields.char('Name'),
        'tot_emp' : fields.integer('Employee Number')
        
       
    }

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'report_employee_attendance')
        cr.execute("""
            create or replace view report_employee_attendance as (
                 select * from 
                (
                    select 
                        min(id) as id, 
                        count(id)::int as measure, 
                        'Present' as name 
                        ,(select count(id)::int as tot_count from hr_employee)
                        from hr_punch where punch_date = now()::date and type = 'punch'
                    union
                    select 
                        min(id) as id, count(id)::int as measure  
                        , 'On Leave' as name 
                        ,(select count(id)::int as tot_count from hr_employee)
                        from hr_punch where punch_date = now()::date and type = 'daily'
                    union
                    select 
                        min(id) as id, count(id)::int as measure 
                        , 'Total' as name 
                        , count(id)::integer as tot_count
                        from hr_employee
                    
                )a


        )""")
    