import re
import os

# Lista de palabras reservadas
RESERVED_WORDS = {
    "if", "else", "while", "for", "return", "int", "float", "char", "void", "string", "bool", "true", "false", "break", "continue"
}

# Expresiones regulares por tipo de token
TOKEN_REGEX = [
    ("COMENTARIO_MULTILINEA_INICIO", re.compile(r"/\*")),
    ("COMENTARIO_MULTILINEA_FIN", re.compile(r"\*/")),
    ("COMENTARIO_SIMPLE", re.compile(r"//.*")),
    ("ESPACIO", re.compile(r"[ \t]+")),
    ("NUEVA_LINEA", re.compile(r"\n")),
    ("ENTERO", re.compile(r"\b\d+\b")),
    ("FLOTANTE", re.compile(r"\b\d+\.\d+\b")),
    ("IDENTIFICADOR", re.compile(r"\b[a-zA-Z_][a-zA-Z_0-9]*\b")),
    ("OPERADOR_ARITMETICO", re.compile(r"[+\-*/%]")),
    ("OPERADOR_RELACIONAL", re.compile(r"(==|!=|<=|>=|<|>)")),
    ("OPERADOR_LOGICO", re.compile(r"(&&|\|\||!)")),
    ("OPERADOR_ASIGNACION", re.compile(r"=")),
    ("DELIMITADOR", re.compile(r"[(){},;]")),
    ("CADENA", re.compile(r'"[^"\n]*"')),
    ("CARACTER", re.compile(r"'.'")),
]

def analizar_codigo_fuente(codigo):
    tokens = []
    errores = []

    i = 0
    line = 1
    en_comentario_multilinea = False

    while i < len(codigo):
        fragmento = codigo[i:]

        if en_comentario_multilinea:
            fin_comentario = re.search(r"\*/", fragmento)
            if fin_comentario:
                i += fin_comentario.end()
                en_comentario_multilinea = False
                continue
            else:
                i = len(codigo)
                break

        # Saltar comentarios simples
        match = re.match(r"//.*", fragmento)
        if match:
            i += match.end()
            continue

        # Detectar comentarios multilínea
        match = re.match(r"/\*", fragmento)
        if match:
            en_comentario_multilinea = True
            i += match.end()
            continue

        # Saltar espacios y tabs
        match = re.match(r"[ \t]+", fragmento)
        if match:
            i += match.end()
            continue

        # Nueva línea
        if fragmento.startswith("\n"):
            line += 1
            i += 1
            continue

        # Buscar tokens válidos
        matched = False
        for token_type, regex in TOKEN_REGEX:
            match = regex.match(fragmento)
            if match:
                lexema = match.group()

                if token_type == "IDENTIFICADOR":
                    if lexema in RESERVED_WORDS:
                        token_type = "PALABRA_RESERVADA"

                tokens.append({"line": line, "lexema": lexema, "tipo": token_type})
                i += len(lexema)
                matched = True
                break

        if not matched:
            errores.append({"line": line, "lexema": fragmento[0], "descripcion": "Símbolo no reconocido"})
            i += 1  # Ignora el carácter no reconocido

    return tokens, errores

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
    tabla_tokens = generar_tabla_tokens(tokens)
    tabla_errores = generar_tabla_errores(errores)
    guardar_tokens_en_archivo(tokens, ruta_archivo)

    return tabla_tokens, tabla_errores
