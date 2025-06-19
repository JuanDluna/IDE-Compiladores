import os
from util.treeNode import ASTNode
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QPlainTextEdit

class Token:
    def __init__(self, lexema, tipo, linea, columna):
        self.lexema = lexema
        self.tipo = tipo
        self.linea = linea
        self.columna = columna
    
    def __str__(self):
        return f"{self.lexema}\t{self.tipo}\t{self.linea}\t{self.columna}"

class Parser:
    def __init__(self, tokens):
        self.tokens = [Token(*t) for t in tokens]
        self.current = 0
        self.errors = []
    
    def error(self, message):
        if self.current < len(self.tokens):
            token = self.tokens[self.current]
            if token and hasattr(token, 'linea') and hasattr(token, 'columna'):
                self.errors.append(f"Error en línea {token.linea}, columna {token.columna}: {message}")
            else:
                self.errors.append(f"Error: {message} (token nulo)")
        else:
            self.errors.append(f"Error: {message} (fin de archivo)")
        return None

    def peek(self):
        """Retorna el token actual sin avanzar el cursor."""
        if self.current < len(self.tokens):
            token = self.tokens[self.current]
            if token and hasattr(token, 'lexema') and hasattr(token, 'tipo') and hasattr(token, 'linea') and hasattr(token, 'columna'):
                return token
        return None

    def advance(self):
        token = self.peek()
        self.current += 1
        return token

    def check(self, tipo=None, lexema=None):
        token = self.peek()
        if not token:
            return False
        if tipo and token.tipo != tipo:
            return False
        if lexema and (isinstance(lexema, str) and token.lexema != lexema or 
                      isinstance(lexema, (list, tuple)) and token.lexema not in lexema):
            return False
        return True

    def match(self, tipo=None, lexema=None):
        if self.check(tipo, lexema):
            return self.advance()
        return None

    def require(self, tipo=None, lexema=None, mensaje=None):
        token = self.match(tipo, lexema)
        if not token:
            actual = self.peek()
            if not mensaje:
                esperado = lexema if lexema else tipo
                mensaje = f"Se esperaba {esperado}"
                if actual and hasattr(actual, 'lexema'):
                    mensaje += f", se encontró '{actual.lexema}'"
            return self.error(mensaje)
        return token

    def format_token(self, token):
        """Formatea un token para mostrar su información."""
        if token and hasattr(token, 'lexema') and hasattr(token, 'linea') and hasattr(token, 'columna'):
            return f"{token.lexema} ({token.linea}:{token.columna})"
        return "token inválido"

    def parse_programa(self):
        """programa → main { lista_declaracion }"""
        root = ASTNode("Programa")
        
        # Verificar 'main'
        main_token = self.require("PALABRA_RESERVADA", "main")
        if not main_token:
            return root
        root.add_child(ASTNode(self.format_token(main_token)))
        
        # Verificar '{'
        llave_token = self.require("DELIMITADOR", "{")
        if not llave_token:
            return root
        
        # Parsear el cuerpo del programa
        while self.peek() and not self.check("DELIMITADOR", "}"):
            if decl := self.parse_declaracion():
                root.add_child(decl)
        
        # Verificar '}'
        llave_token = self.require("DELIMITADOR", "}")
        if llave_token:
            root.add_child(ASTNode(self.format_token(llave_token)))
        return root

    def parse_declaracion(self):
        """declaracion → declaracion_variable | sentencia"""
        if self.check("PALABRA_RESERVADA", ("int", "float", "bool")):
            return self.parse_declaracion_variable()
        return self.parse_sentencia()

    def parse_declaracion_variable(self):
        """declaracion_variable → tipo identificador_list ;"""
        tipo_token = self.require("PALABRA_RESERVADA", ("int", "float", "bool"))
        if not tipo_token:
            return None
        
        node = ASTNode("Declaración")
        node.add_child(ASTNode(self.format_token(tipo_token)))
        
        # Lista de identificadores
        while True:
            id_token = self.require("IDENTIFICADOR")
            if not id_token:
                return None
            id_node = ASTNode(self.format_token(id_token))
            
            # Si hay una asignación inicial
            if self.check("OPERADOR_ASIGNACION", "="):
                op_token = self.advance()
                op_node = ASTNode(self.format_token(op_token))
                op_node.add_child(id_node)
                if expr := self.parse_expresion():
                    op_node.add_child(expr)
                    node.add_child(op_node)
                else:
                    return None
            else:
                node.add_child(id_node)
            
            if not self.check("DELIMITADOR", ","):
                break
            self.advance()  # Consumir la coma
        
        if not self.require("DELIMITADOR", ";"):
            return None
        
        return node

    def parse_sentencia(self):
        """sentencia → if_stmt | while_stmt | do_while_stmt | asignacion | entrada | salida"""
        if not self.peek():
            return None
            
        if self.check("PALABRA_RESERVADA", "if"):
            return self.parse_if_stmt()
        elif self.check("PALABRA_RESERVADA", "while"):
            return self.parse_while_stmt()
        elif self.check("PALABRA_RESERVADA", "do"):
            return self.parse_do_while_stmt()
        elif self.check("PALABRA_RESERVADA", "cin"):
            return self.parse_entrada()
        elif self.check("PALABRA_RESERVADA", "cout"):
            return self.parse_salida()
        elif self.check("IDENTIFICADOR"):
            return self.parse_asignacion()
        
        token = self.peek()
        self.error(f"Sentencia no válida: '{token.lexema}'")
        self.advance()
        return None

    def parse_if_stmt(self):
        """if_stmt → if expresion then bloque (else bloque)? end"""
        if_token = self.require("PALABRA_RESERVADA", "if")
        if not if_token:
            return None
        
        node = ASTNode(self.format_token(if_token))
        
        # Condición
        cond_node = ASTNode("Condición")
        if expr := self.parse_expresion():
            cond_node.add_child(expr)
            node.add_child(cond_node)
        else:
            return None
        
        # Then
        if not self.require("PALABRA_RESERVADA", "then"):
            return None
        
        # Bloque then
        then_node = ASTNode("then")
        while self.peek() and not self.check("PALABRA_RESERVADA", ("else", "end")):
            if stmt := self.parse_sentencia():
                then_node.add_child(stmt)
        node.add_child(then_node)
        
        # Else (opcional)
        if self.match("PALABRA_RESERVADA", "else"):
            else_node = ASTNode("else")
            while self.peek() and not self.check("PALABRA_RESERVADA", "end"):
                if stmt := self.parse_sentencia():
                    else_node.add_child(stmt)
            node.add_child(else_node)
        
        if not self.require("PALABRA_RESERVADA", "end"):
            return None
        
        return node

    def parse_while_stmt(self):
        """while_stmt → while expresion bloque end"""
        while_token = self.require("PALABRA_RESERVADA", "while")
        if not while_token:
            return None
        
        node = ASTNode(self.format_token(while_token))
        
        # Condición
        cond_node = ASTNode("Condición")
        if expr := self.parse_expresion():
            cond_node.add_child(expr)
            node.add_child(cond_node)
        else:
            return None
        
        # Bloque
        body_node = ASTNode("Cuerpo")
        while self.peek() and not self.check("PALABRA_RESERVADA", "end"):
            if stmt := self.parse_sentencia():
                body_node.add_child(stmt)
        node.add_child(body_node)
        
        if not self.require("PALABRA_RESERVADA", "end"):
            return None
        
        return node

    def parse_do_while_stmt(self):
        """do_while_stmt → do bloque until expresion"""
        do_token = self.require("PALABRA_RESERVADA", "do")
        if not do_token:
            return None
        
        node = ASTNode(self.format_token(do_token))
        
        # Bloque
        body_node = ASTNode("Cuerpo")
        while self.peek() and not self.check("PALABRA_RESERVADA", "until"):
            if stmt := self.parse_sentencia():
                body_node.add_child(stmt)
        node.add_child(body_node)
        
        # Until y condición
        if not self.require("PALABRA_RESERVADA", "until"):
            return None
        
        cond_node = ASTNode("Condición")
        if expr := self.parse_expresion():
            cond_node.add_child(expr)
            node.add_child(cond_node)
        else:
            return None
        
        return node

    def parse_asignacion(self):
        """asignacion → identificador op_asignacion expresion ;"""
        id_token = self.require("IDENTIFICADOR")
        if not id_token:
            return None
        
        # Operador de asignación o incremento/decremento
        if self.check("OPERADOR_ASIGNACION") or self.check("OPERADOR_ARITMETICO", ("++", "--")):
            op_token = self.advance()
            if not op_token:
                return self.error("Error inesperado en operador de asignación")
            
            # Si es ++ o --, expandir como a = a + 1 o a = a - 1
            if op_token.lexema in ("++", "--"):
                root = ASTNode(f"Expansión de {op_token.lexema}")
                # Nodo de asignación
                assign_node = ASTNode("=")
                id_node_left = ASTNode(self.format_token(id_token))
                assign_node.add_child(id_node_left)
                # Operación suma/resta
                op = "+" if op_token.lexema == "++" else "-"
                op_node = ASTNode(op)
                id_node_right = ASTNode(self.format_token(id_token))
                one_node = ASTNode("1")
                op_node.add_child(id_node_right)
                op_node.add_child(one_node)
                assign_node.add_child(op_node)
                root.add_child(assign_node)
                if not self.require("DELIMITADOR", ";"):
                    return None
                return root
            
            node = ASTNode(self.format_token(op_token))
            id_node = ASTNode(self.format_token(id_token))
            node.add_child(id_node)
            
            # Para otros operadores, necesitamos una expresión
            if op_token.lexema not in ("++", "--"):
                if expr := self.parse_expresion():
                    node.add_child(expr)
                    if not self.require("DELIMITADOR", ";"):
                        return None
                    return node
                else:
                    return None
            else:
                if not self.require("DELIMITADOR", ";"):
                    return None
                return node
        
        return self.error("Se esperaba un operador de asignación")

    def parse_entrada(self):
        """entrada → cin >> identificador ;"""
        cin_token = self.require("PALABRA_RESERVADA", "cin")
        if not cin_token:
            return None
        
        node = ASTNode(self.format_token(cin_token))
        
        op_token = self.require("OPERADOR_ARITMETICO", ">>")
        if not op_token:
            return None
        
        id_token = self.require("IDENTIFICADOR")
        if not id_token:
            return None
        node.add_child(ASTNode(self.format_token(id_token)))
        
        if not self.require("DELIMITADOR", ";"):
            return None
        
        return node

    def parse_salida(self):
        """salida → cout << expresion ;"""
        cout_token = self.require("PALABRA_RESERVADA", "cout")
        if not cout_token:
            return None
        
        node = ASTNode(self.format_token(cout_token))
        
        op_token = self.require("OPERADOR_ARITMETICO", "<<")
        if not op_token:
            return None
        
        if expr := self.parse_expresion():
            node.add_child(expr)
        else:
            return None
        
        if not self.require("DELIMITADOR", ";"):
            return None
        
        return node

    def parse_expresion(self):
        """expresion → expresion_or"""
        node = self.parse_expresion_or()
        if not node:
            return self.error("Expresión inválida")
        return node

    def parse_expresion_or(self):
        """expresion_or → expresion_and (|| expresion_and)*"""
        node = self.parse_expresion_and()
        if not node:
            return None
        
        while self.check("OPERADOR_LOGICO", "||"):
            op_token = self.advance()
            if not op_token:
                return self.error("Error inesperado en operador lógico OR")
            op_node = ASTNode(self.format_token(op_token))
            op_node.add_child(node)
            
            right = self.parse_expresion_and()
            if not right:
                return self.error("Se esperaba una expresión después de '||'")
            op_node.add_child(right)
            node = op_node
        
        return node

    def parse_expresion_and(self):
        """expresion_and → expresion_rel (&& expresion_rel)*"""
        node = self.parse_expresion_rel()
        if not node:
            return None
        
        while self.check("OPERADOR_LOGICO", "&&"):
            op_token = self.advance()
            if not op_token:
                return self.error("Error inesperado en operador lógico AND")
            op_node = ASTNode(self.format_token(op_token))
            op_node.add_child(node)
            
            right = self.parse_expresion_rel()
            if not right:
                return self.error("Se esperaba una expresión después de '&&'")
            op_node.add_child(right)
            node = op_node
        
        return node

    def parse_expresion_rel(self):
        """expresion_rel → expresion_add ((< | > | <= | >= | == | !=) expresion_add)*"""
        node = self.parse_expresion_add()
        if not node:
            return None
        
        while self.check("OPERADOR_RELACIONAL"):
            op_token = self.advance()
            if not op_token:
                return self.error("Error inesperado en operador relacional")
            op_node = ASTNode(self.format_token(op_token))
            op_node.add_child(node)
            
            right = self.parse_expresion_add()
            if not right:
                return self.error("Se esperaba una expresión después del operador relacional")
            op_node.add_child(right)
            node = op_node
        
        return node

    def parse_expresion_add(self):
        """expresion_add → expresion_mul ((+ | -) expresion_mul)*"""
        node = self.parse_expresion_mul()
        if not node:
            return None
        
        while self.check("OPERADOR_ARITMETICO", ("+", "-")):
            op_token = self.advance()
            if not op_token:
                return self.error("Error inesperado en operador aritmético")
            op_node = ASTNode(self.format_token(op_token))
            op_node.add_child(node)
            
            right = self.parse_expresion_mul()
            if not right:
                return self.error("Se esperaba una expresión después del operador aritmético")
            op_node.add_child(right)
            node = op_node
        
        return node

    def parse_expresion_mul(self):
        """expresion_mul → factor ((* | / | %) factor)*"""
        node = self.parse_factor()
        if not node:
            return None
        
        while self.check("OPERADOR_ARITMETICO", ("*", "/", "%")):
            op_token = self.advance()
            if not op_token:
                return self.error("Error inesperado en operador aritmético")
            op_node = ASTNode(self.format_token(op_token))
            op_node.add_child(node)
            
            right = self.parse_factor()
            if not right:
                return self.error("Se esperaba una expresión después del operador aritmético")
            op_node.add_child(right)
            node = op_node
        
        return node

    def parse_factor(self):
        """factor → numero | identificador | (expresion) | !factor"""
        if not self.peek():
            return self.error("Se esperaba un factor")
        
        # Negación lógica
        if self.match("OPERADOR_LOGICO", "!"):
            token = self.tokens[self.current - 1]
            if not token:
                return self.error("Error inesperado en operador de negación")
            node = ASTNode(self.format_token(token))
            factor = self.parse_factor()
            if not factor:
                return self.error("Se esperaba una expresión después de '!'")
            node.add_child(factor)
            return node
        
        # Paréntesis
        if self.match("DELIMITADOR", "("):
            expr = self.parse_expresion()
            if not expr:
                return self.error("Se esperaba una expresión después de '('")
            if not self.require("DELIMITADOR", ")"):
                return None
            return expr
        
        # Número o identificador
        if self.check("NUMERO_ENTERO") or self.check("NUMERO_FLOTANTE") or self.check("IDENTIFICADOR"):
            token = self.advance()
            if not token:
                return self.error("Error inesperado en factor")
            return ASTNode(self.format_token(token))
        
        token = self.peek()
        if token:
            self.error(f"Factor no válido: '{token.lexema}'")
        else:
            self.error("Factor no válido")
        self.advance()
        return None

def read_tokens_from_file(path="tokens.txt"):
    tokens = []
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) >= 4:
                    tokens.append((parts[0], parts[1], int(parts[2]), int(parts[3])))
    except Exception as e:
        print(f"Error leyendo tokens desde {path}: {e}")
    return tokens

def get_ast():
    """Función principal que retorna el AST y los errores encontrados"""
    tokens = read_tokens_from_file()
    parser = Parser(tokens)
    ast = parser.parse_programa()
    return ast, parser.errors

def fill_tree_widget(widget: QTreeWidget, ast_root: ASTNode, error_output_widget: QPlainTextEdit, parser_errors: list):
    widget.clear()
    error_output_widget.clear()
    errores = []

    def add_node_recursively(parent_widget_item, ast_node):
        if ast_node is None:
            return
        if "Error" in ast_node.name:
            errores.append(ast_node.name)
            return
        item = QTreeWidgetItem([ast_node.name])
        parent_widget_item.addChild(item)
        for child in ast_node.children:
            if child is not None:  # Verificar que el hijo no sea None
                add_node_recursively(item, child)

    if ast_root is None:
        error_output_widget.setPlainText("Error: No se pudo generar el árbol sintáctico")
        return

    root_item = QTreeWidgetItem([ast_root.name])
    widget.addTopLevelItem(root_item)
    for child in ast_root.children:
        if child is not None:  # Verificar que el hijo no sea None
            add_node_recursively(root_item, child)
    widget.expandAll()

    # Combinar errores del AST y del parser
    all_errors = errores + (parser_errors if parser_errors else [])
    if all_errors:
        error_output_widget.setPlainText("\n".join(all_errors))
    else:
        error_output_widget.setPlainText("Sin errores sintácticos.")

if __name__ == "__main__":
    ast, errors = get_ast()
    if errors:
        print("\nErrores encontrados:")
        for error in errors:
            print(error)
    else:
        print("\nAnálisis sintáctico completado sin errores.")