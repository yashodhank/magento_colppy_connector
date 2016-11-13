# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from meli_connector.utils import is_meli_enabled
from frappe.utils.fixtures import sync_fixtures

def execute():
	if not is_meli_enabled():
		return

	sync_fixtures('meli_connector')

	fieldnames = frappe.db.sql("select fieldname from `tabCustom Field`", as_dict=1)

	if not any(field['fieldname'] == 'meli_supplier_id' for field in fieldnames):
		return

	frappe.db.sql("""update tabSupplier set meli_supplier_id=supplier_name """)
	frappe.db.commit()
