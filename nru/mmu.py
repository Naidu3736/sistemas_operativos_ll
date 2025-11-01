import sys

class MMU:
    def __init__(self, physical_memory_size, virtual_memory_size, page_size):
        if (physical_memory_size == 0 or virtual_memory_size == 0 or page_size == 0 or
            physical_memory_size % page_size != 0 or virtual_memory_size % page_size != 0):
            raise ValueError("Parámetros inválidos para el traductor de direcciones")
        
        self.page_size = page_size
        self.num_frames = physical_memory_size // page_size
        self.num_pages = virtual_memory_size // page_size
        
        self.page_size_bits = self._calculate_bits(page_size)
        self.num_pages_bits = self._calculate_bits(self.num_pages)
        self.num_frames_bits = self._calculate_bits(self.num_frames)
        
        self.offset_mask = (1 << self.page_size_bits) - 1
        self.frame_number_mask = (1 << self.num_frames_bits) - 1

        self.present_bit = 1 << self.num_frames_bits
        self.modified_bit = 1 << (self.num_frames_bits + 2)
        self.reference_bit = 1 << (self.num_frames_bits + 3)
        
        # Inicializar tabla de páginas (todos los bits en 0)
        self.page_table = [0] * self.num_pages
        
        # Tabla de marcos: cada entrada contiene el número de página que ocupa ese marco
        # -1 indica que el marco está libre
        self.frame_table = [-1] * self.num_frames
    
    def _calculate_bits(self, n):
        """Calcula el número de bits necesarios para representar n valores"""
        if n <= 1:
            return 1
        n -= 1
        bits = 0
        while n:
            bits += 1
            n >>= 1
        return bits
    
    def print_binary(self, n, bits=None, separator=" "):
        """Imprime un número en formato binario con separadores"""
        if bits is None:
            binary = bin(n)[2:]
        else:
            binary = format(n, f'0{bits}b')
        
        # Agregar separadores cada 4 bits
        binary_with_sep = ""
        for i, bit in enumerate(reversed(binary)):
            if i > 0 and i % 4 == 0:
                binary_with_sep = " " + binary_with_sep
            binary_with_sep = bit + binary_with_sep
        
        return binary_with_sep
    
    def set_page_table(self, page, entry):
        """Establece una entrada en la tabla de páginas"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        self.page_table[page] = entry

    def set_frame_table(self, frame, page):
        """Establece la página que ocupa un marco específico"""
        if frame >= self.num_frames:
            raise IndexError(f"Número de marco {frame} fuera de rango")
        if page >= self.num_pages and page != -1:
            raise IndexError(f"Número de página {page} fuera de rango")
        
        self.frame_table[frame] = page

    def get_page_from_frame(self, frame):
        """Obtiene la página que ocupa un marco específico"""
        if frame >= self.num_frames:
            raise IndexError(f"Número de marco {frame} fuera de rango")
        return self.frame_table[frame]

    def get_free_frames(self):
        """Devuelve una lista de marcos libres"""
        return [frame for frame in range(self.num_frames) if self.frame_table[frame] == -1]

    def is_frame_free(self, frame):
        """Verifica si un marco está libre"""
        if frame >= self.num_frames:
            raise IndexError(f"Número de marco {frame} fuera de rango")
        return self.frame_table[frame] == -1

    def allocate_frame(self, frame, page):
        """Asigna un marco a una página específica"""
        if not self.is_frame_free(frame):
            raise ValueError(f"Marco {frame} ya está ocupado por página {self.frame_table[frame]}")
        
        self.set_frame_table(frame, page)
        self.set_frame_number(page, frame)
        self.set_present_bit(page, True)

    def free_frame(self, frame):
        """Libera un marco específico"""
        if self.is_frame_free(frame):
            return  # Ya está libre
        
        page = self.frame_table[frame]
        self.set_frame_table(frame, -1)
        
        # Si la página existe, marcar como no presente
        if page != -1 and page < self.num_pages:
            self.set_present_bit(page, False)
    
    def set_frame_number(self, page, frame_number):
        """Establece el número de frame para una página"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        if frame_number >= self.num_frames:
            raise IndexError(f"Número de frame {frame_number} fuera de rango")
        
        # Preservar los bits de estado y establecer el frame number
        status_bits = self.page_table[page] & ~self.frame_number_mask
        self.page_table[page] = status_bits | (frame_number & self.frame_number_mask)
    
    def set_present_bit(self, page, present=True):
        """Establece el bit de presencia"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        
        if present:
            self.page_table[page] |= self.present_bit
        else:
            self.page_table[page] &= ~self.present_bit
    
    def set_reference_bit(self, page, referenced=True):
        """Establece el bit de referencia"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        
        if referenced:
            self.page_table[page] |= self.reference_bit
        else:
            self.page_table[page] &= ~self.reference_bit
    
    def set_modified_bit(self, page, modified=True):
        """Establece el bit de modificado"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        
        if modified:
            self.page_table[page] |= self.modified_bit
        else:
            self.page_table[page] &= ~self.modified_bit
    
    def get_reference_bit(self, page) -> bool:
        """Obtiene el estado del bit de referencia"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        
        return (self.page_table[page] & self.reference_bit) != 0
    
    def get_modified_bit(self, page) -> bool:
        """Obtiene el estado del bit de modificado"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        
        return (self.page_table[page] & self.modified_bit) != 0
    
    def get_present_bit(self, page) -> bool:
        """Obtiene el estado del bit de presencia"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        
        return (self.page_table[page] & self.present_bit) != 0
    
    def get_frame_number(self, page):
        """Obtiene el número de frame de una página"""
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        
        return self.page_table[page] & self.frame_number_mask
    
    def clear_all_reference_bits(self):
        """Limpia todos los bits de referencia"""
        for page in range(self.num_pages):
            self.set_reference_bit(page, False)
    
    def get_present_pages(self):
        """Devuelve lista de números de página que están presentes en memoria"""
        return [page for page in range(self.num_pages) if self.get_present_bit(page)]
    
    def virtual_to_physical(self, virtual_address):
        """Convierte una dirección virtual a física"""
        if not self.page_table:
            return None
        
        total_bits = self.num_pages_bits + self.page_size_bits
        if virtual_address >= (1 << total_bits):
            return None
        
        page_number = virtual_address >> self.page_size_bits
        if page_number >= self.num_pages:
            return None
        
        # Verificar si la página está presente
        if not self.get_present_bit(page_number):
            return None
        
        # Marcar como referenciada
        self.set_reference_bit(page_number, True)
        
        offset = virtual_address & self.offset_mask
        frame_number = self.get_frame_number(page_number)
        
        return (frame_number << self.page_size_bits) | offset

    def destroy(self):
        """Libera recursos"""
        self.page_table = None
        self.frame_table = None