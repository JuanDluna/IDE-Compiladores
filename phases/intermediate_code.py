# intermediate_code.py
# Generación de Código Intermedio (TAC - Three Address Code) - Fase 4 del Compilador

import os
from util.treeNode import ASTNode
from util.symbol_table import SymbolTable


class TACGenerator:
    """
    Generador de código intermedio TAC (Three Address Code).
    Recorre el AST anotado semánticamente y genera instrucciones TAC.
    """
    
    def __init__(self, annotations, symbol_table):
        """
        Inicializa el generador TAC.
        
        Args:
            annotations: Diccionario de anotaciones del análisis semántico {id_nodo: {'type': ..., 'value': ...}}
            symbol_table: Tabla de símbolos con información de variables
        """
        self.annotations = annotations
        self.symbol_table = symbol_table
        self.temp_counter = 0  # Contador para temporales: t0, t1, t2, ...
        self.label_counter = 0  # Contador para etiquetas: L0, L1, L2, ...
        self.instructions = []  # Lista de instrucciones TAC
        
    def get_node_id(self, node):
        """Obtiene el ID único de un nodo."""
        return id(node)
    
    def get_node_annotation(self, node):
        """Obtiene las anotaciones de un nodo."""
        node_id = self.get_node_id(node)
        return self.annotations.get(node_id, {})
    
    def new_temp(self):
        """Genera un nuevo temporal y retorna su nombre."""
        temp_name = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp_name
    
    def new_label(self):
        """Genera una nueva etiqueta y retorna su nombre."""
        label_name = f"L{self.label_counter}"
        self.label_counter += 1
        return label_name
    
    def add_instruction(self, instruction):
        """Agrega una instrucción TAC a la lista."""
        self.instructions.append(instruction)
    
    def extract_lexema(self, node_name):
        """Extrae el lexema de un nodo con formato 'lexema (linea:columna)' o simplemente el nombre."""
        if not node_name or not isinstance(node_name, str):
            return node_name
        
        if " (" in node_name:
            parts = node_name.rsplit(" (", 1)
            if len(parts) == 2:
                return parts[0]
        return node_name
    
    def generate_from_ast(self, ast_root):
        """
        Genera código TAC a partir del AST anotado.
        
        Args:
            ast_root: Nodo raíz del AST
        
        Returns:
            Lista de instrucciones TAC
        """
        self.instructions = []  # Reiniciar instrucciones
        self.temp_counter = 0
        self.label_counter = 0
        
        if ast_root is None:
            return []
        
        # El AST raíz es "Programa", sus hijos incluyen main, {, declaraciones/sentencias, }
        # Procesar todos los hijos que sean declaraciones o sentencias
        if hasattr(ast_root, 'children') and ast_root.children:
            for child in ast_root.children:
                if child is not None:
                    node_name = child.name if hasattr(child, 'name') else str(child)
                    lexema = self.extract_lexema(node_name)
                    
                    # Saltar nodos de formato (main, {, })
                    if lexema not in ('main', '{', '}', 'Programa'):
                        self.process_statement(child)
        
        return self.instructions
    
    def process_statement_list(self, node):
        """Procesa una lista de sentencias (bloque)."""
        if node is None:
            return
        
        # Si el nodo tiene hijos, procesarlos secuencialmente
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                if child is not None:
                    self.process_statement(child)
    
    def process_statement(self, node):
        """
        Procesa una sentencia individual y genera código TAC.
        """
        if node is None:
            return
        
        node_name = node.name if hasattr(node, 'name') else str(node)
        lexema = self.extract_lexema(node_name)
        
        # Saltar nodos de formato (main, {, })
        if lexema in ('main', '{', '}'):
            if hasattr(node, 'children') and node.children:
                for child in node.children:
                    self.process_statement(child)
            return
        
        # Declaración de variables
        if node_name == "Declaración":
            # Procesar declaración: puede tener tipo y luego identificadores con asignaciones opcionales
            if hasattr(node, 'children') and node.children:
                tipo_node = node.children[0]
                # Procesar los hijos restantes (identificadores y asignaciones)
                for i in range(1, len(node.children)):
                    child = node.children[i]
                    if child is not None:
                        # Si es una asignación, procesarla
                        if hasattr(child, 'name') and child.name == "=":
                            self.process_statement(child)
            return
        
        # Tipo solo (sin procesar por separado)
        if lexema in ('int', 'float', 'bool'):
            return
        
        # Asignación
        if lexema == "=":
            self.process_assignment(node)
        
        # Asignaciones compuestas
        elif lexema in ("+=", "-=", "*=", "/=", "%="):
            self.process_compound_assignment(node)
        
        # Expansión de ++/--
        elif lexema.startswith("Expansión de"):
            # Ya está expandido como asignación, procesar directamente
            if hasattr(node, 'children') and node.children:
                self.process_statement(node.children[0])
        
        # If statement
        elif lexema == "if":
            self.process_if_statement(node)
        
        # While statement
        elif lexema == "while":
            self.process_while_statement(node)
        
        # Do-while statement
        elif lexema == "do":
            self.process_do_while_statement(node)
        
        # Cin (entrada)
        elif lexema == "cin":
            self.process_cin(node)
        
        # Cout (salida)
        elif lexema == "cout":
            self.process_cout(node)
        
        # Si es un bloque o lista de sentencias, procesar hijos
        elif hasattr(node, 'children') and node.children:
            for child in node.children:
                self.process_statement(child)
    
    def process_expression(self, node):
        """
        Procesa una expresión y retorna el nombre de la variable/temporal que contiene el resultado.
        
        Returns:
            str: Nombre de la variable o temporal con el resultado
        """
        if node is None:
            return None
        
        node_name = node.name if hasattr(node, 'name') else str(node)
        lexema = self.extract_lexema(node_name)
        
        # Obtener anotaciones del nodo
        annotation = self.get_node_annotation(node)
        node_type = annotation.get('type')
        node_value = annotation.get('value')
        
        # Literal numérico o booleano
        if self.is_literal(node):
            literal_value = self.get_literal_value(node)
            # Si es un valor constante, podemos optimizar y retornarlo directamente
            # o crear una instrucción de asignación
            temp = self.new_temp()
            self.add_instruction(f"{temp} = {literal_value}")
            return temp
        
        # Identificador (variable)
        if self.is_identifier(node):
            var_name = lexema
            return var_name
        
        # Operaciones aritméticas: +, -, *, /, %
        if lexema in ("+", "-", "*", "/", "%"):
            return self.process_arithmetic_op(node, lexema)
        
        # Operaciones relacionales: <, >, <=, >=, ==, !=
        if lexema in ("<", ">", "<=", ">=", "==", "!="):
            return self.process_relational_op(node, lexema)
        
        # Operaciones lógicas: &&, ||
        if lexema in ("&&", "||"):
            return self.process_logical_op(node, lexema)
        
        # Negación lógica: !
        if lexema == "!":
            return self.process_negation(node)
        
        # Paréntesis o subexpresión: procesar el hijo
        if hasattr(node, 'children') and node.children:
            # Si tiene un solo hijo, es probablemente una subexpresión
            if len(node.children) == 1:
                return self.process_expression(node.children[0])
            # Si tiene múltiples hijos, puede ser una operación
            # Por ahora, procesar recursivamente el primer hijo
            return self.process_expression(node.children[0])
        
        return None
    
    def is_literal(self, node):
        """Verifica si un nodo es un literal (número o booleano)."""
        if node is None:
            return False
        
        node_name = node.name if hasattr(node, 'name') else str(node)
        lexema = self.extract_lexema(node_name)
        
        # Verificar si es un número
        try:
            float(lexema)
            return True
        except ValueError:
            pass
        
        # Verificar si es un booleano
        if lexema in ('true', 'false'):
            return True
        
        return False
    
    def get_literal_value(self, node):
        """Obtiene el valor de un literal."""
        if node is None:
            return None
        
        node_name = node.name if hasattr(node, 'name') else str(node)
        lexema = self.extract_lexema(node_name)
        
        # Obtener valor desde anotaciones si está disponible
        annotation = self.get_node_annotation(node)
        value = annotation.get('value')
        if value is not None:
            return self.format_value(value, annotation.get('type'))
        
        # Si no hay anotación, intentar parsear
        try:
            if '.' in lexema:
                return float(lexema)
            else:
                return int(lexema)
        except ValueError:
            if lexema in ('true', 'false'):
                return lexema == 'true'
        
        return lexema
    
    def format_value(self, value, value_type):
        """Formatea un valor según su tipo para el TAC."""
        if value is None:
            return "0"
        
        if value_type == 'float':
            if isinstance(value, float):
                if value.is_integer():
                    return f"{int(value)}.0"
                return str(value)
            elif isinstance(value, int):
                return f"{value}.0"
        
        if value_type == 'bool':
            if isinstance(value, bool):
                return "true" if value else "false"
            return str(value)
        
        return str(value)
    
    def is_identifier(self, node):
        """Verifica si un nodo es un identificador (variable)."""
        if node is None:
            return False
        
        node_name = node.name if hasattr(node, 'name') else str(node)
        lexema = self.extract_lexema(node_name)
        
        # Si no es un literal y parece un identificador válido
        if not self.is_literal(node):
            # Verificar que no sea un operador
            if lexema not in ("+", "-", "*", "/", "%", "<", ">", "<=", ">=", "==", "!=", "&&", "||", "!", "=", "+=", "-=", "*=", "/=", "%="):
                # Verificar formato de token
                if " (" in node_name:
                    return True
                # Si no tiene formato, puede ser un identificador simple
                if lexema and (lexema[0].isalpha() or lexema[0] == '_'):
                    return True
        
        return False
    
    def process_arithmetic_op(self, node, operator):
        """Procesa una operación aritmética."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return None
        
        left_node = node.children[0]
        right_node = node.children[1]
        
        left_result = self.process_expression(left_node)
        right_result = self.process_expression(right_node)
        
        if left_result is None or right_result is None:
            return None
        
        result_temp = self.new_temp()
        self.add_instruction(f"{result_temp} = {left_result} {operator} {right_result}")
        return result_temp
    
    def process_relational_op(self, node, operator):
        """Procesa una operación relacional (retorna un temporal booleano con 'true' o 'false')."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return None
        
        left_node = node.children[0]
        right_node = node.children[1]
        
        left_result = self.process_expression(left_node)
        right_result = self.process_expression(right_node)
        
        if left_result is None or right_result is None:
            return None
        
        result_temp = self.new_temp()
        # Generar instrucción que evalúe a 'true' o 'false'
        self.add_instruction(f"{result_temp} = {left_result} {operator} {right_result}")
        return result_temp
    
    def process_logical_op(self, node, operator):
        """Procesa una operación lógica (retorna un temporal booleano con 'true' o 'false')."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return None
        
        left_node = node.children[0]
        right_node = node.children[1]
        
        left_result = self.process_expression(left_node)
        right_result = self.process_expression(right_node)
        
        if left_result is None or right_result is None:
            return None
        
        result_temp = self.new_temp()
        # Convertir operadores lógicos
        tac_op = "&&" if operator == "&&" else "||"
        self.add_instruction(f"{result_temp} = {left_result} {tac_op} {right_result}")
        return result_temp
    
    def process_negation(self, node):
        """Procesa una negación lógica."""
        if not hasattr(node, 'children') or len(node.children) < 1:
            return None
        
        expr_node = node.children[0]
        expr_result = self.process_expression(expr_node)
        
        if expr_result is None:
            return None
        
        result_temp = self.new_temp()
        self.add_instruction(f"{result_temp} = ! {expr_result}")
        return result_temp
    
    def process_assignment(self, node):
        """Procesa una asignación simple: var = expr"""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return
        
        # Hijo 0: identificador (variable destino)
        id_node = node.children[0]
        var_name = self.extract_lexema(id_node.name if hasattr(id_node, 'name') else str(id_node))
        
        # Hijo 1: expresión (valor a asignar)
        expr_node = node.children[1]
        expr_result = self.process_expression(expr_node)
        
        if expr_result is not None:
            self.add_instruction(f"{var_name} = {expr_result}")
    
    def process_compound_assignment(self, node):
        """Procesa una asignación compuesta: var += expr, var -= expr, etc."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return
        
        # Extraer operador base
        operator = self.extract_lexema(node.name)
        base_op = operator[0]  # +, -, *, /, %
        
        # Hijo 0: identificador
        id_node = node.children[0]
        var_name = self.extract_lexema(id_node.name if hasattr(id_node, 'name') else str(id_node))
        
        # Hijo 1: expresión
        expr_node = node.children[1]
        expr_result = self.process_expression(expr_node)
        
        if expr_result is not None:
            # Generar: var = var op expr
            temp = self.new_temp()
            self.add_instruction(f"{temp} = {var_name} {base_op} {expr_result}")
            self.add_instruction(f"{var_name} = {temp}")
    
    def process_if_statement(self, node):
        """Procesa un if-then-else-end."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return
        
        # Estructura esperada: [Condición, then, else?]
        children = node.children
        
        # Buscar nodo de condición
        cond_node = None
        then_node = None
        else_node = None
        
        for child in children:
            child_name = child.name if hasattr(child, 'name') else str(child)
            if child_name == "Condición":
                cond_node = child
            elif child_name == "then":
                then_node = child
            elif child_name == "else":
                else_node = child
        
        if cond_node is None or then_node is None:
            return
        
        # Procesar condición
        if hasattr(cond_node, 'children') and cond_node.children:
            cond_expr = cond_node.children[0]
            cond_result = self.process_expression(cond_expr)
            
            if cond_result is not None:
                # Generar etiquetas
                else_label = self.new_label() if else_node else None
                end_label = self.new_label()
                
                # Saltar al else si la condición es falsa
                if else_node:
                    self.add_instruction(f"if {cond_result} == false goto {else_label}")
                else:
                    self.add_instruction(f"if {cond_result} == false goto {end_label}")
                
                # Código del then
                if hasattr(then_node, 'children') and then_node.children:
                    for stmt in then_node.children:
                        self.process_statement(stmt)
                
                # Si hay else, agregar salto al final y procesar else
                if else_node:
                    self.add_instruction(f"goto {end_label}")
                    self.add_instruction(f"{else_label}:")
                    
                    if hasattr(else_node, 'children') and else_node.children:
                        for stmt in else_node.children:
                            self.process_statement(stmt)
                
                # Etiqueta de fin
                self.add_instruction(f"{end_label}:")
    
    def process_while_statement(self, node):
        """Procesa un while-end."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return
        
        # Estructura: [Condición, Cuerpo]
        children = node.children
        
        cond_node = None
        body_node = None
        
        for child in children:
            child_name = child.name if hasattr(child, 'name') else str(child)
            if child_name == "Condición":
                cond_node = child
            elif child_name == "Cuerpo":
                body_node = child
        
        if cond_node is None or body_node is None:
            return
        
        # Generar etiquetas
        loop_label = self.new_label()
        end_label = self.new_label()
        
        # Etiqueta de inicio del ciclo
        self.add_instruction(f"{loop_label}:")
        
        # Evaluar condición
        if hasattr(cond_node, 'children') and cond_node.children:
            cond_expr = cond_node.children[0]
            cond_result = self.process_expression(cond_expr)
            
            if cond_result is not None:
                # Saltar al final si la condición es falsa
                self.add_instruction(f"if {cond_result} == false goto {end_label}")
        
        # Código del cuerpo
        if hasattr(body_node, 'children') and body_node.children:
            for stmt in body_node.children:
                self.process_statement(stmt)
        
        # Volver al inicio del ciclo
        self.add_instruction(f"goto {loop_label}")
        
        # Etiqueta de fin
        self.add_instruction(f"{end_label}:")
    
    def process_do_while_statement(self, node):
        """Procesa un do-until."""
        if not hasattr(node, 'children') or len(node.children) < 2:
            return
        
        # Estructura: [Cuerpo, Condición]
        children = node.children
        
        body_node = None
        cond_node = None
        
        for child in children:
            child_name = child.name if hasattr(child, 'name') else str(child)
            if child_name == "Cuerpo":
                body_node = child
            elif child_name == "Condición":
                cond_node = child
        
        if body_node is None or cond_node is None:
            return
        
        # Generar etiquetas
        loop_label = self.new_label()
        end_label = self.new_label()
        
        # Etiqueta de inicio del ciclo
        self.add_instruction(f"{loop_label}:")
        
        # Código del cuerpo
        if hasattr(body_node, 'children') and body_node.children:
            for stmt in body_node.children:
                self.process_statement(stmt)
        
        # Evaluar condición (until: repetir mientras condición sea falsa)
        if hasattr(cond_node, 'children') and cond_node.children:
            cond_expr = cond_node.children[0]
            cond_result = self.process_expression(cond_expr)
            
            if cond_result is not None:
                # Si la condición es verdadera, salir del ciclo
                self.add_instruction(f"if {cond_result} == true goto {end_label}")
        
        # Volver al inicio si la condición es falsa
        self.add_instruction(f"goto {loop_label}")
        
        # Etiqueta de fin
        self.add_instruction(f"{end_label}:")
    
    def process_cin(self, node):
        """Procesa una entrada: cin >> var"""
        if not hasattr(node, 'children') or len(node.children) < 1:
            return
        
        # El hijo es el identificador
        id_node = node.children[0]
        var_name = self.extract_lexema(id_node.name if hasattr(id_node, 'name') else str(id_node))
        
        self.add_instruction(f"read {var_name}")
    
    def process_cout(self, node):
        """Procesa una salida: cout << expr"""
        if not hasattr(node, 'children') or len(node.children) < 1:
            return
        
        # El hijo es la expresión
        expr_node = node.children[0]
        expr_result = self.process_expression(expr_node)
        
        if expr_result is not None:
            self.add_instruction(f"write {expr_result}")
    
    def save_to_file(self, filename="codigo_intermedio.tac"):
        """Guarda las instrucciones TAC en un archivo."""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                for instruction in self.instructions:
                    f.write(instruction + "\n")
            return True
        except Exception as e:
            print(f"Error guardando archivo TAC: {e}")
            return False


class TACInterpreter:
    """
    Intérprete (máquina virtual) para ejecutar código TAC.
    """
    
    def __init__(self):
        """Inicializa el intérprete TAC."""
        self.memory = {}  # Almacén de variables y temporales
        self.instructions = []  # Lista de instrucciones TAC
        self.pc = 0  # Program counter (índice de instrucción actual)
        self.labels = {}  # Mapeo de etiquetas a índices de instrucción
        self.output = []  # Salida del programa (para cout)
        self.input_queue = []  # Cola de entrada (para cin)
        self.running = False
        self.error = None
        self.output_callback = None  # Callback para salida
        self.input_callback = None  # Callback para solicitud de entrada
    
    def load_from_file(self, filename="codigo_intermedio.tac"):
        """Carga instrucciones TAC desde un archivo."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.instructions = [line.strip() for line in f if line.strip()]
            self._build_label_map()
            return True
        except Exception as e:
            self.error = f"Error cargando archivo TAC: {e}"
            return False
    
    def load_from_list(self, instructions):
        """Carga instrucciones TAC desde una lista."""
        self.instructions = [inst.strip() for inst in instructions if inst.strip()]
        self._build_label_map()
    
    def _build_label_map(self):
        """Construye el mapeo de etiquetas a índices de instrucción."""
        self.labels = {}
        for i, instruction in enumerate(self.instructions):
            if instruction.endswith(':'):
                label = instruction[:-1].strip()
                self.labels[label] = i
    
    def set_input(self, values):
        """Establece valores de entrada para cin."""
        self.input_queue = list(values)
    
    def get_output(self):
        """Retorna la salida acumulada del programa."""
        return "\n".join(str(v) for v in self.output)
    
    def reset(self):
        """Reinicia el intérprete."""
        self.memory = {}
        self.pc = 0
        self.output = []
        self.input_queue = []
        self.running = False
        self.error = None
    
    def get_value(self, identifier):
        """Obtiene el valor de una variable o temporal."""
        identifier = identifier.strip()
        
        # Primero verificar en memoria
        if identifier in self.memory:
            return self.memory[identifier]
        
        # Intentar como literal booleano (retornar como string 'true'/'false')
        if identifier == 'true':
            return 'true'
        if identifier == 'false':
            return 'false'
        
        # Intentar como número (puede ser un literal en la expresión)
        try:
            if '.' in identifier:
                return float(identifier)
            else:
                return int(identifier)
        except ValueError:
            pass
        
        # Si no se encuentra, retornar 0 (variable no inicializada)
        # Esto puede causar errores, pero es mejor que None
        return 0
    
    def set_value(self, identifier, value):
        """Establece el valor de una variable o temporal."""
        self.memory[identifier] = value
    
    def parse_value(self, value_str):
        """Parsea un valor desde un string."""
        # Verificar si es un identificador
        if value_str in self.memory:
            return self.memory[value_str]
        
        # Verificar si es booleano
        if value_str == 'true':
            return True
        if value_str == 'false':
            return False
        
        # Verificar si es número
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # Si no se puede parsear, retornar 0
        return 0
    
    def execute(self, max_steps=10000):
        """
        Ejecuta el código TAC.
        
        Args:
            max_steps: Número máximo de instrucciones a ejecutar (para evitar loops infinitos)
        
        Returns:
            (success: bool, error_message: str)
        """
        self.reset()
        self.running = True
        steps = 0
        
        while self.running and self.pc < len(self.instructions) and steps < max_steps:
            instruction = self.instructions[self.pc].strip()
            
            # Saltar etiquetas (ya procesadas en el mapeo)
            if instruction.endswith(':'):
                self.pc += 1
                steps += 1
                continue
            
            # Ejecutar instrucción
            success, error = self._execute_instruction(instruction)
            if not success:
                self.error = error
                self.running = False
                return False, error
            
            self.pc += 1
            steps += 1
        
        if steps >= max_steps:
            return False, f"Límite de pasos alcanzado ({max_steps}). Posible ciclo infinito."
        
        return True, None
    
    def _execute_instruction(self, instruction):
        """Ejecuta una instrucción TAC individual."""
        try:
            # Asignación: var = value
            if " = " in instruction:
                parts = instruction.split(" = ", 1)
                if len(parts) == 2:
                    var = parts[0].strip()
                    expr = parts[1].strip()
                    value = self._evaluate_expression(expr)
                    # Si el resultado es booleano, guardar como 'true' o 'false'
                    if isinstance(value, bool):
                        value = 'true' if value else 'false'
                    self.set_value(var, value)
                    return True, None
            
            # Salto condicional: if cond goto label
            if instruction.startswith("if "):
                return self._execute_conditional_jump(instruction)
            
            # Salto incondicional: goto label
            if instruction.startswith("goto "):
                label = instruction[5:].strip()
                if label in self.labels:
                    self.pc = self.labels[label]
                    return True, None
                else:
                    return False, f"Etiqueta '{label}' no encontrada"
            
            # Entrada: read var
            if instruction.startswith("read "):
                var = instruction[5:].strip()
                
                if self.input_queue:
                    value = self.input_queue.pop(0)
                    # Intentar convertir a número
                    try:
                        if isinstance(value, str):
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                    except ValueError:
                        pass
                    self.set_value(var, value)
                    return True, None
                else:
                    # Si no hay entrada en la cola, llamar callback y pausar
                    if self.input_callback:
                        self.input_callback(var)
                    # Retornar un estado especial que indique que necesita pausar
                    # No avanzar el PC, se avanzará cuando llegue el valor
                    return "PAUSE", var  # Estado especial: necesita entrada
            
            # Salida: write expr
            if instruction.startswith("write "):
                expr = instruction[6:].strip()
                value = self._evaluate_expression(expr)
                self.output.append(value)
                # Llamar callback si existe
                if self.output_callback:
                    self.output_callback(value)
                return True, None
            
            return True, None  # Instrucción desconocida, ignorar
        
        except Exception as e:
            return False, f"Error ejecutando instrucción '{instruction}': {e}"
    
    def _execute_conditional_jump(self, instruction):
        """Ejecuta un salto condicional."""
        # Formato: if cond goto label
        # Ejemplos: if t0 == false goto L1, if t1 > 0 goto L2
        
        # Extraer condición y etiqueta
        if " goto " not in instruction:
            return False, "Formato de salto condicional inválido"
        
        parts = instruction.split(" goto ", 1)
        condition = parts[0][3:].strip()  # Quitar "if "
        label = parts[1].strip()
        
        if label not in self.labels:
            return False, f"Etiqueta '{label}' no encontrada"
        
        # Evaluar condición
        result = self._evaluate_boolean_condition(condition)
        
        if result:
            self.pc = self.labels[label]
            return True, None
        else:
            return True, None  # No saltar
    
    def _evaluate_boolean_condition(self, condition):
        """Evalúa una condición booleana."""
        # Formato: expr1 op expr2
        operators = ["==", "!=", "<=", ">=", "<", ">"]
        
        for op in operators:
            if op in condition:
                parts = condition.split(op, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    left_val = self._evaluate_expression(left)
                    right_val = self._evaluate_expression(right)
                    
                    # Convertir 'true'/'false' a booleanos para comparar
                    left_bool = self._to_bool(left_val)
                    right_bool = self._to_bool(right_val)
                    
                    if op == "==":
                        return left_bool == right_bool
                    elif op == "!=":
                        return left_bool != right_bool
                    elif op == "<=":
                        return left_bool <= right_bool
                    elif op == ">=":
                        return left_bool >= right_bool
                    elif op == "<":
                        return left_bool < right_bool
                    elif op == ">":
                        return left_bool > right_bool
        
        # Si no hay operador, evaluar como expresión booleana
        value = self._evaluate_expression(condition)
        return self._to_bool(value)
    
    def _evaluate_expression(self, expr):
        """Evalúa una expresión aritmética o booleana respetando precedencia de operadores."""
        expr = expr.strip()
        
        # Si está vacío, retornar 0
        if not expr:
            return 0
        
        # Negación
        if expr.startswith("!"):
            val = self._evaluate_expression(expr[1:].strip())
            # Convertir a booleano y luego a 'true'/'false'
            result = not bool(self._to_bool(val))
            return 'true' if result else 'false'
        
        # Operadores relacionales (mayor precedencia que lógicos, menor que aritméticos)
        # IMPORTANTE: Para comparaciones relacionales, comparamos valores numéricos, no booleanos
        for op in ["==", "!=", "<=", ">=", "<", ">"]:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    left_val = self._evaluate_expression(left)
                    right_val = self._evaluate_expression(right)
                    
                    # Convertir a números para comparar (no a booleanos)
                    # Si son 'true'/'false', convertirlos a números primero
                    left_num = self._to_number(left_val)
                    right_num = self._to_number(right_val)
                    
                    if op == "==":
                        result = left_num == right_num
                    elif op == "!=":
                        result = left_num != right_num
                    elif op == "<=":
                        result = left_num <= right_num
                    elif op == ">=":
                        result = left_num >= right_num
                    elif op == "<":
                        result = left_num < right_num
                    elif op == ">":
                        result = left_num > right_num
                    else:
                        continue
                    
                    return 'true' if result else 'false'
        
        # Operadores lógicos (menor precedencia)
        if "||" in expr:
            parts = expr.split("||", 1)
            if len(parts) == 2:
                left_val = self._evaluate_expression(parts[0].strip())
                right_val = self._evaluate_expression(parts[1].strip())
                result = bool(self._to_bool(left_val)) or bool(self._to_bool(right_val))
                return 'true' if result else 'false'
        
        if "&&" in expr:
            parts = expr.split("&&", 1)
            if len(parts) == 2:
                left_val = self._evaluate_expression(parts[0].strip())
                right_val = self._evaluate_expression(parts[1].strip())
                result = bool(self._to_bool(left_val)) and bool(self._to_bool(right_val))
                return 'true' if result else 'false'
        
        # Operadores aritméticos: primero * / %, luego + -
        # Buscar desde la derecha para respetar asociatividad izquierda
        for op in ["*", "/", "%"]:
            # Buscar desde la derecha para respetar precedencia
            last_pos = expr.rfind(op)
            if last_pos > 0:
                # Verificar que no sea parte de un identificador o número
                if last_pos > 0 and (expr[last_pos - 1].isspace() or not expr[last_pos - 1].isalnum()):
                    left = expr[:last_pos].strip()
                    right = expr[last_pos + len(op):].strip()
                    
                    if left and right:  # Asegurar que ambas partes existen
                        left_val = self._evaluate_expression(left)
                        right_val = self._evaluate_expression(right)
                        
                        # Convertir 'true'/'false' a números si es necesario
                        left_num = self._to_number(left_val)
                        right_num = self._to_number(right_val)
                        
                        if op == "*":
                            return left_num * right_num
                        elif op == "/":
                            return left_num / right_num if right_num != 0 else 0
                        elif op == "%":
                            return left_num % right_num if right_num != 0 else 0
        
        # Operadores + y - (menor precedencia que * / %)
        # Buscar desde la derecha, evitando números negativos
        for op in ["+", "-"]:
            last_pos = expr.rfind(op)
            if last_pos > 0:  # No al inicio
                # Verificar que no sea parte de un número negativo o identificador
                char_before = expr[last_pos - 1]
                if char_before.isspace() or (not char_before.isalnum() and char_before != '.'):
                    left = expr[:last_pos].strip()
                    right = expr[last_pos + len(op):].strip()
                    
                    if left and right:  # Asegurar que ambas partes existen
                        left_val = self._evaluate_expression(left)
                        right_val = self._evaluate_expression(right)
                        
                        # Convertir 'true'/'false' a números si es necesario
                        left_num = self._to_number(left_val)
                        right_num = self._to_number(right_val)
                        
                        if op == "+":
                            return left_num + right_num
                        elif op == "-":
                            return left_num - right_num
        
        # Valor simple (variable, literal, temporal)
        return self.get_value(expr)
    
    def _to_bool(self, value):
        """Convierte un valor a booleano, manejando 'true'/'false' y números."""
        if value == 'true':
            return True
        if value == 'false':
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        # Intentar convertir string a número
        try:
            if isinstance(value, str):
                if '.' in value:
                    return bool(float(value))
                else:
                    return bool(int(value))
        except ValueError:
            pass
        return bool(value)
    
    def _to_number(self, value):
        """Convierte un valor a número, manejando 'true'/'false'."""
        if value == 'true':
            return 1
        if value == 'false':
            return 0
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return value
        # Intentar convertir string a número
        try:
            if isinstance(value, str):
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
        except ValueError:
            pass
        return 0


def generate_and_run_intermediate_code(ast_root, annotations, symbol_table=None, input_values=None):
    """
    Función pública principal que genera código TAC y lo ejecuta.
    
    Args:
        ast_root: Nodo raíz del AST anotado
        annotations: Diccionario de anotaciones del análisis semántico
        symbol_table: Tabla de símbolos (opcional)
        input_values: Lista de valores de entrada para cin (opcional)
    
    Returns:
        (instructions: list, execution_output: str, success: bool, error: str)
    """
    # Generar código TAC
    generator = TACGenerator(annotations, symbol_table)
    instructions = generator.generate_from_ast(ast_root)
    
    # Guardar en archivo
    generator.save_to_file("codigo_intermedio.tac")
    
    # Ejecutar código TAC
    interpreter = TACInterpreter()
    interpreter.load_from_list(instructions)
    
    # Establecer valores de entrada si se proporcionan
    if input_values is not None:
        interpreter.set_input(input_values)
    
    success, error = interpreter.execute()
    output = interpreter.get_output()
    
    return instructions, output, success, error


if __name__ == "__main__":
    # Prueba del generador e intérprete TAC
    print("Generación e interpretación de código intermedio TAC")
    print("Esta funcionalidad debe ser llamada desde el IDE o después del análisis semántico.")

