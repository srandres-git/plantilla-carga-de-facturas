"""
FUNCIONES DE LECTURA DE CFDI
"""
# _____________________________________________________________
from time import sleep
import lxml.etree as etree
import xml.etree.ElementTree as ET
import re
import os
from datetime import datetime
from file_management import export_to_excel, get_xml_files, path_m_date, read_template
from exception_handling import CFDIAttributeNotFound, CFDIInspectionError, CFDINoAttributesError, CFDINodeNotFound, FileNotFoundError, InvalidXSDPathError, XMLParseError, XSDParseError
from config import DEFAULT_DELAY
# _____________________________________________________________
# FUNCIONES DE INSPECCIÓN DE CFDI

def extract_common_attributes(root: etree.Element, file_path: str) -> dict[str, str]:
    """
    Extrae los atributos comunes de un CFDI: UUID, RFC emisor, Nombre emisor, ruta del archivo, carpeta del archivo.
    """
    # Generamos los XPaths a los nodos de interés
    
    namespaces = root.nsmap
    # Agregar el namespace de TFD
    namespaces['tfd'] = 'http://www.sat.gob.mx/TimbreFiscalDigital'

    #emisor_xpath = generate_xpaths([('Emisor',)], namespaces, 'cfdi', deep=True)[('Emisor',)]
    tfd_xpath = generate_xpaths([('TimbreFiscalDigital',)], namespaces, 'tfd', deep=True)[('TimbreFiscalDigital',)]
    # Extraemos los valores de los nodos
    try:
        uuid = tfd_xpath(root)[0].get('UUID')
        if uuid is None or uuid == '':
            CFDIAttributeNotFound('UUID', file_path).show()
            uuid = None         
    except IndexError:
        CFDINodeNotFound('TimbreFiscalDigital', file_path).show()
        uuid = None
    # try:
    #     nodo_emisor = emisor_xpath(root)[0]
    #     try:
    #         rfc_emisor = nodo_emisor.get('Rfc')
    #         if rfc_emisor is None or rfc_emisor == '':
    #             CFDIAttributeNotFound('Emisor_RFC', file_path).show()
    #             rfc_emisor = None
    #     except AttributeError:
    #         CFDIAttributeNotFound('Emisor_RFC', file_path).show()
    #         rfc_emisor = None
    #     try:
    #         nombre_emisor = nodo_emisor.get('Nombre')
    #         if nombre_emisor is None or nombre_emisor == '':
    #             CFDIAttributeNotFound('Emisor_Nombre', file_path).show()
    #             nombre_emisor = None
    #     except AttributeError:
    #         CFDIAttributeNotFound('Emisor_Nombre', file_path).show()
    #         nombre_emisor = None
    # except IndexError:
    #     CFDINodeNotFound('Emisor', file_path).show()
    #     rfc_emisor = None
    #     nombre_emisor = None
    
    # Extraer la ruta y carpeta del archivo
    # cambiar '\\' por '/'
    #file_path = file_path.replace('\\', '/')
    # Extraer la carpeta del archivo
    #folder_path = os.path.dirname(file_path).split('/')[-1]
    # Fecha de modificación del archivo
    #file_m_date = path_m_date(file_path).strftime('%Y-%m-%d')
    
    common_attributes = {
        'UUID': uuid,
        #'Emisor_RFC': rfc_emisor,
        #'Emisor_Nombre': nombre_emisor,
        #'Ruta_Archivo': file_path,
        #'Fecha_Modificacion': file_m_date,
        #'Carpeta_Archivo': folder_path
    }

    return common_attributes

def extraer_elementos_atributos(
    root: etree.Element, # Elemento raíz del árbol XML 
    elementos_anidados: list[tuple[str, ...]],  # Tuplas con secuencias de elementos (padre, hijo, nieto, ...)
    atributos_por_elemento: dict[str, list[str]],  # Diccionario de atributos por elemento
    xpaths: dict[tuple[str, ...], etree.XPath],  # Diccionario de XPaths por elemento anidado
) -> dict[str, list[dict[str, str]]]:  # El retorno es un dict con listas de dicts
    """
    Extrae elementos y atributos anidados de un archivo XML basado en una lista de rutas de elementos y namespaces.

    :param xml_path: Ruta del archivo XML.
    :param elementos_anidados: Lista de tuplas que representan la secuencia de elementos (padre, hijo, nieto, ...).
    :param atributos_por_elemento: Diccionario que mapea elementos a listas de atributos.
    :param xpaths: Diccionario de XPaths por elemento anidado.
    :return: Diccionario que mapea cada elemento a una lista de diccionarios de atributos y sus valores.
    """

    # Diccionario para almacenar los resultados
    data = {}

    # Recorrer las tuplas de elementos anidados
    for ruta in elementos_anidados:
        # # Verificar si la tupla tiene un solo elemento (convertir a tupla de un solo elemento si es una cadena)
        # if isinstance(ruta, str):
        #     ruta = (ruta,)  
        # Extraer el último elemento (el que contiene los atributos)
        if isinstance(ruta, str):
            ultimo_elemento = ruta # Si es una cadena, el último elemento es la cadena misma
        else:
            ultimo_elemento = ruta[-1] # Si es una tupla, el último elemento es el último elemento de la tupla
               
        # Inicializar la lista para las ocurrencias del último elemento
        data[ruta] = []
        # Buscar los elementos anidados según la ruta construida
        for node in xpaths[ruta](root):
            # Diccionario para almacenar los atributos del último elemento
            datos_atributos = {}            
            # Iterar sobre los atributos de interés para este último elemento
            try:
                for atributo in atributos_por_elemento.get(ultimo_elemento, []):
                    # Obtener el valor del atributo y almacenarlo si existe
                    datos_atributos[atributo] = node.get(atributo)            
            except TypeError:
                CFDINoAttributesError(ruta).show()
            except AttributeError:
                CFDINoAttributesError(ruta).show()
            # Añadir el diccionario con los atributos al resultado para este elemento
            data[ruta].append(datos_atributos)    
    return data

def read_cfdi(
        xml_path: str, 
        nodos: dict[str, list[tuple[str, ...]]],# Diccionario de rutas de nodos por tipo de nodo 
                                                # {cfdi: [(), ()], cartaporte: [(), ()], ...}
        atributos: dict[str, dict[str, list[str]]], # Diccionario de atributos requeridos por tipo de nodo
        xsd_data: dict[str, dict[str, list[str]]],# {'cfdi4': {'required_elements': [], 'required_attributes': [], 'namespaces': [], 'xpaths': []}, ...}
        versiones: dict[str, str], # Diccionario de versiones de carta porte y cfdi
        tipos: list[str] = ['cfdi', 'cartaporte', 'tfd']): # Lista de tipos de nodo a extraer
    """Lee un archivo XML de una ruta y extrae los elementos y atributos requeridos para cada tipo de información:
        CFDI, carta porte y timbre fiscal digital."""
    # Parsear el archivo XML
    try:
        xml_path.seek(0) # Asegurarse de que el archivo esté al inicio
        tree = etree.parse(xml_path)
    except Exception as e:
        XMLParseError(xml_path, e).show()
        return None
    root = tree.getroot()

    data = {}
    # Extraer los elementos y atributos
    for tipo in tipos:
        # Si no hay versión de carta porte, no se extraen los nodos de carta porte
        if versiones[tipo] is None:
            data[tipo] = None
        else:
            try: nodes = nodos[tipo]
            except KeyError:
                CFDIInspectionError(f'No se encontraron nodos para {tipo}').show()
                data[tipo] = None
            try: attributes = atributos[tipo]
            except KeyError:
                CFDIInspectionError(f'No se encontraron atributos para {tipo}').show()
                data[tipo] = None
            try: xpaths = xsd_data[versiones[tipo]]['xpaths']
            except KeyError:
                CFDIInspectionError(f'No se encontró información de XSD para la versión {versiones[tipo]}').show()
                data[tipo] = None
            try:
                data[tipo] = extraer_elementos_atributos(root, nodes, attributes, xpaths)
            except Exception as e:
                CFDIInspectionError(f'Error al extraer información de {tipo} en {xml_path}').show()
                data[tipo] = None
                
    # Extraer atributos comunes
    common_attributes = extract_common_attributes(root, xml_path)
    # Añadir los atributos comunes a todos los nodos
    for tipo in tipos:
        if data[tipo] is not None:
            for _, atrib_list in data[tipo].items(): # nodo, lista de atributos
                for atrib_dict in atrib_list:
                    atrib_dict.update(common_attributes)
    del tree
    return data

def read_cfdi_list_gen(
        xml_paths: list[str],
        nodos: dict[str, list[tuple[str, ...]]],# Diccionario de rutas de nodos por tipo de nodo
                                                # {cfdi: [(), ()], cartaporte: [(), ()], ...}
        atributos: dict[str, dict[str, list[str]]], # Diccionario de atributos requeridos por tipo de nodo
        xsd_data: dict[str, dict[str, list[str]]],# {'cfdi4': {'required_elements': [], 'required_attributes': [], 'namespaces': [], 'xpaths': []}, ...}
        tipos: list[str] = ['cfdi', 'cartaporte', 'tfd'], # Lista de tipos de nodo a extraer
        update_progress_files: callable = lambda x,y: None
        ):
    """Generador. Lee una *lista* de archivos XML a partir de sus rutas y extrae los elementos y atributos requeridos para cada tipo de información:
        CFDI, carta porte y timbre fiscal digital."""
    # Recorrer las rutas de los archivos XML
    N = len(xml_paths)
    for i,xml_path in enumerate(xml_paths):
        # Extraer versión de CFDI y carta porte
        vers = get_cfdi_version(get_namespaces(xml_path))
        if vers['cfdi'] is None:
            continue
        else:
            data = read_cfdi(
                xml_path,
                nodos,
                atributos,
                xsd_data,
                vers,
                tipos
            )
            yield data
            del data
        update_progress_files(i+1, N)

def read_cfdi_list(
        xml_paths: list[str],
        nodos: dict[str, list[tuple[str, ...]]],# Diccionario de rutas de nodos por tipo de nodo
                                                # {cfdi: [(), ()], cartaporte: [(), ()], ...}
        atributos: dict[str, dict[str, list[str]]], # Diccionario de atributos requeridos por tipo de nodo
        xsd_data: dict[str, dict[str, list[str]]],# {'cfdi4': {'required_elements': [], 'required_attributes': [], 'namespaces': [], 'xpaths': []}, ...}
        tipos: list[str] = ['cfdi', 'cartaporte', 'tfd'], # Lista de tipos de nodo a extraer
        update_progress_files: callable = lambda x,y: None
        ):
    """Lee una *lista* de archivos XML a partir de sus rutas y extrae los elementos y atributos requeridos para cada tipo de información:
        CFDI, carta porte y timbre fiscal digital."""
    data_list = []
    for data in read_cfdi_list_gen(xml_paths, nodos, atributos, xsd_data, tipos, update_progress_files):
        data_list.append(data)
    return data_list

def explore_directory_gen(
        path: str,
        nodes: dict[str, list[tuple[str, ...]]],# Diccionario de rutas de nodos por tipo de nodo 
                                                # {cfdi: [(), ()], cartaporte: [(), ()], ...}
        attributes: dict[str, dict[str, list[str]]], # Diccionario de atributos requeridos por tipo de nodo
        xsd_data: dict[str, dict[str, list[str]]],# {'cfdi4': {'required_elements': [], 'required_attributes': [], 'namespaces': [], 'xpaths': []}, ...}
        types: list[str] = ['cfdi', 'cartaporte', 'tfd'],# Lista de tipos de nodo a extraer
        explore_subdirs: bool = False,# Indica si se deben explorar los subdirectorios
        folder_date_range: tuple[datetime, datetime] = None,# Rango de fechas para filtrar los directorios
        file_date_range: tuple[datetime, datetime] = None,# Rango de fechas para filtrar los archivos
        update_progress_files: callable = lambda x,y: None
        ):
    """Generador. Explora un directorio y extrae los datos de CFDI de los archivos XML que contiene."""
    # Obtener la lista de archivos XML
    xml_files = get_xml_files(
        path,
        explore_subdirs=explore_subdirs,
        folder_date_range=folder_date_range,
        file_date_range=file_date_range
    )
    # Extraer los datos de los archivos XML
    yield from read_cfdi_list_gen(
        xml_files,
        nodes,
        attributes,
        xsd_data,
        types,
        update_progress_files
    )

def explore_directories_gen(
        paths: list[str], # Lista de rutas de directorios
        nodes: dict[str, list[tuple[str, ...]]],# Diccionario de rutas de nodos por tipo de nodo 
                                                # {cfdi: [(), ()], cartaporte: [(), ()], ...}
        attributes: dict[str, dict[str, list[str]]], # Diccionario de atributos requeridos por tipo de nodo
        xsd_data: dict[str, dict[str, list[str]]],# {'cfdi4': {'required_elements': [], 'required_attributes': [], 'namespaces': [], 'xpaths': []}, ...}
        types: list[str] = ['cfdi', 'cartaporte', 'tfd'],# Lista de tipos de nodo a extraer
        explore_subdirs: bool = False,# Indica si se deben explorar los subdirectorios
        folder_date_range: tuple[datetime, datetime] = None,# Rango de fechas para filtrar los directorios
        file_date_range: tuple[datetime, datetime] = None,# Rango de fechas para filtrar los archivos
        wait_time: float = DEFAULT_DELAY ,# Tiempo de espera entre directorios):
        update_progress_folders: callable = lambda x,y: None,
        update_progress_files: callable = lambda x,y: None
        ):
    """Generador. Explora una lista de directorios y extrae los datos de CFDI de los archivos XML que contienen.
        Ejecuta función de actualización de progreso y hace una pausa entre cada directorio."""
    N = len(paths)
    for i,path in enumerate(paths):
        yield from explore_directory_gen(
            path,
            nodes,
            attributes,
            xsd_data,
            types,
            explore_subdirs,
            folder_date_range,
            file_date_range,
            update_progress_files
        )
        update_progress_folders(i+1, N,)
        sleep(wait_time)

def xml_reader(
        by_template: bool,
        template_path: str,
        directory_path: str, # Ruta del directorio raíz en caso de no usar plantilla
        export_path: str,
        nodes: dict[str, list[tuple[str, ...]]],# Diccionario de rutas de nodos por tipo de nodo
                                                # {cfdi: [(), ()], cartaporte: [(), ()], ...}
        attributes: dict[str, dict[str, list[str]]], # Diccionario de atributos requeridos por tipo de nodo
        xsd_data: dict[str, dict[str, list[str]]],# {'cfdi4': {'required_elements': [], 'required_attributes': [], 'namespaces': [], 'xpaths': []}, ...}
        types: list[str] = ['cfdi', 'cartaporte', 'tfd'],# Lista de tipos de nodo a extraer
        explore_subdirs: bool = False,# Indica si se deben explorar los subdirectorios
        folder_date_range: tuple[datetime, datetime] = None,# Rango de fechas para filtrar los directorios
        file_date_range: tuple[datetime, datetime] = None,# Rango de fechas para filtrar los archivos
        wait_time: float = DEFAULT_DELAY ,# Tiempo de espera entre directorios
        callback_progress_folders: callable = lambda x,y: None,
        callback_progress_files: callable = lambda x,y: None
    ):
    """Función principal para la lectura de archivos XML de CFDI y extracción de información."""
    # validamos que export_path, wait_time y types no estén vacíos      
    if by_template:
        # Leer plantilla de rutas
        paths = read_template(template_path)
        if paths is None:
            return None
        export_to_excel(
            explore_directories_gen(
                paths,
                nodes,
                attributes,
                xsd_data,
                types,
                explore_subdirs,
                folder_date_range,
                file_date_range,
                wait_time,
                update_progress_folders=callback_progress_folders,
                update_progress_files=callback_progress_files
            ),
            export_path,
            nodes
        )                
    else:
        # Explorar directorio raíz
        export_to_excel(
            explore_directory_gen(
                directory_path,
                nodes,
                attributes,
                xsd_data,
                types,
                explore_subdirs,
                folder_date_range,
                file_date_range,
                update_progress_files=callback_progress_files
            ),
            export_path,
            nodes
        )          

# _____________________________________________________________
# FUNCIONES DE ANÁLISIS DE XSD Y XML

def get_namespaces(xml_path: str) -> dict[str, str]:
    """Extraer los namespaces del documento XML."""
    try:
        # Intentar abrir y parsear el archivo XML
        xml_path.seek(0) # Asegurarse de que el archivo esté al inicio
        namespaces = dict([
            node for _, node in ET.iterparse(xml_path, events=['start-ns'])
        ])
        return namespaces
    except FileNotFoundError:
        FileNotFoundError(xml_path).show()
        return {}
    except ET.ParseError as parse_error:
        XMLParseError(xml_path, parse_error).show()
        return {}


def get_namespaces_from_root(root):
    # Extraer los namespaces del árbol ya parseado
    # Los namespaces están generalmente en los atributos del nodo raíz (xmlns)
    namespaces = {}
    for key, value in root.attrib.items():
        if key.startswith('xmlns:'):
            # Extraer el prefijo del namespace, después de 'xmlns:'
            prefix = key.split(':', 1)[1]
            namespaces[prefix] = value
        elif key == 'xmlns':
            # Este es el namespace por defecto, sin prefijo
            namespaces[''] = value
    return namespaces

def get_cfdi_version(namespaces: dict[str, str]) -> dict[str, str]:
    """Obtiene la versión de CFDI  y carta porte a partir de los namespaces del xml"""
    # 'cfdi': 'http://www.sat.gob.mx/cfd/4'
    try: 
        cfdi_ver = namespaces['cfdi'].split('/')[-1]
    except KeyError:
        cfdi_ver = None
        CFDIInspectionError('No se pudo encontrar el namespace de CFDI').show()
    if cfdi_ver is not None:
        cfdi_ver = 'cfdi'+cfdi_ver
        #  'cartaporte31': 'http://www.sat.gob.mx/CartaPorte31'
        # obtener la key de namspaces que contiene la palabra que hace match con 'cartaporte'
        cartaporte_match = [key for key in namespaces.keys() if re.search('cartaporte', key, re.IGNORECASE)]
        if len(cartaporte_match) > 0:
            cartaporte_ver = cartaporte_match[0]
        else:
            cartaporte_ver = None
        return {'cfdi': cfdi_ver, 'cartaporte': cartaporte_ver, 'tfd': 'tfd'} # por defecto la versión de TFD es 1.1
    return {'cfdi': None, 'cartaporte': None, 'tfd': None}

def get_required_attributes(element, namespaces, ns_name='xs'):
    required_attributes = []
    xpath = build_xpath(('complexType','attribute'), ns_name, deep=False)
    for attribute in element.xpath(xpath, namespaces=namespaces):
        if attribute.get('use') == 'required':
            required_attributes.append(attribute.get('name'))
    return required_attributes

def analizar_xsd(xsd_path:str):
    """Analiza un archivo XSD y extrae los elementos y atributos requeridos, así como los namespaces utilizados."""
    # Comprobar si el archivo XSD existe
    if not os.path.exists(xsd_path):
        InvalidXSDPathError(xsd_path).show_warning()
        return None
    # Parsear el esquema XSD
    try:
        xsd_tree = etree.parse(xsd_path)
    except Exception as e:
        XSDParseError(xsd_path, e).show_warning()
        return None

    root = xsd_tree.getroot()
    
    namespaces = root.nsmap
    required_elements = []
    required_attributes = {}

    # Recorrer los elementos del XSD
    for element in root.iter(f"{{{namespaces['xs']}}}element"):
        name = element.attrib.get('name')
        min_occurs = int(element.attrib.get('minOccurs','1'))  # minOccurs="1" por defecto es requerido
        if min_occurs >= 1:
            required_elements.append(name)
        
        # Recorrer los atributos requeridos del elemento
        required_attributes[name] = get_required_attributes(element, namespaces)

    return {'required_elements': required_elements, 
            'required_attributes': required_attributes, 
            'namespaces': namespaces}

def build_xpath(elemento_anidado, ns_name, deep=False)-> str:
    """Construye una cadena XPath para un elemento anidado con un namespace"""
    if isinstance(elemento_anidado, str):
        elemento_anidado = (elemento_anidado,)
    if deep:
        return '//'+'//'.join(f'{ns_name}:{elemento}' for elemento in elemento_anidado)
    return './'+'/'.join(f'{ns_name}:{elemento}' for elemento in elemento_anidado)

def generate_xpaths(rutas, namespaces, ns_name, deep=False)-> dict[tuple[str, ...], etree.XPath]:
    """Genera un diccionario de XPaths (como elementos de la clase etree.XPath)"""
    #rutas = [ruta if isinstance(ruta, tuple) else (ruta,) for ruta in rutas]
    return {ruta: etree.XPath(build_xpath(ruta, ns_name, deep=deep), namespaces=namespaces) for ruta in rutas}

def load_xsd_data(
        nodos: dict[str, list[tuple[str, ...]]], # Diccionario de rutas de nodos por tipo de documento {cfdi: [(), ()], cartaporte: [(), ()], ...}
        xsd_paths: dict[str, str], # Diccionario de rutas de archivos XSD por tipo de documento
        versiones: dict[str, list[str]], # Diccionario de versiones por tipo de documento
        )-> dict[str, dict[str, list[str]]]: # {'cfdi4': {'required_elements': [], 'required_attributes': [], 'namespaces': [], 'xpaths': []}, ...}
    """
    Carga los datos de los archivos XSD (elementos y atributos requeridos, namespaces y XPaths) para cada tipo de documento.
    Tipo de documento puede ser 'cfdi', 'cartaporte', 'tfd', etc.
    """
    xsd_data = {}
    for key, xsd_path in xsd_paths.items():
        xsd_data[key] = analizar_xsd(xsd_path)
        if xsd_data[key] is None:
            continue
        # ver si key corresponde a una versión de un tipo de documento
        for tipo, vers in versiones.items():
            if key in vers:
                xsd_data[key]['tipo'] = tipo
        xsd_data[key]['xpaths'] = generate_xpaths(
            nodos[xsd_data[key]['tipo']], 
            xsd_data[key]['namespaces'], 
            key if xsd_data[key]['tipo'] == 'cartaporte' else xsd_data[key]['tipo'],
            deep=True
        )
    return xsd_data


# def update_progress(progress, N, what = 'archivos'):    
#     print('\r', ' '*100,end='') # borramos la línea anterior
#     print(f'\rProcesando {progress}/{N} {what}...', end='')
