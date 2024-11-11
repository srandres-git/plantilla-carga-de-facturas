#imports GUI
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import END, filedialog
import customtkinter
from tkcalendar import DateEntry
import threading
from config import DEFAULT_DELAY, PROGRESS_POPUP_HEIGHT, PROGRESS_POPUP_WIDTH, VER, APP_WIDTH, APP_HEIGHT, DEFAULT_START_DATE
from config import NODOS, NOMBRES, NODOS_PREDET
from exception_handling import EmptyFieldError, WrongTypeFieldError
from file_management import generate_template
from cfdi_inspection import xml_reader
# Main Application Class
class XMLReaderApp:
    def __init__(
            self,
            xsd_data: dict,
            attributes: dict,
            width = APP_WIDTH, 
            height = APP_HEIGHT, 
            version = VER, 
            default_delay = DEFAULT_DELAY, 
            default_start_date = DEFAULT_START_DATE,
            available_nodes = NODOS,
            preselected_nodes = NODOS_PREDET
        ):
        self.app = customtkinter.CTk()
        self.width = width
        self.height = height
        self.version = version
        self.default_delay = default_delay
        self.default_start_date = default_start_date

        # XSD data and attributes
        self.xsd_data = xsd_data
        self.attributes = attributes

        self.node_menu = NodeMenu(self.app, self.set_nodes, available_nodes, preselected_nodes)
        self.nodes = self.node_menu.nodes
        self.types = self.get_types()

        # Expected types for fields
        self.expected_types = {
            'delay': float,
            'fecha_inicio_carpeta': datetime,
            'fecha_fin_carpeta': datetime,
            'fecha_inicio_archivo': datetime,
            'fecha_fin_archivo': datetime,
            'exportar_no_leidas': bool,
            'explorar_subdirectorios': bool,
            'path': str,
            'layout': str,
            'exportar_como': str,
            'por_plantilla': bool,
            'nodos': dict
        }
        # Set up the main window
        self.setup_main_window()

        # Frames and Widgets
        self.setup_frames()
        self.create_widgets()

    def setup_main_window(self):
        customtkinter.set_appearance_mode("system")
        customtkinter.set_default_color_theme("blue")
        self.app.geometry(f"{self.width}x{self.height}")
        self.app.resizable(False, False)
        self.app.title(f'XML Reader V{self.version}')

    def setup_frames(self):
        # Grid 2x1
        self.app.grid_columnconfigure(0, weight=1)
        self.app.grid_columnconfigure(1, weight=3)
        self.app.grid_rowconfigure(0,weight=1)

        # Left frame
        self.left_frame = customtkinter.CTkFrame(master=self.app)
        self.left_frame.grid(row=0, column=0, sticky="nswe", padx=2, pady=2)

        # Right frame
        self.right_frame = customtkinter.CTkFrame(master=self.app)
        self.right_frame.grid(row=0, column=1, sticky="nswe", padx=20, pady=100)

    def create_widgets(self):
        # Switch
        self.switch_explore_N = customtkinter.CTkSwitch(
            master=self.left_frame,
            text='Explorar por plantilla',
            command=self.switch_mode
        )
        self.switch_explore_N.place(relx=0.1, rely=0.85)

        # Entries
        self.entry_path = customtkinter.CTkEntry(
            master=self.right_frame, placeholder_text="Buscar XMLs en carpeta:", width=300
        )
        self.entry_path.place(relx=0.3, rely=0.2, anchor=tk.CENTER)

        self.entry_layout = customtkinter.CTkEntry(
            master=self.right_frame, placeholder_text="Ruta plantilla de directorios",  width=300#, state='disabled',
        )
        self.entry_layout.place(relx=0.3, rely=0.5, anchor=tk.CENTER)

        self.entry_delay = customtkinter.CTkEntry(
            master=self.left_frame, placeholder_text='Delay (s)', width=100
        )
        self.entry_delay.insert(0, str(self.default_delay))
        self.entry_delay.configure(state='disabled')
        self.entry_delay.place(relx=0.5, rely=0.915)

        # Labels
        customtkinter.CTkLabel(master=self.left_frame, text='Delay (s)', width=50).place(relx=0.1, rely=0.915)
        customtkinter.CTkLabel(master=self.left_frame, text='Opciones', font=("Helvetica", 14)).place(relx=0.5, rely=0.075, anchor=tk.CENTER)
        customtkinter.CTkLabel(master=self.left_frame ,text='Explorar solo carpetas modificadas:', width=50).place(relx=0.1,rely=0.40, )
        customtkinter.CTkLabel(master=self.left_frame ,text='Desde', width=50).place(relx=0.1,rely=0.47, )
        customtkinter.CTkLabel(master=self.left_frame ,text='Hasta', width=50).place(relx=0.1,rely=0.54, )
        customtkinter.CTkLabel(master=self.left_frame ,text='Explorar solo archivos modificados:', width=50).place(relx=0.1,rely=0.63, )
        customtkinter.CTkLabel(master=self.left_frame ,text='Desde', width=50).place(relx=0.1,rely=0.70, )
        customtkinter.CTkLabel(master=self.left_frame ,text='Hasta', width=50).place(relx=0.1,rely=0.77, )
        
        # Buttons
        self.button_path = customtkinter.CTkButton(
            master=self.right_frame, text='Seleccionar folder', command=lambda: self.select_folder(self.entry_path),
        )
        self.button_path.place(relx=0.8, rely=0.2, anchor=tk.CENTER)

        self.button_layout_path = customtkinter.CTkButton(
            master=self.right_frame, text='Seleccionar archivo', command=lambda: self.select_file(self.entry_layout), state='disabled'
        )
        self.button_layout_path.place(relx=0.8, rely=0.5, anchor=tk.CENTER)

        self.button_layout_gen = customtkinter.CTkButton(
            master=self.right_frame, text='Generar Layout', command=self.generate_layout, state='disabled'
        )
        self.button_layout_gen.place(relx=0.8, rely=0.7, anchor=tk.CENTER)

        self.button_main = customtkinter.CTkButton(
            master=self.right_frame, text="Leer XMLs", command= lambda: self.start_task(self.main_action, ())
        )
        self.button_main.place(relx=0.5, rely=0.85, anchor=tk.CENTER)
        #_____________________________________________________________
        # prueba de menú de nodos
        self.node_menu_button = customtkinter.CTkButton(
            master=self.left_frame, text="Seleccionar nodos...", command=self.open_node_selection_menu,
            fg_color='transparent', border_width=0
        )
        self.node_menu_button.place(relx=0.1, rely=0.14, )


        # Date Entries
        self.setup_date_entries()

        # Checkboxes
        self.setup_checkboxes()

        # Combobox
        self.combobox_exp = customtkinter.CTkComboBox(
            master=self.left_frame, values=['Excel', 'CSV']
        )
        self.combobox_exp.set('Exportar como...')
        self.combobox_exp.place(relx=0.1, rely=0.21)

    def setup_date_entries(self):
        self.de_folder_from = DateEntry(
            master=self.left_frame, width=12, date_pattern="dd/MM/yyyy", background='black', foreground='white'
        )
        self.de_folder_from.place(relx=0.5, rely=0.47)
        self.de_folder_from.set_date(self.default_start_date)

        self.de_folder_to = DateEntry(
            master=self.left_frame, width=12, date_pattern="dd/MM/yyyy", background='black', foreground='white'
        )
        self.de_folder_to.place(relx=0.5, rely=0.54)

        self.de_file_from = DateEntry(
            master=self.left_frame, width=12, date_pattern="dd/MM/yyyy", background='black', foreground='white'
        )
        self.de_file_from.place(relx=0.5, rely=0.70)
        self.de_file_from.set_date(self.default_start_date)

        self.de_file_to = DateEntry(
            master=self.left_frame, width=12, date_pattern="dd/MM/yyyy", background='black', foreground='white'
        )
        self.de_file_to.place(relx=0.5, rely=0.77)
    
    def parse_date(self, date:str, plus_days:int=0)->datetime:
        return datetime.fromordinal(date.toordinal())+timedelta(days=plus_days)
    
    def parse_date_entries(self):
        return {
            'folder_from': self.parse_date(self.de_folder_from.get_date()),
            'folder_to': self.parse_date(self.de_folder_to.get_date(), plus_days=1),
            'file_from': self.parse_date(self.de_file_from.get_date()),
            'file_to': self.parse_date(self.de_file_to.get_date(), plus_days=1)
        }

    def setup_checkboxes(self):
        self.checkbox_no_leidas = customtkinter.CTkCheckBox(master=self.left_frame, text='Exportar reporte de errores')
        self.checkbox_no_leidas.select()
        self.checkbox_no_leidas.place(relx=0.1, rely=0.28)

        self.checkbox_explore_sub = customtkinter.CTkCheckBox(master=self.left_frame, text='Explorar subdirectorios')
        self.checkbox_explore_sub.select()
        self.checkbox_explore_sub.place(relx=0.1, rely=0.35)

        # self.checkbox_ccp = customtkinter.CTkCheckBox(master=self.left_frame, text='Complemento Carta Porte')
        # self.checkbox_ccp.deselect()
        # self.checkbox_ccp.place(relx=0.1, rely=0.35)

    # Utility and Helper Methods
    def resize_and_center(self, window, width, height):
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def select_folder(self, entry):
        path = filedialog.askdirectory(title='Seleccionar folder', initialdir='\\')
        entry.delete(0, END)
        entry.insert(0, path)

    def select_file(self, entry):
        path = filedialog.askopenfilename(title='Seleccionar archivo', initialdir='\\')
        entry.delete(0, END)
        entry.insert(0, path)

    def turn_on(self, widgets):
        for widget in widgets:
            widget.configure(state='normal')

    def turn_off(self, widgets):
        for widget in widgets:
            widget.configure(state='disabled')

    def switch_mode(self):
        # Example logic for toggling widgets based on switch state
        if self.switch_explore_N.get():
            self.turn_on([self.entry_layout, self.entry_delay, self.button_layout_path, self.button_layout_gen])
            self.turn_off([self.entry_path, self.button_path])
        else:
            self.turn_on([self.entry_path, self.button_path])
            self.turn_off([self.entry_layout, self.entry_delay, self.button_layout_path, self.button_layout_gen])

    def generate_layout(self):
        layout_path = filedialog.asksaveasfilename(
            title='Guardar plantilla de directorios', initialdir='\\', filetypes=[('Excel files', '*.xlsx')]
        )
        if layout_path:
            generate_template(layout_path)
    
    def get_all_widgets(self):
        dates = self.parse_date_entries()
        return {
            'path': self.entry_path.get(),
            'layout': self.entry_layout.get(),
            'delay': self.entry_delay.get(),
            'exportar_como': self.combobox_exp.get(),
            'fecha_inicio_carpeta': dates['folder_from'],
            'fecha_fin_carpeta': dates['folder_to'],
            'fecha_inicio_archivo': dates['file_from'],
            'fecha_fin_archivo': dates['file_to'],
            'exportar_no_leidas': self.checkbox_no_leidas.get(),
            'explorar_subdirectorios': self.checkbox_explore_sub.get(),
            'por_plantilla': self.switch_explore_N.get(),
            'nodos': self.nodes
        }
    
    def validate_empty_fields(self, fields: dict):
        """Valida que los campos no estén vacíos"""
        for field_name, field_value in fields.items():
            if field_value == '' or field_value is None:
                EmptyFieldError(field_name).show_warning()
                return False
        return True

    def validate_fields_type(self, fields: dict, expected_type: dict)->tuple[bool, dict]:
        """Valida que los campos se puedan convertir al tipo de dato esperado y regresa los campos convertidos"""
        for field_name, field_value in fields.items():
            if not isinstance(field_value, expected_type[field_name]):                
                try:
                    fields[field_name] = expected_type[field_name](field_value)
                except ValueError:
                    WrongTypeFieldError(field_name, expected_type[field_name].__name__).show_warning()
                    return False, fields
        return True, fields

    def validate_fields(self):
        """Valida los campos de la GUI y regresa un diccionario con los valores convertidos si son válidos"""
        # Get all widgets values
        values = self.get_all_widgets()
        # Validate empty fields
        if values['por_plantilla']:
            if not self.validate_empty_fields({
                'delay': values['delay'],
                'layout': values['layout'],
            }):
                return
        else:
            if not self.validate_empty_fields({
                'path': values['path'],
            }):
                return
        if not values['exportar_como'] in ['Excel', 'CSV']:
            EmptyFieldError('Exportar como').show_warning()
            return
        # Validate fields type        
        success, values = self.validate_fields_type(values, self.expected_types)
        if not success:
            return
        return values

    def open_node_selection_menu(self):
        self.node_menu = NodeMenu(self.app, self.set_nodes, preselected_nodes=self.nodes, available_nodes=NODOS)
        self.node_menu.setup_node_window()
    
    def set_nodes(self, nodes: dict[str, list[str]]):
        self.nodes = nodes
    
    def get_types(self):
        return [key for key in self.nodes.keys() if self.nodes[key]]
    
    def start_task(self, target: callable, args: tuple):
        task = threading.Thread(target=target, args=args)
        task.start()

    # progress popup with progress bar
    def show_progress_popup_files(self):
        self.progress_popup_files = customtkinter.CTkToplevel(self.app)
        self.progress_popup_files.title("Procesando archivos")
        self.progress_popup_files.geometry(f"{PROGRESS_POPUP_WIDTH}x{PROGRESS_POPUP_HEIGHT}")
        self.progress_popup_files.resizable(False, False)
        self.progress_label_files = customtkinter.CTkLabel(self.progress_popup_files, text="Procesando archivos...")
        self.progress_bar_files = customtkinter.CTkProgressBar(self.progress_popup_files,height=PROGRESS_POPUP_HEIGHT/3)
        self.progress_bar_files.grid(row=1, column=0)
        self.progress_label_files.grid(row=0, column=0)
        self.progress_popup_files.pack_slaves()
        self.resize_and_center(self.progress_popup_files, PROGRESS_POPUP_WIDTH, PROGRESS_POPUP_HEIGHT)
    
    def show_progress_popup_folders(self):
        self.progress_popup_folders = customtkinter.CTkToplevel(self.app)
        self.progress_popup_folders.title("Procesando carpetas")
        self.progress_popup_folders.geometry(f"{PROGRESS_POPUP_WIDTH}x{PROGRESS_POPUP_HEIGHT}")
        self.progress_popup_folders.resizable(False, False)
        self.progress_label_folders = customtkinter.CTkLabel(self.progress_popup_folders, text="Procesando carpetas...")
        self.progress_bar_folders = customtkinter.CTkProgressBar(self.progress_popup_folders,height=PROGRESS_POPUP_HEIGHT/3)
        self.progress_bar_folders.grid(row=1, column=0)
        self.progress_label_folders.grid(row=0, column=0)
        self.progress_popup_folders.pack_slaves()
        self.resize_and_center(self.progress_popup_folders, PROGRESS_POPUP_WIDTH, PROGRESS_POPUP_HEIGHT)

    def update_progress_folders(self, n, total):
        if not hasattr(self, 'progress_popup_folders') or not self.progress_popup_folders.winfo_exists():
            self.show_progress_popup_folders()
        self.progress_bar_folders.set(n/total)
        # show progress as text
        self.progress_label_folders.configure(text=f"Procesando carpetas... {n}/{total}")
        # to the front
        self.progress_popup_folders.lift()
        if n == total:
            self.progress_popup_folders.destroy()

    def update_progress_files(self, n, total):
        if not hasattr(self, 'progress_popup_files') or not self.progress_popup_files.winfo_exists():
            self.show_progress_popup_files()
        self.progress_bar_files.set(n/total)
        # show progress as text
        self.progress_label_files.configure(text=f"Procesando archivos... {n}/{total}")
        # to the front
        self.progress_popup_files.lift()
        if n == total:
            self.progress_popup_files.destroy()
    
    def main_action(self):
        # Validate fields
        values = self.validate_fields()
        if not values:
            return
        # Get types
        types = self.get_types()
        # Ask for export path
        export_path = filedialog.asksaveasfilename(
            title='Guardar archivo', initialdir='\\', filetypes=[('Excel files', '*.xlsx')], defaultextension='.xlsx'
        )
        # Read XMLs
        xml_reader(
            by_template=values['por_plantilla'],
            template_path=values['layout'],
            directory_path=values['path'],
            export_path=export_path,
            nodes=self.nodes,
            attributes=self.attributes,
            xsd_data=self.xsd_data,
            types=types,
            explore_subdirs=values['explorar_subdirectorios'],
            folder_date_range=(values['fecha_inicio_carpeta'], values['fecha_fin_carpeta']),
            file_date_range=(values['fecha_inicio_archivo'], values['fecha_fin_archivo']),
            wait_time=values['delay'],
            callback_progress_files= self.update_progress_files,
            callback_progress_folders= self.update_progress_folders
        )

    def run(self):
        self.app.mainloop()

#_____________________________________________________________
# Menú de nodos

class NodeMenu:
    def __init__(
            self,
            app,
            callback_set_nodes: callable,
            available_nodes: dict[str, list[str]],
            preselected_nodes: dict[str, list[str]],
        ):
        self.app : XMLReaderApp = app
        self.callback_set_nodes = callback_set_nodes
        self.available_nodes = available_nodes
        self.preselected_nodes = preselected_nodes
        self.nodes = preselected_nodes
        self.setup_node_vars()
        
    
    def setup_node_window(self):
        self.node_window = customtkinter.CTkToplevel(self.app)
        self.node_window.title("Seleccionar nodos")
        # Disable resizing of the new window
        self.node_window.resizable(False, False)
        # Crear un frame para los checkboxes con scrollbar
        self.checkbox_frame = customtkinter.CTkScrollableFrame(self.node_window)
        self.checkbox_frame.pack(fill="both", expand=True)

        # Add checkboxes to the frame
        self.add_node_checkboxes()

        # Button to confirm selection
        confirm_button = customtkinter.CTkButton(self.checkbox_frame, text="Aceptar", command=self.confirm_node_selection)
        confirm_button.pack(pady=20)

        # Adjust the window to fit the content
        self.node_window.update_idletasks()  # Calculate required size for content
        self.node_window.geometry(f"{self.node_window.winfo_width()}x{self.node_window.winfo_height()}")

         # Focus and restrict input to the new window
        self.node_window.focus_set()  # Brings the window to the front and focuses it
        self.node_window.grab_set()   # Restricts input to this window until it's closed
    
    # Handle confirmed selections
    def confirm_node_selection(self):
        selected_nodes = []
        for node, node_var in self.node_vars.items():
            if node_var.get():
                selected_nodes.append(node)
        self.nodes = self.nodes_list_to_dict(selected_nodes, self.available_nodes)
        self.callback_set_nodes(self.nodes)
        self.node_window.destroy()        
    
    def select_nodes(self, nodes:list[str]):
        for node in nodes:
            self.node_vars[node].set(True)

    def setup_node_vars(self):
        self.node_vars = {}
        for _, nodes_list in self.available_nodes.items():
            for node in nodes_list:
                self.node_vars[node] = tk.BooleanVar()

    def create_node_checkboxes(self, nodes: list[str], parent: tk.Toplevel, padding: int=10):
        for node in nodes:
            node_checkbox = customtkinter.CTkCheckBox(parent, text=node, variable=self.node_vars[node])
            node_checkbox.pack(pady=padding, anchor='w')

    def add_node_checkboxes(self):
        # Create checkboxes for each node type
        for node_type, nodes_list in self.available_nodes.items():
            customtkinter.CTkLabel(self.checkbox_frame, text=f'Nodos de {NOMBRES[node_type]}', font=("Helvetica", 14)).pack(pady=10)
            self.create_node_checkboxes(nodes_list, self.checkbox_frame, padding=10)
            # Select preselected nodes
            if node_type in self.preselected_nodes:
                self.select_nodes(self.preselected_nodes[node_type])

    def nodes_list_to_dict(self, nodes: list[str], available_nodes: dict[str, list[str]]):
        nodes_dict = {}
        for node_type, nodes_list in available_nodes.items():
            nodes_dict[node_type] = [node for node in nodes if node in nodes_list]
        return nodes_dict