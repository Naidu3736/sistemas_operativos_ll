#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include "address_translator.c"

AddressTranslator* translator;

void showMenu() {
    printf("\n======== Menu de Traductor de Direcciones ========\n");
    printf("1. Mostrar tabla de paginas.\n");
    printf("2. Ingresar contenido a tabla de paginas.\n");
    printf("3. Traducir direccion virtual a fisica.\n");
    printf("4. Salir.\n");
    printf("Seleccione una opcion: ");
}

void showTable() {
    if (!translator) {
        printf("Traductor no inicializado.\n");
        return;
    }

    printf("\n======== Tabla de Paginas ========\n");
    printf("Pagina | Entrada (16) | Entrada (2)\n");
    printf("--------------------------------\n");
    
    for (uint32_t i = 0; i < translator->num_pages; i++) {
        uint32_t entry = translator->page_table[i];
        printf("  %3u  |     %3X      |    ", i, entry);
        print_binary(entry, 5 + translator->num_frames_bits);
        printf("\n");
    }
}

void enterPageContent() {
    if (!translator) {
        printf("Traductor no inicializado.\n");
        return;
    }

    uint32_t page, entry;
    int present;
    
    printf("Ingrese numero de pagina (0-%u): ", translator->num_pages - 1);
    scanf("%i", &page);
    
    if (page >= translator->num_pages) {
        printf("Pagina fuera de rango.\n");
        return;
    }

    printf("Ingrese el contenido de la pagina %i: ", page);
    scanf("%i", &entry);
    
    set_page_table(translator, page, entry);
    printf("Entrada de tabla actualizada.\n");
}

void translateAddress() {
    if (!translator) {
        printf("Traductor no inicializado.\n");
        return;
    }

    uint32_t virtual_address;
    printf("Ingrese direccion virtual (0-%X): ", 
           (1 << (translator->num_pages_bits + translator->page_size_bits)) - 1);
    scanf("%i", &virtual_address);
    
    uint32_t physical_address = virtual_to_physical(translator, virtual_address);
    
    if (physical_address == UINT32_MAX) {
        printf("Error: Direccion invalida o pagina ausente.\n");
        return;
    }

    printf("Direccion fisica (16): %x\n", physical_address);
    printf("Direccion fisica (2): ");
    print_binary(physical_address, translator->num_frames_bits + translator->page_size_bits);
    printf("\n");
}

int main() {
    // Inicializar el traductor con memoria de 64KB fisica, 128KB virtual, paginas de 4KB
    uint32_t physical_memory_size, virtual_memory_size, page_size;

    printf("\nIngrese el tamaño de la memoria fisica: ");
    scanf("%u", &physical_memory_size);
    
    printf("Ingrese el tamaño de la memoria virtual: ");
    scanf("%u", &virtual_memory_size);

    printf("Ingrese el tamaño de pagina: ");
    scanf("%u", &page_size);

    
    translator = init(physical_memory_size, virtual_memory_size, page_size);
    
    if (!translator) {
        printf("Error al inicializar el traductor.\n");
        return 1;
    }
    
    printf("\n=== Traductor de Direcciones de Memoria ===\n");
    printf("Configuracion inicial:\n");
    printf("- Memoria fisica: %uKB (%u marcos)\n", physical_memory_size, translator->num_frames);
    printf("- Memoria virtual: %uKB (%u paginas)\n", virtual_memory_size, translator->num_pages);
    printf("- Tamaño de pagina: %uKB\n", translator->page_size);
    printf("- Bits para desplazamiento: %u\n", translator->page_size_bits);
    printf("- Bits para pagina: %u\n", translator->num_pages_bits);
    printf("- Bits para marco: %u\n", translator->num_frames_bits);
    
    int option;
    do {
        showMenu();
        scanf("%d", &option);
        
        switch(option) {
            case 1:
                showTable();
                break;
            case 2:
                enterPageContent();
                break;
            case 3:
                translateAddress();
                break;
            case 4:
                printf("Saliendo...\n");
                break;
            default:
                printf("Opcion invalida.\n");
        }
    } while(option != 4);
    
    destroy(translator);
    return 0;
}
