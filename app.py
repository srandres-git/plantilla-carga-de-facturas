import streamlit as st
import zipfile
import pandas as pd
from cfdi_processing import generar_plantilla
from file_management import get_xml_files_from_zip
from funciones_prev import descarga, desglose_xml, validacion
from utils import get_provs

st.title("Procesar Archivos ZIP")

# SAP auth session keys
if 'sap_authenticated' not in st.session_state:
    st.session_state['sap_authenticated'] = False
if 'sap_username_saved' not in st.session_state:
    st.session_state['sap_username_saved'] = ''
if 'sap_password_saved' not in st.session_state:
    st.session_state['sap_password_saved'] = ''
# SAP auth container
sap_auth_container = st.container(key='sap_auth_container')

# Authentication form: validate credentials before showing uploaders and conciliation
if not st.session_state['sap_authenticated']:
    with sap_auth_container:
        st.markdown('### Autenticación SAP requerida')
        with st.form(key='sap_auth_form'):
            user = st.text_input('Usuario SAP', key='sap_username_input')
            pwd = st.text_input('Contraseña SAP', type='password', key='sap_password_input')
            submit = st.form_submit_button('Validar credenciales SAP')
        if submit:
            with st.spinner('Validando credenciales...'):
                # use a tiny sample to validate credentials quickly
                test = get_provs(['XEXX010101000'], username=user, password=pwd, bucket_size=1)
                if test is None:
                    st.error('Credenciales inválidas o error de conexión. Intenta de nuevo.', icon='❌')
                    st.session_state['sap_authenticated'] = False
                else:
                    st.success('Autenticación SAP exitosa.', icon='✅')
                    st.session_state['sap_authenticated'] = True
                    st.session_state['sap_username_saved'] = user
                    st.session_state['sap_password_saved'] = pwd
                    st.rerun() # rerun to load uploaders
        else:
            st.info('Introduce tus credenciales SAP y pulsa "Validar credenciales SAP" para continuar.')

if st.session_state['sap_authenticated']:
    st.success('Autenticación SAP ya validada. Puedes proceder a subir tus archivos.', icon='✅')
    #Toggle para diferentes funciones
    plantilla = st.toggle("Generar plantilla", key = "toggle", value=True)


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
                
                df = generar_plantilla(archivo_cargado)
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