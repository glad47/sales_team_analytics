# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CrmTeam(models.Model):
    _inherit = 'crm.team'
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytics Account',
        help='Default analytics account for this sales team. '
             'Will be automatically applied to invoice lines from this team.'
    )

    # Add location fields for POS receipts
    receipt_location = fields.Char(
        string='Receipt Location (Line 1)',
        help='First line of location on receipt (e.g., الرحاب - شارع التحلية)',
        translate=True
    )
    
    receipt_location_detail = fields.Char(
        string='Receipt Location Details (Line 2)',
        help='Second line with full address details',
        translate=True
    )
    
    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_id(self):
        """Warn user when changing analytics account"""
        if self.analytic_account_id:
            return {
                'warning': {
                    'title': 'Analytics Account Changed',
                    'message': 'This will affect all new invoices created from this sales team.'
                }
            }