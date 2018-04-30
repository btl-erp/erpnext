// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("branch","revenue_bank_account","revenue_bank_account");

frappe.ui.form.on('Imprest Recoup', {
	setup: function(frm) {
		frm.get_docfield("items").allow_bulk_edit = 1;		
		frm.get_field('items').grid.editable_fields = [
			{fieldname: 'transaction_date', columns: 1},
			{fieldname: 'particulars', columns: 2},
			{fieldname: 'quantity', columns: 1},
			{fieldname: 'rate', columns: 1},
			{fieldname: 'amount', columns: 2},
			{fieldname: 'budget_account', columns: 2},
			{fieldname: 'remarks', columns: 1}
		];
	},
	refresh: function(frm) {
		enable_disable(frm);
		
		if(frm.doc.docstatus===1){
			frm.add_custom_button(__('Accounting Ledger'), function(){
				frappe.route_options = {
					voucher_no: frm.doc.name,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}
	},
	onload: function(frm) {
		// Updating default information based on loggedin user
		if(frm.doc.__islocal) {
			if(!frm.doc.branch){
				frappe.call({
						method: "erpnext.custom_utils.get_user_info",
						args: {
							"user": frappe.session.user
						},
						callback(r) {
							if(r.message){
								cur_frm.set_value("cost_center", r.message.cost_center);
								cur_frm.set_value("branch", r.message.branch);
							}
						}
				});
			}
        }
		
		/*
		if (frm.doc.docstatus === 0 && frm.doc.workflow_state === "Recouped"){
			frm.set_value("workflow_state", "Waiting Recoupment");
			cur_frm.save();
		}
		*/
		
		/*
		if(!frm.doc.entry_date){
			cur_frm.set_value("entry_date", frappe.datetime.now_datetime());
		}
		*/
		
		frm.fields_dict['items'].grid.get_field('budget_account').get_query = function(){
			return{
				filters: {
					'root_type': 'Expense',
					'is_group': 0
				}
			}
		};
		
		cur_frm.set_query("select_cheque_lot", function(){
			return {
				"filters": [
					["status", "!=", "Used"],
					["docstatus", "=", "1"],
					["branch", "=", frm.doc.branch]
				]
			}
		});
	},
	branch: function(frm){
		// Update totals
		update_totals(frm);
		
		// Update Cost Center
		if(frm.doc.branch){
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Cost Center',
					filters: {
						'branch': frm.doc.branch
					},
					fields: ['name']
				},
				callback: function(r){
					if(r.message){
						cur_frm.set_value("cost_center", r.message.name);
						refresh_field('cost_center');
					}
				}
			});
		}
	},
	select_cheque_lot: function(frm){
		if(frm.doc.select_cheque_lot){
			frappe.call({
				method: "erpnext.accounts.doctype.cheque_lot.cheque_lot.get_cheque_no_and_date",
				args: {
				'name': frm.doc.select_cheque_lot
				},
				callback: function(r){
				   if (r.message) {
					   cur_frm.set_value("cheque_no", r.message[0].reference_no);
					   cur_frm.set_value("cheque_date", r.message[1].reference_date);
				   }
				   }
			});
		}
	},
});

frappe.ui.form.on('Imprest Recoup Item',{
	quantity: function(frm, cdt, cdn){
		calculate_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn){
		calculate_amount(frm, cdt, cdn);
	},
	
	amount: function(frm){
		update_totals(frm);
	},
	
	items_remove: function(frm){
		update_totals(frm);
	},	
});

var calculate_amount = function(frm, cdt, cdn){
	var child  = locals[cdt][cdn];
	var amount = 0.0;
	
	amount = parseFloat(child.quantity || 0.0)*parseFloat(child.rate || 0.0);
	frappe.model.set_value(cdt, cdn, "amount", parseFloat(amount || 0.0));
}

var update_totals = function(frm){
	var det = frm.doc.items || [];
	var tot_opening_balance = 0.0, 
		tot_receipt_amount  = 0.0, 
		tot_purchase_amount = 0.0, 
		tot_closing_balance = 0.0;
		
	for(var i=0; i<det.length; i++){
			tot_purchase_amount += parseFloat(det[i].amount || 0.0);
	}
	
	cur_frm.set_value("opening_balance",tot_opening_balance);
	cur_frm.set_value("receipt_amount",tot_receipt_amount);
	cur_frm.set_value("purchase_amount",tot_purchase_amount);
	cur_frm.set_value("closing_balance",parseFloat(tot_opening_balance || 0.0)+parseFloat(tot_receipt_amount)-parseFloat(tot_purchase_amount));
	
	if(frm.doc.branch){
		frappe.call({
			method: "erpnext.accounts.doctype.imprest_receipt.imprest_receipt.get_opening_balance",
			args: {
				"branch": frm.doc.branch,
				"docname": frm.doc.name
			},
			callback: function(r){
				if(r.message){
					cur_frm.set_value("opening_balance",parseFloat(r.message || 0.0));
					cur_frm.set_value("receipt_amount", parseFloat(tot_receipt_amount));
					cur_frm.set_value("closing_balance", parseFloat(r.message || 0.0)+parseFloat(tot_receipt_amount)-parseFloat(tot_purchase_amount));
				}
			}
		});
	}
}

/*
cur_frm.cscript.custom_before_submit = function(frm){
	console.log('before submit');
}
*/

function enable_disable(frm){
	var toggle_fields = ["revenue_bank_account","pay_to_recd_from", "use_cheque_lot","select_cheque_lot","cheque_no", "cheque_date"];
	
	toggle_fields.forEach(function(field_name){
		frm.set_df_property(field_name,"read_only",1);
	});
	
	if(frm.doc.workflow_state == 'Waiting Approval'){
		if(!in_list(user_roles, "Imprest Manager") && !in_list(user_roles, "Accounts User")){
			frm.set_df_property("items", "read_only", 1);
			frm.disable_save();
		}
	}
	else if(frm.doc.workflow_state == 'Waiting Recoupment'){
		if(!in_list(user_roles, "Accounts User")){
			frm.set_df_property("items", "read_only", 1);
			frm.disable_save();
		}
		else {
			toggle_fields.forEach(function(field_name){
				frm.set_df_property(field_name,"read_only",0);
			});
			
			frm.toggle_reqd(["revenue_bank_account","pay_to_recd_from", "cheque_no", "cheque_date"], 1);
		}
	}
	else {
		frm.enable_save();
	}
}

frappe.ui.form.on("Imprest Recoup","items_on_form_rendered", function(frm, grid_row, cdt, cdn){
	var grid_row = cur_frm.open_grid_row();
	if(frm.doc.workflow_state == 'Waiting Approval'){
		if(!in_list(user_roles, "Imprest Manager") && !in_list(user_roles, "Accounts User")){
			//Following works only when row is opened
			grid_row.grid_form.fields_dict.quantity.df.read_only = true;
			grid_row.grid_form.fields_dict.rate.df.read_only = true;
			grid_row.grid_form.fields_dict.quantity.refresh();
			grid_row.grid_form.fields_dict.rate.refresh();
		}
	}
	else if(frm.doc.workflow_state == 'Waiting Recoupment'){
		if(!in_list(user_roles, "Accounts User")){
			//Following works only when row is opened
			grid_row.grid_form.fields_dict.quantity.df.read_only = true;
			grid_row.grid_form.fields_dict.rate.df.read_only = true;
			grid_row.grid_form.fields_dict.budget_account.df.read_only = true;
			grid_row.grid_form.fields_dict.quantity.refresh();
			grid_row.grid_form.fields_dict.rate.refresh();
			grid_row.grid_form.fields_dict.budget_account.refresh();
		}
	}
	
})
