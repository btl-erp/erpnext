# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint,add_days, cstr, flt, getdate, nowdate, rounded, date_diff

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_conditions(filters):
	branch = consumption_date = rate_date = jc_date = insurance_date =  reg_date = tc_date = operator_date = le_date = ss_date= reg_date = not_cdcl = disable = mr_date =  his_date = ""
	'''if filters.get("branch"):
		branch += str(filters.branch)'''

	if filters.get("not_cdcl"):
                not_cdcl +=  "0"
        
        if filters.get("include_disabled"):
                disable  += " "
        else:
                disable  += "0" 

	if filters.get("from_date") and filters.get("to_date"):
		consumption_date = get_dates(filters, "vl", "from_date", "to_date")
		rate_date 	 = get_dates(filters, "pol", "date")
		jc_date 	 = get_dates(filters, "jc", "finish_date")
		insurance_date   = get_dates(filters, "ins", "id.insured_date")
		reg_date         = get_dates(filters, "ins", "rd.registration_date")
		operator_date    = get_dates(filters, "op", "start_date", "end_date")
		tc_date		 = get_dates(filters, "tc", "posting_date")		
		le_date		 = get_dates(filters, "le", "ifnull(le.encashed_date, le.application_date)")
		ss_date		 = get_dates(filters, "ss", "start_date", "ifnull(end_date,curdate())")
		reg_date	 = get_dates(filters, "reg", "registration_date")
		mr_date		 = get_dates(filters, "mr_pay", "from_date", "to_date")
		his_date         = get_dates(filters, "equipments", "eh.from_date", "eh.to_date") #added equ_his date
	return  consumption_date, rate_date, jc_date, insurance_date, reg_date,  operator_date, tc_date, le_date, ss_date, not_cdcl, disable, mr_date, his_date

def get_dates(filters, module = "", from_date_column = "", to_date_column = ""):
	cond1 = ""
	cond2 = ""
	if from_date_column:
		cond1 = ("{0} between \'" + str(filters.from_date) + "\' and \'" + str(filters.to_date) + "\'").format(from_date_column)
	
	if to_date_column:
		if module in ("op","ss", "equipments"):
			cond2 = str(" or {0} between \'" + str(filters.from_date) + "\' and \'" + str(filters.to_date) + "\'").format(to_date_column)
		else:
			cond2 = str("and {0} between \'" + str(filters.from_date) + "\' and \'" + str(filters.to_date) + "\'").format(to_date_column)

	return "({0} {1})".format(cond1, cond2)

def get_data(filters):
	consumption_date, rate_date, jc_date, insurance_date,  reg_date, operator_date, tc_date, le_date, ss_date, not_cdcl, disable, mr_date,his_date  =  get_conditions(filters)
	#frappe.msgprint(reg_date)
	data = []
	# checks if the equipment history branch equals the filters branch
	if filters.get("branch"):
		branch_cond = " and eh.branch = \'"+str(filters.branch)+"\'"
	else:
		branch_cond = " and eh.branch like '%' "

	if filters.get("not_cdcl"):
                not_cdcll = " and not_cdcl = 0"
	else:
		not_cdcll = " and not_cdcl like '%' "
        
        if filters.get("include_disabled"):
               dis = " and is_disabled like '%' "
        else:
               dis  = " and is_disabled != 1 " 
	# fetching the branch, from_date, to_date from equipment history tab
        query = """
				select e.name as name, eh.branch as branch, e.equipment_number as equipment_number, 
					e.equipment_type as equipment_type, e.equipment_model as equipment_model
					from `tabEquipment` e, `tabEquipment History` eh 
					where eh.parent = e.name
					{0} {1} {2} 
					and ('{3}' between eh.from_date and ifnull(eh.to_date, now())
					or '{4}' between eh.from_date and ifnull(eh.to_date, now()))
					 group by eh.branch, eh.parent order by eh.branch, eh.parent
                        """.format(not_cdcll, branch_cond, dis, filters.from_date, filters.to_date)
        equipments = frappe.db.sql(query, as_dict=1);

    	for eq in equipments:
		#frappe.msgprint("{0}".format(eq))
                # `tabVehicle Logbook` 
        	vl = frappe.db.sql("""
                        	select sum(ifnull(consumption,0)) as consumption
                        	from `tabVehicle Logbook`
                        	where equipment = '{0}'
                        	and   docstatus = 1
				and   {1} and branch = '{2}' 
                    """.format(eq.name,consumption_date, eq.branch), as_dict=1)[0]

                # `tabPOL`
            	pol = frappe.db.sql("""
                            	select (sum(qty*rate)/sum(qty)) as rate
                            	from `tabPOL`
                        	where branch = '{0}'
                        	and   docstatus = 1
                    """.format(eq.branch), as_dict=1)[0]
                # `tabJob Card`
                # owned_by pending
            	jc = frappe.db.sql("""
                            	select sum(ifnull(goods_amount,0)) as goods_amount,
                            		sum(ifnull(services_amount,0)) as services_amount
                            	from `tabJob Card`
                            	where equipment = '{0}'
                            	and   docstatus = 1
				and   {1} and branch = '{2}'
                    """.format(eq.name,jc_date, eq.branch), as_dict=1)[0]
		#Insurance
		ins = frappe.db.sql("""
			 	select sum(ifnull(id.insured_amount,0)) as insurance  
				from `tabInsurance Details` id,	`tabInsurance and Registration` ir 
				where id.parent = ir.name and ir.equipment = '{0}'
				and   {1}
			 """.format(eq.name, insurance_date), as_dict=1)[0]
		#Reg fee
		reg = frappe.db.sql("""
				select sum(ifnull(rd.registration_amount,0)) as r_amount
				from `tabRegistration Details` rd, `tabInsurance and Registration` i  
				where rd.parent = i.name  
				and i.equipment = '{0}'
                                and   {1}
			""".format(eq.name, reg_date), as_dict=1)[0]
	
		#v1.append(	#frappe.msgprint(values)
		c_operator = frappe.db.sql("""
				select eo.operator, eo.employee_type, eo.start_date, eo.end_date , eo.name, eh.branch 
				from `tabEquipment Operator` eo, `tabEquipment History` eh
				where eo.parent = '{0}' and eo.parent = eh.parent and eh.branch = '{1}'
				and   eo.docstatus < 2
			""".format(eq.name, eq.branch), as_dict=1)
		travel_claim = 0.0
		e_amount     = 0.0
		gross_pay    = 0.0
		total_exp    = 0.0
		total_sal    = 0.0
		for co in c_operator:
			#frappe.msgprint("{0}".format(co.branch)) 
			if co.employee_type == "Muster Roll Employee":
				#PRoCESS FROM "PROCESS MR PAYMENT"
				mr_pay = frappe.db.sql("""
						select sum(ifnull(mr.total_overall_amount,0)) as mr_payment 
                                                from `tabProcess MR Payment` mr , `tabMR Payment Item` mi
                                                where mi.parent = mr.name
                                                and mi.id_card = '{0}' 
                                                and mr.docstatus = 1
                                                and {1} and branch = '{2}'
					""".format(co.operator, mr_date, co.branch), as_dict=1)[0]

				'''select sum(ifnull(mr.total_overall_amount,0)) as mr_payment 
                                                from `tabProcess MR Payment` mr 
                                                where mr.name = '{0}' 
                                                and mr.docstatus = 1
                                                and {1}'''

				travel_claim += 0.0
                                e_amount     += 0.0
                                gross_pay    += flt(mr_pay.mr_payment)	
			elif co.employee_type == "Employee":
				tc = frappe.db.sql("""
						select sum(ifnull(tc.total_claim_amount,0)) as travel_claim
						from `tabTravel Claim` tc 
						where tc.employee = '{0}'
						and   tc.docstatus = 1
						and   {1} and branch = '{2}'
					""".format(co.operator, tc_date, co.branch), as_dict=1)[0]


				#Leave Encashment Aomunt
				lea = frappe.db.sql("""
						select sum(ifnull(le.encashment_amount,0)) as e_amount 
						from `tabLeave Encashment` le
						where le.employee = '{0}'
						and   le.docstatus = 1
						and   {1}
					""".format(co.operator, le_date), as_dict=1, debug =1)[0]



				cem = frappe.db.sql("""
						select employee, gross_pay, start_date, end_date
						from `tabSalary Slip` ss 
						where employee = '{0}'
						and docstatus = 1
						and {1} and branch = '{2}'
				      """.format(co.operator, ss_date, co.branch),  as_dict=1, debug =1)
				if cem:
					for e in cem:
						total_days = flt(date_diff(e.end_date, e.start_date) + 1)
						if e.end_date < co.start_date:
							pass	
						elif co.end_date and e.start_date > co.end_date:
							pass
						elif co.end_date and e.start_date > co.start_date and e.end_date < co.end_date:
							total_sal += flt(e.gross_pay)
						#	frappe.msgprint("A")
						elif co.end_date and e.start_date <= co.start_date and e.end_date >= co.end_date:
						#	frappe.msgprint("B")
							days = date_diff(co.end_date, co.start_date) + 1
							total_sal += (flt(e.gross_pay) * days ) / total_days
						elif co.end_date and e.start_date > co.start_date and e.end_date > co.end_date:
							days = date_diff(co.end_date, e.start_date) + 1
							total_sal += (flt(e.gross_pay) * days ) / total_days
						#	frappe.msgprint("C")
						elif co.end_date and e.start_date < co.start_date and e.end_date < co.end_date:
							days = date_diff(e.end_date, co.start_date) + 1
							total_sal += (flt(e.gross_pay) * days ) / total_days
						#	frappe.msgprint("D")
						elif not co.end_date and e.start_date >= co.start_date:
							total_sal += flt(e.gross_pay)
						#	frappe.msgprint("E")
						elif not co.end_date and e.start_date < co.start_date:
							days = date_diff(e.end_date, co.start_date) + 1
						#	frappe.msgprint("F")
							total_sal += (flt(e.gross_pay) * days ) / total_days
						else:
							pass

				travel_claim += flt(tc.travel_claim)
				e_amount     += flt(lea.e_amount) 
				gross_pay    += flt(total_sal)
		        total_exp = 	(flt(vl.consumption)*flt(pol.rate))+flt(ins.insurance)+flt(jc.goods_amount)+flt(reg.r_amount)+flt(jc.services_amount)+ travel_claim+e_amount + gross_pay
		data.append((	eq.branch,
				eq.name,
				eq.equipment_number,
				eq.equipment_type,
				flt(vl.consumption)*flt(pol.rate),
				flt(ins.insurance)+flt(reg.r_amount),
				flt(jc.goods_amount),
				flt(jc.services_amount), 
				gross_pay,
				e_amount,
				travel_claim,
				total_exp))
    	return tuple(data)

def get_columns(filters):
	cols = [
		("Branch") + ":Data:120",
                ("ID") + ":Link/Equipment:120",
		("Registration No") + ":Data:120",
		("Equipment Type") + ":Data:120",
                ("HSD Consumption") + ":Float:120",
                ("Insurance") + ":Float:120",
                ("Goods Amount") + ":Float:120",
                ("Services Amount") + ":Float:120",
		("Gross Pay") + ":Float:120",
		("Leave Encashment") + ":Currency:120",
		("Travel Claim") + ":Currency:120",
		("Total Expense") + ":Currency:120"
	]
	return cols
