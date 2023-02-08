# Copyright (c) 2023, PSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BOMRecord(Document):
	def before_insert(doc):
		get_exploded_items(doc.bom, doc)

def get_exploded_items(bom, doc,indent=0, qty=1):
	exploded_items = frappe.get_list(
		"BOM Item",
		{"parent": bom},
		["qty", "bom_no","item_name","item_code"],
	)
	for item in exploded_items:
		doc.append('items',
			{
				"item_code": item.item_code,
				"item_name": item.item_name,
				"bom_no": item.bom_no,
				"bom_level": indent,
				"indent" : indent,
				"qty": item.qty * qty,
				"parent_bom": bom
			}
		)
		if item.bom_no:
			get_exploded_items(item.bom_no, doc, indent=indent + 1, qty=item.qty)

@frappe.whitelist()
def chk_bom_change_status():
	#passing child doctype name to fetch respective item bom
	bom_no = frappe.db.get_value('BOM Record Item', frappe.form_dict.item_name, 'bom_no')

	#checking if both bom_no is same as after change of bom
	if bom_no == frappe.form_dict.bom_no:
		frappe.msgprint(frappe.form_dict.bom_no +' is same as ' + frappe.form_dict.bom_no)
		return False
	elif not bom_no == frappe.form_dict.bom_no:
		#updating item bom with change bom
		bom_record_item = frappe.get_doc("BOM Record Item", frappe.form_dict.item_name)
		bom_record_item.bom_no = frappe.form_dict.bom_no
		bom_record_item.save()
		return True

@frappe.whitelist()
def delete_items_based_on_new_bom():
	bom_record = frappe.get_doc("BOM Record", frappe.form_dict.docname)
	to_remove = []
	#removing items
	for d in bom_record.items:
		if d.idx > int(frappe.form_dict.idx):
			if d.bom_level > int(frappe.form_dict.bom_level):
				to_remove.append(d)
			elif d.bom_level <= int(frappe.form_dict.bom_level):
				break
		else:
			pass
	#removed if array is not empty
	if to_remove:
		[bom_record.remove(d) for d in to_remove]
	bom_record.save()
	return True

@frappe.whitelist()
def add_items_based_on_new_bom():
	bom_record = frappe.get_doc("BOM Record", frappe.form_dict.docname)
	to_add = []

	#set data for passing in function
	bom = frappe.form_dict.bom_no
	indent = int(frappe.form_dict.bom_level) + 1
	doc = bom_record
	index = int(frappe.form_dict.idx)

	to_add = get_items_based_on_new_bom(bom, doc, indent, index, call=0, temp = [])
	for i in to_add:
		bom_record.append('items',i)
	bom_record.save()
	return True

def get_items_based_on_new_bom(bom, doc, indent, index, call, temp, qty=1):
	exploded_items = frappe.get_list(
		"BOM Item",
		{"parent": bom},
		["qty", "bom_no", "item_code"],
	)
	for item in exploded_items:
		index = index + 1
		temp.append(
			{
				"item_code": item.item_code,
				"bom_no": item.bom_no,
				"indent": indent,
				"bom_level": indent,
				"qty": item.qty * qty,
				"idx" : index,
				"parent_bom": bom
			}
		)
		if item.bom_no:
			index = get_items_based_on_new_bom(item.bom_no, doc, indent=indent + 1, index=index, call=1, temp = temp, qty=item.qty)
	if call == 1:
		return index
	elif call == 0:
		return temp