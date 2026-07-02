# Compilador Educativo con IDE Gráfico

> **Compiladores** · Built by [Juan D. Luna](https://github.com/JuanDluna) · Fullstack & Mobile Developer

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white) ![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?style=flat-square&logo=qt&logoColor=white) ![Compilers](https://img.shields.io/badge/Compilers-TAC-orange?style=flat-square)

Compilador modular en Python con interfaz gráfica desarrollada en PyQt5. Implementa las fases principales de un compilador — léxico, sintáctico, semántico y generación de código intermedio — con visualización interactiva de cada fase.

## Características

### Análisis Léxico
- Generación de `tokens.txt` con formato: `LEXEMA<TAB>TOKEN<TAB>LINEA<TAB>COLUMNA`
- Reconocimiento de identificadores, números, operadores y delimitadores
- Detección de comentarios unilínea y multilínea
- Manejo de palabras reservadas

### Análisis Sintáctico
- Analizador descendente recursivo (LL)
- Generación de Árbol Sintáctico Abstracto (AST)
- Estructuras de control: `if-then-else-end`, `while-end`, `do-while-until`
- Entrada/salida: `cin >>`, `cout <<`
- Declaraciones de variables: `int`, `float`, `bool`
- Operaciones aritméticas, relacionales y lógicas
- Manejo de errores sintácticos con recuperación

### Análisis Semántico
- Construcción de tabla de símbolos (nombre, tipo, ámbito, valor, ubicaciones de uso)
- Verificación de tipos con promoción `int → float`
- Detección de errores: variables no declaradas, duplicidad, incompatibilidad de tipos
- AST anotado con tipos heredados y propagación de valores constantes
- Archivos generados: `tabla_simbolos.txt`, `errores_semanticos.txt`, `ast_anotado.json`

### Generación de Código Intermedio (TAC)
- Generación de Three Address Code desde el AST anotado semánticamente
- Intérprete TAC (máquina virtual) con ejecución paso a paso e interactiva
- Soporte para asignaciones, operaciones aritméticas, relacionales y lógicas
- Saltos condicionales e incondicionales, etiquetas, `cin >>` y `cout <<`
- Visualización del código TAC en la pestaña **Código Intermedio**

### IDE Gráfico (PyQt5)
- Editor con resaltado de sintaxis, números de línea y scroll
- Paneles por fase: léxico, sintáctico, semántico, TAC, ejecución y tabla HASH
- Árboles interactivos con expansión/colapsado de nodos
- Ejecución interactiva del TAC con entrada/salida en tiempo real

## Flujo del Compilador

```
Código fuente (.txt)
        │
        ▼
┌───────────────────┐
│  Análisis Léxico  │  →  tokens.txt
└───────────────────┘
        │
        ▼
┌───────────────────────┐
│  Análisis Sintáctico  │  →  AST
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│  Análisis Semántico   │  →  tabla_simbolos.txt
│                       │     errores_semanticos.txt
│                       │     ast_anotado.json
└───────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  Generación de Código TAC     │  →  Código Intermedio (pestaña)
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  Ejecución (Intérprete TAC)   │  →  Salida interactiva
└───────────────────────────────┘
```

## Estructura del Proyecto

```
.
├── phases/
│   ├── __init__.py
│   ├── lexical.py            # Analizador léxico
│   ├── syntactic.py          # Analizador sintáctico (LL)
│   ├── semantic.py           # Analizador semántico
│   └── intermediate_code.py  # Generación TAC e intérprete
├── util/
│   ├── treeNode.py           # Clase ASTNode para el AST
│   └── symbol_table.py       # Tabla de símbolos y ámbitos
├── test/
│   ├── testLexico.txt
│   ├── testSemantico.txt
│   ├── testSintactico_VALIDO.txt
│   ├── testSintactico_VALIDO2.txt
│   ├── testSintactico_ERRONEO.txt
│   └── finales/              # Ejercicios de evaluación
├── IDE.py                    # Aplicación principal del IDE
├── Documentacion_Fase_4.md   # Documentación detallada del TAC
├── requirements.txt
├── LICENSE.md
└── README.md
```

## Instalación y Ejecución

### Requisitos previos

- Python 3.10 o superior

### Instalación

```bash
git clone https://github.com/JuanDluna/IDE-Compiladores.git
cd IDE-Compiladores
pip install -r requirements.txt
```

### Ejecutar el IDE

```bash
python IDE.py
```

### Compilar un programa

1. Abre o crea un archivo de código fuente en el editor (puedes cargar ejemplos desde `test/`).
2. Guarda el archivo antes de compilar.
3. Ejecuta el pipeline completo con **Compilar → Compilar** (o el botón de compilar en la barra de herramientas).

Esto ejecuta automáticamente las cuatro fases en orden: léxico → sintáctico → semántico → código intermedio.

### Ejecutar fases individualmente

Desde el menú **Compilar**:

| Fase | Menú | Salida |
|------|------|--------|
| Léxico | Análisis Léxico | `tokens.txt` + pestaña Análisis Léxico |
| Sintáctico | Análisis Sintáctico | AST en pestaña Análisis Sintáctico |
| Semántico | Análisis Semántico | `tabla_simbolos.txt`, `errores_semanticos.txt`, `ast_anotado.json` |
| TAC | Código Intermedio | Código TAC en pestaña Código Intermedio |

Cada fase ejecuta automáticamente las fases previas si aún no se han completado.

### Ejecutar el código TAC

1. Completa el análisis semántico (o compila el programa completo).
2. Ve a la pestaña **Ejecución**.
3. Presiona **Ejecutar** para iniciar la máquina virtual TAC.
4. Proporciona valores de entrada cuando el programa lo solicite (`cin >>`).

## Fases del Compilador

| Fase | Estado |
|------|--------|
| Análisis Léxico | ✅ Completado |
| Análisis Sintáctico | ✅ Completado |
| Análisis Semántico | ✅ Completado |
| Generación de Código Intermedio (TAC) | ✅ Completado |
| Optimización de código | ⏳ Fuera de alcance |
| Generación de código objeto | ⏳ Fuera de alcance |

## Notas Técnicas

### Política de Errores
- **Errores no fatales**: se reportan y el análisis continúa.
- **Errores fatales**: detienen el análisis y se marcan como FATAL.

### Compatibilidad de Tipos
- `int ↔ int`: permitido
- `float ↔ int`: permitido (promoción `int → float`)
- `int ← float`: error de incompatibilidad
- `bool`: solo con expresiones booleanas

### Operaciones Especiales
- `++/--`: se expanden semánticamente a `a = a + 1` o `a = a - 1`
- Asignaciones compuestas (`+=`, `-=`, etc.): se expanden a asignaciones equivalentes

## Tecnologías

| Tecnología | Uso |
|------------|-----|
| **Python 3.10+** | Lenguaje principal del compilador |
| **PyQt5** | Interfaz gráfica del IDE |
| **Análisis LL** | Parser descendente recursivo |
| **TAC (Three Address Code)** | Representación intermedia del código |
| **JSON** | Serialización del AST anotado |

## Licencia

Este proyecto está licenciado bajo la [GNU Lesser General Public License v3.0](LICENSE.md).

## Autor

**Juan D. Luna** — Fullstack & Mobile Engineer

[![GitHub](https://img.shields.io/badge/GitHub-JuanDluna-181717?style=flat-square&logo=github)](https://github.com/JuanDluna)

Universidad Autónoma de Aguascalientes

---

*Part of my professional portfolio. See more projects at [github.com/JuanDluna](https://github.com/JuanDluna)*
