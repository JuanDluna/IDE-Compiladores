# lexical.py
def analizar_codigo_fuente(codigo):
    tokens = []
    errores = []
    estado = "INICIO"
    lexema = ""
    fila = 1
    columna = 1
    i = 0
    longitud = len(codigo)

    def agregar_token(tipo):
        tokens.append({"line": fila, "column": columna - len(lexema), "lexema": lexema, "tipo": tipo})

    def agregar_error(descripcion):
        errores.append({"line": fila, "column": columna - len(lexema), "value": lexema, "descripcion": descripcion})

    while i < longitud:
        c = codigo[i]

        if estado == "INICIO":
            lexema = ""
            if c.isspace():
                if c == "\n":
                    fila += 1
                    columna = 0
                estado = "INICIO"
            elif c.isdigit():
                estado = "NUM_ENTERO"
                lexema += c
            elif c.isalpha() or c == "_":
                estado = "IDENT"
                lexema += c
            elif c == "/":
                estado = "POSIBLE_COMENT"
                lexema += c
            elif c in "+-*/%=<>!&|":
                estado = "OP"
                lexema += c
            elif c in "{}[]();,":
                lexema += c
                agregar_token("DELIMITADOR")
                estado = "INICIO"
            else:
                lexema += c
                agregar_error("Carácter no reconocido")
                estado = "INICIO"
        elif estado == "NUM_ENTERO":
            if c.isdigit():
                lexema += c
            elif c == ".":
                lexema += c
                estado = "PUNTO_DECIMAL"
            else:
                agregar_token("NUMERO_ENTERO")
                estado = "INICIO"
                continue  # Reanalizar este carácter
        elif estado == "PUNTO_DECIMAL":
            if c.isdigit():
                lexema += c
                estado = "NUM_FLOTANTE"
            else:
                agregar_error("Punto decimal mal usado")
                estado = "INICIO"
                continue
        elif estado == "NUM_FLOTANTE":
            if c.isdigit():
                lexema += c
            else:
                agregar_token("NUMERO_FLOTANTE")
                estado = "INICIO"
                continue
        elif estado == "IDENT":
            if c.isalnum() or c == "_":
                lexema += c
            else:
                tipo = "PALABRA_RESERVADA" if lexema in RESERVED_WORDS else "IDENTIFICADOR"
                agregar_token(tipo)
                estado = "INICIO"
                continue
        elif estado == "POSIBLE_COMENT":
            if c == "/":
                estado = "COMENT_UNILINEA"
                lexema += c
            elif c == "*":
                estado = "COMENT_MULTILINEA"
                lexema += c
            else:
                agregar_token("OPERADOR_ARITMETICO")
                estado = "INICIO"
                continue
        elif estado == "COMENT_UNILINEA":
            lexema += c
            if c == "\n":
                agregar_token("COMENTARIO_UNILINEA")
                fila += 1
                columna = 0
                estado = "INICIO"
        elif estado == "COMENT_MULTILINEA":
            lexema += c
            if c == "*" and i + 1 < longitud and codigo[i + 1] == "/":
                lexema += "/"
                i += 1
                agregar_token("COMENTARIO_MULTILINEA")
                estado = "INICIO"
        elif estado == "OP":
            if (lexema + c) in ("<=", ">=", "==", "!=", "&&", "||", "**"):
                lexema += c
                agregar_token("OPERADOR")
                estado = "INICIO"
            elif c == "=":
                lexema += c
                agregar_token("OPERADOR")
                estado = "INICIO"
            else:
                agregar_token("OPERADOR")
                estado = "INICIO"
                continue

        i += 1
        columna += 1

    # Estado final pendiente
    if estado == "NUM_ENTERO":
        agregar_token("NUMERO_ENTERO")
    elif estado == "NUM_FLOTANTE":
        agregar_token("NUMERO_FLOTANTE")
    elif estado == "IDENT":
        tipo = "PALABRA_RESERVADA" if lexema in RESERVED_WORDS else "IDENTIFICADOR"
        agregar_token(tipo)

    return tokens, errores


RESERVED_WORDS = {
    "if", "else", "end", "do", "while", "switch", "case",
    "int", "float", "main", "cin", "cout", "then", "until"
}


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
            f.write(f"{token['lexema']}\t{token['tipo']}\n")

    return generar_tabla_tokens(tokens), generar_tabla_errores(errores)
