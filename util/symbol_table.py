# symbol_table.py
# Clase para manejar la tabla de símbolos con ámbitos

class SymbolEntry:
    """Entrada en la tabla de símbolos."""
    def __init__(self, nombre, tipo, ambito, direccion, linea, columna):
        self.nombre = nombre
        self.tipo = tipo  # 'int', 'float', 'bool'
        self.ambito = ambito  # 'global' o nombre del bloque
        self.direccion = direccion
        self.linea = linea
        self.columna = columna
        self.ubicaciones = [(linea, columna)]  # Lista de todas las apariciones (linea, columna)
    
    def agregar_ubicacion(self, linea, columna):
        """Agrega una nueva ubicación donde aparece la variable."""
        if (linea, columna) not in self.ubicaciones:
            self.ubicaciones.append((linea, columna))
    
    def agregar_linea(self, linea):
        """Agrega una línea donde aparece la variable (para duplicar apariciones como en ++/--)."""
        # Agregar la línea dos veces para representar las dos apariciones en 'a = a + 1'
        # Usamos columna -1 para indicar que son apariciones duplicadas en la misma línea
        self.ubicaciones.append((linea, -1))
        self.ubicaciones.append((linea, -1))
    
    def get_ubicaciones_str(self):
        """Retorna las ubicaciones como string: (5),(7) - solo líneas, sin columnas"""
        # Extraer todas las líneas (manteniendo duplicados para contar apariciones)
        lineas = [l for l, c in self.ubicaciones]
        # Ordenar y mantener todas las apariciones
        lineas_ordenadas = sorted(lineas)
        return ",".join([f"({l})" for l in lineas_ordenadas])
    
    def get_valor(self):
        """Retorna el valor actual de la variable si está disponible."""
        # Por ahora retornamos None, se puede extender para mantener valores
        return getattr(self, 'valor_actual', None)
    
    def set_valor(self, valor):
        """Establece el valor actual de la variable."""
        self.valor_actual = valor
    
    def __repr__(self):
        return f"SymbolEntry({self.nombre}, {self.tipo}, {self.ambito}, {self.direccion})"


class SymbolTable:
    """Tabla de símbolos con soporte para ámbitos anidados."""
    
    def __init__(self):
        self.scopes = [{}]  # Lista de diccionarios, cada uno representa un ámbito. Inicializar con ámbito global
        self.current_scope_name = "global"
        self.direccion_counter = 0
        self.entries = []  # Lista plana de todas las entradas para generar el archivo
    
    def enter_scope(self, scope_name=None):
        """Entra en un nuevo ámbito."""
        if scope_name is None:
            scope_name = f"bloque_{len(self.scopes)}"
        self.scopes.append({})
        self.current_scope_name = scope_name
    
    def exit_scope(self):
        """Sale del ámbito actual."""
        if len(self.scopes) > 1:  # No salir del ámbito global
            self.scopes.pop()
            # Restaurar nombre del ámbito anterior
            if len(self.scopes) > 0:
                self.current_scope_name = "global" if len(self.scopes) == 1 else f"bloque_{len(self.scopes)-1}"
    
    def declare(self, nombre, tipo, linea, columna):
        """
        Declara una variable en el ámbito actual.
        Retorna (True, None) si tiene éxito, (False, mensaje_error) si hay duplicidad.
        """
        # Verificar duplicidad en el ámbito actual
        current_scope = self.scopes[-1]
        if nombre in current_scope:
            return False, f"Variable '{nombre}' ya declarada en este ámbito"
        
        # Crear entrada
        direccion = self.direccion_counter
        self.direccion_counter += 1
        
        entry = SymbolEntry(nombre, tipo, self.current_scope_name, direccion, linea, columna)
        current_scope[nombre] = entry
        self.entries.append(entry)
        
        return True, None
    
    def lookup(self, nombre, linea=None, columna=None):
        """
        Busca una variable desde el ámbito actual hacia arriba.
        Retorna (entry, None) si se encuentra, (None, mensaje_error) si no.
        Si se proporcionan linea y columna, registra la aparición de la variable.
        """
        # Buscar desde el ámbito actual hacia arriba
        for scope in reversed(self.scopes):
            if nombre in scope:
                entry = scope[nombre]
                # Si se proporcionan línea y columna, registrar la aparición
                if linea is not None and columna is not None:
                    entry.agregar_ubicacion(linea, columna)
                return entry, None
        
        return None, f"Variable '{nombre}' no declarada"
    
    def get_all_entries(self):
        """Retorna todas las entradas de la tabla de símbolos."""
        return self.entries
    
    def get_current_scope(self):
        """Retorna el nombre del ámbito actual."""
        return self.current_scope_name


