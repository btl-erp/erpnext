// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Consolidated Invoice', {
	refresh: function(frm) {
		if(!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today())
		}
	},
	to_date: function(frm) {
		if(frm.doc.from_date && frm.doc.from_date < frm.doc.to_date) {
			get_invoices(frm.doc.from_date, frm.doc.to_date, frm.doc.item_code, frm.doc.customer, frm.doc.cost_center)
		}
		else if(frm.doc.from_date && frm.doc.from_date > frm.doc.to_date) {
			msgprint("To Date should be smaller than From Date")
			frm.set_value("to_date", "")
		}
	},
	from_date: function(frm) {
		if(frm.doc.to_date && frm.doc.from_date < frm.doc.to_date) {
			get_invoices(frm.doc.from_date, frm.doc.to_date, frm.doc.item_code, frm.doc.customer, frm.doc.cost_center)
		}
		else if(frm.doc.to_date && frm.doc.from_date > frm.doc.to_date) {
			msgprint("To Date should be smaller than From Date")
			frm.set_value("from_date", "")
		}
	},
	item_code: function(frm) {
		frm.fields_dict['item_price'].get_query = function(doc) {
			return {
				filters: {
					"item_code": frm.doc.item_code
				}
			}
		}
	}
});

cur_frm.add_fetch("item_price", "price_list_rate", "rate")
cur_frm.add_fetch("item_code", "stock_uom", "uom")
cur_frm.add_fetch("item_code", "item_name", "item_name")

function get_invoices(from_date, to_date, item_code, customer, cost_center) {
	frappe.call({
		method: "erpnext.selling.doctype.consolidated_invoice.consolidated_invoice.get_invoices",
		args: {
			"from_date": from_date,
			"to_date": to_date,
			"customer": customer,
			"cost_center": cost_center,
			"item_code": item_code
		},
		callback: function(r) {
			if(r.message) {
				var total_amount = 0;
				var total_qty = 0;
				cur_frm.clear_table("items");
				r.message.forEach(function(invoice) {
				        var row = frappe.model.add_child(cur_frm.doc, "Consolidated Invoice Item", "items");
					row.invoice_no = invoice['name']
					row.amount = invoice['outstanding_amount']
					row.date = invoice['posting_date']
					row.delivery_note = invoice['delivery_note']
					row.sales_order = invoice['sales_order']
					refresh_field("items");

					total_amount += invoice['outstanding_amount']
					total_qty += invoice['accepted_qty']
				});

				cur_frm.set_value("total_amount", total_amount)
				cur_frm.set_value("quantity", total_qty)
			}
		}
	})
}
