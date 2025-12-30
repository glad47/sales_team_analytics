# -*- coding: utf-8 -*-
from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def _pos_ui_models_to_load(self):
        """Ensure crm.team model is loaded in POS"""
        result = super()._pos_ui_models_to_load()
        if 'crm.team' not in result:
            result.append('crm.team')
        return result
    
    def _loader_params_crm_team(self):
        """Define which fields to load from crm.team"""
        return {
            'search_params': {
                'domain': [],
                'fields': [
                    'name',
                    'receipt_location',
                    'receipt_location_detail',
                ],
            },
        }
    
    def _get_pos_ui_crm_team(self, params):
        """Load crm.team data for POS"""
        return self.env['crm.team'].search_read(**params['search_params'])