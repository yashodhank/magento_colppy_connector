# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe
from frappe.utils.fixtures import sync_fixtures

def execute():
	sync_fixtures("meli_connector")
	frappe.reload_doctype("Item")
	frappe.reload_doctype("Customer")
	frappe.reload_doctype("Sales Order")
	frappe.reload_doctype("Delivery Note")
	frappe.reload_doctype("Sales Invoice")

	for doctype, column in {"Customer": "meli_customer_id",
		"Item": "meli_product_id",
		"Sales Order": "meli_order_id",
		"Delivery Note": "meli_order_id",
		"Sales Invoice": "meli_order_id"}.items():

		if "meli_id" in frappe.db.get_table_columns(doctype):
			frappe.db.sql("update `tab%s` set %s=meli_id" % (doctype, column))
