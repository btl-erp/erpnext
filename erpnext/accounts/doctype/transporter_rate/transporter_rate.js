// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Transporter Rate', {
	setup: function(frm) {
		frm.get_field('items').grid.editable_fields = [
			{fieldname: 'equipment_type', columns: 2},
			{fieldname: 'item_code', columns: 3},
			{fieldname: 'lower_rate', columns: 2},
			{fieldname: 'higher_rate', columns: 2},
			{fieldname: 'unloading_rate', columns: 1}
		];
	},
	refresh: function(frm) {

	}
});
