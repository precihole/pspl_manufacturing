# Copyright (c) 2023, PSPL and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	get_data(filters, data)
	return columns, data

def get_data(filters, data):
	get_all_rol_bom_items(filters.rol_bom, data)

def get_all_rol_bom_items(rol_bom, data):
	temp = []
	#get bom level of current filter document
	bom_level = frappe.db.get_value('ROL BOM', rol_bom, 'bom_level')

	#all rol bom items of current filter document
	rol_bom_items = frappe.get_all(
		"ROL BOM Item",
		{"parent": rol_bom},
		["item_code", "item_name","bom", "req_qty","warehouse"],
		order_by = 'idx asc'
	)
	for rows in rol_bom_items:
		#1 if bom level 0 then get the current stock from bin
		if bom_level == 0:
			is_group = frappe.db.get_value("Warehouse",{"name": rows.warehouse},["is_group"])
			if is_group == 1:
				group_warehouse_list = frappe.get_all("Warehouse",
					{"parent_warehouse": rows.warehouse},
					["name"],
					pluck='name'
				)
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
			#final append to report of bom level 0
			safety_stock = frappe.db.get_value('Item', rows.item_code, 'safety_stock') or 0
			lead_time_days = frappe.db.get_value('Item', rows.item_code, 'lead_time_days') or 0
			rows.cal_rol = (lead_time_days + safety_stock) * (rows.qty / 26)
			rows.rol = frappe.db.get_value('Item Reorder', {'parent':rows.item_code}, 'warehouse_reorder_level') or 0
			rows.location = frappe.db.get_value('Item', rows.item_code, 'primary_location_c')
			rows.item_name = frappe.db.get_value('Item', rows.item_code, 'item_name')
			rows.item_name = frappe.db.get_value('Item', rows.item_code, 'item_name')
			rows.item_group = frappe.db.get_value('Item', rows.item_code, 'item_group')
			rows.uom = frappe.db.get_value('Item', rows.item_code, 'stock_uom')
			data.append(rows)
		#2 if bom level 1 then get first level items and 
		# get the current stock of those items from bin
		elif bom_level == 1:
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
		elif bom_level == 2:
			#get exploded items
			temp = get_exploded_items(rows.bom, temp, rows.warehouse, qty=rows.req_qty)

	#run if all item push in temp from bom for bom level 1 and 2
	if bom_level == 1:
		#get unique item code by passing temp[]
		temp = group_by_item_code_and_sum_qty(temp)
		for item in temp:
			#now get warehouse qty from bin
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
			#final append for bom level 1
			safety_stock = frappe.db.get_value('Item', item.item_code, 'safety_stock') or 0
			lead_time_days = frappe.db.get_value('Item', item.item_code, 'lead_time_days') or 0
			item.cal_rol = (lead_time_days + safety_stock) * (item.qty / 26)
			item.rol = frappe.db.get_value('Item Reorder', {'parent':item.item_code}, 'warehouse_reorder_level') or 0
			item.location = frappe.db.get_value('Item', item.item_code, 'primary_location_c')
			item.item_name = frappe.db.get_value('Item', item.item_code, 'item_name')
			item.item_group = frappe.db.get_value('Item', item.item_code, 'item_group')
			item.uom = frappe.db.get_value('Item', item.item_code, 'stock_uom')
			item.diff = item.actual_qty - item.qty
			data.append(item)
	#writing this code again because we are getting 
	# result in dict than the syntax is change
	elif bom_level == 2:
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
			#final append for bom level 2
			safety_stock = frappe.db.get_value('Item', item['item_code'], 'safety_stock') or 0
			lead_time_days = frappe.db.get_value('Item', item['item_code'], 'lead_time_days') or 0
			item['cal_rol'] = (lead_time_days + safety_stock) * (item['qty'] / 26)
			item['rol'] = frappe.db.get_value('Item Reorder', {'parent':item['item_code']}, 'warehouse_reorder_level') or 0
			item['location'] = frappe.db.get_value('Item', item['item_code'], 'primary_location_c')
			item['item_name'] = frappe.db.get_value('Item', item['item_code'], 'item_name')
			item['item_group'] = frappe.db.get_value('Item', item['item_code'], 'item_group')
			item['uom'] = frappe.db.get_value('Item', item['item_code'], 'stock_uom')
			item['diff'] = item['actual_qty'] - item['qty']
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

def set_cell_color(row, color, index):
    row[index].style.background_color = color


def get_columns():
	return [
		{"label": "Item Code","fieldtype": "Link","fieldname": "item_code","width": 150,"options": "Item"},
		{"label": "Item Name", "fieldtype": "Data", "fieldname": "item_name", "width": 200},
		{"label": "Item Group","fieldtype": "Link","fieldname": "item_group","width": 100,"options": "Item Group"},
		{"label": "UOM","fieldtype": "Link","fieldname": "uom","width": 50,"options": "UOM"},
		{"label": "Location", "fieldtype": "Data", "fieldname": "location", "width": 100},
		#{"label": "BOM","fieldtype": "Link","fieldname": "bom","width": 300,"options": "BOM"},
		{"label": "Warehouse","fieldtype": "Link","fieldname": "warehouse","width": 150,"options": "Warehouse"},
		# {"label": "BOM", "fieldtype": "Link", "fieldname": "bom_no", "width": 150, "options": "BOM"},
		{"label": "Req Qty", "fieldtype": "Data", "fieldname": "qty", "width": 100},
		{"label": "In Stock Qty", "fieldtype": "Data", "fieldname": "actual_qty", "width": 100},
		# {"label": "BOM Level", "fieldtype": "Int", "fieldname": "bom_level", "width": 100},
		# {"label": "Standard Description", "fieldtype": "data", "fieldname": "description", "width": 150},
		{"label": "Difference", "fieldtype": "Data", "fieldname": "diff", "width": 100},
		{"label": "Re-order Level", "fieldtype": "Data", "fieldname": "rol", "width": 100},
		{"label": "Calculated ROL", "fieldtype": "Data", "fieldname": "cal_rol", "width": 100},
	]