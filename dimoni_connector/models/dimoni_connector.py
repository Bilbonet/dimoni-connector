# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import sys
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DimoniCompany(models.Model):
    _name = "dimoni.company"
    _description = "Dimoni Companies"
    _order = 'grp_id'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one('res.company', string='Company',
                default=_get_default_company_id, required=True)
    dbconnection_id = fields.Integer(string='Database connection', required=True)
    grp_id = fields.Char(string='Dimoni Company Code Identifier', size=12)
    cod_emp = fields.Char(string='Dimoni Company Code', size=6)
    name = fields.Char(string='Dimoni Company Name', size=40)

    # Prepare the internal XML-ID in column "id"
    def _build_xmlid(row_id, model_name):
        # Replace dots "." by "-" because in XML-ID dots are not allowed
        row_id = row_id.replace('.', '-')
        xml_prefix = model_name.replace('.', '_')
        return xml_prefix + '_' + row_id

    def _import_data(self, flds, data, model_obj):
        cols = list(flds)  # copy to avoid side effects
        errmsg = str()

        importmsg = dict()
        try:
            importmsg = model_obj.load(cols, [data])
        except:
            errmsg = str(sys.exc_info()[1])
        if errmsg:
            # Fail
            raise ValidationError(errmsg)
            return False

        # Check the import model returned message
        if not importmsg['ids']:
            message = [i['message'] for i in importmsg['messages']
                       if 'message' in i]
            raise ValidationError(message)
            return False

        return True

    def import_company(self, company):
        # Obtain Dimoni companies
        params = []
        db_dimoni = company.dbconnection_id

        sql = "SELECT " \
              "GRP_ID as 'grp_id', " \
              "CodEmpre as 'cod_emp', " \
              "Nombre as 'name' FROM dbo.SEMPE"
        res = db_dimoni.execute(sql, params, metadata=True)

        # Prepare columns
        cidx = [i for i, x in enumerate(res['cols'])]
        cols = [x for i, x in enumerate(res['cols'])] + ['id'] + ['dbconnection_id']

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
            data.append(DimoniCompany._build_xmlid(row[0].strip(), self._name))
            data.append(company.dbconnection_id.id)

            # Import row
            self._import_data(cols, data, model_obj)

class DimoniSeries(models.Model):
    _name = "dimoni.serie"
    _description = "Dimoni Company Series"
    _order = 'cod_serie'

    grp_id = fields.Many2one('dimoni.company',
                             string='Dimoni Company Code Identifier')
    cod_serie = fields.Char(string='Dimoni Serie Code', size=3)
    name = fields.Char(string='Dimoni Serie Name', size=30)
    almacen = fields.Char(string='Dimoni Serie Almacén', size=2)

    def import_serie(self, company):
        # Obtain Dimoni Series
        params = [company.dimoni_company.grp_id, 1]
        db_dimoni = company.dbconnection_id

        # Fields Many2one needs XML-ID value for the relation with the model
        sql = "SELECT Serie as 'cod_serie', " \
              "'dimoni_company_'+GRP_ID as 'grp_id/id', " \
              "Descripc as 'name', " \
              "Almacen as 'almacen' " \
              "FROM dbo.PSERI " \
              "WHERE GRP_ID = ? and Activa = ?"
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
            data.append(DimoniCompany._build_xmlid(row[0].strip(), self._name))

            # Import row
            DimoniCompany._import_data(self, cols, data, model_obj)

        return True

class DimoniDocument(models.Model):
    _name = "dimoni.document"
    _description = "Dimoni Document Types"
    _order = 'ambito'

    grp_id = fields.Many2one('dimoni.company',
                             string='Dimoni Company Code Identifier')
    cod_serie = fields.Many2one('dimoni.serie', string='Dimoni Serie Code')
    tipo_doc = fields.Char(string='Dimoni Tipo Doc', size=2)
    name = fields.Char(string='Dimoni Document Name', size=30)
    ambito = fields.Integer(string='Sale, Purchase, Warehouse, TPV', size=1)

    def import_tipodoc(self, company):
        # Obtain Dimoni Document types
        params = [company.dimoni_company.grp_id,
                  company.dimoni_serie.cod_serie, 2]
        db_dimoni = company.dbconnection_id

        # Fields Many2one needs XML-ID value for the relation with the model
        sql = "SELECT t.TipoDoc as 'tipo_doc', " \
              "'dimoni_company_'+s.GRP_ID as 'grp_id/id', " \
              "'dimoni_serie_'+s.Serie as 'cod_serie/id', " \
              "t.Descripc as 'name', " \
              "Ambito as 'ambito' " \
              "FROM dbo.PSERI AS s INNER JOIN " \
              "dbo.PSERD AS p ON s.GRP_ID = p.GRP_ID AND s.Serie = p.Serie INNER JOIN " \
              "dbo.PTDOC AS t ON s.GRP_ID = t.GRP_ID AND p.TipoDoc = t.TipoDoc " \
              "WHERE s.GRP_ID = ? and s.Serie = ? and p.Activa = ?"
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
            data.append(DimoniCompany._build_xmlid(row[0].strip(), self._name))

            # Import row
            DimoniCompany._import_data(self, cols, data, model_obj)

        return True

class DimoniSale(models.Model):
    _name = "dimoni.sale"
    _description = "Dimoni Sales"

    sale_order = fields.Many2one('sale.order',
                                 string='Sale Order')
    grp_id = fields.Char(string='Dimoni Company Code Identifier', size=12)
    cod_emp = fields.Char(string='Dimoni Company Code', size=6)
    cod_serie = fields.Char(string='Dimoni Serie Code', size=3)
    tipo_doc = fields.Char(string='Dimoni Tipo Doc', size=2)
    document = fields.Integer(string='Dimoni Docu Number')
    refnum = fields.Char(string='Dimoni Docu Reference', size=15)

    def _asign_domment_number(self, db_dimoni, params):
        # Obtain the last number of the document
        sql = "Select contador " \
              "FROM PSERD " \
              "WHERE (GRP_ID= ?) AND(Serie= ?) AND (TipoDoc= ?)"
        res = db_dimoni.execute(sql, params)
        number = res[0][0]

        # Increase by one the document counter
        sql = "UPDATE PSERD " \
             "SET Contador = Contador + 1 " \
             "FROM PSERD " \
             "WHERE (GRP_ID= ?) AND (Serie= ?) AND (TipoDoc= ?)"
        db_dimoni.update(sql, params)

        return number

    @api.multi
    def recurring_create_sale_dimoni(self, sale_order):
        db_dimoni = sale_order.company_id.dbconnection_id
        grp_id = sale_order.company_id.dimoni_company.grp_id
        serie = sale_order.company_id.dimoni_serie.cod_serie
        tipo_doc = sale_order.company_id. dimoni_docsale.tipo_doc
        params = [grp_id, serie, tipo_doc]

        document_number = self._asign_domment_number(db_dimoni, params)
        raise ValidationError(document_number)

        return True

        # if sale_order.ids:
        #     raise ValidationError(
        #         'Codigo Empresa: %s\n'
        #         'Serie: %s\n'
        #         'Tipo Doc.: %s'
        #         % (grp_id, serie, tipo_doc)
        #     )
