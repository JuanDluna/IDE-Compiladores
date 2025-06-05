import sys
import re
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMenuBar, QMenu, QStatusBar, QFileDialog, QToolBar, QAction, QSplitter, QMessageBox
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
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

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
        painter.fillRect(event.rect(), QColor(Qt.lightGray))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = int(top + self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(
                    0, top, self.line_number_area.width(), self.fontMetrics().height(),
                    Qt.AlignRight, number
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

        self.new_action.triggered.connect(self.new_file)
        self.open_action.triggered.connect(self.open_file)
        self.save_action.triggered.connect(self.save_file)
        self.save_as_action.triggered.connect(self.save_file_as)
        self.compile_action.triggered.connect(self.compile)

        self.toolbar.addAction(self.new_action)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.save_as_action)
        self.toolbar.addAction(self.compile_action)

        # Editor de código
        self.code_editor = CodeEditor()
        self.code_editor.textChanged.connect(self.check_for_changes)  # Monitorear cambios

        # Panel de Análisis (pestañas)
        self.analysis_tabs = QTabWidget()
        self.lexical_analysis_tab = QPlainTextEdit()
        self.syntax_analysis_tab = QTreeWidget()
        self.syntax_analysis_tab.setHeaderHidden(True)
        self.semantic_analysis_tab = QPlainTextEdit()
        self.intermediate_code_tab = QPlainTextEdit()
        self.execution_tab = QPlainTextEdit()
        self.hash_table_tab = QPlainTextEdit()

        # Configurar los paneles de análisis como de solo lectura
        self.lexical_analysis_tab.setReadOnly(True)
        self.semantic_analysis_tab.setReadOnly(True)
        self.intermediate_code_tab.setReadOnly(True)
        self.execution_tab.setReadOnly(True)
        self.hash_table_tab.setReadOnly(True)

        self.analysis_tabs.addTab(self.lexical_analysis_tab, "Análisis Léxico")
        self.analysis_tabs.addTab(self.syntax_analysis_tab, "Análisis Sintáctico")
        self.analysis_tabs.addTab(self.semantic_analysis_tab, "Análisis Semántico")
        self.analysis_tabs.addTab(self.intermediate_code_tab, "Código Intermedio")
        self.analysis_tabs.addTab(self.execution_tab, "Ejecución")
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
        self.splitter_top = QSplitter(Qt.Horizontal)
        self.splitter_top.addWidget(self.code_editor)
        self.splitter_top.addWidget(self.analysis_tabs)

        self.splitter_bottom = QSplitter(Qt.Vertical)
        self.splitter_bottom.addWidget(self.splitter_top)
        self.splitter_bottom.addWidget(self.error_tabs)

        # Widget central
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()
        self.central_layout.addWidget(self.splitter_bottom)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # Menú Superior
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("Archivo")
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        self.exit_action = QAction(QIcon("media/exit_icon.png"), "Cerrar", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        self.compile_menu = self.menu_bar.addMenu("Compilar")
        self.compile_menu.addAction(self.compile_action)
        self.compile_menu.addSeparator()
        self.compile_menu.addAction("Análisis Léxico", self.run_lexical_phase)
        self.compile_menu.addAction("Análisis Sintáctico", self.run_syntactic_phase)
        self.compile_menu.addAction("Análisis Semántico", self.run_semantic_phase)

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
            ast_root = syntactic.get_ast()
            fill_tree_widget(self.syntax_analysis_tab, ast_root, self.syntax_errors_tab)
        except Exception as e:
            QMessageBox.critical(self, "Error en análisis sintáctico", str(e))



    def run_semantic_phase(self):
        try:
            source_code = self.code_editor.toPlainText()
            resultado = semantic.analyze(source_code)
            self.semantic_analysis_tab.setPlainText(resultado)
        except Exception:
            self.semantic_analysis_tab.setPlainText("Fase semántica aún no implementada.")

    def run_intermediate_code_phase(self):
        try:
            source_code = self.code_editor.toPlainText()
            resultado = intermediate_code.generate(source_code)
            self.intermediate_code_tab.setPlainText(resultado)
        except Exception:
            self.intermediate_code_tab.setPlainText("Generación de código intermedio aún no implementada.")


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

def fill_tree_widget(widget: QTreeWidget, ast_root: ASTNode, error_output_widget: QPlainTextEdit):
    widget.clear()
    error_output_widget.clear()
    errores = []

    def add_node_recursively(parent_widget_item, ast_node):
        # Si es un nodo de error, lo almacenamos y no lo añadimos al árbol visual
        if "Error" in ast_node.name:
            errores.append(ast_node.name)
            return

        item = QTreeWidgetItem([ast_node.name])
        parent_widget_item.addChild(item)

        for child in ast_node.children:
            add_node_recursively(item, child)

    # Raíz del árbol
    root_item = QTreeWidgetItem([ast_root.name])
    widget.addTopLevelItem(root_item)

    for child in ast_root.children:
        add_node_recursively(root_item, child)

    widget.expandAll()  # Puedes quitar esto si quieres que se muestre colapsado por defecto

    # Mostrar errores recolectados
    if errores:
        error_output_widget.setPlainText("\n".join(errores))
    else:
        error_output_widget.setPlainText("Sin errores sintácticos.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = CompilerIDE()
    ide.show()
    sys.exit(app.exec_())