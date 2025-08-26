from abc import ABC, abstractmethod
from utils.process import Process

class MemoryAllocationAbstract(ABC):
    """Clase abstracta de administración de memoria"""
    def __init__(self, MAX_SIZE, MIN_SIZE):
        self.MAX_SIZE = MAX_SIZE
        self.MIN_SIZE = MIN_SIZE
    
    @abstractmethod
    def allocate(self, pid, size):
        """Asigna memoria a un proceso"""
        pass
    
    @abstractmethod
    def release(self, pid):
        """Libera memoria de un proceso"""
        pass
    
    @abstractmethod
    def get_used_memory(self):
        """Retorna memoria utilizada"""
        pass
    
    @abstractmethod
    def get_free_memory(self):
        """Retorna memoria libre"""
        pass
    
    @abstractmethod
    def get_memory_usage(self):
        """Retorna porcentaje de uso"""
        pass