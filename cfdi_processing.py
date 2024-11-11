from funciones_prev import generar_diccionarios
from cfdi_inspection import read_cfdi_list, load_xsd_data
from file_management import get_xml_files_from_zip
from config import NODOS, XSD_PATHS, VERSIONES, ATRIBUTOS_PREDET
import pandas as pd
import xml.etree.ElementTree as ET
from zipfile import ZipFile

def conceptos_cartaporte(zip_xmls : ZipFile)-> pd.DataFrame:
    """Genera un DataFrame con el desglose de los conceptos y atributos de carta porte de un archivo ZIP con XML's de CFDI"""
    xml_files = get_xml_files_from_zip(zip_xmls)
    cartasporte = read_cartaporte(xml_files)
    conceptos = conceptos_df(read_conceptos(xml_files))
    return conceptos.merge(cartasporte, on='UUID', how='left')

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
            tree = ET.parse(archivo)
            root = tree.getroot()
            nombre = archivo
            nombre = nombre.replace(".xml","")
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