# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from meli_connector.meli_requests import get_meli_items
from frappe.utils import cint
from frappe import _
from meli_connector.exceptions import MeliError
import requests.exceptions
from frappe.utils.fixtures import sync_fixtures

def execute():
	sync_fixtures("meli_connector")
	frappe.reload_doctype("Item")

	meli_settings = frappe.get_doc("Meli Settings")
	if not meli_settings.enable_meli:
		return

	try:
		meli_items = get_item_list()
	except MeliError:
		print "Could not run MercadoLibre patch 'set_variant_id' for site: {0}".format(frappe.local.site)
		return

	if meli_settings.meli_url and meli_items:
		for item in frappe.db.sql("""select name, item_code, meli_id, has_variants, variant_of from tabItem
			where sync_with_meli=1 and meli_id is not null""", as_dict=1):

			if item.get("variant_of"):
				frappe.db.sql(""" update tabItem set meli_variant_id=meli_id
					where name = %s """, item.get("name"))

			elif not item.get("has_variants"):
				product = filter(lambda meli_item: meli_item['id'] == cint(item.get("meli_id")), meli_items)

				if product:
					frappe.db.sql(""" update tabItem set meli_variant_id=%s
						where name = %s """, (product[0]["variants"][0]["id"], item.get("name")))

def get_item_list():
	try:
		return get_meli_items()
	except (requests.exceptions.HTTPError, MeliError) as e:
		frappe.throw(_("Something went wrong: {0}").format(frappe.get_traceback()), MeliError)
