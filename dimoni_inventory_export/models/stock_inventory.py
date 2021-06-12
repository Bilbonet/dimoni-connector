# Copyright 2021 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _


class Inventory(models.Model):
    _inherit = "stock.inventory"

    def action_generate_file(self):
        pass