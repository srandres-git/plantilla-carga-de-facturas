from cfdi_inspection import explore_directories_gen, load_xsd_data, read_cfdi, read_cfdi_list_gen, get_cfdi_version, get_namespaces, explore_directory_gen, get_xml_files, xml_reader
from config import NODOS, VERSIONES, XSD_PATHS

# import pandas as pd
import timeit
from file_management import export_to_excel, generate_template
from cfdi_processing import read_cartaporte
from funciones_prev import generar_reporte, read_conceptos

xml_files = get_xml_files(r"C:\Users\Andres Sanchez\OneDrive - OPEN LOG S.A DE C.V\Documentos\XML files\XML_FACT_AGO24_CAPTURADAS")
cartasporte = read_cartaporte(xml_files)
conceptos = generar_reporte(read_conceptos(xml_files))
print(
    conceptos.merge(cartasporte, on='UUID', how='left')
)