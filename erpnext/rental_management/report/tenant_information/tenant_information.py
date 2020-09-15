# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns  = get_columns()
	data = get_data(filters)
	return columns, data


def get_data(filters):
	query = """select branch, tenant_name, cid, customer_code, dzongkhag, location,
town_category, building_classification, building_category, block_no,
flat_no, ministry_agency, department, designation, employee_id, grade, mobile_no, dob, date_of_appointment, pf_account_no, tenant_dzongkhag, gewog, village, floor_area, rate_per_sq_ft, rent_amount, security_deposit, receipt_no, receipt_date, area, repayment_period, original_monthly_instalment, allocated_date, status, surrendered_date from `tabTenant Information` where docstatus = 1"""
	return frappe.db.sql(query) 
		


def get_columns():
	return[
		("Branch") + ":Link/Branch:120",
		("Tenant Name") + ":Data:120",
		("CID No.") + ":Data:100",
		("Customer Code") + ":Data:80",
		("Tenant Dzongkhag") + ":Data:120",
		("location") + ":Data:120",
		("Town Category") + ":Data:120",
		("Building Classification") + ":Data:120",
		("Building Category") + ":Data:120",
        	("Block No") + ":Data:80",
		("Flat No") + ":Data:80",
		("Ministry/Agency") + ":Data:120",
		("Department") + ":Data:120",
		("Designation") + ":Data:120",
		("Employee ID") + ":Data:120",
		("Grade") + ":Data:120",
        	("Mobile No") + ":Data:120",
		("Date of Birth") + ":Data:120",
		("Date of Appointment In Service") + ":Data:120",
		("Provident Fund A/C No.") + ":Data:120",
		("Dzongkhag") + ":Data:120",
		("Gewog") + ":Data:120",
		("Village") + ":Data:120",
		("Floot Area (Sqft)") + ":Data:120",
		("Rate per Sqft") + ":Data:120",
		("Rent Amount") + ":Currency:120",
		("Security Deposit") + ":Currency:120",
		("SD Receipt No.") + ":Data:120",
		("SD Receipt Date") + ":Date:100",
        	("House No") + ":Data:120",
		("Land area (Sq.m)") + ":Data:100",
		("Repayment Period") + ":Data:100",
		("Original Monthly Installment") + ":Data:120",
		("Allocated Date") + ":Data:120",
		("Rental Status") + ":Data:100",
		("Surrendered Date") + ":Data:100"
		]	
