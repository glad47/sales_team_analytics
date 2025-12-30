# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    receipt_location = fields.Char(
        string='Receipt Location Line 1',
        compute='_compute_receipt_location',
        store=True,
    )
    
    receipt_location_detail = fields.Char(
        string='Receipt Location Line 2',
        compute='_compute_receipt_location',
        store=True,
    )
    
    @api.depends('crm_team_id', 'crm_team_id.receipt_location', 'crm_team_id.receipt_location_detail')
    def _compute_receipt_location(self):
        """Get receipt location from linked sales team"""
        for config in self:
            if config.crm_team_id:
                config.receipt_location = config.crm_team_id.receipt_location or ''
                config.receipt_location_detail = config.crm_team_id.receipt_location_detail or ''
            else:
                config.receipt_location = ''
                config.receipt_location_detail = ''