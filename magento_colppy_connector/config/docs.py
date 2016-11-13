source_link = "https://github.com/binardev/meli_connector"
docs_base_url = "https://github.com/binardev/meli_connector"
headline = "BinarERP MercadoLibre Connector"
sub_heading = "Sync transactions between MercadoLibre and BinarERP"
long_description = """BinarERP MercadoLibre Connector will sync data between your MercadoLibre and BinarERP accounts.
<br>
<ol>
	<li> It will sync Products and Cutomers between MercadoLibre and BinarERP</li>
	<li> It will push Orders from MercadoLibre to BinarERP
		<ul>
			<li>
				If the Order has been paid for in MercadoLibre, it will create a Sales Invoice in BinarERP and record the corresponding Payment Entry
			</li>
			<li>
				If the Order has been fulfilled in MercadoLibre, it will create a draft Delivery Note in BinarERP
			</li>
		</ul>
	</li>
</ol>"""
docs_version = "1.0.0"

def get_context(context):
	context.title = "BinarERP MercadoLibre Connector"
