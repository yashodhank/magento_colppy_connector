# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from meli_connector.meli_requests import get_meli_items
from meli_connector.sync_products import get_supplier
from meli_connector.utils import is_meli_enabled
from frappe.utils.fixtures import sync_fixtures

def execute():
	if not is_meli_enabled():
		return

	sync_fixtures('meli_connector')

	for index, meli_item in enumerate(get_meli_items(ignore_filter_conditions=True)):
		name = frappe.db.get_value("Item", {"meli_product_id": meli_item.get("id")}, "name")
		supplier = get_supplier(meli_item)

		if name and supplier:
			frappe.db.set_value("Item", name, "default_supplier", supplier, update_modified=False)

		if (index+1) % 100 == 0:
			frappe.db.commit()
