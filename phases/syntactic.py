import os
from util.treeNode import ASTNode

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_index = 0
        self.current_token = self.tokens[0] if tokens else None

    def advance(self):
        self.current_index += 1
        if self.current_index < len(self.tokens):
            self.current_token = self.tokens[self.current_index]
        else:
            self.current_token = None
        return self.current_token

    def peek(self):
        peek_index = self.current_index + 1
        if peek_index < len(self.tokens):
            return self.tokens[peek_index]
        return None

    def consume(self, token_type=None, token_value=None):
        if not self.current_token:
            return None
            
        current_type = self.current_token[1]
        current_value = self.current_token[0]
        
        if (token_type and current_type != token_type) or (token_value and current_value != token_value):
            return None
            
        consumed_token = self.current_token
        self.advance()
        return ASTNode(f"{current_type}: {current_value}")

    def parse(self):
        program_node = ASTNode("Programa")
        
        while self.current_token:
            statement_node = self.parse_statement()
            if statement_node:
                program_node.add_child(statement_node)
            else:
                # Manejo de error
                error_node = ASTNode(f"Error de sintaxis en {self.current_token[0]}")
                program_node.add_child(error_node)
                self.advance()  # Recuperación de error: saltar token problemático
                
        return program_node

    def parse_statement(self):
        if not self.current_token:
            return None
            
        token_type = self.current_token[1]
        token_value = self.current_token[0]
        
        # Declaración de variable
        if token_type == "PALABRA_RESERVADA" and token_value in ["int", "float", "string", "bool"]:
            return self.parse_declaration()
            
        # Estructuras de control
        elif token_type == "PALABRA_RESERVADA" and token_value == "if":
            return self.parse_if_statement()
        elif token_type == "PALABRA_RESERVADA" and token_value == "while":
            return self.parse_while_loop()
            
        # Asignación
        elif token_type == "IDENTIFICADOR" and self.peek() and self.peek()[1] == "OPERADOR_ASIGNACION":
            return self.parse_assignment()
            
        # Expresión
        else:
            return self.parse_expression()

    def parse_declaration(self):
        declaration_node = ASTNode("Declaracion")
        
        # Tipo de variable
        type_node = self.consume("PALABRA_RESERVADA")
        declaration_node.add_child(type_node)
        
        # Identificador
        id_node = self.consume("IDENTIFICADOR")
        if not id_node:
            declaration_node.add_child(ASTNode("Error: Se esperaba identificador"))
            return declaration_node
        declaration_node.add_child(id_node)
        
        # Posible asignación
        if self.current_token and self.current_token[1] == "OPERADOR_ASIGNACION":
            assign_op = self.consume("OPERADOR_ASIGNACION")
            declaration_node.add_child(assign_op)
            expr_node = self.parse_expression()
            if expr_node:
                declaration_node.add_child(expr_node)
        
        # Punto y coma
        if not self.consume("DELIMITADOR", ";"):
            declaration_node.add_child(ASTNode("Error: Se esperaba ';'"))
        
        return declaration_node

    def parse_assignment(self):
        assignment_node = ASTNode("Asignacion")
        
        # Identificador
        id_node = self.consume("IDENTIFICADOR")
        assignment_node.add_child(id_node)
        
        # Operador de asignación
        assign_op = self.consume("OPERADOR_ASIGNACION")
        if not assign_op:
            assignment_node.add_child(ASTNode("Error: Se esperaba '='"))
            return assignment_node
        assignment_node.add_child(assign_op)
        
        # Expresión
        expr_node = self.parse_expression()
        if expr_node:
            assignment_node.add_child(expr_node)
        
        # Punto y coma
        if not self.consume("DELIMITADOR", ";"):
            assignment_node.add_child(ASTNode("Error: Se esperaba ';'"))
        
        return assignment_node

    def parse_expression(self):
        return self.parse_logical_expression()

    def parse_logical_expression(self):
        left_node = self.parse_relational_expression()
        
        while self.current_token and self.current_token[0] in ["&&", "||"]:
            op_node = ASTNode(f"Operador: {self.current_token[0]}")
            self.advance()
            right_node = self.parse_relational_expression()
            
            op_node.add_child(left_node)
            op_node.add_child(right_node)
            left_node = op_node
            
        return left_node

    def parse_relational_expression(self):
        left_node = self.parse_additive_expression()
        
        while self.current_token and self.current_token[0] in ["<", ">", "<=", ">=", "==", "!="]:
            op_node = ASTNode(f"Operador: {self.current_token[0]}")
            self.advance()
            right_node = self.parse_additive_expression()
            
            op_node.add_child(left_node)
            op_node.add_child(right_node)
            left_node = op_node
            
        return left_node

    def parse_additive_expression(self):
        left_node = self.parse_multiplicative_expression()
        
        while self.current_token and self.current_token[0] in ["+", "-"]:
            op_node = ASTNode(f"Operador: {self.current_token[0]}")
            self.advance()
            right_node = self.parse_multiplicative_expression()
            
            op_node.add_child(left_node)
            op_node.add_child(right_node)
            left_node = op_node
            
        return left_node

    def parse_multiplicative_expression(self):
        left_node = self.parse_primary_expression()
        
        while self.current_token and self.current_token[0] in ["*", "/", "%"]:
            op_node = ASTNode(f"Operador: {self.current_token[0]}")
            self.advance()
            right_node = self.parse_primary_expression()
            
            op_node.add_child(left_node)
            op_node.add_child(right_node)
            left_node = op_node
            
        return left_node

    def parse_primary_expression(self):
        if not self.current_token:
            return ASTNode("Error: Se esperaba expresión")
            
        token_value, token_type, line, col = self.current_token
        
        # Literales
        if token_type in ["NUMERO_ENTERO", "NUMERO_FLOTANTE"]:
            node = ASTNode(f"Literal {token_type}: {token_value}")
            self.advance()
            return node
            
        # Identificadores
        elif token_type == "IDENTIFICADOR":
            node = ASTNode(f"Variable: {token_value}")
            self.advance()
            return node
            
        # Expresión entre paréntesis
        elif token_value == "(":
            self.advance()  # Consume '('
            expr_node = self.parse_expression()
            if not self.consume("DELIMITADOR", ")"):
                expr_node.add_child(ASTNode("Error: Se esperaba ')'"))
            return expr_node
            
        # Error
        else:
            error_node = ASTNode(f"Error: Token inesperado '{token_value}'")
            self.advance()
            return error_node

    def parse_if_statement(self):
        if_node = ASTNode("If")
        
        # Palabra clave 'if'
        if not self.consume("PALABRA_RESERVADA", "if"):
            if_node.add_child(ASTNode("Error: Se esperaba 'if'"))
            return if_node
        
        # Condición entre paréntesis
        if not self.consume("DELIMITADOR", "("):
            if_node.add_child(ASTNode("Error: Se esperaba '('"))
        
        cond_node = self.parse_expression()
        if cond_node:
            if_node.add_child(cond_node)
        
        if not self.consume("DELIMITADOR", ")"):
            if_node.add_child(ASTNode("Error: Se esperaba ')'"))
        
        # Cuerpo del if
        body_node = self.parse_statement()
        if body_node:
            if_node.add_child(body_node)
        
        # Posible else
        if self.current_token and self.current_token[0] == "else":
            else_node = self.consume("PALABRA_RESERVADA", "else")
            if_node.add_child(else_node)
            else_body = self.parse_statement()
            if else_body:
                if_node.add_child(else_body)
        
        return if_node

    def parse_while_loop(self):
        while_node = ASTNode("While")
        
        # Palabra clave 'while'
        if not self.consume("PALABRA_RESERVADA", "while"):
            while_node.add_child(ASTNode("Error: Se esperaba 'while'"))
            return while_node
        
        # Condición entre paréntesis
        if not self.consume("DELIMITADOR", "("):
            while_node.add_child(ASTNode("Error: Se esperaba '('"))
        
        cond_node = self.parse_expression()
        if cond_node:
            while_node.add_child(cond_node)
        
        if not self.consume("DELIMITADOR", ")"):
            while_node.add_child(ASTNode("Error: Se esperaba ')'"))
        
        # Cuerpo del while
        body_node = self.parse_statement()
        if body_node:
            while_node.add_child(body_node)
        
        return while_node

def read_tokens_from_file(path="tokens.txt"):
    tokens = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split("\t")
            if len(parts) >= 4:
                lexema = parts[0]
                tipo = parts[1]
                linea = int(parts[2])
                columna = int(parts[3])
                tokens.append((lexema, tipo, linea, columna))
    return tokens

def analyze():
    try:
        tokens = read_tokens_from_file()
        parser = Parser(tokens)
        ast = parser.parse()
        return ast
    except Exception as e:
        return ASTNode(f"Error en análisis sintáctico: {str(e)}")

def get_ast():
    return analyze()