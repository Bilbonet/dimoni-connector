# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Connect with ERP Dimoni",
    "version": "11.0.1.0.0",
    "author": "Jesus Ramiro",
    "license": "AGPL-3",
    "category": "Connector",
    'website': 'https://github.com/Bilbonet/dimoni-connector',
    "depends": [
        'sale',
        'base_external_dbsource_odbc',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/sale_view.xml',
        'views/res_company_view.xml',
    ],
    'installable': True,
}