🧠 Compilador Educativo con IDE Gráfico

Este proyecto implementa un compilador modular en Python con interfaz gráfica desarrollada en PyQt5.
Su propósito es ilustrar las fases de un compilador (léxica, sintáctica y semántica) de forma visual e interactiva.

🚀 Características Principales

Análisis léxico con generación de tokens.txt

Análisis sintáctico descendente recursivo (LL)

Soporta estructuras if, while, do-while, cin, cout

Manejo de errores fatales y recuperables

Árbol sintáctico abstracto (AST) visual

IDE en PyQt5 con:

Resaltado de sintaxis

Paneles de análisis y errores

Árbol interactivo colapsable

Pruebas incluidas (códigos válidos y erróneos)

🧩 Estructura del Proyecto
phases/
├── lexical.py
├── syntactic.py
├── semantic.py
├── intermediate_code.py
util/
└── treeNode.py
IDE.py
tokens.txt
testSintactico_VALIDO.txt
testSintactico_VALIDO2.txt
testSintactico_ERRONEO.txt
codigoPrueba.txt

🧮 Ejecución

Guarda tu código fuente (por ejemplo codigo.txt).

Ejecuta el IDE:

python IDE.py


Desde el menú Compilar → Análisis Léxico / Sintáctico ejecuta las fases.

Observa los resultados en las pestañas correspondientes.

🔍 Árbol Sintáctico Abstracto

Muestra solo los tokens terminales en formato lexema (línea:columna).

Puede expandirse/colapsarse como estructura de carpetas.

🧱 Requisitos

Python 3.10+

PyQt5 (pip install pyqt5)

🧰 Pendientes / Próximas Fases

 Implementación del análisis semántico

 Generación de código intermedio

 Tablas de símbolos avanzadas

✍️ Autor

Juan de Luna
Estudiante de Ingeniería en Sistemas Computacionales
Universidad Autónoma de Aguascalientes