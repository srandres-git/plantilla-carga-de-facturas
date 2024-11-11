import streamlit as st
import zipfile
import pandas as pd
from cfdi_processing import conceptos_cartaporte
from file_management import get_xml_files_from_zip
from funciones_prev import lectura_xml, generar_reporte, descarga, desglose_xml, validacion

st.title("Procesar Archivos ZIP")
# xmls = []

#Toggle para diferentes funciones
plantilla = st.toggle("Generar plantilla", key = "toggle")


# Subir el archivo ZIP
archivo_cargado = st.file_uploader("Sube un archivo ZIP", type="zip")

if archivo_cargado is not None:
    # Leer el contenido del archivo ZIP
    # with zipfile.ZipFile(archivo_cargado, 'r') as zip_ref:
        # Listar los archivos en el ZIP
        # nombres_archivos = zip_ref.namelist()
        # st.write("Archivos en el ZIP:")

        # #Se abre archivos xml en memoria y se almacenan en una lista
        # for filename in nombres_archivos:
        #     if filename.lower().endswith('.xml'):
        #         xmls.append(zip_ref.open(filename))
        
        if plantilla == True:
            # # Se llama a la función para leer el xml *** to do: definir nueva función para leer el xml
            # contenido = lectura_xml(xmls)

            # # Genera el DataFrame mediante la función y se muestra en pantalla *** to do: definir nueva función para generar el reporte
            # df = generar_reporte(contenido)
            df = conceptos_cartaporte(archivo_cargado)
            st.dataframe(df)

            #Llama a la función para la descarga del archivo
            salida = descarga(df)

            #Genera el boton para poder descargar el archivo de excel
            st.download_button(
            label= "Descargar Excel",
            data= salida,
            file_name= "plantilla.xlsx",
            mime= "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        else:
            archivo_ecomp = st.file_uploader("Sube el archivo de ecomp.", type = ".xlsx")
            if archivo_ecomp is not None:
                xmls = get_xml_files_from_zip(archivo_cargado)
                contenido = desglose_xml(xmls)
                df = validacion(item = contenido, ecomp = archivo_ecomp)
                st.dataframe(df)

                salida = descarga(df)

                st.download_button(
                label= "Descargar Excel",
                data= salida,
                file_name= "desglose.xlsx",
                mime= "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")