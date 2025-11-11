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
                    # Convertir el lexema a su valor numérico o booleano correspondiente
                    valor_literal = None
                    if tipo == 'int':
                        try:
                            valor_literal = int(lexema)
                        except ValueError:
                            valor_literal = None
                    elif tipo == 'float':
                        try:
                            valor_literal = float(lexema)
                        except ValueError:
                            valor_literal = None
                    elif tipo == 'bool':
                        valor_literal = True if lexema == 'true' else False
                    
                    self.annotate_node(node, tipo=tipo, valor=valor_literal)
                    return tipo
                
                # Es un identificador
                entry, error_msg = self.symbol_table.lookup(lexema, linea, columna)
                if entry:
                    # Obtener valor de la variable si está disponible
                    valor_variable = entry.get_valor()
                    # Si la variable no tiene valor asignado, no es un error fatal,
                    # pero puede causar problemas en operaciones aritméticas
                    # (se reportará cuando se intente usar en una operación)
                    self.annotate_node(node, tipo=entry.tipo, valor=valor_variable)
                    return entry.tipo
                else:
                    self.report_error("VARIABLE_NO_DECLARADA", error_msg, linea, columna, fatal=False)
                    return None
        else:
            # El nodo no tiene formato de token. Verificar si es un literal sin formato
            # (por ejemplo, "1" creado directamente como ASTNode("1"))
            tipo_literal = self.infer_type_from_literal(node_name)
            if tipo_literal:
                # Es un literal sin formato de token (ej: "1", "2.5", "true")
                valor_literal = None
                if tipo_literal == 'int':
                    try:
                        valor_literal = int(node_name)
                    except ValueError:
                        valor_literal = None
                elif tipo_literal == 'float':
                    try:
                        valor_literal = float(node_name)
                    except ValueError:
                        valor_literal = None
                elif tipo_literal == 'bool':
                    valor_literal = True if node_name == 'true' else False
                
                self.annotate_node(node, tipo=tipo_literal, valor=valor_literal)
                return tipo_literal
        
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
        
        # Verificar si algún operando no tiene valor (variable sin inicializar)
        # NOTA: Esto es un error de ejecución, no semántico, así que no reportamos error.
        # Solo anotamos el nodo sin valor y continuamos el análisis.
        if left_value is None or right_value is None:
            # No podemos calcular el resultado, pero el tipo puede inferirse
            # Anotar el nodo con el tipo pero sin valor (no es error semántico)
            self.annotate_node(node, tipo=result_type, valor=None)
            return result_type
        
        # Ambos operandos tienen valores, calcular el resultado
        if left_value is not None and right_value is not None:
            try:
                # Convertir valores a números, manejando tanto números como strings
                # Para left_value
                if isinstance(left_value, (int, float)):
                    left_num = left_value
                elif isinstance(left_value, str):
                    # Es un string, intentar convertir a número
                    try:
                        if '.' in left_value or 'e' in left_value.lower() or 'E' in left_value:
                            left_num = float(left_value)
                        else:
                            left_num = int(left_value)
                    except ValueError:
                        left_num = float(left_value) if result_type == 'float' else int(left_value)
                else:
                    # Otro tipo, convertir directamente
                    left_num = float(left_value) if result_type == 'float' else int(left_value)
                
                # Para right_value
                if isinstance(right_value, (int, float)):
                    right_num = right_value
                elif isinstance(right_value, str):
                    # Es un string, intentar convertir a número
                    try:
                        if '.' in right_value or 'e' in right_value.lower() or 'E' in right_value:
                            right_num = float(right_value)
                        else:
                            right_num = int(right_value)
                    except ValueError:
                        right_num = float(right_value) if result_type == 'float' else int(right_value)
                else:
                    # Otro tipo, convertir directamente
                    right_num = float(right_value) if result_type == 'float' else int(right_value)
                
                # Realizar la operación
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
                
                # Formatear resultado según el tipo
                if result_value is not None:
                    if result_type == 'int':
                        result_value = int(result_value)
                    else:
                        result_value = float(result_value)
            except (ValueError, TypeError, AttributeError):
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
        
        # Verificar que la variable esté declarada
        entry, error_msg = self.symbol_table.lookup(id_lexema, id_linea, id_columna)
        if not entry:
            self.report_error("VARIABLE_NO_DECLARADA", error_msg, id_linea, id_columna, fatal=False)
            return None
        
        # Obtener el valor actual de la variable ANTES de analizar la expresión
        # Esto es importante para operaciones como a = a + 1, donde el 'a' de la derecha
        # debe usar el valor ANTES de la asignación
        valor_actual_variable = entry.get_valor()
        
        # Anotar el identificador del lado izquierdo con su tipo y valor actual
        # (antes de analizar la expresión, para que se muestre en el árbol)
        self.annotate_node(id_node, tipo=entry.tipo, valor=valor_actual_variable)
        
        # Analizar tipo de la expresión (esto puede usar el valor actual de la variable)
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
        
        # Actualizar el valor de la variable en la tabla de símbolos SOLO DESPUÉS de calcular la expresión
        # Esto asegura que cuando analizamos 'a' en 'a + 1', obtenemos el valor anterior
        if expr_value is not None:
            entry.set_valor(expr_value)
        
        # El valor de la asignación es el valor de la expresión (el nuevo valor de la variable)
        # Este es el valor POST-operación que se asigna a la variable
        self.annotate_node(node, tipo=entry.tipo, valor=expr_value)
        
        # Retornar el tipo de la variable (que es el tipo de la asignación)
        return entry.tipo
    
    def analyze_compound_assignment(self, node):
        """Analiza asignación compuesta: +=, -=, *=, /=, %="""
        if len(node.children) < 2:
            return None
        
        # El nombre del nodo contiene el operador (ej: "+= (5:10)")
        parsed_op = self.parse_token_node(node.name)
        if not parsed_op:
            return None
        
        op_lexema, op_linea, op_columna = parsed_op
        if op_lexema not in ('+=', '-=', '*=', '/=', '%='):
            return None
        
        # Hijo 0: identificador destino
        # Hijo 1: expresión fuente
        id_node = node.children[0]
        expr_node = node.children[1]
        
        parsed_id = self.parse_token_node(id_node.name)
        if not parsed_id:
            return None
        
        id_lexema, id_linea, id_columna = parsed_id
        
        # Verificar que la variable esté declarada (registrar primera aparición)
        entry, error_msg = self.symbol_table.lookup(id_lexema, id_linea, id_columna)
        if not entry:
            self.report_error("VARIABLE_NO_DECLARADA", error_msg, id_linea, id_columna, fatal=False)
            return None
        
        # Obtener el valor actual de la variable ANTES de analizar la expresión
        # (porque la expresión puede usar la variable y necesitamos su valor anterior)
        valor_actual = entry.get_valor()
        
        # Analizar tipo de la expresión (esto puede registrar más apariciones de la variable si se usa en la expresión)
        expr_type = self.analyze_expression(expr_node)
        
        # Para asignaciones compuestas, la variable se usa dos veces: una vez como destino y otra en la expresión implícita
        # Por ejemplo: a += b es semánticamente a = a + b, donde 'a' aparece dos veces
        # Ya registramos una aparición arriba (la del identificador), ahora registramos otra en la misma línea
        if id_linea:
            # Verificar cuántas veces aparece esta línea
            lineas_en_esta_linea = [l for l, c in entry.ubicaciones if l == id_linea]
            # Si solo aparece una vez, agregar otra aparición (la segunda 'a' en 'a = a + b')
            if len(lineas_en_esta_linea) == 1:
                entry.agregar_ubicacion(id_linea, -1)  # Usar columna -1 para la segunda aparición
        
        # Obtener valor de la expresión si está disponible
        expr_annotations = self.get_node_annotation(expr_node)
        expr_value = expr_annotations.get('value')
        
        if not expr_type:
            self.annotate_node(node, tipo=None)
            return None
        
        # Verificar compatibilidad de tipos para la operación
        # La expresión debe ser compatible con el tipo de la variable
        es_compatible, mensaje = self.check_type_compatibility(entry.tipo, expr_type, id_linea, id_columna)
        if not es_compatible:
            self.report_error("TIPO_INCOMPATIBLE", 
                            f"Incompatibilidad de tipos en asignación compuesta '{op_lexema}': {mensaje}", 
                            id_linea, id_columna)
            self.annotate_node(node, tipo=None)
            return None
        
        # Calcular el nuevo valor si ambos valores están disponibles
        nuevo_valor = None
        if valor_actual is not None and expr_value is not None:
            try:
                # Convertir valores a números
                if entry.tipo == 'float' or expr_type == 'float':
                    val_actual = float(valor_actual)
                    val_expr = float(expr_value)
                    resultado_float = True
                else:
                    val_actual = int(valor_actual)
                    val_expr = int(expr_value)
                    resultado_float = False
                
                # Realizar la operación
                if op_lexema == '+=':
                    nuevo_valor = val_actual + val_expr
                elif op_lexema == '-=':
                    nuevo_valor = val_actual - val_expr
                elif op_lexema == '*=':
                    nuevo_valor = val_actual * val_expr
                elif op_lexema == '/=':
                    if val_expr == 0:
                        nuevo_valor = None  # División por cero
                    else:
                        nuevo_valor = val_actual / val_expr
                        resultado_float = True  # La división siempre produce float
                elif op_lexema == '%=':
                    nuevo_valor = val_actual % val_expr
                
                # Formatear resultado según el tipo
                if nuevo_valor is not None:
                    if resultado_float or entry.tipo == 'float':
                        nuevo_valor = float(nuevo_valor)
                    else:
                        nuevo_valor = int(nuevo_valor)
            except (ValueError, TypeError):
                nuevo_valor = None
        
        # Actualizar el valor de la variable en la tabla de símbolos
        if nuevo_valor is not None:
            entry.set_valor(nuevo_valor)
        
        # Anotar el nodo con el tipo y valor
        self.annotate_node(node, tipo=entry.tipo, valor=nuevo_valor)
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
                                    # Obtener valor de la expresión
                                    expr_annotations = self.get_node_annotation(expr_node)
                                    expr_value = expr_annotations.get('value')
                                    es_compatible, mensaje = self.check_type_compatibility(
                                        tipo_lexema, expr_type, id_linea, id_columna)
                                    if not es_compatible:
                                        self.report_error("TIPO_INCOMPATIBLE", mensaje, id_linea, id_columna)
                                        # Marcar el nodo de asignación con ERROR
                                        self.annotate_node(child, tipo=None)
                                    else:
                                        # Actualizar valor de la variable solo si no hay error
                                        if expr_value is not None:
                                            entry.set_valor(expr_value)
                                        # Anotar el nodo de asignación con el tipo correcto
                                        self.annotate_node(child, tipo=tipo_lexema, valor=expr_value)
                                else:
                                    # Error en la expresión, marcar asignación con ERROR
                                    self.annotate_node(child, tipo=None)
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
        
        # Asignación simple (=)
        parsed = self.parse_token_node(node_name)
        if parsed and parsed[0] == '=':
            tipo = self.analyze_assignment(node)
            # El tipo y valor ya están anotados en analyze_assignment
            return
        
        # Operadores de asignación compuestos (+=, -=, *=, /=, %=)
        if parsed and parsed[0] in ('+=', '-=', '*=', '/=', '%='):
            tipo = self.analyze_compound_assignment(node)
            # El tipo y valor ya están anotados en analyze_compound_assignment
            return
        
        # Incremento/Decremento (ya expandidos por el parser)
        if "Expansión de" in node_name:
            # El parser ya expandió ++/-- como asignación (a = a + 1)
            # Obtener la línea y el identificador ANTES de analizar
            parsed = None
            id_lexema = None
            linea_op = None
            id_columna = None
            
            # Intentar obtener información del nodo de expansión o del primer hijo
            if node.children and node.children[0].children:
                id_node = node.children[0].children[0]  # El identificador de la izquierda en la asignación
                parsed = self.parse_token_node(id_node.name)
                if parsed:
                    id_lexema, linea_op, id_columna = parsed
            
            # Contar apariciones ANTES del análisis de esta operación ++/--
            apariciones_antes_operacion = 0
            if id_lexema and linea_op:
                entry, _ = self.symbol_table.lookup(id_lexema)
                if entry:
                    apariciones_antes_operacion = len([l for l, c in entry.ubicaciones if l == linea_op])
            
            # Analizar la asignación expandida directamente llamando a analyze_assignment
            # en lugar de analyze_statement para tener mejor control
            if node.children:
                assign_node = node.children[0]  # El nodo "="
                
                # Analizar la asignación directamente
                if assign_node and len(assign_node.children) >= 2:
                    # Llamar a analyze_assignment directamente para asegurar que se analice correctamente
                    self.analyze_assignment(assign_node)
                    
                    # Después del análisis, verificar cuántas apariciones NUEVAS se agregaron
                    if id_lexema and linea_op:
                        entry, _ = self.symbol_table.lookup(id_lexema)
                        if entry:
                            apariciones_despues_operacion = len([l for l, c in entry.ubicaciones if l == linea_op])
                            apariciones_agregadas = apariciones_despues_operacion - apariciones_antes_operacion
                            
                            # Para ++/--, necesitamos exactamente 2 apariciones NUEVAS en esta línea
                            # Si se agregaron menos de 2, agregar las que faltan
                            if apariciones_agregadas < 2:
                                faltantes = 2 - apariciones_agregadas
                                # Usar un contador único para las columnas de las apariciones adicionales
                                # Empezar desde -1000 para evitar conflictos con columnas reales
                                columna_base = -1000
                                for i in range(faltantes):
                                    entry.agregar_ubicacion(linea_op, columna_base - i)
                            # Si se agregaron más de 2 (no debería pasar), eliminar las extras
                            elif apariciones_agregadas > 2:
                                # Eliminar las apariciones extra que se agregaron en esta operación
                                ubicaciones_linea = [(l, c) for l, c in entry.ubicaciones if l == linea_op]
                                # Mantener solo las primeras N apariciones (donde N = apariciones_antes + 2)
                                ubicaciones_a_mantener = apariciones_antes_operacion + 2
                                if len(ubicaciones_linea) > ubicaciones_a_mantener:
                                    ubicaciones_a_eliminar = ubicaciones_linea[ubicaciones_a_mantener:]
                                    for ubicacion in ubicaciones_a_eliminar:
                                        if ubicacion in entry.ubicaciones:
                                            entry.ubicaciones.remove(ubicacion)
                    
                    # Obtener las anotaciones del nodo de asignación DESPUÉS de analizarlo
                    # analyze_assignment ya analizó completamente todos los hijos (incluyendo la expresión a + 1)
                    # y actualizó el valor en la tabla de símbolos
                    assign_annotations = self.get_node_annotation(assign_node)
                    assign_tipo = assign_annotations.get('type')
                    assign_valor = assign_annotations.get('value')
                    
                    # Si el nodo de asignación tiene un valor, ese ES el valor POST-operación
                    # porque analyze_assignment ya actualizó la tabla de símbolos y anotó el nodo con el nuevo valor
                    if assign_valor is None:
                        # Si no hay valor en las anotaciones, obtenerlo directamente de la expresión
                        if len(assign_node.children) >= 2:
                            expr_node = assign_node.children[1]
                            expr_annotations = self.get_node_annotation(expr_node)
                            assign_valor = expr_annotations.get('value')
                    
                    # Si aún no tenemos valor, obtenerlo de la tabla de símbolos
                    # (que debería tener el valor POST-operación después de analyze_assignment)
                    if assign_valor is None and id_lexema:
                        entry, _ = self.symbol_table.lookup(id_lexema)
                        if entry:
                            assign_valor = entry.get_valor()
                            if assign_tipo is None:
                                assign_tipo = entry.tipo
                    
                    # Si no tenemos tipo, obtenerlo de la entrada en la tabla de símbolos
                    if assign_tipo is None and id_lexema:
                        entry, _ = self.symbol_table.lookup(id_lexema)
                        if entry:
                            assign_tipo = entry.tipo
                    
                    # Propagar tipo y valor al nodo de expansión
                    # El valor debe ser el valor POST-operación (después del incremento/decremento)
                    # Este valor ya fue calculado por analyze_assignment y está en las anotaciones del nodo =
                    if assign_tipo:
                        # Anotar el nodo de expansión con el tipo y valor POST-operación
                        self.annotate_node(node, tipo=assign_tipo, valor=assign_valor)
                    else:
                        # Si hay error en la asignación, propagarlo
                        self.annotate_node(node, tipo=None)
                else:
                    # Si no hay hijos válidos, marcar como error
                    self.annotate_node(node, tipo=None)
            else:
                # Si no hay hijos, marcar como error
                self.annotate_node(node, tipo=None)
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
            valor_actual = entry.get_valor()
            valor_str = str(valor_actual) if valor_actual is not None else ""
            tabla_dict.append({
                "nombre": entry.nombre,
                "tipo": entry.tipo,
                "ambito": entry.ambito,
                "valor": valor_str,
                "direccion": entry.get_ubicaciones_str()  # Ubicaciones (solo líneas)
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
            f.write("nombre\ttipo\tambito\tvalor\tdireccion\n")
            for entry in tabla_simbolos:
                valor = entry.get('valor', '')
                f.write(f"{entry['nombre']}\t{entry['tipo']}\t{entry['ambito']}\t{valor}\t{entry['direccion']}\n")
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

