# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Company(models.Model):
    _inherit = 'res.company'

    dimoni_serie_wh = fields.Many2one('dimoni.serie',
                                string='Dimoni Serie Warehouse')
    dimoni_docwh = fields.Many2one('dimoni.document',
                                string='Dimoni Warehouse OPA')
    dimoni_originwh = fields.Many2one('dimoni.warehouse',
                                string="Dimoni Origin Warehouse")

    @api.onchange('dimoni_company')
    def _onchange_dimoni_company_wh(self):
        self.dimoni_serie_wh = False

    @api.onchange('dimoni_serie_wh')
    def _onchange_dimoni_serie_wh(self):
        self.dimoni_docwh = False

    @api.onchange('dimoni_docwh')
    def _onchange_dimoni_docwh(self):
        self.dimoni_originwh = False
        if self.dimoni_serie_wh:
            self.env['dimoni.warehouse'].import_warehouse(self)
