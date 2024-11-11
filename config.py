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
NODOS_CFDI = ['Concepto',]
NODOS_TFD = []
NODOS = {'cfdi': NODOS_CFDI, 'cartaporte': NODOS_CARTAPORTE, 'tfd': NODOS_TFD}
NODOS_PREDET = {'cfdi':[ 'Comprobante'], 'cartaporte': [], 'tfd': []}

ATRIBUTOS_PREDET = {
    'cfdi':{
        'Concepto': ['CveProdServ', 'DescCveProdServ', 'Descripcion', 'Importe'],
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
# # GUI
# VER = '5.0'
# APP_WIDTH = 875
# APP_HEIGHT = 450
# PROGRESS_POPUP_WIDTH = 210
# PROGRESS_POPUP_HEIGHT = 60
DEFAULT_START_DATE = datetime(year=2010,month=1,day=1)