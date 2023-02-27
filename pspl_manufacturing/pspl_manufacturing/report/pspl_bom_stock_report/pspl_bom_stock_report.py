# Copyright (c) 2023, PSPL and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	get_data(filters, data)
	return columns, data

def get_data(filters, data):
	get_items_from_rol_bom(filters.rol_bom, data)

def get_items_from_rol_bom(parent_table_name, data):
	temp = []

	#bom level 0 or 1 or 2
	bom_level = frappe.db.get_value('ROL BOM', parent_table_name, 'bom_level')
	rol_bom_items = frappe.get_all(
		"ROL BOM Item",
		{"parent": parent_table_name},
		["item_code", "item_name","bom", "req_qty","warehouse"],
		order_by = 'idx asc'
	)
	for rows in rol_bom_items:
		#1 BOM Level 0
		if bom_level == '0':
			is_group = frappe.db.get_value("Warehouse",{"name": rows.warehouse},["is_group"])
			if is_group == 1:
				group_warehouse_list = frappe.get_all("Warehouse",
					{"parent_warehouse": rows.warehouse},
					["name"],
					pluck='name'
				)
				if group_warehouse_list:
					actual_qty = frappe.db.get_all(
						"Bin",
						{"item_code": rows.item_code, "warehouse": ["in", group_warehouse_list]},
						["sum(actual_qty) as actual_qty"], group_by='item_code')
					if actual_qty:
						rows.actual_qty = actual_qty[0].actual_qty
					else:
						rows.actual_qty = 0
			else:
				rows.actual_qty = frappe.db.get_value("Bin",{"item_code": rows.item_code, "warehouse": ["in",[rows.warehouse]]},["actual_qty"]) or 0
			rows.qty = rows.req_qty
			rows.diff = rows.actual_qty - rows.qty
			safety_stock = frappe.db.get_value('Item', rows.item_code, 'safety_stock') or 0
			lead_time_days = frappe.db.get_value('Item', rows.item_code, 'lead_time_days') or 0
			rows.cal_rol = (lead_time_days + safety_stock) * (rows.qty / 26)
			rows.rol = frappe.db.get_value('Item Reorder', {'parent':rows.item_code}, 'warehouse_reorder_level') or 0
			#primary_location_c is custom fiedl in item
			rows.location = frappe.db.get_value('Item', rows.item_code, 'primary_location_c')
			rows.item_name = frappe.db.get_value('Item', rows.item_code, 'item_name')
			rows.item_name = frappe.db.get_value('Item', rows.item_code, 'item_name')
			rows.item_group = frappe.db.get_value('Item', rows.item_code, 'item_group')
			rows.uom = frappe.db.get_value('Item', rows.item_code, 'stock_uom')
			#append for bom level 0
			data.append(rows)
		#2 BOM Level 1
		elif bom_level == '1':
			exploded_items = frappe.get_all(
				"BOM Item",
				{"parent": rows.bom},
				["item_code", "item_name", "sum(qty) as qty"],
				order_by = 'idx asc',
				group_by = 'item_code'
			)
			for rm in exploded_items:
				rm.warehouse = rows.warehouse
				rm.qty = rm.qty * rows.req_qty
				#temporary append to temp[]
				temp.append(rm)
		#3 BOM Level 2
		elif bom_level == '2':
			temp = get_exploded_items(rows.bom, temp, rows.warehouse, qty=rows.req_qty)

	if bom_level == '1':
		temp = group_by_item_code_and_sum_qty(temp)
		for item in temp:
			is_group = frappe.db.get_value("Warehouse",{"name": item.warehouse},["is_group"])
			if is_group == 1:
				group_warehouse_list = frappe.get_all("Warehouse",
					{"parent_warehouse": item.warehouse},
					["name"],
					pluck='name'
				)
				actual_qty = frappe.db.get_all(
					"Bin",
					{"item_code": item.item_code, "warehouse": ["in", group_warehouse_list]},
					["sum(actual_qty) as actual_qty"], group_by='item_code')
				if actual_qty:
					item.actual_qty = actual_qty[0].actual_qty
				else:
					item.actual_qty = 0
			elif is_group == 0:
				item.actual_qty = frappe.db.get_value("Bin",{"item_code": item.item_code, "warehouse": ["in",[item.warehouse]]},["actual_qty"]) or 0
			safety_stock = frappe.db.get_value('Item', item.item_code, 'safety_stock') or 0
			lead_time_days = frappe.db.get_value('Item', item.item_code, 'lead_time_days') or 0
			item.cal_rol = (lead_time_days + safety_stock) * (item.qty / 26)
			item.rol = frappe.db.get_value('Item Reorder', {'parent':item.item_code}, 'warehouse_reorder_level') or 0
			#primary_location_c is custom fiedl in item
			item.location = frappe.db.get_value('Item', item.item_code, 'primary_location_c')
			item.item_name = frappe.db.get_value('Item', item.item_code, 'item_name')
			item.item_group = frappe.db.get_value('Item', item.item_code, 'item_group')
			item.uom = frappe.db.get_value('Item', item.item_code, 'stock_uom')
			item.diff = item.actual_qty - item.qty
			#append for bom level 1
			data.append(item)
	#duplicate code as above
	elif bom_level == '2':
		temp = group_by_item_code_and_sum_qty(temp)
		for item in temp:
			is_group = frappe.db.get_value("Warehouse",{"name": item['warehouse']},["is_group"])
			if is_group == 1:
				group_warehouse_list = frappe.get_all("Warehouse",
					{"parent_warehouse": item['warehouse']},
					["name"],
					pluck='name'
				)
				actual_qty = frappe.db.get_all(
					"Bin",
					{"item_code": item['item_code'], "warehouse": ["in", group_warehouse_list]},
					["sum(actual_qty) as actual_qty"], group_by='item_code')
				if actual_qty:
					item['actual_qty'] = actual_qty[0].actual_qty
				else:
					item['actual_qty'] = 0
			elif is_group == 0:
				item['actual_qty'] = frappe.db.get_value("Bin",{"item_code": item['item_code'], "warehouse": ["in",[item['warehouse']]]},["actual_qty"]) or 0
			safety_stock = frappe.db.get_value('Item', item['item_code'], 'safety_stock') or 0
			lead_time_days = frappe.db.get_value('Item', item['item_code'], 'lead_time_days') or 0
			item['cal_rol'] = (lead_time_days + safety_stock) * (item['qty'] / 26)
			item['rol'] = frappe.db.get_value('Item Reorder', {'parent':item['item_code']}, 'warehouse_reorder_level') or 0
			#primary_location_c is custom fiedl in item
			item['location'] = frappe.db.get_value('Item', item['item_code'], 'primary_location_c')
			item['item_name'] = frappe.db.get_value('Item', item['item_code'], 'item_name')
			item['item_group'] = frappe.db.get_value('Item', item['item_code'], 'item_group')
			item['uom'] = frappe.db.get_value('Item', item['item_code'], 'stock_uom')
			item['diff'] = item['actual_qty'] - item['qty']
			#append for bom level 2
			data.append(item)

def group_by_item_code_and_sum_qty(item_list):
    item_dict = {}
    for item in item_list:
        key = (item['item_code'], item['warehouse'])
        if key in item_dict:
            item_dict[key]['qty'] += item['qty']
        else:
            item_dict[key] = item

    item_list = [item for item in item_dict.values()]
    item_list.sort(key=lambda x: x['item_code'])
    return item_list

def get_exploded_items(bom, temp, warehouse, qty):
	exploded_items = frappe.get_all(
		"BOM Item",
		filters={"parent": bom},
		fields=["bom_no", "qty", "item_code", "item_name"],
	)
	for item in exploded_items:
		temp.append(
			{
				"item_code": item.item_code,
				"item_name": item.item_name,
				"warehouse": warehouse,
				"qty": item.qty * qty
			}
		)
		if item.bom_no:
			get_exploded_items(item.bom_no, temp, warehouse, qty=qty)
	return temp

def get_columns():
	return [
		{"label": "Item Code","fieldtype": "Link","fieldname": "item_code","width": 150,"options": "Item"},
		{"label": "Item Name", "fieldtype": "Data", "fieldname": "item_name", "width": 200},
		{"label": "Item Group","fieldtype": "Link","fieldname": "item_group","width": 100,"options": "Item Group"},
		{"label": "UOM","fieldtype": "Link","fieldname": "uom","width": 50,"options": "UOM"},
		{"label": "Location", "fieldtype": "Data", "fieldname": "location", "width": 100},
		{"label": "Warehouse","fieldtype": "Link","fieldname": "warehouse","width": 150,"options": "Warehouse"},
		{"label": "Req Qty", "fieldtype": "Data", "fieldname": "qty", "width": 100},
		{"label": "In Stock Qty", "fieldtype": "Data", "fieldname": "actual_qty", "width": 100},
		{"label": "Difference", "fieldtype": "Data", "fieldname": "diff", "width": 100},
		{"label": "Re-order Level", "fieldtype": "Data", "fieldname": "rol", "width": 100},
		{"label": "Calculated ROL", "fieldtype": "Data", "fieldname": "cal_rol", "width": 100},
	]