import re
from enum import Enum, auto

# Palabras reservadas según el PDF
RESERVED_WORDS = {
    "if", "else", "end", "do", "while", "switch", "case", 
    "int", "float", "main", "cin", "cout", "then", "until"
}

TOKEN_PATTERNS = [
    # Operadores lógicos primero (máxima prioridad)
    ('OPERADOR_LOGICO', r'&&|\|\||!'),
    
    # Luego operadores relacionales
    ('OPERADOR_RELACIONAL', r'<=|>=|==|!=|<|>'),
    
    # Operadores aritméticos y otros
    ('OPERADOR_INCREMENTO', r'\+\+'),
    ('OPERADOR_DECREMENTO', r'--'),
    ('OPERADOR_POTENCIA', r'\*\*'),
    ('OPERADOR_COMPUESTO', r'[\+\-\*/%]='),
    ('OPERADOR_ARITMETICO', r'[\+\-\*/%]'),
    ('OPERADOR_ASIGNACION', r'='),
    
    # Números
    ('NUMERO_FLOTANTE', r'-?\d+\.\d+'),
    ('NUMERO_ENTERO', r'-?\d+'),
    
    # Identificadores
    ('IDENTIFICADOR', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    
    # Símbolos
    ('DELIMITADOR', r'[\(\)\[\]\{\},;]'),
]

def analizar_segmento(segmento):
    # Primero verificar si es palabra reservada
    if segmento in RESERVED_WORDS:
        return 'PALABRA_RESERVADA'
    
    # Probar cada patrón en orden de prioridad
    for token_type, pattern in TOKEN_PATTERNS:
        if re.fullmatch(pattern, segmento):
            return token_type
    
    return 'ERROR'


def analizar_linea(linea, num_linea):
    tokens = []
    errores = []
    i = 0
    n = len(linea)
    
    while i < n:
        char = linea[i]
        
        # Saltar espacios
        if char.isspace():
            i += 1
            continue
            
        # Buscar el token más largo posible
        matched = False
        for token_type, pattern in TOKEN_PATTERNS:
            regex = re.compile(pattern)
            match = regex.match(linea, i)
            
            if match:
                value = match.group()
                # Verificar si es palabra reservada
                if token_type == 'IDENTIFICADOR' and value in RESERVED_WORDS:
                    token_type = 'PALABRA_RESERVADA'
                
                tokens.append({
                    'line': num_linea,
                    'column': i+1,
                    'lexema': value,
                    'tipo': token_type
                })
                i += len(value)
                matched = True
                break
        
        if not matched:
            # Manejar errores léxicos
            errores.append({
                'line': num_linea,
                'column': i+1,
                'value': char,
                'descripcion': 'Símbolo no reconocido'
            })
            i += 1
    
    return tokens, errores

def analizar_codigo_fuente(codigo):
    tokens = []
    errores = []
    lineas = codigo.split('\n')
    
    for num_linea, linea in enumerate(lineas, start=1):
        # Saltar líneas vacías
        if not linea.strip():
            continue
            
        # Manejar comentarios multilínea (implementación básica)
        if '/*' in linea and '*/' in linea:
            tokens.append({
                'line': num_linea,
                'column': linea.index('/*') + 1,
                'lexema': linea[linea.index('/*'):linea.index('*/')+2],
                'tipo': 'COMENTARIO_MULTILINEA'
            })
            continue
            
        line_tokens, line_errors = analizar_linea(linea, num_linea)
        tokens.extend(line_tokens)
        errores.extend(line_errors)
    
    return tokens, errores

# Las funciones restantes permanecen igual...

def generar_tabla_tokens(tokens):
    output = "Línea\tColumna\tToken\t\tTipo\n"
    output += "-" * 50 + "\n"
    for token in tokens:
        output += f"{token['line']}\t{token['column']}\t{token['lexema']}\t\t{token['tipo']}\n"
    return output

def generar_tabla_errores(errores):
    if not errores:
        return "Sin errores léxicos encontrados."
    
    output = "Línea\tColumna\tCarácter\tDescripción\n"
    output += "-" * 60 + "\n"
    for error in errores:
        output += f"{error['line']}\t{error['column']}\t{error['value']}\t\t{error['descripcion']}\n"
    return output

def analizar_desde_archivo(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        codigo = f.read()

    tokens, errores = analizar_codigo_fuente(codigo)
    
    # Guardar tokens en archivo
    with open("tokens.txt", "w", encoding="utf-8") as f:
        for token in tokens:
            f.write(f"{token['line']}\t{token['column']}\t{token['lexema']}\t{token['tipo']}\n")
    
    return generar_tabla_tokens(tokens), generar_tabla_errores(errores)