import xml.etree.ElementTree as ET
import pandas as pd
import io
import zipfile


def generar_diccionarios(root):
    nodo = {}
    contador = 0

    try:
        for nodos in root:
            nodo[str(contador)] = nodos.tag
            contador +=1
        return(nodo)
    
    except:
        return()


def lectura_xml(nombre_archivo):
    item = []

    for archivo in nombre_archivo:

            #Lectura del xml
            tree = ET.parse(archivo)
            root = tree.getroot()
            nombre = archivo.name
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


def generar_reporte(lista):

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

    #Filtro para LAR MEX
    df.loc[(df["RFC"] == "TLM7201085N4") & (df["Tasa o cuota IVA"] != "0.160000"), "Clave retencion"] = "G1I"

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
    #df.to_excel("prueba.xlsx", index = False)

def descarga (df):
    
    salida = io.BytesIO()
    with pd.ExcelWriter(salida, engine = "openpyxl") as writer:
        df.to_excel(writer, index = False, sheet_name = "XML")

    salida.seek(0)

    return(salida)


#Revisar
def unzip (uploaded_file):

    #Lee el contenido del archivo ZIP
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:

        #Enlista los archivos en el ZIP
        file_names = zip_ref.namelist()

    return(file_names)

def desglose_xml(rutas):
    item = []

    for ruta in rutas:
        
        #Lectura del xml
        tree = ET.parse(ruta)
        root = tree.getroot()
        nombre = ruta.name
        nombre = nombre.replace(".xml","")
        nodo = generar_diccionarios(root)

        #Saca el tipo de comprobante para filtrar
        TipoDeComprobante = root.attrib["TipoDeComprobante"]

        if TipoDeComprobante == "P":
            pass
        
        else:
            #Lee datos del nodo Comprobante
            Version = root.attrib["Version"]
            try:
                Serie = root.attrib["Serie"]
            except:
                Serie = ""
            Folio = root.attrib["Folio"]
            Fecha = root.attrib["Fecha"]
            MetodoPago = root.attrib["MetodoPago"]
            FormaPago = root.attrib["FormaPago"]
            Moneda = root.attrib["Moneda"]
            Exportacion = root.attrib["Exportacion"]

            #Lee datos del nodo CfdiRelacionado
            try:
                TipoRelacion = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}CfdiRelacionados")].attrib["TipoRelacion"]
                UUID_relacionado = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}CfdiRelacionados")][0].attrib["UUID"]

            except:
                TipoRelacion = ""
                UUID_relacionado = ""

            #Lee datos del nodo Emisor
            Rfc_emisor = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Emisor")].attrib["Rfc"]
            Nombre_emisor = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Emisor")].attrib["Nombre"]
            RegimenFiscal = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Emisor")].attrib["RegimenFiscal"]

            #Lee datos del nodo Receptor
            DomicilioFiscalReceptor = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Receptor")].attrib["DomicilioFiscalReceptor"]
            Rfc_receptor = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Receptor")].attrib["Rfc"]
            Nombre_receptor = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Receptor")].attrib["Nombre"]
            RegimenFiscalReceptor = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Receptor")].attrib["RegimenFiscalReceptor"]
            UsoCFDI = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Receptor")].attrib["UsoCFDI"]


            #Genera los diccionarios de los diferentes nodos
            nodo_conceptos = generar_diccionarios(root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Conceptos")])
            nodo_impuestos = generar_diccionarios(root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Conceptos")][list(nodo_conceptos.values()).index("{http://www.sat.gob.mx/cfd/4}Concepto")])
            try:
                nodo_impuesto = generar_diccionarios(root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Conceptos")][list(nodo_conceptos.values()).index("{http://www.sat.gob.mx/cfd/4}Concepto")][list(nodo_impuestos.values()).index("{http://www.sat.gob.mx/cfd/4}Impuestos")])
            except:
                nodo_impuesto = []
            nodo_timbre = generar_diccionarios(root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Complemento")])

            #Lee los datos de complemento
            try: 
                Carta_porte_version = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Complemento")][list(nodo_timbre.values()).index("{http://www.sat.gob.mx/CartaPorte31}CartaPorte")].attrib["Version"]
                Carta_porte = "Si"
            
            except:
                Carta_porte = "No"
                Carta_porte_version = "Sin carta porte"

            UUID = root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Complemento")][list(nodo_timbre.values()).index("{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital")].attrib["UUID"]
            
            #Lee datos del nodo conceptos
            for concepto in root[list(nodo.values()).index("{http://www.sat.gob.mx/cfd/4}Conceptos")]:
                ClaveProdServ = concepto.attrib["ClaveProdServ"]
                Descripcion = concepto.attrib["Descripcion"]
                Importe = concepto.attrib["Importe"]
                ObjetoImp = concepto.attrib["ObjetoImp"]


                #Lee datos de base iva
                try:
                        for base in concepto[list(nodo_impuestos.values()).index("{http://www.sat.gob.mx/cfd/4}Impuestos")][list(nodo_impuesto.values()).index("{http://www.sat.gob.mx/cfd/4}Traslados")]:
                            Base_iva = base.attrib["Base"]
                            Impuesto_iva = base.attrib["Impuesto"]
                            TasaOCuota = base.attrib["TasaOCuota"]
                            Importe_iva = base.attrib["Importe"]

                                        #Lee datos de base retencion
                        try:
                            Base_retencion = ""
                            Impuesto_retencion = ""
                            TasaOCuota_retencion = ""
                            Importe_retencion = ""

                            for retencion in concepto[list(nodo_impuestos.values()).index("{http://www.sat.gob.mx/cfd/4}Impuestos")][list(nodo_impuesto.values()).index("{http://www.sat.gob.mx/cfd/4}Retenciones")]:
                                Base_retencion = retencion.attrib["Base"] + "|" + Base_retencion
                                Impuesto_retencion = retencion.attrib["Impuesto"] + "|" + Impuesto_retencion
                                TasaOCuota_retencion = retencion.attrib["TasaOCuota"] + "|" + TasaOCuota_retencion
                                Importe_retencion = retencion.attrib["Importe"] + "|" + Importe_retencion

                        except:
                                Base_retencion = ""
                                Impuesto_retencion = ""
                                TasaOCuota_retencion = ""
                                Importe_retencion = ""

                except:
                    Base_iva = ""
                    Impuesto_iva = ""
                    TasaOCuota = ""
                    Importe_iva = ""

                    try:
                            TasaOCuota_retencion = ""
                            for retencion in concepto[list(nodo_impuestos.values()).index("{http://www.sat.gob.mx/cfd/4}Impuestos")][list(nodo_impuesto.values()).index("{http://www.sat.gob.mx/cfd/4}Retenciones")]:
                                Base_retencion = retencion.attrib["Base"] + "|" + Base_retencion
                                Impuesto_retencion = retencion.attrib["Impuesto"] + "|" + Impuesto_retencion
                                TasaOCuota_retencion = retencion.attrib["TasaOCuota"] + "|" + TasaOCuota_retencion
                                Importe_retencion = retencion.attrib["Importe"] + "|" + Importe_retencion                
                                
                    except:
                                Base_retencion = ""
                                Impuesto_retencion = ""
                                TasaOCuota_retencion = ""
                                Importe_retencion = ""


                item.append((nombre,
                        Version,
                        Serie,
                        Folio,
                        Fecha,
                        MetodoPago,
                        FormaPago,
                        Moneda,
                        TipoDeComprobante,
                        Exportacion,
                        TipoRelacion,
                        UUID_relacionado,
                        Rfc_emisor,
                        Nombre_emisor,
                        RegimenFiscal,
                        DomicilioFiscalReceptor,
                        Rfc_receptor,
                        Nombre_receptor,
                        RegimenFiscalReceptor,
                        UsoCFDI,
                        ClaveProdServ,
                        Descripcion,
                        Importe, 
                        ObjetoImp,
                        Base_iva,
                        Impuesto_iva,
                        TasaOCuota,
                        Importe_iva,
                        Base_retencion,
                        Impuesto_retencion,
                        TasaOCuota_retencion,
                        Importe_retencion,
                        Carta_porte,
                        Carta_porte_version,
                        UUID))

    return(item)

def validacion (item, ecomp):
    df_ecom = pd.read_excel(ecomp, usecols = ["Estatus", "UUID"], skiprows = 4)
    df = pd.DataFrame(item, columns = ["Nombre",
                        "Version",
                        "Serie",
                        "Folio",
                        "Fecha",
                        "Metodo_de_pago",
                        "Forma_de_pago",
                        "Moneda",
                        "Tipo_de_comprobante",
                        "Exportacion",
                        "TipoRelacion",
                        "UUID_relacionado",
                        "Rfc_emisor",
                        "Nombre_emisor",
                        "Regimen_fiscal_emisor",
                        "Domicilio_fiscal_receptor",
                        "Rfc_receptor",
                        "Nombre_receptor",
                        "Regimen_fiscal_receptor",
                        "Uso_de_CFDI",
                        "Clave_ProdServ",
                        "Descripcion",
                        "Importe", 
                        "Objeto_de_impuesto",
                        "Base_IVA",
                        "Impuesto_IVA",
                        "Tasa_o_cuota_IVA",
                        "Importe_IVA",
                        "Base_retencion",
                        "Impuesto_retencion",
                        "Tasa_o_cuota_retencion",
                        "Importe_retencion",
                        "Carta_porte",
                        "Carta_porte_version",
                        "UUID"])
    
    df["Observaciones"] = ""

    #Regla para solo aceptar el RFC de Multilog
    df.loc[(df["Rfc_receptor"] != "MIN1002195D0"), "Observaciones"] += "RFC receptor no es el de MLG| "

    #Regla para convinacion metodo de pago y forma de pago
    df.loc[((df["Metodo_de_pago"] != "PUE") & (df["Forma_de_pago"] == "03")) | ((df["Metodo_de_pago"] != "PPD") & (df["Forma_de_pago"] == "99")), "Observaciones"] += "Error en metodo y forma de pago| "
    
    #Regla para versión de CFDI
    df.loc[(df["Version"] != "4.0"), "Observaciones"] += "Version CFDI diferente a 4.0| "
    
    #Regla para tipo de comprobante
    df.loc[(df["Tipo_de_comprobante"] != "I") & (df["Tipo_de_comprobante"] != "E") & (df["Tipo_de_comprobante"] != "P"), "Observaciones"] += "Tipo de comprobante no aceptado| "

    #Regla para regimen fiscal de Multilog
    df.loc[(df["Regimen_fiscal_receptor"] != "601"), "Observaciones"] += "Regimen fiscal receptor no es el de MLG| "

    #Regla para uso de CFDI
    df.loc[(df["Uso_de_CFDI"] != "G03") & (df["Tipo_de_comprobante"] != "E"), "Observaciones"] += "Uso de CFDI no aceptado| "

    #Regla para versión de complemento de carta porte
    df.loc[(df["Carta_porte"] == "Si") & (df["Carta_porte_version"] != "3.1"), "Observaciones"] += "Version Carta Porte diferente a 3.1| "

    #Regla para claves de impuestos
    df.loc[((df["Impuesto_IVA"] != "002") & (df["Impuesto_IVA"] != "003")) & (df["Objeto_de_impuesto"] != "01"), "Observaciones"] += "Clave de impuesto no aceptado| "

    #Regla para que documentos tipo E tengan un documento relacionado
    df.loc[(df["Tipo_de_comprobante"] == "E") & (df["TipoRelacion"] == ""), "Observaciones"] += "NC sin documento relacionado| "

    #Regla para que las NC solo puedan tener relación 01
    df.loc[(df["Tipo_de_comprobante"] == "E") & ((df["TipoRelacion"] != "01") & (df["TipoRelacion"] != "")), "Observaciones"] += "NC con clave de relación incorrecta| "

    #Regla para delimitar solamente claves seleccionadas
    df.loc[(df["Clave_ProdServ"] != "01010101") &
           (df["Clave_ProdServ"] != "13111201") &
           (df["Clave_ProdServ"] != "24112800") &
           (df["Clave_ProdServ"] != "24112901") &
           (df["Clave_ProdServ"] != "24141504") &
           (df["Clave_ProdServ"] != "24141511") &
           (df["Clave_ProdServ"] != "31181701") &
           (df["Clave_ProdServ"] != "31201500") &
           (df["Clave_ProdServ"] != "43233204") &
           (df["Clave_ProdServ"] != "46171600") &
           (df["Clave_ProdServ"] != "72102103") &
           (df["Clave_ProdServ"] != "72141700") &
           (df["Clave_ProdServ"] != "72151802") &
           (df["Clave_ProdServ"] != "76121600") &
           (df["Clave_ProdServ"] != "76122401") &
           (df["Clave_ProdServ"] != "76122403") &
           (df["Clave_ProdServ"] != "78101500") &
           (df["Clave_ProdServ"] != "78101502") &
           (df["Clave_ProdServ"] != "78101700") &
           (df["Clave_ProdServ"] != "78101702") &
           (df["Clave_ProdServ"] != "78101800") &
           (df["Clave_ProdServ"] != "78101801") &
           (df["Clave_ProdServ"] != "78101802") &
           (df["Clave_ProdServ"] != "78101803") &
           (df["Clave_ProdServ"] != "78101804") &
           (df["Clave_ProdServ"] != "78101805") &
           (df["Clave_ProdServ"] != "78101806") &
           (df["Clave_ProdServ"] != "78102200") &
           (df["Clave_ProdServ"] != "78102203") &
           (df["Clave_ProdServ"] != "78102204") &
           (df["Clave_ProdServ"] != "78102205") &
           (df["Clave_ProdServ"] != "78121500") &
           (df["Clave_ProdServ"] != "78121502") &
           (df["Clave_ProdServ"] != "78121600") &
           (df["Clave_ProdServ"] != "78121601") &
           (df["Clave_ProdServ"] != "78121602") &
           (df["Clave_ProdServ"] != "78121603") &
           (df["Clave_ProdServ"] != "78131600") &
           (df["Clave_ProdServ"] != "78131601") &
           (df["Clave_ProdServ"] != "78131701") &
           (df["Clave_ProdServ"] != "78131702") &
           (df["Clave_ProdServ"] != "78131800") &
           (df["Clave_ProdServ"] != "78131801") &
           (df["Clave_ProdServ"] != "78131804") &
           (df["Clave_ProdServ"] != "78141500") &
           (df["Clave_ProdServ"] != "78141501") &
           (df["Clave_ProdServ"] != "78141502") &
           (df["Clave_ProdServ"] != "78141504") &
           (df["Clave_ProdServ"] != "78141600") &
           (df["Clave_ProdServ"] != "78141700") &
           (df["Clave_ProdServ"] != "78141703") &
           (df["Clave_ProdServ"] != "78141800") &
           (df["Clave_ProdServ"] != "78141801") &
           (df["Clave_ProdServ"] != "78141804") &
           (df["Clave_ProdServ"] != "78141900") &
           (df["Clave_ProdServ"] != "78141902") &
           (df["Clave_ProdServ"] != "78181702") &
           (df["Clave_ProdServ"] != "80151601") &
           (df["Clave_ProdServ"] != "80151602") &
           (df["Clave_ProdServ"] != "80151605") &
           (df["Clave_ProdServ"] != "81102500") &
           (df["Clave_ProdServ"] != "81141600") &
           (df["Clave_ProdServ"] != "81141601") &
           (df["Clave_ProdServ"] != "81141604") &
           (df["Clave_ProdServ"] != "84111506") &
           (df["Clave_ProdServ"] != "84131607") &
           (df["Clave_ProdServ"] != "92121500") &
           (df["Clave_ProdServ"] != "92121502") &
           (df["Clave_ProdServ"] != "92121504") &
           (df["Clave_ProdServ"] != "92121701") &
           (df["Clave_ProdServ"] != "93171702"), "Observaciones"] += "Clave de producto o serv. no aceptado| "
     
    #Reglas para clave con retención
    df.loc[((df["Clave_ProdServ"] == "01010101") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "13111201") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "24112800") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "24112901") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "24141504") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "24141511") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "31181701") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "31201500") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "43233204") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "46171600") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "72102103") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "72141700") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "72151802") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "76121600") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "76122401") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "76122403") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78101500") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78101502") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78101700") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78101702") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78101800") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78101801") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78101802") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78101803") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78101804") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78101805") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78101806") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78102200") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78102203") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78102204") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78102205") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78121500") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78121502") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78121600") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78121601") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78121602") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78121603") & (df["Tasa_o_cuota_retencion"] != "0.040000|")) |
           ((df["Clave_ProdServ"] == "78131600") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78131601") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78131701") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78131702") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78131800") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78131801") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78131804") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141500") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141501") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141502") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141504") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141600") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141700") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141703") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141800") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141801") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141804") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141900") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78141902") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "78181702") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "80151601") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "80151602") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "80151605") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "81102500") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "81141600") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "81141601") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "81141604") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "84111506") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "84131607") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "92121500") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "92121502") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "92121504") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "92121701") & (df["Tasa_o_cuota_retencion"] != "")) |
           ((df["Clave_ProdServ"] == "93171702") & (df["Tasa_o_cuota_retencion"] != "")), "Observaciones"] += "Retención incorrecta para clave de prod. y serv.| "


    #Reglas para objeto de impuesto
    df.loc[((df["Clave_ProdServ"] == "01010101") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "13111201") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "24112800") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "24112901") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "24141504") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "24141511") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "31181701") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "31201500") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "43233204") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "46171600") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "72102103") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "72141700") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "72151802") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "76121600") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "76122401") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "76122403") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78101500") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78101700") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78101800") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78101801") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78101802") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78101803") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78101804") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78101805") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78102200") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78102203") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78102204") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78102205") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78121500") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78121502") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78121600") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78121601") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78121602") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78121603") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78131600") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78131601") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78131701") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78131702") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78131800") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78131801") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78131804") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141500") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141501") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141502") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141504") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141600") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141700") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141703") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141800") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141801") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141804") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141900") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78141902") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "78181702") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "80151601") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "80151602") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "80151605") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "81102500") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "81141600") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "81141601") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "81141604") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "84111506") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "84131607") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "92121500") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "92121502") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "92121504") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "92121701") & (df["Objeto_de_impuesto"] != "02")) |
           ((df["Clave_ProdServ"] == "93171702") & (df["Objeto_de_impuesto"] != "02")), "Observaciones"] += "Objeto de impuesto incorrecto para clave de prod. y serv.| "


    #Reglas para carta porte
    df.loc[((df["Clave_ProdServ"] == "78101500") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101502") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101700") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101702") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101800") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101802") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101803") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101804") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101805") & (df["Carta_porte"] != "Si")) |
           ((df["Clave_ProdServ"] == "78101806") & (df["Carta_porte"] != "Si")) |    
           ((df["Clave_ProdServ"] == "78121603") & (df["Carta_porte"] != "Si")), "Observaciones"] += "Carta Porte no anexa para clave de prod. y serv.| "

    df2 = df.merge(df_ecom, how = "left")

    return(df2)