// Copyright (c) 2023, PSPL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["PSPL BOM Stock Report"] = {
	"filters": [
		{
			fieldname: "rol_bom",
			label: __("ROL BOM"),
			fieldtype: "Link",
			options: "ROL BOM",
			reqd: 1
		},
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);	
		if (column.id == "item_code") {
			if (data["diff"] < 0) {
				value = "<span style='color:red;'>" + data['item_code'] + "</span>";
			} else {
				value = "<span style='color:green;'>" + data['item_code'] + "</span>";
			} 
		}
		return value
	}
};
