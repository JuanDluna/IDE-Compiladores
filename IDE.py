import sys
import re
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMenuBar, QMenu, QStatusBar, QFileDialog, QToolBar, QAction, QSplitter, QMessageBox,
    QLineEdit, QPushButton, QLabel, QTextEdit
)
from PyQt5.QtGui import QTextCursor, QTextBlockFormat, QTextFormat, QPainter, QColor, QIcon, QFont
from PyQt5.QtCore import Qt, QRect, QSize
from phases import lexical, syntactic, semantic, intermediate_code
from util.treeNode import ASTNode


class LineNumberArea(QWidget):
    """Widget personalizado para mostrar los números de línea."""
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    """Editor de código con números de línea."""
    def __init__(self):
        super().__init__()
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width()
        self.setup_highlighter()

        # Desactivar el ajuste de línea para permitir scroll horizontal
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Habilitar el scroll horizontal
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Aumentar el tamaño de la fuente
        font = self.font()
        font.setPointSize(12)  # Tamaño de fuente a 12 puntos
        self.setFont(font)

    def line_number_area_width(self):
        """Calcula el ancho necesario para el área de números de línea."""
        digits = 1
        max_lines = max(1, self.blockCount())
        while max_lines >= 10:
            max_lines /= 10
            digits += 1
        return 3 + self.fontMetrics().width('9') * digits

    def update_line_number_area_width(self):
        """Actualiza el ancho del área de números de línea."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Actualiza el área de números de línea."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

    def resizeEvent(self, event):
        """Reajusta el área de números de línea cuando se redimensiona el editor."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        #Pinta los números de línea en el área correspondiente.
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(Qt.GlobalColor.lightGray))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = int(top + self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(
                    0, top, self.line_number_area.width(), self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = int(top + self.blockBoundingRect(block).height())
            block_number += 1
    def setup_highlighter(self):
        from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
        
        class Highlighter(QSyntaxHighlighter):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.highlighting_rules = []
                self.multiline_comment_format = QTextCharFormat()
                
                # 1. ROSA - Identificadores (Color 2)
                identifier_format = QTextCharFormat()
                identifier_format.setForeground(QColor("#FF00FF"))  # Rosa
                self.highlighting_rules.append((r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', identifier_format))
                
                # 2. ROJO - Palabras reservadas (Color 4)
                reserved_format = QTextCharFormat()
                reserved_format.setForeground(QColor("#FF0000"))  # Rojo
                reserved_format.setFontWeight(75)  # Hacerlas un poco más gruesas
                for word in lexical.RESERVED_WORDS:
                    self.highlighting_rules.append((r'\b' + word + r'\b', reserved_format))
                
                # 3. AZUL - Operadores aritméticos (Color 5)
                arithmetic_format = QTextCharFormat()
                arithmetic_format.setForeground(QColor("#0000FF"))  # Azul
                self.highlighting_rules.append((r'[\+\-\*/%]', arithmetic_format))
                self.highlighting_rules.append((r'\+\+', arithmetic_format))
                self.highlighting_rules.append((r'--', arithmetic_format))
                self.highlighting_rules.append((r'\*\*', arithmetic_format))
                
                # 4. VERDE - Números (Color 1)
                number_format = QTextCharFormat()
                number_format.setForeground(QColor("#00AA00"))  # Verde
                self.highlighting_rules.append((r'\b\d+\b', number_format))
                self.highlighting_rules.append((r'\b\d+\.\d+\b', number_format))
                
                # 5. MARRÓN - Operadores relacionales y lógicos (Color 6)
                relational_format = QTextCharFormat()
                relational_format.setForeground(QColor("#AA5500"))  # Marrón
                self.highlighting_rules.append((r'<=|>=|==|!=|<|>', relational_format))
                self.highlighting_rules.append((r'&&|\|\||!', relational_format))
                
                # 6. AMARILLO - Comentarios (Color 3)
                comment_format = QTextCharFormat()
                comment_format.setForeground(QColor("#AAAA00"))  # Amarillo
                self.highlighting_rules.append((r'//.*', comment_format))
                
                # Formato para comentarios multilínea
                self.multiline_comment_format = QTextCharFormat()
                self.multiline_comment_format.setForeground(QColor("#AAAA00"))  # Amarillo
                
                # Delimitadores y otros
                symbol_format = QTextCharFormat()
                symbol_format.setForeground(QColor("#000000"))  # Negro
                self.highlighting_rules.append((r'[\(\)\[\]\{\},;]', symbol_format))
                
                # Patrón para inicio/fin de comentarios multilínea
                self.comment_start = re.compile(r'/\*')
                self.comment_end = re.compile(r'\*/')
            
            def highlightBlock(self, text):
                if text is None:
                    return
                
                # Aplicar reglas normales primero
                for pattern, format in self.highlighting_rules:
                    expression = re.compile(pattern)
                    for match in expression.finditer(text):
                        start, end = match.span()
                        self.setFormat(start, end - start, format)
                
                # Manejo especial para comentarios multilínea
                self.setCurrentBlockState(0)
                
                # Inicializar start_index
                start_index = 0
                if self.previousBlockState() != 1:
                    start_match = self.comment_start.search(text)
                    start_index = start_match.start() if start_match else -1
                
                # Buscar comentarios multilínea
                while start_index >= 0:
                    end_match = self.comment_end.search(text, start_index)
                    if end_match:
                        end_index = end_match.end()
                        length = end_index - start_index
                        self.setCurrentBlockState(0)
                    else:
                        self.setCurrentBlockState(1)
                        length = len(text) - start_index
                    
                    # Aplicar formato al comentario
                    self.setFormat(start_index, length, self.multiline_comment_format)
                    
                    # Buscar siguiente comentario
                    next_match = self.comment_start.search(text, start_index + length)
                    start_index = next_match.start() if next_match else -1
        
        self.highlighter = Highlighter(self.document())



class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE para Compilador")
        self.setGeometry(100, 100, 1000, 600)

        # Variable para almacenar la ruta del archivo abierto
        self.current_file_path = None
        self.file_content_on_disk = ""  # Almacena el contenido del archivo en disco

        # Crear la barra de herramientas y agregar íconos
        self.toolbar = QToolBar("Barra de herramientas")
        self.addToolBar(self.toolbar)

        # Acciones para la barra de herramientas
        self.new_action = QAction(QIcon("media/new_file_icon.png"), "Nuevo archivo", self)
        self.open_action = QAction(QIcon("media/open_icon.png"), "Abrir", self)
        self.save_action = QAction(QIcon("media/save_icon.png"), "Guardar", self)
        self.save_as_action = QAction(QIcon("media/save_as_icon.png"), "Guardar como", self)
        self.compile_action = QAction(QIcon("media/compile_icon.png"), "Compilar", self)

        # Atajos de teclado
        self.new_action.setShortcut("Ctrl+N")
        self.open_action.setShortcut("Ctrl+O")
        self.save_action.setShortcut("Ctrl+S")
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.compile_action.setShortcut("Ctrl+R")

        # Conectar acciones
        self.new_action.triggered.connect(self.new_file)
        self.open_action.triggered.connect(self.open_file)
        self.save_action.triggered.connect(self.save_file)
        self.save_as_action.triggered.connect(self.save_file_as)
        self.compile_action.triggered.connect(self.compile)

        # Agregar acciones a la barra de herramientas
        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.save_as_action)
        self.toolbar.addAction(self.compile_action)

        # Editor de código
        self.code_editor = CodeEditor()
        self.code_editor.textChanged.connect(self.check_for_changes)

        # Panel de Análisis (pestañas)
        self.analysis_tabs = QTabWidget()
        self.lexical_analysis_tab = QPlainTextEdit()
        self.syntax_analysis_tab = QTreeWidget()
        self.syntax_analysis_tab.setHeaderHidden(True)
        self.semantic_analysis_tab = QTreeWidget()
        self.semantic_analysis_tab.setHeaderHidden(True)
        self.intermediate_code_tab = QPlainTextEdit()
        # Crear widget de ejecución interactivo
        self.execution_widget = self._create_execution_widget()
        self.hash_table_tab = QPlainTextEdit()

        # Configurar los paneles de análisis como de solo lectura
        self.lexical_analysis_tab.setReadOnly(True)
        self.intermediate_code_tab.setReadOnly(True)
        self.hash_table_tab.setReadOnly(True)
        
        # Variables para el intérprete
        self.tac_interpreter = None
        self.tac_instructions = []
        self.execution_running = False

        self.analysis_tabs.addTab(self.lexical_analysis_tab, "Análisis Léxico")
        self.analysis_tabs.addTab(self.syntax_analysis_tab, "Análisis Sintáctico")
        self.analysis_tabs.addTab(self.semantic_analysis_tab, "Análisis Semántico")
        self.analysis_tabs.addTab(self.intermediate_code_tab, "Código Intermedio")
        self.analysis_tabs.addTab(self.execution_widget, "Ejecución")
        self.analysis_tabs.addTab(self.hash_table_tab, "Tabla HASH")

        # Panel de Errores (pestañas)
        self.error_tabs = QTabWidget()
        self.lexical_errors_tab = QPlainTextEdit()
        self.syntax_errors_tab = QPlainTextEdit()
        self.semantic_errors_tab = QPlainTextEdit()

        # Configurar los paneles de errores como de solo lectura
        self.lexical_errors_tab.setReadOnly(True)
        self.syntax_errors_tab.setReadOnly(True)
        self.semantic_errors_tab.setReadOnly(True)

        self.error_tabs.addTab(self.lexical_errors_tab, "Errores Léxicos")
        self.error_tabs.addTab(self.syntax_errors_tab, "Errores Sintácticos")
        self.error_tabs.addTab(self.semantic_errors_tab, "Errores Semánticos")

        # Layout principal con QSplitter para paneles reajustables
        self.splitter_top = QSplitter(Qt.Orientation.Horizontal)
        self.splitter_top.addWidget(self.code_editor)
        self.splitter_top.addWidget(self.analysis_tabs)

        self.splitter_bottom = QSplitter(Qt.Orientation.Vertical)
        self.splitter_bottom.addWidget(self.splitter_top)
        self.splitter_bottom.addWidget(self.error_tabs)

        # Widget central
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_layout.addWidget(self.splitter_bottom)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # Menú Superior
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        
        # Menú Archivo
        self.file_menu = QMenu("Archivo", self.menu_bar)
        self.menu_bar.addMenu(self.file_menu)
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        
        # Acción de salir
        self.exit_action = QAction(QIcon("media/exit_icon.png"), "Cerrar", self)
        self.exit_action.triggered.connect(self.close_window)
        self.file_menu.addAction(self.exit_action)

        # Menú Compilar
        self.compile_menu = QMenu("Compilar", self.menu_bar)
        self.menu_bar.addMenu(self.compile_menu)
        self.compile_menu.addAction(self.compile_action)
        self.compile_menu.addSeparator()
        
        # Acciones de análisis
        self.lexical_action = QAction("Análisis Léxico", self)
        self.lexical_action.triggered.connect(self.run_lexical_phase)
        self.compile_menu.addAction(self.lexical_action)
        
        self.syntactic_action = QAction("Análisis Sintáctico", self)
        self.syntactic_action.triggered.connect(self.run_syntactic_phase)
        self.compile_menu.addAction(self.syntactic_action)
        
        self.semantic_action = QAction("Análisis Semántico", self)
        self.semantic_action.triggered.connect(self.run_semantic_phase)
        self.compile_menu.addAction(self.semantic_action)
        
        self.intermediate_action = QAction("Código Intermedio", self)
        self.intermediate_action.triggered.connect(self.run_intermediate_code_phase)
        self.compile_menu.addAction(self.intermediate_action)

        # Barra de Estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.code_editor.cursorPositionChanged.connect(self.update_status_bar)

    def update_status_bar(self):
        """Actualiza la barra de estado con la línea y columna actual del cursor."""
        cursor = self.code_editor.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.status_bar.showMessage(f"Línea: {line}, Columna: {column}")

    def new_file(self):
        """Crea un nuevo archivo, preguntando si se desea guardar los cambios no guardados."""
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Cambios no guardados",
                "¿Desea guardar los cambios antes de crear un nuevo archivo?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return  # Cancelar la creación del nuevo archivo

        self.code_editor.setPlainText("")
        self.current_file_path = None
        self.file_content_on_disk = ""
        self.update_window_title()

    def open_file(self):
        """Abre un archivo y carga su contenido en el editor."""
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self, "Cambios no guardados",
                "¿Desea guardar los cambios antes de abrir un nuevo archivo?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return  # Cancelar la apertura del archivo

        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", "Archivos de texto (*.txt)")
        if file_path:
            with open(file_path, "r") as file:
                content = file.read()
                self.code_editor.setPlainText(content)
                self.current_file_path = file_path
                self.file_content_on_disk = content  # Guardar el contenido del archivo en disco
                self.update_window_title()

    def save_file(self):
        """Guarda el contenido del editor en un archivo."""
        if self.current_file_path:
            content = self.code_editor.toPlainText()
            with open(self.current_file_path, "w") as file:
                file.write(content)
            self.file_content_on_disk = content  # Actualizar el contenido en disco
            self.update_window_title()
        else:
            self.save_file_as()

    def save_file_as(self):
        """Guarda el contenido del editor en un archivo con un nombre diferente."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", "", "Archivos de texto (*.txt)")
        if file_path:
            content = self.code_editor.toPlainText()
            with open(file_path, "w") as file:
                file.write(content)
            self.current_file_path = file_path
            self.file_content_on_disk = content  # Actualizar el contenido en disco
            self.update_window_title()

    def compile(self):
        if not self.ensure_file_saved():
            return
        self.run_lexical_phase()
        self.run_syntactic_phase()
        self.run_semantic_phase()
        self.run_intermediate_code_phase()

    def ensure_file_saved(self):
        """Verifica que el archivo esté guardado antes de compilar."""
        if not self.current_file_path:
            respuesta = QMessageBox.question(
                self, "Archivo no guardado",
                "El archivo no ha sido guardado. ¿Deseas guardarlo ahora?",
                QMessageBox.Yes | QMessageBox.No
            )
            if respuesta == QMessageBox.Yes:
                self.save_file()
            else:
                return False

        current_content = self.code_editor.toPlainText()
        if current_content != self.file_content_on_disk:
            respuesta = QMessageBox.question(
                self, "Cambios no guardados",
                "Existen cambios sin guardar. ¿Deseas guardarlos antes de compilar?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if respuesta == QMessageBox.Yes:
                self.save_file()
            elif respuesta == QMessageBox.Cancel:
                return False
        return True

    def run_lexical_phase(self):
        try:
            tabla_tokens, tabla_errores = lexical.analizar_desde_archivo(self.current_file_path)

            # Mostrar resultados en el IDE
            self.lexical_analysis_tab.setPlainText(tabla_tokens)
            self.lexical_errors_tab.setPlainText(tabla_errores)

            # Ya no generamos el archivo aquí, se hace en el analizador léxico
        except Exception as e:
            QMessageBox.critical(self, "Error en análisis léxico", str(e))
            

    def run_syntactic_phase(self):
        try:
            # Ejecutar primero el análisis léxico (si es necesario)
            if not os.path.exists("tokens.txt") or not self.current_file_path:
                # Si no hay tokens o no hay archivo abierto, ejecutar análisis léxico
                self.run_lexical_phase()
            
            # Asegurarse de que el archivo de tokens existe después del análisis léxico
            if not os.path.exists("tokens.txt"):
                QMessageBox.warning(self, "Advertencia", 
                                  "No se pudo generar el archivo de tokens. Por favor, verifique el archivo de código fuente.")
                return

            # Ejecutar el análisis sintáctico
            ast_root, errors = syntactic.get_ast()
            
            # Verificar si hay errores fatales
            if errors and any("Fatal" in error for error in errors):
                QMessageBox.critical(self, "Error Sintáctico", 
                                   "Se encontraron errores fatales durante el análisis sintáctico.")
            
            # Mostrar el árbol y los errores
            fill_tree_widget(self.syntax_analysis_tab, ast_root, self.syntax_errors_tab, errors)
            
        except Exception as e:
            QMessageBox.critical(self, "Error en análisis sintáctico", 
                               f"Error inesperado durante el análisis sintáctico:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def run_semantic_phase(self):
        try:
            # Ejecutar primero el análisis sintáctico (que incluye el léxico)
            if not os.path.exists("tokens.txt") or not self.current_file_path:
                # Si no hay tokens o no hay archivo abierto, ejecutar análisis sintáctico
                self.run_syntactic_phase()
            else:
                # Si hay tokens pero no se ha ejecutado el sintáctico, ejecutarlo
                # Verificar si hay AST válido ejecutando el sintáctico
                try:
                    ast_root, errors = syntactic.get_ast()
                    # Mostrar el árbol sintáctico también
                    fill_tree_widget(self.syntax_analysis_tab, ast_root, self.syntax_errors_tab, errors)
                except:
                    # Si falla, ejecutar desde el léxico
                    self.run_syntactic_phase()
            
            # Asegurarse de que el archivo de tokens existe después del análisis sintáctico
            if not os.path.exists("tokens.txt"):
                QMessageBox.warning(self, "Advertencia", 
                                  "No se pudo generar el archivo de tokens. Por favor, verifique el archivo de código fuente.")
                return
            
            # Ejecutar el análisis semántico
            ast_anotado, tabla_simbolos, errores, annotations, ast_root = semantic.get_semantic_results()
            
            # Mostrar árbol semántico anotado en la pestaña de análisis semántico
            if ast_root and annotations:
                fill_semantic_tree_widget(self.semantic_analysis_tab, ast_root, annotations)
            
            # Mostrar tabla de símbolos en la pestaña "Tabla HASH" (solo la tabla)
            tabla_texto = "nombre\ttipo\tambito\tvalor\tdireccion\n"
            for entry in tabla_simbolos:
                valor = entry.get('valor', '')
                tabla_texto += f"{entry['nombre']}\t{entry['tipo']}\t{entry['ambito']}\t{valor}\t{entry['direccion']}\n"
            self.hash_table_tab.setPlainText(tabla_texto)
            
            # Mostrar errores en el panel de errores semánticos
            if errores:
                errores_texto = "\n".join([
                    f"{error['tipo']}: {error['descripcion']} ({error['linea']}:{error['columna']})"
                    for error in errores
                ])
                self.semantic_errors_tab.setPlainText(errores_texto)
            else:
                self.semantic_errors_tab.setPlainText("Sin errores semánticos.")
            
            # Verificar si hay errores fatales
            if errores and any(error.get('fatal', False) for error in errores):
                QMessageBox.critical(self, "Error Semántico", 
                                   "Se encontraron errores fatales durante el análisis semántico.")
            
        except Exception as e:
            self.semantic_analysis_tab.setPlainText(f"Error durante el análisis semántico:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def run_intermediate_code_phase(self):
        """Genera código intermedio TAC y lo ejecuta."""
        try:
            # Ejecutar primero el análisis semántico (que incluye sintáctico y léxico)
            if not os.path.exists("tokens.txt") or not self.current_file_path:
                self.run_semantic_phase()
            else:
                # Verificar si tenemos los resultados semánticos
                try:
                    ast_anotado, tabla_simbolos, errores, annotations, ast_root = semantic.get_semantic_results()
                except:
                    # Si falla, ejecutar análisis semántico completo
                    self.run_semantic_phase()
                    ast_anotado, tabla_simbolos, errores, annotations, ast_root = semantic.get_semantic_results()
            
            # Obtener resultados semánticos
            ast_anotado, tabla_simbolos, errores, annotations, ast_root = semantic.get_semantic_results()
            
            if ast_root is None:
                self.intermediate_code_tab.setPlainText("Error: No se pudo obtener el AST. Ejecuta primero el análisis semántico.")
                return
            
            # Verificar si hay errores semánticos fatales
            if errores and any(error.get('fatal', False) for error in errores):
                self.intermediate_code_tab.setPlainText(
                    "Error: No se puede generar código intermedio debido a errores semánticos fatales.\n"
                    "Por favor, corrige los errores y vuelve a ejecutar el análisis semántico."
                )
                return
            
            # Generar código TAC (sin ejecutar aún)
            generator = intermediate_code.TACGenerator(annotations, tabla_simbolos)
            instructions = generator.generate_from_ast(ast_root)
            
            # Guardar instrucciones para ejecución interactiva
            self.tac_instructions = instructions
            
            # Mostrar código TAC generado
            tac_text = "\n".join(instructions) if instructions else "No se generaron instrucciones."
            self.intermediate_code_tab.setPlainText(tac_text)
            
            # Mostrar mensaje en ejecución
            if hasattr(self, 'execution_output'):
                self.execution_output.clear()
                self.execution_output.append("=== CÓDIGO TAC GENERADO ===\n")
                self.execution_output.append("Presione 'Ejecutar' para iniciar la ejecución interactiva.\n")
                self.execution_output.append(f"Total de instrucciones: {len(instructions)}\n")
                if hasattr(self, 'execution_run_btn'):
                    self.execution_run_btn.setEnabled(True)
            
        except Exception as e:
            error_msg = f"Error durante la generación de código intermedio:\n{str(e)}"
            self.intermediate_code_tab.setPlainText(error_msg)
            if hasattr(self, 'execution_output'):
                self.execution_output.clear()
                self.execution_output.append(error_msg)
            import traceback
            traceback.print_exc()
    

    def check_for_changes(self):
        """Verifica si hay cambios no guardados en el editor."""
        if self.current_file_path:
            current_content = self.code_editor.toPlainText()
            if current_content != self.file_content_on_disk:
                self.update_window_title(has_unsaved_changes=True)
            else:
                self.update_window_title(has_unsaved_changes=False)

    def has_unsaved_changes(self):
        """Verifica si hay cambios no guardados en el editor."""
        if self.current_file_path:
            current_content = self.code_editor.toPlainText()
            return current_content != self.file_content_on_disk
        return False

    def update_window_title(self, has_unsaved_changes=False):
        """Actualiza el título de la ventana con el nombre del archivo y un asterisco si hay cambios no guardados."""
        if self.current_file_path:
            title = f"IDE para Compilador - {self.current_file_path}"
            if has_unsaved_changes:
                title += " *"
            self.setWindowTitle(title)
        else:
            self.setWindowTitle("IDE para Compilador")

    def close_window(self):
        """Cierra la ventana principal."""
        self.close()
        return None
    
    def _create_execution_widget(self):
        """Crea el widget de ejecución interactivo."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Área de salida (read-only)
        output_label = QLabel("Salida del Programa:")
        self.execution_output = QTextEdit()
        self.execution_output.setReadOnly(True)
        self.execution_output.setFont(QFont("Courier", 10))
        
        # Área de estado (variables y código TAC actual)
        state_label = QLabel("Estado de Ejecución (Variables y Código TAC):")
        self.execution_state = QTextEdit()
        self.execution_state.setReadOnly(True)
        self.execution_state.setFont(QFont("Courier", 9))
        self.execution_state.setMaximumHeight(200)
        
        # Área de entrada
        input_label = QLabel("Entrada (escriba un valor y presione Enter o clic en Enviar):")
        input_layout = QHBoxLayout()
        self.execution_input = QLineEdit()
        self.execution_input.setPlaceholderText("Ingrese un valor...")
        self.execution_input.returnPressed.connect(self._send_input_value)
        self.execution_send_btn = QPushButton("Enviar")
        self.execution_send_btn.clicked.connect(self._send_input_value)
        self.execution_send_btn.setEnabled(False)
        input_layout.addWidget(self.execution_input)
        input_layout.addWidget(self.execution_send_btn)
        
        # Botones de control
        control_layout = QHBoxLayout()
        self.execution_run_btn = QPushButton("Ejecutar")
        self.execution_run_btn.clicked.connect(self._start_execution)
        self.execution_stop_btn = QPushButton("Detener")
        self.execution_stop_btn.clicked.connect(self._stop_execution)
        self.execution_stop_btn.setEnabled(False)
        self.execution_clear_btn = QPushButton("Limpiar")
        self.execution_clear_btn.clicked.connect(self._clear_execution)
        control_layout.addWidget(self.execution_run_btn)
        control_layout.addWidget(self.execution_stop_btn)
        control_layout.addWidget(self.execution_clear_btn)
        control_layout.addStretch()
        
        # Ensamblar layout
        layout.addWidget(output_label)
        layout.addWidget(self.execution_output)
        layout.addWidget(state_label)
        layout.addWidget(self.execution_state)
        layout.addWidget(input_label)
        layout.addLayout(input_layout)
        layout.addLayout(control_layout)
        
        widget.setLayout(layout)
        return widget
    
    def _clear_execution(self):
        """Limpia las áreas de ejecución."""
        self.execution_output.clear()
        self.execution_state.clear()
        self.execution_input.clear()
        self.tac_interpreter = None
        self.tac_instructions = []
        self.execution_running = False
        self.execution_run_btn.setEnabled(True)
        self.execution_stop_btn.setEnabled(False)
        self.execution_send_btn.setEnabled(False)
    
    def _start_execution(self):
        """Inicia la ejecución del código TAC."""
        try:
            # Obtener código TAC generado
            if not self.tac_instructions:
                # Intentar generar código TAC
                if not os.path.exists("tokens.txt") or not self.current_file_path:
                    QMessageBox.warning(self, "Advertencia", 
                                      "Primero debe ejecutar el análisis semántico para generar código intermedio.")
                    return
                
                try:
                    ast_anotado, tabla_simbolos, errores, annotations, ast_root = semantic.get_semantic_results()
                except:
                    QMessageBox.warning(self, "Advertencia", 
                                      "Primero debe ejecutar el análisis semántico.")
                    return
                
                if ast_root is None:
                    QMessageBox.warning(self, "Advertencia", 
                                      "No se pudo obtener el AST.")
                    return
                
                # Generar código TAC
                from phases import intermediate_code
                generator = intermediate_code.TACGenerator(annotations, tabla_simbolos)
                self.tac_instructions = generator.generate_from_ast(ast_root)
                
                # Mostrar código TAC en la pestaña correspondiente
                tac_text = "\n".join(self.tac_instructions) if self.tac_instructions else "No se generaron instrucciones."
                self.intermediate_code_tab.setPlainText(tac_text)
            
            # Crear intérprete
            from phases import intermediate_code
            self.tac_interpreter = intermediate_code.TACInterpreter()
            self.tac_interpreter.load_from_list(self.tac_instructions)
            
            # Configurar callbacks para entrada/salida
            self.tac_interpreter.output_callback = self._on_output
            self.tac_interpreter.input_callback = self._on_input_request
            
            # Iniciar ejecución
            self.execution_running = True
            self.execution_run_btn.setEnabled(False)
            self.execution_stop_btn.setEnabled(True)
            self.execution_output.clear()
            self.execution_state.clear()
            self.execution_output.append("=== INICIANDO EJECUCIÓN ===\n")
            
            # Ejecutar
            self._execute_step()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error iniciando ejecución:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def _execute_step(self):
        """Ejecuta pasos del intérprete."""
        if not self.execution_running or not self.tac_interpreter:
            return
        
        try:
            max_steps = 10000
            steps = 0
            
            while self.execution_running and self.tac_interpreter.pc < len(self.tac_interpreter.instructions) and steps < max_steps:
                instruction = self.tac_interpreter.instructions[self.tac_interpreter.pc].strip()
                
                # Saltar etiquetas
                if instruction.endswith(':'):
                    self.tac_interpreter.pc += 1
                    continue
                
                # Ejecutar instrucción
                result = self.tac_interpreter._execute_instruction(instruction)
                
                # Verificar si necesita pausar para entrada
                if isinstance(result, tuple) and result[0] == "PAUSE":
                    var_name = result[1]
                    # Pausar y esperar entrada del usuario
                    # El mensaje ya se muestra en el callback _on_input_request
                    self._update_execution_state()
                    self.execution_send_btn.setEnabled(True)
                    self.execution_input.setFocus()
                    return  # Pausar ejecución
                
                # Verificar error
                if isinstance(result, tuple):
                    success, error = result
                    if not success:
                        self.execution_output.append(f"ERROR: {error}")
                        self.execution_running = False
                        break
                
                # Avanzar contador de programa
                self.tac_interpreter.pc += 1
                steps += 1
                
                # Actualizar estado cada 5 pasos
                if steps % 5 == 0:
                    self._update_execution_state()
            
            # Verificar si terminó
            if self.tac_interpreter.pc >= len(self.tac_interpreter.instructions):
                self.execution_output.append("\n=== EJECUCIÓN COMPLETADA ===")
                self.execution_running = False
                self.execution_run_btn.setEnabled(True)
                self.execution_stop_btn.setEnabled(False)
                self.execution_send_btn.setEnabled(False)
                self._update_execution_state()
            elif steps >= max_steps:
                self.execution_output.append(f"\n=== ADVERTENCIA: Límite de pasos alcanzado ({max_steps}) ===")
                self.execution_running = False
                self.execution_run_btn.setEnabled(True)
                self.execution_stop_btn.setEnabled(False)
                self.execution_send_btn.setEnabled(False)
            
        except Exception as e:
            self.execution_output.append(f"ERROR: {str(e)}")
            self.execution_running = False
            self.execution_run_btn.setEnabled(True)
            self.execution_stop_btn.setEnabled(False)
            self.execution_send_btn.setEnabled(False)
            import traceback
            traceback.print_exc()
    
    def _update_execution_state(self):
        """Actualiza el estado de ejecución mostrando variables y código actual."""
        if not self.tac_interpreter:
            return
        
        state_text = "=== ESTADO DE EJECUCIÓN ===\n\n"
        
        # Mostrar instrucción actual
        if self.tac_interpreter.pc < len(self.tac_interpreter.instructions):
            current_inst = self.tac_interpreter.instructions[self.tac_interpreter.pc]
            state_text += f"Instrucción {self.tac_interpreter.pc}/{len(self.tac_interpreter.instructions)-1}:\n"
            state_text += f"  {current_inst}\n\n"
        
        # Mostrar variables con valores
        state_text += "=== VARIABLES Y TEMPORALES ===\n"
        if self.tac_interpreter.memory:
            variables = []
            temporales = []
            for var, value in sorted(self.tac_interpreter.memory.items()):
                if var.startswith('t'):
                    temporales.append((var, value))
                else:
                    variables.append((var, value))
            
            if variables:
                state_text += "Variables:\n"
                for var, value in variables:
                    state_text += f"  {var} = {value}\n"
            
            if temporales:
                state_text += "\nTemporales (últimos 5):\n"
                for var, value in temporales[-5:]:
                    state_text += f"  {var} = {value}\n"
        else:
            state_text += "(Sin variables asignadas aún)\n"
        
        self.execution_state.setPlainText(state_text)
    
    def _on_output(self, value):
        """Callback para cuando el programa produce salida."""
        self.execution_output.append(str(value))
        self._update_execution_state()
    
    def _on_input_request(self, var_name):
        """Callback para cuando el programa solicita entrada."""
        # Solo mostrar el mensaje una vez
        if not hasattr(self, '_last_input_request') or self._last_input_request != var_name:
            self.execution_output.append(f"Esperando entrada para: {var_name}")
            self._last_input_request = var_name
        self._update_execution_state()
    
    def _send_input_value(self):
        """Envía un valor de entrada al intérprete."""
        if not self.execution_running or not self.tac_interpreter:
            return
        
        value_str = self.execution_input.text().strip()
        if not value_str:
            return
        
        try:
            # Convertir a número si es posible
            if '.' in value_str:
                value = float(value_str)
            else:
                value = int(value_str)
        except ValueError:
            value = value_str
        
        # Procesar la instrucción read que estaba pausada
        if self.tac_interpreter.pc < len(self.tac_interpreter.instructions):
            instruction = self.tac_interpreter.instructions[self.tac_interpreter.pc].strip()
            if instruction.startswith("read "):
                var = instruction[5:].strip()
                # Asignar el valor directamente
                self.tac_interpreter.set_value(var, value)
                self.execution_output.append(f"Entrada recibida para {var}: {value}")
                # Avanzar el PC
                self.tac_interpreter.pc += 1
            else:
                # Si no es read, agregar a la cola (por si acaso)
                self.tac_interpreter.input_queue.append(value)
                self.execution_output.append(f"Entrada recibida: {value}")
        
        self.execution_input.clear()
        self.execution_send_btn.setEnabled(False)
        
        # Continuar ejecución (que verificará si hay otro read)
        self._execute_step()
    
    def _stop_execution(self):
        """Detiene la ejecución."""
        self.execution_running = False
        self.execution_run_btn.setEnabled(True)
        self.execution_stop_btn.setEnabled(False)
        self.execution_send_btn.setEnabled(False)
        self.execution_output.append("\n=== EJECUCIÓN DETENIDA POR EL USUARIO ===")

def fill_tree_widget(widget: QTreeWidget, ast_root: ASTNode, error_output_widget: QPlainTextEdit, parser_errors: list):
    widget.clear()
    error_output_widget.clear()
    errores = []

    def add_node_recursively(parent_widget_item, ast_node):
        if ast_node is None:
            return
        if isinstance(ast_node.name, str) and "Error" in ast_node.name:
            errores.append(ast_node.name)
            return
        
        # Crear el item con el nombre del nodo
        item = QTreeWidgetItem([ast_node.name])
        parent_widget_item.addChild(item)
        
        # Procesar recursivamente los hijos
        if hasattr(ast_node, 'children'):
            for child in ast_node.children:
                if child is not None:
                    add_node_recursively(item, child)

    # Verificar si el árbol está vacío
    if ast_root is None:
        error_output_widget.setPlainText("Error: No se pudo generar el árbol sintáctico")
        return

    # Crear el nodo raíz
    root_item = QTreeWidgetItem([ast_root.name])
    widget.addTopLevelItem(root_item)
    
    # Procesar los hijos del nodo raíz
    if hasattr(ast_root, 'children'):
        for child in ast_root.children:
            if child is not None:
                add_node_recursively(root_item, child)
    
    widget.expandAll()

    # Combinar y mostrar errores
    all_errors = errores + (parser_errors if parser_errors else [])
    if all_errors:
        error_output_widget.setPlainText("\n".join(all_errors))
    else:
        error_output_widget.setPlainText("Sin errores sintácticos.")


def fill_semantic_tree_widget(widget: QTreeWidget, ast_root: ASTNode, annotations: dict):
    """
    Llena un QTreeWidget con el AST anotado semánticamente, mostrando tipos y valores.
    """
    widget.clear()
    
    def get_node_annotation(node):
        """Obtiene las anotaciones de un nodo."""
        node_id = id(node)
        return annotations.get(node_id, {})
    
    def format_node_name(node):
        """Formatea el nombre del nodo con anotaciones semánticas."""
        node_name = node.name
        node_annotations = get_node_annotation(node)
        
        # Extraer lexema si es un token
        parsed = None
        if " (" in node_name and ")" in node_name:
            parts = node_name.rsplit(" (", 1)
            if len(parts) == 2:
                lexema = parts[0]
                loc = parts[1].rstrip(")")
                node_name = f"{lexema} ({loc})"
        
        # Agregar anotaciones
        tipo = node_annotations.get('type')
        valor = node_annotations.get('value')
        
        # Construir texto del nodo
        texto = node_name
        
        # Agregar tipo o ERROR
        if tipo:
            texto += f" : {tipo}"
        elif 'type' in node_annotations:
            # Si 'type' está explícitamente en las anotaciones pero es None, hay un error
            texto += " : ERROR"
        # Si no hay 'type' en las anotaciones, no agregamos nada (nodo sin anotación semántica)
        
        # Agregar valor si existe (solo si no hay error)
        # Para nodos como "Expansión de ++", también mostrar el valor si está disponible
        # Incluir valor incluso si es 0 (que es un valor válido)
        if tipo is not None:  # Si hay tipo, intentar mostrar valor
            if valor is not None:
                # Formatear el valor apropiadamente según el tipo
                if tipo == 'float':
                    # Si el tipo es float, siempre mostrar con decimales
                    if isinstance(valor, float):
                        if valor.is_integer():
                            texto += f" = {valor:.1f}"
                        else:
                            # Limitar decimales para floats no enteros
                            texto += f" = {valor:.6g}".rstrip('0').rstrip('.')
                    elif isinstance(valor, int):
                        # Si el valor es int pero el tipo es float, mostrar como float
                        texto += f" = {float(valor):.1f}"
                    else:
                        texto += f" = {valor}"
                elif isinstance(valor, float):
                    # Si el valor es float pero el tipo no es float, mostrar normalmente
                    if valor.is_integer():
                        texto += f" = {int(valor)}"
                    else:
                        texto += f" = {valor:.6g}".rstrip('0').rstrip('.')
                elif isinstance(valor, bool):
                    texto += f" = {valor}"
                elif isinstance(valor, (int, str)):
                    texto += f" = {valor}"
                else:
                    texto += f" = {valor}"
        
        return texto
    
    def add_node_recursively(parent_widget_item, ast_node):
        if ast_node is None:
            return
        
        # Formatear nombre con anotaciones
        node_text = format_node_name(ast_node)
        item = QTreeWidgetItem([node_text])
        parent_widget_item.addChild(item)
        
        # Procesar recursivamente los hijos
        if hasattr(ast_node, 'children'):
            for child in ast_node.children:
                if child is not None:
                    add_node_recursively(item, child)
    
    # Verificar si el árbol está vacío
    if ast_root is None:
        return
    
    # Crear el nodo raíz
    root_text = format_node_name(ast_root)
    root_item = QTreeWidgetItem([root_text])
    widget.addTopLevelItem(root_item)
    
    # Procesar los hijos del nodo raíz
    if hasattr(ast_root, 'children'):
        for child in ast_root.children:
            if child is not None:
                # Saltar tokens de formato (main, {, })
                parsed = None
                if " (" in child.name and ")" in child.name:
                    parts = child.name.rsplit(" (", 1)
                    if len(parts) == 2:
                        lexema = parts[0]
                        if lexema in ('main', '{', '}'):
                            continue
                elif child.name in ('main', '{', '}'):
                    continue
                
                add_node_recursively(root_item, child)
    
    widget.expandAll()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = CompilerIDE()
    ide.show()
    sys.exit(app.exec_())