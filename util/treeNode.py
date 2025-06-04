# treeNodes.py

class ASTNode:
    def __init__(self, name, children=None):
        self.name = name
        self.children = children if children is not None else []

    def add_child(self, node):
        """Agrega un nodo hijo a este nodo."""
        self.children.append(node)

    def is_leaf(self):
        """Verifica si el nodo es hoja (no tiene hijos)."""
        return len(self.children) == 0

    def pretty_print(self, indent=0, is_last=True):
        """
        Retorna una representación jerárquica en texto del árbol.
        Usa símbolos 📂 para nodos intermedios y 📄 para hojas.
        """
        prefix = "    " * (indent - 1) + ("└── " if is_last and indent > 0 else "├── " if indent > 0 else "")
        icon = "📄" if self.is_leaf() else "📂"
        result = f"{prefix}{icon} {self.name}\n"
        
        for i, child in enumerate(self.children):
            is_last_child = i == len(self.children) - 1
            result += child.pretty_print(indent + 1, is_last_child)
        
        return result

    def to_dict(self):
        """Convierte el árbol a un diccionario (para debug o visualizadores externos)."""
        return {
            "name": self.name,
            "children": [child.to_dict() for child in self.children] if self.children else []
        }
