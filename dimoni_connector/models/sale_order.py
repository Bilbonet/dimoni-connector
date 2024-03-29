# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dimoni_sale = fields.Many2one(string='Dimoni Sale', comodel_name='dimoni.sale')

    def dimoni_create_sale(self):
        self.ensure_one()
        self.env['dimoni.sale'].recurring_create_sale_dimoni(self)

        return True

    def dimoni_delete_sale(self):
        self.ensure_one()
        res = self.env['dimoni.sale'].dimoni_delete_sale(self.dimoni_sale)

        if res:
            # Change Sale Order state to sale
            self.update({'state': 'sale'})
            return True
    