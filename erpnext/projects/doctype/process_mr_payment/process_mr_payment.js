// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
//cur_frm.add_fetch("project", "branch", "branch")
//cur_frm.add_fetch("project", "cost_center", "cost_center")
//cur_frm.add_fetch("cost_center", "branch", "branch")

cur_frm.add_fetch("project", "branch", "branch")
cur_frm.add_fetch("project", "cost_center", "cost_center")
cur_frm.add_fetch("branch", "cost_center", "cost_center")

frappe.ui.form.on('Process MR Payment', {
	setup: function(frm) {
		frm.get_docfield("items").allow_bulk_edit = 1;
	},
	refresh: function(frm) {
		if (frm.doc.payment_jv && frappe.model.can_read("Journal Entry")) {
			cur_frm.add_custom_button(__('Bank Entries'), function() {
				frappe.route_options = {
					"Journal Entry Account.reference_type": me.frm.doc.doctype,
					"Journal Entry Account.reference_name": me.frm.doc.name,
				};
				frappe.set_route("List", "Journal Entry");
			}, __("View"));
		}
	},

	onload: function(frm) {
		if(!frm.doc.from_date) {
			frm.set_value("from_date", frappe.datetime.month_start(get_today()))	
		}
		if(!frm.doc.to_date) {
			frm.set_value("to_date", frappe.datetime.month_end(get_today()))	
		}
		if(!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today())	
		}
	},

	load_records: function(frm) {
		cur_frm.set_df_property("load_records", "disabled",  true);
		//msgprint ("Processing wages.............")
		if(frm.doc.from_date && frm.doc.cost_center && frm.doc.employee_type && frm.doc.from_date < frm.doc.to_date) {
			get_records(frm.doc.employee_type, frm.doc.fiscal_year, frm.doc.month, frm.doc.from_date, frm.doc.to_date, frm.doc.cost_center, frm.doc.branch, frm.doc.name)
		}
		else if(frm.doc.from_date && frm.doc.from_date > frm.doc.to_date) {
			msgprint("To Date should be smaller than From Date")
			frm.set_value("to_date", "")
		}
	},
	load_employee: function(frm) {
		//load_accounts(frm.doc.company)
		return frappe.call({
			method: "load_employee",
			doc: frm.doc,
			callback: function(r, rt) {
				frm.refresh_field("items");
				frm.refresh_fields();
			}
		});
	}
});

var update_details = function(doc){
	cur_frm.call({
		method: "update_details",
		doc: doc
	});
}

function get_records(employee_type, fiscal_year, month, from_date, to_date, cost_center, branch, dn) {
	frappe.call({
		method: "erpnext.projects.doctype.process_mr_payment.process_mr_payment.get_records",
		args: {
			"fiscal_year": fiscal_year,
			"fiscal_month": month,
			"from_date": from_date,
			"to_date": to_date,
			"cost_center": cost_center,
			"branch": branch,
			"employee_type": employee_type,
			"dn": dn
		},
		callback: function(r) {
			if(r.message) {
				var total_overall_amount = 0;
				var ot_amount = 0; 
				var wages_amount = 0;
				console.log(r.message)
				cur_frm.clear_table("items");
				r.message.forEach(function(mr) {
					if(mr['number_of_days'] > 0 || mr['number_of_hours'] > 0) {
						var row = frappe.model.add_child(cur_frm.doc, "MR Payment Item", "items");
						
						row.employee_type 	= mr['type'];
						row.employee 		= mr['name'];
						row.person_name 	= mr['person_name'];
						row.id_card 		= mr['id_card'];
						row.business_activity = mr['business_activity'];
						row.fiscal_year 	= fiscal_year;
						row.month 			= month;
						row.number_of_days 	= mr['number_of_days'];
						row.daily_rate 		= mr['rate_per_day'];
						row.number_of_hours = mr['number_of_hours'];
						row.hourly_rate 	= mr['rate_per_hour'];
						row.total_ot_amount = row.number_of_hours * row.hourly_rate;
						row.total_wage 		= row.daily_rate * row.number_of_days;
						
						if(mr['type'] == 'DES Employee'){
							row.daily_rate      = parseFloat(mr['salary'])/parseFloat(mr['noof_days_in_month']);
							row.hourly_rate     = parseFloat(mr['salary']*1.5)/parseFloat(mr['noof_days_in_month']*8);
							row.total_ot_amount = row.number_of_hours * row.hourly_rate;
							row.total_wage      = row.daily_rate * row.number_of_days;
							
							if((parseFloat(row.total_wage) > parseFloat(mr['salary']))||(parseFloat(mr['noof_days_in_month']) == parseFloat(mr['number_of_days']))){
								row.total_wage = parseFloat(mr['salary']);
							}
						}
						
						/*
						if(mr['type'] == 'DES Employee' && parseFloat(row.total_wage) > parseFloat(mr['salary'])){
							row.total_wage = parseFloat(mr['salary']);
						}
						else if(mr['type'] == 'DES Employee' && parseFloat(mr['noof_days_in_month']) == parseFloat(mr['number_of_days'])){
							row.total_wage = parseFloat(mr['salary']);
						}
						*/
						
						row.total_amount 	= row.total_ot_amount + row.total_wage;
						refresh_field("items");

						total_overall_amount += row.total_amount;
						ot_amount 			 += row.total_ot_amount;
						wages_amount 		 += row.total_wage;
					}
				});

				cur_frm.set_value("total_overall_amount", total_overall_amount)
				cur_frm.set_value("wages_amount", wages_amount)
				cur_frm.set_value("ot_amount", ot_amount)
				cur_frm.refresh_field("total_overall_amount")
				cur_frm.refresh_field("wages_amount")
				cur_frm.refresh_field("ot_amount")
				cur_frm.refresh_field("items");
			}
			else {
				frappe.msgprint("No Overtime and Attendance Record Found")
			}
		}
	})
}
