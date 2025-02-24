import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class IDE:
    def __init__(self, root):
        self.root = root
        self.root.title("IDE para Compilador - [Sin archivo]")
        self.current_file = None  # Ruta del archivo actual
        self.create_menu()
        self.create_panels()

    def create_menu(self):
        menubar = tk.Menu(self.root)

        # Menú de archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir", command=self.open_file)
        file_menu.add_command(label="Guardar", command=self.save_file)
        file_menu.add_command(label="Guardar como", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú de compilación
        compile_menu = tk.Menu(menubar, tearoff=0)
        compile_menu.add_command(label="Análisis Léxico", command=self.lexical_analysis)
        compile_menu.add_command(label="Análisis Sintáctico", command=self.syntactic_analysis)
        compile_menu.add_command(label="Análisis Semántico", command=self.semantic_analysis)
        compile_menu.add_command(label="Código Intermedio", command=self.intermediate_code)
        compile_menu.add_command(label="Ejecución", command=self.execute)
        menubar.add_cascade(label="Compilar", menu=compile_menu)

        self.root.config(menu=menubar)

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

        # Frame para el editor
        self.editor_scroll_frame = tk.Frame(self.editor_frame)
        self.editor_scroll_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scroll vertical para el editor
        self.editor_scroll_y = tk.Scrollbar(self.editor_scroll_frame, orient="vertical")

        # Editor de código (con ajuste de texto)
        self.editor = tk.Text(
            self.editor_scroll_frame,
            wrap="word",  # Ajustar el texto al ancho del editor
            padx=5,
            pady=5,
            yscrollcommand=self.on_scroll,  # Vincular al evento de scroll
        )
        self.editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configurar el scroll vertical
        self.editor_scroll_y.config(command=self.editor.yview)
        self.editor_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Panel de resultados (con pestañas)
        self.result_frame = tk.Frame(self.paned_window)
        self.notebook = ttk.Notebook(self.result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Pestañas para cada tipo de análisis
        self.lexical_tab = tk.Text(self.notebook, wrap="none")
        self.syntactic_tab = tk.Text(self.notebook, wrap="none")
        self.semantic_tab = tk.Text(self.notebook, wrap="none")
        self.intermediate_tab = tk.Text(self.notebook, wrap="none")
        self.execution_tab = tk.Text(self.notebook, wrap="none")

        self.notebook.add(self.lexical_tab, text="Análisis Léxico")
        self.notebook.add(self.syntactic_tab, text="Análisis Sintáctico")
        self.notebook.add(self.semantic_tab, text="Análisis Semántico")
        self.notebook.add(self.intermediate_tab, text="Código Intermedio")
        self.notebook.add(self.execution_tab, text="Ejecución")

        # Añadir los paneles al panel principal (50/50)
        self.paned_window.add(self.editor_frame, minsize=400)  # Mitad izquierda
        self.paned_window.add(self.result_frame, minsize=400)  # Mitad derecha

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
        self.lexical_tab.delete(1.0, "end")
        self.lexical_tab.insert(1.0, "Resultados del análisis léxico...")

    def syntactic_analysis(self):
        # Simulación de análisis sintáctico
        self.syntactic_tab.delete(1.0, "end")
        self.syntactic_tab.insert(1.0, "Resultados del análisis sintáctico...")

    def semantic_analysis(self):
        # Simulación de análisis semántico
        self.semantic_tab.delete(1.0, "end")
        self.semantic_tab.insert(1.0, "Resultados del análisis semántico...")

    def intermediate_code(self):
        # Simulación de código intermedio
        self.intermediate_tab.delete(1.0, "end")
        self.intermediate_tab.insert(1.0, "Código intermedio generado...")

    def execute(self):
        # Simulación de ejecución
        self.execution_tab.delete(1.0, "end")
        self.execution_tab.insert(1.0, "Resultado de la ejecución...")

if __name__ == "__main__":
    root = tk.Tk()
    app = IDE(root)
    root.geometry("800x600")  # Tamaño inicial de la ventana
    root.mainloop()