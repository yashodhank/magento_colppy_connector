# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from .exceptions import MeliSetupError

def disable_meli_sync_for_item(item, rollback=False):
	"""Disable Item if not exist on MercadoLibre"""
	if rollback:
		frappe.db.rollback()

	item.sync_with_meli= 0
	item.sync_qty_with_meli = 0
	item.save(ignore_permissions=True)
	frappe.db.commit()

def disable_meli_sync_on_exception():
	frappe.db.rollback()
	frappe.db.set_value("Meli Settings", None, "enable_meli", 0)
	frappe.db.commit()

def is_meli_enabled():
	meli_settings = frappe.get_doc("Meli Settings")
	if not meli_settings.enable_meli:
		return False
	try:
		meli_settings.validate()
	except MeliSetupError:
		return False

	return True

def make_meli_log(title="Sync Log", status="Queued", method="sync_meli", message=None, exception=False,
name=None, request_data={}):
	if not name:
		name = frappe.db.get_value("Meli Log", {"status": "Queued"})

		if name:
			""" if name not provided by log calling method then fetch existing queued state log"""
			log = frappe.get_doc("Meli Log", name)

		else:
			""" if queued job is not found create a new one."""
			log = frappe.get_doc({"doctype":"Meli Log"}).insert(ignore_permissions=True)

		if exception:
			frappe.db.rollback()
			log = frappe.get_doc({"doctype":"Meli Log"}).insert(ignore_permissions=True)

		log.message = message if message else frappe.get_traceback()
		log.title = title[0:140]
		log.method = method
		log.status = status
		log.request_data= json.dumps(request_data)

		log.save(ignore_permissions=True)
		frappe.db.commit()
