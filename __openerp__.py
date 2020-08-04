# -*- coding: utf-8 -*-
{
    'name': "Tecs module",

    'summary': """
        Modulo para el manejo de cuotas en la factura.""",

    'description': """
        Modulo para el manejo de cuotas en la factura.
    """,

    'author': "Librasoft",
    'website': "http://libra-soft.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_accountant'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'views/views.xml',
        'wizards/convenio_wizards.xml',
        'wizards/convenio_reports.xml',
        'views/reports.xml',
        'tecs_module_report.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        #'demo/demo.xml',
    ],
}