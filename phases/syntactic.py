import os
from util.treeNode import ASTNode

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_index = 0
        self.current_token = self.tokens[0] if tokens else None
        self.line = self.current_token[2] if tokens else 0
        self.column = self.current_token[3] if tokens else 0
        print(f"Parser initialized with {len(tokens)} tokens")

    def advance(self):
        self.current_index += 1
        if self.current_index < len(self.tokens):
            self.current_token = self.tokens[self.current_index]
            self.line = self.current_token[2]
            self.column = self.current_token[3]
        else:
            self.current_token = None
            print(f"Reached end of tokens at index {self.current_index}")
        print(f"Advanced to token: {self.current_token}")
        return self.current_token

    def peek(self):
        peek_index = self.current_index + 1
        if peek_index < len(self.tokens):
            print(f"Peeking at next token: {self.tokens[peek_index]}")
            return self.tokens[peek_index]
        print("Peeking at end of tokens")
        return None

    def consume(self, token_type=None, token_value=None):
        print(f"Consuming: Expected {token_value or token_type}, Current token: {self.current_token}")
        if not self.current_token:
            print(f"Error: No current token at {self.line}:{self.column}")
            return ASTNode(f"Error at {self.line}:{self.column}: Unexpected end of input")
        
        current_type = self.current_token[1]
        current_value = self.current_token[0]
        
        if (token_type and current_type != token_type) or (token_value and current_value != token_value):
            print(f"Error: Mismatch at {self.line}:{self.column} - Expected {token_value or token_type}, got {current_value}")
            error_node = ASTNode(f"Error at {self.line}:{self.column}: Expected {token_value or token_type}, got {current_value}")
            self.advance()  # Force advance on mismatch to prevent cycling
            return error_node
        
        consumed_token = ASTNode(f"{current_type}: {current_value} at {self.line}:{self.column}")
        print(f"Consumed: {consumed_token.name}")
        self.advance()
        return consumed_token

    def parse(self):
        print("Starting parse of program")
        program_node = ASTNode("Programa")
        
        if not self.consume("IDENTIFICADOR", "main"):
            print(f"Error: 'main' not found at start, skipping to next valid structure")
            program_node.add_child(ASTNode(f"Error at {self.line}:{self.column}: Expected 'main'"))
            while self.current_token and self.current_token[0] != "{":  # Skip until block start
                self.advance()
        
        if self.current_token and self.current_token[0] == "(":
            self.consume("DELIMITADOR", "(")
            self.consume("DELIMITADOR", ")")
        
        if not self.consume("DELIMITADOR", "{"):
            print(f"Error: '{{' not found after 'main()', skipping")
            program_node.add_child(ASTNode(f"Error at {self.line}:{self.column}: Expected '{{'"))
            return program_node
        
        print("Parsing lista_declaracion")
        lista_declaracion = self.parse_lista_declaracion()
        program_node.add_child(lista_declaracion)
        
        if self.current_token and self.current_token[0] != "}":
            print(f"Error: '}}' not found, current token: {self.current_token}")
            program_node.add_child(ASTNode(f"Error at {self.line}:{self.column}: Expected '}}'"))
        else:
            self.consume("DELIMITADOR", "}")
        
        print("Parse completed")
        return program_node

    def parse_lista_declaracion(self):
        print("Entering parse_lista_declaracion")
        lista_node = ASTNode("ListaDeclaracion")
        iteration = 0
        max_iterations = 100  # Safeguard against infinite loops
        while self.current_token and self.current_token[0] != "}" and iteration < max_iterations:
            print(f"Processing next declaration, current token: {self.current_token}")
            decl = self.parse_declaracion()
            if decl:
                lista_node.add_child(decl)
            else:
                print(f"Skipping invalid token: {self.current_token}")
                self.advance()
            iteration += 1
        if iteration >= max_iterations:
            print("Warning: Max iterations reached, possible infinite loop")
        print("Exiting parse_lista_declaracion")
        return lista_node

    def parse_declaracion(self):
        print("Entering parse_declaracion")
        decl_node = ASTNode("Declaracion")
        if self.current_token and self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] in ["int", "float", "bool"]:
            print("Parsing declaracion_variable")
            decl_var = self.parse_declaracion_variable()
            decl_node.add_child(decl_var)
        else:
            print("Parsing lista_sentencias")
            lista_sent = self.parse_lista_sentencias()
            decl_node.add_child(lista_sent)
        print("Exiting parse_declaracion")
        return decl_node

    def parse_declaracion_variable(self):
        print("Entering parse_declaracion_variable")
        decl_node = ASTNode("DeclaracionVariable")
        
        type_node = self.consume("PALABRA_RESERVADA")
        if not type_node or "Error" in type_node.name:
            print(f"Error in type consumption: {type_node.name if type_node else 'None'}")
            return type_node if type_node else ASTNode(f"Error at {self.line}:{self.column}: Expected type")
        decl_node.add_child(type_node)
        
        id_node = self.consume("IDENTIFICADOR")
        if not id_node or "Error" in id_node.name:
            print(f"Error in identifier consumption: {id_node.name if id_node else 'None'}")
            decl_node.add_child(ASTNode(f"Error at {self.line}:{self.column}: Expected identifier"))
            return decl_node
        decl_node.add_child(id_node)
        
        if self.current_token and self.current_token[0] == "=":
            print("Parsing assignment in declaration")
            assign_op = self.consume("OPERADOR_ASIGNACION", "=")
            decl_node.add_child(assign_op)
            expr_node = self.parse_expression()
            if expr_node:
                decl_node.add_child(expr_node)
        
        semicolon = self.consume("DELIMITADOR", ";")
        if "Error" in semicolon.name:
            print(f"Error in semicolon consumption: {semicolon.name}")
            decl_node.add_child(semicolon)
        
        print("Exiting parse_declaracion_variable")
        return decl_node

    def parse_lista_sentencias(self):
        print("Entering parse_lista_sentencias")
        lista_node = ASTNode("ListaSentencias")
        iteration = 0
        max_iterations = 100  # Safeguard against infinite loops
        while self.current_token and self.current_token[0] not in ["}", "else", "end"] and iteration < max_iterations:
            print(f"Processing next statement, current token: {self.current_token}")
            stmt = self.parse_statement()
            if stmt:
                lista_node.add_child(stmt)
            else:
                print(f"Skipping invalid token in statements: {self.current_token}")
                self.advance()
            iteration += 1
        if iteration >= max_iterations:
            print("Warning: Max iterations reached, possible infinite loop")
        print("Exiting parse_lista_sentencias")
        return lista_node

    def parse_statement(self):
        print(f"Entering parse_statement, current token: {self.current_token}")
        if not self.current_token:
            print("No current token, exiting parse_statement")
            return None
        
        token_type = self.current_token[1]
        token_value = self.current_token[0]
        
        if token_type == "PALABRA_RESERVADA" and token_value in ["int", "float", "bool"]:
            print("Parsing declaration variable")
            return self.parse_declaracion_variable()
        elif token_type == "PALABRA_RESERVADA" and token_value == "if":
            print("Parsing if statement")
            return self.parse_if_statement()
        elif token_type == "PALABRA_RESERVADA" and token_value == "while":
            print("Parsing while loop")
            return self.parse_while_loop()
        elif token_type == "PALABRA_RESERVADA" and token_value == "return":
            print("Parsing return statement")
            return self.parse_return_statement()
        elif token_type == "IDENTIFICADOR" and self.peek() and self.peek()[0] == "=":
            print("Parsing assignment")
            return self.parse_assignment()
        elif token_value == "{":
            print("Parsing block")
            return self.parse_block()
        else:
            print("Parsing expression as statement")
            expr = self.parse_expression()
            if expr and self.current_token and self.current_token[0] == ";":
                self.consume("DELIMITADOR", ";")
            return expr

    def parse_block(self):
        print("Entering parse_block")
        block_node = ASTNode("Block")
        
        if not self.consume("DELIMITADOR", "{"):
            print(f"Error: Expected '{{' at {self.line}:{self.column}")
            block_node.add_child(ASTNode(f"Error at {self.line}:{self.column}: Expected '{{'"))
            return block_node
        
        print("Parsing block contents")
        block_node.add_child(self.parse_lista_sentencias())
        
        if not self.consume("DELIMITADOR", "}"):
            print(f"Error: Expected '}}' at {self.line}:{self.column}")
            block_node.add_child(ASTNode(f"Error at {self.line}:{self.column}: Expected '}}'"))
        
        print("Exiting parse_block")
        return block_node

    def parse_assignment(self):
        print("Entering parse_assignment")
        assignment_node = ASTNode("Asignacion")
        
        id_node = self.consume("IDENTIFICADOR")
        if not id_node or "Error" in id_node.name:
            print(f"Error in identifier: {id_node.name if id_node else 'None'}")
            return id_node if id_node else ASTNode(f"Error at {self.line}:{self.column}: Expected identifier")
        assignment_node.add_child(id_node)
        
        assign_op = self.consume("OPERADOR_ASIGNACION", "=")
        if "Error" in assign_op.name:
            print(f"Error in assignment operator: {assign_op.name}")
            assignment_node.add_child(assign_op)
            return assignment_node
        assignment_node.add_child(assign_op)
        
        expr_node = self.parse_expression()
        if expr_node:
            assignment_node.add_child(expr_node)
        
        semicolon = self.consume("DELIMITADOR", ";")
        if "Error" in semicolon.name:
            print(f"Error in semicolon: {semicolon.name}")
            assignment_node.add_child(semicolon)
        
        print("Exiting parse_assignment")
        return assignment_node

    def parse_return_statement(self):
        print("Entering parse_return_statement")
        return_node = ASTNode("Return")
        
        self.consume("PALABRA_RESERVADA", "return")
        
        expr_node = self.parse_expression()
        if expr_node:
            return_node.add_child(expr_node)
        
        semicolon = self.consume("DELIMITADOR", ";")
        if "Error" in semicolon.name:
            print(f"Error in semicolon: {semicolon.name}")
            return_node.add_child(semicolon)
        
        print("Exiting parse_return_statement")
        return return_node

    def parse_expression(self):
        print("Entering parse_expression")
        return self.parse_expresion()

    def parse_expresion(self):
        print("Entering parse_expresion")
        expr_node = ASTNode("Expresion")
        left = self.parse_expresion_simple()
        if left:
            expr_node.add_child(left)
        if self.current_token and self.current_token[0] in ["<", "<=", ">", ">=", "==", "!="]:
            rel_op = self.consume("OPERADOR_RELACIONAL")
            if not rel_op or "Error" in rel_op.name:
                print(f"Error in relational operator: {rel_op.name}")
                expr_node.add_child(rel_op)
                return expr_node
            expr_node.add_child(rel_op)
            right = self.parse_expresion_simple()
            if right:
                expr_node.add_child(right)
        print("Exiting parse_expresion")
        return expr_node

    def parse_expresion_simple(self):
        print("Entering parse_expresion_simple")
        expr_node = ASTNode("ExpresionSimple")
        left = self.parse_termino()
        if left:
            expr_node.add_child(left)
        while self.current_token and self.current_token[0] in ["+", "-"]:
            op_node = ASTNode(f"Operator: {self.current_token[0]} at {self.line}:{self.column}")
            self.advance()
            right = self.parse_termino()
            if right:
                op_node.add_child(left)
                op_node.add_child(right)
                expr_node.add_child(op_node)
                left = op_node
        print("Exiting parse_expresion_simple")
        return expr_node

    def parse_termino(self):
        print("Entering parse_termino")
        term_node = ASTNode("Termino")
        left = self.parse_factor()
        if left:
            term_node.add_child(left)
        while self.current_token and self.current_token[0] in ["*", "/", "%"]:
            op_node = ASTNode(f"Operator: {self.current_token[0]} at {self.line}:{self.column}")
            self.advance()
            right = self.parse_factor()
            if right:
                op_node.add_child(left)
                op_node.add_child(right)
                term_node.add_child(op_node)
                left = op_node
        print("Exiting parse_termino")
        return term_node

    def parse_factor(self):
        print("Entering parse_factor")
        factor_node = ASTNode("Factor")
        if self.current_token and self.current_token[0] == "(":
            print("Parsing parenthesized expression")
            self.consume("DELIMITADOR", "(")
            expr = self.parse_expresion()
            if expr:
                factor_node.add_child(expr)
            closing = self.consume("DELIMITADOR", ")")
            if "Error" in closing.name:
                print(f"Error in closing parenthesis: {closing.name}")
                factor_node.add_child(closing)
            return factor_node
        elif self.current_token and self.current_token[1] in ["NUMERO_ENTERO", "NUMERO_FLOTANTE"]:
            print(f"Consuming number: {self.current_token}")
            return self.consume(self.current_token[1])
        elif self.current_token and self.current_token[1] == "IDENTIFICADOR":
            print(f"Consuming identifier: {self.current_token}")
            return self.consume("IDENTIFICADOR")
        else:
            print(f"Error: Unexpected token at {self.line}:{self.column} - {self.current_token}")
            return ASTNode(f"Error at {self.line}:{self.column}: Expected factor")

    def parse_if_statement(self):
        print("Entering parse_if_statement")
        if_node = ASTNode("If")
        
        if_node.add_child(self.consume("PALABRA_RESERVADA", "if"))
        
        open_paren = self.consume("DELIMITADOR", "(")
        if "Error" in open_paren.name:
            print(f"Error in opening parenthesis: {open_paren.name}")
            if_node.add_child(open_paren)
        
        cond_node = self.parse_expression()
        if cond_node:
            if_node.add_child(cond_node)
        
        close_paren = self.consume("DELIMITADOR", ")")
        if "Error" in close_paren.name:
            print(f"Error in closing parenthesis: {close_paren.name}")
            if_node.add_child(close_paren)
        
        body_node = self.parse_statement()
        if body_node:
            if_node.add_child(body_node)
        
        if self.current_token and self.current_token[0] == "else":
            print("Parsing else clause")
            else_node = self.consume("PALABRA_RESERVADA", "else")
            if_node.add_child(else_node)
            else_body = self.parse_statement()
            if else_body:
                if_node.add_child(else_body)
        
        print("Exiting parse_if_statement")
        return if_node

    def parse_while_loop(self):
        print("Entering parse_while_loop")
        while_node = ASTNode("While")
        
        while_node.add_child(self.consume("PALABRA_RESERVADA", "while"))
        
        open_paren = self.consume("DELIMITADOR", "(")
        if "Error" in open_paren.name:
            print(f"Error in opening parenthesis: {open_paren.name}")
            while_node.add_child(open_paren)
        
        cond_node = self.parse_expression()
        if cond_node:
            while_node.add_child(cond_node)
        
        close_paren = self.consume("DELIMITADOR", ")")
        if "Error" in close_paren.name:
            print(f"Error in closing parenthesis: {close_paren.name}")
            while_node.add_child(close_paren)
        
        body_node = self.parse_statement()
        if body_node:
            while_node.add_child(body_node)
        
        print("Exiting parse_while_loop")
        return while_node

def read_tokens_from_file(path="tokens.txt"):
    tokens = []
    try:
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) >= 4:
                    lexema = parts[0]
                    tipo = parts[1]
                    linea = int(parts[2])
                    columna = int(parts[3])
                    tokens.append((lexema, tipo, linea, columna))
        print(f"Read {len(tokens)} tokens from {path}")
    except Exception as e:
        print(f"Error reading tokens from {path}: {e}")
    return tokens

def analyze():
    try:
        print("Starting analysis")
        tokens = read_tokens_from_file()
        if not tokens:
            print("No tokens found")
            return ASTNode("Error: No tokens found")
        parser = Parser(tokens)
        ast = parser.parse()
        print("Analysis completed")
        return ast
    except Exception as e:
        print(f"Analysis failed with exception: {str(e)}")
        return ASTNode(f"Error en análisis sintáctico: {str(e)}")

def get_ast():
    return analyze()