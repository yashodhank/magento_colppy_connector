# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from .exceptions import MeliError
from erpnext.stock.utils import get_bin
#from .sync_orders import sync_orders
#from .sync_customers import sync_customers
from .sync_products import sync_products, update_item_stock_qty
from .utils import disable_meli_sync_on_exception, make_meli_log
from frappe.utils.background_jobs import enqueue

@frappe.whitelist()
def sync_meli():
	"Enqueue longjob for syncing MercadoLibre"
	enqueue("meli_connector.api.sync_meli_resources", queue='long')
	frappe.msgprint(_("Queued for syncing. It may take a few minutes to an hour if this is your first sync."))

@frappe.whitelist()
def sync_meli_resources():
	meli_settings = frappe.get_doc("Meli Settings")

	make_meli_log(title="Sync Job Queued", status="Queued", method=frappe.local.form_dict.cmd, message="Sync Job Queued")

	if meli_settings.enable_meli:
		try :
			# first_time = frappe.utils.now()
			# frappe.db.set_value("Meli Settings", None, "last_sync_datetime", first_time)
			validate_meli_settings(meli_settings)
			frappe.local.form_dict.count_dict = {}
			meli_item_list = []
			sync_products(meli_settings.price_list, meli_settings.warehouse, meli_item_list)
			#sync_customers()
			#sync_orders()
			#sync_listings()
			update_item_stock_qty(meli_item_list)
			now_time = frappe.utils.now()
			frappe.db.set_value("Meli Settings", None, "last_sync_datetime", now_time)

			make_meli_log(title="Sync Completed", status="Success", method=frappe.local.form_dict.cmd,
				message= "Updated {products} item(s)".format(**frappe.local.form_dict.count_dict))
				# message= "Updated {customers} customer(s), {products} item(s), {orders} order(s)".format(**frappe.local.form_dict.count_dict))

		except Exception, e:
			pass
			# make_meli_log(title=e.title, status="Error", method="sync_meli_resources", message=frappe.get_traceback(),
			# 	request_data=e.message, exception=True)
			# pass
			# if e.args[0] and hasattr(e.args[0], "startswith") and e.args[0].startswith("402"):
			# 	make_meli_log(title="Meli has suspended your account", status="Error",
			# 		method="sync_shopify_resources", message=_("""Shopify has suspended your account till
			# 		you complete the payment. We have disabled ERPNext Shopify Sync. Please enable it once
			# 		your complete the payment at Shopify."""), exception=True)
			#
			# 	disable_meli_sync_on_exception()
			#
			# else:
			# 	make_meli_log(title="sync has terminated", status="Error", method="sync_meli_resources",
			# 		message=frappe.get_traceback(), exception=True)

	elif frappe.local.form_dict.cmd == "meli_connector.api.sync_meli":
		make_meli_log(
			title="MercadoLibre connector is disabled",
			status="Error",
			method="sync_meli_resources",
			message=_("""MercadoLibre connector is not enabled. Click on 'Connect to MercadoLibre' to connect BinarERP and your MercadoLibre store."""),
			exception=True)

def validate_meli_settings(meli_settings):
	"""
		This will validate mandatory fields and access token or app credentials
		by calling validate() of MercadoLibre settings.
	"""
	try:
		meli_settings.save()
	except MeliError:
		disable_meli_sync_on_exception()

@frappe.whitelist()
def get_log_status():
	log = frappe.db.sql("""select name, status from `tabMeli Log`
		order by modified desc limit 1""", as_dict=1)
	if log:
		if log[0].status=="Queued":
			message = _("Last sync request is queued")
			alert_class = "alert-warning"
		elif log[0].status=="Error":
			message = _("Last sync request was failed, check <a href='../desk#Form/Meli Log/{0}'> here</a>"
				.format(log[0].name))
			alert_class = "alert-danger"
		else:
			message = _("Last sync request was successful")
			alert_class = "alert-success"

		return {
			"text": message,
			"alert_class": alert_class
		}

@frappe.whitelist()
def add_to_bin():
	get_bin("MLA636633322", "Productos terminados - I")
