# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.desk.reportview import get_match_cond
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import flt, getdate
from erpnext.custom_utils import check_future_date, get_branch_cc, prepare_gl, prepare_sl, check_budget_available
from erpnext.controllers.stock_controller import StockController
from erpnext.maintenance.report.maintenance_report import get_pol_till
from erpnext.stock.utils import get_stock_balance
from erpnext.maintenance.maintenance_utils import get_without_fuel_hire, get_equipment_ba

class IssuePOL(StockController):
	def validate(self):
		check_future_date(self.posting_date)
		self.validate_branch()
		self.populate_data()
		self.validate_data()
		self.validate_branch()
		self.validate_posting_time()
		self.validate_uom_is_integer("stock_uom", "qty")
		self.check_on_dry_hire()

	def validate_branch(self):
		if self.purpose == "Issue" and self.is_hsd_item and not self.tanker:
			frappe.throw("For HSD Issues, Tanker is Mandatory")

		if not self.is_hsd_item:
			self.tanker = ""

		if self.tanker and self.branch != frappe.db.get_value("Equipment", self.tanker, "branch"):
			frappe.throw("Selected Branch and Equipment Branch does not match")

	def populate_data(self):
		self.cost_center = get_branch_cc(self.branch)

	def validate_warehouse(self):
		self.validate_warehouse_branch(self.branch, self.warehouse)

	def validate_data(self):
		if not self.purpose:
			frappe.throw("Purpose is Missing")
		if not self.cost_center or not self.warehouse:
			frappe.throw("Cost Center and Warehouse are Mandatory")
		total_quantity = 0
		for a in self.items:
			no_tank = frappe.db.get_value("Equipment Type", frappe.db.get_value("Equipment", a.equipment, "equipment_type"), "no_own_tank")
			if no_tank and self.purpose == "Issue":
				frappe.throw("Cannot Issue to Equipments without own tank " + str(a.equipment))
			if not a.equipment_warehouse or not a.equipment_cost_center:
				frappe.throw("<b>"+str(a.equipment_number) + "</b> does have a Warehouse and Cost Center Defined")
			if not flt(a.qty) > 0:
				frappe.throw("Quantity for <b>"+str(a.equipment_number)+"</b> should be greater than 0")
			total_quantity = flt(total_quantity) + flt(a.qty)
		self.total_quantity = total_quantity

	def check_on_dry_hire(self):
                for a in self.items:
                        record = get_without_fuel_hire(a.equipment, self.posting_date, self.posting_time)
                        if record:
                                data = record[0]
                                a.hiring_cost_center = data.cc
                                a.hiring_branch =  data.br
                        else:
                                a.hiring_cost_center = None
                                a.hiring_branch =  None
                                a.hiring_warehouse = None

	def on_submit(self):
		if not self.items:
			frappe.throw("Should have a POL Issue Details to Submit")
		self.validate_data()
		self.check_on_dry_hire()
		self.check_dry_hire_wh()
		self.check_tanker_hsd_balance()
		self.update_stock_gl_ledger(1, 1)
		self.make_pol_entry()

	def check_dry_hire_wh(self):
                for a in self.items:
			if a.hiring_branch and not a.hiring_warehouse:
				frappe.throw("Select hiring warehouse for row {0}".format(a.idx))

	def update_stock_gl_ledger(self, post_gl=None, post_sl=None, map_rate=None):
		sl_entries = []
		gl_entries = []

		wh_account = frappe.db.get_value("Account", {"account_type": "Stock", "warehouse": self.warehouse}, "name")
		if not wh_account:
			frappe.throw(str(self.warehouse) + " is not linked to any account.")

		for a in self.items:
			#from erpnext.stock.stock_ledger import get_valuation_rate
			if a.hiring_branch:
                                comparing_branch = a.hiring_branch
                        else:
                                comparing_branch = a.equipment_branch

                        if a.hiring_cost_center:
                                cc = a.hiring_cost_center
                        else:
                                cc = a.equipment_cost_center

                        if a.hiring_warehouse:
                                wh = a.hiring_warehouse
                        else:
                                wh = a.equipment_warehouse

			if not map_rate:
				stock_qty, map_rate = get_stock_balance(self.pol_type, self.warehouse, self.posting_date, self.posting_time, with_valuation_rate=True)
				#map_rate = get_valuation_rate(self.pol_type, self.warehouse)
                        valuation_rate = flt(a.qty) * flt(map_rate)

			if self.is_hsd_item:
				ec = frappe.db.get_value("Equipment", a.equipment, "equipment_category")
				budget_account = frappe.db.get_value("Equipment Category", ec, "budget_account")
			else:
				budget_account = frappe.db.get_value("Item", self.pol_type, "expense_account")
			if not budget_account:
				frappe.throw("Set Budget Account in Equipment Category")		

			if self.purpose == "Issue":
				sl_entries.append(prepare_sl(self, 
						{
							"actual_qty": -1 * flt(a.qty), 
							"warehouse": self.warehouse, 
							"incoming_rate": 0 
						}))

				gl_entries.append(
					prepare_gl(self, {"account": wh_account,
							 "credit": flt(valuation_rate),
							 "credit_in_account_currency": flt(valuation_rate),
							 "cost_center": self.cost_center,
							 "business_activity": get_equipment_ba(self.tanker)
							})
					)

				gl_entries.append(
					prepare_gl(self, {"account": budget_account,
							 "debit": flt(valuation_rate),
							 "debit_in_account_currency": flt(valuation_rate),
							 "cost_center": cc,
							 "business_activity": get_equipment_ba(a.equipment)
							})
					)
				
				#Do IC Accounting Entry if different branch
				if comparing_branch != self.branch:
					allow_inter_company_transaction = frappe.db.get_single_value("Accounts Settings", "auto_accounting_for_inter_company")
					if allow_inter_company_transaction:
						ic_account = frappe.db.get_single_value("Accounts Settings", "intra_company_account")
						if not ic_account:
							frappe.throw("Setup Intra-Company Account in Accounts Settings")
						gl_entries.append(
							prepare_gl(self, {"account": ic_account,
									 "debit": flt(valuation_rate),
									 "debit_in_account_currency": flt(valuation_rate),
									 "cost_center": self.cost_center,
									 "business_activity": get_equipment_ba(self.tanker)
									})
							)

						gl_entries.append(
							prepare_gl(self, {"account": ic_account,
									 "credit": flt(valuation_rate),
									 "credit_in_account_currency": flt(valuation_rate),
									 "cost_center": cc,
									 "business_activity": get_equipment_ba(a.equipment)
									})
							)
					
			else : #Transfer only if different warehouse
				if wh != self.warehouse:
					#Stock Ledger Entries
					sl_entries.append(prepare_sl(self, 
							{
								"actual_qty": -1 * flt(a.qty), 
								"warehouse": self.warehouse, 
								"incoming_rate": 0 
							}))

					sl_entries.append(prepare_sl(self,
							{
								"actual_qty": flt(a.qty), 
								"warehouse": wh, 
								"incoming_rate": flt(map_rate)
							}))

				#Do IC Accounting Entry if different branch
				if comparing_branch != self.branch:
					twh_account = frappe.db.get_value("Account", {"account_type": "Stock", "warehouse": wh}, "name")
					if not twh_account:
						frappe.throw(str(self.warehouse) + " is not linked to any account.")

					gl_entries.append(
						prepare_gl(self, {"account": wh_account,
								 "credit": flt(valuation_rate),
								 "credit_in_account_currency": flt(valuation_rate),
								 "cost_center": self.cost_center,
								 "business_activity": get_equipment_ba(self.tanker)
								})
						)

					gl_entries.append(
						prepare_gl(self, {"account": twh_account,
								 "debit": flt(valuation_rate),
								 "debit_in_account_currency": flt(valuation_rate),
								 "cost_center": cc,
								 "business_activity": get_equipment_ba(a.equipment)
								})
						)

					allow_inter_company_transaction = frappe.db.get_single_value("Accounts Settings", "auto_accounting_for_inter_company")
					if allow_inter_company_transaction:
						ic_account = frappe.db.get_single_value("Accounts Settings", "intra_company_account")
						if not ic_account:
							frappe.throw("Setup Intra-Company Account in Accounts Settings")
						gl_entries.append(
							prepare_gl(self, {"account": ic_account,
									 "debit": flt(valuation_rate),
									 "debit_in_account_currency": flt(valuation_rate),
									 "cost_center": self.cost_center,
									 "business_activity": get_equipment_ba(self.tanker)
									})
							)

						gl_entries.append(
							prepare_gl(self, {"account": ic_account,
									 "credit": flt(valuation_rate),
									 "credit_in_account_currency": flt(valuation_rate),
									 "cost_center": cc,
									 "business_activity": get_equipment_ba(a.equipment)
									})
							)

		if sl_entries: 
			if self.docstatus == 2:
				sl_entries.reverse()

			if post_sl:
				self.make_sl_entries(sl_entries, self.amended_from and 'Yes' or 'No')

		if gl_entries:
			from erpnext.accounts.general_ledger import make_gl_entries
			if post_gl:
				make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=True)
			else:
				return gl_entries

	def on_cancel(self):
		self.update_stock_gl_ledger(1, 1)
		self.delete_pol_entry()

	def check_tanker_hsd_balance(self):
		if not self.tanker:
			return
		received_till = get_pol_till("Stock", self.tanker, self.posting_date, self.pol_type)
		issue_till = get_pol_till("Issue", self.tanker, self.posting_date, self.pol_type)
		balance = flt(received_till) - flt(issue_till)
		if flt(self.total_quantity) > flt(balance):
			frappe.throw("Not enough balance in tanker to issue. The balance is " + str(balance))	

	def make_pol_entry(self):
		if getdate(self.posting_date) <= getdate("2018-03-31"):
			return
		if self.tanker:
			con = frappe.new_doc("POL Entry")
			con.flags.ignore_permissions = 1
			con.company = self.company
			con.equipment = self.tanker
			con.pol_type = self.pol_type
			con.branch = self.branch
			con.date = self.posting_date
			con.posting_time = self.posting_time
			con.qty = self.total_quantity
			con.reference_type = "Issue POL"
			con.reference_name = self.name
			con.type = "Issue"
			con.is_opening = 0
			con.submit()

		for a in self.items:
			if self.branch == a.equipment_branch:
				own = 1
			else:
				own = 0
			con = frappe.new_doc("POL Entry")
			con.flags.ignore_permissions = 1
			con.equipment = a.equipment
			con.company = self.company
			con.pol_type = self.pol_type
			con.branch = a.equipment_branch
			con.date = self.posting_date
			con.posting_time = self.posting_time
			con.qty = a.qty
			con.reference_type = "Issue POL"
			con.reference_name = self.name
			con.own_cost_center = own
			if self.purpose == "Issue":
				con.type = "Receive"
			else:
				con.type = "Stock"
			con.is_opening = 0
			con.submit()

	def delete_pol_entry(self):
		frappe.db.sql("delete from `tabPOL Entry` where reference_name = %s", self.name)

def equipment_query(doctype, txt, searchfield, start, page_len, filters):
	if not filters['branch']:
		filters['branch'] = '%'
        return frappe.db.sql("""
                        select
                                e.name,
                                e.equipment_type,
                                e.equipment_number
                        from `tabEquipment` e
                        where e.branch like %(branch)s
                        and e.is_disabled != 1
                        and e.not_cdcl = 0
                        and exists(select 1
                                     from `tabEquipment Type` t
                                    where t.name = e.equipment_type
                                      and t.is_container = 1)
                        and (
                                {key} like %(txt)s
                                or
                                e.equipment_type like %(txt)s
                                or
                                e.equipment_number like %(txt)s
                        )
                        {mcond}
                        order by
                                if(locate(%(_txt)s, e.name), locate(%(_txt)s, e.name), 99999),
                                if(locate(%(_txt)s, e.equipment_type), locate(%(_txt)s, e.equipment_type), 99999),
                                if(locate(%(_txt)s, e.equipment_number), locate(%(_txt)s, e.equipment_number), 99999),
                                idx desc,
                                e.name, e.equipment_type, e.equipment_number
                        limit %(start)s, %(page_len)s
                        """.format(**{
                                'key': searchfield,
                                'mcond': get_match_cond(doctype)
                        }),
                        {
				"txt": "%%%s%%" % txt,
				"_txt": txt.replace("%", ""),
				"start": start,
				"page_len": page_len,
                                "branch": filters['branch']
			})

