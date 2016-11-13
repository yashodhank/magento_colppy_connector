from __future__ import unicode_literals
import frappe

class MeliError(frappe.ValidationError): pass
class MeliSetupError(frappe.ValidationError): pass
