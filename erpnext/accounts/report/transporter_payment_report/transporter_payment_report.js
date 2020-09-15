// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Transporter Payment Report"] = {
"filters": [
	{
	"fieldname":"branch",
	"label": ("Branch"),
	"fieldtype": "Link",
	"options": "Branch",
	"width": "100",
	},
	{
	"fieldname": "from_date",
	"label": __("From Date"),
	"fieldtype": "Date",
	"default": frappe.defaults.get_user_default("year_start_date"),
	},
	{	
	"fieldname": "to_date",
	"label": __("To Date"),
	"fieldtype": "Date",
	"default": frappe.defaults.get_user_default("year_end_date"),
	},
	{
	"fieldname":"equipment_type",
	"label": ("Equipment Type"),
	"fieldtype": "Link",
	"options": "Equipment Type",
	"width": "100",
	}

]
}
