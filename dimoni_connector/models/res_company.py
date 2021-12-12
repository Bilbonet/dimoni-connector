# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Company(models.Model):
    _inherit = 'res.company'

    dbconnection_id = fields.Many2one(string='Database Connection', 
        comodel_name='base.external.dbsource', ondelete='restrict')
    dimoni_company = fields.Many2one(string='Dimoni Company', 
        comodel_name='dimoni.company')
    dimoni_serie = fields.Many2one(string='Dimoni Sales Serie', 
        comodel_name='dimoni.serie')
    dimoni_docsale = fields.Many2one( string='Dimoni Sales OPA', 
        comodel_name='dimoni.document')

    @api.onchange('dbconnection_id')
    def _onchange_dbconnection(self):
        self.dimoni_company = False
        if self.dbconnection_id:
            self.env['dimoni.company'].import_company(self)

    @api.onchange('dimoni_company')
    def _onchange_dimoni_company(self):
        self.dimoni_serie = False
        if self.dimoni_company:
            self.env['dimoni.serie'].import_serie(self)

    @api.onchange('dimoni_serie')
    def _onchange_dimoni_serie(self):
        self.dimoni_docsale = False
        if self.dimoni_serie:
            self.env['dimoni.document'].import_tipodoc(self)
