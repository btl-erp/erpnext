# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime
from frappe.model.document import Document
from erpnext.crm_utils import add_user_roles, remove_user_roles

class Site(Document):
	def validate(self):
		self.validate_defaults()
		self.add_user_roles()
		self.validate_items()
		self.update_customer()

	def on_trash(self):
		""" remove role `CRM Customer` if no sites available for the user """
		if not frappe.db.exists("Site", {"user": self.user, "name": ("!=", self.name)}):
			remove_user_roles(self.user, "CRM Customer")

	def add_user_roles(self):
		""" add role `CRM Customer` """
		add_user_roles(self.user, "CRM Customer")

	def update_customer(self):
		""" create/update Customer based on CID """
		if frappe.db.exists("Customer", {"customer_id": self.user}):
			#doc = frappe.get_doc("Customer", {"customer_id": self.user})
			return
		else:
			doc = frappe.new_doc("Customer")

		ua = frappe.get_doc("User Account", self.user)
		customer_address = [ua.first_name, ua.last_name, ua.billing_address_line1, ua.billing_address_line2,
					ua.billing_dzongkhag, ua.billing_gewog, ua.billing_pincode]
		customer_address = [i for i in customer_address if i]
		customer_address = "\n".join(customer_address) if customer_address else doc.customer_details
		doc.customer_name = ua.full_name if ua.full_name else frappe.db.get_value("User", self.user, "full_name")	
		doc.customer_group= "Domestic"
		doc.territory	  = "Bhutan"
		doc.customer_type = "Domestic Customer"
		doc.customer_id	  = ua.user
		doc.dzongkhag	  = ua.billing_dzongkhag if ua.billing_dzongkhag else doc.dzongkhag
		doc.mobile_no	  = ua.mobile_no if ua.mobile_no else doc.mobile_no
		doc.customer_details = customer_address
		doc.save(ignore_permissions=True)
		self.customer	  = doc.name

	def validate_defaults(self):
		""" basic validations  """
		if get_datetime(self.construction_end_date) <= get_datetime(self.construction_start_date):
			frappe.throw(_("Construction End Date cannot be on or before Construction Start Date"))
		self.extension_till_date = self.construction_end_date if not self.extension_till_date else self.extension_till_date

	def validate_items(self):
		dup = {}
		for i in self.get("items"):
			if i.item_sub_group in dup:
				frappe.throw(_("Row#{0}: Duplication of material {1} not permitted").format(i.idx, i.item_sub_group))
			else:
				dup[i.item_sub_group] = 1

			if flt(i.expected_quantity) < 0:
				frappe.throw(_("Row#{0}: Expected Quantity cannot be a negative value").format(i.idx))
			i.overall_expected_quantity  = flt(i.expected_quantity) + flt(i.extended_quantity)
			i.balance_quantity  = flt(i.expected_quantity) + flt(i.extended_quantity) - flt(i.ordered_quantity)

@frappe.whitelist()
def site_active(site):
	return frappe.db.get_value("Site", site, "enabled")

@frappe.whitelist()
def has_pending_transactions(site):
	return frappe.db.sql("""select count(*) from `tabCustomer Order`
		where site = "{site}" and docstatus = 1 and ifnull(total_balance_amount,0) > 0
	""".format(site=site))[0][0]
