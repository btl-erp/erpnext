# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from erpnext.hr.doctype.leave_application.leave_application \
        import get_leave_allocation_records, get_leave_balance_on, get_approved_leaves_for_period

from frappe.utils import getdate, get_first_day, get_last_day, flt

class CarryForwardEntry(Document):
	def validate(self):
		self.validate_carry_forward()
		self.validate_duplicate()
		self.get_data()


	def validate_carry_forward(self):
		is_carry_forward = frappe.get_doc("Leave Type", self.leave_type).is_carry_forward
		if not is_carry_forward:
			frappe.throw(" <b> {0} </b> cannot be carry forwarded ".format(self.leave_type))
		

	def validate_duplicate(self):
		query = """select name from `tabCarry Forward Entry` where docstatus != 2 and fiscal_year = '{0}' and name != '{1}'
			""".format(self.fiscal_year, self.name)
		if self.branch:
			query += " and branch = '{0}'".format(self.branch)
		doc = frappe.db.sql(query)

                '''doc = frappe.db.sql("select name from `tabCarry Forward Entry` where docstatus != 2 and fiscal_year = \'"+str(self.fiscal_year)+"\' and name != \'"+str(self.name)+"\'")
                '''
		if doc:
                        frappe.throw("Can not create multiple Entries for the same year")


	def get_data(self):
		fy_start_end_date = frappe.db.get_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"])
		if not fy_start_end_date:
			frappe.throw(_("Fiscal Year {0} not found.").format(self.fiscal_year))

		frappe.msgprint('y_start {0}, y_end {1}'.format(fy_start_end_date[0], fy_start_end_date[1]))	
		from_date = get_first_day(getdate(fy_start_end_date[0]))
		to_date = get_last_day(getdate(fy_start_end_date[1]))
		employee = ''
		allocation_records_based_on_to_date = get_leave_allocation_records(to_date)
		filters_dict = { "status": "Active", "company": self.company}
		if self.branch:
			filters_dict['branch'] = self.branch

		active_employees = frappe.get_all("Employee",
			filters = filters_dict,
			fields = ["name", "employee_name", "department", "branch", "date_of_joining"])

		self.set('items', [])
		for employee in active_employees:
			#leaves allocated
			leaves_allocated = 0.0
			allocation   = get_leave_allocation_records(to_date, employee.name).get(employee.name, frappe._dict()).get(self.leave_type, frappe._dict())
			
			if allocation:
				leaves_allocated = allocation['total_leaves_allocated']
			
			# leaves taken
			leaves_taken = get_approved_leaves_for_period(employee.name, self.leave_type,
				from_date, to_date)

			# closing balance
			'''leave_balance = get_leave_balance_on(employee.name, self.leave_type, to_date,
				allocation_records_based_on_to_date.get(employee.name, frappe._dict()))'''
			employee_no = employee.name
			employee_name = employee.employee_name
			leave_balance = flt(leaves_allocated) - flt(leaves_taken)
			
			row = self.append('items', {})
			d = {'employee': employee_no, 'employee_name': employee_name, \
				'leaves_allocated': leaves_allocated, 'leaves_taken': leaves_taken, 'leave_balance': leave_balance}
			row.update(d)

