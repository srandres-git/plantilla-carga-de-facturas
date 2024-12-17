from datetime import datetime
# _____________________________________________________________
# Inspección de CFDI  
VERSIONES = {
    'cfdi': ['cfdi3', 'cfdi4'],
    'cartaporte': ['cartaporte','cartaporte20', 'cartaporte31', 'cartaporte30'],
    'tfd': ['tfd'],
}
XSD_PATHS = {}
for tipo in VERSIONES.keys():
    for ver in VERSIONES[tipo]:
        XSD_PATHS[ver] = f'./xsd_files/{tipo}/{ver}.xsd'

NODOS_CARTAPORTE = ['CartaPorte', ]
NODOS_CFDI = ['Emisor',]
NODOS_TFD = []
NODOS = {'cfdi': NODOS_CFDI, 'cartaporte': NODOS_CARTAPORTE, 'tfd': NODOS_TFD}
NODOS_PREDET = {'cfdi':[ 'Comprobante'], 'cartaporte': [], 'tfd': []}

ATRIBUTOS_PREDET = {
    'cfdi':{
        'Concepto': ['CveProdServ', 'DescCveProdServ', 'Descripcion', 'Importe'],
        'Emisor': ['Rfc', 'Nombre'],
    },
    'cartaporte':{
        'CartaPorte': ['Version','TranspInternac', 'EntradaSalidaMerc'],
    },
    'tfd':{

    },
}
# _____________________________________________________________

NOMBRES = {'cfdi': 'CFDI', 'cartaporte': 'Carta Porte', 'tfd': 'Timbre Fiscal'}

DEFAULT_DELAY = 1.0
# _____________________________________________________________

DEFAULT_START_DATE = datetime(year=2010,month=1,day=1)

# _____________________________________________________________
# # PLANTILLA

# Conceptos a buscar en nodo descripción
# estas serán las palabras clave que buscaremos en la descripción de los productos
CONCEPTOS = {
    "FLETE": 'FLETE[S]*',
    'MOVIMIENTO EN FALSO': '[A-ZÁÉÍÓÚÑ]*[ ]*EN FALSO',
    "NACIONAL": 'NACIONAL[ES]*',
    "LOCAL": 'LOCAL[ES]*',
    'REGIONAL': 'REGIONAL[ES]*',
    "INTERNACIONAL": 'INTERNACIONAL[ES]*',
    "CONTENEDOR": 'CONTENEDOR[ES]*',
    "DEMORAS": 'DEMORA[S]*',
    "SERVICIOS DE TRANSPORTE": 'SERVICIO[S]* [DE ]*TRANSPORTE',
    "ESTADÍAS": 'ESTAD[ÍI]A[S]*',
    "LOGÍSTICA": 'LOG[ÍI]STICA',
    "CRUCE": 'CRUCE[S]*',
    "MANEJO DE MATERIALES": 'MANEJO[S]* [DE ]*MATERIAL[ES]*',
    "QUÍMICOS": 'QU[ÍI]MICO[S]*',
    "CUSTODIA": 'CUSTODIA[S]*',
    "ALMACENAMIENTO": 'ALMACENA[MIENTO]*[AJE]*',
    "REFACCIONES AUTOMOTRICES": 'REFACCI[OÓ]N[ES]* AUTOMOTRI[Z]*[CES]*',
    "AUTOPISTAS": 'AUTOPISTA[S]*',
    "PEDIMENTO": 'PEDIMENTO[S]*',
    "MANIOBRAS": 'MANIOBRA[S]*',
    "CARGA": '[^S]CARGA[S]*',
    "DESCARGA": 'DESCARGA[S]*',
    "ACCESORIOS PARA VIAJE": 'ACCESORIO[S]* [PARA ]*VIAJE',
    "SOBREPESO": 'SOBREPESO[S]*',
    "BÁSCULA": 'B[ÁA]SCULA[S]*',
    "PERMISOS": 'PERMISO[S]*',
    "MANEJO DE MERCANCÍAS": 'MANEJO[S]* [DE ]*MERCANC[ÍI]A[S]*',
    "DOCUMENTACIÓN": 'DOCUMENTACI[ÓO]N',
    "ESTACIONAMIENTO": 'ESTACIONAMIENTO[S]*',
    "ACCESORIO FLETE": 'ACCESORIO[S]* [DE ]*FLETE',
    "CARTA PORTE": 'CARTA[S]* PORTE',
    "SEGURO": '[A]*SEGUR[OA]+[MIENTO]*[S]*',
}
# Algunos nombres de columnas
# los campos que se tomarán del reporte de cartas porte
CAMPOS_CCP = ['Version', 
              'cartaporte: TranspInternac', 
              'cartaporte: EntradaSalidaMerc',]
# nombres de las columnas que se toman para asignar fecha de vencimiento y pago
COLS_PAY_DATE = {
    'Llegada a Box': 'Llegada Box',
    'Días de crédito': 'Días Credito',
}
# columnas que se utilizarán para obtener el número de servicio
COLS_SERVICE = ['Nombre del archivo', 'Descripcion']

# Claves de productos SAT
# CveProdServ de productos de transporte de carga por carretera
# 78101800 Transporte de carga por carretera
# 78101801 Servicios de transporte de carga por carretera (en camión) en área local
# 78101802 Servicios transporte de carga por carretera (en camión) a nivel regional y nacional
# 78101806 Servicios transporte de carga por carretera a nivel internacional
# 78101807 Servicios de transporte de carga de petróleo o químicos  por carretera
CVES_TRANSPORTE_TERR = ['78101800', '78101801', '78101802', '78101806', '78101807']
CVES_TRANSPORTE_TERR_NAC = ['78101800', '78101801', '78101802', '78101807']
# Claves genéricas (No existe en el catálogo)
CVES_GEN = ['1010101','01010101']

# Archivo que relaciona las claves de productos con las descripciones para aquellos que no son de transporte ni tienen retención
PATH_CVES_NO_TRANSP_SIN_RET = './cves_prod_no_transp_sin_ret.xlsx'

# Archivo de base de proveedores
PATH_BASE_PROV = './base_proveedores.xlsx'

# columnas que se exportarán a la plantilla
COLS_PLANTILLA = ['No. Doc', 'Posicion', 'Tipo de documento', 'Tipo de asignación', 'Asignación', 'Proveedor', 'Empresa compradora', 
                  'No. Servicio', 'Moneda', 'Documento externo', 'Folio fiscal', 'Fecha de recepción', 'Fecha de factura',
                  'Fecha de contabilización', 'Fecha de vencimiento', 'ID de producto','Cantidad', 'Precio neto',
                  'Código de impuesto', 'Código de retención' , 'Importe de impuesto', 
                  'Nombre archivo XML', 'Descripción', 'Observación asignación de producto', 'Clave de producto o servicio','Descripción concepto XML']