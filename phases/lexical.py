import re
import os
from enum import Enum, auto

# Lista de palabras reservadas
RESERVED_WORDS = {
    "if", "else", "while", "for", "return", "int", "float", "char", 
    "void", "string", "bool", "true", "false", "break", "continue"
}

# Estados del autómata
class State(Enum):
    INITIAL = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    OPERATOR_ARITHMETIC = auto()
    OPERATOR_RELATIONAL = auto()
    OPERATOR_LOGICAL = auto()
    OPERATOR_ASSIGNMENT = auto()  # Nuevo estado para asignación
    OPERATOR_COMPOUND_ASSIGNMENT = auto()  # Para +=, -=, etc.
    DELIMITER = auto()
    STRING = auto()
    CHAR = auto()
    COMMENT_SINGLE = auto()
    COMMENT_MULTI = auto()
    COMMENT_MULTI_END = auto()
    WHITESPACE = auto()
    NEWLINE = auto()
    ERROR = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

def analizar_codigo_fuente(codigo):
    tokens = []
    errores = []
    current_line = 1
    i = 0
    n = len(codigo)
    
    while i < n:
        state = State.INITIAL
        lexeme = ""
        start_pos = i
        start_line = current_line
        
        while state != State.ERROR and i < n:
            char = codigo[i]
            
            # Máquina de estados finitos
            if state == State.INITIAL:
                if char.isspace():
                    if char == '\n':
                        state = State.NEWLINE
                    else:
                        state = State.WHITESPACE
                elif char.isalpha() or char == '_':
                    state = State.IDENTIFIER
                elif char.isdigit():
                    state = State.INTEGER
                elif char in {'+', '-', '*', '/'}:
                    # Podría ser operador aritmético o parte de asignación compuesta
                    state = State.OPERATOR_ARITHMETIC
                elif char == '%':
                    state = State.OPERATOR_ARITHMETIC
                elif char in {'<', '>'}:
                    state = State.OPERATOR_RELATIONAL
                elif char == '=':
                    state = State.OPERATOR_ASSIGNMENT
                elif char == '!':
                    state = State.NOT
                elif char == '&':
                    state = State.AND
                elif char == '|':
                    state = State.OR
                elif char in {'(', ')', '{', '}', ',', ';'}:
                    state = State.DELIMITER
                elif char == '"':
                    state = State.STRING
                elif char == "'":
                    state = State.CHAR
                elif char == '/':
                    # Verificar si es comentario
                    if i + 1 < n:
                        next_char = codigo[i+1]
                        if next_char == '/':
                            state = State.COMMENT_SINGLE
                        elif next_char == '*':
                            state = State.COMMENT_MULTI
                            i += 1  # Consume el '*'
                        else:
                            state = State.OPERATOR_ARITHMETIC
                else:
                    state = State.ERROR
                
            elif state == State.IDENTIFIER:
                if not (char.isalnum() or char == '_'):
                    break
                
            elif state == State.INTEGER:
                if char == '.':
                    state = State.FLOAT
                elif not char.isdigit():
                    break
                
            elif state == State.FLOAT:
                if not char.isdigit():
                    break
                
            elif state == State.OPERATOR_RELATIONAL:
                if char != '=':
                    break
                
            elif state == State.OPERATOR_ARITHMETIC:
                if char == '=':
                    state = State.OPERATOR_COMPOUND_ASSIGNMENT
                    i += 1  # Consume el '='
                    break
                else:
                    break
                    
            elif state == State.OPERATOR_ASSIGNMENT:
                # Verificar si es asignación simple o relacional (==)
                if char == '=':
                    state = State.OPERATOR_RELATIONAL
                    i += 1  # Consume el segundo '='
                    break
                else:
                    break
                    
            elif state == State.AND:
                if char != '&':
                    state = State.ERROR
                else:
                    state = State.OPERATOR_LOGICAL
                    i += 1  # Consume el segundo '&'
                    break
                
            elif state == State.OR:
                if char != '|':
                    state = State.ERROR
                else:
                    state = State.OPERATOR_LOGICAL
                    i += 1  # Consume el segundo '|'
                    break
                    
            elif state == State.NOT:
                if char == '=':
                    state = State.OPERATOR_RELATIONAL
                    i += 1  # Consume el '='
                    break
                else:
                    state = State.OPERATOR_LOGICAL
                    break
                    
            elif state == State.STRING:
                if char == '"':
                    i += 1  # Consume la comilla de cierre
                    break
                elif char == '\n':
                    state = State.ERROR
                    break
                    
            elif state == State.CHAR:
                if char == "'":
                    i += 1  # Consume la comilla de cierre
                    break
                elif len(lexeme) > 3:  # 'x' tiene 3 caracteres
                    state = State.ERROR
                    break
                    
            elif state == State.COMMENT_SINGLE:
                if char == '\n':
                    state = State.NEWLINE
                    break
                    
            elif state == State.COMMENT_MULTI:
                if char == '*' and i + 1 < n and codigo[i+1] == '/':
                    state = State.COMMENT_MULTI_END
                    i += 1  # Consume el '/'
                    break
                elif char == '\n':
                    current_line += 1
                    
            # No necesitamos procesar estos estados más allá
            elif state in {State.WHITESPACE, State.NEWLINE, State.DELIMITER, 
                          State.OPERATOR_COMPOUND_ASSIGNMENT, State.COMMENT_MULTI_END}:
                break
                
            lexeme += char
            i += 1
        
        # Procesar el token reconocido
        if state != State.ERROR and lexeme:
            token_type = get_token_type(state, lexeme)
            if token_type not in {"ESPACIO", "NUEVA_LINEA", "COMENTARIO_SIMPLE", "COMENTARIO_MULTILINEA_INICIO", 
                                 "COMENTARIO_MULTILINEA_FIN"}:
                tokens.append({"line": start_line, "lexema": lexeme, "tipo": token_type})
            
            if state == State.NEWLINE:
                current_line += 1
        elif state == State.ERROR:
            errores.append({"line": start_line, "lexema": codigo[start_pos], "descripcion": "Símbolo no reconocido"})
            i = start_pos + 1  # Avanza al siguiente carácter
    
    return tokens, errores

def get_token_type(state, lexeme):
    """Mapea el estado del autómata al tipo de token"""
    if state == State.IDENTIFIER:
        return "PALABRA_RESERVADA" if lexeme in RESERVED_WORDS else "IDENTIFICADOR"
    elif state == State.INTEGER:
        return "ENTERO"
    elif state == State.FLOAT:
        return "FLOTANTE"
    elif state == State.OPERATOR_ARITHMETIC:
        return "OPERADOR_ARITMETICO"
    elif state == State.OPERATOR_RELATIONAL:
        return "OPERADOR_RELACIONAL"
    elif state == State.OPERATOR_LOGICAL:
        return "OPERADOR_LOGICO"
    elif state == State.OPERATOR_ASSIGNMENT:
        return "OPERADOR_ASIGNACION"
    elif state == State.OPERATOR_COMPOUND_ASSIGNMENT:
        return "OPERADOR_ASIGNACION"  # Puedes usar otro tipo si prefieres diferenciarlos
    elif state == State.DELIMITER:
        return "DELIMITADOR"
    elif state == State.STRING:
        return "CADENA"
    elif state == State.CHAR:
        return "CARACTER"
    elif state == State.AND:
        return "OPERADOR_LOGICO" if lexeme == "&&" else "ERROR"
    elif state == State.OR:
        return "OPERADOR_LOGICO" if lexeme == "||" else "ERROR"
    elif state == State.NOT:
        return "OPERADOR_LOGICO" if lexeme == "!" else "ERROR"
    elif state == State.COMMENT_SINGLE:
        return "COMENTARIO_SIMPLE"
    elif state == State.COMMENT_MULTI:
        return "COMENTARIO_MULTILINEA_INICIO"
    elif state == State.COMMENT_MULTI_END:
        return "COMENTARIO_MULTILINEA_FIN"
    elif state == State.WHITESPACE:
        return "ESPACIO"
    elif state == State.NEWLINE:
        return "NUEVA_LINEA"
    return "ERROR"

# Las siguientes funciones se mantienen exactamente igual para mantener compatibilidad con el IDE
def generar_tabla_tokens(tokens):
    output = "Línea\tToken\t\tTipo\n"
    output += "-" * 40 + "\n"
    for token in tokens:
        linea = token["line"]
        lexema = token["lexema"]
        tipo = token["tipo"]
        output += f"{linea}\t{lexema}\t\t{tipo}\n"
    return output

def generar_tabla_errores(errores):
    if not errores:
        return "Sin errores léxicos encontrados."

    output = "Línea\tLexema\t\tDescripción\n"
    output += "-" * 50 + "\n"
    for error in errores:
        output += f"{error['line']}\t{error['lexema']}\t\t{error['descripcion']}\n"
    return output

def guardar_tokens_en_archivo(tokens, ruta_base):
    nombre_archivo = os.path.splitext(os.path.basename(ruta_base))[0]
    ruta_archivo = os.path.join(os.path.dirname(ruta_base), f"{nombre_archivo}_tokens.txt")
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        for token in tokens:
            f.write(f"{token['line']}\t{token['lexema']}\t{token['tipo']}\n")

def analizar_desde_archivo(ruta_archivo):
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        codigo = f.read()

    tokens, errores = analizar_codigo_fuente(codigo)
    
    # Generar tablas para mostrar en el IDE
    tabla_tokens = generar_tabla_tokens(tokens)  # Con cabeceras para mostrar en el IDE
    tabla_errores = generar_tabla_errores(errores)  # Con cabeceras para mostrar en el IDE
    
    # Guardar archivo tokens.txt en raíz del proyecto (sin cabeceras)
    with open("tokens.txt", "w", encoding="utf-8") as f:
        for token in tokens:
            f.write(f"{token['line']}\t{token['lexema']}\t{token['tipo']}\n")

    return tabla_tokens, tabla_errores