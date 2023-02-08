# Copyright (c) 2023, PSPL and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	get_data(filters, data)
	return columns, data


def get_data(filters, data):
	get_exploded_items(filters.bom_record,filters.bom_record, data, flag= 1, bom_level_test = None)


def get_exploded_items(bom_record, docname, data, flag, bom_level_test):
	if flag == 1:
		bom = frappe.db.get_value('BOM Record', bom_record, 'bom')
		test = frappe.get_all(
			"BOM Record Item",
			{"parent_bom": bom,"parent": docname},
			["item_code", "item_name", "indent","bom_level", "bom_no", "qty","parent_bom"],
			order_by = 'idx asc',
			group_by='item_code'
		)
	elif flag == 0:
		bom = bom_record
		test = frappe.get_all(
			"BOM Record Item",
			{"parent_bom": bom_record,"parent": docname, 'bom_level': ['>', bom_level_test]},
			["item_code", "item_name","indent","bom_level", "bom_no", "qty","parent_bom"],
			order_by = 'idx asc',
			group_by='item_code'
		)
	for i in test:
		data.append(i)
		if i.bom_no:
			get_exploded_items(i.bom_no, docname, data, flag = 0, bom_level_test = i.bom_level)

def get_columns():
	return [
		{
			"label": "Item Code",
			"fieldtype": "Link",
			"fieldname": "item_code",
			"width": 300,
			"options": "Item",
		},
		{"label": "Item Name", "fieldtype": "data", "fieldname": "item_name", "width": 100},
		{"label": "BOM", "fieldtype": "Link", "fieldname": "bom_no", "width": 150, "options": "BOM"},
		{"label": "Qty", "fieldtype": "data", "fieldname": "qty", "width": 100},
		# {"label": "UOM", "fieldtype": "data", "fieldname": "uom", "width": 100},
		{"label": "BOM Level", "fieldtype": "Int", "fieldname": "bom_level", "width": 100},
		# {"label": "Standard Description", "fieldtype": "data", "fieldname": "description", "width": 150},
		# {"label": "Scrap", "fieldtype": "data", "fieldname": "scrap", "width": 100},
	]