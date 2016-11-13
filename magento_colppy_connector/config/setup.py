from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Integrations"),
			"icon": "icon-star",
			"items": [
				{
					"type": "doctype",
					"name": "Magento Colppy Settings",
					"description": _("Connect Magento with Colppy"),
					"hide_count": True
				}
			]
		}
	]
