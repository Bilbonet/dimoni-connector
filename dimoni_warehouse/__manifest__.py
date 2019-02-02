# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Warehouse operations from Odoo sales orders",
    "version": "11.0.1.0.0",
    "author": "Jesus Ramiro",
    "license": "AGPL-3",
    "category": "Connector",
    'website': 'https://github.com/Bilbonet/dimoni-connector',
    "depends": [
        'dimoni_connector',
        'stock',
    ],
    "data": [
        'views/res_company_view.xml',
    ],
    'installable': True,
}