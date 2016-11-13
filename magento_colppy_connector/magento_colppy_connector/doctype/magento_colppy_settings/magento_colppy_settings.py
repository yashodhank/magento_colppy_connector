# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import requests.exceptions
from frappe.model.document import Document
from magento_colppy_connector.magento_colppy_requests import get_request
from magento_colppy_connector.exceptions import MeliSetupError

class MagentoColppySettings(Document):
	def validate(self):
		if self.enable_magento == 1:
			self.validate_access_credentials()
			self.validate_access()

	def validate_access_credentials(self):
		if not (self.access_token and self.refresh_token):
			frappe.msgprint(_("Missing value for Access Token"), raise_exception=MeliSetupError)

	def validate_access(self):
		try:
			get_request("/users/me")

		except requests.exceptions.HTTPError:
			# disable MercadoLibre!
			frappe.db.rollback()
			self.set("enable_magento", 0)
			frappe.db.commit()

			frappe.throw(_("""Invalid access token"""), MeliSetupError)


@frappe.whitelist()
def get_series():
		return {
			"sales_order_series" : frappe.get_meta("Sales Order").get_options("naming_series") or "PD-Meli-",
			"sales_invoice_series" : frappe.get_meta("Sales Invoice").get_options("naming_series")  or "FC-Meli-",
			"delivery_note_series" : frappe.get_meta("Delivery Note").get_options("naming_series")  or "RM-Meli-"
		}
