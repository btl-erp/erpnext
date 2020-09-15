// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.add_fetch("account", "account_code", "account_code")
frappe.ui.form.on('Budget', {
	setup: function(frm) {
		frm.get_docfield("accounts").allow_bulk_edit = 1;
	},
	onload: function(frm) {
		frm.set_query("cost_center", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_disabled: 0,
				}
			}
		})

		frm.set_query("account", "accounts", function() {
			return {
				filters: {
					company: frm.doc.company,
			//		report_type: "Profit and Loss",
					is_group: 0
				}
			}
		})

		frm.set_query("monthly_distribution", function() {
			return {
				filters: {
					fiscal_year: frm.doc.fiscal_year
				}
			}
		})
	},
	get_accounts: function(frm) {
		//load_accounts(frm.doc.company)
		return frappe.call({
			method: "get_accounts",
			doc: frm.doc,
			callback: function(r, rt) {
				frm.refresh_field("accounts");
				frm.refresh_field("total_royalty");
				frm.refresh_fields();
			},
			freeze: true,
			freeze_message: "Loading Expense Accounts..... Please Wait"
		});
	}
});

//Custom Scripts
//Calculate when initial budget changes
frappe.ui.form.on("Budget Account", "initial_budget", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//Calculate when supplementary budget changes
frappe.ui.form.on("Budget Account", "supplementary_budget", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//Calculate when re-appropiation budget received budget changes
frappe.ui.form.on("Budget Account", "budget_received", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//Calculate when re-appropiation budget sent budget changes
frappe.ui.form.on("Budget Account", "budget_sent", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//recalculate during validate
frappe.ui.form.on("Budget Account", "validate", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//Function to calculate available budget (budget_amount)
function calculate_budget_amount(child) {
    return (child.initial_budget + (child.supplementary_budget || 0) + (child.budget_received || 0)  - (child.budget_sent || 0) )
}

//custom Scripts
//Calculate when initial budget changes
frappe.ui.form.on("Budget Account", "initial_budget", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//Calculate when supplementary budget changes
frappe.ui.form.on("Budget Account", "supplementary_budget", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//Calculate when re-appropiation budget received budget changes
frappe.ui.form.on("Budget Account", "budget_received", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//Calculate when re-appropiation budget sent budget changes
frappe.ui.form.on("Budget Account", "budget_sent", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//recalculate during validate
frappe.ui.form.on("Budget Account", "validate", function(frm, cdt, cdn) {
    var child = locals[cdt][cdn];

    frappe.model.set_value(cdt, cdn, "budget_amount", calculate_budget_amount(child));
});

//Function to calculate available budget (budget_amount)
function calculate_budget_amount(child) {
    return (child.initial_budget + (child.supplementary_budget || 0) + (child.budget_received || 0)  - (child.budget_sent || 0) )
}

frappe.ui.form.on("Budget", "refresh", function(frm) {
    cur_frm.set_query("cost_center", function() {
        return {
            "filters": {
                "is_group": 0,
		"is_disabled": 0
            }
        };
    });
});



