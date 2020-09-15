# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

'''
------------------------------------------------------------------------------------------------------------------------------------------
Version          Author         Ticket#           CreatedOn          ModifiedOn          Remarks
------------ --------------- --------------- ------------------ -------------------  -----------------------------------------------------
3.0               SHIV		                   28/01/2019                          Original Version
------------------------------------------------------------------------------------------------------------------------------------------                                                                          
'''

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.hr.doctype.approver_settings.approver_settings import get_final_approver
from erpnext.hr.hr_custom_functions import get_officiating_employee

def validate_workflow_states(doc):
	approver_field = {
			"Leave Encashment": ["approver", "approver_name"],
			"Salary Advance": ["advance_approver","advance_approver_name","advance_approver_designation"],
			"Leave Application": ["leave_approver","leave_approver_name"],
			"Travel Authorization": ["supervisor",""],
			"Travel Claim": ["supervisor",""],
			"Employee Benefits": ["benefit_approver","benefit_approver_name"],
                        "Request EL Allocation": ["approver", "approver_name"],
			"Overtime Authorization": ["approver", "approver_name"],
			"Overtime Claim": ["approver", "approver_name"],
	}
	
	if not approver_field.has_key(doc.doctype) or not frappe.db.exists("Workflow", {"document_type": doc.doctype, "is_active": 1}):
		return
	document_approver = approver_field[doc.doctype]
	employee          = frappe.db.get_value("Employee", doc.employee, ["user_id","employee_name","designation","name"])
	reports_to        = frappe.db.get_value("Employee", frappe.db.get_value("Employee", doc.employee, "reports_to"), ["user_id","employee_name","designation","name"])
	if not reports_to:
		frappe.throw("Set Up Reports to in Employee Master")

	final_approver    = frappe.db.get_value("Employee", {"user_id": get_final_approver(doc.branch)}, ["user_id","employee_name","designation","name"])
	workflow_state    = doc.get("workflow_state").lower()

	#Leave Encashment, Employee(Apply) ---> HR(Approves) ---> Accounts for Payment
	if doc.doctype == "Leave Encashment":
		hr_user = frappe.db.get_single_value("HR Settings", "hr_approver")
               	hr_approver = frappe.db.get_value("Employee", hr_user, ["user_id","employee_name","designation","name"])
		officiating = get_officiating_employee(hr_approver[3])
                if officiating:
                	officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])

		if workflow_state == "Draft".lower():
			vars(doc)[document_approver[0]] == ""
			vars(doc)[document_approver[1]] == ""

		elif workflow_state == "Waiting Approval".lower():
			vars(doc)[document_approver[0]] = officiating[0] if officiating else hr_approver[0]
                        vars(doc)[document_approver[1]] = officiating[1] if officiating else hr_approver[1]
			if doc.owner != frappe.session.user:
				frappe.throw(" Only <b> {0} </b> can apply this Leave Encashment".format(employee[1]))

        	elif workflow_state == "Approved".lower():
                        vars(doc)[document_approver[0]] = officiating[0] if officiating else hr_approver[0]
                        vars(doc)[document_approver[1]] = officiating[1] if officiating else hr_approver[1]
                  	if doc.workflow_state == "Approved" and doc.docstatus == 0:
				doc.workflow_state = "Waiting Approval"

			if doc.approver != frappe.session.user:
                                frappe.throw("Only <b> {0} </b> can approve this Leave Encashment".format(doc.approver_name))

		elif workflow_state == 'Rejected'.lower(): 
                        vars(doc)[document_approver[0]] = officiating[0] if officiating else hr_approver[0]
                        vars(doc)[document_approver[1]] = officiating[1] if officiating else hr_approver[1]
                        if doc.approver != frappe.session.user:
                                frappe.throw("Only <b> {0} </b> can Reject this Leave Encashment".format(doc.approver_name))
                        doc.workflow_state = "Rejected"

		elif workflow_state == 'Cancelled'.lower():
			vars(doc)[document_approver[0]] = officiating[0] if officiating else hr_approver[0]
                        vars(doc)[document_approver[1]] = officiating[1] if officiating else hr_approver[1]
                        if doc.approver != frappe.session.user:
                                frappe.throw("Only <b> {0} </b> can Cancel this Leave Encashment".format(doc.approver_name))
                        doc.workflow_state = "Cancelled"
	
		else:
			pass


	#Travel Authorization, Employee(Apply) ---> Supervisor(Approve) --- Accounts for Payment
	elif doc.doctype == "Travel Authorization":	
                officiating = get_officiating_employee(reports_to[0])
                if officiating:
                        officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])

		if workflow_state == "Draft".lower():
			vars(doc)[document_approver[0]] == ""
		
		elif workflow_state == "Waiting Approval".lower():
                        vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
                        if doc.owner != frappe.session.user:
                                frappe.throw(" Only <b> {0} </b> can apply this Document".format(employee[1]))

                elif workflow_state == "Approved".lower():
			vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
			if doc.supervisor != frappe.session.user:
                                frappe.throw("Only <b> {0} </b> can Approve this Document".format(doc.supervisor))
			doc.document_status = "Approved"
			if doc.workflow_state == "Approved" and doc.docstatus == 0:
				doc.workflow_state = "Waiting Approval"

                elif workflow_state == 'Rejected'.lower():
			vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
			if doc.supervisor != frappe.session.user:
				frappe.throw("Only <b> {0} </b> can Reject this Document".format(doc.supervisor))
			doc.document_status = "Rejected"

		elif workflow_state == "Cancelled".lower():
			vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
			if doc.supervisor != frappe.session.user:
				frappe.throw("Only <b> {0} </b> can Cancell this Document".format(doc.supervisor))
			
		else:
			pass

	#Travel Claim, Employee(Apply) ---> Supervisor(Approver) ---> Accounts for Payment
	elif doc.doctype == "Travel Claim":
		officiating = get_officiating_employee(reports_to[0])
                if officiating:
                        officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])

                elif workflow_state == "Draft".lower():
                        vars(doc)[document_approver[0]] = ""

		elif workflow_state == "Waiting Approval".lower():
                        vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
                        if doc.owner != frappe.session.user:
                                frappe.throw(" Only <b> {0} </b> can apply this Document".format(employee[1]))
		
                elif workflow_state == "Approved".lower():
			vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
                        if doc.supervisor != frappe.session.user:
                                frappe.throw("Only <b> {0} </b> can Approve this Document".format(doc.supervisor))

			if doc.workflow_state == "Approved" and doc.docstatus == 0:
                                doc.workflow_state = "Waiting Approval"

                elif workflow_state == 'Rejected'.lower():
                        vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
                        if doc.supervisor != frappe.session.user:
                                frappe.throw("Only <b> {0} </b> can Reject this Document".format(doc.supervisor))
                        doc.document_status = "Rejected"

                elif workflow_state == "Cancelled".lower():
                        vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
                        if doc.supervisor != frappe.session.user:
                                frappe.throw("Only <b> {0} </b> can Cancell this Document".format(doc.supervisor))

        	else:
                	pass


	#Leaves Application, leaves like Maternity, Paternity and Bereavement leave not captured in the system.
	#It will be maintained in their BCSR system for record purpose.
	#Employee(Apply) ---> Supervisor(Approves) 
	elif doc.doctype == "Leave Application":
		officiating = get_officiating_employee(reports_to[3])
		frappe.msgprint("off {0}".format(reports_to[3]))
                if officiating:
                	officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
	
		if workflow_state == "Draft".lower():
			vars(doc)[document_approver[0]] = ""
			vars(doc)[document_approver[1]] = ""

                elif workflow_state == "Waiting Approval".lower():
			vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
                        vars(doc)[document_approver[1]] = officiating[1] if officiating else reports_to[1]
			
                elif workflow_state == "Approved".lower():
			#vars(doc)[document_approver[0]] = reports_to[0]
			#vars(doc)[document_approver[1]] = reports_to[1]
			#officiating = get_officiating_employee(reports_to[3])
                        #if officiating:
                        #        officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
                        vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
			vars(doc)[document_approver[1]] = officiating[1] if officiating else reports_to[1]
                        if doc.docstatus == 0 and doc.workflow_state == "Approved":
                                doc.workflow_state = "Waiting Supervisor Approval"
                        if  doc.leave_approver != frappe.session.user:
                                frappe.throw("Only <b> {0} </b> can Approve the leave application".format(doc.leave_approver_name))

                        #Change employment status in  Employee Master -- Author: Thukten Dendup<thukten.dendup@bt.bt>
                        doc.status= "Approved"
                        emp_status = frappe.db.get_value("Leave Type", doc.leave_type, ["check_employment_status","employment_status"])
                        if emp_status[0] and emp_status[1]:
                                emp = frappe.get_doc("Employee", doc.employee)
                                emp.employment_status = emp_status[1]
                                emp.save()	

                elif workflow_state == "Rejected".lower():
			if doc.description == "":
				doc.workflow_state = "Waiting Supervisor Approval"

			if frappe.session.user != doc.leave_approver:
                                frappe.throw("Only  <b>{0}</b>  can Reject this document.".format(doc.leave_approver_name), title="Operation not permitted")

                	doc.status = "Rejected"

                elif workflow_state == "Cancelled".lower():
                        if frappe.session.user not in (doc.leave_approver,"Administrator"):
                                frappe.throw(_("Only leave approver <b>{0}</b> ( {1} ) can cancel this document.").format(doc.leave_approver_name, doc.leave_approver), title="Operation not permitted")
		
		else:
			pass



	###
        if doc.doctype == "Salary Advance":
                #CEO is set as the approver for Salary Advance.
                advance_doc  = frappe.get_doc("Employee", {"designation": 'Chief Executive Officer', "status": 'Active'})
                vars(doc)[document_approver[0]] = advance_doc.user_id
                vars(doc)[document_approver[1]] = advance_doc.employee_name
                vars(doc)[document_approver[2]] = advance_doc.designation
                officiating = get_officiating_employee(advance_doc.name)
		
                if officiating:
                        officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
                        vars(doc)[document_approver[0]] = officiating[0] if officiating else document_approver[0]
                        vars(doc)[document_approver[1]] = officiating[1] if officiating else document_approver[1]
                        vars(doc)[document_approver[2]] = officiating[2] if officiating else document_approver[2]
                if workflow_state == "Approved".lower():
                        if doc.get(document_approver[0]) != frappe.session.user:
                                frappe.throw(_("Only <b>{0}, {1}</b> can approve this application").format(doc.get(document_approver[1]),doc.get(document_approver[1])), title="Invalid Operation")
                elif workflow_state == "Rejected".lower():
                        if doc.get(document_approver[0]) and doc.get(document_approver[0]) != frappe.session.user:
                                if workflow_state != doc.get_db_value("workflow_state"):
                                        frappe.throw(_("Only <b>{0}, {1}</b> can reject this application").format(doc.get(document_approver[1]),doc.get(document_approver[1])), title="Invalid Operation")
                else:
                        pass

	elif doc.doctype == "Request EL Allocation":
		hr_user = frappe.db.get_single_value("HR Settings", "hr_approver")
		hr_approver = frappe.db.get_value("Employee", hr_user, ["user_id","employee_name","designation","name"])
		if workflow_state == "Draft".lower():
			vars(doc)[document_approver[0]] = employee[0]
			vars(doc)[document_approver[1]] = employee[1]
		elif workflow_state == "Waiting Approval".lower():
			if doc.get(document_approver[0]) != frappe.session.user:
				frappe.throw("Only {0} is allowed to process this application ".format(doc.get(document_approver[0])))
			officiating = get_officiating_employee(hr_approver[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
			vars(doc)[document_approver[0]] = officiating[0] if officiating else hr_approver[0]
			vars(doc)[document_approver[1]] = officiating[1] if officiating else hr_approver[1]
		elif workflow_state == "Waiting Supervisor Approval".lower():
			if employee[0] == final_approver[0]:
				officiating = get_officiating_employee(hr_approver[3])
				if officiating:
					officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
				vars(doc)[document_approver[0]] = officiating[0] if officiating else hr_approver[0]
				vars(doc)[document_approver[1]] = officiating[1] if officiating else hr_approver[1]

			else:
				officiating = get_officiating_employee(final_approver[3])
				if officiating:
					officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
				vars(doc)[document_approver[0]] = officiating[0] if officiating else final_approver[0]
				vars(doc)[document_approver[1]] = officiating[1] if officiating else final_approver[1]

		elif workflow_state == "Approved".lower():
			if doc.get(document_approver[0]) != frappe.session.user:
				frappe.throw(_("Only <b>{0}, {1}</b> can approve this application").format(doc.get(document_approver[1]),doc.get(document_approver[1])), title="Invalid Operation")
		elif workflow_state == "Rejected".lower():
			if doc.get(document_approver[0]) and doc.get(document_approver[0]) != frappe.session.user:
				if workflow_state != doc.get_db_value("workflow_state"):
					frappe.throw(_("Only <b>{0}, {1}</b> can reject this application").format(doc.get(document_approver[1]),doc.get(document_approver[1])), title="Invalid Operation")
		else:
			pass	

	elif doc.doctype in ["Overtime Claim","Overtime Authorization"]:
		hr_user = frappe.db.get_single_value("HR Settings", "hr_approver")
		hr_approver = frappe.db.get_value("Employee", hr_user, ["user_id","employee_name","designation","name"])
		
		if workflow_state == "Draft".lower():
			vars(doc)[document_approver[0]] = employee[0]
			vars(doc)[document_approver[1]] = employee[1]

		elif workflow_state == "Approved".lower():
			if  doc.approver != frappe.session.user:
				frappe.throw("Only {0} can only approve Overtime Application".format(doc.approver))
			if final_approver[0] != doc.approver and employee[0] != final_approver[0]:
				frappe.throw("Only {0} can approve your Overtime Application".format(frappe.bold(final_approver[0])))
			#doc.status= "Approved"
			if doc.doctype == "Overtime Claim":
				officiating = get_officiating_employee(hr_approver[3])
				if officiating:
					officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
				vars(doc)[document_approver[0]] = officiating[0] if officiating else hr_approver[0]
				vars(doc)[document_approver[1]] = officiating[1] if officiating else hr_approver[1]
				

		elif workflow_state == "Claimed".lower():
			if  hr_approver[0] != frappe.session.user:
				frappe.throw("Only {0} can verify payment for  Overtime Application".format(hr_approver[0]))

		if workflow_state == "Waiting Supervisor Approval".lower():
			officiating = get_officiating_employee(reports_to[3])
			if officiating:
				officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
			vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
			vars(doc)[document_approver[1]] = officiating[1] if officiating else reports_to[1]

			if doc.approver == employee[0]:
				frappe.throw("Overtime Application submitter {0} cannot be the supervisor ".format(doc.approver))
		elif workflow_state == "Verified By Supervisor".lower():
			if  doc.approver != frappe.session.user:
				frappe.throw("Only {0} can submit the leave application".format(doc.approver))
			if final_approver[0] != employee[0]:
				officiating = get_officiating_employee(final_approver[3])
				if officiating:
					officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
				vars(doc)[document_approver[0]] = officiating[0] if officiating else final_approver[0]
				vars(doc)[document_approver[1]] = officiating[1] if officiating else final_approver[1]
		elif workflow_state == "Rejected".lower():
			if doc.approver != frappe.session.user:
				frappe.throw("Only {0} can Reject this application".format(doc.approver), title="Operation not permitted")
			else:
				if workflow_state == "Rejected".lower():
					doc.status = "Rejected"
				vars(doc)[document_approver[0]] = reports_to[0]
				vars(doc)[document_approver[1]] = reports_to[1]

		elif workflow_state == "Cancelled".lower():
			if frappe.session.user not in (doc.approver,"Administrator"):
				frappe.throw(_("Only Overtime approver <b>{0}</b> ( {1} ) can cancel this document.").format(doc.approver_name, doc.approver), title="Operation not permitted")		

	elif doc.doctype == "Employee Benefits":
		hr_user = frappe.db.get_single_value("HR Settings", "hr_approver")
		hr_approver = frappe.db.get_value("Employee", hr_user, ["user_id","employee_name","designation","name"])

		if workflow_state == "Draft".lower():
			if doc.purpose == "Separation" and hr_approver[0] != frappe.session.user:
				frappe.throw("Only HR user {0}, {1} is allowed to create the application with Purpose Separation.".format(hr_approver[1], hr_approver[0]))
			vars(doc)[document_approver[0]] = frappe.session.user
			login_user        = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["user_id","employee_name","designation","name"])
		  	vars(doc)[document_approver[1]] = login_user[1]
		elif workflow_state == "Waiting Approval".lower():
			if doc.purpose == "Separation" and hr_approver[0] != frappe.session.user:
				frappe.throw("Only HR user {0}, {1} is allowed to create the application with Purpose Separation.".format(hr_approver[1], hr_approver[0]))
			# If employee is RM|HR Manager, it will look for Officiating, else it will go their Supervisor
			if employee[0] == final_approver[0]:
				officiating = get_officiating_employee(reports_to[3])
				if officiating:
					officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
				vars(doc)[document_approver[0]] = officiating[0] if officiating else reports_to[0]
				vars(doc)[document_approver[1]] = officiating[1] if officiating else reports_to[1]
			else:
				officiating = get_officiating_employee(final_approver[3])
				if officiating:
					officiating = frappe.db.get_value("Employee", officiating[0].officiate, ["user_id","employee_name","designation","name"])
				vars(doc)[document_approver[0]] = officiating[0] if officiating else final_approver[0]
				vars(doc)[document_approver[1]] = officiating[1] if officiating else final_approver[1]
		elif workflow_state == "Approved".lower():
			if doc.docstatus == 0 and doc.workflow_state == "Approved":
				doc.workflow_state = "Waiting Approval"
			if doc.get(document_approver[0]) != frappe.session.user:
				frappe.throw(_("Only <b>{0}, {1}</b> can approve this application").format(doc.get(document_approver[0]),doc.get(document_approver[1])), title="Invalid Operation")
		elif workflow_state == "Rejected".lower():
			if doc.get(document_approver[0]) and doc.get(document_approver[0]) != frappe.session.user:
				if workflow_state != doc.get_db_value("workflow_state"):
					frappe.throw(_("Only <b>{0}, {1}</b> can reject this application").format(doc.get(document_approver[0]),doc.get(document_approver[1])), title="Invalid Operation")
		else:
			pass


