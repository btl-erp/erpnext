from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe import msgprint
from frappe.utils import rounded, flt, cint, now, nowdate, getdate, get_datetime,now_datetime
from frappe.utils.data import date_diff, add_days, get_first_day, get_last_day, add_years
#from erpnext.hr.hr_custom_functions import get_month_details, get_company_pf, get_employee_gis, get_salary_tax, update_salary_structure
from erpnext.hr.hr_custom_functions import get_month_details, get_salary_tax
from datetime import timedelta, date
from erpnext.custom_utils import get_branch_cc, get_branch_warehouse, prepare_gl
from erpnext.accounts.utils import make_asset_transfer_gl
from datetime import datetime
import os
import subprocess

def update_mr():
	doc = frappe.get_doc("Process MR Payment", 'MRP200200016')
	print doc.name
	doc.save(ignore_permissions = True)



def check_stock_gl():
	for a in frappe.db.sql("select name, branch from `tabStock Entry` where docstatus = 1 and name = 'SEMI19030600'", as_dict=1):
		try:
			cc = get_branch_cc(a.branch)
			sed = frappe.db.sql("select name from `tabStock Entry Detail` where parent = %s and cost_center != %s", (a.name, cc))
			if sed:
				print(a.name)
				frappe.db.sql("update `tabStock Entry Detail` set cost_center = %s where parent = %s", (cc, a.name))
				frappe.db.sql("delete from `tabGL Entry` where voucher_no = %s", a.name)
				doc = frappe.get_doc("Stock Entry", a.name)
				doc.make_gl_entries()
		except:
			cc = "Dummy"

def update_gl_stock_2019():
	for a in frappe.db.sql("select name from `tabStock Entry` where name = 'SEMT18070012'", as_dict=1):
		print(str(a.name))
		self = frappe.get_doc("Stock Entry", a.name)
		self.make_gl_entries()

def test_get_branch():
	for a in frappe.db.sql("select name from `tabStock Entry` where docstatus = 1 and purpose = 'Material Transfer' and posting_date between '2019-01-01' and '2019-12-31' and name = 'SEMT19010037'", as_dict=1):
		print(a.name)
		frappe.db.sql("delete from `tabGL Entry` where voucher_no = %s", a.name)
		doc = frappe.get_doc("Stock Entry", a.name)
		doc.make_gl_entries()

def update_wh_branch():
        counter =0
        for t in frappe.get_all("Warehouse", ["name", "branch"]):
                if not frappe.db.exists("Warehouse Branch", {"parent" :t.name }):
                        counter +=1
                        print counter, t.name
                        doc = frappe.get_doc("Warehouse", t.name)
                        row = doc.append ("items",{})
                        row.branch  = t.branch
                        row.save()
                        print t
        print 'dona saving .........'


def asset_test():
	for a in frappe.db.sql("select name, asset_category, opening_accumulated_depreciation as oad from tabAsset where asset_category = 'Machinery & Equipment(10 Years)' and docstatus = 1 and status not in ('Scrapped', 'Sold')", as_dict=1):
		accu_ar = frappe.db.sql("""select
                	gl.accumulated_depreciation_amount as ac
                        from `tabDepreciation Schedule` gl, tabAsset ass
                        where gl.parent = ass.name
                        and gl.schedule_date <= '2018-12-31'
                        and gl.docstatus = 1
			and ass.name = '{0}'
                        and gl.journal_entry is not null 
			order by gl.schedule_date desc limit 1""".format(a.name), as_dict=1)
		opening = a.oad
		if accu_ar:
			opening = accu_ar[0].ac
		
		gl_acc = frappe.db.sql("select name, sum(credit) as cr, sum(debit) as dr from `tabGL Entry` where account like '%Depreciation -Machinery & Equipment(10 Years) - CDCL' and voucher_type not in ('Asset Movement', 'Bulk Asset Transfer') and posting_date < '2019-01-01' and against_voucher = '{0}'".format(a.name), as_dict=1)
		gl_open = 1 
		if gl_acc:
			gl_open = gl_acc[0].cr
	
		if not gl_open:	
			gl_open = 1
		if flt(opening) - flt(gl_open) > 1 or flt(opening) - flt(gl_open) < -1:
			print str(a.name) + " ==> " + str(opening) + " : " + str(gl_open)

def change_pol_cc():
	for a in frappe.db.sql("select distinct  voucher_no from `tabGL Entry` where account = 'Clearing Account - CDCL' and posting_date > '2018-12-31';", as_dict=1):
		pol = frappe.get_doc("POL", a.voucher_no)
		print(pol.equipment_warehouse)
		frappe.db.sql("update `tabGL Entry` set account = %s where voucher_no = %s", (pol.equipment_warehouse, a.voucher_no))

def update_musterroll():
	MR = frappe.db.sql("select rate_per_day, rate_per_hour, joining_date, name from `tabMuster Roll Employee`;", as_dict=1)
	counter = 0
        for i in MR:
                counter += 1
                
                doc = frappe.get_doc("Muster Roll Employee", i.name)
                row = doc.append("musterroll", {})
                row.rate_per_day    = i.rate_per_day
                row.rate_per_hour           = i.rate_per_hour
                row.from_date             = i.joining_date
                row.save()
def change_dn():
	for a in frappe.db.sql("select name, branch from `tabDelivery Note` where docstatus = 1 and posting_date > '2018-12-31'", as_dict=1):
		cc = get_branch_cc(a.branch)
		print(cc)
		frappe.db.sql("update `tabDelivery Note Item` set cost_center = %s where parent = %s", (cc, a.name))
		frappe.db.sql("update `tabGL Entry` set cost_center = %s where voucher_no = %s", (cc, a.name))

def change_si():
	for a in frappe.db.sql("select name, branch from `tabSales Invoice` where docstatus = 0 and posting_date > '2018-12-31'", as_dict=1):
		cc = get_branch_cc(a.branch)
		print(cc)
		frappe.db.sql("update `tabSales Invoice Item` set cost_center = %s where parent = %s", (cc, a.name))
		frappe.db.sql("update `tabGL Entry` set cost_center = %s where voucher_no = %s", (cc, a.name))

def change_cc():
	for a in frappe.db.sql("select name, branch from `tabStock Entry` where docstatus = 0 and posting_date > '2018-12-31'", as_dict=1):
		cc = get_branch_cc(a.branch)
		print(cc)
		frappe.db.sql("update `tabStock Entry Detail` set cost_center = %s where parent = %s", (cc, a.name))
		frappe.db.sql("update `tabGL Entry` set cost_center = %s where voucher_no = %s", (cc, a.name))
		"""for b in frappe.db.sql("select cost_center from `tabGL Entry` where voucher_no = %s and cost_center != %s", (a.name, cc), as_dict=1)
			print()
		"""
def update_bank():
	for a in frappe.db.sql("select id_card, bank, account_no, designation from `tabMuster Roll Employee", as_dict=1):
		bank1 =a.bank
		account = a.account_no
		designation1= a.designation
		frappe.db.sql("update `tabMR Payment Item` set bank = %s, account_no = %s, designation = %s where id_card = %s", (bank1, account, designation1, a.id_card))

def get_cc():
	print(frappe.defaults.get_defaults().cost_center)

def get_diff_asset():
        for a in frappe.db.sql("select name, asset_category, asset_account from tabAsset where docstatus = 1", as_dict=1):
                as_acc = frappe.db.get_value("Asset Category Account", {"parent": a.asset_category}, "fixed_asset_account")
                if as_acc != a.asset_account:
                        print(str(a.name) + "   :  " + str(as_acc) + "  ==> " + str(a.asset_account))


def update_equipment():
        els = frappe.db.sql("select name from tabEquipment", as_dict=1)
        for a in els:
                print a.name
                doc = frappe.get_doc("Equipment", a.name)
                doc.save()
                frappe.db.commit()

def check_ds():
	#for a in frappe.db.sql("select b.name as ass_name, a.schedule_date as dep_date, a.name, b.residual_value, b.expected_value_after_useful_life as ev, b.gross_purchase_amount as gross, b.value_after_depreciation as vad, a.accumulated_depreciation_amount as ada, a.depreciation_amount as da from `tabDepreciation Schedule` a, tabAsset b where a.parent = b.name and b.docstatus = 1 and a.journal_entry is null and b.status in ('Partially Depreciated', 'Submitted') and residual_value > 0 order by b.name, a.schedule_date", as_dict=1):
	for a in frappe.db.sql("select b.name as ass_name, a.schedule_date as dep_date, a.name, b.residual_value, b.expected_value_after_useful_life as ev, b.gross_purchase_amount as gross, b.value_after_depreciation as vad, a.accumulated_depreciation_amount as ada, a.depreciation_amount as da from `tabDepreciation Schedule` a, tabAsset b where a.parent = b.name and b.docstatus = 1 and a.journal_entry is null and b.status in ('Partially Depreciated', 'Submitted') and residual_value > 0 and a.accumulated_depreciation_amount > (b.gross_purchase_amount - b.residual_value - b.expected_value_after_useful_life) order by b.name, a.schedule_date", as_dict=1):
		new_accu = rounded(flt(a.gross) - flt(a.residual_value) - flt(a.ev), 2)
		new_dep = rounded(flt(a.ada) - new_accu, 2)
		print(str(a.ass_name) + " ==> " + str(a.dep_date) + " : " + str(new_dep))
		frappe.db.sql("update `tabDepreciation Schedule` set depreciation_amount = %s, accumulated_depreciation_amount = %s where name = %s", (new_dep, new_accu, a.name))

def delete_ds():
	for a in frappe.db.sql("select a.name as dname from `tabDepreciation Schedule` a, tabAsset b where a.parent = b.name and b.docstatus = 1 and a.journal_entry is null and b.value_after_depreciation = b.expected_value_after_useful_life;", as_dict=1):
		frappe.db.sql("delete from `tabDepreciation Schedule` where name = %s", a.dname)

def import_asset():
	lines = [line.rstrip('\n') for line in open('/home/kinley/erp/asset_file.csv')]
	for line in lines:
		a = line.split(",")
		print(a[0])
		frappe.db.sql("update tabAsset set residual_value = %s, value_after_depreciation = %s where name = %s", (a[1], 1, a[0]))

def adjust_residual():
	for a in frappe.db.sql("select name, value_after_depreciation as vad, residual_value as rv, expected_value_after_useful_life as ev from tabAsset where value_after_depreciation < 0 and docstatus = 1", as_dict=1):
		val = str(rounded(flt(a.rv) + flt(a.vad) - flt(a.ev), 2))
		frappe.db.sql("update tabAsset set residual_value = %s and value_after_depreciation = %s where name = %s", (val, a.ev, a.name))
		print(str(a.name) + "  :  " + str(rounded(flt(a.rv) + flt(a.vad) - flt(a.ev), 2)))

def pass_open_accu():
	for a in frappe.db.sql("select name, creation from tabAsset where opening_accumulated_depreciation > 0 and purchase_date >= '2018-01-01' and docstatus = 1 order by creation", as_dict=1):
		print(a.name)
		doc = frappe.get_doc("Asset", a.name)
		doc.make_opening_accumulated_gl_entry()

def adjust_direct_con():
	for a in frappe.db.sql("select name from tabPOL where direct_consumption = 1 and docstatus = 1 and posting_date > '2018-03-31'", as_dict=1):
		print(a.name)
		self = frappe.get_doc("POL", a.name)

		if self.hiring_warehouse:
			wh = self.hiring_warehouse
		else:
			wh = self.equipment_warehouse
		wh_account = frappe.db.get_value("Account", {"account_type": "Stock", "warehouse": wh}, "name")
		if not wh_account:
			frappe.throw(str(wh) + " is not linked to any account.")
		cl_account = "Clearing Account - CDCL"

		map_rate = frappe.db.get_value("Stock Ledger Entry", {"voucher_no": a.name, "actual_qty": ["<", 0]}, "valuation_rate")
		map_amount = flt(map_rate) * flt(self.qty)

		if self.hiring_cost_center:
			cc = self.hiring_cost_center
		else:
			cc = get_branch_cc(self.equipment_branch)

		gl_entries = []

                gl_entries.append(
                        prepare_gl(self, {"account": wh_account,
                                         "debit": flt(self.total_amount),
                                         "debit_in_account_currency": flt(self.total_amount),
                                         "cost_center": cc,
                                        })
                        )

                gl_entries.append(
                        prepare_gl(self, {"account": cl_account,
                                         "credit": flt(self.total_amount),
                                         "credit_in_account_currency": flt(self.total_amount),
                                         "cost_center": cc,
                                        })
                        )

                gl_entries.append(
                        prepare_gl(self, {"account": cl_account,
                                         "debit": flt(map_amount),
                                         "debit_in_account_currency": flt(map_amount),
                                         "cost_center": cc,
                                        })
                        )

                gl_entries.append(
                        prepare_gl(self, {"account": wh_account,
                                         "credit": flt(map_amount),
                                         "credit_in_account_currency": flt(map_amount),
                                         "cost_center": cc,
                                        })
                        )
		
                from erpnext.accounts.general_ledger import make_gl_entries
		make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False)

def adjust_sr():
	#for a in frappe.db.sql("select name from `tabStock Reconciliation` a where docstatus = 1 and posting_date between '2018-01-01' and '2018-12-31' and not exists (select 1 from `tabGL Entry` where voucher_no = a.name)", as_dict=1):
	print("Starting")
	frappe.db.sql("delete from `tabGL Entry` where voucher_no = 'SR/000053'")
	doc = frappe.get_doc("Stock Reconciliation", 'SR/000053')
	doc.make_gl_entries()
	print("DONE")

def check_it():
	for a in frappe.db.sql("select a.name, b.warehouse  from `tabDelivery Note` a, `tabDelivery Note Item` b where a.name = b.parent and a.docstatus = 1 and a.posting_date > '2017-12-31'", as_dict=1):
		stock = frappe.db.sql("select sum(actual_qty * valuation_rate) as amount from `tabStock Ledger Entry` where voucher_no = %s", a.name, as_dict=1)
		if stock[0]['amount']:
			try:
				stock = rounded(stock[0]['amount'] * -1, 2)
			except:
				frappe.throw(str(stock))
		else:
			stock = 0

		wh_account = frappe.db.get_value("Account", {"account_type": "Stock", "warehouse": a.warehouse}, "name")

		gl = frappe.db.sql("select credit from `tabGL Entry` where account = %s and voucher_no = %s", (wh_account, a.name), as_dict=1)
		if gl:
			gl = gl[0]['credit']
		else:
			gl = 0

		diff = flt(stock) - flt(gl)	
	
		if diff > 0.5 or diff < -0.5:
			print(str(a.name) + "  : " + str(stock) + " ==> " + str(gl))
			#frappe.db.sql("delete from `tabGL Entry` where voucher_no = %s", a.name)
			#doc = frappe.get_doc("Issue POL", a.name)
			#doc.update_stock_gl_ledger(1, 0)

def adjust_it():
	name = "IPOL180500322"
	frappe.db.sql("delete from `tabGL Entry` where voucher_no = %s", name)
	doc = frappe.get_doc("Issue POL", name)
	doc.update_stock_gl_ledger(1, 0)

def get_stats():
        filename = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = '/home/kinley/erp/logs/stats/top'+filename+'.log'
        values  = []
        
        with open(filename, "w") as outfile:
                subprocess.call("top -b -n1", shell=True, stdout=outfile)

        with open(filename) as infile:
                counter = 0
                start   = 999
                
                for line in infile:
                        counter += 1
                        record   = ()
                        if counter > start:
                                record = tuple([
                                        str(filename).strip(),
                                        line[:5].strip(),
                                        line[5:14].strip(),
                                        line[14:18].strip(),
                                        line[18:22].strip(),
                                        line[22:30].strip(),
                                        line[30:37].strip(),
                                        line[37:44].strip(),
                                        line[44:46].strip(),
                                        line[46:52].strip(),
                                        line[52:57].strip(),
                                        line[57:67].strip(),
                                        line[67:len(line)].strip(),
                                        str(frappe.session.user).strip(),
                                        str(now_datetime()).strip()
                                ])
                                values.append(str(record))
                        else:
                                if line[:5].strip() == "PID":
                                        start = counter
        if len(values) > 0:
                qry = """
                        insert into maintenance.stats(filename,pid,user,pr,ni,virt,res,shr,s,
                                cpu,mem,time,command,owner,creation)
                        values {0}
                """

                try:
                        sql = qry.format(",".join(values))
                        frappe.db.sql(sql)
                except Exception, e:
                        frappe.throw(_("{0}").format(str(e)))
        print filename

def adjust_pr_entry():
	for a in frappe.db.sql("select name from `tabPurchase Receipt` where name in ('PRCO18110243', 'PRCO18070032')", as_dict=1):
		print(str(a.name))
		frappe.db.sql("delete from `tabGL Entry` where voucher_no = %s", a.name)
		doc = frappe.get_doc("Purchase Receipt", a.name)
		doc.make_gl_entries()

	"""for a in frappe.db.sql("select distinct parent from `tabPurchase Receipt Item` where parent in ('PRCO18050290', 'PRCO18110238')", as_dict=1):
		print(str(a.parent))
		frappe.db.sql("delete from `tabGL Entry` where voucher_no = %s", a.parent)
		doc = frappe.get_doc("Purchase Receipt", a.parent)
		doc.make_gl_entries()"""

def adjust_se_entry():
	for a in frappe.db.sql("select distinct parent from `tabStock Entry Detail` where parent in ('PRCO18050290','SEMI18060781','SEMT18060017','PRCO18070032','PRCO18110238','PRCO18110243','SEMI18121376','SEMI18121378','SEMI18121380')", as_dict=1):
		print(str(a.parent))
		frappe.db.sql("delete from `tabGL Entry` where voucher_no = %s", a.parent)
		doc = frappe.get_doc("Stock Entry", a.parent)
		doc.make_gl_entries()

def update_increments_jan2019():
	err_count = 0
	for i in frappe.db.sql("select * from maintenance.update_increments where ifnull(flag,0) = 0", as_dict=True):
		if not frappe.db.exists("Salary Increment", {'fiscal_year': '2019', 'month': '01', 'employee': i.employee}):
			err_count += 1
			print i.sno, i.employee, i.remarks, i.increment_amount, i.flag

	if err_count:
		print 'ERROR: Unable to update increments due to above listed employees not having increments.'
		return False

	# Updating increments
	for i in frappe.db.sql("select * from maintenance.update_increments where ifnull(flag,0) = 0", as_dict=True):
		doc = frappe.get_doc("Salary Increment", {'fiscal_year': '2019', 'month': '01', 'employee': i.employee, 'docstatus': 0})
		print doc.name
		if i.remarks == "NO_INCREMENT":
			try:
				doc.remarks = 'No increment as per the excel sheet provided in ticket#1265'
				doc.increment = 0
				doc.new_basic = flt(doc.old_basic)
				doc.save()
				frappe.db.sql("update maintenance.update_increments set flag=1 where employee='{0}'".format(i.employee))
				print i.employee,'NO_INCREMENT'
			except Exception, e:
				print i
				frappe.throw(_("ERROR: While updating for NO_INCREMENT. {0}").format(e))
		elif i.remarks == "PRORATED":
			try:
				doc.remarks = 'Prorated as per the excel sheet provided in ticket#1265'
				doc.increment = flt(i.increment_amount)
				doc.new_basic = flt(doc.old_basic)+flt(i.increment_amount)
				doc.save()
				frappe.db.sql("update maintenance.update_increments set flag=1 where employee='{0}'".format(i.employee))
				print i.employee,'PRORATED'
			except Exception, e:
				print i
				frappe.throw(_("ERROR: While updating for PRORATED. {0}").format(e))
		else:
			print i
			frappe.throw(_("No matching record found for the excel sheet records provided"))

def update_consumed_budget_direct_payment():
        ml = frappe.db.sql("select p.name as name, p.posting_date as posting_date, p.cost_center as cost_center, p.debit_account as budget_account, p.amount as amount  from `tabDirect Payment` p where p.payment_type='payment' and journal_entry == "" p.name not in (select po_no from `tabConsumed Budget`)", as_dict=1)
        for a in ml:
                dc = frappe.new_doc("Committed Budget")
                dc.account = a.budget_account
                dc.cost_center = a.cost_center
                dc.po_no = a.name
                dc.po_date = a.posting_date
                dc.amount = a.amount
                dc.poi_name = a.name
                dc.date = a.posting_date
                dc.flags.ignore_permissions=1
                dc.submit()

                cb = frappe.new_doc("Consumed Budget")
                cb.account = a.budget_account
                cb.cost_center = a.cost_center
                cb.po_no = a.name
                cb.po_date = a.posting_date
                cb.amount = a.amount
                cb.pii_name = a.name,
                cb.com_ref = dc.name,
                cb.date = a.posting_date
                cb.flags.ignore_permissions=1
                cb.submit()
			
def update_consumed_budget():
        ml = frappe.db.sql("select p.name as name, p.posting_date as posting_date, p.cost_center as cost_center, i.budget_account as budget_account, i.amount as amount  from `tabImprest Recoup` p, `tabImprest Recoup Item` i where p.name = i.parent and p.docstatus = 1 and p.name not in (select po_no from `tabConsumed Budget`)", as_dict=1)
        for a in ml:
                dc = frappe.new_doc("Committed Budget")
                dc.account = a.budget_account
                dc.cost_center = a.cost_center
                dc.po_no = a.name
                dc.po_date = a.posting_date
                dc.amount = a.amount
                dc.poi_name = a.name
                dc.date = a.posting_date
                dc.flags.ignore_permissions=1
                dc.submit()

                cb = frappe.new_doc("Consumed Budget")
                cb.account = a.budget_account
                cb.cost_center = a.cost_center
                cb.po_no = a.name
                cb.po_date = a.posting_date
                cb.amount = a.amount
                cb.pii_name = a.name,
                cb.com_ref = dc.name,
                cb.date = a.posting_date
                cb.flags.ignore_permissions=1
                cb.submit()


def test():
	print("IN TEST")

def update_dp_gl():
        for a in frappe.db.sql("select name, posting_date from `tabDirect Payment` where docstatus = 1", as_dict=1):
                for b in frappe.db.sql("select name, posting_date from `tabGL Entry` where voucher_no = %s", a.name, as_dict=1):
                        if b.posting_date != a.posting_date:
                                print(str(a.name) + " : " + str(a.posting_date) + " to " + str(b.posting_date))
				frappe.db.sql("update `tabGL Entry` set posting_date = %s where name = %s", (a.posting_date, b.name))

def adjust_asset_sale():
	for a in frappe.db.sql("select name, branch from `tabSales Invoice` where naming_series = 'Fixed Asset' and docstatus = 1 and posting_date > '2018-01-01'", as_dict=1):
		gl = None
		gls = frappe.db.sql("select name from `tabGL Entry` where voucher_no = %s and account = 'Gain or Loss on Sale of Asset - CDCL'", a.name, as_dict=1)
		if gls:
			gl = gls[0].name
		if gl:
			cc = get_branch_cc(a.branch)
			print(str(a.name) + " : " + str(gl) + " ==> " + str(cc))
			frappe.db.sql("update `tabGL Entry` set cost_center = %s where name = %s", (cc, gl))

def adjust_budget_po():
        for a in frappe.db.sql("select name, status from `tabPurchase Order` where status = 'Closed' and transaction_date > '2017-12-31' and docstatus = 1", as_dict=1):
                print(str(a.name) + " ==> " + str(a.status))
                doc = frappe.get_doc("Purchase Order", a.name)
                doc.adjust_commit_budget(a.status)

def cancel_bdr():
	#for a in frappe.db.sql("select name from `tabBreak Down Report` b where b.docstatus = 1 and b.date < '2018-12-01' and not exists (select 1 from `tabJob Card` j where j.break_down_report = b.name);", as_dict=1):
	for a in frappe.db.sql("select name from `tabBreak Down Report` b where b.docstatus = 1 and b.date < '2018-12-01' and not exists (select 1 from `tabJob Card` j where j.break_down_report = b.name and j.docstatus in (0, 1));", as_dict=1):
		print(str(a.name))
		doc = frappe.get_doc("Break Down Report", a.name)
		doc.cancel()

"""def restore_jc():
	for a in frappe.db.sql("select a.name, b.stock_entry from `tabJob Card` a, `tabJob Card Item` b where a.name = b.parent and a.docstatus = 1 and b.stock_entry is not null group by b.stock_entry", as_dict=1):
		print(str(a.name) + " ==> " + str(a.stock_entry))
		frappe.db.sql("update `tabStock Entry` set job_card = %s where name = %s", (a.name, a.stock_entry))

def repost_stock_gl():
	sr = frappe.db.sql("select a.name from `tabStock Reconciliation` a, `tabStock Reconciliation Item` b where a.name = b.parent and b.item_code = '100452' and a.docstatus = 1", as_dict=1)
	for a in sr:
		print(a.name)
		self = frappe.get_doc("Stock Reconciliation", a.name)
		posting_date = str(get_datetime(str(self.posting_date) + ' ' + str(self.posting_time)))
                for b in self.items:
                        self.repost_issue_pol(b, posting_date)
		frappe.db.commit()

def check_pol_gl():
	for a in frappe.db.sql("select p.name from tabPOL p, `tabJournal Entry` b where p.jv = b.name and p.docstatus = 1 and b.docstatus = 2 and p.posting_date > '2017-12-31'", as_dict=1):
		print(str(a.name))

def link_pol_je():
	docs = frappe.db.sql("select je.reference_name, je.parent from `tabJournal Entry Account` je, tabPOL p where p.name = je.reference_name and je.docstatus = 1 and je.reference_name is not null", as_dict=1)
	for d in docs:
		frappe.db.sql("update tabPOL set jv = %s where name = %s", (d.parent, d.reference_name))
		print(str(d.reference_name) + " ==> " + str(d.parent))
"""


def update_sst_payment_methods():
        counter = 0
        for i in frappe.db.sql("select * from `tabSalary Component` where field_value is not null", as_dict=True):
                counter += 1
                print counter, i.name
                frappe.db.sql("""
                        update `tabSalary Structure`
                        set {0} = '{1}'
                """.format(i.field_method, i.payment_method))

        frappe.db.sql("update `tabSalary Structure` set temporary_transfer_allowance_method = 'Percent' where ifnull(temporary_transfer_allowance,0) > 0 and ifnull(lumpsum_temp_transfer_amount,0) = 0")
        frappe.db.sql("update `tabSalary Structure` set temporary_transfer_allowance_method = 'Lumpsum' where ifnull(temporary_transfer_allowance,0) = 0 and ifnull(lumpsum_temp_transfer_amount,0) > 0;");
        print 'Done updating.....'

