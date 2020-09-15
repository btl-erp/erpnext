// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

{% include 'erpnext/selling/sales_common.js' %}

frappe.ui.form.on("Sales Order", {
	onload: function(frm) {

		//cur_frm.get_field("items").grid.toggle_reqd("selling_template", true);
		
		/*erpnext.queries.setup_queries(frm, "Warehouse", function() {
			return erpnext.queries.warehouse(frm.doc);
		});
		
		if(!frm.doc.selling_price_list) {
			//set default price list
			frm.set_value("selling_price_list", "Standard Selling")
		}*/

		//formatter for material request item
		frm.set_indicator_formatter('item_code', function(doc) { return (doc.qty<=doc.delivered_qty) ? "green" : "orange" });
	},
	"naming_series": function(frm) { 
	},
	"discount_or_cost_amount": function(frm) {
	},
	"additional_cost": function(frm) {
        },
});



 frappe.ui.form.on("Sales Order Item", {
	refresh: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
/*		if(frm.doc.quotation && child.prevdoc_docname){
			child.set_df_property("selling_template", "hidden", true);
		}
		else{
			cur_frm.fields_dict.child_table_name.grid.toggle_reqd("selling_template", (child.prevdoc_docname && frm.doc.quotation))
		} */
	},
	"item_code": function(frm, cdt, cdn){
	/*	var child = locals[cdt][cdn];
		cur_frm.call({
				method: "erpnext.stock.doctype.stock_price_template.stock_price_template.get_item_rate",
				args: {
					 tran_type: 'Sales',
					 item_code: child.item_code,
					 tran_date: frm.doc.transaction_date
				},
				callback: function(r) {
				   if(r.message)  { 
						frappe.model.set_value(cdt, cdn, 'item_code', r.message[0]['item_code']);
						frappe.model.set_value(cdt, cdn, 'item_name', r.message[0]['item_name']);
						frappe.model.set_value(cdt, cdn, 'qty', 0);
						frappe.model.set_value(cdt, cdn, 'rate', r.message[0]['rate']);
						//refresh_field("items"); 
				    }
				}
			}); */
		},
});


erpnext.selling.SalesOrderController = erpnext.selling.SellingController.extend({
	refresh: function(doc, dt, dn) {
		this._super();
		var allow_purchase = false;
		var allow_delivery = false;

		if(doc.docstatus==1) {
			if(doc.status != 'Closed') {

				for (var i in cur_frm.doc.items) {
					var item = cur_frm.doc.items[i];
					if(item.delivered_by_supplier === 1 || item.supplier){
						if(item.qty > flt(item.ordered_qty)
							&& item.qty > flt(item.delivered_qty)) {
							allow_purchase = true;
						}
					}

					if (item.delivered_by_supplier===0) {
						if(item.qty > flt(item.delivered_qty)) {
							allow_delivery = true;
						}
					}

					if (allow_delivery && allow_purchase) {
						break;
					}
				}

				if (this.frm.has_perm("submit")) {
					//close
					if(flt(doc.per_delivered, 2) < 100 || flt(doc.per_billed) < 100) {
							cur_frm.add_custom_button(__('Close'), this.close_sales_order, __("Status"))
						}
				}

				//Delivery Note and Payment
				if(flt(doc.per_delivered, 2) < 100 && ["Sales", "Shopping Cart"].indexOf(doc.order_type)!==-1 && allow_delivery) {
					cur_frm.add_custom_button(__('Delivery'), this.make_delivery_note, __("Make"));
					cur_frm.add_custom_button(__('Payment'), cur_frm.cscript.make_payment_entry, __("Make"));
					cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
				}

				// Make Purchase Order
				if(flt(doc.per_delivered, 2) < 100 && allow_purchase) {
					cur_frm.add_custom_button(__('Purchase Order'), cur_frm.cscript.make_purchase_order, __("Make"));
				}
	
				//Maintenance
				if(flt(doc.per_delivered, 2) < 100 &&
						["Sales", "Shopping Cart"].indexOf(doc.order_type)===-1) {
					cur_frm.add_custom_button(__('Maintenance Visit'), this.make_maintenance_visit, __("Make"));
					cur_frm.add_custom_button(__('Maintenance Schedule'), this.make_maintenance_schedule, __("Make"));
				}

			
			} else {
				if (this.frm.has_perm("submit")) {
					cur_frm.add_custom_button(__('Re-open'), cur_frm.cscript['Unclose Sales Order'], __("Status"));
				}
			}
		}
		if (this.frm.doc.docstatus===0) {
			cur_frm.add_custom_button(__('Quotation'),
				function() {
					erpnext.utils.map_current_doc({
						method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
						source_doctype: "Quotation",
						get_query_filters: {
							docstatus: 1,
							status: ["!=", "Lost"],
							order_type: cur_frm.doc.order_type,
							customer: cur_frm.doc.customer || undefined,
							company: cur_frm.doc.company
						}
					})
				}, __("Get items from"));

			}
			this.order_type(doc);
	},

	order_type: function() {
		this.frm.toggle_reqd("delivery_date", this.frm.doc.order_type == "Sales");
	},

	tc_name: function() {
		this.get_terms();
	},

	make_material_request: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_material_request",
			frm: cur_frm
		})
	},

	make_delivery_note: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
			frm: cur_frm
		})
	},

	make_sales_invoice: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
			frm: cur_frm
		})
	},
	
	make_maintenance_schedule: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_maintenance_schedule",
			frm: cur_frm
		})
	},

	make_maintenance_visit: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.selling.doctype.sales_order.sales_order.make_maintenance_visit",
			frm: cur_frm
		})
	},

	make_purchase_order: function(){
		var dialog = new frappe.ui.Dialog({
			title: __("For Supplier"),
			fields: [
				{"fieldtype": "Link", "label": __("Supplier"), "fieldname": "supplier", "options":"Supplier",
					"get_query": function () {
						return {
							query:"erpnext.selling.doctype.sales_order.sales_order.get_supplier",
							filters: {'parent': cur_frm.doc.name}
						}
					}, "reqd": 1 },
				{"fieldtype": "Button", "label": __("Make Purchase Order"), "fieldname": "make_purchase_order", "cssClass": "btn-primary"},
			]
		});

		dialog.fields_dict.make_purchase_order.$input.click(function() {
			args = dialog.get_values();
			if(!args) return;
			dialog.hide();
			return frappe.call({
				type: "GET",
				method: "erpnext.selling.doctype.sales_order.sales_order.make_purchase_order_for_drop_shipment",
				args: {
					"source_name": cur_frm.doc.name,
					"for_supplier": args.supplier
				},
				freeze: true,
				callback: function(r) {
					if(!r.exc) {
						var doc = frappe.model.sync(r.message);
						frappe.set_route("Form", r.message.doctype, r.message.name);
					}
				}
			})
		});
		dialog.show();
	},
	close_sales_order: function(){
		cur_frm.cscript.update_status("Close", "Closed")
	}	
	
});

$.extend(cur_frm.cscript, new erpnext.selling.SalesOrderController({frm: cur_frm}));

cur_frm.cscript.new_contact = function(){
	tn = frappe.model.make_new_doc_and_get_name('Contact');
	locals['Contact'][tn].is_customer = 1;
	if(doc.customer) locals['Contact'][tn].customer = doc.customer;
	frappe.set_route('Form', 'Contact', tn);
}

cur_frm.fields_dict['project'].get_query = function(doc, cdt, cdn) {
	return {
		query: "erpnext.controllers.queries.get_project_name",
		filters: {
			'customer': doc.customer
		}
	}
}


cur_frm.cscript.update_status = function(label, status){
	var doc = cur_frm.doc;
	frappe.ui.form.is_saving = true;
	frappe.call({
		method: "erpnext.selling.doctype.sales_order.sales_order.update_status",
		args: {status: status, name: doc.name},
		callback: function(r){
			cur_frm.reload_doc();
		},
		always: function() {
			frappe.ui.form.is_saving = false;
		}
	});
}

cur_frm.cscript['Unclose Sales Order'] = function() {
	cur_frm.cscript.update_status('Re-open', 'Draft')
}

cur_frm.cscript.on_submit = function(doc, cdt, cdn) {
	if(cint(frappe.boot.notification_settings.sales_order)) {
		cur_frm.email_doc(frappe.boot.notification_settings.sales_order_message);
	}
};

frappe.ui.form.on("Sales Order", "refresh", function(frm) {
    cur_frm.set_query("customer", function() {
        return {
            "filters": {
                "disabled": 0
            }
        };
    });
});

cur_frm.fields_dict['items'].grid.get_field('price_template').get_query = function(frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        return {
                query: "erpnext.controllers.queries.price_template_list",
	        filters: {'item_code': d.item_code, 'transaction_date': frm.transaction_date, 'branch': frm.branch}
	}
}


cur_frm.fields_dict['items'].grid.get_field('warehouse').get_query = function(frm, cdt, cdn) {
	item = locals[cdt][cdn]
	return {
		"query": "erpnext.controllers.queries.filter_branch_wh",
		filters: {'branch': frm.branch}
	}
}

// on_selection of price_template, auto load the seling rate for items
frappe.ui.form.on("Sales Order Item", {
        "price_template": function(frm, cdt, cdn) {
                d = locals[cdt][cdn]
		 if(cur_frm.doc.location){
                         loc = cur_frm.doc.location;
                 }else{
                         loc = "NA";
                 }
		console.log("Loc :" + loc);
                frappe.call({
                        method: "erpnext.selling.doctype.selling_price.selling_price.get_selling_rate",
                        args: {
                                "price_list": d.price_template,
                                "branch": cur_frm.doc.branch,
                                "item_code": d.item_code,
                                "transaction_date": cur_frm.doc.transaction_date,
				"location": loc
                        },
                        callback: function(r) {
                                frappe.model.set_value(cdt, cdn, "price_list_rate", r.message)
                                frappe.model.set_value(cdt, cdn, "rate", r.message)
                                cur_frm.refresh_field("price_list_rate")
                                cur_frm.refresh_field("rate")
                        }
                })
        },

	"item_code": function(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "price_template", "") 
}
})

