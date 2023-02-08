// Copyright (c) 2023, PSPL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["PSPL BOM Explorer"] = {
	"filters": [
		{
			fieldname: "bom_record",
			label: __("BOM Record"),
			fieldtype: "Link",
			options: "BOM Record",
			reqd: 1
		},
	]
};
