# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def _get_source_analytic_account(self):
        """Get analytic account from source document (SO or POS order)
        
        Returns:
            recordset: analytic.account record or False if not found
        """
        self.ensure_one()
        
        try:
            # Check if invoice comes from Sale Order
            if self.invoice_origin:
                try:
                    sale_order = self.env['sale.order'].search([
                        ('name', '=', self.invoice_origin)
                    ], limit=1)
                    
                    if sale_order:
                        if sale_order.team_id and sale_order.team_id.analytic_account_id:
                            _logger.info(
                                f"Invoice {self.name} linked to SO {sale_order.name} "
                                f"with team {sale_order.team_id.name}"
                            )
                            return sale_order.team_id.analytic_account_id
                        else:
                            _logger.debug(
                                f"SO {sale_order.name} found but no team or "
                                f"analytic account configured"
                            )
                    else:
                        _logger.debug(
                            f"No sale order found for invoice_origin: {self.invoice_origin}"
                        )
                except Exception as e:
                    _logger.warning(
                        f"Error searching sale order for invoice {self.name}: {str(e)}"
                    )
            
            # Check if invoice comes from POS
            try:
                if hasattr(self, 'pos_order_ids') and self.pos_order_ids:
                    pos_order = self.pos_order_ids[0]
                    if pos_order.session_id:
                        config = pos_order.session_id.config_id
                        if config and config.crm_team_id and config.crm_team_id.analytic_account_id:
                            team = config.crm_team_id
                            _logger.info(
                                f"Invoice {self.name} linked to POS order {pos_order.name} "
                                f"with team {team.name}"
                            )
                            return team.analytic_account_id
                        else:
                            _logger.debug(
                                f"POS order {pos_order.name} found but no team or "
                                f"analytic account configured"
                            )
                    else:
                        _logger.debug(
                            f"POS order {pos_order.name} has no session"
                        )
            except AttributeError:
                # POS module not installed
                _logger.debug("POS module not installed, skipping POS check")
            except Exception as e:
                _logger.warning(
                    f"Error checking POS order for invoice {self.name}: {str(e)}"
                )
            
            # Fallback: Check sale_line_ids in invoice lines
            try:
                for line in self.line_ids:
                    if line.sale_line_ids:
                        sale_line = line.sale_line_ids[0]
                        if (sale_line.order_id and 
                            sale_line.order_id.team_id and 
                            sale_line.order_id.team_id.analytic_account_id):
                            _logger.info(
                                f"Invoice {self.name} team found via invoice line sale order"
                            )
                            return sale_line.order_id.team_id.analytic_account_id
            except Exception as e:
                _logger.warning(
                    f"Error checking sale lines for invoice {self.name}: {str(e)}"
                )
            
            _logger.debug(f"No source analytic account found for invoice {self.name}")
            return False
            
        except Exception as e:
            _logger.error(
                f"Unexpected error getting source analytic account for "
                f"invoice {self.name}: {str(e)}"
            )
            return False
    
    def _post(self, soft=True):
        """Override post to apply analytics account before posting"""
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund'):
                try:
                    move._apply_team_analytics_account()
                except Exception as e:
                    _logger.error(
                        f"Failed to apply team analytics account for "
                        f"invoice {move.name}: {str(e)}"
                    )
                    # Don't block posting, just log the error
                    # Uncomment below to block posting on error:
                    # raise UserError(_(
                    #     "Failed to apply analytics account: %s"
                    # ) % str(e))
        
        return super(AccountMove, self)._post(soft=soft)
    
    def _apply_team_analytics_account(self):
        """Apply analytics account from sales team to invoice lines 
        (excluding receivable/payable)
        
        Raises:
            UserError: If there's a critical error applying analytics
        """
        self.ensure_one()
        
        try:
            analytic_account = self._get_source_analytic_account()
            
            if not analytic_account:
                _logger.debug(f"No analytics account to apply for invoice {self.name}")
                return
            
            # Validate analytic account is active
            if not analytic_account.active:
                _logger.warning(
                    f"Analytic account {analytic_account.name} is archived, "
                    f"skipping for invoice {self.name}"
                )
                return
            
            lines_to_update = self.line_ids.filtered(
                lambda l: (
                    l.account_id and
                    l.account_id.account_type not in (
                        'asset_receivable', 
                        'liability_payable'
                    ) and 
                    l.display_type not in ('line_section', 'line_note') and
                    not l.analytic_distribution
                )
            )
            
            if not lines_to_update:
                _logger.debug(
                    f"No lines to update for invoice {self.name} "
                    f"(all lines already have analytics or are excluded)"
                )
                return
            
            lines_updated = 0
            lines_failed = 0
            
            for line in lines_to_update:
                try:
                    line.analytic_distribution = {
                        str(analytic_account.id): 100
                    }
                    lines_updated += 1
                    _logger.debug(
                        f"Applied analytics account {analytic_account.name} "
                        f"to line {line.name} (Account: {line.account_id.code})"
                    )
                except Exception as e:
                    lines_failed += 1
                    _logger.warning(
                        f"Failed to apply analytics to line {line.id} "
                        f"in invoice {self.name}: {str(e)}"
                    )
            
            if lines_updated > 0:
                _logger.info(
                    f"Applied analytics account '{analytic_account.name}' "
                    f"to {lines_updated} lines in invoice {self.name}"
                )
            
            if lines_failed > 0:
                _logger.warning(
                    f"Failed to apply analytics to {lines_failed} lines "
                    f"in invoice {self.name}"
                )
                
        except Exception as e:
            _logger.error(
                f"Error applying team analytics account for invoice {self.name}: {str(e)}"
            )
            raise


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    @api.model_create_multi
    def create(self, vals_list):
        """Apply analytics account on line creation if parent invoice has source team"""
        lines = super(AccountMoveLine, self).create(vals_list)
        
        for line in lines:
            try:
                # Skip if not a customer invoice/refund
                if line.move_id.move_type not in ('out_invoice', 'out_refund'):
                    continue
                
                # Skip if already has analytic distribution
                if line.analytic_distribution:
                    continue
                
                # Skip if no account or excluded account types
                if not line.account_id:
                    continue
                    
                if line.account_id.account_type in ('asset_receivable', 'liability_payable'):
                    continue
                
                # Skip sections and notes
                if line.display_type in ('line_section', 'line_note'):
                    continue
                
                # Get and apply analytic account
                analytic_account = line.move_id._get_source_analytic_account()
                
                if analytic_account:
                    # Validate analytic account is active
                    if not analytic_account.active:
                        _logger.debug(
                            f"Skipping archived analytic account {analytic_account.name} "
                            f"for line creation"
                        )
                        continue
                    
                    line.analytic_distribution = {
                        str(analytic_account.id): 100
                    }
                    _logger.debug(
                        f"Applied analytics account on line creation: "
                        f"{analytic_account.name} (Account: {line.account_id.code})"
                    )
                    
            except Exception as e:
                _logger.warning(
                    f"Error applying analytics on line creation for "
                    f"move {line.move_id.name if line.move_id else 'Unknown'}: {str(e)}"
                )
                # Don't block line creation, just log the error
                continue
        
        return lines
