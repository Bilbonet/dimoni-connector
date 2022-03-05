# Copyright 2021 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Dimoni Inventory Export",
    "version": "13.0.1.0.0",
    "author": "Jesus Ramiro",
    "license": "AGPL-3",
    "category": "Inventory",
    'website': 'https://github.com/Bilbonet/dimoni-connector',
    "depends": [
        'base',
        'stock',
        'dimoni_warehouse',
    ],
    "data": [
        'views/stock_inventory_views.xml',
    ],
    'installable': True,
}