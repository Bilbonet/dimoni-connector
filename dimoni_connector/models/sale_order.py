# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dimoni_sale = fields.Many2one('dimoni.sale',
                                 string='Dimoni Sale')

    def dimoni_create_sale(self):
        self.ensure_one()
        self.env['dimoni.sale'].recurring_create_sale_dimoni(self)

        return True

    def dimoni_delete_sale(self):
        self.ensure_one()
        self.env['dimoni.sale'].dimoni_delete_sale(self.dimoni_sale)

        return True