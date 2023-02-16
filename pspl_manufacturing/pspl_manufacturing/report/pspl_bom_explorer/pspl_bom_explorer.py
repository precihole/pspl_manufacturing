# Copyright (c) 2023, PSPL and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	get_data(filters, data)
	in_house_costing = frappe.db.get_value('BOM Record', filters.bom_record, 'in_house_costing')
	data.append(
		{
			"item_code": 'In House Costing',
			"costing": in_house_costing
		}
	)
	return columns, data


def get_data(filters, data):
	bom = frappe.db.get_value('BOM Record', filters.bom_record, 'bom')
	get_exploded_items(bom, filters.bom_record, data, flag= 1, bom_level = 0)


def get_exploded_items(bom, parent, data, flag, bom_level):
	if flag == 1:
		bom_items = frappe.get_all(
			"BOM Record Item",
			{"parent_bom": bom,"parent": parent},
			["item_code", "item_name", "indent","bom_level", "bom_no", "sum(qty) as qty","parent_bom","cost"],
			order_by = 'idx asc',
			group_by='item_code'
		)
	elif flag == 0:
		bom_items = frappe.get_all(
			"BOM Record Item",
			{"parent_bom": bom,"parent": parent, 'bom_level': ['>', bom_level]},
			["item_code", "item_name","indent","bom_level", "bom_no", "sum(qty) as qty","parent_bom", "cost"],
			order_by = 'idx asc',
			group_by='item_code'
		)
	costing = 0	
	for i in bom_items:
		item_dict = frappe.db.get_value('Item', i.item_code, ['last_purchase_rate', 'min_order_qty', 'lead_time_days', 'safety_stock', 'stock_uom', 'item_group', 'method_of_procurement', 'manufacturing_cost_c'], as_dict=1)
		i.last_purchase_rate = item_dict.last_purchase_rate
		i.min_order_qty = item_dict.min_order_qty
		i.lead_time_days = item_dict.lead_time_days
		i.safety_stock = item_dict.safety_stock
		i.uom = item_dict.stock_uom
		i.item_group = item_dict.item_group
		i.method_of_procurement = item_dict.method_of_procurement
		i.manufacturing_cost_c = item_dict.manufacturing_cost_c

		i.suppliers = fetch_all_supplier(i.item_code)
		if frappe.db.get_value("Has Role",{"role":'Purchase Manager', 'parent':frappe.session.user}, 'role') == 'Purchase Manager':
			if i.bom_no and (i.item_group == "Manufactured Components" and i.method_of_procurement == 'Manufacture'):
				costing = calculate_bom_cost(parent, i.bom_no)
				i.costing = round(costing * i.qty, 2)
			elif i.bom_no and i.item_group == "Sub-assembly":
				costing = calculate_bom_cost(parent, i.bom_no)
				i.costing = round(costing * i.qty, 2)
			else:
				if frappe.db.get_value('Item', i.item_code, 'method_of_procurement') == 'Manufacture':
					i.costing = round(frappe.db.get_value('Item', i.item_code, 'manufacturing_cost_c') * i.qty, 2)
				else:
					i.costing = round(frappe.db.get_value('Item', i.item_code, 'last_purchase_rate') * i.qty, 2)
		else:
			i.costing = 0
		data.append(i)
		if i.bom_no:
			get_exploded_items(i.bom_no, parent, data, flag = 0, bom_level = i.bom_level)

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

def calculate_bom_cost(parent, parent_bom):

	bom_record_items = frappe.get_all(
		"BOM Record Item",
		{"parent_bom": parent_bom, "parent": parent},
		["item_code", "item_name", "indent","bom_level", "bom_no", "sum(qty) as qty","parent_bom"],
		order_by = 'idx asc',
		group_by='item_code'
	)

	cost = 0
	rm_cost = 0
	for row in bom_record_items:
		item_group = frappe.db.get_value('Item', row.item_code, 'item_group')
		mop = frappe.db.get_value('Item', row.item_code, 'method_of_procurement')

		#cost logic
		if (row.bom_no and item_group == "Sub-assembly") or (row.bom_no and item_group == "Manufactured Components" and mop == "Manufacture"):
			rm_cost = calculate_bom_cost(parent, row.bom_no)
			cost = cost + rm_cost
		elif row.bom_no:
			rm_cost = calculate_bom_cost(parent, row.bom_no)
			cost = cost + rm_cost
			
			if frappe.db.get_value('Item', row.item_code, 'method_of_procurement') == 'Manufacture':
				rm_cost = frappe.db.get_value('Item', row.item_code, 'manufacturing_cost_c')
				rm_cost = round(rm_cost * row.qty, 2)
				cost = cost + rm_cost
			else:
				rm_cost = frappe.db.get_value('Item', row.item_code, 'last_purchase_rate')
				rm_cost = round(rm_cost * row.qty, 2)
				cost = cost + rm_cost
		else:
			if frappe.db.get_value('Item', row.item_code, 'method_of_procurement') == 'Manufacture':
				rm_cost = frappe.db.get_value('Item', row.item_code, 'manufacturing_cost_c')
				rm_cost = round(rm_cost * row.qty, 2)
				cost = cost + rm_cost
			else:
				rm_cost = frappe.db.get_value('Item', row.item_code, 'last_purchase_rate')
				rm_cost = round(rm_cost * row.qty, 2)
				cost = cost + rm_cost
		#end cost logic
	return cost

def get_columns():
	return [
		{"label": "Item Code","fieldtype": "Link","fieldname": "item_code","width": 300,"options": "Item"},
		{"label": "Item Group", "fieldtype": "Link", "options": "Item Group", "fieldname": "item_group", "width": 150},
		{"label": "MOP", "fieldtype": "Data", "fieldname": "method_of_procurement", "width": 100},
		{"label": "UOM", "fieldtype": "Link", "options": "UOM", "fieldname": "uom", "width": 60},
		{"label": "Qty", "fieldtype": "data", "fieldname": "qty", "width": 60},
		{"label": "Costing", "fieldtype": "Data", "fieldname": "costing", "width": 100},
		{"label": "Last Purchase Rate", "fieldtype": "Float", "fieldname": "last_purchase_rate", "width": 100},
		{"label": "Manufacturing Cost", "fieldtype": "Float", "fieldname": "manufacturing_cost_c", "width": 100},
		{"label": "MOQ", "fieldtype": "Int", "fieldname": "min_order_qty", "width": 100},
		{"label": "Lead Time in days", "fieldtype": "Int", "fieldname": "lead_time_days", "width": 100},
		{"label": "Safety Stock", "fieldtype": "Float", "fieldname": "safety_stock", "width": 100},
		{"label": "Suppliers", "fieldtype": "HTML Editor", "fieldname": "suppliers", "width": 100},
		{"label": "BOM Level", "fieldtype": "Int", "fieldname": "bom_level", "width": 100},
	]