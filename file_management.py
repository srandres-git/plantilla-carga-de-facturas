"""
FUNCIONES AUXILIARES PARA MANEJO DE ARCHIVOS
"""
# _____________________________________________________________
# IMPORTS
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

from exception_handling import EmptyExportError, ExportError, InvalidExportPathError, PermissionExportError, FileNotFoundError
# _____________________________________________________________
# FUNCIONES DE BÚSQUEDA DE XMLs

def get_xml_files(
        path : str,
        explore_subdirs : bool = False,
        folder_date_range : tuple[ datetime, datetime ] = None,
        file_date_range : tuple[ datetime, datetime ] = None
)-> list[str]:
    """
    Regresa una lista con los archivos xml en un directorio.
    Si explore_subdirs=True, busca en subdirectorios.
    Si folder_date_range o file_date_range no son None, filtra por fecha de modificación de directorio o archivo.
    """
    xml_files = []

    #Filtro subdirectorios
    try:
        if explore_subdirs:
            path_walk = [(root,dirs,files) for root,dirs,files in os.walk(path)]
        else:
            path_walk = [(
                path, [], [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
            )]
    except Exception as error:
        print(f'No se pudo generar path_walk en {path}:\n',error)
        return None
        
    # Filtro por fecha de modificación de directorio
    if folder_date_range is not None:
        try:
            path_walk = folder_date_filter(path_walk,folder_date_range)
        except Exception as error:
            print(f'No se pudo filtrar por fecha de modificación de directorio en {path}:\n',error)
            return None
    
    # Filtro por fecha de modificación de archivo
    if file_date_range is not None:
        try:
            path_walk = file_date_filter(path_walk, file_date_range)
        except Exception as error:
            print(f'No se pudo filtrar por fecha de modificación de archivo en {path}:\n',error)
            return None
    
    # Generar lista de archivos xml
    try:
        for root, _, files in path_walk:
            xml_files.extend([os.path.join(root, file) for file in files if file.lower().endswith('.xml')])
    except Exception as error:
        print(f'No se pudo generar lista de archivos xml en {path}:\n',error)
        return None
    
    return xml_files

def get_xml_files_from_zip(zip_file)-> list[str]:
    """
    Regresa una lista con los archivos xml en un archivo zip.
    """
    import zipfile
    xml_files = []
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith('.xml'):
                    xml_files.append(filename)
    except Exception as error:
        print(f'No se pudo leer el archivo zip:\n',error)
        return None
    return xml_files
# __________________________________________________________
# FUNCIONES FILTROS POR FECHA

def folder_date_filter(
        path_walk : list,
        date_range : tuple[ datetime, datetime ]
)-> list[tuple[str, list[str], list[str]]]: # [(root, dirs, files), ...]
    """
    Filtra los directorios de un path_walk cuya fecha de modificación esté en el rango date_range
    """
    return [(root, dirs, files) for root, dirs, files in path_walk
        if in_date_range(path_m_date(root),date_range)]

def file_date_filter(
        path_walk : list[tuple[str, list[str], list[str]]],
        date_range : tuple[ datetime, datetime ]
)-> list[tuple[str, list[str], list[str]]]: # [(root, dirs, files), ...]
    """
    Filtra los archivos de un path_walk cuya fecha de modificación esté en el rango date_range
    """
    return [
        (root, dirs, [file for file in files if in_date_range(path_m_date(os.path.join(root, file)), date_range)])
        for root, dirs, files in path_walk
    ]

def in_date_range(
        date : datetime,
        date_range : tuple[ datetime, datetime ]
)-> bool:
    return date_range[0]<=date<=date_range[1]

def path_m_date(path : str)-> datetime:
    """
    Regresa la fecha de modificación de un archivo
    """
    return datetime.fromtimestamp(os.path.getmtime(path))


def from_prior_month(date_1 : datetime, date_2 : datetime):
    """
    Revisa si date_1 es de un mes anterior a date_2
    """
    if date_2.year > date_1.year:
        return True
    else:
        diff = relativedelta(
            datetime(date_2.year, date_2.month, 1),
            datetime(date_1.year, date_1.month, 1)
        )
        return diff.months>=1
# _____________________________________________________________
# EXPORTACIÓN DE DATOS A EXCEL

def export_to_excel(data_gen, output_path, nodes: dict[str, list[tuple[str, ...]]]):
    import pandas as pd
    # verificar si se puede escribir en el archivo
    try:
        writer = pd.ExcelWriter(output_path)
    except FileNotFoundError:
        InvalidExportPathError(output_path).show_error()
        return None
    except PermissionError:
        PermissionExportError(output_path).show_error()
        return None
    # verificar si hay datos para exportar
    try:        
        startrows = {(tipo, nodo): 0 for tipo in nodes.keys() for nodo in nodes[tipo]}
        firtsrows = {tipo: 0 for tipo in nodes.keys()}
    except AttributeError:
        EmptyExportError(output_path).show_error()
        return None
    except TypeError:
        EmptyExportError(output_path).show_error()
        return None
    if not any([bool(val) for val in nodes.values()]):
        EmptyExportError(output_path).show_error()
        return None
    
    for i, data in enumerate(data_gen):        
        for tipo, nodos in data.items():
            if nodos is not None:
                for nodo, atributos in nodos.items():
                    df = pd.DataFrame(atributos)
                    try:
                        header = i==firtsrows[tipo]
                        df.to_excel(
                            writer,
                            sheet_name=f'{nodo}',
                            startrow=startrows[(tipo, nodo)],
                            header=header,
                            index=False
                        )
                        startrows[(tipo, nodo)] += len(df)+ header
                    except Exception as error:
                        ExportError(output_path, str(error)).show()
                        return None
            else:
                firtsrows[tipo]+=1

                    
    try:
        writer.close()
    except IndexError:
        EmptyExportError(output_path).show_error()
        return None
    # mensaje de éxito
    print("Exportación exitosa", f"Datos exportados a: {output_path.split('/')[-1]}")
    # abrir archivo
    os.startfile(output_path)
    
# _____________________________________________________________
# PLANTILLA PARA IMPORTAR RUTAS A EXPLORAR
def generate_template(path):
    """
    Genera una plantilla de excel para importar rutas a explorar
    """
    import pandas as pd
    df = pd.DataFrame({'Directorios':['ruta\\de\\ejemplo1','ruta\\de\\ejemplo2']})
    df.to_excel(path,
                index=False,
                freeze_panes=(1,0),
                sheet_name='Directorios')
    os.startfile(path)
    
def read_template(path):
    """
    Lee una plantilla de excel para importar rutas a explorar
    """
    import pandas as pd
    try:
        df = pd.read_excel(path, sheet_name='Directorios')
    except FileNotFoundError:
        FileNotFoundError(path).show_warning()
        return None
    except PermissionError:
        PermissionExportError(path).show_warning()
        return None
    return df['Directorios'].tolist()