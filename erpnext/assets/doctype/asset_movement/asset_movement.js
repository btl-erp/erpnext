// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("target_custodian", "user_id", "target_user_id")

frappe.ui.form.on('Asset Movement', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1) {
			cur_frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}
	},
	onload: function(frm) {
		frm.add_fetch("asset", "warehouse", "source_warehouse");
		frm.add_fetch("asset", "issued_to", "source_custodian");
		frm.add_fetch("asset", "cost_center", "current_cost_center");
		
		frm.set_query("target_warehouse", function() {
			return {
				filters: [
                                         ["Warehouse", "company", "in", ["", cstr(frm.doc.company)]],
                                         ["Warehouse", "is_group", "=", 0]
                                        ]				
			}
		})
		frm.set_query("target_cost_center", function() {
			return {
				filters: [
                                         ["Cost Center", "is_disabled", "!=", 1],
                                         ["Cost Center", "is_group", "=", 0]
                                        ]				
			}
		})
	}
});
