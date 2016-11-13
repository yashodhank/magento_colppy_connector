# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from meli_connector.after_install import create_weight_uom

def execute():
	create_weight_uom()
