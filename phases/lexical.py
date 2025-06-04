# lexical.py
RESERVED_WORDS = {
    "if", "else", "end", "do", "while", "switch", "case",
    "int", "float", "main", "cin", "cout", "then", "until"
}

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
                # Saltar espacios
            elif c.isdigit():
                estado = "NUM_ENTERO"
                lexema += c
            elif c.isalpha() or c == "_":
                estado = "IDENT"
                lexema += c
            elif c == "/":
                estado = "POSIBLE_COMENTARIO"
                lexema += c
            elif c in "+-*=<>!%":
                estado = "OPERADOR"
                lexema += c
            elif c in "&|":
                estado = "OPERADOR_LOGICO_POTENCIAL"
                lexema += c
            elif c in "{}[]();,":
                lexema += c
                agregar_token("DELIMITADOR")
            else:
                lexema += c
                agregar_error("Carácter no reconocido")
        elif estado == "NUM_ENTERO":
            if c.isdigit():
                lexema += c
            elif c == ".":
                lexema += c
                estado = "PUNTO_DECIMAL"
            else:
                agregar_token("NUMERO_ENTERO")
                estado = "INICIO"
                continue
        elif estado == "PUNTO_DECIMAL":
            if c.isdigit():
                lexema += c
                estado = "NUM_FLOTANTE"
            else:
                agregar_error("Punto decimal mal utilizado")
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
        elif estado == "POSIBLE_COMENTARIO":
            if c == "/":
                estado = "COMENTARIO_UNILINEA"
                lexema += c
            elif c == "*":
                estado = "COMENTARIO_MULTILINEA"
                lexema += c
            else:
                agregar_token("OPERADOR_ARITMETICO")
                estado = "INICIO"
                continue
        elif estado == "COMENTARIO_UNILINEA":
            if c == "\n":
                fila += 1
                columna = 0
                estado = "INICIO"
        elif estado == "COMENTARIO_MULTILINEA":
            if c == "*" and i + 1 < longitud and codigo[i + 1] == "/":
                lexema += "/"
                i += 1
                estado = "INICIO"
        elif estado == "OPERADOR_LOGICO_POTENCIAL":
            # Solo aceptamos && y || completos
            if (lexema == "&" and c == "&") or (lexema == "|" and c == "|"):
                lexema += c
                agregar_token("OPERADOR_LOGICO")
                estado = "INICIO"
            else:
                agregar_error("Operador lógico incompleto (se esperaba '&&' o '||')")
                estado = "INICIO"
                continue  # Re-procesar el carácter actual
        
        elif estado == "OPERADOR":
            # Manejo de operadores aritméticos, relacionales y asignación
            if c == "=" and lexema in "+-*/%=<>!":
                lexema += c
                if lexema in ("==", "!=", "<=", ">="):
                    agregar_token("OPERADOR_RELACIONAL")
                else:
                    agregar_token("OPERADOR_ASIGNACION")
                estado = "INICIO"
            elif lexema == c and c in "+-":
                lexema += c
                agregar_token("OPERADOR_ARITMETICO")  # ++ o --
                estado = "INICIO"
            else:
                tipo = {
                    "+": "OPERADOR_ARITMETICO",
                    "-": "OPERADOR_ARITMETICO",
                    "*": "OPERADOR_ARITMETICO",
                    "/": "OPERADOR_ARITMETICO",
                    "%": "OPERADOR_ARITMETICO",
                    "=": "OPERADOR_ASIGNACION",
                    "<": "OPERADOR_RELACIONAL",
                    ">": "OPERADOR_RELACIONAL",
                    "!": "OPERADOR_LOGICO"
                }.get(lexema, "OPERADOR")
                agregar_token(tipo)
                estado = "INICIO"
                continue

        i += 1
        columna += 1

    # Finalizar token si queda uno abierto
    if lexema:
        if estado == "NUM_ENTERO":
            agregar_token("NUMERO_ENTERO")
        elif estado == "NUM_FLOTANTE":
            agregar_token("NUMERO_FLOTANTE")
        elif estado == "IDENT":
            tipo = "PALABRA_RESERVADA" if lexema in RESERVED_WORDS else "IDENTIFICADOR"
            agregar_token(tipo)
        elif estado == "COMENTARIO_UNILINEA":
            agregar_token("COMENTARIO_UNILINEA")
        elif estado == "COMENTARIO_MULTILINEA":
            agregar_error("Comentario multilínea sin cerrar")
        elif estado == "PUNTO_DECIMAL":
            agregar_error("Punto decimal mal utilizado")
        elif estado == "OPERADOR":
            agregar_token("OPERADOR")
        elif estado == "OPERADOR_LOGICO_POTENCIAL":
            agregar_error("Operador lógico incompleto (se esperaba '&&' o '||')")

    return tokens, errores

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

    # Guardar tokens en archivo con línea y columna
    with open("tokens.txt", "w", encoding="utf-8") as f:
        for token in tokens:
            lexema = token["lexema"]
            tipo = token["tipo"]
            linea = token["line"]
            columna = token["column"]
            f.write(f"{lexema}\t{tipo}\t{linea}\t{columna}\n")

    return generar_tabla_tokens(tokens), generar_tabla_errores(errores)

