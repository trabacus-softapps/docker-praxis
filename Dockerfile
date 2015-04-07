FROM softapps/docker-odoobase-upstream
MAINTAINER Arun T K <arun.kalikeri@xxxxxxxx.com>
ADD additional_addons/pentaho_reports /opt/odoo/additional_addons/pentaho_reports
ADD additional_addons/attachment_large_object /opt/odoo/additional_addons/attachment_large_object
ADD additional_addons/Praxis /opt/odoo/additional_addons/Praxis

RUN chown -R odoo:odoo /opt/odoo/additional_addons/
