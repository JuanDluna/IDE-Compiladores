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


    def to_dict(self):
        """Convierte el árbol a un diccionario (para debug o visualizadores externos)."""
        return {
            "name": self.name,
            "children": [child.to_dict() for child in self.children] if self.children else []
        }
