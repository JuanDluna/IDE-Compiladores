# Proyecto de Compilador - Contexto General (Cursor AI)

## Descripción general
Este es un proyecto de compilador desarrollado en Python con un IDE propio construido con PyQt5. El compilador consta de varias fases, de las cuales ya se han implementado las siguientes:

- Analizador Léxico (lexical.py)
- Analizador Sintáctico (syntactic.py)
- Estructura del árbol sintáctico abstracto (AST) con treeNode.py
- Interfaz gráfica en Qt con soporte para mostrar errores y árboles

Actualmente, el objetivo es mejorar la fase de análisis sintáctico, garantizando que se generen correctamente los nodos del árbol y se respeten las reglas gramaticales definidas en EBNF.

---

## Archivos involucrados

### 1. lexical.py
Este archivo implementa el analizador léxico mediante una máquina de estados finita (determinista) que procesa el código fuente y genera un archivo `tokens.txt`.

- Entrada: código fuente (`.txt` o editor en IDE)
- Salida: `tokens.txt` con estructura `lexema<TAB>token<TAB>linea<TAB>columna`
- Tokens válidos:  
  - NUMERO_ENTERO  
  - NUMERO_FLOTANTE  
  - IDENTIFICADOR  
  - PALABRA_RESERVADA (e.g., `main`, `int`, `float`, `if`, `while`, etc.)  
  - DELIMITADOR (`{`, `}`, `;`, `(`, `)`, `,`)  
  - OPERADOR_ARITMETICO (`+`, `-`, `*`, `/`, `%`)  
  - OPERADOR_RELACIONAL (`<`, `>`, `<=`, `>=`, `==`, `!=`)  
  - OPERADOR_LOGICO (`&&`, `||`, `!`)  
  - OPERADOR_ASIGNACION (`=`, `+=`, `-=`, `*=`, `/=`, `++`, `--`)  

- Características:
  - En caso de errores léxicos se reportan con tipo, línea y columna.
  - Aplica la filosofía de "cadena más larga" para identificar tokens.

---

### 2. tokens.txt (Ejemplo de estructura)
x IDENTIFICADOR 2 5
= OPERADOR_ASIGNACION 2 7
45 NUMERO_ENTERO 2 9
; DELIMITADOR 2 11


---

### 3. syntactic.py
Implementa el **analizador sintáctico descendente** que:

- Lee tokens desde `tokens.txt`
- Usa un parser basado en reglas gramaticales EBNF
- Crea un árbol sintáctico abstracto con `ASTNode`
- Reporta errores sintácticos con mensajes detallados
- Tiene soporte parcial para `if`, `while`, `do-while`, `cin`, `cout`, expresiones, y asignaciones

#### Problemas actuales detectados:
- Falta procesamiento de nodos para estructuras de control (e.g., `if`, `while`, `do-while`, `cout`, `cin`)
- No se imprimen correctamente todos los nodos del árbol
- Algunos errores no se detectan correctamente o no detienen el análisis
- El nodo raíz es mostrado, pero no todos los nodos terminales (tokens) son visualizados
- Se deben omitir nodos intermedios como "Asignación" o "Expresión" y únicamente mostrar nodos de tokens reales

---

### 4. treeNode.py (en carpeta util)
Estructura de datos para el AST:

```python
class ASTNode:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children if children else []

    def add_child(self, node):
        self.children.append(node)

    def is_leaf(self):
        return len(self.children) == 0

    def to_dict(self):
        return {
            "name": self.name,
            "children": [child.to_dict() for child in self.children]
        }
```
Se usa para generar un árbol visual colapsable en el IDE con QTreeWidget.
##Requerimientos funcionales de la gramática (EBNF)
Ejemplo general de la gramática que debe reconocer el compilador:

programa → [tipo] main [()] { lista_declaracion }
lista_declaracion → declaracion*
declaracion → declaracion_variable | sentencia
declaracion_variable → tipo identificador (, identificador)* [= expresion] ;
sentencia → if | while | do-while | asignacion | cout | cin
asignacion → identificador = expresion ;
expresion → expresion_simple [operador_relacional expresion_simple]
expresion_simple → termino (op_suma termino)*
termino → factor (op_mult factor)*
factor → número | identificador | (expresion)


#Casos de prueba
## Caso de código válido
```C
main {
    int x, y, z;
    float a, b, c;
    suma = 45;
    x = 32.32;
    x = 23;
    y = 2 + 3 - 1;
    z = y + 7;
    y = y + 1;
    a=24.0+4-1/3*2+34-1;
    x=(5-3)*(8/2);
    y=5+3-2*4/7-9;
    z = 8 / 2 + 15 * 4;
    y = 14.54;
    if 2>3 then
        y = a + 3;
    else
        if 4>2 && true then
            b = 3.2;
        else
            b = 5.0;
        end
        y = y + 1;
    end
    a++;
    c--;
    x = 3 + 4;
    do
        y = (y + 1) * 2 + 1;
        while x > 7
            x = 6 + 8 / 9 * 8 / 3;
            cin >> x;
            mas = 36 / 7;
        end
    until y == 5
    while y == 0
        cin >> mas;
        cout << x;
    end
}
```

## Caso de error fatal
```
main {
    int x y z   // falta de comas y punto y coma
    x = ;
    if ( > 3) { y = 1; }
}

```


Errores comunes esperados
Tokens inesperados (e.g., x = ;)

Estructura inválida (e.g., if > 3)

Paréntesis no cerrados

Falta de punto y coma

Tipos no declarados o mal usados

Funcionalidad del IDE
Panel para análisis léxico y errores léxicos

Panel para análisis sintáctico (visualización del árbol sintáctico como carpetas)

Panel para errores sintácticos (con línea, columna y descripción)

Integración:
run_lexical_phase() ejecuta el análisis léxico y guarda tokens.txt

run_syntactic_phase() llama a syntactic.get_ast() y muestra el árbol

Los errores del análisis sintáctico se capturan y se muestran en syntax_errors_tab como texto

Objetivo actual
Reescribir o mejorar el archivo syntactic.py para que:

Procese correctamente toda la gramática (sentencias de control, entrada/salida, expresiones, etc.)

Omita nodos intermedios y solo muestre tokens reales en el árbol

Detenga el análisis si se detecta un error fatal

Genere errores detallados (tipo, línea, columna)

Funcione con el código ejemplo proporcionado por la profesora