# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    source_team_id = fields.Many2one(
        'crm.team',
        string='Source Sales Team',
        compute='_compute_source_team_id',
        store=True,
        help='Sales team from the source document (SO or POS)'
    )
    
    @api.depends('invoice_origin', 'line_ids.sale_line_ids', 'pos_order_ids')
    def _compute_source_team_id(self):
        """Compute the source sales team from SO or POS order"""
        for move in self:
            team = False
            
            # Check if invoice comes from Sale Order
            if move.invoice_origin:
                sale_order = self.env['sale.order'].search([
                    ('name', '=', move.invoice_origin)
                ], limit=1)
                
                if sale_order and sale_order.team_id:
                    team = sale_order.team_id
                    _logger.info(
                        f"Invoice {move.name} linked to SO {sale_order.name} "
                        f"with team {team.name}"
                    )
            
            # Check if invoice comes from POS
            if not team and move.pos_order_ids:
                pos_order = move.pos_order_ids[0]
                if pos_order.session_id and pos_order.session_id.config_id.crm_team_id:
                    team = pos_order.session_id.config_id.crm_team_id
                    _logger.info(
                        f"Invoice {move.name} linked to POS order {pos_order.name} "
                        f"with team {team.name}"
                    )
            
            # Fallback: Check sale_line_ids in invoice lines
            if not team:
                for line in move.line_ids:
                    if line.sale_line_ids:
                        sale_line = line.sale_line_ids[0]
                        if sale_line.order_id.team_id:
                            team = sale_line.order_id.team_id
                            _logger.info(
                                f"Invoice {move.name} team found via invoice line "
                                f"sale order"
                            )
                            break
            
            move.source_team_id = team
    
    def _post(self, soft=True):
        """Override post to apply analytics account before posting"""
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund') and move.source_team_id:
                move._apply_team_analytics_account()
        return super(AccountMove, self)._post(soft=soft)
    
    def _apply_team_analytics_account(self):
        """Apply analytics account from sales team to invoice lines"""
        self.ensure_one()
        
        if not self.source_team_id or not self.source_team_id.analytic_account_id:
            _logger.info(f"No analytics account to apply for invoice {self.name}")
            return
        
        analytic_account = self.source_team_id.analytic_account_id
        lines_updated = 0
        
        for line in self.invoice_line_ids.filtered(
            lambda l: not l.exclude_from_invoice_tab and l.display_type == 'product'
        ):
            # Only update if line doesn't already have an analytics account
            # Remove this condition to force override
            if not line.analytic_distribution:
                line.analytic_distribution = {
                    str(analytic_account.id): 100
                }
                lines_updated += 1
                _logger.info(
                    f"Applied analytics account {analytic_account.name} "
                    f"to line {line.name}"
                )
        
        if lines_updated > 0:
            _logger.info(
                f"Applied analytics account '{analytic_account.name}' "
                f"to {lines_updated} lines in invoice {self.name}"
            )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.model_create_multi
    def create(self, vals_list):
        """Apply analytics account on line creation if parent invoice has source team"""
        lines = super(AccountMoveLine, self).create(vals_list)
        
        for line in lines:
            if (line.move_id.move_type in ('out_invoice', 'out_refund') and 
                line.move_id.source_team_id and 
                line.move_id.source_team_id.analytic_account_id and
                not line.analytic_distribution and
                line.display_type == 'product'):
                
                analytic_account = line.move_id.source_team_id.analytic_account_id
                line.analytic_distribution = {
                    str(analytic_account.id): 100
                }
                _logger.info(
                    f"Applied analytics account on line creation: "
                    f"{analytic_account.name}"
                )
        
        return lines