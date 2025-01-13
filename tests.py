import pandas as pd
# import pandas as pd
from file_management import export_to_excel, generate_template, get_xml_files_from_zip
from cfdi_processing import conceptos_cartaporte, generar_plantilla, read_conceptos_impuestos

zip_path = r"C:\Users\Andres Sanchez\OneDrive - OPEN LOG S.A DE C.V\Documentos\XML files\Sample XMLs.zip"

plantilla = generar_plantilla(zip_path)
print(plantilla)
plantilla.to_excel('plantilla.xlsx', index=False)
