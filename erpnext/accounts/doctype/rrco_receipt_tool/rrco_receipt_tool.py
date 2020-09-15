# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document


class RRCOReceiptTool(Document):
	pass


@frappe.whitelist()
def get_invoices(purpose = None, start_date=None, end_date=None, tds_rate=2):
	invoices_not_marked = []
	invoices_marked = []
	query = ""
	if tds_rate == '1234567890':
		query = "select  \'" + str(purpose) + "\' as purpose, name, application_date as posting_date, concat(employee_name, \" (\",  name, \")\") bill_no, '' as supplier FROM `tabLeave Encashment` AS a WHERE a.docstatus = 1 AND a.application_date BETWEEN \'" + str(start_date) + "\' AND \'" + str(end_date) + "\' AND NOT EXISTS (SELECT 1 FROM `tabRRCO Receipt Entries` AS b WHERE b.purchase_invoice = a.name);"
	else:
		query = "select \'" + str(purpose) + "\' as purpose, name, posting_date, bill_no, supplier FROM `tabPurchase Invoice` AS a WHERE docstatus = 1 AND posting_date BETWEEN \'" + str(start_date) + "\' AND \'" + str(end_date) + "\' AND tds_rate = " + str(tds_rate) + " AND NOT EXISTS (SELECT 1 FROM `tabRRCO Receipt Entries` AS b WHERE b.purchase_invoice = a.name) UNION select \'" + str(purpose) + "\' as purpose, name, posting_date, name as bill_no, party as supplier FROM `tabDirect Payment` AS a WHERE docstatus = 1 AND posting_date BETWEEN \'" + str(start_date) + "\' AND \'" + str(end_date) + "\' AND tds_percent = " + str(tds_rate) + " AND NOT EXISTS (SELECT 1 FROM `tabRRCO Receipt Entries` AS b WHERE b.purchase_invoice = a.name);"
	
	invoice_list = frappe.db.sql(query, as_dict=True);
	return {
		"marked": invoices_marked,
		"unmarked": invoice_list 
	}


@frappe.whitelist()
def mark_invoice(invoice_list=None, receipt_number=None, receipt_date=None, cheque_number=None, cheque_date=None):
	invoice_list = json.loads(invoice_list)
	for invoice in invoice_list:
		rrco = frappe.new_doc("RRCO Receipt Entries")
		rrco.purpose = invoice['purpose']
		rrco.supplier = invoice['supplier']
		rrco.bill_no = invoice['bill_no']
		rrco.purchase_invoice = invoice['name']
		rrco.receipt_date = str(receipt_date)
		rrco.receipt_number = str(receipt_number)
		rrco.cheque_number = str(cheque_number)
		rrco.cheque_date = str(cheque_date)
		rrco.submit()

@frappe.whitelist()
def updateSalaryTDS(purpose = None, month=None, fiscal_year=None, receipt_number=None, receipt_date=None, cheque_number=None,cheque_date=None):
	chk_value = frappe.db.get_value("RRCO Receipt Entries", {"fiscal_year": str(fiscal_year), "month": str(month)})
	if chk_value:
		frappe.throw("RRCO Receipt and date has been already assigned for the given month and fiscal year")
	else:
		rrco = frappe.new_doc("RRCO Receipt Entries")
		rrco.purpose = str(purpose)
		rrco.fiscal_year = str(fiscal_year)
		rrco.month = str(month)
		rrco.receipt_date = str(receipt_date)
		rrco.receipt_number = str(receipt_number)
		rrco.cheque_number = str(cheque_number)
		rrco.cheque_date = str(cheque_date)
		rrco.submit()

		return "DONE"

@frappe.whitelist()
def updateBonus(purpose=None, fiscal_year=None, receipt_number=None, receipt_date=None, cheque_number=None,cheque_date=None):
	chk_value = frappe.db.get_value("RRCO Receipt Entries", {"fiscal_year": str(fiscal_year), "purpose": str(purpose)})
	if chk_value:
		frappe.throw("RRCO Receipt and date has been already assigned for the given fiscal year for Annual Bonus")
	else:
		rrco = frappe.new_doc("RRCO Receipt Entries")
		rrco.purpose = str(purpose)
		rrco.fiscal_year = str(fiscal_year)
		rrco.receipt_date = str(receipt_date)
		rrco.receipt_number = str(receipt_number)
		rrco.cheque_number = str(cheque_number)
		rrco.cheque_date = str(cheque_date)
		rrco.submit()

		return "DONE"

@frappe.whitelist()
def updatePBVA(purpose=None, fiscal_year=None, receipt_number=None, receipt_date=None, cheque_number=None,cheque_date=None):
	chk_value = frappe.db.get_value("RRCO Receipt Entries", {"fiscal_year": str(fiscal_year), "purpose": str(purpose)}, "name")
	if chk_value:
		frappe.throw("RRCO Receipt and date has been already assigned for the given fiscal year for PBVA")
	else:
		rrco = frappe.new_doc("RRCO Receipt Entries")
		rrco.purpose = str(purpose)
		rrco.fiscal_year = str(fiscal_year)
		rrco.receipt_date = str(receipt_date)
		rrco.receipt_number = str(receipt_number)
		rrco.cheque_number = str(cheque_number)
		rrco.cheque_date = str(cheque_date)
		rrco.submit()

		return "DONE"
