# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.accounts.general_ledger import make_gl_entries
from frappe import _
from erpnext.controllers.accounts_controller import AccountsController

class TDSRemittance(AccountsController):
	def validate(self):
		if self.items:
			total_bill= total_tds = 0
			for d in self.items:
				total_bill += flt(d.bill_amount)
				total_tds += flt(d.tds_amount)
				self.total_tds = total_tds 
				self.total_amount= total_bill	
		self.validate_tds_account()
		#self.duplication_entry_check()
	
	def duplication_entry_check(self):
		for i in self.items:
			check_dup = frappe.db.sql("""
				select 1 from `tabTDS Remittance Item` i
				inner join `tabTDS Remittance` t
				on i.parent = t.name
				where i.invoice_no = %s
				and t.docstatus = 1
			""", (str(i.invoice_no)))
		
			if check_dup:
				frappe.throw("TDS Remittance entry for '{0}' is already processed".format(i.invoice_no))


	def validate_tds_account(self):
		if self.tds_rate == 2:
			self.tds_account = frappe.db.get_single_value ("Accounts Settings", "tds_2_account")
		if self.tds_rate ==3 :
			self.tds_account = frappe.db.get_single_value ("Accounts Settings", "tds_3_account")
		if self.tds_rate == 5:
                        self.tds_account = frappe.db.get_single_value ("Accounts Settings", "tds_5_account")
                if self.tds_rate ==10:
                        self.tds_account = frappe.db.get_single_value ("Accounts Settings", "tds_10_account")


	def on_submit(self):
		self.post_gl_entry()


	def on_cancel(self):
		self.post_gl_entry()

	
	def get_details(self):
		query = """ select d.posting_date, d.party, d.name as invoice_no, d.invoice_date, d.taxable_amount as bill_amount, d.tds_amount, (select vendor_tpn_no from `tabSupplier` where name = d.party) as vendor_tpn_no from 
                                `tabDirect Payment` d  where tds_percent = '{0}' 
                                and d.posting_date >= '{1}' and d.posting_date <= '{2}' 
                                and docstatus = 1 
                                and not exists (
                                        select 1 from `tabTDS Remittance Item` i
                                        inner join `tabTDS Remittance` t
                                        on i.parent = t.name
                                        where i.invoice_no = d.name
                                        and t.docstatus = 1
                                )
				union all 
                                select p.posting_date, p.supplier, p.name, p.bill_date as invoice_date, p.tds_taxable_amount as bill_amount, p.tds_amount, (select vendor_tpn_no from `tabSupplier` where name = p.supplier) as vendor_tpn_no
                                from `tabPurchase Invoice` p where tds_rate = '{0}' and docstatus =1 
                                and posting_date >= '{1}' and posting_date<= '{2}'
				and not exists (
                                        select 1 from `tabTDS Remittance Item` i
                                        inner join `tabTDS Remittance` t
                                        on i.parent = t.name
                                        where i.invoice_no = p.name
                                        and t.docstatus = 1
                                ) """.format(self.tds_rate, self.from_date, self.to_date)	
		

		entries = frappe.db.sql(query, as_dict=True)
		if not entries:
			frappe.msgprint("No Record Found")

		self.set('items', [])

		for d in entries:
			row = self.append('items', {})
			row.update(d)	

        def post_gl_entry(self):
		cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")
                gl_entries   = []
               	if self.total_tds > 0:
			gl_entries.append(
				self.get_gl_dict({
					"account": self.tds_account,
                        		"debit": self.total_tds,
                   			"debit_in_account_currency": self.total_tds,
                    			"voucher_no": self.name,
                        		"voucher_type": self.doctype,
                       			"cost_center": cost_center,
                       			"business_activity": 'Common'
                                               }))
                                
			gl_entries.append(
				self.get_gl_dict({
               				"account": self.account,
                        		"credit": self.total_tds,
                       			"credit_in_account_currency": self.total_tds,
                      			"voucher_no": self.name,
                       			"voucher_type": self.doctype,
                        		"cost_center": cost_center,
                      			"business_activity": 'Common'
                                               }))
			make_gl_entries(gl_entries, cancel=(self.docstatus == 2),update_outstanding="No", merge_entries=False)
		else:
                        frappe.throw("Total TDS Amount is Zero")
		
