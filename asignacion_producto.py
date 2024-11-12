"""Funciones realizadas para la asignación de producto SAP dependiendo de la clave de producto o servicio del CFDI,
    la descripción del mismo y el complemento de carta porte"""
from config import CONCEPTOS, CAMPOS_CCP, COLS_PAY_DATE, COLS_SERVICE, CVES_TRANSPORTE_TERR, CVES_TRANSPORTE_TERR_NAC, CVES_GEN, PATH_CVES_NO_TRANSP_SIN_RET
import re
import numpy as np
import pandas as pd

# _____________________________________________________________
# FORMATO DE DESCRIPCIÓN
def format_description(df_facturas : pd.DataFrame)-> pd.DataFrame:
    """
    Formatea la columna de descripción de un DataFrame
    """
    # descripción a mayúsculas
    df_facturas['Descripcion'] = df_facturas['Descripcion'].str.upper()
    # CveProdServ a string
    df_facturas['Clave de producto o servicio'] = df_facturas['Clave de producto o servicio'].astype(str)
    # quitamos el '.0' de la columna CveProdServ
    df_facturas['Clave de producto o servicio'] = df_facturas['Clave de producto o servicio'].str.replace('.0','')
    # UUID a mayúsculas
    df_facturas['UUID'] = df_facturas['UUID'].str.upper()
    return df_facturas
# _____________________________________________________________
# ANÁLISIS DEL CAMPO DESCRIPCIÓN
# Función para buscar conceptos en la descripción
def search_keywords(text : str, keywords : dict):
    """
    Busca palabras clave en un texto y regresa un diccionario booleano con los resultados
    """
    res = {}
    for concept, pattern in keywords.items():
        res[concept] = bool(re.search(pattern, text))
    return res

def get_keywords(text : str, keywords : dict):
    """
    Busca palabras clave en un texto y regresa una lista con los conceptos encontrados
    """
    res = []
    for concept, pattern in keywords.items():
        if re.search(pattern, text):
            res.append(concept)
    return res
def concat_keywords(words : list, message : str = '[Sin palabras clave]'):
    """
    Concatena las palabras clave en una sola cadena
    """
    return '|'.join(words) if len(words)>0 else message
# Función para extraer el número de servicio
def find_service(row):
    """
    Encuentra el número de servicio en una cadena de texto s:
    formato AA-XXXXXX
    """    
    # Expresión regular para el patrón AA-XXXXXX
    pattern = rf'(2[34]+)[ ]?[- _]+[ ]?(\d{{6}})'
    # Buscar el patrón en el texto de cada columna de la lista cols_service
    for col in COLS_SERVICE:
        matches = re.findall(pattern, row[col])
        if len(matches)>0:
            # regresar solo matches distintos
            return '/'.join(set([f'{m[0]}-{m[1]}' for m in matches]))
    return np.nan

def analisis_descripcion(df_facturas : pd.DataFrame)-> pd.DataFrame:
    """
    Realiza el análisis de la descripción de los productos.
    Genera las columnas 'Palabras clave' y 'Servicio'.
    """
    df_facturas = format_description(df_facturas)
    # Buscar palabras clave
    df_facturas['Palabras clave'] = df_facturas['Descripcion'].apply(lambda x: concat_keywords(get_keywords(x, CONCEPTOS)))
    # Encontrar número de servicio
    df_facturas['Servicio'] = df_facturas.apply(find_service, axis=1)
    return df_facturas

# _____________________________________________________________
# ASIGNACIÓN DE PRODUCTO


def cves_prod_no_transp_sin_ret(cve_sat:str, palabras_clave:str, asign_table:pd.DataFrame):
    """Asigna el producto de SAP a un concepto *diferente* de transporte de carga por carretera
        usando la descripción de la clave de producto y las palabras clave encontradas,
        mediante una tabla de asignación manual."""
    # Buscar en la tabla
    mask = (asign_table['CveProdServ']==cve_sat) & (asign_table['Palabras clave']==palabras_clave)
    if mask.any():
        return asign_table.loc[mask, 'Producto'].values[0], 'Asignación mediante tabla'
    else:
        return 'INDETERMINADO', '(!) No se encontró coincidencia en la tabla de asignación'

def asign_cve_prod_sap(row, asign_table:pd.DataFrame):
    """
    Asigna la clave de producto de SAP a un concepto de transporte de carga por carretera,
    tomando en cuenta traslado o retención de IVA, datos de la carta porte y el análisis de la descripción.
    Además, genera una observación en caso de que la factura no cumpla con los requisitos.
    """
    cve_sat = row['Clave de producto o servicio']
    # desc_cve_sat = row['DescCveProdServ']
    base_iva_16 = row['Base IVA 16% Traslado']
    base_ret_iva_4 = row['Base IVA 4% Retencion']
    ccp = row['Tiene CCP']
    transp_internac = row['TranspInternac']
    entrada_salida = row['EntradaSalidaMerc']
    palabras_clave = row['Palabras clave']
    mov_falso = row['Palabras clave'].find('MOVIMIENTO EN FALSO')>=0

    # ¿Tiene CveProd SAT de transporte de carga terrestre?
    if cve_sat in CVES_TRANSPORTE_TERR:
        # ¿Base Traslado IVA 16% >0?
        if base_iva_16>0:
            # ¿Base Retención IVA 4% >0?
            if base_ret_iva_4>0:
                # ¿Tiene CCP?
                if ccp:
                    # ¿TranspInternac?
                    if transp_internac=='Sí':
                        # ¿EntradaSalidaMerc?
                        if entrada_salida=='Entrada':
                            return 'CRUCE_FRONTERA_E', 'Traslado y retención de IVA/ CCP: transp. internacional, entrada'
                        elif entrada_salida=='Salida':
                            return 'CRUCE_FRONTERA_N', 'Traslado y retención de IVA/ CCP: transp. internacional, salida'
                    elif transp_internac=='No':
                        return 'FLETE_TER_N', 'Traslado y retención de IVA/ CCP: transp. nacional'
                else:
                    # ¿Cve = 78101806 (internacional)?
                    if cve_sat=='78101806':
                        return 'FLETE_TER_E', '(!) Traslado y retención de IVA/ cve SAT: T. internacional /Sin CCP'
                    else:
                        # ¿Cve = 78101801 (local) o 78101800 (general)?
                        if cve_sat in ['78101801', '78101800']:
                            return 'FLETE_TER_N', 'Traslado y retención de IVA/ cve SAT: T. local (o con clave general) /Sin CCP'
                        else:
                            return 'FLETE_TER_N', '(!) Traslado y retención de IVA/ cve SAT: T. nacional no local /Sin CCP'
            else:
                # ¿Movimiento en falso (Descripción)?
                if mov_falso:
                    return 'MOV_FALSO_N', 'Traslado de IVA sin retención/ Desc.: Movimiento en falso'
                # ¿Cve de transporte nacional?
                elif cve_sat in CVES_TRANSPORTE_TERR_NAC:
                        # Palabras clave: Flete, Servicio de transporte, ninguna
                        if palabras_clave.find('FLETE')>=0 or palabras_clave.find('SERVICIOS DE TRANSPORTE')>=0 or palabras_clave=='[Sin palabras clave]':
                            return 'SERV_LOG_N', '(!) Traslado de IVA sin retención/ cve SAT: T. nacional'
                        # Palabras clave: demoras
                        elif palabras_clave.find('DEMORAS')>=0:
                                # Palabras clave: Descarga
                                if palabras_clave.find('DESCARGA')>=0:
                                    return 'DEM_DES_N', '(!) Traslado de IVA sin retención/ cve SAT: T. nacional'
                                else:
                                    return 'DEM_CAR_N', '(!) Traslado de IVA sin retención/ cve SAT: T. nacional'
                        else:
                            return 'INDETERMINADO', '(!) Traslado de IVA sin retención/ cve SAT: T. nacional'
                else:
                    return 'FLETE_TER_E', 'Traslado de IVA sin retención/ cve SAT: T. internacional'
        else:
            # ¿Tiene CCP?
            if ccp:
                # ¿TranspInternac?
                if transp_internac=='Sí':
                    # ¿Cve = 78101806 (internacional)?
                    if cve_sat=='78101806':
                        return 'FLETE_TER_E', 'CCP y cve SAT: transp. internacional/ Sin IVA'
                    else:
                        return 'FLETE_TER_E', '(!) CCP: transp. internacional/ cve SAT: transp. nacional/ Sin IVA'
                elif transp_internac=='No':
                    # ¿Cve = 78101806 (internacional)?
                    if cve_sat=='78101806':
                        return 'FLETE_TER_E', '(!) CCP: transp. nacional/ cve SAT: transp. internacional/ Sin IVA'
                    else:
                        return 'FLETE_TER_N', '(!) CCP y cve SAT: transp. nacional/ Sin IVA'
            else:
                # ¿Movimiento en falso (Descripción)?
                if mov_falso:
                    return 'MOV_FALSO_N', 'Sin IVA/ Desc.: Movimiento en falso'
                # ¿Cve = 78101806 (internacional)?
                elif cve_sat=='78101806':
                        return 'FLETE_TER_E', 'Sin IVA/ cve SAT: T. internacional /Sin CCP'
                else:
                    return 'FLETE_TER_N', '(!) Sin IVA/ cve SAT: T. nacional /Sin CCP/ No mov. en falso'
    else:
        # ¿Base Retención IVA 4% >0?
        if base_ret_iva_4>0:
            # ¿Cve = 78101803 (Transp. de vehículos)?
            if cve_sat=='78101803':
                return 'FLETE_TER_N', 'Retención de IVA/ cve SAT: T. vehículos'
            else:
                # ¿Cve = 78141500 (Serv. org. transp.)?
                if cve_sat=='78141500':
                    # Palabra clave: Cruce
                    if palabras_clave.find('CRUCE')>=0:
                        return 'CRUCE_FRONTERA_N', 'Retención de IVA/ cve SAT: Serv. org. transp.'
                    # ¿Flete  o sin palabras clave (Desc.)?
                    elif palabras_clave.find('FLETE')>=0 or palabras_clave=='[Sin palabras clave]':
                        return 'FLETE_TER_N', 'Retención de IVA/ cve SAT: Serv. org. transp.'
                    else:
                        return 'INDETERMINADO', '(!) Retención de IVA/ cve SAT: Serv. org. transp.'
                # ¿Cve = 76122401 (Tarifa sobreestadía)?
                elif cve_sat=='76122401':
                    return 'EST_DES_N', 'Retención de IVA/ cve SAT: Tarifa sobreestadía'
                # ¿Cve = 78121601 (Carga y des. de merc.)?
                elif cve_sat=='78121601':
                    return 'MAN_CAR_N', 'Retención de IVA/ cve SAT: Carga y descarga de mercancías'
                # ¿Cve = No existe en el catálogo?
                elif cve_sat in CVES_GEN:
                    # ¿Descarga (Desc.)?
                    if palabras_clave.find('DESCARGA')>=0:
                        return 'MAN_DES_N', 'Retención de IVA/ cve SAT: No existe en el catálogo'
                    # ¿Demoras (Desc.)?
                    elif palabras_clave.find('DEMORAS')>=0:
                        return 'DEM_CAR_N', 'Retención de IVA/ cve SAT: No existe en el catálogo'
                    else:
                        return 'INDETERMINADO', '(!) Retención de IVA/ cve SAT: No existe en el catálogo'
                else:
                    return 'INDETERMINADO', '(!) Retención de IVA/ cve SAT: No es de transporte'
        else:
            # Asignación mediante tabla
            return cves_prod_no_transp_sin_ret(cve_sat, palabras_clave,asign_table)