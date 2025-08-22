from abc import ABC, abstractmethod
from utils.process import Process

class MemoryAllocationStrategy(ABC):
    """Interfaz para estrategias de administración de memoria"""
    
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
    
    @abstractmethod
    def show(self):
        """Muestra el estado de la memoria"""
        pass