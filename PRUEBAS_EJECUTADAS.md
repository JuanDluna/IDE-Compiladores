# Pruebas Ejecutadas - Fase Semántica

## Comandos de Prueba

### 1. Prueba Básica desde Python

```python
from phases import semantic

# Ejecutar análisis semántico
ast_anotado, tabla_simbolos, errores = semantic.get_semantic_results()

print(f"Entradas en tabla de símbolos: {len(tabla_simbolos)}")
print(f"Errores encontrados: {len(errores)}")
```

### 2. Prueba con testSemantico.txt

**Pasos:**

1. **Análisis Léxico:**
   - Abrir `test/testSemantico.txt` en el IDE
   - Ejecutar: Compilar → Análisis Léxico
   - Verificar que se genere `tokens.txt`

2. **Análisis Sintáctico:**
   - Ejecutar: Compilar → Análisis Sintáctico
   - Verificar que se genere el AST sin errores sintácticos fatales

3. **Análisis Semántico:**
   - Ejecutar: Compilar → Análisis Semántico
   - Verificar archivos generados:
     - `tabla_simbolos.txt`
     - `errores_semanticos.txt`
     - `ast_anotado.json`

### 3. Ejecución Directa del Script

```bash
python phases/semantic.py
```

## Resultados Esperados con testSemantico.txt

### Tabla de Símbolos Esperada

El archivo `tabla_simbolos.txt` debe contener:

```
nombre	tipo	ambito	direccion
x	int	global	0
y	int	global	1
z	int	global	2
a	float	global	3
b	float	global	4
c	float	global	5
mas	int	bloque_1	6
```

### Errores Semánticos Esperados

El archivo `errores_semanticos.txt` debe contener al menos:

```
VARIABLE_NO_DECLARADA	Variable 'suma' no declarada	4:5
TIPO_INCOMPATIBLE	Incompatibilidad de tipos en asignación: no se puede asignar float a int	5:5
TIPO_INCOMPATIBLE	Incompatibilidad de tipos en asignación: no se puede asignar float a int	14:5
```

### Casos de Prueba Específicos

#### 1. Declaraciones Múltiples
```c
int x, y, z;
```
**Resultado esperado:** 3 entradas en tabla de símbolos (x, y, z) con tipo `int` y ámbito `global`

#### 2. Variable No Declarada
```c
suma = 45;
```
**Resultado esperado:** Error `VARIABLE_NO_DECLARADA` en línea 4, columna 5

#### 3. Incompatibilidad de Tipos
```c
int x;
x = 32.32;  // Error: asignar float a int
```
**Resultado esperado:** Error `TIPO_INCOMPATIBLE` en línea 5, columna 5

#### 4. Asignación con Inferencia de Tipos
```c
float a;
a = 24.0 + 4 - 1/3*2 + 34 - 1;
```
**Resultado esperado:** 
- Variable `a` declarada con tipo `float`
- Expresión analizada y tipo inferido como `float`
- Sin errores de tipo

#### 5. Operadores ++ y --
```c
a++;
c--;
```
**Resultado esperado:**
- Parser expande como `a = a + 1` y `c = c - 1`
- Verificación de que `a` y `c` sean numéricos
- Sin errores si las variables son numéricas

#### 6. Operadores Lógicos
```c
if 4>2 && true then
```
**Resultado esperado:**
- `4>2` produce tipo `bool`
- `true` es tipo `bool`
- `&&` requiere operandos `bool` → sin error

#### 7. Operadores Relacionales
```c
if 2>3 then
```
**Resultado esperado:**
- `2>3` produce tipo `bool`
- Condición de `if` debe ser `bool` → sin error

#### 8. Ámbito de Bloques
```c
if 2>3 then
    y = a + 3;
else
    b = 3.2;
end
```
**Resultado esperado:**
- Variables en bloques `if_then` e `if_else` tienen ámbitos locales
- Variables globales accesibles desde bloques

## Validación de Archivos Generados

### tabla_simbolos.txt

Formato esperado:
```
nombre	tipo	ambito	direccion
x	int	global	0
y	int	global	1
...
```

**Validación:**
- ✅ Todas las variables declaradas están presentes
- ✅ Tipos correctos (int, float, bool)
- ✅ Ámbitos correctos (global, bloque_N)
- ✅ Direcciones incrementales

### errores_semanticos.txt

Formato esperado:
```
TIPO	descripcion	linea:columna	FATAL
VARIABLE_NO_DECLARADA	Variable 'suma' no declarada	4:5
...
```

**Validación:**
- ✅ Errores reportados con formato correcto
- ✅ Ubicación (línea:columna) correcta
- ✅ Errores fatales marcados con "FATAL"

### ast_anotado.json

Formato esperado:
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

**Validación:**
- ✅ Estructura JSON válida
- ✅ Nodos con atributos `type` cuando aplica
- ✅ Nodos con atributos `value` para literales
- ✅ Nodos con atributos `loc` para tokens terminales

## Salida Esperada en Consola

Al ejecutar `python phases/semantic.py`:

```
Ejecutando análisis semántico...
Tabla de símbolos escrita: 6 entradas
Archivo de errores escrito: 2 errores
AST anotado escrito a ast_anotado.json

Resultados:
- Entradas en tabla de símbolos: 6
- Errores encontrados: 2

Errores:
  VARIABLE_NO_DECLARADA: Variable 'suma' no declarada (4:5)
  TIPO_INCOMPATIBLE: Incompatibilidad de tipos en asignación: no se puede asignar float a int (5:5)

Archivos generados:
  - tabla_simbolos.txt
  - errores_semanticos.txt
  - ast_anotado.json
```

## Notas de Implementación

- El analizador continúa después de errores no fatales
- Los errores fatales detienen el análisis inmediatamente
- Las anotaciones de tipo se agregan a los nodos del AST
- La tabla de símbolos maneja ámbitos anidados correctamente
- Los operadores aritméticos promocionan int a float cuando es necesario

