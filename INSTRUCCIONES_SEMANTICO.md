# Instrucciones para la Fase Semántica

## Archivos Generados

La implementación de la fase semántica incluye los siguientes archivos:

1. **`phases/semantic.py`** - Analizador semántico principal
2. **`util/symbol_table.py`** - Clase para manejo de tabla de símbolos con ámbitos

## Integración en el IDE

La función `run_semantic_phase()` en `IDE.py` ya está actualizada para usar el analizador semántico. No se requiere configuración adicional.

## Uso desde el IDE

1. Abre el IDE ejecutando: `python IDE.py`
2. Abre o crea un archivo de código fuente
3. Ejecuta el análisis léxico (menú Compilar → Análisis Léxico)
4. Ejecuta el análisis sintáctico (menú Compilar → Análisis Sintáctico)
5. Ejecuta el análisis semántico (menú Compilar → Análisis Semántico)

## Uso desde Línea de Comandos

### Ejecutar análisis semántico directamente:

```python
from phases import semantic

# Obtener resultados (lee AST desde syntactic.get_ast())
ast_anotado, tabla_simbolos, errores = semantic.get_semantic_results()

# O pasar un AST personalizado
from phases import syntactic
ast_root, parser_errors = syntactic.get_ast()
ast_anotado, tabla_simbolos, errores = semantic.get_semantic_results(ast_root)
```

### Ejecutar como script:

```bash
python phases/semantic.py
```

Esto ejecutará el análisis semántico sobre el archivo `tokens.txt` generado por la fase léxica.

## Archivos Generados

Al ejecutar el análisis semántico, se generan automáticamente los siguientes archivos en la raíz del proyecto:

1. **`tabla_simbolos.txt`** - Tabla de símbolos con formato:
   ```
   nombre	tipo	ambito	direccion
   x	int	global	0
   y	float	global	1
   ```

2. **`errores_semanticos.txt`** - Errores semánticos encontrados:
   ```
   TIPO	descripcion	linea:columna	FATAL
   VARIABLE_NO_DECLARADA	Variable 'suma' no declarada	4:5
   ```

3. **`ast_anotado.json`** - AST con anotaciones semánticas (tipos y valores):
   ```json
   {
     "name": "Programa",
     "children": [
       {
         "name": "Declaración",
         "type": "int",
         "loc": "2:5",
         "children": [...]
       }
     ]
   }
   ```

## API Principal

### `get_semantic_results(ast_root=None)`

Función principal que realiza el análisis semántico completo.

**Parámetros:**
- `ast_root` (ASTNode, opcional): AST a analizar. Si es `None`, se obtiene automáticamente desde `syntactic.get_ast()`

**Retorna:**
- `ast_anotado_dict`: Diccionario con el AST anotado (serializable a JSON)
- `tabla_simbolos_list`: Lista de diccionarios con entradas de la tabla de símbolos
- `errores_list`: Lista de diccionarios con errores semánticos encontrados

**Ejemplo:**
```python
ast_anotado, tabla, errores = semantic.get_semantic_results()

print(f"Entradas en tabla: {len(tabla)}")
print(f"Errores: {len(errores)}")
```

## Errores Semánticos Detectados

El analizador detecta los siguientes tipos de errores:

1. **VARIABLE_NO_DECLARADA** - Uso de variable no declarada
2. **DUPLICIDAD_DECLARACION** - Variable declarada dos veces en el mismo ámbito
3. **TIPO_INCOMPATIBLE** - Incompatibilidad de tipos en asignaciones u operaciones
4. **AST_INVALIDO** - Error fatal si el AST no es válido

## Reglas de Compatibilidad de Tipos

- `int ↔ int`: Permitido
- `float ↔ int`: Permitido (promoción int → float)
- `int ← float`: **Error** (no se puede asignar float a int)
- `bool`: Solo compatible con bool
- Operaciones aritméticas: Resultado es `float` si algún operando es `float`, sino `int`
- Operadores lógicos (`&&`, `||`, `!`): Requieren operandos `bool`
- Operadores relacionales: Producen `bool`, permiten comparar `int` y `float`

## Pruebas

### Probar con testSemantico.txt:

1. Ejecutar análisis léxico sobre `test/testSemantico.txt`
2. Ejecutar análisis sintáctico
3. Ejecutar análisis semántico
4. Verificar archivos generados:
   - `tabla_simbolos.txt` debe contener variables declaradas
   - `errores_semanticos.txt` debe reportar el error de variable no declarada (`suma = 45;`)

### Casos de Prueba Incluidos:

- ✅ Declaraciones múltiples (`int x, y, z;`)
- ✅ Asignación con inferencia de tipos (`float a = 24.0 + 4 - ...`)
- ✅ Operadores `++` y `--` (expandidos por el parser)
- ✅ `cin` y `cout` (no requieren verificación de tipos especial)
- ✅ Variable no declarada (`suma = 45;` → error semántico)
- ✅ Incompatibilidad de tipos (`int x = 32.32;` → error)

## Estructura del Código

### Clases Principales:

1. **`SemanticAnalyzer`**: Analizador principal que recorre el AST
   - `analyze(ast_root)`: Método principal de análisis
   - `analyze_expression(node)`: Analiza expresiones y retorna tipo
   - `analyze_statement(node)`: Analiza sentencias
   - `analyze_declaracion(node)`: Analiza declaraciones de variables

2. **`SymbolTable`**: Tabla de símbolos con soporte de ámbitos
   - `enter_scope(name)`: Entra en un nuevo ámbito
   - `exit_scope()`: Sale del ámbito actual
   - `declare(name, type, line, col)`: Declara una variable
   - `lookup(name)`: Busca una variable

3. **`SemanticError`**: Representa un error semántico
   - Atributos: `tipo`, `descripcion`, `linea`, `columna`, `fatal`

## Notas Técnicas

- Los nodos terminales del AST tienen formato: `"lexema (linea:columna)"`
- El analizador parsea este formato para extraer información de ubicación
- Las anotaciones se almacenan en un diccionario paralelo (no se modifica `ASTNode`)
- El AST anotado se serializa a JSON para visualización
- Los errores no fatales permiten continuar el análisis
- Los errores fatales detienen el análisis inmediatamente

## Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'phases'"
- Asegúrate de ejecutar desde el directorio raíz del proyecto
- Verifica que exista `phases/__init__.py` (puede estar vacío)

### Error: "El AST está vacío o es None"
- Ejecuta primero el análisis sintáctico
- Verifica que `tokens.txt` exista y tenga contenido válido

### No se generan archivos
- Verifica permisos de escritura en el directorio
- Revisa la consola para mensajes de error

