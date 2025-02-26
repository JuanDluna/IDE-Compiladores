import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk  # Necesitas instalar Pillow: pip install pillow

class IDE:
    def __init__(self, root):
        self.root = root
        self.root.title("IDE para Compilador - [Sin archivo]")
        self.current_file = None  # Ruta del archivo actual
        self.create_menu()
        self.create_toolbar()  # Crear barra de herramientas con íconos
        self.create_panels()

    def create_menu(self):
        menubar = tk.Menu(self.root)

        # Menú de archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Guardar", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Guardar como", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú de compilación
        compile_menu = tk.Menu(menubar, tearoff=0)
        compile_menu.add_command(label="Compilar", command=self.compile)
        compile_menu.add_command(label="Análisis Léxico", command=self.lexical_analysis)
        compile_menu.add_command(label="Análisis Sintáctico", command=self.syntactic_analysis)
        compile_menu.add_command(label="Análisis Semántico", command=self.semantic_analysis)
        compile_menu.add_command(label="Código Intermedio", command=self.intermediate_code)
        compile_menu.add_command(label="Ejecución", command=self.execute)
        menubar.add_cascade(label="Compilar", menu=compile_menu)

        self.root.config(menu=menubar)

        # Atajos de teclado
        self.root.bind("<Control-o>", lambda event: self.open_file())
        self.root.bind("<Control-s>", lambda event: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda event: self.save_file_as())
        self.root.bind("<Control-q>", lambda event: self.root.quit())

    def create_toolbar(self):
        # Crear una barra de herramientas
        self.toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Cargar íconos
        try:
            self.open_icon = ImageTk.PhotoImage(Image.open("open_icon.png").resize((20, 20)))
            self.save_icon = ImageTk.PhotoImage(Image.open("save_icon.png").resize((20, 20)))
            self.save_as_icon = ImageTk.PhotoImage(Image.open("save_as_icon.png").resize((20, 20)))
            self.exit_icon = ImageTk.PhotoImage(Image.open("exit_icon.png").resize((20, 20)))

            # Botones con íconos
            open_button = tk.Button(self.toolbar, image=self.open_icon, command=self.open_file)
            open_button.pack(side=tk.LEFT, padx=2, pady=2)

            save_button = tk.Button(self.toolbar, image=self.save_icon, command=self.save_file)
            save_button.pack(side=tk.LEFT, padx=2, pady=2)

            save_as_button = tk.Button(self.toolbar, image=self.save_as_icon, command=self.save_file_as)
            save_as_button.pack(side=tk.LEFT, padx=2, pady=2)

            exit_button = tk.Button(self.toolbar, image=self.exit_icon, command=self.root.quit)
            exit_button.pack(side=tk.LEFT, padx=2, pady=2)
        except Exception as e:
            print(f"Error al cargar íconos: {e}")

    def create_panels(self):
        # Panel principal (dividido en dos partes 50/50)
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Panel del editor de código
        self.editor_frame = tk.Frame(self.paned_window)
        self.editor_frame.pack_propagate(False)  # Evita que el frame se ajuste al contenido

        # Número de línea en el editor
        self.line_numbers = tk.Text(self.editor_frame, width=4, padx=5, pady=5, wrap="none", state="disabled")
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Frame para el editor y el scroll horizontal
        self.editor_scroll_frame = tk.Frame(self.editor_frame)
        self.editor_scroll_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scroll vertical para el editor
        self.editor_scroll_y = tk.Scrollbar(self.editor_scroll_frame, orient="vertical")

        # Scroll horizontal para el editor (ahora está debajo del editor)
        self.editor_scroll_x = tk.Scrollbar(self.editor_scroll_frame, orient="horizontal")

        # Editor de código (con ajuste de texto desactivado para permitir scroll horizontal)
        self.editor = tk.Text(
            self.editor_scroll_frame,
            wrap="none",  # Desactivar el ajuste de texto para permitir scroll horizontal
            padx=5,
            pady=5,
            yscrollcommand=self.editor_scroll_y.set,
            xscrollcommand=self.editor_scroll_x.set,
        )
        self.editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Configurar el scroll vertical
        self.editor_scroll_y.config(command=self.editor.yview)
        self.editor_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Configurar el scroll horizontal (ahora está debajo del editor)
        self.editor_scroll_x.config(command=self.editor.xview)
        self.editor_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Panel de resultados (con pestañas)
        self.result_frame = tk.Frame(self.paned_window)
        self.notebook = ttk.Notebook(self.result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Pestañas para cada tipo de análisis
        self.lexical_tab = tk.Text(self.notebook, wrap="none", state="disabled")
        self.syntactic_tab = tk.Text(self.notebook, wrap="none", state="disabled")
        self.semantic_tab = tk.Text(self.notebook, wrap="none", state="disabled")
        self.intermediate_tab = tk.Text(self.notebook, wrap="none", state="disabled")
        self.execution_tab = tk.Text(self.notebook, wrap="none", state="disabled")
        self.hash_table_tab = tk.Text(self.notebook, wrap="none", state="disabled")

        self.notebook.add(self.lexical_tab, text="Análisis Léxico")
        self.notebook.add(self.syntactic_tab, text="Análisis Sintáctico")
        self.notebook.add(self.semantic_tab, text="Análisis Semántico")
        self.notebook.add(self.intermediate_tab, text="Código Intermedio")
        self.notebook.add(self.execution_tab, text="Ejecución")
        self.notebook.add(self.hash_table_tab, text="Tabla Hash")

        # Añadir los paneles al panel principal (50/50)
        self.paned_window.add(self.editor_frame, minsize=400)  # Mitad izquierda
        self.paned_window.add(self.result_frame, minsize=400)  # Mitad derecha

        # Ventana de errores en la parte inferior (con re-size vertical)
        self.error_frame = tk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.error_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Pestañas para los errores
        self.error_notebook = ttk.Notebook(self.error_frame)
        self.error_frame.add(self.error_notebook)

        self.lexical_errors_tab = tk.Text(self.error_notebook, wrap="none", state="disabled")
        self.syntactic_errors_tab = tk.Text(self.error_notebook, wrap="none", state="disabled")
        self.semantic_errors_tab = tk.Text(self.error_notebook, wrap="none", state="disabled")

        self.error_notebook.add(self.lexical_errors_tab, text="Errores Léxicos")
        self.error_notebook.add(self.syntactic_errors_tab, text="Errores Sintácticos")
        self.error_notebook.add(self.semantic_errors_tab, text="Errores Semánticos")

        # Barra de estado en la parte inferior de la ventana principal
        self.status_bar = tk.Label(self.root, text="Línea: 1, Columna: 1", bd=1, relief="sunken", anchor="w")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Actualizar números de línea y barra de estado
        self.editor.bind("<KeyRelease>", self.update_line_numbers)
        self.editor.bind("<KeyRelease>", self.update_status_bar)
        self.editor.bind("<ButtonRelease-1>", self.update_status_bar)  # Actualizar al soltar el clic
        self.editor.bind("<Motion>", self.on_mouse_move)  # Actualizar al mover el cursor

        # Vincular eventos de scroll y redimensionamiento
        self.editor.bind("<MouseWheel>", self.on_mouse_wheel)  # Scroll con rueda del mouse
        self.editor.bind("<Configure>", self.update_line_numbers)   # Redimensionamiento del editor

        # Inicializar números de línea
        self.update_line_numbers()

    def compile(self):
        # Ejecutar todas las fases del compilador
        self.lexical_analysis()
        self.syntactic_analysis()
        self.semantic_analysis()
        self.intermediate_code()
        self.execute()
        self.show_hash_table()
        self.show_errors()

    def on_scroll(self, first, last):
        # Actualizar el scroll y los números de línea
        self.editor_scroll_y.set(first, last)
        self.update_line_numbers()

    def on_mouse_wheel(self, event):
        # Manejar el scroll con la rueda del mouse
        if event.delta > 0:
            self.editor.yview_scroll(-1, "units")
        else:
            self.editor.yview_scroll(1, "units")
        self.update_line_numbers()

    def update_line_numbers(self, event=None):
        # Obtener la posición actual del scroll
        first_visible_line = self.editor.index("@0,0").split(".")[0]
        last_visible_line = self.editor.index("@0,10000").split(".")[0]

        # Crear una lista de números de línea para las líneas visibles
        line_numbers_text = ""
        for i in range(int(first_visible_line), int(last_visible_line) + 1):
            line_numbers_text += f"{i}\n"
            # Calcular el número de líneas visuales que ocupa esta línea lógica
            wrapped_lines = self.calculate_wrapped_lines(i)
            if wrapped_lines > 1:
                line_numbers_text += "\n" * (wrapped_lines - 1)

        # Actualizar el widget de números de línea
        self.line_numbers.config(state="normal")
        self.line_numbers.delete(1.0, "end")
        self.line_numbers.insert(1.0, line_numbers_text.strip())
        self.line_numbers.config(state="disabled")

    def calculate_wrapped_lines(self, line_number):
        # Calcular cuántas líneas visuales ocupa una línea lógica
        line_start = f"{line_number}.0"
        line_end = f"{line_number}.end"
        bbox_start = self.editor.bbox(line_start)
        bbox_end = self.editor.bbox(line_end)

        if bbox_start is None or bbox_end is None:
            return 1  # Si no se puede calcular, asumir que ocupa una línea

        # Calcular la diferencia en píxeles entre el inicio y el final de la línea
        y_start = bbox_start[1]
        y_end = bbox_end[1]
        line_height = bbox_start[3]

        if y_start == y_end:
            return 1  # La línea no está dividida
        else:
            # Calcular el número de líneas visuales
            return int((y_end - y_start) / line_height) + 1

    def update_status_bar(self, event=None):
        # Actualizar barra de estado con línea y columna actual del cursor
        cursor_index = self.editor.index("insert")
        line, col = cursor_index.split('.')
        self.status_bar.config(text=f"Línea: {line}, Columna: {col}")

    def on_mouse_move(self, event=None):
        # Actualizar la barra de estado solo si el cursor está dentro del editor
        if self.editor.winfo_containing(event.x_root, event.y_root) == self.editor:
            self.update_status_bar()

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
        if file_path:
            self.current_file = file_path
            with open(file_path, "r") as file:
                self.editor.delete(1.0, "end")
                self.editor.insert(1.0, file.read())
            self.update_line_numbers()
            self.update_window_title()  # Actualizar el título de la ventana

    def save_file(self):
        if self.current_file:
            content = self.editor.get(1.0, "end-1c")
            with open(self.current_file, "w") as file:
                file.write(content)
            messagebox.showinfo("Guardar", "Archivo guardado correctamente.")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt")])
        if file_path:
            self.current_file = file_path
            content = self.editor.get(1.0, "end-1c")
            with open(file_path, "w") as file:
                file.write(content)
            messagebox.showinfo("Guardar como", "Archivo guardado correctamente.")
            self.update_window_title()  # Actualizar el título de la ventana

    def update_window_title(self):
        # Actualizar el título de la ventana con el nombre del archivo
        if self.current_file:
            self.root.title(f"IDE para Compilador - [{self.current_file}]")
        else:
            self.root.title("IDE para Compilador - [Sin archivo]")

    def lexical_analysis(self):
        # Simulación de análisis léxico
        self.lexical_tab.config(state="normal")
        self.lexical_tab.delete(1.0, "end")
        self.lexical_tab.insert(1.0, "Resultados del análisis léxico...")
        self.lexical_tab.config(state="disabled")

    def syntactic_analysis(self):
        # Simulación de análisis sintáctico
        self.syntactic_tab.config(state="normal")
        self.syntactic_tab.delete(1.0, "end")
        self.syntactic_tab.insert(1.0, "Resultados del análisis sintáctico...")
        self.syntactic_tab.config(state="disabled")

    def semantic_analysis(self):
        # Simulación de análisis semántico
        self.semantic_tab.config(state="normal")
        self.semantic_tab.delete(1.0, "end")
        self.semantic_tab.insert(1.0, "Resultados del análisis semántico...")
        self.semantic_tab.config(state="disabled")

    def intermediate_code(self):
        # Simulación de código intermedio
        self.intermediate_tab.config(state="normal")
        self.intermediate_tab.delete(1.0, "end")
        self.intermediate_tab.insert(1.0, "Código intermedio generado...")
        self.intermediate_tab.config(state="disabled")

    def execute(self):
        # Simulación de ejecución
        self.execution_tab.config(state="normal")
        self.execution_tab.delete(1.0, "end")
        self.execution_tab.insert(1.0, "Resultado de la ejecución...")
        self.execution_tab.config(state="disabled")

    def show_hash_table(self):
        # Simulación de la tabla hash
        self.hash_table_tab.config(state="normal")
        self.hash_table_tab.delete(1.0, "end")
        self.hash_table_tab.insert(1.0, "Contenido de la tabla hash...")
        self.hash_table_tab.config(state="disabled")

    def show_errors(self):
        # Simulación de la ventana de errores
        self.lexical_errors_tab.config(state="normal")
        self.lexical_errors_tab.delete(1.0, "end")
        self.lexical_errors_tab.insert(1.0, "Errores léxicos...")
        self.lexical_errors_tab.config(state="disabled")

        self.syntactic_errors_tab.config(state="normal")
        self.syntactic_errors_tab.delete(1.0, "end")
        self.syntactic_errors_tab.insert(1.0, "Errores sintácticos...")
        self.syntactic_errors_tab.config(state="disabled")

        self.semantic_errors_tab.config(state="normal")
        self.semantic_errors_tab.delete(1.0, "end")
        self.semantic_errors_tab.insert(1.0, "Errores semánticos...")
        self.semantic_errors_tab.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = IDE(root)
    root.geometry("800x600")  # Tamaño inicial de la ventana
    root.mainloop()