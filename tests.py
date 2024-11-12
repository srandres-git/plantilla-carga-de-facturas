import pandas as pd
from cfdi_inspection import  get_xml_files
# import pandas as pd
from file_management import export_to_excel, generate_template
from cfdi_processing import conceptos_cartaporte, generar_plantilla, obtener_base, cve_retencion
from funciones_prev import generar_reporte, read_conceptos
from asignacion_producto import analisis_descripcion, asign_cve_prod_sap
from config import PATH_CVES_NO_TRANSP_SIN_RET

zip_path = r"C:\Users\Andres Sanchez\OneDrive - OPEN LOG S.A DE C.V\Documentos\Cruce claves de producto\Cruce Cve-CCP-Desc\No está SAP 2024 241111\XML_NOESTÁSAP_OK_111124.zip"
# facturas = conceptos_cartaporte(zip_path)
# facturas['Base IVA 16% Traslado'] = facturas.apply(lambda x: obtener_base(x, 0.16, 'Precio neto', 'Importe de impuesto'), axis=1)
# facturas['Base IVA 4% Retencion'] = facturas.apply(lambda x: obtener_base(x, 0.04, 'Base individual retencion', 'Importe de retencion'), axis=1)
# facturas = analisis_descripcion(facturas)
# #print(facturas[facturas['Servicio'].notnull()][['Descripcion','Servicio','Palabras clave']])
# asign_table = pd.read_excel(PATH_CVES_NO_TRANSP_SIN_RET)
# facturas[['ID de producto','Observación asignación de producto']] = facturas.apply(lambda x: asign_cve_prod_sap(x, asign_table), axis=1, result_type='expand')
# #print(facturas[['ID de producto','Observación asignación de producto']])
# facturas['Clave retención'] = facturas.apply(cve_retencion, axis=1)
# print(facturas[['ID de producto','Observación asignación de producto','Clave retención']])
print(generar_plantilla(zip_path))