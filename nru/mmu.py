import sys

class MMU:
    """
    @class MMU
    @brief Implementación de un traductor de direcciones de memoria virtual a física
      
    @universidad Universidad Autónoma de Puebla
    @facultad Facultad de Ciencias de la Computación
    @materia Sistemas Operativos II
    
    @author
      + Aparicio Martínez Francisco  
      + Salinas Gil Diego
    
    @date 10/09/2025
    
    Objetivo:
      Implementar un sistema de traducción de direcciones mediante paginación
    
    Descripción:
      Este sistema gestiona la traducción de direcciones virtuales a físicas
      usando una tabla de páginas y división de memoria en páginas de tamaño fijo
    
    Características:
      - Traducción unidireccional virtual → física
      - Gestión de tabla de páginas y tabla de marcos
      - Detección de fallos de página
      - Soporte para algoritmos de reemplazo (NRU)
      - Máscaras de bits para extracción eficiente
    """
    
    def __init__(self, physical_memory_size, virtual_memory_size, page_size):
        """
        @brief Inicializa el traductor de direcciones (Memory Management Unit)
        @param physical_memory_size Tamaño memoria física en bytes
        @param virtual_memory_size Tamaño memoria virtual en bytes  
        @param page_size Tamaño de página en bytes
        
        @note physical_memory_size y virtual_memory_size deben ser múltiplos de page_size
        @throws ValueError si parámetros son inválidos
        """
        if (physical_memory_size == 0 or virtual_memory_size == 0 or page_size == 0 or
            physical_memory_size % page_size != 0 or virtual_memory_size % page_size != 0):
            raise ValueError("Parámetros inválidos para el traductor de direcciones")
        
        # Configurar propiedades básicas
        self.page_size = page_size
        self.num_frames = physical_memory_size // page_size
        self.num_pages = virtual_memory_size // page_size
        
        # Calcular bits para máscaras
        self.page_size_bits = self._calculate_bits(page_size)
        self.num_pages_bits = self._calculate_bits(self.num_pages)
        self.num_frames_bits = self._calculate_bits(self.num_frames)
        
        # Calcular máscaras para extracción de bits
        self.offset_mask = (1 << self.page_size_bits) - 1
        self.frame_number_mask = (1 << self.num_frames_bits) - 1

        # Definir posiciones de bits de estado
        self.present_bit = 1 << self.num_frames_bits        # Bit de presencia
        self.modified_bit = 1 << (self.num_frames_bits + 2) # Bit de modificado  
        self.reference_bit = 1 << (self.num_frames_bits + 3) # Bit de referencia
        
        # Inicializar tablas de memoria
        self.page_table = [0] * self.num_pages    # Tabla que mapea páginas → marcos + flags
        self.frame_table = [-1] * self.num_frames # Tabla que mapea marcos → páginas (-1 = libre)
    
    def _calculate_bits(self, n):
        """
        @brief Calcula bits necesarios para representar un número
        @param n Número a calcular
        @return Número de bits requeridos
        
        @example _calculate_bits(8) → 3 (para valores de 0-7)
        @example _calculate_bits(0) → 1 (0 necesita 1 bit)
        """
        if n <= 1:
            return 1
        n -= 1
        bits = 0
        while n:
            bits += 1
            n >>= 1
        return bits
    
    def print_binary(self, n, bits=None, separator=" "):
        """
        @brief Imprime número en binario con formato
        @param n Número a imprimir
        @param bits Número de bits a imprimir (None = automático)
        @param separator Separador entre grupos de bits
        
        @example print_binary(13, 8) → "0000 1101"
        """
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
        """
        @brief Establece entrada en tabla de páginas
        @param page Número de página virtual
        @param entry Entrada de tabla (marco físico + flags)
        
        @throws IndexError si página fuera de rango
        """
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        self.page_table[page] = entry

    def set_frame_table(self, frame, page):
        """
        @brief Establece la página que ocupa un marco específico
        @param frame Número de marco físico
        @param page Número de página virtual (-1 para marco libre)
        
        @throws IndexError si marco o página fuera de rango
        """
        if frame >= self.num_frames:
            raise IndexError(f"Número de marco {frame} fuera de rango")
        if page >= self.num_pages and page != -1:
            raise IndexError(f"Número de página {page} fuera de rango")
        self.frame_table[frame] = page

    def get_page_from_frame(self, frame):
        """
        @brief Obtiene la página que ocupa un marco específico
        @param frame Número de marco físico
        @return Número de página o -1 si marco libre
        
        @throws IndexError si marco fuera de rango
        """
        if frame >= self.num_frames:
            raise IndexError(f"Número de marco {frame} fuera de rango")
        return self.frame_table[frame]

    def get_free_frames(self):
        """
        @brief Devuelve una lista de marcos libres
        @return Lista de números de marco disponibles
        """
        return [frame for frame in range(self.num_frames) if self.frame_table[frame] == -1]

    def is_frame_free(self, frame):
        """
        @brief Verifica si un marco está libre
        @param frame Número de marco físico
        @return True si marco libre, False si ocupado
        
        @throws IndexError si marco fuera de rango
        """
        if frame >= self.num_frames:
            raise IndexError(f"Número de marco {frame} fuera de rango")
        return self.frame_table[frame] == -1

    def allocate_frame(self, frame, page):
        """
        @brief Asigna un marco a una página específica
        @param frame Número de marco físico a asignar
        @param page Número de página virtual a cargar
        
        @throws ValueError si marco ya está ocupado
        @throws IndexError si marco o página fuera de rango
        
        @note Actualiza tanto tabla de páginas como tabla de marcos
        """
        if not self.is_frame_free(frame):
            raise ValueError(f"Marco {frame} ya está ocupado por página {self.frame_table[frame]}")
        
        # Actualizar tabla de marcos
        self.set_frame_table(frame, page)
        
        # Establecer frame number en la entrada de página
        status_bits = self.page_table[page] & ~self.frame_number_mask
        self.page_table[page] = status_bits | (frame & self.frame_number_mask)
        
        # Marcar página como presente
        self.set_present_bit(page, True)

    def free_frame(self, frame):
        """
        @brief Libera un marco específico
        @param frame Número de marco físico a liberar
        
        @note Si el marco estaba ocupado, marca la página como ausente
        """
        if self.is_frame_free(frame):
            return  # Marco ya está libre
        
        # Obtener página que ocupaba el marco
        page = self.frame_table[frame]
        
        # Liberar marco en tabla de marcos
        self.set_frame_table(frame, -1)
        
        # Marcar página como ausente si existe
        if page != -1 and page < self.num_pages:
            self.set_present_bit(page, False)
    
    def set_present_bit(self, page, present=True):
        """
        @brief Establece el bit de presencia
        @param page Número de página virtual
        @param present True para presente, False para ausente
        
        @throws IndexError si página fuera de rango
        """
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        if present:
            self.page_table[page] |= self.present_bit
        else:
            self.page_table[page] &= ~self.present_bit
    
    def set_reference_bit(self, page, referenced=True):
        """
        @brief Establece el bit de referencia
        @param page Número de página virtual
        @param referenced True para referenciada, False para no referenciada
        
        @throws IndexError si página fuera de rango
        """
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        if referenced:
            self.page_table[page] |= self.reference_bit
        else:
            self.page_table[page] &= ~self.reference_bit
    
    def set_modified_bit(self, page, modified=True):
        """
        @brief Establece el bit de modificado
        @param page Número de página virtual
        @param modified True para modificada, False para no modificada
        
        @throws IndexError si página fuera de rango
        """
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        if modified:
            self.page_table[page] |= self.modified_bit
        else:
            self.page_table[page] &= ~self.modified_bit
    
    def get_reference_bit(self, page) -> bool:
        """
        @brief Obtiene el estado del bit de referencia
        @param page Número de página virtual
        @return True si página fue referenciada, False en caso contrario
        
        @throws IndexError si página fuera de rango
        """
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        return (self.page_table[page] & self.reference_bit) != 0
    
    def get_modified_bit(self, page) -> bool:
        """
        @brief Obtiene el estado del bit de modificado
        @param page Número de página virtual
        @return True si página fue modificada, False en caso contrario
        
        @throws IndexError si página fuera de rango
        """
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        return (self.page_table[page] & self.modified_bit) != 0
    
    def get_present_bit(self, page) -> bool:
        """
        @brief Obtiene el estado del bit de presencia
        @param page Número de página virtual
        @return True si página está en memoria, False si ausente
        
        @throws IndexError si página fuera de rango
        """
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        return (self.page_table[page] & self.present_bit) != 0
    
    def get_frame_number(self, page):
        """
        @brief Obtiene el número de frame de una página
        @param page Número de página virtual
        @return Número de marco físico asociado a la página
        
        @throws IndexError si página fuera de rango
        """
        if page >= self.num_pages:
            raise IndexError(f"Número de página {page} fuera de rango")
        return self.page_table[page] & self.frame_number_mask
    
    def clear_all_reference_bits(self):
        """
        @brief Limpia todos los bits de referencia
        @note Utilizado por algoritmos de reemplazo como NRU para reset periódico
        """
        for page in range(self.num_pages):
            self.set_reference_bit(page, False)
    
    def get_present_pages(self):
        """
        @brief Devuelve lista de números de página que están presentes en memoria
        @return Lista de páginas cargadas en memoria física
        """
        return [page for page in range(self.num_pages) if self.get_present_bit(page)]
    
    def virtual_to_physical(self, virtual_address):
        """
        @brief Convierte dirección virtual a física
        @param virtual_address Dirección virtual a traducir
        @return Dirección física o None si error
        
        @retval None si:
          - Traductor no inicializado
          - Dirección virtual fuera de rango  
          - Página fuera de rango
          - Página ausente
        
        @note Marca automáticamente la página como referenciada en acceso exitoso
        """
        if not self.page_table:
            return None
        
        # Verificar que dirección virtual esté dentro del rango permitido
        total_bits = self.page_size_bits + self.num_pages_bits
        if virtual_address >= (1 << total_bits):
            return None
        
        # Calcular número de página (parte alta de la dirección)
        page_number = virtual_address >> self.page_size_bits
        
        # Verificar límites de página
        if page_number >= self.num_pages:
            return None
        
        # Verificar si la página está presente
        if not self.get_present_bit(page_number):
            return None
        
        # Marcar página como referenciada (acceso de lectura)
        self.set_reference_bit(page_number, True)
        
        # Extraer desplazamiento (parte baja de la dirección)
        offset = virtual_address & self.offset_mask
        
        # Extraer número de marco físico
        frame_number = self.get_frame_number(page_number)
        
        # Construir dirección física: marco + offset
        return (frame_number << self.page_size_bits) | offset
