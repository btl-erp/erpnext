# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint

class SellingPrice(Document):
	def validate(self):
		self.check_sp_rate()

	def on_update(self):
		self.check_duplicate_entries()
		self.check_duplicate_settings()

	def check_sp_rate(self):
		for a in self.item_rates:
			if not flt(a.selling_price) > 0:
				frappe.throw("Selling Rate should be greater than 0 for <b>" + str(a.particular) + "</b>")

			if a.price_based_on == "Item":
				a.item_name = frappe.db.get_value("Item", a.particular, "item_name")
			else:
				a.item_name = None


	def check_duplicate_entries(self):
                branches = frappe.db.sql("select branch, count(branch) as num from `tabSelling Price Branch` where parent = %s group by branch having num > 1", self.name, as_dict=1)
                for a in branches:
                        frappe.throw("Branch <b>" + str(a.branch) + "</b> has been defined more than once")
	
                sps = frappe.db.sql("select particular, count(particular) as num from `tabSelling Price Rate` where parent = %s group by particular having num > 1", self.name, as_dict=1)
                for a in sps:
			if a.particular:
				frappe.throw("<b>" + str(a.particular) + "</b> has been defined more than once")

	def check_duplicate_settings(self):
                #Check branch duplicate
                item_list = []
                for a in self.item_rates:
                        item_list.append(str(a.particular))
		
		branch_list = [str(d.branch) for d in self.get("item_branch")]
		branch_list.append(str("DUMMY"))
	
                for a in frappe.db.sql("select a.branch, b.name from `tabSelling Price Branch` a, `tabSelling Price` b where a.parent = b.name and b.name != %s and a.branch in {0} and (%s between b.from_date and b.to_date or %s between b.from_date and b.to_date or (%s > b.from_date and %s < b.to_date) or (%s < b.from_date and %s > b.to_date))".format(tuple(branch_list)), (self.name, self.from_date, self.to_date, self.from_date, self.to_date, self.from_date, self.to_date), as_dict=1):
                        #check for Item duplicate
                        doc = frappe.get_doc("Selling Price", a.name)
                        for b in doc.item_rates:
                                if str(b.particular) in item_list:
					frappe.throw("<b>"+str(b.particular) + "</b> already defined for the same period in <b>"+str(frappe.get_desk_link(self.doctype, a.name))+"</b>")


@frappe.whitelist()
def get_cop_amount(cop, branch, posting_date, item_code):
	if not cop or not branch or not posting_date or not item_code:
		frappe.throw("COP, Branch, Item Code and Posting Date are mandatory")
	item_sub_group = frappe.db.get_value("Item", item_code, "item_sub_group")
	if not item_sub_group:
		frappe.db.sql("No Item Sub Group Assigned")
	cop_amount = frappe.db.sql("select cop_amount from `tabCOP Rate Item` where parent = %s and item_sub_group = %s", (cop, item_sub_group), as_dict=1)
	return cop_amount and flt(cop_amount[0].cop_amount) or 0.0


@frappe.whitelist()
def get_selling_rate(price_list, branch, item_code, transaction_date):
        if not branch or not item_code or not transaction_date:
                frappe.throw("Select Item Code or Branch or Posting Date")
	rate=""
	
	rate = frappe.db.sql(""" select selling_price as rate from `tabSelling Price Rate` where parent = '{0}' and particular = '{1}' """.format(price_list, item_code), as_dict =1)
		
        return rate and flt(rate[0].rate) or 0.0

