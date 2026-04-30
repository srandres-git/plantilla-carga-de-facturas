import pandas as pd
import requests
import streamlit as st

def format_request_url(base_url : str, report_name : str, parameters: dict):
    """Devuelve URL de consulta OData con el formato correcto"""

    select_str =  "$select=" + ','.join(parameters['select'])

    if len(parameters['filter'])>0:
        filter_str = f"$filter=({parameters['filter'][0]})"
        # Si hay más de un filtro, los une mediante un 'and'
        if len(parameters['filter'])>1:
            for i in range(1,len(parameters['filter'])):
                filter_str+= f" and ({parameters['filter'][i]})"
    else:
        filter_str=''
    
    if filter_str=='':
        url = base_url+report_name+'QueryResults?'+select_str+'&$format=json'
    else:
        url = base_url+report_name+'QueryResults?'+select_str+'&'+filter_str+'&$format=json'

    return url

def request_df(base_url : str, report_name : str, parameters : dict, username : str, password : str):
    "Realiza petición OData y regresa los resultados en un Dataframe"

    headers = {"Accept": "application/json"}  # ensure JSON is returned
    # Make the request
    url = format_request_url(base_url, report_name, parameters)
    # print(f"Requesting URL: {url}")
    response = requests.get(url, auth=(username, password), headers=headers)
    print(f"Response: {response}")
    # print("DETAILS: "
    #       f"URL: {response.url}, Status Code: {response.status_code}, Reason: {response.reason}")
    if response.status_code == 200:
    # Generate Dataframe
        try:
            df = pd.json_normalize(response.json()['d']['results'])
            # CPOSTING_DATE from string ms to datetime
            if 'CPOSTING_DATE' in df.columns:
                df['CPOSTING_DATE'] = pd.to_datetime(df['CPOSTING_DATE'].str.extract(r'/Date\((\d+)\)/')[0].astype(int), unit='ms')
            if 'CTRANSDAT' in df.columns:
                df['CTRANSDAT'] = pd.to_datetime(df['CTRANSDAT'].str.extract(r'/Date\((\d+)\)/')[0].astype(int), unit='ms')
            return df
        except Exception as error:
            print(error)
            return None
    else:
        print("Error Response Text:", response.text)  # safer than .json() for 401
        return None

def get_provs(rfc_list:list,username,password, bucket_size: int = 30)->pd.DataFrame:
    """Obtiene los proveedores de SAP a partir de una lista de RFCs"""
    report_name = "RPBUPSPP_Q0001"
    parameters = {
        'select': ['CBP_UUID', 'CTAX_ID_NR','CCREATION_DT','C1FHH0E7IT2A94ZAWAW8C3VPCIP','TTAX_COUNTRY'],
    }
    # realizamos la petición en buckets de 30 RFCs
    provs = pd.DataFrame()
    for i in range(0, len(rfc_list), bucket_size):
        print(f'[Procesando RFCs {i+1} a {min(i+bucket_size, len(rfc_list))} de {len(rfc_list)}]')
        rfc_bucket = rfc_list[i:i+bucket_size]
        filter_rfc = " or ".join([f"CTAX_ID_NR eq '{rfc}'" for rfc in rfc_bucket])
        parameters['filter'] = [filter_rfc]
        provs_bucket = request_df(st.secrets['sap_odata_base_url'], report_name, parameters, username, password)
        if provs_bucket is not None:
            print(f'[Proveedores obtenidos en este bucket: {len(provs_bucket)}]')
            provs = pd.concat([provs, provs_bucket], ignore_index=True)
    if provs.empty:
        print('No se obtuvieron proveedores de SAP.')
        return None
    # depuramos la fecha de creación
    provs['CCREATION_DT'] = pd.to_datetime(provs['CCREATION_DT'].str.split(' ').str[0], errors='raise', format='%d.%m.%Y')
    # ordenamos descendentemente por ID de proveedor y fecha de creación
    provs = provs.sort_values(['CBP_UUID','CCREATION_DT'], ascending=[False, False])
    # quitamos duplicados por RFC, dejando la primera (la de fecha más reciente)
    provs = provs.drop_duplicates(subset=['CTAX_ID_NR'], keep='first').reset_index(drop=True)
    # quitamos la columna de fecha de creación para el usuario final, ya que no es relevante y puede generar confusión
    provs = provs.drop(columns=['CCREATION_DT'])
    provs.rename(columns={'CBP_UUID':'Proveedor', 'CTAX_ID_NR':'RFC', 'C1FHH0E7IT2A94ZAWAW8C3VPCIP': 'Nombre Proveedor', 'TTAX_COUNTRY': 'País/Región fiscal de proveedor'}, inplace=True)

    return provs