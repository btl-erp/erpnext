# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from erpnext.accounts.utils import get_child_cost_centers, get_period_date
from frappe.utils import flt, rounded
from erpnext.custom_utils import get_production_groups
from erpnext.production.doctype.production_target.production_target import get_target_value

def execute(filters=None):
	build_filters(filters)
	columns = get_columns(filters)
	data = get_data(filters)

	return columns, data

def build_filters(filters):
	filters.is_company = frappe.db.get_value("Cost Center", filters.cost_center, "is_company")
	filters.from_date, filters.to_date = get_period_date(filters.fiscal_year, filters.report_period, filters.cumulative)

def get_data(filters):
	data = []
	cc_condition = get_cc_conditions(filters)
	conditions = get_filter_conditions(filters)

	group_by = get_group_by(filters)
	order_by = get_order_by(filters)
	abbr = " - " + str(frappe.db.get_value("Company", filters.company, "abbr"))

	#query = "select pe.cost_center, pe.branch, pe.location, cc.parent_cost_center as region, sum(qty) as total_qty from `tabProduction Entry` pe RIGHT JOIN `tabCost Center` cc ON cc.name = pe.cost_center where 1 = 1 {0} {1} {2} {3}".format(cc_condition, conditions, group_by, order_by)

	query = "select pe.cost_center, pe.branch, pe.location, cc.parent_cost_center as region from `tabProduction Target` pe, `tabCost Center` cc where cc.name = pe.cost_center and pe.fiscal_year = {0} {1} {2} {3}".format(filters.fiscal_year, cc_condition, group_by, order_by)
	amt = 0
	for a in frappe.db.sql(query, as_dict=1):
		if filters.branch:
			target = get_target_value("Disposal", a.location, filters.production_group, filters.fiscal_year, filters.from_date, filters.to_date, True)
			row = [a.location, target]
			cond = " and dni.location = '{0}'".format(a.location)
		else:
			if filters.is_company:
				target = get_target_value("Disposal", a.region, filters.production_group, filters.fiscal_year, filters.from_date, filters.to_date)
				all_ccs = get_child_cost_centers(a.region)
				cond = " and dni.cost_center in {0} ".format(tuple(all_ccs))	
				a.region = str(a.region).replace(abbr, "")
				row = [a.region, target]
			else:
				target = get_target_value("Disposal", a.cost_center, filters.production_group, filters.fiscal_year, filters.from_date, filters.to_date)
				row = [a.branch, target]
				cond = " and dni.cost_center = '{0}'".format(a.cost_center)
	
		total = 0
		total_amt = 0
		for b in get_production_groups(filters.production_group):
		#	qty = frappe.db.sql("select sum(pe.qty) from `tabProduction Entry` pe where 1 = 1 {0} and pe.item_sub_group = '{1}' {2}".format(conditions, str(b), cond))
			qty = frappe.db.sql("Select sum(dni.qty), sum(dni.amount)  from `tabDelivery Note` dn INNER JOIN `tabDelivery Note Item` dni on dn.name = dni.parent where 1=1 {0} and dni.item_sub_group = '{1}' {2}".format(conditions, str(b), cond))	
			amt = qty and qty[0][1] or 0
			qty = qty and qty[0][0] or 0
			row.append(rounded(qty, 2))
			
			total += flt(qty)
			total_amt += flt(amt)
		row.append(total_amt)
		row.insert(2, rounded(total, 2))
		if target == 0:
			target = 1
		row.insert(3, rounded(100 * total/target, 2))
		data.append(row)

	return data

def get_group_by(filters):
	if filters.branch:
		group_by = " group by region, branch, location"
	else:
		if filters.is_company:
			group_by = " group by region"
		else:
			group_by = " group by region, branch"

	return group_by

def get_order_by(filters):
	return " order by region, location"

def get_cc_conditions(filters):
	if not filters.cost_center:
		return " and pe.docstatus = 10"

	all_ccs = get_child_cost_centers(filters.cost_center)
	condition = " and cc.name in {0} ".format(tuple(all_ccs))	

	return condition

def get_filter_conditions(filters):
	condition = ""
	if filters.location:
		condition += " and dni.location = '{0}'".format(filters.location)

	if filters.from_date and filters.to_date:
		condition += " and dn.posting_date between '{0}' and '{1}'".format(filters.from_date, filters.to_date)

	return condition

def get_columns(filters):
	if filters.branch:
		columns = ["Location:Link/Location:150", "Target Qty:Float:120", "Achieved Qty:Float:120", "Ach. Percent:Percent:100"]
	else:
		if filters.is_company:
			columns = ["Region:Data:150", "Target Qty:Float:120", "Achieved Qty:Float:120", "Ach. Percent:Percent:100"]
		else:
			columns = ["Branch:Link/Branch:150", "Target Qty:Float:120", "Achieved Qty:Float:120", "Ach. Percent:Percent:100"]

	for a in get_production_groups(filters.production_group):
		columns.append(str(str(a) + ":Float:100"))
		
	columns.append("Sales Amount:Currency:120")
	
	return columns

