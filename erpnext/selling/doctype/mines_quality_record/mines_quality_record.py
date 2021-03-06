# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class MinesQualityRecord(Document):
	
	def autoname(self):
		self.name = make_autoname('MQR.YYYY.MM.####')
