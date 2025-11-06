# semantic.py
# Análisis Semántico - Fase 3 del Compilador

import json
import os
from util.treeNode import ASTNode
from util.symbol_table import SymbolTable, SymbolEntry


class SemanticError:
    """Representa un error semántico."""
    def __init__(self, tipo, descripcion, linea, columna, fatal=False):
        self.tipo = tipo
        self.descripcion = descripcion
        self.linea = linea
        self.columna = columna
        self.fatal = fatal
    
    def __str__(self):
        fatal_str = "FATAL" if self.fatal else ""
        return f"{self.tipo}\t{self.descripcion}\t{self.linea}:{self.columna}\t{fatal_str}".strip()
    
    def to_dict(self):
        return {
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "linea": self.linea,
            "columna": self.columna,
            "fatal": self.fatal
        }


class SemanticAnalyzer:
    """Analizador semántico que recorre el AST y verifica reglas semánticas."""
    
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.annotations = {}  # Diccionario para anotar nodos: {id_nodo: {'type': ..., 'value': ...}}
        self.node_counter = 0
        self.should_stop = False  # Para errores fatales
    
    def parse_token_node(self, node_name):
        """
        Parsea un nodo terminal con formato 'lexema (linea:columna)'.
        Retorna (lexema, linea, columna) o None si no es válido.
        """
        if not node_name or not isinstance(node_name, str):
            return None
        
        # Formato esperado: "lexema (linea:columna)"
        if " (" in node_name and ")" in node_name:
            parts = node_name.rsplit(" (", 1)
            if len(parts) == 2:
                lexema = parts[0]
                loc_part = parts[1].rstrip(")")
                if ":" in loc_part:
                    try:
                        linea, columna = map(int, loc_part.split(":"))
                        return lexema, linea, columna
                    except ValueError:
                        pass
        return None
    
    def get_node_id(self, node):
        """Genera un ID único para un nodo (usando id() de Python)."""
        return id(node)
    
    def annotate_node(self, node, tipo=None, valor=None):
        """Anota un nodo con tipo y/o valor."""
        node_id = self.get_node_id(node)
        if node_id not in self.annotations:
            self.annotations[node_id] = {}
        if tipo is not None:
            self.annotations[node_id]['type'] = tipo
        if valor is not None:
            self.annotations[node_id]['value'] = valor
    
    def get_node_annotation(self, node):
        """Obtiene las anotaciones de un nodo."""
        node_id = self.get_node_id(node)
        return self.annotations.get(node_id, {})
    
    def report_error(self, tipo, descripcion, linea, columna, fatal=False):
        """Reporta un error semántico."""
        error = SemanticError(tipo, descripcion, linea, columna, fatal)
        self.errors.append(error)
        if fatal:
            self.should_stop = True
        return error
    
    def infer_type_from_literal(self, lexema):
        """
        Infiere el tipo de un literal (número o booleano).
        Retorna 'int', 'float', 'bool' o None.
        """
        if lexema in ('true', 'false'):
            return 'bool'
        try:
            if '.' in lexema or 'e' in lexema.lower() or 'E' in lexema:
                float(lexema)
                return 'float'
            else:
                int(lexema)
                return 'int'
        except ValueError:
            return None
    
    def check_type_compatibility(self, tipo_dest, tipo_src, linea, columna, contexto="asignación"):
        """
        Verifica compatibilidad de tipos.
        Retorna (es_compatible, mensaje_error).
        """
        if tipo_dest == tipo_src:
            return True, None
        
        # Promoción int -> float permitida
        if tipo_dest == 'float' and tipo_src == 'int':
            return True, None
        
        # int <- float no permitido (error)
        if tipo_dest == 'int' and tipo_src == 'float':
            return False, f"Incompatibilidad de tipos en {contexto}: no se puede asignar float a int"
        
        # bool solo con bool
        if tipo_dest == 'bool' and tipo_src != 'bool':
            return False, f"Incompatibilidad de tipos en {contexto}: se esperaba bool, se encontró {tipo_src}"
        
        if tipo_src == 'bool' and tipo_dest != 'bool':
            return False, f"Incompatibilidad de tipos en {contexto}: no se puede usar bool donde se espera {tipo_dest}"
        
        return False, f"Incompatibilidad de tipos en {contexto}: {tipo_dest} vs {tipo_src}"
    
    def analyze_expression(self, node):
        """
        Analiza una expresión y retorna su tipo inferido.
        Anota el nodo con el tipo resultante.
        """
        if not node:
            return None
        
        node_name = node.name
        
        # Si es un nodo terminal (token)
        parsed = self.parse_token_node(node_name)
        if parsed:
            lexema, linea, columna = parsed
            
            # Verificar si es un operador (no debe tratarse como identificador)
            operadores = ['+', '-', '*', '/', '%', '<', '>', '<=', '>=', '==', '!=', 
                         '&&', '||', '!', '=', '++', '--', '>>', '<<']
            if lexema in operadores:
                # Es un operador que viene como token. Actualizar el nombre del nodo
                # para que se maneje correctamente en la sección de operadores
                node.name = lexema
                # Continuar con el procesamiento de operadores más abajo (no buscar como identificador)
            else:
                # No es un operador, puede ser literal o identificador
                # Es un literal
                tipo = self.infer_type_from_literal(lexema)
                if tipo:
                    self.annotate_node(node, tipo=tipo, valor=lexema)
                    return tipo
                
                # Es un identificador
                entry, error_msg = self.symbol_table.lookup(lexema, linea, columna)
                if entry:
                    self.annotate_node(node, tipo=entry.tipo)
                    return entry.tipo
                else:
                    self.report_error("VARIABLE_NO_DECLARADA", error_msg, linea, columna, fatal=False)
                    return None
        
        # Si es un operador (verificar node_name directamente o después de actualizar desde token)
        node_name = node.name  # Actualizar por si se modificó arriba
        if node_name in ('+', '-', '*', '/', '%'):
            return self.analyze_arithmetic_op(node)
        elif node_name in ('<', '>', '<=', '>=', '==', '!='):
            return self.analyze_relational_op(node)
        elif node_name in ('&&', '||'):
            return self.analyze_logical_op(node)
        elif node_name == '!':
            return self.analyze_negation(node)
        elif node_name == '=':
            return self.analyze_assignment(node)
        
        # Si es un nodo no terminal con estructura conocida, analizar recursivamente
        # Por ejemplo, nodos como "Condición" que contienen expresiones
        if node.children:
            # Analizar todos los hijos y propagar el tipo y valor del último hijo válido
            ultimo_tipo = None
            ultimo_valor = None
            tiene_error = False
            
            for child in node.children:
                tipo = self.analyze_expression(child)
                if tipo:
                    ultimo_tipo = tipo
                    # Obtener valor del hijo si está disponible
                    child_annotations = self.get_node_annotation(child)
                    if 'value' in child_annotations and child_annotations['value'] is not None:
                        ultimo_valor = child_annotations['value']
                elif tipo is None and child is not None:
                    # Verificar si el hijo tiene un error explícito
                    child_annotations = self.get_node_annotation(child)
                    if 'type' in child_annotations and child_annotations['type'] is None:
                        tiene_error = True
            
            # Anotar el nodo padre con el tipo y valor del último hijo válido
            if tiene_error:
                self.annotate_node(node, tipo=None)
                return None
            elif ultimo_tipo:
                self.annotate_node(node, tipo=ultimo_tipo, valor=ultimo_valor)
                return ultimo_tipo
        
        # Si no se pudo inferir, retornar None
        return None
    
    def analyze_arithmetic_op(self, node):
        """Analiza operación aritmética: +, -, *, /, %"""
        if len(node.children) < 2:
            return None
        
        left_type = self.analyze_expression(node.children[0])
        right_type = self.analyze_expression(node.children[1])
        
        # Obtener valores de los hijos si están disponibles
        left_annotations = self.get_node_annotation(node.children[0])
        right_annotations = self.get_node_annotation(node.children[1])
        left_value = left_annotations.get('value')
        right_value = right_annotations.get('value')
        
        if not left_type or not right_type:
            # Si hay error en los hijos, propagar el error
            self.annotate_node(node, tipo=None)
            return None
        
        # Verificar que sean numéricos
        if left_type == 'bool' or right_type == 'bool':
            parsed = self.parse_token_node(node.children[0].name) or self.parse_token_node(node.children[1].name)
            if parsed:
                _, linea, columna = parsed
            else:
                linea, columna = 0, 0
            self.report_error("TIPO_INCOMPATIBLE", 
                            f"Operador aritmético '{node.name}' no puede usarse con bool", 
                            linea, columna)
            self.annotate_node(node, tipo=None)
            return None
        
        # Resultado: float si alguno es float, sino int
        result_type = 'float' if (left_type == 'float' or right_type == 'float') else 'int'
        
        # Calcular valor si ambos operandos tienen valores
        result_value = None
        if left_value is not None and right_value is not None:
            try:
                left_num = float(left_value) if result_type == 'float' or '.' in str(left_value) else int(left_value)
                right_num = float(right_value) if result_type == 'float' or '.' in str(right_value) else int(right_value)
                
                if node.name == '+':
                    result_value = left_num + right_num
                elif node.name == '-':
                    result_value = left_num - right_num
                elif node.name == '*':
                    result_value = left_num * right_num
                elif node.name == '/':
                    if right_num == 0:
                        result_value = None  # División por cero
                    else:
                        result_value = left_num / right_num
                elif node.name == '%':
                    result_value = left_num % right_num
                
                # Formatear resultado
                if result_value is not None:
                    if result_type == 'int':
                        result_value = int(result_value)
                    else:
                        result_value = float(result_value)
            except (ValueError, TypeError):
                result_value = None
        
        self.annotate_node(node, tipo=result_type, valor=result_value)
        return result_type
    
    def analyze_relational_op(self, node):
        """Analiza operador relacional: <, >, <=, >=, ==, !="""
        if len(node.children) < 2:
            return None
        
        left_type = self.analyze_expression(node.children[0])
        right_type = self.analyze_expression(node.children[1])
        
        # Obtener valores de los hijos si están disponibles
        left_annotations = self.get_node_annotation(node.children[0])
        right_annotations = self.get_node_annotation(node.children[1])
        left_value = left_annotations.get('value')
        right_value = right_annotations.get('value')
        
        if not left_type or not right_type:
            self.annotate_node(node, tipo=None)
            return None
        
        # Comparar bool con número → error
        if (left_type == 'bool' and right_type != 'bool') or (right_type == 'bool' and left_type != 'bool'):
            parsed = self.parse_token_node(node.children[0].name) or self.parse_token_node(node.children[1].name)
            if parsed:
                _, linea, columna = parsed
            else:
                linea, columna = 0, 0
            self.report_error("TIPO_INCOMPATIBLE",
                            f"No se puede comparar bool con {right_type if left_type == 'bool' else left_type}",
                            linea, columna)
            self.annotate_node(node, tipo=None)
            return None
        
        # Calcular valor si ambos operandos tienen valores
        result_value = None
        if left_value is not None and right_value is not None:
            try:
                left_num = float(left_value) if '.' in str(left_value) else int(left_value)
                right_num = float(right_value) if '.' in str(right_value) else int(right_value)
                
                if node.name == '<':
                    result_value = left_num < right_num
                elif node.name == '>':
                    result_value = left_num > right_num
                elif node.name == '<=':
                    result_value = left_num <= right_num
                elif node.name == '>=':
                    result_value = left_num >= right_num
                elif node.name == '==':
                    result_value = left_num == right_num
                elif node.name == '!=':
                    result_value = left_num != right_num
                
                result_value = 'true' if result_value else 'false'
            except (ValueError, TypeError):
                result_value = None
        
        # Relacionales producen bool
        self.annotate_node(node, tipo='bool', valor=result_value)
        return 'bool'
    
    def analyze_logical_op(self, node):
        """Analiza operador lógico: &&, ||"""
        if len(node.children) < 2:
            return None
        
        left_type = self.analyze_expression(node.children[0])
        right_type = self.analyze_expression(node.children[1])
        
        # Obtener valores de los hijos si están disponibles
        left_annotations = self.get_node_annotation(node.children[0])
        right_annotations = self.get_node_annotation(node.children[1])
        left_value = left_annotations.get('value')
        right_value = right_annotations.get('value')
        
        if not left_type or not right_type:
            self.annotate_node(node, tipo=None)
            return None
        
        # Deben ser bool
        if left_type != 'bool' or right_type != 'bool':
            parsed = self.parse_token_node(node.children[0].name) or self.parse_token_node(node.children[1].name)
            if parsed:
                _, linea, columna = parsed
            else:
                linea, columna = 0, 0
            self.report_error("TIPO_INCOMPATIBLE",
                            f"Operador lógico '{node.name}' requiere operandos bool",
                            linea, columna)
            self.annotate_node(node, tipo=None)
            return None
        
        # Calcular valor si ambos operandos tienen valores
        result_value = None
        if left_value is not None and right_value is not None:
            try:
                left_bool = left_value in ('true', True, 1, '1')
                right_bool = right_value in ('true', True, 1, '1')
                
                if node.name == '&&':
                    result_value = left_bool and right_bool
                elif node.name == '||':
                    result_value = left_bool or right_bool
                
                result_value = 'true' if result_value else 'false'
            except (ValueError, TypeError):
                result_value = None
        
        self.annotate_node(node, tipo='bool', valor=result_value)
        return 'bool'
    
    def analyze_negation(self, node):
        """Analiza negación lógica: !"""
        if len(node.children) < 1:
            return None
        
        expr_type = self.analyze_expression(node.children[0])
        
        # Obtener valor del hijo si está disponible
        expr_annotations = self.get_node_annotation(node.children[0])
        expr_value = expr_annotations.get('value')
        
        if not expr_type:
            self.annotate_node(node, tipo=None)
            return None
        
        if expr_type != 'bool':
            parsed = self.parse_token_node(node.children[0].name)
            if parsed:
                _, linea, columna = parsed
            else:
                linea, columna = 0, 0
            self.report_error("TIPO_INCOMPATIBLE",
                            f"Operador '!' requiere operando bool, se encontró {expr_type}",
                            linea, columna)
            self.annotate_node(node, tipo=None)
            return None
        
        # Calcular valor si el operando tiene valor
        result_value = None
        if expr_value is not None:
            try:
                expr_bool = expr_value in ('true', True, 1, '1')
                result_value = 'false' if expr_bool else 'true'
            except (ValueError, TypeError):
                result_value = None
        
        self.annotate_node(node, tipo='bool', valor=result_value)
        return 'bool'
    
    def analyze_assignment(self, node):
        """Analiza asignación: ="""
        if len(node.children) < 2:
            return None
        
        # Hijo 0: identificador destino
        # Hijo 1: expresión fuente
        id_node = node.children[0]
        expr_node = node.children[1]
        
        parsed_id = self.parse_token_node(id_node.name)
        if not parsed_id:
            return None
        
        id_lexema, id_linea, id_columna = parsed_id
        
        # Verificar que la variable esté declarada (registrar aparición)
        entry, error_msg = self.symbol_table.lookup(id_lexema, id_linea, id_columna)
        if not entry:
            self.report_error("VARIABLE_NO_DECLARADA", error_msg, id_linea, id_columna, fatal=False)
            return None
        
        # Analizar tipo de la expresión
        expr_type = self.analyze_expression(expr_node)
        
        # Obtener valor de la expresión si está disponible
        expr_annotations = self.get_node_annotation(expr_node)
        expr_value = expr_annotations.get('value')
        
        if not expr_type:
            self.annotate_node(node, tipo=None)
            return None
        
        # Verificar compatibilidad
        es_compatible, mensaje = self.check_type_compatibility(entry.tipo, expr_type, id_linea, id_columna)
        if not es_compatible:
            self.report_error("TIPO_INCOMPATIBLE", mensaje, id_linea, id_columna)
            self.annotate_node(node, tipo=None)
            return None
        
        # El valor de la asignación es el valor de la expresión
        self.annotate_node(node, tipo=entry.tipo, valor=expr_value)
        return entry.tipo
    
    def analyze_declaracion(self, node):
        """Analiza una declaración de variables."""
        if not node or node.name != "Declaración":
            return
        
        if not node.children:
            return
        
        # El primer hijo es el tipo
        tipo_node = node.children[0]
        parsed_tipo = self.parse_token_node(tipo_node.name)
        if not parsed_tipo:
            return
        
        tipo_lexema, _, _ = parsed_tipo
        if tipo_lexema not in ('int', 'float', 'bool'):
            return
        
        # Los siguientes hijos son identificadores o asignaciones
        for i in range(1, len(node.children)):
            child = node.children[i]
            
            # Puede ser un identificador directo o una asignación
            if child.name == '=':
                # Es una asignación: el primer hijo es el identificador
                if child.children and len(child.children) > 0:
                    id_node = child.children[0]
                    parsed_id = self.parse_token_node(id_node.name)
                    if parsed_id:
                        id_lexema, id_linea, id_columna = parsed_id
                        # Declarar la variable
                        success, error_msg = self.symbol_table.declare(id_lexema, tipo_lexema, id_linea, id_columna)
                        if not success:
                            self.report_error("DUPLICIDAD_DECLARACION", error_msg, id_linea, id_columna)
                        else:
                            # Analizar la expresión de asignación
                            if len(child.children) > 1:
                                expr_node = child.children[1]
                                expr_type = self.analyze_expression(expr_node)
                                if expr_type:
                                    es_compatible, mensaje = self.check_type_compatibility(
                                        tipo_lexema, expr_type, id_linea, id_columna)
                                    if not es_compatible:
                                        self.report_error("TIPO_INCOMPATIBLE", mensaje, id_linea, id_columna)
            else:
                # Es un identificador sin asignación
                parsed_id = self.parse_token_node(child.name)
                if parsed_id:
                    id_lexema, id_linea, id_columna = parsed_id
                    success, error_msg = self.symbol_table.declare(id_lexema, tipo_lexema, id_linea, id_columna)
                    if not success:
                        self.report_error("DUPLICIDAD_DECLARACION", error_msg, id_linea, id_columna)
    
    def analyze_statement(self, node):
        """Analiza una sentencia."""
        if not node:
            return
        
        node_name = node.name
        
        # Declaración
        if node_name == "Declaración":
            self.analyze_declaracion(node)
            return
        
        # Asignación
        parsed = self.parse_token_node(node_name)
        if parsed and parsed[0] == '=':
            tipo = self.analyze_assignment(node)
            # El tipo y valor ya están anotados en analyze_assignment
            return
        
        # Incremento/Decremento (ya expandidos por el parser)
        if "Expansión de" in node_name:
            # El parser ya expandió ++/-- como asignación
            if node.children:
                self.analyze_statement(node.children[0])
                # Propagar tipo y valor de la asignación al nodo de expansión
                if node.children[0].children:
                    assign_node = node.children[0]
                    assign_annotations = self.get_node_annotation(assign_node)
                    assign_tipo = assign_annotations.get('type')
                    assign_valor = assign_annotations.get('value')
                    if assign_tipo:
                        self.annotate_node(node, tipo=assign_tipo, valor=assign_valor)
            return
        
        # if
        parsed = self.parse_token_node(node_name)
        if parsed and parsed[0] == 'if':
            self.analyze_if_statement(node)
            return
        
        # while
        if parsed and parsed[0] == 'while':
            self.analyze_while_statement(node)
            return
        
        # do
        if parsed and parsed[0] == 'do':
            self.analyze_do_while_statement(node)
            return
        
        # cin/cout (no requieren verificación de tipos especial)
        if parsed and parsed[0] in ('cin', 'cout'):
            self.analyze_io_statement(node)
            return
        
        # Recursivamente analizar hijos y propagar tipo y valor del último hijo válido
        ultimo_tipo = None
        ultimo_valor = None
        tiene_error = False
        
        for child in node.children:
            # Analizar el hijo como sentencia
            self.analyze_statement(child)
            # Intentar obtener tipo y valor del hijo
            child_annotations = self.get_node_annotation(child)
            child_tipo = child_annotations.get('type')
            if child_tipo:
                ultimo_tipo = child_tipo
                if 'value' in child_annotations and child_annotations['value'] is not None:
                    ultimo_valor = child_annotations['value']
            elif child_tipo is None and 'type' in child_annotations:
                tiene_error = True
        
        # Propagar tipo y valor al nodo padre
        if tiene_error:
            self.annotate_node(node, tipo=None)
        elif ultimo_tipo:
            self.annotate_node(node, tipo=ultimo_tipo, valor=ultimo_valor)
    
    def analyze_if_statement(self, node):
        """Analiza sentencia if."""
        # Buscar nodo "Condición"
        cond_node = None
        for child in node.children:
            if child.name == "Condición":
                cond_node = child
                break
        
        cond_tipo = None
        cond_valor = None
        if cond_node and cond_node.children:
            cond_tipo = self.analyze_expression(cond_node.children[0])
            if cond_tipo:
                cond_annotations = self.get_node_annotation(cond_node.children[0])
                cond_valor = cond_annotations.get('value')
                # Propagar tipo y valor al nodo "Condición"
                self.annotate_node(cond_node, tipo=cond_tipo, valor=cond_valor)
            if cond_tipo and cond_tipo != 'bool':
                parsed = self.parse_token_node(node.name)
                if parsed:
                    _, linea, columna = parsed
                    self.report_error("TIPO_INCOMPATIBLE",
                                    f"Condición de if debe ser bool, se encontró {cond_tipo}",
                                    linea, columna)
        
        # Entrar en ámbito para bloque then
        self.symbol_table.enter_scope("if_then")
        for child in node.children:
            if child.name == "then":
                # Analizar sentencias del bloque then
                ultimo_tipo_then = None
                ultimo_valor_then = None
                for stmt in child.children:
                    self.analyze_statement(stmt)
                    stmt_annotations = self.get_node_annotation(stmt)
                    stmt_tipo = stmt_annotations.get('type')
                    if stmt_tipo:
                        ultimo_tipo_then = stmt_tipo
                        if 'value' in stmt_annotations and stmt_annotations['value'] is not None:
                            ultimo_valor_then = stmt_annotations['value']
                # Propagar tipo y valor al nodo "then"
                if ultimo_tipo_then:
                    self.annotate_node(child, tipo=ultimo_tipo_then, valor=ultimo_valor_then)
        self.symbol_table.exit_scope()
        
        # Entrar en ámbito para bloque else (si existe)
        for child in node.children:
            if child.name == "else":
                self.symbol_table.enter_scope("if_else")
                # Analizar sentencias del bloque else
                ultimo_tipo_else = None
                ultimo_valor_else = None
                for stmt in child.children:
                    self.analyze_statement(stmt)
                    stmt_annotations = self.get_node_annotation(stmt)
                    stmt_tipo = stmt_annotations.get('type')
                    if stmt_tipo:
                        ultimo_tipo_else = stmt_tipo
                        if 'value' in stmt_annotations and stmt_annotations['value'] is not None:
                            ultimo_valor_else = stmt_annotations['value']
                # Propagar tipo y valor al nodo "else"
                if ultimo_tipo_else:
                    self.annotate_node(child, tipo=ultimo_tipo_else, valor=ultimo_valor_else)
                self.symbol_table.exit_scope()
                break
        
        # Propagar tipo y valor de la condición al nodo if
        if cond_tipo:
            self.annotate_node(node, tipo=cond_tipo, valor=cond_valor)
    
    def analyze_while_statement(self, node):
        """Analiza sentencia while."""
        # Buscar nodo "Condición"
        cond_node = None
        for child in node.children:
            if child.name == "Condición":
                cond_node = child
                break
        
        cond_tipo = None
        cond_valor = None
        if cond_node and cond_node.children:
            cond_tipo = self.analyze_expression(cond_node.children[0])
            if cond_tipo:
                cond_annotations = self.get_node_annotation(cond_node.children[0])
                cond_valor = cond_annotations.get('value')
                # Propagar tipo y valor al nodo "Condición"
                self.annotate_node(cond_node, tipo=cond_tipo, valor=cond_valor)
            if cond_tipo and cond_tipo != 'bool':
                parsed = self.parse_token_node(node.name)
                if parsed:
                    _, linea, columna = parsed
                    self.report_error("TIPO_INCOMPATIBLE",
                                    f"Condición de while debe ser bool, se encontró {cond_tipo}",
                                    linea, columna)
        
        # Entrar en ámbito para bloque
        self.symbol_table.enter_scope("while")
        for child in node.children:
            if child.name == "Cuerpo":
                # Analizar sentencias del bloque
                ultimo_tipo_cuerpo = None
                ultimo_valor_cuerpo = None
                for stmt in child.children:
                    self.analyze_statement(stmt)
                    stmt_annotations = self.get_node_annotation(stmt)
                    stmt_tipo = stmt_annotations.get('type')
                    if stmt_tipo:
                        ultimo_tipo_cuerpo = stmt_tipo
                        if 'value' in stmt_annotations and stmt_annotations['value'] is not None:
                            ultimo_valor_cuerpo = stmt_annotations['value']
                # Propagar tipo y valor al nodo "Cuerpo"
                if ultimo_tipo_cuerpo:
                    self.annotate_node(child, tipo=ultimo_tipo_cuerpo, valor=ultimo_valor_cuerpo)
        self.symbol_table.exit_scope()
        
        # Propagar tipo y valor de la condición al nodo while
        if cond_tipo:
            self.annotate_node(node, tipo=cond_tipo, valor=cond_valor)
    
    def analyze_do_while_statement(self, node):
        """Analiza sentencia do-while."""
        # Entrar en ámbito para bloque
        self.symbol_table.enter_scope("do_while")
        for child in node.children:
            if child.name == "Cuerpo":
                # Analizar sentencias del bloque
                ultimo_tipo_cuerpo = None
                ultimo_valor_cuerpo = None
                for stmt in child.children:
                    self.analyze_statement(stmt)
                    stmt_annotations = self.get_node_annotation(stmt)
                    stmt_tipo = stmt_annotations.get('type')
                    if stmt_tipo:
                        ultimo_tipo_cuerpo = stmt_tipo
                        if 'value' in stmt_annotations and stmt_annotations['value'] is not None:
                            ultimo_valor_cuerpo = stmt_annotations['value']
                # Propagar tipo y valor al nodo "Cuerpo"
                if ultimo_tipo_cuerpo:
                    self.annotate_node(child, tipo=ultimo_tipo_cuerpo, valor=ultimo_valor_cuerpo)
        self.symbol_table.exit_scope()
        
        # Analizar condición
        cond_node = None
        for child in node.children:
            if child.name == "Condición":
                cond_node = child
                break
        
        cond_tipo = None
        cond_valor = None
        if cond_node and cond_node.children:
            cond_tipo = self.analyze_expression(cond_node.children[0])
            if cond_tipo:
                cond_annotations = self.get_node_annotation(cond_node.children[0])
                cond_valor = cond_annotations.get('value')
                # Propagar tipo y valor al nodo "Condición"
                self.annotate_node(cond_node, tipo=cond_tipo, valor=cond_valor)
            if cond_tipo and cond_tipo != 'bool':
                parsed = self.parse_token_node(node.name)
                if parsed:
                    _, linea, columna = parsed
                    self.report_error("TIPO_INCOMPATIBLE",
                                    f"Condición de do-while debe ser bool, se encontró {cond_tipo}",
                                    linea, columna)
        
        # Propagar tipo y valor de la condición al nodo do-while
        if cond_tipo:
            self.annotate_node(node, tipo=cond_tipo, valor=cond_valor)
    
    def analyze_io_statement(self, node):
        """Analiza sentencias de entrada/salida (cin/cout)."""
        parsed = self.parse_token_node(node.name)
        if not parsed:
            return
        
        lexema, _, _ = parsed
        
        if lexema == 'cin':
            # cin >> id: verificar que id esté declarado
            if node.children:
                id_node = node.children[0]
                parsed_id = self.parse_token_node(id_node.name)
                if parsed_id:
                    id_lexema, id_linea, id_columna = parsed_id
                    entry, error_msg = self.symbol_table.lookup(id_lexema, id_linea, id_columna)
                    if not entry:
                        self.report_error("VARIABLE_NO_DECLARADA", error_msg, id_linea, id_columna)
                    else:
                        # Propagar tipo de la variable al nodo cin
                        self.annotate_node(node, tipo=entry.tipo)
        elif lexema == 'cout':
            # cout << expr: analizar expresión y propagar tipo y valor
            if node.children:
                expr_node = node.children[0]
                expr_tipo = self.analyze_expression(expr_node)
                if expr_tipo:
                    expr_annotations = self.get_node_annotation(expr_node)
                    expr_valor = expr_annotations.get('value')
                    # Propagar tipo y valor de la expresión al nodo cout
                    self.annotate_node(node, tipo=expr_tipo, valor=expr_valor)
    
    def analyze(self, ast_root):
        """
        Analiza el AST completo.
        Retorna (ast_anotado_dict, tabla_simbolos_dict, errores_list).
        """
        if not ast_root:
            self.report_error("AST_INVALIDO", "El AST está vacío o es None", 0, 0, fatal=True)
            return self._build_results()
        
        if ast_root.name != "Programa":
            self.report_error("AST_INVALIDO", f"Se esperaba nodo 'Programa', se encontró '{ast_root.name}'", 0, 0, fatal=True)
            return self._build_results()
        
        # Analizar el programa
        for child in ast_root.children:
            if self.should_stop:
                break
            
            # Saltar tokens de formato (main, {, })
            parsed = self.parse_token_node(child.name)
            if parsed and parsed[0] in ('main', '{', '}'):
                continue
            
            self.analyze_statement(child)
        
        return self._build_results()
    
    def _build_results(self):
        """Construye los resultados del análisis."""
        # Construir diccionario de tabla de símbolos
        tabla_dict = []
        for entry in self.symbol_table.get_all_entries():
            tabla_dict.append({
                "nombre": entry.nombre,
                "tipo": entry.tipo,
                "ambito": entry.ambito,
                "direccion": entry.get_ubicaciones_str()  # Usar ubicaciones en lugar de dirección numérica
            })
        
        # Construir lista de errores
        errores_list = [error.to_dict() for error in self.errors]
        
        return {
            "annotations": self.annotations,
            "tabla_simbolos": tabla_dict,
            "errores": errores_list
        }


def ast_to_dict_annotated(ast_node, annotations, parent_id=None):
    """
    Convierte el AST a diccionario con anotaciones.
    """
    if not ast_node:
        return None
    
    node_id = id(ast_node)
    node_annotations = annotations.get(node_id, {})
    
    # Extraer información de ubicación si es un token
    loc = None
    parsed = None
    if " (" in ast_node.name and ")" in ast_node.name:
        parsed = ast_node.name.rsplit(" (", 1)
        if len(parsed) == 2:
            loc_part = parsed[1].rstrip(")")
            if ":" in loc_part:
                try:
                    linea, columna = map(int, loc_part.split(":"))
                    loc = f"{linea}:{columna}"
                except ValueError:
                    pass
    
    result = {
        "name": ast_node.name,
        "children": []
    }
    
    if node_annotations.get('type'):
        result["type"] = node_annotations['type']
    if node_annotations.get('value') is not None:
        result["value"] = node_annotations['value']
    if loc:
        result["loc"] = loc
    
    # Procesar hijos
    for child in ast_node.children:
        child_dict = ast_to_dict_annotated(child, annotations, node_id)
        if child_dict:
            result["children"].append(child_dict)
    
    return result


def get_semantic_results(ast_root=None):
    """
    Función principal que realiza el análisis semántico.
    
    Args:
        ast_root: ASTNode opcional. Si es None, se obtiene desde syntactic.get_ast()
    
    Returns:
        (ast_anotado_dict, tabla_simbolos_dict, errores_list, annotations_dict, ast_root_node)
    """
    # Si no se proporciona AST, obtenerlo desde syntactic
    if ast_root is None:
        try:
            from phases import syntactic
            ast_root, parser_errors = syntactic.get_ast()
            if parser_errors:
                print(f"Advertencia: El parser reportó {len(parser_errors)} errores sintácticos")
        except Exception as e:
            print(f"Error obteniendo AST: {e}")
            return None, [], [], {}, None
    
    # Crear y ejecutar analizador semántico
    analyzer = SemanticAnalyzer()
    results = analyzer.analyze(ast_root)
    
    # Construir AST anotado como diccionario
    ast_anotado_dict = ast_to_dict_annotated(ast_root, results["annotations"])
    
    # Generar archivos
    _write_symbol_table_file(results["tabla_simbolos"])
    _write_errors_file(results["errores"])
    _write_annotated_ast_file(ast_anotado_dict)
    
    return ast_anotado_dict, results["tabla_simbolos"], results["errores"], results["annotations"], ast_root


def _write_symbol_table_file(tabla_simbolos):
    """Escribe la tabla de símbolos a tabla_simbolos.txt"""
    try:
        with open("tabla_simbolos.txt", "w", encoding="utf-8") as f:
            f.write("nombre\ttipo\tambito\tdireccion\n")
            for entry in tabla_simbolos:
                f.write(f"{entry['nombre']}\t{entry['tipo']}\t{entry['ambito']}\t{entry['direccion']}\n")
        print(f"Tabla de símbolos escrita: {len(tabla_simbolos)} entradas")
    except Exception as e:
        print(f"Error escribiendo tabla de símbolos: {e}")


def _write_errors_file(errores):
    """Escribe los errores semánticos a errores_semanticos.txt"""
    try:
        with open("errores_semanticos.txt", "w", encoding="utf-8") as f:
            if not errores:
                f.write("Sin errores semánticos.\n")
            else:
                for error in errores:
                    fatal_str = "FATAL" if error.get('fatal', False) else ""
                    f.write(f"{error['tipo']}\t{error['descripcion']}\t{error['linea']}:{error['columna']}\t{fatal_str}\n".strip() + "\n")
        print(f"Archivo de errores escrito: {len(errores)} errores")
    except Exception as e:
        print(f"Error escribiendo archivo de errores: {e}")


def _write_annotated_ast_file(ast_anotado_dict):
    """Escribe el AST anotado a ast_anotado.json"""
    try:
        with open("ast_anotado.json", "w", encoding="utf-8") as f:
            json.dump(ast_anotado_dict, f, indent=2, ensure_ascii=False)
        print("AST anotado escrito a ast_anotado.json")
    except Exception as e:
        print(f"Error escribiendo AST anotado: {e}")


if __name__ == "__main__":
    # Prueba del analizador semántico
    print("Ejecutando análisis semántico...")
    ast_anotado, tabla, errores = get_semantic_results()
    
    print(f"\nResultados:")
    print(f"- Entradas en tabla de símbolos: {len(tabla)}")
    print(f"- Errores encontrados: {len(errores)}")
    
    if errores:
        print("\nErrores:")
        for error in errores:
            print(f"  {error['tipo']}: {error['descripcion']} ({error['linea']}:{error['columna']})")
    
    print("\nArchivos generados:")
    print("  - tabla_simbolos.txt")
    print("  - errores_semanticos.txt")
    print("  - ast_anotado.json")

