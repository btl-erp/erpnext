# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe.model.document import Document
from erpnext.hr.doctype.leave_application.leave_application import get_leave_balance_on
#from erpnext.hr.doctype.leave_encashment.leave_encashment import get_le_settings

class LeaveAdjustment(Document):
	def validate(self):
		self.validate_leave_balance()

	def check_mandatory(self):
		if not self.adjustment_date:
			frappe.throw("Adjustment Date is Mandatory")
		if not self.leave_type:
			frappe.throw("Leave Type is Mandatory")

	def validate_leave_balance(self):
		self.check_mandatory()
		for a in self.items:
			a.leave_balance = get_leave_balance_on(a.employee, self.leave_type, self.adjustment_date)
			a.difference = flt(a.leave_balance) - flt(a.actual_balance)

	def on_submit(self):
		self.validate_leave_balance()
		self.adjust_leave()

	def on_cancel(self):
		self.adjust_leave(1)

	def adjust_leave(self, cancel=0):
		#le = get_le_settings()                         #Commented by SHIV on 2018/10/16
		for a in self.items:
			if flt(a.difference) == 0:
				pass
			else:
                                le = frappe.get_doc("Employee Group",frappe.db.get_value("Employee",a.employee,"employee_group")) # Line added by SHIV on 2018/10/16
				las = frappe.db.sql("select name from `tabLeave Allocation` where employee = %s and leave_type = %s and to_date >= %s", (a.employee, self.leave_type, self.adjustment_date), as_dict=True)
				for l in las:
					doc = frappe.get_doc("Leave Allocation", l.name)
					carry_forwarded = flt(doc.carry_forwarded_leaves) - flt(a.difference)
					balance = flt(doc.total_leaves_allocated) - flt(a.difference)
					if cancel:
						carry_forwarded = flt(doc.carry_forwarded_leaves) + flt(a.difference)
						balance = flt(doc.total_leaves_allocated) + flt(a.difference)
					
					if flt(carry_forwarded) > flt(le.encashment_lapse):
						carry_forwarded = le.encashment_lapse
					if flt(balance) > flt(le.encashment_lapse):
						balance = le.encashment_lapse
					doc.db_set("carry_forwarded_leaves", carry_forwarded)
					doc.db_set("total_leaves_allocated", balance)

	def get_employees(self):
		self.check_mandatory()
		query = "select name as employee, employee_name from tabEmployee where status = 'Active' and date_of_joining <= %s"
		if self.branch:
			query += " and branch = \'"+str(self.branch)+"\'"

		entries = frappe.db.sql(query, self.adjustment_date, as_dict=True)
		self.set('items', [])

		for d in entries:
			balance = get_leave_balance_on(d.employee, self.leave_type, self.adjustment_date)
			d.leave_balance = balance
			d.actual_balance = balance
			d.difference = 0
			row = self.append('items', {})
			row.update(d)
