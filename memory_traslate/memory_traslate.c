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
 *   - Traducción bidireccional virtual ↔ física
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
 * @var offset_mask - Máscara para extraer offset
 * @var frame_number_mask - Máscara para extraer número de marco
 * @var page_table - Tabla que mapea páginas → marcos
 */
typedef struct {
    uint32_t page_size;
    uint32_t num_pages;
    uint32_t num_frames;
    uint32_t offset_mask;
    uint32_t frame_number_mask;
    uint32_t* page_table;
    uint32_t* frame_table;
} AddressTranslator;

/**
 * @brief Calcula bits necesarios para representar un número
 * @param n Número a calcular
 * @return Número de bits requeridos
 * 
 * @example calculate_bits(8) → 4 (1000 necesita 4 bits)
 * @example calculate_bits(0) → 1 (0 necesita 1 bit)
 */
uint32_t calculate_bits(uint32_t n) {
    if (n == 0) return 1;  // Caso especial: 0 necesita 1 bit
    
    uint32_t bits = 0;
    while (n > 0) {
        bits++;
        n >>= 1;  // n = n / 2
    }
    return bits;
}

/**
 * @brief Imprime número en binario con formato
 * @param n Número a imprimir
 * 
 * @example print_binary(13) → "0000 0000 0000 0000 0000 0000 0000 1101"
 */
void print_binary(uint32_t n) {
    for (int i = 31; i >= 0; i--) {
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
    AddressTranslator* translator = (AddressTranslator*)malloc(sizeof(AddressTranslator));
    if (!translator) return NULL;  // Error de memoria
    
    // Configurar propiedades básicas
    translator->page_size = page_size;
    translator->num_frames = physical_memory_size / page_size;
    translator->num_pages = virtual_memory_size / page_size;

    // Calcular máscaras
    translator->offset_mask = (1 << calculate_bits(page_size-1)) - 1;
    translator->frame_number_mask = (1 << calculate_bits(translator->num_frames-1)) - 1;

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
    if (!translator || !translator->page_table || page < 0 || entry < 0) return;
    translator->page_table[page] = entry;
}

/**
 * @brief Traduce dirección virtual a física
 * @param translator Puntero al traductor
 * @param virtual_address Dirección virtual a traducir
 * @return Dirección física o UINT32_MAX si error
 * 
 * @retval UINT32_MAX si:
 * - Traductor no inicializado
 * - Página fuera de rango  
 * - Página ausente
 */
uint32_t virtual_to_physical(AddressTranslator* translator, uint32_t virtual_address) {
    if (!translator) return UINT32_MAX;

    // Extraer offset (parte baja de la dirección)
    uint32_t offset = virtual_address & translator->offset_mask;
    
    // Calcular número de página (parte alta de la dirección)
    uint32_t page_number = virtual_address >> calculate_bits(translator->page_size-1);

    // Verificar límites
    if (page_number >= translator->num_pages) return UINT32_MAX;

    // Verificar si la página está presente 
    uint32_t present_bit_mask = (1 << calculate_bits(translator->num_frames-1));
    if ((translator->page_table[page_number] & present_bit_mask) == 0) {
        return UINT32_MAX;  // Página ausente
    }

    // Extraer número de marco físico
    uint32_t frame_number = translator->page_table[page_number] & translator->frame_number_mask;
    
    // Construir dirección física: marco + offset
    uint32_t offset_bits = calculate_bits(translator->page_size-1);
    return (frame_number << offset_bits) | offset;
}