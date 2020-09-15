# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, cstr

def execute(filters=None):
	validate_filters(filters);
	columns = get_columns();
	queries = construct_query(filters);
	data = get_data(queries, filters);

	return columns, data

def get_data(query, filters=None):
	data = []
	datas = frappe.db.sql(query, (filters.from_date, filters.to_date), as_dict=True);
	for d in datas:
		row = [d.entry_date, d.item_code, d.item_name, d.serial_number, d.equipment_type, d.equipment_model, d.reg_number, d.brand, d.engine_no,
			d.chesis_no, d.qty, d.custodian, d.issued_date, d.amount]
		data.append(row);
	return data

def construct_query(filters=None):
	query = """select id.serial_number, id.entry_date, id.item_code, id.item_name, id.qty,id.serial_number, 
			id.equipment_type, id.equipment_model, id.reg_number, id.brand, id.engine_no, id.chesis_no,
			(select e.employee_name from tabEmployee as e where e.name = id.issued_to) as custodian, 
			id.issued_date, id.amount from `tabAsset Issue Details` as id
			where id.docstatus = 1 and id.entry_date between %s and %s
			order by id.creation asc
			"""
	return query;

def validate_filters(filters):
	if not filters.fiscal_year:
		frappe.throw(_("Fiscal Year {0} is required").format(filters.fiscal_year))

	fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	if not fiscal_year:
		frappe.throw(_("Fiscal Year {0} does not exist").format(filters.fiscal_year))
	else:
		filters.year_start_date = getdate(fiscal_year.year_start_date)
		filters.year_end_date = getdate(fiscal_year.year_end_date)

	if not filters.from_date:
		filters.from_date = filters.year_start_date

	if not filters.to_date:
		filters.to_date = filters.year_end_date

	filters.from_date = getdate(filters.from_date)
	filters.to_date = getdate(filters.to_date)

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

	if (filters.from_date < filters.year_start_date) or (filters.from_date > filters.year_end_date):
		frappe.msgprint(_("From Date should be within the Fiscal Year. Assuming From Date = {0}")\
			.format(formatdate(filters.year_start_date)))

		filters.from_date = filters.year_start_date

	if (filters.to_date < filters.year_start_date) or (filters.to_date > filters.year_end_date):
		frappe.msgprint(_("To Date should be within the Fiscal Year. Assuming To Date = {0}")\
			.format(formatdate(filters.year_end_date)))
		filters.to_date = filters.year_end_date


def get_columns():
	return [
		{
		  "fieldname": "entry_date",
		  "label": "Entry Date",
		  "fieldtype": "Date",
		  "width": 100
		},
		{
		  "fieldname": "item_code",
		  "label": "Material Code",
		  "fieldtype": "Link",
		  "options": "Item",
		  "width": 200
		},
		{
		  "fieldname": "item_name",
		  "label": "Material Name",
		  "fieldtype": "Data",
		  "width": 150
		},
		{
		  "fieldname": "serial",
		  "label": "Serial Number",
		  "fieldtype": "Data",
		  "width": 120
		},
		{
                  "fieldname": "equipment_type",
                  "label": "Equipment Type",
                  "fieldtype": "Data",
                  "width": 120
                },
		{
                  "fieldname": "equipment_model",
                  "label": "Equipment Model",
                  "fieldtype": "Data",
                  "width": 120
                },
		{
                  "fieldname": "reg_number",
                  "label": "Registration Number",
                  "fieldtype": "Data",
                  "width": 120
                },
		{
                  "fieldname": "brand",
                  "label": "Brand",
                  "fieldtype": "Data",
                  "width": 120
                },
		{
                  "fieldname": "engine_no",
                  "label": "Engine Number",
                  "fieldtype": "Data",
                  "width": 120
                },
		{
                  "fieldname": "chesis_no",
                  "label": "Chesis Number",
                  "fieldtype": "Data",
                  "width": 120
                },
		
		{
		  "fieldname": "qty",
		  "label": "Quantity",
		  "fieldtype": "Data",
		  "width": 100
		},
		{
		  "fieldname": "issued_to",
		  "label": "Custodian",
		  "fieldtype": "Link",
		  "options": "Employee",
		  "width": 150
		},
		{
		  "fieldname": "issued_date",
		  "label": "Issued Date",
		  "fieldtype": "Date",
		  "width": 100
		},
		{
		  "fieldname": "amount",
		  "label": "Gross Amount",
		  "fieldtype": "Currency",
		  "width": 120
		}
	]
