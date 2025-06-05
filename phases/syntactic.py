import os
from util.treeNode import ASTNode

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_index = 0
        self.current_token = self.tokens[0] if tokens else None
        self.line = self.current_token[2] if tokens else 0
        self.column = self.current_token[3] if tokens else 0
        self.fatal_error = False  # Flag to track fatal errors
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

    def consume(self, token_type=None, token_value=None, required=False):
        print(f"Consuming: Expected {token_value or token_type}, Current token: {self.current_token}, Required: {required}")
        if self.fatal_error:
            return None
        
        if not self.current_token:
            print(f"Error: No current token at {self.line}:{self.column}")
            error_node = ASTNode(f"Fatal Error at {self.line}:{self.column}: Unexpected end of input")
            self.fatal_error = True
            return error_node
        
        current_type = self.current_token[1]
        current_value = self.current_token[0]
        
        if (token_type and current_type != token_type) or (token_value and current_value != token_value):
            print(f"Error: Mismatch at {self.line}:{self.column} - Expected {token_value or token_type}, got {current_value}")
            error_node = ASTNode(f"Error at {self.line}:{self.column}: Expected {token_value or token_type}, got {current_value}")
            if required:  # Missing terminal is a fatal error
                print(f"Fatal Error: Missing required terminal {token_value or token_type}, stopping analysis")
                error_node.name = f"Fatal Error at {self.line}:{self.column}: Missing required terminal {token_value or token_type}"
                self.fatal_error = True
            else:
                self.advance()  # Advance for non-fatal errors
            return error_node
        
        consumed_token = ASTNode(f"{current_type}: {current_value} at {self.line}:{self.column}")
        print(f"Consumed: {consumed_token.name}")
        self.advance()
        return consumed_token

    def parse(self):
        print("Starting parse of program")
        program_node = ASTNode("Programa")
        
        # Optional return type before main
        if self.current_token and self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] in ["int", "float", "bool", "double", "boolean"]:
            type_node = self.parse_tipo_dato()
            program_node.add_child(type_node)
        
        # Required main and following terminals
        main_node = self.consume("PALABRA_RESERVADA", "main", required=True)
        program_node.add_child(main_node)
        if self.fatal_error:
            return program_node
        
        program_node.add_child(self.consume("DELIMITADOR", "(", required=True))
        if self.fatal_error:
            return program_node
        
        program_node.add_child(self.consume("DELIMITADOR", ")", required=True))
        if self.fatal_error:
            return program_node
        
        program_node.add_child(self.consume("DELIMITADOR", "{", required=True))
        if self.fatal_error:
            return program_node
        
        if self.current_token and not self.fatal_error:
            print("Parsing lista_declaraciones")
            lista_declaraciones = self.parse_lista_declaraciones()
            program_node.add_child(lista_declaraciones)
        
        if not self.fatal_error:
            program_node.add_child(self.consume("DELIMITADOR", "}", required=True))
        
        print("Parse completed")
        return program_node

    def parse_lista_declaraciones(self):
        print("Entering parse_lista_declaraciones")
        lista_node = ASTNode("ListaDeclaraciones")
        iteration = 0
        max_iterations = 100
        while self.current_token and self.current_token[0] != "}" and iteration < max_iterations and not self.fatal_error:
            print(f"Processing next declaration, current token: {self.current_token}")
            decl = self.parse_declaracion()
            if decl:
                lista_node.add_child(decl)
                if "Fatal Error" in decl.name:
                    break
            else:
                print(f"Skipping invalid declaration, advancing to next semicolon or brace")
                while self.current_token and self.current_token[0] not in [";", "}", "else"] and not self.fatal_error:
                    self.advance()
                if self.current_token and self.current_token[0] in [";", "else"] and not self.fatal_error:
                    self.advance()
            iteration += 1
        if iteration >= max_iterations:
            print("Warning: Max iterations reached, possible infinite loop")
        print("Exiting parse_lista_declaraciones")
        return lista_node

    def parse_declaracion(self):
        print("Entering parse_declaracion")
        if self.fatal_error:
            return None
        decl_node = ASTNode("Declaracion")
        if self.current_token and self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] in ["int", "float", "bool", "double", "boolean"]:
            print("Parsing declaracion_variable")
            decl_var = self.parse_declaracion_variable()
            decl_node.add_child(decl_var)
        else:
            print("Parsing sentencia")
            sentencia = self.parse_sentencia()
            decl_node.add_child(sentencia)
        print("Exiting parse_declaracion")
        return decl_node

    def parse_declaracion_variable(self):
        print("Entering parse_declaracion_variable")
        if self.fatal_error:
            return None
        decl_node = ASTNode("DeclaracionVariable")
        
        type_node = self.parse_tipo_dato()
        if not type_node or "Error" in type_node.name:
            print(f"Error in type consumption: {type_node.name if type_node else 'None'}")
            return type_node if type_node else ASTNode(f"Error at {self.line}:{self.column}: Expected type")
        decl_node.add_child(type_node)
        
        id_node = self.consume("IDENTIFICADOR", required=True)
        if not id_node or "Fatal Error" in id_node.name:
            decl_node.add_child(id_node if id_node else ASTNode(f"Fatal Error at {self.line}:{self.column}: Expected identifier"))
            return decl_node
        decl_node.add_child(id_node)
        
        if self.current_token and self.current_token[0] == "=" and not self.fatal_error:
            print("Parsing optional assignment")
            decl_node.add_child(self.consume("OPERADOR_ASIGNACION", "=", required=True))
            if self.fatal_error:
                return decl_node
            expr_node = self.parse_expresion()
            if expr_node:
                decl_node.add_child(expr_node)
        
        semicolon_node = self.consume("DELIMITADOR", ";", required=True)
        decl_node.add_child(semicolon_node)
        print("Exiting parse_declaracion_variable")
        return decl_node

    def parse_tipo_dato(self):
        print("Entering parse_tipo_dato")
        if self.fatal_error:
            return None
        if self.current_token and self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] in ["int", "float", "bool", "double", "boolean"]:
            return self.consume("PALABRA_RESERVADA")
        return ASTNode(f"Error at {self.line}:{self.column}: Expected type (int, float, bool, double, boolean)")

    def parse_sentencia(self):
        print("Entering parse_sentencia")
        if not self.current_token or self.fatal_error:
            return None
        
        token_value = self.current_token[0]
        if token_value == "{":
            return self.parse_bloque()
        elif self.current_token[1] == "IDENTIFICADOR" and self.peek() and self.peek()[0] == "=":
            return self.parse_asignacion()
        elif self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] == "if":
            return self.parse_sentencia_if()
        elif self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] == "while":
            return self.parse_sentencia_while()
        elif self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] == "return":
            return self.parse_sentencia_return()
        elif self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] == "cin":
            return self.parse_entrada()
        elif self.current_token[1] == "PALABRA_RESERVADA" and self.current_token[0] == "cout":
            return self.parse_salida()
        else:
            return ASTNode(f"Error at {self.line}:{self.column}: Unexpected token in sentencia")

    def parse_bloque(self):
        print("Entering parse_bloque")
        if self.fatal_error:
            return None
        block_node = ASTNode("Bloque")
        block_node.add_child(self.consume("DELIMITADOR", "{", required=True))
        if self.fatal_error:
            return block_node
        block_node.add_child(self.parse_lista_sentencias())
        block_node.add_child(self.consume("DELIMITADOR", "}", required=True))
        print("Exiting parse_bloque")
        return block_node

    def parse_lista_sentencias(self):
        print("Entering parse_lista_sentencias")
        if self.fatal_error:
            return None
        lista_node = ASTNode("ListaSentencias")
        iteration = 0
        max_iterations = 100
        while self.current_token and self.current_token[0] not in ["}", "else"] and iteration < max_iterations and not self.fatal_error:
            print(f"Processing next sentencia, current token: {self.current_token}")
            stmt = self.parse_sentencia()
            if stmt:
                lista_node.add_child(stmt)
                if "Fatal Error" in stmt.name:
                    break
            else:
                print(f"Skipping invalid sentencia, advancing to next semicolon or brace")
                while self.current_token and self.current_token[0] not in [";", "}", "else"] and not self.fatal_error:
                    self.advance()
                if self.current_token and self.current_token[0] in [";", "else"] and not self.fatal_error:
                    self.advance()
            iteration += 1
        if iteration >= max_iterations:
            print("Warning: Max iterations reached, possible infinite loop")
        print("Exiting parse_lista_sentencias")
        return lista_node

    def parse_asignacion(self):
        print("Entering parse_asignacion")
        if self.fatal_error:
            return None
        assign_node = ASTNode("Asignacion")
        assign_node.add_child(self.consume("IDENTIFICADOR", required=True))
        if self.fatal_error:
            return assign_node
        assign_node.add_child(self.consume("OPERADOR_ASIGNACION", "=", required=True))
        if self.fatal_error:
            return assign_node
        expr_node = self.parse_expresion()
        if expr_node:
            assign_node.add_child(expr_node)
        assign_node.add_child(self.consume("DELIMITADOR", ";", required=True))
        print("Exiting parse_asignacion")
        return assign_node

    def parse_sentencia_if(self):
        print("Entering parse_sentencia_if")
        if self.fatal_error:
            return None
        if_node = ASTNode("SentenciaIf")
        if_node.add_child(self.consume("PALABRA_RESERVADA", "if", required=True))
        if self.fatal_error:
            return if_node
        if_node.add_child(self.consume("DELIMITADOR", "(", required=True))
        if self.fatal_error:
            return if_node
        if_node.add_child(self.parse_expresion())
        if_node.add_child(self.consume("DELIMITADOR", ")", required=True))
        if self.fatal_error:
            return if_node
        if_node.add_child(self.parse_sentencia())
        if self.current_token and self.current_token[0] == "else" and not self.fatal_error:
            if_node.add_child(self.consume("PALABRA_RESERVADA", "else"))
            if_node.add_child(self.parse_sentencia())
        print("Exiting parse_sentencia_if")
        return if_node

    def parse_sentencia_while(self):
        print("Entering parse_sentencia_while")
        if self.fatal_error:
            return None
        while_node = ASTNode("SentenciaWhile")
        while_node.add_child(self.consume("PALABRA_RESERVADA", "while", required=True))
        if self.fatal_error:
            return while_node
        while_node.add_child(self.consume("DELIMITADOR", "(", required=True))
        if self.fatal_error:
            return while_node
        while_node.add_child(self.parse_expresion())
        while_node.add_child(self.consume("DELIMITADOR", ")", required=True))
        if self.fatal_error:
            return while_node
        while_node.add_child(self.parse_sentencia())
        print("Exiting parse_sentencia_while")
        return while_node

    def parse_sentencia_return(self):
        print("Entering parse_sentencia_return")
        if self.fatal_error:
            return None
        return_node = ASTNode("SentenciaReturn")
        return_node.add_child(self.consume("PALABRA_RESERVADA", "return", required=True))
        if self.fatal_error:
            return return_node
        return_node.add_child(self.parse_expresion())
        return_node.add_child(self.consume("DELIMITADOR", ";", required=True))
        print("Exiting parse_sentencia_return")
        return return_node

    def parse_entrada(self):
        print("Entering parse_entrada")
        if self.fatal_error:
            return None
        entrada_node = ASTNode("Entrada")
        entrada_node.add_child(self.consume("PALABRA_RESERVADA", "cin", required=True))
        if self.fatal_error:
            return entrada_node
        entrada_node.add_child(self.consume("OPERADOR_ARITMETICO", ">>", required=True))
        if self.fatal_error:
            return entrada_node
        entrada_node.add_child(self.consume("IDENTIFICADOR", required=True))
        if self.fatal_error:
            return entrada_node
        entrada_node.add_child(self.consume("DELIMITADOR", ";", required=True))
        print("Exiting parse_entrada")
        return entrada_node

    def parse_salida(self):
        print("Entering parse_salida")
        if self.fatal_error:
            return None
        salida_node = ASTNode("Salida")
        salida_node.add_child(self.consume("PALABRA_RESERVADA", "cout", required=True))
        if self.fatal_error:
            return salida_node
        salida_node.add_child(self.consume("OPERADOR_ARITMETICO", "<<", required=True))
        if self.fatal_error:
            return salida_node
        salida_node.add_child(self.parse_expresion())
        salida_node.add_child(self.consume("DELIMITADOR", ";", required=True))
        print("Exiting parse_salida")
        return salida_node

    def parse_expresion(self):
        print("Entering parse_expresion")
        if self.fatal_error:
            return None
        expr_node = ASTNode("Expresion")
        left = self.parse_expresion_simple()
        if left:
            expr_node.add_child(left)
        if self.current_token and self.current_token[1] == "OPERADOR_RELACIONAL" and not self.fatal_error:
            expr_node.add_child(self.consume("OPERADOR_RELACIONAL"))
            right = self.parse_expresion_simple()
            if right:
                expr_node.add_child(right)
        print("Exiting parse_expresion")
        return expr_node

    def parse_expresion_simple(self):
        print("Entering parse_expresion_simple")
        if self.fatal_error:
            return None
        expr_node = ASTNode("ExpresionSimple")
        left = self.parse_termino()
        if left:
            expr_node.add_child(left)
        while self.current_token and self.current_token[0] in ["+", "-"] and not self.fatal_error:
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
        if self.fatal_error:
            return None
        term_node = ASTNode("Termino")
        left = self.parse_factor()
        if left:
            term_node.add_child(left)
        while self.current_token and self.current_token[0] in ["*", "/", "%"] and not self.fatal_error:
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
        if self.fatal_error:
            return None
        factor_node = ASTNode("Factor")
        if self.current_token and self.current_token[1] in ["NUMERO_ENTERO", "NUMERO_FLOTANTE"]:
            factor_node.add_child(self.consume(self.current_token[1]))
        elif self.current_token and self.current_token[1] == "IDENTIFICADOR":
            factor_node.add_child(self.consume("IDENTIFICADOR"))
        elif self.current_token and self.current_token[0] == "(":
            factor_node.add_child(self.consume("DELIMITADOR", "(", required=True))
            if self.fatal_error:
                return factor_node
            factor_node.add_child(self.parse_expresion())
            factor_node.add_child(self.consume("DELIMITADOR", ")", required=True))
        else:
            factor_node.add_child(ASTNode(f"Error at {self.line}:{self.column}: Expected factor"))
        print("Exiting parse_factor")
        return factor_node

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