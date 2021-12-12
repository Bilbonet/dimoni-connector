# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    dimoni_serie_wh = fields.Many2one(string='Dimoni Warehouse Serie',
        comodel_name='dimoni.serie')
    dimoni_docwh = fields.Many2one(string='Dimoni Warehouse OPA',
        comodel_name='dimoni.document')

    @api.onchange('dimoni_company')
    def _onchange_dimoni_company_wh(self):
        self.dimoni_serie_wh = False

    @api.onchange('dimoni_serie_wh')
    def _onchange_dimoni_serie_wh(self):
        self.dimoni_docwh = False

    @api.onchange('dimoni_docwh')
    def _onchange_dimoni_docwh(self):
        if self.dimoni_serie_wh:
            self.env['dimoni.warehouse'].import_warehouse(self)
