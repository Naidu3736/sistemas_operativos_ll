import sys 
from mmu import MMU

class NRU:
    """
    @class NRU
    @brief Implementación del algoritmo de reemplazo Not Recently Used (NRU)
      
    @universidad Universidad Autónoma de Puebla
    @facultad Facultad de Ciencias de la Computación
    @materia Sistemas Operativos II
    
    @author
      + Aparicio Martínez Francisco  
      + Salinas Gil Diego
    
    @date 10/09/2025
    
    Objetivo:
      Implementar el algoritmo de reemplazo de páginas NRU para gestión de memoria virtual
    
    Descripción:
      El algoritmo NRU clasifica las páginas en 4 clases basadas en los bits 
      de referencia (R) y modificación (M), seleccionando víctimas de las clases 
      más bajas primero.
    
    Características:
      - Clasificación en 4 clases: (R=0,M=0), (R=0,M=1), (R=1,M=0), (R=1,M=1)
      - Reset periódico de bits de referencia
      - Selección simple y eficiente de víctimas
      - Bajo overhead computacional
    """
    
    def __init__(self, reset_interval=1000):
        """
        @brief Inicializa el algoritmo NRU
        @param reset_interval Número de referencias antes de resetear bits R
        
        @note Un reset_interval bajo favorece páginas recientemente usadas
        @note Un reset_interval alto puede causar que páginas antiguas permanezcan
        """
        self.reference_count = 0      # Contador de referencias desde último reset
        self.reset_interval = reset_interval  # Intervalo para reset de bits R

    def _classify_page(self, mmu: MMU, page):
        """
        @brief Clasifica una página en una de las 4 clases NRU
        @param mmu Instancia del Memory Management Unit
        @param page Número de página a clasificar
        @return Clase NRU (0-3) según bits R y M
        
        @retval 0 Clase más baja: R=0, M=0 (mejor candidato a víctima)
        @retval 1 Clase baja: R=0, M=1
        @retval 2 Clase media: R=1, M=0  
        @retval 3 Clase alta: R=1, M=1 (peor candidato a víctima)
        
        @note Las páginas de clase 0 son las ideales para reemplazo
        """
        r = mmu.get_reference_bit(page)
        m = mmu.get_modified_bit(page)

        if not r and not m:
            return 0  # No referenciada, no modificada - Mejor víctima
        if not r and m:
            return 1  # No referenciada, modificada - Buena víctima
        if r and not m:
            return 2  # Referenciada, no modificada - Mala víctima
        if r and m:
            return 3  # Referenciada, modificada - Peor víctima
        
    def _reset_reference_bits_if_needed(self, mmu: MMU):
        """
        @brief Resetea los bits de referencia si se alcanza el intervalo
        @param mmu Instancia del Memory Management Unit
        
        @note Este reset simula el comportamiento de un "reloj" que periódicamente
              limpia los bits de referencia, permitiendo detectar páginas no usadas
        """
        self.reference_count += 1

        if self.reference_count >= self.reset_interval:
            self.reference_count = 0
            mmu.clear_all_reference_bits()

    def select_victim(self, mmu: MMU):
        """
        @brief Selecciona una página víctima para reemplazo usando NRU
        @param mmu Instancia del Memory Management Unit
        @return Número de página seleccionada como víctima o None si no hay páginas
        
        @algorithm
          1. Resetear bits R si es necesario (reloj NRU)
          2. Obtener todas las páginas presentes en memoria
          3. Clasificar cada página en las 4 clases NRU
          4. Seleccionar la primera página de la clase no vacía más baja
          5. Retornar la página víctima
        
        @note Siempre selecciona de la clase más baja disponible
        @note Si múltiples páginas en misma clase, selecciona la primera (FIFO implícito)
        """
        # Paso 1: Verificar si es necesario resetear bits de referencia
        self._reset_reference_bits_if_needed(mmu)

        # Paso 2: Obtener páginas candidatas (solo las presentes en memoria)
        present_pages = mmu.get_present_pages()
        if not present_pages:
            return None  # No hay páginas para reemplazar
        
        # Paso 3: Clasificar páginas en las 4 clases NRU
        classes = {0: [], 1: [], 2: [], 3: []}
        for page in present_pages:
            page_class = self._classify_page(mmu, page)
            classes[page_class].append(page)

        # Paso 4: Buscar víctima en orden de clase (0 → 1 → 2 → 3)
        for class_num in range(4):
            if classes[class_num]:
                # Seleccionar primera página de la clase más baja no vacía
                return classes[class_num][0]
            
        # Fallback: debería ser inalcanzable si hay páginas presentes
        return present_pages[0]
