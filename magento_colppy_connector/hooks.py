# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "magento_colppy_connector"
app_title = "Conector Magento-Colppy"
app_publisher = "Binar"
app_description = "Conector de Magento para Colppy"
app_icon = "octicon octicon-file-directory"
app_color = "yellow"
app_email = "info@binar.io"
app_license = "MIT"

# fixtures = ["Custom Field"]
# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/meli_connector/css/meli_connector.css"
# app_include_js = "/assets/meli_connector/js/meli_connector.js"

# include js, css files in header of web template
# web_include_css = "/assets/meli_connector/css/meli_connector.css"
# web_include_js = "/assets/meli_connector/js/meli_connector.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "meli_connector.install.before_install"
after_install = "meli_connector.after_install.create_weight_uom"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "meli_connector.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Bin": {
		"on_update": "meli_connector.sync_products.trigger_update_item_stock"
	},
	"Item": {
		"after_insert": "meli_connector.sync_products.predict_category",
		"before_save": "meli_connector.meli_validations.meli_validations"
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"meli_connector.api.sync_meli"
	]
}

# Testing
# -------

# before_tests = "meli_connector.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "meli_connector.event.get_events"
# }
