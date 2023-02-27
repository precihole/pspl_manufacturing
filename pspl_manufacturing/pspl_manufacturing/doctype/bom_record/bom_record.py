# Copyright (c) 2023, PSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BOMRecord(Document):
	def before_insert(doc):
		get_exploded_items(doc.bom, doc)

def get_exploded_items(bom, doc, indent=0, qty=1):
	exploded_items = frappe.get_list(
		"BOM Item",
		{"parent": bom},
		["qty", "bom_no", "item_name", "item_code"],
		order_by = 'idx asc',
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
			get_exploded_items(item.bom_no, doc, indent=indent + 1, qty=1)

@frappe.whitelist()
def check_bom_status():
	bom_no = frappe.db.get_value('BOM Record Item', frappe.form_dict.child_table_name, 'bom_no')
	#both bom are same validation
	if bom_no == frappe.form_dict.bom_no:
		frappe.msgprint(frappe.form_dict.bom_no +' is same as ' + frappe.form_dict.bom_no)
		return False
	#bom empty validation
	elif frappe.form_dict.bom_no == '':
		frappe.msgprint('BOM should not empty')
		return False
	#bom not same
	elif not bom_no == frappe.form_dict.bom_no:
		child_table = frappe.get_doc("BOM Record Item", frappe.form_dict.child_table_name)
		child_table.bom_no = frappe.form_dict.bom_no
		child_table.save()
		return True

@frappe.whitelist()
def delete_by_new_bom():
	parent_table = frappe.get_doc("BOM Record", frappe.form_dict.parent_table_name)
	to_remove = []
	for d in parent_table.items:
		if d.idx > int(frappe.form_dict.idx):
			if d.bom_level > int(frappe.form_dict.bom_level):
				to_remove.append(d)
			elif d.bom_level <= int(frappe.form_dict.bom_level):
				break
		else:
			pass
	if to_remove:
		[parent_table.remove(d) for d in to_remove]
	parent_table.save()
	return True

@frappe.whitelist()
def add_by_new_bom():
	parent_table = frappe.get_doc("BOM Record", frappe.form_dict.parent_table_name)
	to_add = []
	bom = frappe.form_dict.bom_no
	indent = int(frappe.form_dict.bom_level) + 1
	doc = parent_table
	index = int(frappe.form_dict.idx)

	to_add = get_items_by_new_bom(bom, doc, indent, index, call=0, temp = [])
	for item in to_add:
		parent_table.append('items', item)
	parent_table.save()
	return True

def get_items_by_new_bom(bom, doc, indent, index, call, temp, qty=1):
	exploded_items = frappe.get_list(
		"BOM Item",
		{"parent": bom},
		["qty", "bom_no","item_name","item_code"],
	)
	for item in exploded_items:
		index = index + 1
		temp.append(
			{
				"item_code": item.item_code,
				"item_name": item.item_name,
				"bom_no": item.bom_no,
				"indent": indent,
				"bom_level": indent,
				"qty": item.qty * qty,
				"idx" : index,
				"parent_bom": bom
			}
		)
		if item.bom_no:
			index = get_items_by_new_bom(item.bom_no, doc, indent=indent + 1, index=index, call=1, temp = temp, qty=item.qty)
	if call == 1:
		return index
	elif call == 0:
		return temp