🧠 Compilador Educativo con IDE Gráfico

Este proyecto implementa un compilador modular en Python con interfaz gráfica desarrollada en PyQt5.
Su propósito es ilustrar las fases de un compilador (léxica, sintáctica y semántica) de forma visual e interactiva.

🚀 Características Principales

## Análisis Léxico
- Generación de `tokens.txt` con formato: `LEXEMA<TAB>TOKEN<TAB>LINEA<TAB>COLUMNA`
- Reconocimiento de identificadores, números, operadores, delimitadores
- Detección de comentarios (unilínea y multilínea)
- Manejo de palabras reservadas

## Análisis Sintáctico
- Analizador descendente recursivo (LL)
- Generación de Árbol Sintáctico Abstracto (AST)
- Soporta estructuras de control:
  - `if-then-else-end`
  - `while-end`
  - `do-while-until`
- Soporta entrada/salida: `cin >>`, `cout <<`
- Declaraciones de variables: `int`, `float`, `bool`
- Operaciones aritméticas, relacionales y lógicas
- Manejo de errores sintácticos con recuperación

## Análisis Semántico ✨
- **Construcción de tabla de símbolos** con información de:
  - Nombre de variable
  - Tipo de dato (int, float, bool)
  - Ámbito (global/local)
  - Valor actual (si está asignado)
  - Ubicaciones de uso (líneas donde aparece)
- **Verificación de tipos**:
  - Compatibilidad en asignaciones
  - Promoción de tipos (int → float)
  - Validación de operadores aritméticos, relacionales y lógicos
- **Detección de errores semánticos**:
  - Variable no declarada
  - Duplicidad de declaración en mismo ámbito
  - Incompatibilidad de tipos
  - Uso incorrecto de operadores
- **AST Anotado Semánticamente**:
  - Anotación de tipos heredados en cada nodo
  - Cálculo y propagación de valores constantes
  - Visualización de valores en operaciones aritméticas
  - Manejo especial de operaciones `++/--` y asignaciones compuestas
- **Archivos generados**:
  - `tabla_simbolos.txt`: Tabla de símbolos completa
  - `errores_semanticos.txt`: Reporte de errores encontrados
  - `ast_anotado.json`: AST con anotaciones semánticas

## IDE en PyQt5
- **Editor de código** con:
  - Resaltado de sintaxis
  - Números de línea
  - Scroll horizontal y vertical
- **Paneles de análisis**:
  - Análisis Léxico: Lista de tokens generados
  - Análisis Sintáctico: Árbol sintáctico visual
  - Análisis Semántico: Árbol semántico anotado con tipos y valores
  - Tabla HASH: Tabla de símbolos completa
  - Errores Semánticos: Lista de errores encontrados
- **Árboles interactivos**:
  - Expansión/colapsado de nodos
  - Visualización de tipos y valores en tiempo real
  - Navegación intuitiva

🧩 Estructura del Proyecto

```
.
├── phases/
│   ├── __init__.py
│   ├── lexical.py          # Analizador léxico
│   ├── syntactic.py        # Analizador sintáctico
│   ├── semantic.py         # Analizador semántico
│   └── intermediate_code.py # (Pendiente) Generación de código intermedio
├── util/
│   ├── treeNode.py         # Clase ASTNode para el AST
│   └── symbol_table.py     # Tabla de símbolos y gestión de ámbitos
├── test/
│   ├── testLexico.txt
│   ├── testSemantico.txt
│   ├── testSintactico_VALIDO.txt
│   ├── testSintactico_VALIDO2.txt
│   └── testSintactico_ERRONEO.txt
├── IDE.py                  # Aplicación principal del IDE
├── tokens.txt              # Tokens generados por el analizador léxico
├── tabla_simbolos.txt      # Tabla de símbolos generada
├── errores_semanticos.txt  # Errores semánticos encontrados
└── ast_anotado.json        # AST con anotaciones semánticas
```

🧮 Ejecución

1. **Preparar el código fuente**:
   - Abre o crea un archivo de código fuente en el IDE
   - O carga un archivo desde `test/` para probar

2. **Ejecutar el IDE**:
   ```bash
   python IDE.py
   ```

3. **Ejecutar las fases del compilador**:
   - **Análisis Léxico**: Menú `Compilar → Análisis Léxico`
     - Genera `tokens.txt`
     - Muestra tokens en la pestaña correspondiente
   
   - **Análisis Sintáctico**: Menú `Compilar → Análisis Sintáctico`
     - Requiere que `tokens.txt` exista (se ejecuta léxico automáticamente si falta)
     - Genera el AST
     - Muestra el árbol sintáctico en la pestaña correspondiente
   
   - **Análisis Semántico**: Menú `Compilar → Análisis Semántico`
     - Requiere que el análisis sintáctico esté completo (se ejecuta automáticamente si falta)
     - Genera `tabla_simbolos.txt`, `errores_semanticos.txt`, `ast_anotado.json`
     - Muestra el árbol semántico anotado, tabla de símbolos y errores en las pestañas correspondientes

4. **Observar los resultados**:
   - Árboles sintáctico y semántico en las pestañas correspondientes
   - Tabla de símbolos en la pestaña "Tabla HASH"
   - Errores en la pestaña "Errores Semánticos"
   - Archivos generados en la raíz del proyecto

🔍 Árbol Sintáctico Abstracto

- Muestra tokens terminales en formato `lexema (línea:columna)`
- Estructura jerárquica que representa la sintaxis del programa
- Puede expandirse/colapsarse interactivamente
- Visualización clara de la estructura del código

🔍 Árbol Semántico Anotado

- **Anotaciones de tipo**: Cada nodo muestra su tipo inferido (int, float, bool)
- **Valores calculados**: Operaciones aritméticas muestran el resultado calculado
- **Propagación de valores**: Los valores se propagan desde los literales hasta las operaciones
- **Manejo de errores**: Nodos con errores se marcan como `: ERROR`
- **Operaciones especiales**:
  - `++/--`: Muestra el valor post-operación
  - Asignaciones compuestas: Muestra el valor calculado
  - Operaciones anidadas: Muestra valores en cada nivel

📊 Tabla de Símbolos

La tabla de símbolos incluye:
- **Nombre**: Identificador de la variable
- **Tipo**: Tipo de dato (int, float, bool)
- **Ámbito**: Scope donde se declara (global, local)
- **Valor**: Valor actual asignado (si existe)
- **Dirección**: Líneas donde aparece la variable (formato: `(5),(7),(7)`)

Para operaciones `++/--` y asignaciones compuestas, la línea aparece dos veces para indicar el uso doble de la variable.

🧱 Requisitos

- Python 3.10+
- PyQt5: `pip install pyqt5`

🧰 Próximas Fases

- ✅ Análisis Léxico - **Completado**
- ✅ Análisis Sintáctico - **Completado**
- ✅ Análisis Semántico - **Completado**
- ⏳ Generación de Código Intermedio - **Pendiente**
- ⏳ Optimización de código - **Pendiente**
- ⏳ Generación de código objeto - **Pendiente**

📝 Notas Técnicas

## Política de Errores
- **Errores no fatales**: Se reportan y el análisis continúa
- **Errores fatales**: Detienen el análisis y se marcan como FATAL

## Compatibilidad de Tipos
- `int ↔ int`: Permitido
- `float ↔ int`: Permitido (promoción int → float)
- `int ← float`: Error de incompatibilidad
- `bool`: Solo con expresiones booleanas

## Operaciones Aritméticas
- Resultado `float` si algún operando es `float`
- Resultado `int` si ambos operandos son `int`
- Operadores lógicos y relacionales producen `bool`

## Operaciones Especiales
- `++/--`: Se expanden semánticamente a `a = a + 1` o `a = a - 1`
- Asignaciones compuestas (`+=`, `-=`, etc.): Se expanden a asignaciones equivalentes
- Ambas operaciones registran dos apariciones de la variable en la misma línea

✍️ Autores

Equipo de Compiladores
Estudiantes de Ingeniería en Sistemas Computacionales
Universidad Autónoma de Aguascalientes
