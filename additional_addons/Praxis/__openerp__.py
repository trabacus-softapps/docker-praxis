{
    'name': "Praxis",
    'version': '1.0',
    'author': "Softappsit Solutions",
    'website' : 'http://www.softappsit.com',
    'sequence': 1,
    'category': 'HR',
    'description': """
    Description text
    """,
    # data files always loaded at installation
    'depends' :['base','hr','hr_holidays'],
    'data': [
             'pr_config_view.xml',
             'pr_hr_view.xml',
             'security/pr_security.xml',
             'security/ir.model.access.csv',
             
       
    ],
    

}