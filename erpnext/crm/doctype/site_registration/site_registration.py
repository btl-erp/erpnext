# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.core.doctype.user.user import send_sms

class SiteRegistration(Document):
	def validate(self):
		self.validate_user()
		self.update_user_details()
		self.update_status()
		#self.validate_cid()
		self.validate_defaults()
		self.validate_approval_no()
		self.validate_items()
		self.attach_cid()

	def after_insert(self):
		#msg = "Your request for site registration is created successfully. You will be notified upon approval by NRDCL. Tran Ref No {0}".format(self.name)
		#self.sendsms(msg)
		pass

	def on_submit(self):
		self.validate_documents()
		self.validate_distance()
		self.create_site()
		self.sendsms()

	def before_cancel(self):
		self.update_status()

	def on_cancel(self):
		self.remove_site()

	def on_update(self):
		self.get_distance()

	def attach_cid(self):
		target_doc = None
		def set_missing_values(source, target):
			target.attached_to_doctype = self.doctype
			target.attached_to_name = self.name

		''' attach documents '''
		file = frappe.db.sql("""
			select 
				f.name file, ur.name user_request,
				f.attached_to_doctype, f.attached_to_name, f.file_name, f.file_url 
			from `tabUser Request` ur, `tabFile` f
			where ur.user	 	  = "{user}"
			and ur.request_category   = "CID Details" 
			and ur.docstatus 	  = 1
			and f.attached_to_doctype = "User Request"
			and f.attached_to_name 	  = ur.name
			order by ur.modified desc
			limit 1
		""".format(user=self.user),as_dict=True)
		if file and not frappe.db.exists("File", {"attached_to_doctype": self.doctype, "attached_to_name": self.name, "file_url": file[0].file_url}):
			attachment = get_mapped_doc("File", file[0].file, {
					"File": {
						"doctype": "File",
					},
			}, target_doc, set_missing_values, ignore_permissions=True)
			attachment.save(ignore_permissions=True)

	def validate_approval_no(self):
		if not self.approval_no:
			frappe.throw(_("Construction Approval No. is mandatory"))
		self.approval_no = str(self.approval_no).strip()

		sr = frappe.db.sql("""
				select name, site, docstatus, approval_status, approval_no
				from `tabSite Registration`
				where user = "{user}"
				and docstatus != 2
				and lower(approval_no) = "{approval_no}"
				and name != "{name}"
			""".format(name=self.name, user=self.user, approval_no=str(self.approval_no).lower()), as_dict=True)
		for i in sr:
			if i.docstatus == 0:
				link = frappe.get_desk_link("Site Registration", i.name)
				frappe.throw(_("A request already exists for Construction Approval No. {0}. Ref# {1}")\
					.format(self.approval_no, link), title="Duplicate Entry")
			else:
				if i.approval_status == "Approved":
					if i.site:
						link = frappe.get_desk_link("Site", i.site)
						frappe.throw(_("A Site already exists for Construction Approval No. {0}. Ref# {1}")\
							.format(self.approval_no, link), title="Duplicate Entry")
					else:
						link = frappe.get_desk_link("Site Registration", i.name)
						frappe.throw(_("A request already exists for Construction Approval No. {0}. Ref# {1}")\
							.format(self.approval_no, link), title="Duplicate Entry")

	def update_user_details(self):
		if frappe.db.exists("User Account", self.user):
			doc = frappe.get_doc("User Account", self.user)
			self.full_name = doc.full_name
			self.mobile_no = doc.mobile_no
			self.alternate_mobile_no = doc.alternate_mobile_no

	def validate_user(self):
		if not self.user:
			frappe.throw(_("User is mandatory"))
		else:
			if not frappe.db.exists("User Request",{"user":self.user,"request_category": "CID Details",\
				"docstatus":1,"approval_status": "Approved"}):
				if frappe.db.exists("User Request",{"user":self.user,"request_category":"CID Details","docstatus":0}):
					frappe.throw(_("Your request for account verification is pending approval"))
				else:
					frappe.throw(_("You need to submit a copy of CID document first"))

	def sendsms(self,msg=None):
		if self.docstatus == 1:
			if self.approval_status == "Rejected":
				msg = "Your request for site registration is {0}. Tran Ref No {1}. {2}".format(str(self.approval_status).lower(),self.name,self.rejection_reason)	
			else:
				msg = "Your request for site registration is {0}. Tran Ref No {1}".format(str(self.approval_status).lower(),self.name)	
		mobile_no = frappe.db.get_value("User", self.user, "mobile_no")
		if mobile_no:
			send_sms(mobile_no, msg)

	def update_status(self):
		if self.docstatus == 0:
			self.status = "Pending"
		elif self.docstatus == 1:
			self.status = self.approval_status
		else:
			self.status = "Cancelled"

	def get_distance(self):
		if not self.get("distance"):
			for i in get_distance(self.name):
				row = self.append('distance',{})
				row.update(i)

	def validate_distance(self):
		if self.approval_status == "Rejected":
			return 
		for i in self.get("distance"):
			if not flt(i.distance):
				frappe.throw(_("Row#{0} : Please enter distance from unit <b>{1}</b> to site location").format(i.idx, i.branch))

	def validate_documents(self):
		if not frappe.db.exists('File', {'attached_to_doctype': self.doctype, 'attached_to_name': self.name})\
			and self.approval_status == "Approved":
			frappe.throw(_("Please attach valid Construction Approval Document"))

	def validate_cid(self):
		if not frappe.db.sql("""select 1 from `tabUser Account` where name = "{0}" 
				and cid_file_front is not null and cid_file_back is not null""".format(self.user)):
			frappe.throw(_("You need to submit a copy of CID document first"))

	def validate_defaults(self):
		# validate construction dates
		self.site_type = frappe.db.get_value("Site Type", {"is_default": 1}, "name") if not self.site_type else self.site_type
		if get_datetime(self.construction_end_date) <= get_datetime(self.construction_start_date):
			frappe.throw(_("Construction End Date cannot be on or before start date"))
		self.is_building = frappe.db.get_value("Construction Type", self.construction_type, "is_building")

	def validate_items(self):
		dup = {}
		for i in self.get("items"):
			if i.item_sub_group in dup:
				frappe.throw(_("Row#{0}: Duplication of material {1} not permitted").format(i.idx, i.item_sub_group))
			else:
				dup[i.item_sub_group] = 1

			if flt(i.expected_quantity) < 0:
				frappe.throw(_("Row#{0}: Expected Quantity cannot be a negative value").format(i.idx))

	def create_site(self):
		""" create site """
		target_doc = None
		site 	   = None
		def set_missing_values(source, target):
			target.attached_to_doctype = "Site"
			target.attached_to_name = site.name

		if self.approval_status == "Rejected":
			return
		elif self.approval_status == "Rejected" and not self.rejection_reason:
			frappe.throw(_("Rejection Reason is mandatory"))
		elif self.approval_status == "Pending":
			frappe.throw(_("Request cannot be submitted in Pending status"))
		#elif not self.approval_document:
		#	frappe.throw(_("Please attach valid Construction Approval Document"))

		site = get_mapped_doc("Site Registration", self.name, {
				"Site Registration": {
					"doctype": "Site",
				},
				"Site Registration Item": {
					"doctype": "Site Item",
				},
				"Site Registration Distance": {
					"doctype": "Site Distance",
				},
		}, target_doc=None)
		site.save(ignore_permissions=True)
		self.db_set("site", site.name)

		''' attach documents '''
		if site:
			for i in frappe.db.get_all("File", "name", {"attached_to_doctype": self.doctype, "attached_to_name": self.name}):
				attachment = get_mapped_doc("File", i.name, {
						"File": {
							"doctype": "File",
						},
				}, target_doc, set_missing_values)
				attachment.save(ignore_permissions=True)

	def remove_site(self):
		""" deactivate the site """
		if frappe.db.exists("Site", {"site_registration": self.name}):
			doc = frappe.get_doc("Site", {"site_registration": self.name})
			frappe.db.sql("""update `tabSite` set enabled=0,docstatus=2 where name="{0}" """.format(doc.name))
			frappe.db.sql("""update `tabSite Item` set docstatus=2 where parent="{0}" """.format(doc.name))


@frappe.whitelist()
def get_distance_old(site):
	qry = """
		select distinct cbs.branch, i.name as item, i.item_name, i.item_sub_group
		from 
			`tabCRM Branch Setting` cbs,
			`tabCRM Branch Setting Item` cbsi,
			`tabItem` i,
			`tabSite Registration Item` sri
		where sri.parent = '{0}' 
		and i.item_sub_group = sri.item_sub_group
		and cbsi.item 	= i.name
		and cbs.name 	= cbsi.parent
		and cbs.has_common_pool = 1
		order by cbs.branch, i.name
	""".format(site)
	return frappe.db.sql(qry, as_dict=True)

@frappe.whitelist()
def get_distance(site):
	qry = """
		select distinct cbs.branch, i.item_sub_group
		from 
			`tabCRM Branch Setting` cbs,
			`tabCRM Branch Setting Item` cbsi,
			`tabItem` i,
			`tabSite Registration Item` sri
		where sri.parent = '{0}' 
		and i.item_sub_group = sri.item_sub_group
		and cbsi.item 	= i.name
		and cbs.name 	= cbsi.parent
		and cbs.has_common_pool = 1
		and exists(select 1
			from `tabTransportation Rate` tr
			where tr.branch = cbs.branch
			and tr.item_sub_group = i.item_sub_group)
		order by cbs.branch, i.item_sub_group
	""".format(site)
	return frappe.db.sql(qry, as_dict=True)
