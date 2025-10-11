/**
 * @file memory_translator.c
 * @brief Implementación de un traductor de direcciones de memoria virtual a física
 *  
 * @universidad Universidad Autónoma de Puebla
 * @facultad Facultad de Ciencias de la Computación
 * @materia Sistemas Operativos II
 * 
 * @author
 *   + Aparicio Martínez Francisco  
 *   + Salinas Gil Diego
 * 
 * @date 10/09/2025
 * 
 * Objetivo:
 *   Implementar un sistema de traducción de direcciones mediante paginación
 * 
 * Descripción:
 *   Este sistema gestiona la traducción de direcciones virtuales a físicas
 *   usando una tabla de páginas y división de memoria en páginas de tamaño fijo
 * 
 * Características:
 *   - Traducción unidireccional virtual → física
 *   - Gestión de tabla de páginas
 *   - Detección de fallos de página
 *   - Máscaras de bits para extracción eficiente
 */


#include <stdint.h>
#include <stdlib.h>

/**
 * @struct AddressTranslator
 * @brief Traduce direcciones virtuales a físicas usando paginación
 * 
 * @var page_size - Tamaño de página en bytes
 * @var num_pages - Número de páginas virtuales
 * @var num_frames - Número de marcos físicos
 * @var page_size_bits - Número de bits para representar el tamaño de página
 * @var num_pages_bits - Número de bits para representar el número de páginas
 * @var num_frames_bits - Número de bits para representar el número de marcos
 * @var offset_mask - Máscara para extraer offset
 * @var frame_number_mask - Máscara para extraer número de marco
 * @var page_table - Tabla que mapea páginas → marcos
 * 
 * Nuevos campos para manejo de reemplazo de páginas:
 * @var use_bit - Bit de uso para cada marco (algoritmo de reemplazo)
 * @var frame_to_page - Mapeo inverso de marco a página (algoritmo de reemplazo)
 * @var clock_pointer - Puntero del reloj para algoritmo de reemplazo
 * @var occupied_frames - Número de marcos actualmente ocupados
 */
typedef struct {
    uint32_t page_size;
    uint32_t num_pages;
    uint32_t num_frames;
    uint32_t page_size_bits;
    uint32_t num_pages_bits;
    uint32_t num_frames_bits;
    uint32_t offset_mask;
    uint32_t frame_number_mask;
    uint32_t* page_table;

    uint8_t* use_bit;        
    int* frame_to_page;      
    uint32_t clock_pointer;  
    uint32_t occupied_frames;
} AddressTranslator;

/**
 * @brief Calcula bits necesarios para representar un número
 * @param n Número a calcular
 * @return Número de bits requeridos
 * 
 * @example calculate_bits(8) → 3 (para valores de 0-7)
 * @example calculate_bits(0) → 1 (0 necesita 1 bit)
 */
uint32_t calculate_bits(uint32_t n) {
    if (n <= 1) return 1;  // Caso especial: 0 necesita 1 bit
    n--;
    uint32_t bits = 0;
    while (n) {
        bits++;
        n >>= 1;  // n = n / 2
    }
    return bits;
}

/**
 * @brief Imprime número en binario con formato
 * @param n Número a imprimir
 * @param b Número de bits a imprimir
 * 
 * @example print_binary(13, 16) → "0000 0000 0000 1101"
 */
void print_binary(uint32_t n, uint32_t b, const char* str) {
    if (str) {
        printf("%s", str);
    }

    for (int i = b - 1; i >= 0; i--) {
        printf("%d", (n >> i) & 1);
        if (i % 4 == 0) printf(" ");  // Separador cada 4 bits
    }
}

/**
 * @brief Inicializa el traductor de direcciones
 * @param physical_memory_size Tamaño memoria física en bytes
 * @param virtual_memory_size Tamaño memoria virtual en bytes  
 * @param page_size Tamaño de página en bytes
 * @return Puntero a AddressTranslator o NULL si error
 * 
 * @note physical_memory_size y virtual_memory_size deben ser múltiplos de page_size
 */
AddressTranslator* init(uint32_t physical_memory_size, uint32_t virtual_memory_size, uint32_t page_size) {
    // Validar parámetros
    if (physical_memory_size == 0 || virtual_memory_size == 0 || page_size == 0 ||
        physical_memory_size % page_size != 0 || virtual_memory_size % page_size != 0) {
        return NULL;
    }

    AddressTranslator* translator = (AddressTranslator*)malloc(sizeof(AddressTranslator));
    if (!translator) return NULL;  // Error de memoria
    
    // Configurar propiedades básicas
    translator->page_size = page_size;
    translator->num_frames = physical_memory_size / page_size;
    translator->num_pages = virtual_memory_size / page_size;

    // Calcular bits para máscaras
    translator->page_size_bits = calculate_bits(page_size);
    translator->num_pages_bits = calculate_bits(translator->num_pages);
    translator->num_frames_bits = calculate_bits(translator->num_frames);

    // Calcular máscaras
    translator->offset_mask = (1 << translator->page_size_bits) - 1;
    print_binary(translator->offset_mask, 16, "\nMascara de offset: ");
    print_binary(translator->frame_number_mask, 16, "\nMascara de numero de marco: ");

    // Crear tabla de páginas
    translator->page_table = (uint32_t*)malloc(translator->num_pages * sizeof(uint32_t));
    for (unsigned int i = 0; i < translator->num_pages; ++i) {
       translator->page_table[i] = 0;  // Inicializar todas como ausentes
    }

    return translator;
}

/**
 * @brief Libera memoria del traductor
 * @param translator Puntero al traductor a destruir
 */
void destroy(AddressTranslator* translator) {
    // Verifica que el traductor esté inicializado, en otro caso no hace nada
    if (translator) {
        if (translator->page_table) {
            free(translator->page_table);
        }
        free(translator);
    }
}

/**
 * @brief Establece entrada en tabla de páginas
 * @param translator Puntero al traductor
 * @param page Número de página virtual
 * @param entry Entrada de tabla (marco físico + flags)
 */
void set_page_table(AddressTranslator* translator, uint32_t page, uint32_t entry) {
    // Verifica que el traductor y la tabla de páginas esten correctamente inicializados
    if (!translator || !translator->page_table) return;

    // Verfica que el número de páginas esté dentro de los límites del arreglo
    if (page >= translator->num_pages) return;

    // Asigna la entrada en la página
    translator->page_table[page] = entry;
}

/**
 * @brief Maneja fallo de página usando algoritmo de reemplazo Clock
 * @brief translator Puntero al traductor
 * @brief page_number Número de página que causó el fallo
 * @note Asume que la página no está presente en la tabla
 * @note Actualiza la tabla de páginas y estructuras internas
 * @note Si hay marcos libres, los usa antes de reemplazar
 * @note Usa el bit de uso para decidir qué página reemplazar
 * @note Marca la nueva página como presente y con bit de uso activo
 * @note Si reemplaza, marca la página antigua como ausente
 * @note Usa máscaras para manipular bits en las entradas
 */
void handle_page_fault(AddressTranslator* translator, uint32_t page_number) {
    const uint32_t present_bit_mask = 0x80;
    const uint32_t frame_number_mask = 0x7F;

    // Si hay marcos libres
    if (translator->occupied_frames < translator->num_frames) {
        for (uint32_t i = 0; i < translator->num_frames; i++) {
            if (translator->frame_to_page[i] == -1) {
                translator->page_table[page_number] = (i & frame_number_mask) | present_bit_mask;
                translator->frame_to_page[i] = page_number;
                translator->use_bit[i] = 1;
                translator->occupied_frames++;
                return;
            }
        }
    }

    // Clock replacement
    while (1) {
        uint32_t current_frame = translator->clock_pointer;
        if (translator->use_bit[current_frame] == 0) {
            int old_page = translator->frame_to_page[current_frame];
            if (old_page != -1) translator->page_table[old_page] &= ~present_bit_mask;

            translator->page_table[page_number] = (current_frame & frame_number_mask) | present_bit_mask;
            translator->frame_to_page[current_frame] = page_number;
            translator->use_bit[current_frame] = 1;

            translator->clock_pointer = (translator->clock_pointer + 1) % translator->num_frames;
            return;
        } else {
            translator->use_bit[current_frame] = 0;
            translator->clock_pointer = (translator->clock_pointer + 1) % translator->num_frames;
        }
    }
}

/**
 * @brief Traduce dirección virtual a física
 * @param translator Puntero al traductor
 * @param virtual_address Dirección virtual a traducir
 * @return Dirección física o UINT32_MAX si error
 * 
 * @retval UINT32_MAX si:
 * - Traductor o tabla de páginas no inicializado
 * - Dirección virtual válida
 * - Página fuera de rango  
 * - Página ausente
 */
uint32_t virtual_to_physical(AddressTranslator* translator, uint32_t virtual_address) {
    if (!translator || !translator->page_table) return UINT32_MAX;

    // Calcula el total de bits permitidos para la dirección virtual
    uint32_t total_bits = translator->num_pages_bits + translator->page_size_bits;

    // Verifica que la dirección virtual proporcionada sea válida
    if (virtual_address >= (1 << total_bits)) return UINT32_MAX;
    
    // Calcular número de página (parte alta de la dirección)
    uint32_t page_number = virtual_address >> translator->page_size_bits;
    printf("page_number: %u\n", page_number);
    
    // Verificar límites
    if (page_number >= translator->num_pages) return UINT32_MAX;
    
    // Verificar si la página está presente 
    uint32_t present_bit_mask = (1 << translator->num_frames_bits);
    if ((translator->page_table[page_number] & present_bit_mask) == 0) {
        return UINT32_MAX;  // Página ausente
    }

    // Extraer desplazamiento (parte baja de la dirección)
    uint32_t offset = virtual_address & translator->offset_mask;

    // Extraer número de marco físico
    uint32_t frame_number = translator->page_table[page_number] & translator->frame_number_mask;
    
    // Actualizar bit de uso (algoritmo de reemplazo)    
    translator->use_bit[frame_number] = 1;

    // Construir dirección física: marco + offset
    return (frame_number << translator->page_size_bits) | offset;

}

