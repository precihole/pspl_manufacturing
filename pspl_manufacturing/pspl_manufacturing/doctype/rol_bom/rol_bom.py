# Copyright (c) 2023, PSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ROLBOM(Document):
	def before_save(doc):
		if not doc.items:
			frappe.throw('Enter atleast one item to check BOM Stock Report')