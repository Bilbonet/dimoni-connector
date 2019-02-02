# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models



class DimoniWarehouse(models.Model):
    _name = "dimoni.warehouse"
    _description = "Dimoni Warehouses"
    _order = 'cod_wh'

    grp_id = fields.Many2one('dimoni.company',
                             string='Dimoni Company Code Identifier')
    cod_wh = fields.Char(string='Dimoni Warehouse Code', size=3)
    name = fields.Char(string='Dimoni Warehouse Name', size=30)

    def import_warehouse(self, company):
        # Obtain Dimoni Warehouses
        params = [company.dimoni_company.grp_id]
        db_dimoni = company.dbconnection_id

        # Fields Many2one needs XML-ID value for the relation with the model
        sql = "SELECT Codigo as 'cod_wh', " \
              "'dimoni_company_'+GRP_ID as 'grp_id/id', " \
              "Descrip as 'name' " \
              "FROM dbo.PALMA " \
              "WHERE GRP_ID = ?"
        res = db_dimoni.execute(sql, params, metadata=True)

        # Prepare columns
        cidx = [i for i, x in enumerate(res['cols'])]
        cols = [x for i, x in enumerate(res['cols'])] + ['id']

        model_name = self._name
        model_obj = self.env.get(model_name)

        # Import each row
        for row in res['rows']:
            # Build data row;
            data = list()
            for i in cidx:
                v = row[i]
                if isinstance(v, str):
                    v = v.strip()
                data.append(v)

            data.append(self.env['dimoni.company']._build_xmlid(
                                                row[0].strip(), self._name))

            # Import row
            self.env['dimoni.company']._import_data(cols, data, model_obj)
        return True
