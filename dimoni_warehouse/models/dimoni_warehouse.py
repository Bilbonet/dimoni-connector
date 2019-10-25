# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


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

    def _create_warehouse_document_header(self, document, sale_order):
        db_dimoni = document.company_id.dbconnection_id
        data = [
            document.grp_id, document.tipo_doc,
            document.company_id.dimoni_serie.almacen,
            document.ejercic, document.cod_serie, document.document,
            datetime.strptime(str(sale_order.confirmation_date),
                              "%Y-%m-%d %H:%M:%S"),
            document.signo, document.cod_serie, document.refnum,
            datetime.strptime(str(sale_order.confirmation_date),
                              "%Y-%m-%d %H:%M:%S"),
            sale_order.name,
        ]

        sql = """INSERT INTO PIACA 
                (GRP_ID,TipoDoc,
                Cuenta,
                Ejercic,Serie,Document,
                Fecha,
                Signo,RefSerie,RefNum,
                Moneda,Cambio,Clave,
                Limite,
                Proces,Historic,Export,Actualiz,Eliminad,MonDoc,Contabil,
                Origen,Emitido,DirEmail,DirWeb,ClaseDoc,
                SuRef,Observac,RefExt) 
                VALUES 
                (?, ?, ?, 
                ?, ?, ?, 
                ?, 
                ?, ?, ?, 
                '978','1','',
                ?,
                '2','2','2','1','2','1','2',
                '1','2','','','1',
                ?,'','')"""
        db_dimoni.commit(sql, data)
        return True

    def _create_warehouse_document_line(self, document, dimoni_cod_wh, line):
        db_dimoni = document.company_id.dbconnection_id
        data = [
            document.grp_id, document.signo, document.cod_serie, document.refnum,
            line.sequence, dimoni_cod_wh,
            line.product_id.code, line.product_id.name.rstrip()[:50].strip(),
            line.product_id.standard_price, line.product_id.standard_price,
            line.product_uom_qty, line.product_uom_qty, line.product_uom_qty,
        ]

        sql = """INSERT INTO PIALI 
                (GRP_ID,Signo,RefSerie,RefNum,
                Linea,Almacen,
                Articulo,Descripc,
                ClEspe,ClClas,Clave,
                PVenta, PVtaS2,
                CantEco,CantMan,CantOper,
                Procesad,Historic,Exportad,ListEmba,Actualiz,Eliminad,
                Regimen,Cee,TipoImp,Caracter) 
                VALUES 
                (?,?,?,?,
                ?,?,
                ?,?,
                '','','',
                ?,?,
                ?,?,?,
                '2','2','2','2','2','2',
                'X','X','X','X')"""
        db_dimoni.commit(sql, data)
        return True

    @api.multi
    def recurring_create_warehouse_dimoni(self, sale_order):
        db_dimoni = sale_order.company_id.dbconnection_id
        grp_id = sale_order.company_id.dimoni_company.grp_id
        serie = sale_order.company_id.dimoni_serie_wh.cod_serie
        tipo_doc = sale_order.company_id.dimoni_docwh.tipo_doc
        params = [grp_id, serie, tipo_doc]

        document_number = self.env['dimoni.sale']._asign_document_number(
                                                            db_dimoni, params)
        refnum = self.env['dimoni.sale']._create_refnum(document_number)
        ejercic = datetime.strptime(str(sale_order.confirmation_date),
                                    "%Y-%m-%d %H:%M:%S").strftime("%y")

        # Register the Dimoni Operation in database and self object
        document = self.env['dimoni.sale'].create({
            'company_id': sale_order.company_id.id,
            'grp_id': grp_id,
            'cod_emp': sale_order.company_id.dimoni_company.cod_emp,
            'cod_serie': serie,
            'tipo_doc': tipo_doc,
            'document': document_number,
            'refnum': refnum,
            'ejercic': ejercic,
            'signo': 'A',
        })

        # Create document header
        self._create_warehouse_document_header(document, sale_order)

        # Create document lines
        for line in sale_order.order_line:
            self._create_warehouse_document_line(document,
                                            sale_order.dimoni_wh.cod_wh, line)

        # Write relation Dimoni document with the sale order
        sale_order.write({'dimoni_sale': document.id})
        #
        # Change Sale Order state to blocked
        sale_order.write({'state': 'done'})

        return True

    def _dimoni_warehouse_delete_document(self, dimoni_document):
        # Keep dimoni document in self
        self = dimoni_document
        db_dimoni = self.company_id.dbconnection_id
        params = [
            self.grp_id, self.tipo_doc, self.cod_serie,
            self.document, self.refnum,
            self.ejercic, self.signo,
        ]

        # First: Search the document before be precesed in Dimoni
        sql = """Select ROW_ID 
              FROM PIACA 
              Where GRP_ID = ? And TipoDoc = ? And Serie = ? 
              And Document = ? And RefNum = ? 
              And Ejercic = ? And Signo = ?"""
        res = db_dimoni.execute(sql, params)

        # Record exits and we can delete it
        if len(res) == 1:
            # Delete Header
            sql = """DELETE PIACA 
                  Where GRP_ID = ? And TipoDoc = ? 
                  And Serie = ? 
                  And Document = ? And RefNum = ? 
                  And Ejercic = ? And Signo = ?"""
            db_dimoni.commit(sql, params)

            # Delete Lines. We have to change parameters.
            params = [i for j, i in enumerate(params) if j not in (1, 3, 5, 7)]
            sql = """DELETE PIALI 
                  Where GRP_ID = ? And RefSerie = ? 
                  And RefNum = ? And Signo = ?"""
            db_dimoni.commit(sql, params)
            #
            # Finally we adjust the number counter.
            self._desasign_document_number()
            return True

        '''Search the document processed:
        The field (refnum) is different in processed document.
        We eliminated the parameter for the search.'''
        params.remove(self.refnum)
        if not res:
            sql = """Select ROW_ID 
                  FROM PDACA 
                  Where GRP_ID = ? And TipoDoc = ? And Serie = ? 
                  And Document = ? And Ejercic = ? And Signo = ?"""
            res = db_dimoni.commit(sql, params)
            # We find the document procesed and Alert
            if res:
                raise UserError(_
                    ("Document: %s\n"
                    "The document has been processed in Dimoni.\n"
                    "You should first delete it in Dimoni.")
                    % self.name)
                return False
            else:
                return True
        else:
            raise UserError(_
                ("Something is wrong. Results of the search are not correct."))
            return False


    @api.multi
    def dimoni_delete_warehouse(self, dimoni_document):
        res = self._dimoni_warehouse_delete_document(dimoni_document)
        # Delete record
        if res:
            dimoni_document.unlink()

        return True
