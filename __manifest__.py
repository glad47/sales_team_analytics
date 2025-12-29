# -*- coding: utf-8 -*-
{
    'name': 'Sales Team Analytics Account',
    'version': '16.0.1.0.0',
    'category': 'Sales/Accounting',
    'summary': 'Add analytics account to sales teams and auto-apply to invoices',
    'description': """
Sales Team Analytics Account
=============================

This module adds analytics account management for sales teams:

Features:
---------
* Add Analytics Account field to Sales Teams (CRM Teams)
* Automatic analytics account assignment to invoice lines based on:
  - POS orders (from POS session's sales team)
  - Sales orders (from sales order's sales team)
* Visual indicators in UI
* Comprehensive logging for debugging

Usage:
------
1. Configure Sales Teams with Analytics Accounts
2. Create Sales Orders or POS Orders with these teams
3. Generate invoices - analytics will be auto-applied on posting

Technical:
----------
* Compatible with Odoo 16
* Uses analytic_distribution format
* Hooks into invoice posting process
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'crm',
        'sale',
        'account',
        'point_of_sale',
        'analytic',
    ],
    'data': [
        'views/crm_team_views.xml',
        'views/account_move_views.xml',
    ],
    'images': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}