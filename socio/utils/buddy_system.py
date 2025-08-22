"""
* Integrantes:
*   + Aparicio Martínez Francisco
*   + Salinas Gil Diego
*
* Objetivo:
*   Implementación del algoritmo Buddy System para gestión de memoria
*
* Descripción:
*   Este sistema gestiona la memoria dividiéndola en bloques de tamaño potencia de 2
*   y permite la asignación y liberación de procesos de manera eficiente
*
"""

from typing import Optional, Iterator
from strategy.system import MemoryAllocationStrategy

class Node:
    def __init__(self, size, parent=None, is_allocated=False, pid=-1):
        """
        Inicializa un nodo de memoria
        
        Args:
            size (int): Tamaño del bloque de memoria
            parent (Node, optional): Nodo padre. Defaults to None.
            is_allocated (bool, optional): Indica si el bloque está asignado. Defaults to False.
            pid (int, optional): ID del proceso asignado. Defaults to -1.
                - -1: Sin proceso asignado (libre)
                - >=1: Con proceso asignado
        """
        # PID = -1 (Sin proceso asignado)
        # PID >= 1 (Con proceso asignado)
        self.pid = pid
        self.size = size  # Tamaño del bloque de memoria
        self.is_allocated = is_allocated  # Estado de asignación
        self.parent = parent  # Referencia al nodo padre
        self.left = None  # Hijo izquierdo (buddy)
        self.right = None  # Hijo derecho (buddy)
        self.is_split = False  # Indica si el nodo está dividido

class BuddySystemIterator:
    def __init__(self, root: Optional[Node]):
        self.stack = []
        if root:
            self.stack.append(root)
    
    def __iter__(self) -> Iterator[Node]:
        return self
    
    def __next__(self) -> Node:
        if not self.stack:
            raise StopIteration
        
        current = self.stack.pop()
        
        # Agregar hijos en orden inverso para procesar en pre-order
        if current.right:
            self.stack.append(current.right)
        if current.left:
            self.stack.append(current.left)
        
        return current

class BuddySystem(MemoryAllocationStrategy):
    def __init__(self, MAX_SIZE=1024, MIN_SIZE=4):
        """
        Inicializa el sistema Buddy
        
        Args:
            MAX_SIZE (int, optional): Tamaño máximo de memoria. Defaults to 1024.
            MIN_SIZE (int, optional): Tamaño mínimo de bloque. Defaults to 8.
        """
        self.MAX_SIZE = MAX_SIZE  # Tamaño total de memoria disponible
        self.MIN_SIZE = MIN_SIZE  # Tamaño mínimo de bloque asignable
        self.root = Node(MAX_SIZE)  # Nodo raíz que representa toda la memoria

    def __iter__(self):
        """Retorna un iterador para recorrer el árbol en pre-order"""
        return BuddySystemIterator(self.root)

    def allocate(self, pid, size):
        """
        Asigna memoria a un proceso
        
        Args:
            pid (int): ID del proceso
            size (int): Tamaño de memoria solicitado
            
        Returns:
            bool: True si la asignación fue exitosa, False en caso contrario
        """
        if size > self.MAX_SIZE:
            return False  # El tamaño solicitado excede la memoria total
        
        return self.__allocated_helper(self.root, pid, size)

    def release(self, pid):
        """
        Libera la memoria asignada a un proceso
        
        Args:
            pid (int): ID del proceso a liberar
            
        Returns:
            bool: True si la liberación fue exitosa, False en caso contrario
        """
        if self.root is None:
            return False  # No hay memoria inicializada
        
        if not self.__release_helper(self.root, pid):
            return False  # No se encontró el proceso
        
        return True  # Liberación exitosa

    def __allocated_helper(self, node: Node, pid, size):
        """
        Función helper recursiva para asignar memoria
        
        Args:
            node (Node): Nodo actual en la recursión
            pid (int): ID del proceso
            size (int): Tamaño de memoria solicitado
            
        Returns:
            bool: True si la asignación fue exitosa, False en caso contrario
        """
        if node.is_allocated:
            return False  # El nodo ya está asignado, no se puede usar
        
        if node.is_split:
            # Si el nodo está dividido, busca en sus hijos
            return (self.__allocated_helper(node.left, pid, size) or
                    self.__allocated_helper(node.right, pid, size))
                    
        # Si el nodo es lo suficientemente grande para dividir y cumplir con el mínimo
        if node.size // 2 >= self.MIN_SIZE and node.size // 2 >= size:
            if self.__split_node(node):
                # Después de dividir, intenta asignar en los hijos
                return (self.__allocated_helper(node.left, pid, size) 
                        or self.__allocated_helper(node.right, pid, size))
            return False
        # Si el tamaño del nodo es adecuado para la asignación
        elif node.size >= size:
            node.is_allocated = True
            node.pid = pid
            return True  # Asignación exitosa
        
        return False  # No se pudo asignar
    
    def __split_node(self, node: Node):
        """
        Divide un nodo de memoria en dos buddies
        
        Args:
            node (Node): Nodo a dividir
            
        Returns:
            bool: True si la división fue exitosa, False en caso contrario
        """
        # Verifica si el nodo ya está dividido, asignado o si el nuevo tamaño sería menor al mínimo
        if (node is None or node.is_split or node.is_allocated or
            node.size // 2 < self.MIN_SIZE):
            return False  # No se puede dividir
        
        node.is_split = True  # Marca el nodo como dividido
        # Crea los dos hijos (buddies) con la mitad del tamaño
        node.left = Node(node.size // 2, node)
        node.right = Node(node.size // 2, node)

        return True  # División exitosa

    def __release_helper(self, node: Node, pid):
        """
        Función helper recursiva para liberar memoria
        
        Args:
            node (Node): Nodo actual en la recursión
            pid (int): ID del proceso a liberar
            
        Returns:
            bool: True si se encontró y liberó el proceso, False en caso contrario
        """
        if node.pid == pid:
            # Encontró el proceso, libera el nodo
            node.is_allocated = False
            node.pid = -1
            self.__merge_buddies(node.parent)  # Intenta combinar buddies libres
            return True  # Liberación exitosa
        elif node.is_split:
            # Si está dividido, busca en los hijos
            return (self.__release_helper(node.left, pid) or
                    self.__release_helper(node.right, pid))
        
        return False  # No se encontró el proceso

    def __merge_buddies(self, parent: Node):
        """
        Combina buddies si ambos están libres (recursivamente hacia arriba)
        
        Args:
            node (Node): Nodo desde donde comenzar la combinación
        """
        # Caso base: no hay padre o el nodo actual está allocated
        if parent is None:
            return
        
        if (parent.left is not None and
            not parent.left.is_allocated and
            not parent.left.is_split and
            parent.right is not None and
            not parent.right.is_allocated and
            not parent.right.is_split):

            # Ambos buddies están libres → podemos mergear
            parent.is_split = False
            parent.left = None
            parent.right = None
            
            self.__merge_buddies(parent.parent)

    def get_used_memory(self):
        """
        Retorna la cantidad total de memoria utilizada por procesos.
        
        Returns:
            int: Memoria utilizada en unidades de tamaño
        """
        return self.__calculate_used_memory(self.root)
        
    def get_free_memory(self):
        """
        Retorna la cantidad total de memoria disponible para nuevos procesos.
        
        Returns:
            int: Memoria libre en unidades de tamaño
        """
        return self.MAX_SIZE - self.__calculate_used_memory(self.root)
        
    def get_memory_usage(self):
        """
        Retorna el porcentaje de memoria utilizada respecto al total disponible.
        
        Returns:
            float: Porcentaje de uso (0.0 a 100.0)
        """
        return (self.__calculate_used_memory(self.root) / self.MAX_SIZE) * 100

    def __calculate_used_memory(self, node: Node):
        """
        Método helper recursivo que calcula la memoria utilizada recorriendo el árbol.
        Utiliza recorrido en post-orden (hijos primero, luego raíz).
        
        Args:
            node (Node): Nodo actual del árbol a evaluar
            
        Returns:
            int: Memoria utilizada en el subárbol a partir de este nodo
        """
        if node is None:
            return 0  # Caso base: nodo nulo, no contribuye a memoria usada
        
        # Primero procesamos los hijos recursivamente
        if node.is_allocated:
            # Nodo asignado a un proceso → contribuye con todo su tamaño
            return node.size
        elif node.is_split:
            # Nodo dividido → la memoria usada es la suma de sus hijos
            return (self.__calculate_used_memory(node.left) + 
                    self.__calculate_used_memory(node.right))
        return 0  # Nodo libre → no contribuye a memoria usada

    def show(self, node = None, level=0):
        """Muestra el árbol de memoria (para debug)."""
        if node is None:
            node = self.root
        
        indent = "    " * level
        status = f"PID={node.pid}" if node.is_allocated else "FREE"
        if node.is_split:
            print(f"{indent}[Size={node.size} SPLIT]")
            self.show(node.left, level + 1)
            self.show(node.right, level + 1)
        else:
            print(f"{indent}[Size={node.size} {status}]")