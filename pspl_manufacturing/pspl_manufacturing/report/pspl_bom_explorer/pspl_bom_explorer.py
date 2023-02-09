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
	test_tr = []
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
		i.last_purchase_rate = frappe.db.get_value('Item', i.item_code, 'last_purchase_rate')
		i.min_order_qty = frappe.db.get_value('Item', i.item_code, 'min_order_qty')
		i.lead_time_days = frappe.db.get_value('Item', i.item_code, 'lead_time_days')
		i.safety_stock = frappe.db.get_value('Item', i.item_code, 'safety_stock')
		i.item_group = frappe.db.get_value('Item', i.item_code, 'item_group')
		i.method_of_procurement = frappe.db.get_value('Item', i.item_code, 'method_of_procurement')
		i.manufacturing_cost_c = frappe.db.get_value('Item', i.item_code, 'manufacturing_cost_c')
		i.suppliers = fetch_all_supplier(i.item_code)
		data.append(i)
		if i.bom_no:
			get_exploded_items(i.bom_no, docname, data, flag = 0, bom_level_test = i.bom_level)

def fetch_all_supplier(item_code):
	#unique supplier
	all_supplier = []
	unique_supplier = []
	supplier_string = ""
	purchase_orders = frappe.db.get_list('Purchase Order Item',
		{
			'item_code': item_code,
			'docstatus': 1
		},
		['parent'],
		group_by= 'parent'
	)
	for po in purchase_orders:
		supplier = frappe.db.get_value('Purchase Order',po.parent,'supplier')
		all_supplier.append(supplier)
	#remove duplicate supplier
	for ven in all_supplier:
		if ven not in unique_supplier:
			unique_supplier.append(ven)
	#convert array to string
	supplier_string = ','.join(unique_supplier)
	return supplier_string

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
		#added from Item Master
		{"label": "UOM", "fieldtype": "Link", "options": "UOM", "fieldname": "uom", "width": 100},
		{"label": "Last Purchase Rate", "fieldtype": "Float", "fieldname": "last_purchase_rate", "width": 100},
		{"label": "MOQ", "fieldtype": "Int", "fieldname": "min_order_qty", "width": 100},
		{"label": "Lead Time in days", "fieldtype": "Int", "fieldname": "lead_time_days", "width": 100},
		{"label": "Safety Stock", "fieldtype": "Float", "fieldname": "safety_stock", "width": 100},
		{"label": "Item Group", "fieldtype": "Link", "options": "Item Group", "fieldname": "item_group", "width": 100},
		{"label": "MOP", "fieldtype": "Data", "fieldname": "method_of_procurement", "width": 100},
		{"label": "Manufacturing Cost", "fieldtype": "Float", "fieldname": "manufacturing_cost_c", "width": 100},
		{"label": "Suppliers", "fieldtype": "HTML Editor", "fieldname": "suppliers", "width": 100},
	]