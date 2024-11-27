from funciones_prev import generar_diccionarios
from cfdi_inspection import read_cfdi_list, load_xsd_data
from file_management import get_xml_files_from_zip
from asignacion_producto import analisis_descripcion, asign_cve_prod_sap
from config import CAMPOS_CCP, NODOS, XSD_PATHS, VERSIONES, ATRIBUTOS_PREDET, PATH_CVES_NO_TRANSP_SIN_RET, PATH_BASE_PROV
import pandas as pd
import xml.etree.ElementTree as ET
import lxml.etree as etree

def generar_plantilla(zip_xmls)-> pd.DataFrame:
    """Genera un DataFrame con la plantilla para carga de facturas a SAP"""
    # leer los archivos xml y generamos el desglose de conceptos y cruce con carta porte
    facturas = conceptos_cartaporte(zip_xmls)
    # Generamos columnas de base de retención  y traslado de IVA
    facturas['Base IVA 16% Traslado'] = facturas.apply(lambda x: obtener_base(x, 0.16, 'Precio neto', 'Importe de impuesto'), axis=1)
    facturas['Base IVA 4% Retencion'] = facturas.apply(lambda x: obtener_base(x, 0.04, 'Base individual retencion', 'Importe de retencion'), axis=1)
    # realizamos el análisis de la descripción
    facturas = analisis_descripcion(facturas)
    # Cargamos la tabla de asignación de productos
    asign_table = pd.read_excel(PATH_CVES_NO_TRANSP_SIN_RET)
    # asignamos la clave de producto
    facturas[['ID de producto','Observación asignación de producto']] = facturas.apply(lambda x: asign_cve_prod_sap(x, asign_table), axis=1, result_type='expand')
    # asignamos la clave de retención
    facturas['Clave retención'] = facturas.apply(cve_retencion, axis=1)
    # asignamos la clave de proveedor
    base_prov = pd.read_excel(PATH_BASE_PROV)
    facturas = facturas.merge(base_prov, on='RFC', how='left')
    return facturas

def conceptos_cartaporte(zip_xmls)-> pd.DataFrame:
    """Genera un DataFrame con el desglose de los conceptos y atributos de carta porte de un archivo ZIP con XML's de CFDI"""
    xml_files = get_xml_files_from_zip(zip_xmls)
    cartasporte = read_cartaporte(xml_files)
    conceptos = conceptos_df(read_conceptos(xml_files))
    # emisor = read_emisor(xml_files)
    if cartasporte.empty:
        cartasporte = pd.DataFrame(columns=ATRIBUTOS_PREDET['cartaporte']['CartaPorte']+['UUID'])
    df = conceptos.merge(cartasporte, on='UUID', how='left')
    # df = df.merge(emisor, on='UUID', how='left')
    df['Tiene CCP'] = df['Version'].notnull()

    return df
    # return conceptos

def obtener_base(row, tasa, col_base:str, col_impuesto:str):
    """Comprueba que una base corresponda a una tasa determinada.
    Si la base corresponde a la tasa, regresa la base, de lo contrario regresa 0"""
    base = float(row[col_base])
    impuesto = float(row[col_impuesto])
    if base == 0:
        return 0
    elif round(impuesto*100/base) == tasa*100: # Se multiplica por 100 para evitar errores de redondeo
        return base
    else:
        return 0

def cve_retencion(row):
    """Asigna la clave de retención a una fila de un DataFrame"""
    iva_ret_4 = row['Base IVA 4% Retencion']
    iva_16 = row['Base IVA 16% Traslado']
    producto = row['ID de producto']

    if producto == 'FLETE_TER_N':
        if iva_ret_4 > 0:
            return 'A3V'
        else:
            return 'G1I'
    else:
        if iva_ret_4 > 0:
            return None
        else:
            return None # Revisar si se debe asignar una clave de retención
            

def read_cartaporte(xml_list: list)-> pd.DataFrame:
    xsd_data = load_xsd_data(nodos=NODOS, xsd_paths=XSD_PATHS, versiones=VERSIONES)
    data = read_cfdi_list(
        xml_paths=xml_list,
        nodos=NODOS,
        atributos=ATRIBUTOS_PREDET,
        xsd_data=xsd_data,
        tipos=['cartaporte'],
    )
    # Unpack the data
    data = [ccp['CartaPorte'] for register in data  for _, ccp in register.items() if ccp is not None]
    data = [lista[0] for lista in data if len(lista)>0]
    return pd.DataFrame(data)

def read_emisor(xml_list: list)-> pd.DataFrame:            
    xsd_data = load_xsd_data(nodos=NODOS, xsd_paths=XSD_PATHS, versiones=VERSIONES)
    data = read_cfdi_list(
        xml_paths=xml_list,
        nodos={'cfdi': ['Emisor',]},
        atributos=ATRIBUTOS_PREDET,
        xsd_data=xsd_data,
        tipos=['cfdi'],
    )
    # Unpack the data
    data = [line['Emisor'] for register in data  for _, line in register.items() if line is not None]
    data = [lista[0] for lista in data if len(lista)>0]
    data = pd.DataFrame(data)
    # Nombre de las columnas
    data.rename(columns={'Rfc':'RFC Emisor','Nombre':'Nombre Emisor'}, inplace=True)
    return data

def conceptos_df(lista)-> pd.DataFrame:

    df = pd.DataFrame(lista, columns = ["Nombre del archivo",
                                    "Fecha",
                                    "Tipo de comprobante",
                                    "Moneda",
                                    "RFC",
                                    "Clave de producto o servicio",
                                    "Descripcion",
                                    "Precio neto",
                                    "Tasa o cuota IVA",
                                    "Importe de impuesto", 
                                    "Base individual retencion",
                                    "Tasa o cuota retencion",
                                    "Importe de retencion",
                                    "UUID"])

    #Filtro para crear la columna con el código de retención
    df.loc[df["Tasa o cuota retencion"] == "0.012500|0.04|", "Clave retencion"] = "A11A"
    df.loc[df["Tasa o cuota retencion"] == "0.04|0.012500|", "Clave retencion"] = "A11A"
    df.loc[df["Tasa o cuota retencion"] == "0.040000|0.012500|", "Clave retencion"] = "A11A"
    df.loc[df["Tasa o cuota retencion"] == "0.012500|0.040000|", "Clave retencion"] = "A11A"
    df.loc[df["Tasa o cuota retencion"] == "0.012500|", "Clave retencion"] = "A12B"
    df.loc[df["Tasa o cuota retencion"] == "0.040000|", "Clave retencion"] = "A3V"
    df.loc[df["Tasa o cuota retencion"  ] == 0, "Clave retencion"] = ""

    # #Filtro para LAR MEX
    # df.loc[(df["RFC"] == "TLM7201085N4") & (df["Tasa o cuota IVA"] != "0.160000"), "Clave retencion"] = "G1I"

    #Se crea la columna de tipo de documento
    df.loc[df["Tipo de comprobante"] == "I", "Tipo de documento"] = "Factura"
    df.loc[df["Tipo de comprobante"] == "E", "Tipo de documento"] = "Nota de crédito"


    #Se crea la columna donde extrar el número de servicio según la descripción
    df["Servicio"] = df["Descripcion"].str.extract(r"(\d{2}-\d{6})")

    #Crea el número de posición dentro de la misma factura
    df["Posicion"] = df.groupby("Nombre del archivo").cumcount() + 1

    #Crea la columna Tipo de asignacion
    df["Tipo de asignacion"] = "CC"

    #Crea la columna Empresa compradora
    df["Empresa compradora"] = "MLG1000"

    #Crea la columna cantidad
    df["Cantidad"] = 1

    return(df)

def read_conceptos(nombres_archivos: list[str])-> list:
    item = []

    for archivo in nombres_archivos:

            #Lectura del xml
            try:
                archivo.seek(0) # Asegurarse de que el archivo esté al inicio
                tree = etree.parse(archivo)
            except Exception as e:
                print(f"Error al leer el archivo {archivo}: {e}")
                continue
            root = tree.getroot()
            nombre = archivo.name
            nombre = nombre.replace(".xml","")
            nombre = nombre.split("/")[-1]
            nodo = generar_diccionarios(root)
            
            #Se saca la fecha
            Fecha = root.attrib["Fecha"]

            #Se lee el atributo de tipo de comprobante del xml
            TipoDeComprobante = root.attrib["TipoDeComprobante"]

            #Hace filtro para solo trabajar con archivos de ingresos y egresos
            if TipoDeComprobante == "T":
                pass

            else:
                #Se empieza a extraer el atributo de Moneda y Rfc
                Moneda = root.attrib["Moneda"]
                Rfc = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Emisor")].attrib["Rfc"]

                #Genera los diccionarios para revisión de nodos para bases e impuestos individuales
                nodo_conceptos = generar_diccionarios(root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Conceptos")])
                nodo_impuestos = generar_diccionarios(root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Conceptos")][list(nodo_conceptos.values()).index("{http://www.sat.gob.mx/cfd/4}Concepto")])
                try:
                    nodo_impuesto = generar_diccionarios(root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Conceptos")][list(nodo_conceptos.values()).index("{http://www.sat.gob.mx/cfd/4}Concepto")][list(nodo_impuestos.values()).index("{http://www.sat.gob.mx/cfd/4}Impuestos")])
                except:
                    nodo_impuesto = []
                nodo_timbre = generar_diccionarios(root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Complemento")])
            
                #Extracción de UUID
                UUID = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Complemento")][list(nodo_timbre.values()).index("{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital")].attrib["UUID"]

                #Extración de la clave de producto o servicio y la descipción
                for concepto in root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Conceptos")]:
                    ClaveProdServ = concepto.attrib["ClaveProdServ"]
                    Descripcion = concepto.attrib["Descripcion"]

                    #Extrae la base, tasa e importe del iva
                    try:
                        for base in concepto[list(nodo_impuestos.values()).index("{http://www.sat.gob.mx/cfd/4}Impuestos")][list(nodo_impuesto.values()).index("{http://www.sat.gob.mx/cfd/4}Traslados")]:
                            base_individual_iva = base.attrib["Base"]
                            TasaOCuota = base.attrib["TasaOCuota"]
                            Importe_iva = base.attrib["Importe"]

                    #Extrae la base, tasa e importe de la retencion     
                        try:
                            TasaOCuota_retencion = ""
                            for retencion in concepto[list(nodo_impuestos.values()).index("{http://www.sat.gob.mx/cfd/4}Impuestos")][list(nodo_impuesto.values()).index("{http://www.sat.gob.mx/cfd/4}Retenciones")]:
                                base_individual_retencion = retencion.attrib["Base"]
                                TasaOCuota_retencion = retencion.attrib["TasaOCuota"] + "|" + TasaOCuota_retencion
                                Importe_retencion = retencion.attrib["Importe"]                    
                                
                        except:
                            base_individual_retencion = 0
                            TasaOCuota_retencion = 0
                            Importe_retencion = 0

                    except:
                        #Revisar este except a lo mejor se tiene que corregir
                        base_individual_iva = concepto.attrib["Importe"]
                        TasaOCuota = 0
                        Importe_iva = 0 


                                            #Extrae la base, tasa e importe de la retencion     
                        try:
                            TasaOCuota_retencion = ""
                            for retencion in concepto[list(nodo_impuestos.values()).index("{http://www.sat.gob.mx/cfd/4}Impuestos")][list(nodo_impuesto.values()).index("{http://www.sat.gob.mx/cfd/4}Retenciones")]:
                                base_individual_retencion = retencion.attrib["Base"]
                                TasaOCuota_retencion = retencion.attrib["TasaOCuota"] + "|" + TasaOCuota_retencion
                                Importe_retencion = retencion.attrib["Importe"]                    
                                
                        except:
                            base_individual_retencion = 0
                            TasaOCuota_retencion = 0
                            Importe_retencion = 0

                    item.append((nombre,
                                    Fecha,
                                    TipoDeComprobante,
                                    Moneda,
                                    Rfc,
                                    ClaveProdServ,
                                    Descripcion,
                                    base_individual_iva,
                                    TasaOCuota,
                                    Importe_iva,
                                    base_individual_retencion,
                                    TasaOCuota_retencion,
                                    Importe_retencion,
                                    UUID))


    #print(item)para 
    return(item)