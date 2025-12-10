# 📚 Documentación de la Fase 4: Generación de Código Intermedio (TAC)

## 🎯 Descripción General

La Fase 4 del compilador implementa la generación de código intermedio en formato TAC (Three Address Code) y un intérprete (máquina virtual) capaz de ejecutar dicho código. Esta fase integra directamente con el análisis semántico para generar código intermedio optimizado y ejecutable.

---

## 🏗️ Arquitectura

### Componentes Principales

1. **`TACGenerator`**: Clase responsable de generar código TAC desde el AST anotado
2. **`TACInterpreter`**: Clase que implementa una máquina virtual para ejecutar código TAC
3. **Función pública `generate_and_run_intermediate_code()`**: Orquesta la generación y ejecución

---

## 📋 Estructura del Código TAC

### Formato de Instrucciones

El código TAC generado sigue un formato de tres direcciones donde cada instrucción tiene la forma:

```
destino = operando1 operador operando2
```

### Tipos de Instrucciones Soportadas

#### 1. Asignaciones
```
variable = valor
temporal = expresion
```

#### 2. Operaciones Aritméticas
```
t0 = a + b
t1 = t0 * c
t2 = x / y
```

#### 3. Operaciones Relacionales y Lógicas
```
t0 = a > b
t1 = cond1 && cond2
t2 = !expr
```

#### 4. Saltos Condicionales
```
if condicion == false goto L1
if t0 == true goto L2
```

#### 5. Saltos Incondicionales
```
goto L1
```

#### 6. Entrada/Salida
```
cin >> variable
cout << expresion
```

#### 7. Etiquetas
```
L0:
L1:
```

---

## 🔧 Implementación Técnica

### TACGenerator

#### Generación de Temporales y Etiquetas

El generador TAC utiliza contadores internos para crear identificadores únicos:

- **Temporales**: `t0`, `t1`, `t2`, ... (generados con `new_temp()`)
- **Etiquetas**: `L0`, `L1`, `L2`, ... (generadas con `new_label()`)

#### Procesamiento del AST

El generador recorre el AST anotado semánticamente siguiendo esta estructura:

1. **Nodo Raíz (Programa)**: Procesa todos los hijos excepto nodos de formato (`main`, `{`, `}`)
2. **Declaraciones**: Las declaraciones de variables se procesan cuando tienen asignaciones iniciales
3. **Sentencias**: Cada tipo de sentencia tiene su propio método de procesamiento:
   - `process_statement()`: Dispatcher principal
   - `process_assignment()`: Asignaciones simples
   - `process_compound_assignment()`: Asignaciones compuestas (`+=`, `-=`, etc.)
   - `process_if_statement()`: Estructuras condicionales
   - `process_while_statement()`: Ciclos while
   - `process_do_while_statement()`: Ciclos do-while
   - `process_cin()` / `process_cout()`: Entrada/salida

#### Procesamiento de Expresiones

Las expresiones se procesan recursivamente:

1. **Literales**: Se asignan directamente o a un temporal
2. **Identificadores**: Se retorna el nombre de la variable
3. **Operaciones**: Se procesan los operandos primero, luego se genera la operación

**Ejemplo de procesamiento de expresión:**

```
Código fuente: y = 2 + 3 - 1

TAC generado:
t0 = 2 + 3
t1 = t0 - 1
y = t1
```

#### Manejo de Estructuras de Control

##### If-Then-Else

```python
if condición then
    bloque_then
else
    bloque_else
end
```

**TAC generado:**
```
t0 = <evaluar condición>
if t0 == false goto L1
<bloque then>
goto L2
L1:
<bloque else>
L2:
```

##### While

```python
while condición do
    bloque
end
```

**TAC generado:**
```
L0:
t0 = <evaluar condición>
if t0 == false goto L1
<bloque>
goto L0
L1:
```

##### Do-While (Do-Until)

```python
do
    bloque
until condición
```

**TAC generado:**
```
L0:
<bloque>
t0 = <evaluar condición>
if t0 == true goto L1
goto L0
L1:
```

### TACInterpreter

#### Memoria Virtual

El intérprete mantiene un diccionario `memory` que almacena:
- Variables del programa
- Temporales generados durante la ejecución
- Valores de expresiones calculadas

#### Ejecución de Instrucciones

El intérprete ejecuta instrucciones secuencialmente usando un contador de programa (`pc`):

1. **Carga de código**: Desde archivo o lista de instrucciones
2. **Construcción de mapeo de etiquetas**: Pre-procesa todas las etiquetas
3. **Ejecución**: Itera sobre las instrucciones hasta completar o encontrar error

#### Manejo de Errores

- **División por cero**: Retorna 0 en lugar de error
- **Variables no inicializadas**: Retorna 0 como valor por defecto
- **Loops infinitos**: Límite de pasos máximo (10000 por defecto)

---

## 🔄 Integración con Fases Previas

### Flujo de Datos

```
Análisis Léxico → Análisis Sintáctico → Análisis Semántico → Generación TAC → Ejecución
                                    ↓
                            AST Anotado + Tabla de Símbolos
                                    ↓
                            TACGenerator + TACInterpreter
```

### Uso de Anotaciones Semánticas

El generador TAC utiliza las anotaciones del análisis semántico:

- **Tipo de dato**: Para formatear valores correctamente
- **Valores calculados**: Para optimización de expresiones constantes

**Ejemplo:**

Si el análisis semántico calculó que `2 + 3 = 5`, el generador puede optimizar directamente a:

```
t0 = 5
```

En lugar de:

```
t0 = 2 + 3
```

---

## 📁 Archivos Generados

### `codigo_intermedio.tac`

Contiene todas las instrucciones TAC generadas, una por línea. Este archivo puede ser:
- Visualizado en la pestaña "Código Intermedio" del IDE
- Ejecutado por el intérprete TAC
- Utilizado para futuras fases (optimización, generación de código objeto)

**Ejemplo de archivo generado:**

```
t0 = 2 + 3
t1 = t0 - 1
y = t1
t2 = y + 7
z = t2
```

---

## 🧪 Ejemplos de Uso

### Ejemplo 1: Asignación Simple

**Código fuente:**
```c
int x;
x = 5;
```

**TAC generado:**
```
t0 = 5
x = t0
```

### Ejemplo 2: Expresión Aritmética

**Código fuente:**
```c
int y;
y = 2 + 3 - 1;
```

**TAC generado:**
```
t0 = 2 + 3
t1 = t0 - 1
y = t1
```

### Ejemplo 3: Estructura Condicional

**Código fuente:**
```c
if x > 0 then
    y = 1;
else
    y = 2;
end
```

**TAC generado:**
```
t0 = x > 0
if t0 == false goto L0
t1 = 1
y = t1
goto L1
L0:
t2 = 2
y = t2
L1:
```

### Ejemplo 4: Ciclo While

**Código fuente:**
```c
while x > 0 do
    x = x - 1;
end
```

**TAC generado:**
```
L0:
t0 = x > 0
if t0 == false goto L1
t1 = x - 1
x = t1
goto L0
L1:
```

### Ejemplo 5: Operaciones con ++/--

**Código fuente:**
```c
a++;
c--;
```

**TAC generado:**
```
t0 = a + 1
a = t0
t1 = c - 1
c = t1
```

---

## 🎮 Integración en el IDE

### Pestañas del IDE

1. **"Código Intermedio"**: Muestra el código TAC generado
2. **"Ejecución"**: Muestra la salida del programa ejecutado

### Menú de Compilación

Se agregó una nueva opción al menú "Compilar":
- **"Código Intermedio"**: Genera y ejecuta el código TAC

### Flujo en el IDE

1. Usuario ejecuta "Análisis Semántico"
2. Usuario ejecuta "Código Intermedio" (o "Compilar" que ejecuta todas las fases)
3. El IDE muestra:
   - Código TAC generado en la pestaña correspondiente
   - Resultado de la ejecución en la pestaña "Ejecución"

---

## 🐛 Manejo de Errores

### Errores en la Generación

- **AST inválido**: Se reporta error y no se genera código
- **Errores semánticos fatales**: Se bloquea la generación

### Errores en la Ejecución

- **Variable no inicializada**: Se usa 0 como valor por defecto
- **División por cero**: Se retorna 0
- **Loop infinito**: Se detiene después de 10000 pasos
- **Etiqueta no encontrada**: Se reporta error y se detiene la ejecución

---

## ✅ Pruebas Realizadas

### Archivo de Prueba: `test/testSemantico.txt`

Este archivo contiene un programa completo que prueba:

- ✅ Declaraciones de variables (int, float)
- ✅ Asignaciones simples
- ✅ Expresiones aritméticas complejas
- ✅ Estructuras condicionales anidadas (if-then-else)
- ✅ Operadores incremento/decremento (++, --)
- ✅ Ciclos do-while con estructuras anidadas
- ✅ Ciclos while
- ✅ Entrada/salida (cin, cout)
- ✅ Operaciones relacionales y lógicas

### Resultado de las Pruebas

El código TAC generado para `test/testSemantico.txt` debe:

1. ✅ Generarse sin errores
2. ✅ Ejecutarse correctamente
3. ✅ Mostrar la salida esperada en la pestaña "Ejecución"
4. ✅ Guardarse en `codigo_intermedio.tac`

---

## 🔍 Evidencias de Funcionamiento

### Archivos Generados

Después de ejecutar la fase 4, se genera:
- ✅ `codigo_intermedio.tac`: Código TAC completo

### Visualización en el IDE

- ✅ Pestaña "Código Intermedio": Muestra todas las instrucciones generadas
- ✅ Pestaña "Ejecución": Muestra la salida del programa (o errores si los hay)

### Ejemplo de Salida en IDE

**Pestaña "Código Intermedio":**
```
t0 = 2 + 3
t1 = t0 - 1
y = t1
...
```

**Pestaña "Ejecución":**
```
=== EJECUCIÓN EXITOSA ===

=== SALIDA DEL PROGRAMA ===
<valores impresos con cout>
```

---

## 📝 Notas Técnicas

### Optimizaciones Implementadas

1. **Uso de valores constantes**: Si una expresión es constante, se usa el valor directamente
2. **Temporales reutilizables**: Los temporales se generan secuencialmente y pueden reutilizarse
3. **Manejo eficiente de etiquetas**: Se construye un mapeo una sola vez antes de ejecutar

### Limitaciones Actuales

1. **Sin optimización avanzada**: No se optimiza el código generado (se puede mejorar)
2. **Sin manejo de tipos en tiempo de ejecución**: Los tipos se manejan implícitamente
3. **Sin soporte para funciones**: Solo se procesa el bloque `main`

### Extensiones Futuras

1. **Optimización de código**: Eliminar código muerto, optimizar expresiones constantes
2. **Generación de código objeto**: Compilar TAC a código máquina
3. **Soporte para funciones**: Generar código para llamadas a funciones

---

## 👥 Autores

Equipo de Compiladores  
Estudiantes de Ingeniería en Sistemas Computacionales  
Universidad Autónoma de Aguascalientes

---

## 📅 Fecha

2025

---

## 📚 Referencias

- Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006). *Compilers: Principles, Techniques, and Tools* (2nd ed.). Pearson.
- Three Address Code (TAC) format documentation
- Intermediate Representation (IR) standards


