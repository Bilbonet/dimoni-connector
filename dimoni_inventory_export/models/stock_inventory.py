# Copyright 2021 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, _
from odoo.exceptions import UserError
import base64


class Inventory(models.Model):
    _inherit = "stock.inventory"

    dimoni_wh = fields.Many2one(comodel_name='dimoni.warehouse', string='Dimoni Warehouse')
    dimoni_inv_attachment = fields.Many2one('ir.attachment',
        string='Inventory File', readonly=True, copy=False)
    dimoni_inv_filename = fields.Char(related='dimoni_inv_attachment.name',
        string='File Name')
    dimoni_inv_file = fields.Binary(related='dimoni_inv_attachment.datas',
        string='File Content')

    def generate_inventory_file(self):
        """Returns (inventory file as string, filename)"""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_(
                "There are no lines for this inventory yet. Please add any first."))

        date_str = self.date.strftime('%d-%m-%Y')
        filename = ('INV%s_%s.txt') % (self.id,date_str)
        first_line = ('INV;%s;%s;%s\n') % (date_str, self.name, self.id,)

        file_str = first_line
        cons_line = "LI;" + self.dimoni_wh.cod_wh
        for line in self.line_ids:
            file_str += ('%s;%s;;%s;%s;0;0;\n') % (
                        cons_line, line.product_id.default_code, int(line.product_qty), int(line.product_qty))

        inventory_file_str = file_str.encode('utf-8')
        return inventory_file_str, filename

    def action_generate_file(self):
        self.ensure_one()
        inventory_file_str, filename = self.generate_inventory_file()

        if inventory_file_str and filename:
            vals = {}
            vals.update({
                'name': filename,
                'datas': base64.b64encode(inventory_file_str),
                # 'datas_fname': filename,
            })

            if not self. dimoni_inv_attachment:
                vals.update ({
                    'res_model': 'stock.inventory',
                    'res_id': self.id,
                    'description': _('Dimoni inventory import file compatible'),
                })
                attachment = self.env['ir.attachment'].create(vals)
                self.update({'dimoni_inv_attachment': attachment.id})
            else:
                self.dimoni_inv_attachment.update(vals)

    def action_cancel_draft(self):
        super(Inventory, self).action_cancel_draft()
        if self.dimoni_inv_attachment:
            self.dimoni_inv_attachment.unlink()
