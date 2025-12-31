

odoo.define('sales_team_analytics.pos_models', function (require) {
    'use strict';

    // console.log('========================================');
    // console.log('[SalesTeamAnalytics] Module loading started');
    // console.log('========================================');

    const { PosGlobalState, Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    // console.log('[SalesTeamAnalytics] PosGlobalState:', PosGlobalState);
    // console.log('[SalesTeamAnalytics] Order:', Order);
    // console.log('[SalesTeamAnalytics] Registries:', Registries);

    // =============================================
    // 1. Load crm.team data into POS
    // =============================================
    const PosGlobalStateSalesTeam = (PosGlobalState) => class extends PosGlobalState {
        async _processData(loadedData) {
            // console.log('----------------------------------------');
            // console.log('[SalesTeamAnalytics] _processData called');
            // console.log('[SalesTeamAnalytics] loadedData keys:', Object.keys(loadedData));
            // console.log('[SalesTeamAnalytics] loadedData["crm.team"]:', loadedData['crm.team']);

            await super._processData(loadedData);

            this.crm_teams = loadedData['crm.team'] || [];

            // console.log('[SalesTeamAnalytics] this.crm_teams set to:', this.crm_teams);
            // console.log('[SalesTeamAnalytics] Number of teams loaded:', this.crm_teams.length);
            // console.log('----------------------------------------');
        }
    };

    // console.log('[SalesTeamAnalytics] Extending PosGlobalState...');
    Registries.Model.extend(PosGlobalState, PosGlobalStateSalesTeam);
    // console.log('[SalesTeamAnalytics] PosGlobalState extended successfully');

    // =============================================
    // 2. Extend Order for receipt printing
    // =============================================
    const SalesTeamOrder = (Order) => class extends Order {
        export_for_printing() {
            // console.log('========================================');
            // console.log('[SalesTeamAnalytics] export_for_printing called');

            const result = super.export_for_printing();

            // console.log('[SalesTeamAnalytics] Base result from super:', result);
            // console.log('[SalesTeamAnalytics] this.pos:', this.pos);
            // console.log('[SalesTeamAnalytics] this.pos.config:', this.pos?.config);
            // console.log('[SalesTeamAnalytics] this.pos.config.crm_team_id:', this.pos?.config?.crm_team_id);
            // console.log('[SalesTeamAnalytics] this.pos.crm_teams:', this.pos?.crm_teams);

            if (this.pos.config && this.pos.config.crm_team_id) {
                const teamId = Array.isArray(this.pos.config.crm_team_id)
                    ? this.pos.config.crm_team_id[0]
                    : this.pos.config.crm_team_id;

                // console.log('[SalesTeamAnalytics] crm_team_id is array?', Array.isArray(this.pos.config.crm_team_id));
                // console.log('[SalesTeamAnalytics] Resolved teamId:', teamId);

                const team = this.pos.crm_teams?.find(t => t.id === teamId);

                // console.log('[SalesTeamAnalytics] Found team:', team);

                if (team) {
                    result.receipt_location = team.receipt_location || '';
                    result.receipt_location_detail = team.receipt_location_detail || '';
                    // console.log('[SalesTeamAnalytics] Set receipt_location:', result.receipt_location);
                    // console.log('[SalesTeamAnalytics] Set receipt_location_detail:', result.receipt_location_detail);
                } else {
                    result.receipt_location = '';
                    result.receipt_location_detail = '';
                    // console.warn('[SalesTeamAnalytics] WARNING: Team not found for teamId:', teamId);
                    // console.warn('[SalesTeamAnalytics] Available teams:', this.pos.crm_teams);
                }
            } else {
                result.receipt_location = '';
                result.receipt_location_detail = '';
                // console.warn('[SalesTeamAnalytics] WARNING: No crm_team_id configured');
                // console.warn('[SalesTeamAnalytics] this.pos.config exists?', !!this.pos?.config);
                // console.warn('[SalesTeamAnalytics] crm_team_id value:', this.pos?.config?.crm_team_id);
            }

            // console.log('[SalesTeamAnalytics] Final result:', result);
            // console.log('========================================');

            return result;
        }
    };

    // console.log('[SalesTeamAnalytics] Extending Order...');
    Registries.Model.extend(Order, SalesTeamOrder);
    // console.log('[SalesTeamAnalytics] Order extended successfully');

    // console.log('========================================');
    // console.log('[SalesTeamAnalytics] Module loading completed');
    // console.log('========================================');

    return { PosGlobalStateSalesTeam, SalesTeamOrder };
});

