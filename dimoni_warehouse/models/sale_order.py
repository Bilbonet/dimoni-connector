# Copyright 2019 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dimoni_wh = fields.Many2one('dimoni.warehouse',
                                 string='Dimoni Warehouse')

    def dimoni_create_warehouse(self):
        self.ensure_one()
        self.env['dimoni.warehouse'].recurring_create_warehouse_dimoni(self)

        return True

    def dimoni_delete_warehouse(self):
        self.ensure_one()
        self.env['dimoni.warehouse'].dimoni_delete_warehouse(self.dimoni_sale)

        return True
