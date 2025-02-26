import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QMenu, QStatusBar, QFileDialog, QToolBar, QAction, QSplitter
)
from PyQt5.QtGui import QTextCursor, QTextBlockFormat, QTextFormat, QPainter, QColor, QIcon
from PyQt5.QtCore import Qt, QRect, QSize

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

        # Desactivar el ajuste de línea para permitir scroll horizontal
        self.setLineWrapMode(QPlainTextEdit.NoWrap)

        # Habilitar el scroll horizontal
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

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
        """Pinta los números de línea en el área correspondiente."""
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

class CompilerIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IDE para Compilador")
        self.setGeometry(100, 100, 1000, 600)

        # Crear la barra de herramientas y agregar íconos
        self.toolbar = QToolBar("Barra de herramientas")
        self.addToolBar(self.toolbar)

        # Acciones para la barra de herramientas
        self.open_action = QAction(QIcon("open_icon.png"), "Abrir", self)
        self.save_action = QAction(QIcon("save_icon.png"), "Guardar", self)
        self.save_as_action = QAction(QIcon("save_as_icon.png"), "Guardar como", self)
        self.compile_action = QAction(QIcon("compile_icon.png"), "Compilar", self)

        self.open_action.triggered.connect(self.open_file)
        self.save_action.triggered.connect(self.save_file)
        self.save_as_action.triggered.connect(self.save_file_as)
        self.compile_action.triggered.connect(self.compile)

        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.save_action)
        self.toolbar.addAction(self.save_as_action)
        self.toolbar.addAction(self.compile_action)

        # Editor de código
        self.code_editor = CodeEditor()

        # Panel de Análisis (pestañas)
        self.analysis_tabs = QTabWidget()
        self.lexical_analysis_tab = QPlainTextEdit()
        self.syntax_analysis_tab = QPlainTextEdit()
        self.semantic_analysis_tab = QPlainTextEdit()
        self.intermediate_code_tab = QPlainTextEdit()
        self.execution_tab = QPlainTextEdit()
        self.hash_table_tab = QPlainTextEdit()

        # Configurar los paneles de análisis como de solo lectura
        self.lexical_analysis_tab.setReadOnly(True)
        self.syntax_analysis_tab.setReadOnly(True)
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
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.save_as_action)
        self.file_menu.addSeparator()
        self.exit_action = QAction(QIcon("exit_icon.png"), "Cerrar", self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        self.compile_menu = self.menu_bar.addMenu("Compilar")
        self.compile_menu.addAction(self.compile_action)
        self.compile_menu.addSeparator()
        self.compile_menu.addAction("Análisis Léxico", self.lexical_analysis)
        self.compile_menu.addAction("Análisis Sintáctico", self.syntax_analysis)
        self.compile_menu.addAction("Análisis Semántico", self.semantic_analysis)

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

    def open_file(self):
        """Abre un archivo y carga su contenido en el editor."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo", "", "Archivos de texto (*.txt)")
        if file_path:
            with open(file_path, "r") as file:
                self.code_editor.setPlainText(file.read())

    def save_file(self):
        """Guarda el contenido del editor en un archivo."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo", "", "Archivos de texto (*.txt)")
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.code_editor.toPlainText())

    def save_file_as(self):
        """Guarda el contenido del editor en un archivo con un nombre diferente."""
        self.save_file()

    def compile(self):
        """Función de compilación (placeholder)."""
        print("Compilando...")

    def lexical_analysis(self):
        """Función de análisis léxico (placeholder)."""
        print("Realizando análisis léxico...")

    def syntax_analysis(self):
        """Función de análisis sintáctico (placeholder)."""
        print("Realizando análisis sintáctico...")

    def semantic_analysis(self):
        """Función de análisis semántico (placeholder)."""
        print("Realizando análisis semántico...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ide = CompilerIDE()
    ide.show()
    sys.exit(app.exec_())