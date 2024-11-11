from tkinter import messagebox
"""Manejo de excepciones en la inspección de CFDIs"""

class CFDIInspectionError(Exception):
    """Clase base para excepciones de inspección de CFDI"""
    def __init__(self, message: str):
        self.message = message
    def __str__(self):
        return self.message
    def show(self):
        print(self.message)
    def show_warning(self):
        messagebox.showwarning("Advertencia", self.message)
    def show_error(self):
        messagebox.showerror("Error", self.message)

class FileNotFoundError(CFDIInspectionError):
    """Error al intentar abrir un archivo"""
    def __init__(self, file_path):
        super().__init__(f"No se encontró el archivo: {file_path}")

class DirectoryNotFoundError(CFDIInspectionError):
    """Error al intentar abrir un directorio"""
    def __init__(self, directory_path):
        super().__init__(f"No se encontró el directorio: {directory_path}")

class XMLParseError(CFDIInspectionError):
    """Error al intentar parsear el archivo XML"""
    def __init__(self, file_path: str, error: Exception):
        super().__init__(f"Error al parsear el archivo XML: {file_path} \n{str(error)}")

class XSDParseError(CFDIInspectionError):
    """Error al intentar parsear el archivo XSD"""
    def __init__(self, file_path: str, error: Exception):
        super().__init__(f"Error al parsear el archivo XSD: {file_path} \n{str(error)}")

class InvalidCFDIError(CFDIInspectionError):
    def __init__(self, file_path: str, error: Exception):
        super().__init__(f"El archivo {file_path} no es un CFDI válido: \n{str(error)}")

class CFDIAttributeNotFound(CFDIInspectionError):
    """Error cuando no se encuentra un atributo esperado en el XML"""
    def __init__(self, attribute: str, file_path: str):
        super().__init__(f"No se encontró el atributo '{attribute}' en el archivo: {file_path}")

class CFDINodeNotFound(CFDIInspectionError):
    """Error cuando no se encuentra un nodo esperado en el XML"""
    def __init__(self, node: str, file_path: str):
        super().__init__(f"No se encontró el nodo '{node}' en el archivo: {file_path}")

class CFDINoAttributesError(CFDIInspectionError):
    """Error cuando no se encuentran atributos en algún nodo"""
    def __init__(self, node: str,):
        super().__init__(f"No se encontraron atributos en el nodo '{node}'")

class ExportError(CFDIInspectionError):
    """Error al intentar exportar un archivo"""
    def __init__(self, file_path: str, cause: str,):
        super().__init__(f"Error al intentar exportar a: {file_path}. {cause}")

class EmptyExportError(ExportError):
    """Error al intentar exportar un archivo vacío"""
    def __init__(self, file_path: str):
        super().__init__(file_path, "\nNo hay datos para exportar.")

class InvalidExportPathError(ExportError):
    """Error al intentar exportar un archivo a una ruta inválida"""
    def __init__(self, file_path: str):
        super().__init__(file_path, "\nLa ruta de exportación no es válida.")

class PermissionExportError(ExportError):
    """Error al intentar exportar un archivo sin permisos de escritura"""
    def __init__(self, file_path: str):
        super().__init__(file_path, "\nNo se tienen permisos para escribir en la ruta de exportación.")

class EmptyDirectoryError(CFDIInspectionError):
    """Error al intentar abrir un directorio vacío"""
    def __init__(self, directory_path: str):
        super().__init__(f"El directorio está vacío: {directory_path}")

class InvalidXSDPathError(CFDIInspectionError):
    """Error al intentar abrir el archivo XSD"""
    def __init__(self, file_path: str):
        super().__init__(f"No se encontró el archivo XSD: {file_path}")

class InvalidXSDDataError(CFDIInspectionError):
    """Error al intentar abrir el archivo XSD"""
    def __init__(self, file_path: str, error: Exception):
        super().__init__(f"Error al intentar abrir el archivo XSD: {file_path} \n{str(error)}")

#_____________________________________________________________
# VALIDACIÓN DE CAMPOS GUI

class GUIValidationError(Exception):
    """Clase base para excepciones de validación de campos en la GUI"""
    def __init__(self, message: str):
        self.message = message
    def __str__(self):
        return self.message
    def show(self):
        print(self.message)
    def show_warning(self):
        messagebox.showwarning("Advertencia", self.message)
    def show_error(self):
        messagebox.showerror("Error", self.message)

class EmptyFieldError(GUIValidationError):
    """Error al intentar validar un campo vacío"""
    def __init__(self, field_name: str):
        super().__init__(f"El campo '{field_name}' no puede estar vacío.")

class WrongTypeFieldError(GUIValidationError):
    """Error al intentar validar un campo con un tipo de dato incorrecto"""
    def __init__(self, field_name: str, expected_type: str):
        super().__init__(f"El campo '{field_name}' debe ser de tipo {expected_type}.")

