-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- 				FUNCTION:Late In Early Out Report
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
/*
drop type if exists latein_earlyout cascade;
create type latein_earlyout as (  

	  employee_id integer,
	  gen_date date,
	  emp_no varchar(20),
	  employee varchar(30),
	  charge_date date,
	  login_time varchar(15),	
	  end_time varchar(15), 
	  late_in varchar(5),
	  early_out varchar(5),
	  emp_comp varchar(30),
	  emp_type varchar(30)
	  );


drop function if exists latein_earlyout_func(from_date date,to_date date);

CREATE OR REPLACE FUNCTION latein_earlyout_func(from_date date,to_date date)

RETURNS SETOF latein_earlyout AS
$BODY$

    DECLARE
       r latein_earlyout%rowtype;
       rec record;
       sqlstr text;
    BEGIN
       from_date := to_char((from_date)::date, 'yyyy-mm-dd');
       to_date := to_char((to_date)::date, 'yyyy-mm-dd');

   CREATE TEMP TABLE tmp_latein_earlyout(employee_id int,gen_date date,employee varchar(50),emp_no varchar(20))
          

       
    ON COMMIT DROP;


    for rec in (SELECT 
			 t.employee_id
			,MIN(r.name || e.last_name) as employee 
			,MAX(e.identification_id) as emp_no 
		FROM

		hr_emp_timesheet t
		INNER JOIN hr_employee e on e.id = t.employee_id
		INNER JOIN resource_resource r on r.id = e.resource_id
		GROUP BY t.employee_id
		ORDER BY t.employee_id)	LOOP	

	INSERT INTO tmp_latein_earlyout(gen_date,employee_id,employee,emp_no)
	(
	select a.i as gen_date
	      ,rec.employee_id as employee_id
	      , rec.employee as employee
	      , rec.emp_no as emp_no
	from

	(select i::date from generate_series(from_date::date, to_date::date, '1 day'::interval) i)a

	);

	END LOOP;


	sqlstr = 'SELECT y.employee_id
			        ,y.gen_date
	                ,y.emp_no
	                ,y.employee
	                ,x.charge_date
	                ,x.login_time 
	                ,x.end_time
	                ,x.late_in
	                ,x.early_out
	                ,x.emp_comp
	                ,x.emp_type

	FROM
	(
	SELECT 
		  tp.gen_date
		, tp.employee_id
		, tp.employee
		, tp.emp_no
		 
		
	FROM tmp_latein_earlyout tp
	) y
	LEFT OUTER JOIN 

	(SELECT
		  MAX(e.identification_id) as employee_no
		, MIN(r.name || e.last_name) as employee
		,  MAX(p.punch_date) as charge_date
		, to_char(p.punch_date, ''dd'' ) as day
		, t.employee_id
		, MAX(rc.name) as emp_comp
		, MAX(et.name) as emp_type
		, e.employee_type_id

		, MAX(to_char((p.start_time ::TIMESTAMP::VARCHAR || '' UTC'')::TIMESTAMPTZ AT TIME ZONE 
	          (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), ''HH:MI:SS AM'') )as login_time	
	          	
		, MAX(to_char((p.end_time ::TIMESTAMP::VARCHAR || '' UTC'')::TIMESTAMPTZ AT TIME ZONE 
	          (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), ''HH:MI:SS AM'')) as end_time	
	          
		, CASE WHEN MAX(to_char((p.start_time ::TIMESTAMP::VARCHAR || '' UTC'')::TIMESTAMPTZ AT TIME ZONE 
	          (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), ''HH:MI:SS AM'') ) > ''09:00:00'' THEN ''YES'' ELSE  null END as late_in
  
		, CASE WHEN MAX(to_char((p.end_time ::TIMESTAMP::VARCHAR || '' UTC'')::TIMESTAMPTZ AT TIME ZONE 
	          (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), ''HH:MI:SS AM'') ) < ''05:30:00'' THEN ''YES'' ELSE  null END as early_out
	          
		
	FROM hr_emp_timesheet t

	INNER JOIN hr_employee e on e.id = t.employee_id
	INNER JOIN resource_resource r on r.id = e.resource_id
	LEFT OUTER JOIN res_company rc on rc.id = r.company_id
	LEFT OUTER JOIN hr_employee_type et on et.id = e.employee_type_id

	INNER JOIN hr_punch p on p.timesheet_id = t.id

	WHERE p.punch_date >= '''||from_date||''' AND p.punch_date <= '''||to_date||'''


	GROUP BY t.employee_id ,day,e.employee_type_id
	ORDER BY t.employee_id,charge_date

	) x 
	
	on x.employee_id = y.employee_id  AND y.gen_date = x.charge_date' ; 

	FOR r IN execute sqlstr LOOP
    	return next r;          
        END LOOP;        

	RETURN;
     END 

		
  $BODY$
LANGUAGE plpgsql VOLATILE;

*/

drop type if exists latein_earlyout cascade;
drop table if exists tmp_latein_earlyout;
create type latein_earlyout as (  

	  employee_id integer,
	  gen_date date,
	  emp_no varchar(20),
	  employee varchar(30),
	  charge_date date,
	  login_time varchar(15),	
	  end_time varchar(15), 
	  late_in varchar(5),
	  early_out varchar(5),
	  emp_comp varchar(30),
	  emp_type varchar(30),
	  groupby_value integer,
	  sort_value varchar
	  );


drop function if exists latein_earlyout_func(start_date date,end_date date, emp_ids text, gp_value varchar, sort_value varchar);

CREATE OR REPLACE FUNCTION latein_earlyout_func(start_date date,end_date date, tsheet_ids text, gp_value varchar, sort_value varchar)

RETURNS SETOF latein_earlyout AS
$BODY$

    DECLARE
       r latein_earlyout%rowtype;
       rec record;
       sqlstr text;
       ids integer[];
    BEGIN
       ids = string_to_array($3,','); 		
       start_date := to_char((start_date)::date, 'yyyy-mm-dd');
       end_date := to_char((end_date)::date, 'yyyy-mm-dd');


   CREATE temp TABLE tmp_latein_earlyout(employee_id int,gen_date date,employee varchar(50),emp_no varchar(20), groupby_value integer, sort_value varchar)
          
--drop table tmp_latein_earlyout
       
    ON COMMIT DROP;


    for rec in (SELECT 
		 e.id as employee_id
		,MIN(r.name || ' ' ||e.last_name) as employee 
		,MAX(e.identification_id) as emp_no 
		,MAX(CASE WHEN  gp_value = 'class_id1' THEN e.class_id1 ELSE
			CASE WHEN  gp_value = 'class_id2' THEN e.class_id2 ELSE	
			CASE WHEN  gp_value = 'class_id3' THEN e.class_id3 ELSE
			CASE WHEN  gp_value = 'class_id4' THEN e.class_id4 ELSE 
			CASE WHEN  gp_value = 'class_id5' THEN e.class_id5 ELSE
			CASE WHEN  gp_value = 'class_id6' THEN e.class_id6 ELSE
			CASE WHEN  gp_value = 'class_id7' THEN e.class_id7 ELSE
			CASE WHEN  gp_value = 'class_id8' THEN e.class_id8 ELSE
			CASE WHEN  gp_value = 'class_id9' THEN e.class_id9 ELSE 
			CASE WHEN  gp_value = 'class_id10' THEN e.class_id10 ELSE  NULL
			
			END END END END END END 
			END END END
			END

		   ) AS groupby_value

		,MAX(CASE WHEN sort_value = 'name_related' THEN e.name_related ELSE e.identification_id END) as sort_value   
			
		    
	FROM

	hr_employee e
	LEFT OUTER JOIN hr_punch p on p.employee_id =  e.id
	INNER JOIN resource_resource r on r.id = e.resource_id
	
	LEFT OUTER JOIN hr_class1 c1 on c1.id = e.class_id1
	LEFT OUTER JOIN hr_class2 c2 on c2.id = e.class_id2
	LEFT OUTER JOIN hr_class3 c3 on c3.id = e.class_id3
	LEFT OUTER JOIN hr_class4 c4 on c4.id = e.class_id4
	LEFT OUTER JOIN hr_class5 c5 on c5.id = e.class_id5
	LEFT OUTER JOIN hr_class6 c6 on c6.id = e.class_id6
	LEFT OUTER JOIN hr_class7 c7 on c7.id = e.class_id7
	LEFT OUTER JOIN hr_class8 c8 on c8.id = e.class_id8
	LEFT OUTER JOIN hr_class9 c9 on c9.id = e.class_id9
	LEFT OUTER JOIN hr_class10 c10 on c10.id = e.class_id10
	

	WHERE e.id in (select unnest(ids))
	
	GROUP BY e.id
	ORDER BY groupby_value,sort_value, e.id )	LOOP	

	INSERT INTO tmp_latein_earlyout(gen_date,employee_id,employee,emp_no,groupby_value, sort_value)
	(
	select a.i as gen_date
	      ,rec.employee_id as employee_id
	      , rec.employee as employee
	      , rec.emp_no as emp_no
	      , rec.groupby_value as groupby_value
	      , rec.sort_value as sort_value
	from

	(select i::date from generate_series(start_date::date, end_date::date, '1 day'::interval) i)a

	);

	END LOOP;


	sqlstr = 'SELECT y.employee_id
			,y.gen_date
	                ,y.emp_no
	                ,y.employee
	                ,x.charge_date
	                ,x.login_time 
	                ,x.end_time
	                ,x.late_in
	                ,x.early_out
	                ,x.emp_comp
	                ,x.emp_type
	                ,y.groupby_value
	                ,y.sort_value

	FROM
	(
	SELECT 
		  tp.gen_date
		, tp.employee_id
		, tp.employee
		, tp.emp_no
		, tp.groupby_value
		, tp.sort_value
		 
		
	FROM tmp_latein_earlyout tp
	) y
	LEFT OUTER JOIN 

	(SELECT
		  MAX(e.identification_id) as employee_no
		, MIN(r.name || e.last_name) as employee
		,  MAX(p.punch_date) as charge_date
		, to_char(p.punch_date, ''dd'' ) as day
		, e.id as employee_id
		, MAX(rc.name) as emp_comp
		, MAX(et.name) as emp_type
		, e.employee_type_id

		, MAX(to_char((p.start_time ::TIMESTAMP::VARCHAR || '' UTC'')::TIMESTAMPTZ AT TIME ZONE 
	          (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), ''HH:MI:SS AM'') )as login_time	
	          	
		, MAX(to_char((p.end_time ::TIMESTAMP::VARCHAR || '' UTC'')::TIMESTAMPTZ AT TIME ZONE 
	          (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), ''HH:MI:SS AM'')) as end_time	
	          
		, CASE WHEN MAX(to_char((p.start_time ::TIMESTAMP::VARCHAR || '' UTC'')::TIMESTAMPTZ AT TIME ZONE 
	          (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), ''HH:MI:SS AM'') ) > ''09:00:00'' THEN ''YES'' ELSE  null END as late_in
  
		, CASE WHEN MAX(to_char((p.end_time ::TIMESTAMP::VARCHAR || '' UTC'')::TIMESTAMPTZ AT TIME ZONE 
	          (SELECT rp.tz from res_partner rp inner join res_users u on rp.id = u.partner_id where u.id = (1)), ''HH:MI:SS AM'') ) < ''05:30:00'' THEN ''YES'' ELSE  null END as early_out
	          
		
	FROM hr_employee e
	INNER JOIN resource_resource r on r.id = e.resource_id
	LEFT OUTER JOIN res_company rc on rc.id = r.company_id
	LEFT OUTER JOIN hr_employee_type et on et.id = e.employee_type_id

	INNER JOIN hr_punch p on p.employee_id = e.id

	WHERE e.id in (select unnest(''' || ids::TEXT || '''::INT[])) AND p.punch_date >= '''||start_date||''' AND p.punch_date <= '''||end_date||'''


	GROUP BY e.id ,day,e.employee_type_id
	ORDER BY e.id ,charge_date

	) x 
	
	on x.employee_id = y.employee_id  AND y.gen_date = x.charge_date' ; 

	FOR r IN execute sqlstr LOOP
    	return next r;          
        END LOOP;        

	RETURN;
     END 

		
  $BODY$
LANGUAGE plpgsql VOLATILE;

/*
SELECT * FROM latein_earlyout_func('2015-08-01','2015-08-31', '1', 'class_id2', 'emp_name') 
order by groupby_value,sort_value,gen_date,employee_id
*/