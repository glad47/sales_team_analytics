// odoo.define('sales_team_analytics.models', function (require) {
//     'use strict';

//     const { Order } = require('point_of_sale.models');
//     const Registries = require('point_of_sale.Registries');

//     const SalesTeamAnalyticsOrder = (Order) => class extends Order {
//         export_for_printing() {
//             const result = super.export_for_printing();
            
//             // Get location from config (via related fields)
//             console.log("CVCVCVCVCVCVCVCVCVCVCVCVCVCVCVCV")
//             if (this.pos && this.pos.config) {
//                 console.log("i am working inside")
//                 console.log(result)
//                 result.receipt_location = this.pos.config.receipt_location || '';
//                 result.receipt_location_detail = this.pos.config.receipt_location_detail || '';
//             }else{
//                 console.log("not work!!!")
//             }
            
//             return result;
//         }
//     };

//     Registries.Model.extend(Order, SalesTeamAnalyticsOrder);

//     return Order;
// });



odoo.define('sales_team_analytics.models', function (require) {
    'use strict';

    const { Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const SalesTeamOrder = (Order) => class extends Order {
        export_for_printing() {
            const result = super.export_for_printing();
            
            // Get team data from config
            console.log("hdhdhdhdhdhdhdhdhdhdhd")

            if (this.pos.config) {
                if(this.pos.config.crm_team_id){
                    const teamId = Array.isArray(this.pos.config.crm_team_id) 
                        ? this.pos.config.crm_team_id[0] 
                        : this.pos.config.crm_team_id;
                    
                    // Find team in loaded models
                    const team = this.pos.models['crm.team'].find(t => t.id === teamId);
                    
                    if (team) {
                        result.receipt_location = team.receipt_location || '';
                        result.receipt_location_detail = team.receipt_location_detail || '';
                    } else {
                        result.receipt_location = '';
                        result.receipt_location_detail = '';
                    }
                }else{
                    console.log("**********************************")
                    console.log("working  cccc")
                }
                
            } else {
                result.receipt_location = '';
                result.receipt_location_detail = '';
            }
            
            return result;
        }
    };

    Registries.Model.extend(Order, SalesTeamOrder);

    return Order;
});
