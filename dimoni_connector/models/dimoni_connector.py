# Copyright 2018 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DimoniCompany(models.Model):
    _name = "dimoni.company"
    _description = "Dimoni Companies"
    _order = 'grp_id'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one(string='Company', comodel_name='res.company', 
        default=_get_default_company_id, required=True)
    dbconnection_id = fields.Many2one(string='Database connection',
        comodel_name="base.external.dbsource", required=True, ondelete='cascade')
    grp_id = fields.Char(string='Dimoni Company Code Identifier', size=12)
    cod_emp = fields.Char(string='Dimoni Company Code', size=6)
    name = fields.Char(string='Dimoni Company Name', size=40)

    _sql_constraints = [(
        'uniq_grp_id',
        'unique(company_id, dbconnection_id, grp_id)',
        'A Dimoni Company with the same reference already exists for this company and connection!')]
        
    def import_company(self, company):
        # Obtain Dimoni companies
        params = []
        db_dimoni = company.dbconnection_id
        sql = "SELECT " \
              "GRP_ID as 'grp_id', " \
              "CodEmpre as 'cod_emp', " \
              "Nombre as 'name' FROM dbo.SEMPE"
        res = db_dimoni.execute(sql, params, metadata=True)

        if len(res['rows']) == 0:
            raise UserError(_
                ("There's no any company whit this connection.\n"
                 "Are you sure is the correct connection?"))

        company_id = company._origin.id
        for row in res['rows']:
            try:
                self.create({
                    'company_id': company_id,
                    'dbconnection_id': company.dbconnection_id.id,
                    'grp_id': row[0],
                    'cod_emp': row[1],
                    'name': row[2],
                })
            except:
                continue


class DimoniSeries(models.Model):
    _name = "dimoni.serie"
    _description = "Dimoni Company Series"
    _order = 'cod_serie'

    grp_id = fields.Many2one(string='Company Code', 
        comodel_name='dimoni.company', ondelete='cascade',
        help='Dimoni Company Code Identifier')
    cod_serie = fields.Char(string='Dimoni Serie Code', size=3)
    name = fields.Char(string='Dimoni Serie Name', size=30)
    almacen = fields.Char(string='Dimoni WH', size=2,
        help='Dimoni warehouse for the serie')

    _sql_constraints = [(
            'uniq_serie',
            'unique(grp_id, cod_serie)',
            'A Dimoni Seire with the same code already exists for this company!')]

    def import_serie(self, company):
        params = [company.dimoni_company.grp_id, 1]
        db_dimoni = company.dbconnection_id
        sql = "SELECT " \
              "Serie as 'cod_serie', " \
              "Descripc as 'name', " \
              "Almacen as 'almacen' " \
              "FROM dbo.PSERI " \
              "WHERE GRP_ID = ? and Activa = ?"
        res = db_dimoni.execute(sql, params, metadata=True)

        if len(res['rows']) == 0:
            raise UserError(_
                ("There's no any Serie for this company.\n"
                 "Are you sure is the correct company?"))

        for row in res['rows']:
            try:
                self.create({
                    'grp_id': company.dimoni_company.id,
                    'cod_serie': row[0],
                    'name': row[1],
                    'almacen': row[2],
                })
            except:
                continue


class DimoniDocument(models.Model):
    _name = "dimoni.document"
    _description = "Dimoni Document Types"
    _order = 'ambito'

    grp_id = fields.Many2one(string='Company Code', 
        comodel_name='dimoni.company', ondelete='cascade',
        help='Dimoni Company Code Identifier')
    cod_serie = fields.Many2one('dimoni.serie', string='Dimoni Serie Code')
    tipo_doc = fields.Char(string='Dimoni Tipo Doc', size=2)
    name = fields.Char(string='Dimoni Document Name', size=30)
    ambito = fields.Integer(string='Sale, Purchase, Warehouse, TPV', size=1)

    _sql_constraints = [(
            'uniq_document',
            'unique(grp_id, cod_serie, tipo_doc)',
            'A Dimoni Tipe Document with the same code already exists for this company and serie!')]

    def import_tipodoc(self, company):
        params = [company.dimoni_company.grp_id,
                  company.dimoni_serie.cod_serie, 2]
        db_dimoni = company.dbconnection_id

        sql = "SELECT " \
              "t.TipoDoc as 'tipo_doc', " \
              "t.Descripc as 'name', " \
              "Ambito as 'ambito' " \
              "FROM dbo.PSERI AS s INNER JOIN " \
              "dbo.PSERD AS p ON s.GRP_ID = p.GRP_ID AND s.Serie = p.Serie INNER JOIN " \
              "dbo.PTDOC AS t ON s.GRP_ID = t.GRP_ID AND p.TipoDoc = t.TipoDoc " \
              "WHERE s.GRP_ID = ? and s.Serie = ? and p.Activa = ?"
        res = db_dimoni.execute(sql, params, metadata=True)

        if len(res['rows']) == 0:
            raise UserError(_
                ("There's no any Document Tipe for this serie.\n"
                 "Are you sure is the correct serie?"))

        for row in res['rows']:
            try:
                self.create({
                    'grp_id': company.dimoni_company.id,
                    'cod_serie': company.dimoni_serie.id,
                    'tipo_doc': row[0],
                    'name': row[1],
                    'ambito': row[2],
                })
            except:
                continue


class DimoniSale(models.Model):
    _name = "dimoni.sale"
    _description = "Dimoni Sales"

    @api.one
    @api.depends('cod_emp', 'cod_serie', 'tipo_doc', 'document')
    def _compute_name(self):
        self.name = self.cod_emp + ' (' + \
                    datetime.strptime(self.ejercic, "%y").strftime("%Y") + \
                    ') ' + ' / ' + self.tipo_doc + '-' +  \
                    self.cod_serie + '-' + str(self.document)

    name = fields.Char(compute='_compute_name')
    company_id = fields.Many2one(string='Company', 
        comodel_name='res.company', required=True)
    grp_id = fields.Char(string='Dimoni Company Code Identifier', size=12)
    cod_emp = fields.Char(string='Dimoni Company Code', size=6)
    tipo_doc = fields.Char(string='Dimoni Tipo Doc', size=2)
    cod_serie = fields.Char(string='Dimoni Serie Code', size=3)
    document = fields.Integer(string='Dimoni Docu Number')
    refnum = fields.Char(string='Dimoni Docu Reference', size=15)
    ejercic = fields.Char(string='Fiscal Exercise', size=2,
        help='Dimoni two digits year as accounting exercise')
    signo = fields.Char(string='Sign', size=1,
        help='V: Sale, P:Purchase, A:Warehouse')

    def _asign_document_number(self, db_dimoni, params):
        # Obtain the last number of the document
        sql = "SELECT CONVERT(int,Contador) as 'contador'  " \
              "FROM PSERD " \
              "WHERE (GRP_ID= ?) AND(Serie= ?) AND (TipoDoc= ?)"
        res = db_dimoni.execute(sql, params)
        number = res[0][0]

        # Increase by one the document counter
        sql = "UPDATE PSERD " \
             "SET Contador = Contador + 1 " \
             "FROM PSERD " \
             "WHERE (GRP_ID= ?) AND (Serie= ?) AND (TipoDoc= ?)"
        db_dimoni.commit(sql, params)

        return number

    def _desasign_document_number(self):
        '''When we eliminated a document before be processed, we check
        the number and decreased by one if it's the last document created.'''
        db_dimoni = self.company_id.dbconnection_id
        params = [
            self.grp_id, self.tipo_doc, self.cod_serie,
            self.document,
            self.grp_id, self.tipo_doc, self.cod_serie,
        ]
        sql = "If (" \
              "(Select Contador FROM PSERD " \
              "WHERE " \
              "(GRP_ID = ?) AND (TipoDoc = ?) " \
              "AND (Serie = ?)" \
              ") - ?) = 1 " \
              "BEGIN " \
              "UPDATE PSERD " \
              "SET Contador = Contador - 1 " \
              "FROM PSERD " \
              "WHERE (GRP_ID = ?) AND (TipoDoc = ?) " \
              "AND (Serie = ?) " \
              "END"
        db_dimoni.commit(sql, params)
        return True

    def _create_refnum(self, document_number):
        '''This field is necessary for the relation between header and lines
        during the import process.
        When the document is imported in Dimoni this 'refnum' field is
        assigned by different one.'''
        refnum = str(document_number)
        while len(refnum) < 15:
            refnum = '0'+refnum

        return refnum

    def _create_document_header(self, sale_order):
        db_dimoni = self.company_id.dbconnection_id
        data = [
            self.grp_id, self.cod_serie, self.tipo_doc,
            sale_order.partner_id.ref, self.ejercic, self.document,
            datetime.strptime(str(sale_order.confirmation_date),
                              "%Y-%m-%d %H:%M:%S"),
            self.signo, self.cod_serie, self.refnum,
            datetime.strptime(str(sale_order.confirmation_date),
                              "%Y-%m-%d %H:%M:%S"),
            sale_order.partner_id.ref,
            sale_order.name,
        ]

        sql = "INSERT INTO PIVCA " \
              "(GRP_ID,Serie,TipoDoc," \
              "Cuenta,Ejercic,Document," \
              "Fecha," \
              "Signo,RefSerie,RefNum," \
              "Moneda,Cambio," \
              "Limite,CtaAsig,Proces," \
              "Historic,Export,Actualiz,Eliminad,MonDoc,Contabil," \
              "Origen,Emitido,DirEmail,DirWeb,ClaseDoc," \
              "SuRef,Vendedor,Observac,RefExt,Clave) " \
              "VALUES " \
              "(?, ?, ?, " \
              "?, ?, ?, " \
              "?, " \
              "?, ?, ?, " \
              "'978','1'," \
              "?,?,'2'," \
              "'2','2','1','2','1','2'," \
              "'1','2','','','1'," \
              "?,'','','','')"
        db_dimoni.commit(sql, data)
        return True

    def _create_document_line(self, line):
        db_dimoni = self.company_id.dbconnection_id
        data = [
            self.grp_id, self.cod_serie, self.refnum, self.signo,
            line.sequence, self.company_id.dimoni_serie.almacen,
            line.product_id.code, line.product_id.name.rstrip()[:50].strip(),
            line.price_unit, line.price_unit, line.product_uom_qty,
            line.product_uom_qty,
            line.product_uom_qty,
            line.discount,
        ]

        sql = "INSERT INTO PIVLI " \
              "(GRP_ID,RefSerie,RefNum,Signo," \
              "Linea,Almacen," \
              "Articulo,Descripc," \
              "ClEspe,ClClas,Clave,Pventa,PVtaS2,TipPrec,MonVent,CantEco," \
              "CantMan,Impuesto,Tributar,Recargo,DescLote,NPlan," \
              "Largo,Ancho,Alto,CantOper,Prevista,Limite,Procesad,Historic," \
              "Exportad,ListEmba,Actualiz,Eliminad,Analitic,VenCom,Devoluci," \
              "CtaImpu,Regimen,Cee,TipoImp,Caracter,Bultos,AplDtoAr,Peso," \
              "CodUDist,DtoCar01," \
              "PesoBrut,TaraReal,PesoNeto,Observac,PtoVerdF,Expedien," \
              "CodTradu,DesTradu,CtaImpIn,CmedioMB,CultMB,Proyecto," \
              "oExped,oTipo,oClase,oDep) " \
              "VALUES " \
              "(?,?,?,?," \
              "?,?," \
              "?,?," \
              "'','','',?,?,'','',?," \
              "?,'',0,0,'',''," \
              "0,0,0,?,'','','2','2'," \
              "'','','','2','','70000000','70800000'," \
              "'47700000','','','','',0,'',0," \
              "'',?," \
              "0,0,0,'',0,''," \
              "'','','47200000',0,0,''," \
              "'','','','')"
        db_dimoni.commit(sql, data)
        return True

    @api.multi
    def recurring_create_sale_dimoni(self, sale_order):
        db_dimoni = sale_order.company_id.dbconnection_id
        grp_id = sale_order.company_id.dimoni_company.grp_id
        serie = sale_order.company_id.dimoni_serie.cod_serie
        tipo_doc = sale_order.company_id.dimoni_docsale.tipo_doc
        params = [grp_id, serie, tipo_doc]

        document_number = self._asign_document_number(db_dimoni, params)
        refnum = self._create_refnum(document_number)
        ejercic = datetime.strptime(str(sale_order.confirmation_date),
                                    "%Y-%m-%d %H:%M:%S").strftime("%y")

        # Register the Dimoni Operation in database and self object
        self = self.create({
            'company_id': sale_order.company_id.id,
            'grp_id': grp_id,
            'cod_emp': sale_order.company_id.dimoni_company.cod_emp,
            'cod_serie': serie,
            'tipo_doc': tipo_doc,
            'document': document_number,
            'refnum': refnum,
            'ejercic': ejercic,
            'signo': 'V',
        })

        # Create document header
        self._create_document_header(sale_order)

        # Create document lines
        for line in sale_order.order_line:
            self._create_document_line(line)

        # Write relation Dimoni document with the sale order
        sale_order.write({'dimoni_sale': self.id})

        # Change Sale Order state to blocked
        sale_order.write({'state': 'done'})

        return True

    def _dimoni_delete_document(self):
        db_dimoni = self.company_id.dbconnection_id
        params = [
            self.grp_id, self.tipo_doc, self.cod_serie,
            self.document, self.refnum, self.ejercic, self.signo,
        ]

        # First: Search the document before be precesed in Dimoni
        sql = "Select ROW_ID " \
              "FROM PIVCA " \
              "Where GRP_ID = ? And TipoDoc = ? And Serie = ? " \
              "And Document = ? And RefNum = ? And Ejercic = ? " \
              "And Signo = ?"
        res = db_dimoni.execute(sql, params)

        # Record exits and we can delete it
        if len(res) == 1:
            # Delete Header
            sql = "DELETE PIVCA " \
                  "Where GRP_ID = ? And TipoDoc = ? And Serie = ? " \
                  "And Document = ? And RefNum = ? And Ejercic = ? " \
                  "And Signo = ?"
            db_dimoni.commit(sql, params)

            # Delete Lines. We have to change parameters.
            params = [i for j, i in enumerate(params) if j not in (1, 3, 5, 7)]
            sql = "DELETE PIVLI " \
                  "Where GRP_ID = ? And RefSerie = ? " \
                  "And RefNum = ? And Signo = ?"
            db_dimoni.commit(sql, params)

            # Finally we check the number counter
            self._desasign_document_number()
            return True

        '''Search the document processed:
        The field (refnum) is different in processed document. 
        We eliminated the parameter for the search.'''
        params.remove(self.refnum)
        if not res:
            sql = "Select ROW_ID " \
                  "FROM PDVCA " \
                  "Where GRP_ID = ? And TipoDoc = ? And Serie = ? " \
                  "And Document = ? And Ejercic = ? And Signo = ?"
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
    def dimoni_delete_sale(self, dimoni_document):
        # Keep dimoni document in self
        self = dimoni_document

        res = self._dimoni_delete_document()
        # Delete record
        if res:
            self.unlink()

        return True
