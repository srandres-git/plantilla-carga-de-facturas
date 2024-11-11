from cfdi_inspection import  get_xml_files

# import pandas as pd
from file_management import export_to_excel, generate_template
from cfdi_processing import conceptos_cartaporte
from funciones_prev import generar_reporte, read_conceptos

zip_path = r"C:\Users\Andres Sanchez\OneDrive - OPEN LOG S.A DE C.V\Documentos\Cruce claves de producto\Cruce Cve-CCP-Desc\No está SAP 2024 241111\XML_NOESTÁSAP_OK_111124.zip"
print(
    conceptos_cartaporte(zip_path)
)