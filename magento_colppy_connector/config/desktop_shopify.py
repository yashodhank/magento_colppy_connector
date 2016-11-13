from frappe import _

def get_data():
    return {
        "Shopify Sync": {
            "color": "#f1c40f",
            "icon": "octicon octicon-link",
            "label": _("Magento-Colppy Sync"),
            "link": "Form/Magento Colppy Settings",
            "doctype": "Magento Colppy Settings",
            "type": "list"
        },
    }
