# Copyright (c) 2023, PSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ROLBOM(Document):
	def before_save(doc):
		if not (doc.bom_level == 0 or doc.bom_level == 1 or doc.bom_level == 2):
			frappe.throw(str(doc.bom_level) + ' is not a valid BOM Level')
		if not doc.items:
			frappe.throw('Enter atleast one item to check BOM Stock Report')
