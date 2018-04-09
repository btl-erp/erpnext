'''
--------------------------------------------------------------------------------------------------------------------------
Version          Author          CreatedOn          ModifiedOn          Remarks
------------ --------------- ------------------ -------------------  -----------------------------------------------------
2.0		  SHIV		                   28/11/2017         get_user_info method included.
2.0               SHIV                             02/02/2018         added function nvl()
                                                                        * This function return if the arg1 is not null,
                                                                        else return arg2.
2.0               SHIV                             03/22/2018         added functon get_prev_doc()
                                                                        * This function can be used globally to fetch
                                                                        previous database record by passing arguments
                                                                        like DocType, DocName, ListOf Columns to be fetched.
--------------------------------------------------------------------------------------------------------------------------                                                                          
'''

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import msgprint
from frappe.utils import flt, cint, nowdate, getdate
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils.data import get_first_day, get_last_day, add_years
from frappe.desk.form.linked_with import get_linked_doctypes, get_linked_docs
from frappe.model.naming import getseries


##
# Check for future dates in transactions
##
def check_future_date(date):
	if not date:
		frappe.throw("Date Argument Missing")
	if getdate(date) > getdate(nowdate()):
		frappe.throw("Posting for Future Date is not Permitted")

##
# Get cost center from branch
##
def get_branch_cc(branch):
        if not branch:
                frappe.throw("No Branch Argument Found")
        cc = frappe.db.get_value("Cost Center", {"branch": branch, "is_disabled": 0, "is_group": 0}, "name")
        if not cc:
                frappe.throw(str(branch) + " is not linked to any cost center")
        return cc

##
# Rounds to the nearest 5 with precision of 1 by default
##
def round5(x, prec=1, base=0.5):
        return round(base * round(flt(x)/base), prec)

##
# If the document is linked and the linked docstatus is 0 and 1, return the first linked document
##
def check_uncancelled_linked_doc(doctype, docname):
        linked_doctypes = get_linked_doctypes(doctype)
        linked_docs = get_linked_docs(doctype, docname, linked_doctypes)
        for docs in linked_docs:
                for doc in linked_docs[docs]:
                        if doc['docstatus'] < 2:
                                return [docs, doc['name']]
        return 1

def get_year_start_date(date):
	return str(date)[0:4] + "-01-01"

def get_year_end_date(date):
	return str(date)[0:4] + "-12-31"

# Ver 2.0 Begins, following method added by SHIV on 28/11/2017
@frappe.whitelist()
def get_user_info(user=None, employee=None, cost_center=None):
        info = {}
        
	#cost_center,branch = frappe.db.get_value("Employee", {"user_id": user}, ["cost_center", "branch"])

        if employee:
                # Nornal Employee
                cost_center = frappe.db.get_value("Employee", {"name": employee}, "cost_center")
                branch      = frappe.db.get_value("Employee", {"name": employee}, "branch")

                # GEP Employee
                if not cost_center:
                        cost_center = frappe.db.get_value("GEP Employee", {"name": employee}, "cost_center")
                        branch      = frappe.db.get_value("GEP Employee", {"name": employee}, "branch")

                # MR Employee
                if not cost_center:
                        cost_center = frappe.db.get_value("Muster Roll Employee", {"name": employee}, "cost_center")
                        branch      = frappe.db.get_value("Muster Roll Employee", {"name": employee}, "branch")
		
        elif user:
                # Normal Employee
                cost_center = frappe.db.get_value("Employee", {"user_id": user}, "cost_center")
                branch      = frappe.db.get_value("Employee", {"user_id": user}, "branch")

                # GEP Employee
                if not cost_center:
                        cost_center = frappe.db.get_value("GEP Employee", {"user_id": user}, "cost_center")
                        branch      = frappe.db.get_value("GEP Employee", {"user_id": user}, "branch")

                # MR Employee
                if not cost_center:
                        cost_center = frappe.db.get_value("Muster Roll Employee", {"user_id": user}, "cost_center")
                        branch      = frappe.db.get_value("Muster Roll Employee", {"user_id": user}, "branch")
		
	warehouse   = frappe.db.get_value("Cost Center", cost_center, "warehouse")
	approver    = frappe.db.get_value("Approver Item", {"cost_center": cost_center}, "approver")
        customer    = frappe.db.get_value("Customer", {"cost_center": cost_center}, "name")

        info.setdefault('cost_center', cost_center)
        info.setdefault('branch', branch)
        info.setdefault('warehouse', warehouse)
        info.setdefault('approver',approver)
        info.setdefault('customer', customer)
	
	#return [cc, wh, app, cust]
        return info
# Ver 2.0 Ends

##
# Cancelling draft documents
##
@frappe.whitelist()
def cancel_draft_doc(doctype, docname):
        doc = frappe.get_doc(doctype, docname)
        doc.db_set("docstatus", 2)
	if doctype == "Material Request":
		doc.db_set("status", "Cancelled")
		doc.db_set("workflow_state", "Cancelled")
	if doctype == "Travel Claim":
		if doc.ta:
			ta = frappe.get_doc("Travel Authorization", doc.ta)
			ta.db_set("travel_claim", "")

##
#  nvl() function added by SHIV on 02/02/2018
##
def nvl(val1, val2):
        return val1 if val1 else val2

##
# generate and get the receipt number
##
def generate_receipt_no(doctype, docname, branch, fiscal_year):
	if doctype and docname:
		abbr = frappe.db.get_value("Branch", branch, "abbr")
		if not abbr:
			frappe.throw("Set Branch Abbreviation in Branch Master Record")
		name = str("CDCL/" + str(abbr) + "/" + str(fiscal_year) + "/")
		current = getseries(name, 4)
		doc = frappe.get_doc(doctype, docname)
		doc.db_set("money_receipt_no", current)
		doc.db_set("money_receipt_prefix", name)

##
#  get_prev_doc() function added by SHIV on 03/22/2018
##
@frappe.whitelist()
def get_prev_doc(doctype,docname,col_list=""):
        if col_list:
                return frappe.db.get_value(doctype,docname,col_list.split(","),as_dict=1)
        else:
                return frappe.get_doc(doctype,docname)

##
# Prepre the basic stock ledger 
##
def prepare_sl(d, args):
        sl_dict = frappe._dict({
                "item_code": d.pol_type,
                "warehouse": d.warehouse,
                "posting_date": d.posting_date,
                "posting_time": d.posting_time,
                'fiscal_year': get_fiscal_year(d.posting_date, company=d.company)[0],
                "voucher_type": d.doctype,
                "voucher_no": d.name,
                "voucher_detail_no": d.name,
                "actual_qty": 0,
                "stock_uom": d.stock_uom,
                "incoming_rate": 0,
                "company": d.company,
                "batch_no": "",
                "serial_no": "",
                "project": "",
                "is_cancelled": d.docstatus==2 and "Yes" or "No"
        })

        sl_dict.update(args)
        return sl_dict

##
# Prepre the basic accounting ledger 
##
def prepare_gl(d, args):
        """this method populates the common properties of a gl entry record"""
        gl_dict = frappe._dict({
                'company': d.company,
                'posting_date': d.posting_date,
                'fiscal_year': get_fiscal_year(d.posting_date, company=d.company)[0],
                'voucher_type': d.doctype,
                'voucher_no': d.name,
                'remarks': d.remarks,
                'debit': 0,
                'credit': 0,
                'debit_in_account_currency': 0,
                'credit_in_account_currency': 0,
                'is_opening': "No",
                'party_type': None,
                'party': None,
                'project': ""
        })
        gl_dict.update(args)

        return gl_dict

##
# Check budget availability in the budget head
##
def check_budget_available(cost_center, budget_account, transaction_date, amount):
        action = frappe.db.sql("select action_if_annual_budget_exceeded as action from tabBudget where docstatus = 1 and cost_center = \'" + str(cost_center) + "\' and fiscal_year = " + str(transaction_date)[0:4] + " ", as_dict=True)
        if action and action[0].action == "Ignore":
                pass
        else:
                budget_amount = frappe.db.sql("select ba.budget_amount from `tabBudget` b, `tabBudget Account` ba where b.docstatus = 1 and ba.parent = b.name and ba.account=%s and b.cost_center=%s and b.fiscal_year = %s", (budget_account, cost_center, str(transaction_date)[0:4]), as_dict=True)
                if budget_amount:
                        consumed = frappe.db.sql("select SUM(cb.amount) as total from `tabCommitted Budget` cb where cb.cost_center=%s and cb.account=%s and cb.po_date between %s and %s", (cost_center, budget_account, str(transaction_date)[0:4] + "-01-01", str(transaction_date)[0:4] + "-12-31"), as_dict=True)
                        if consumed:
                                total_consumed_amount = flt(consumed[0].total) + flt(amount)
                                if flt(budget_amount[0].budget_amount) < flt(total_consumed_amount):
                                        frappe.throw("Not enough budget in <b>" + str(budget_account) + "</b> under <b>" + str(cost_center) + "</b>. Budget exceeded by <b>" + str(flt(total_consumed_amount) - flt(budget_amount[0].budget_amount)) + "</b>")
                else:
                        frappe.throw("There is no budget in <b>" + str(budget_account) + "</b> under <b>" + str(cost_center) + "</b>")


@frappe.whitelist()
def get_cc_warehouse(branch):
        cc = get_branch_cc(branch)
        wh = frappe.db.get_value("Cost Center", cc, "warehouse")
        return {"cc": cc, "wh": wh}	

@frappe.whitelist()
def get_branch_warehouse(branch):
        cc = get_branch_cc(branch)
        wh = frappe.db.get_value("Cost Center", cc, "warehouse")
        return wh
