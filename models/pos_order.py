# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    def _prepare_invoice_vals(self):
        """Override to ensure POS orders link to invoices properly"""
        vals = super(PosOrder, self)._prepare_invoice_vals()
        
        # The account.move will compute source_team_id via pos_order_ids
        # This ensures proper linking for analytics assignment
        
        return vals


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    # Note: crm_team_id is a standard field in pos.config in Odoo 16
    # This model is here for reference and potential future customizations
    pass