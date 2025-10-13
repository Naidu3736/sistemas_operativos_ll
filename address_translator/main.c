#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "address_translator.c"
#include "menu_ad.c"


AddressTranslator* translator;

void showMenu() {
    printf("\n======== Menu de Traductor de Direcciones ========\n");
    printf("1. Mostrar tabla de paginas.\n");
    printf("2. Ingresar contenido a tabla de paginas.\n");
    printf("3. Traducir direccion virtual a fisica.\n");
    printf("4. Salir.\n");
    printf("Seleccione una opcion: ");
}

void showInit(uint32_t physical_memory_size, uint32_t virtual_memory_size) {
    printf("\n=== Traductor de Direcciones de Memoria ===\n");
    printf("Configuracion inicial:\n");
    printf("- Memoria fisica: %uB (%u marcos)\n", physical_memory_size, translator->num_frames);
    printf("- Memoria virtual: %uB (%u paginas)\n", virtual_memory_size, translator->num_pages);
    printf("- Tamano de pagina: %uB\n", translator->page_size);
    printf("- Bits para desplazamiento: %u\n", translator->page_size_bits);
    printf("- Bits para pagina: %u\n", translator->num_pages_bits);
    printf("- Bits para marco: %u\n", translator->num_frames_bits);
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
        print_binary(entry, 5 + translator->num_frames_bits, NULL);
        printf("\n");
    }
}
void enterPageContent() {
    if (!translator) {
        printf("Traductor no inicializado.\n");
        return;
    }

    uint32_t page, entry;
    
    printf("Ingrese numero de pagina (0-%u): ", translator->num_pages - 1);
    
    // 1. VERIFICAR que se leyó un número correctamente
    if (scanf("%u", &page) != 1) {
        printf("\nError: Entrada invalida. Debe ingresar un numero.\n");
        // 2. LIMPIAR el búfer de entrada para evitar un bucle infinito
        while (getchar() != '\n'); 
        return;
    }
    
    if (page >= translator->num_pages) {
        printf("Pagina fuera de rango.\n");
        return;
    }

    printf("Ingrese el contenido de la pagina %u: ", page);

    // 3. REPETIR la misma verificación para la segunda entrada
    if (scanf("%u", &entry) != 1) {
        printf("\nError: Entrada invalida. Debe ingresar un numero.\n");
        while (getchar() != '\n');
        return;
    }
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
    scanf("%X", &virtual_address);
    
    uint32_t physical_address = virtual_to_physical(translator, virtual_address);
    
    if (physical_address == UINT32_MAX) {
        printf("Error: Direccion invalida o pagina ausente.\n");
        return;
    }

    printf("Direccion fisica (16): %X\n", physical_address);
    printf("Direccion fisica (2): ");
    print_binary(physical_address, translator->num_frames_bits + translator->page_size_bits, NULL);
    printf("\n");
}

void loadFromFile(const char* filename) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        printf("No se pudo abrir el archivo %s\n", filename);
        return;
    }

    uint32_t physical_memory_size, virtual_memory_size, page_size;
    fscanf(file, "%u %u %u", &physical_memory_size, &virtual_memory_size, &page_size);

    translator = init(physical_memory_size, virtual_memory_size, page_size);
    if (!translator) {
        printf("Error al inicializar el traductor desde archivo.\n");
        fclose(file);
        return;
    }

    showInit(physical_memory_size, virtual_memory_size);
    printf("\n");

    char command[32];
    while (fscanf(file, "%s", command) != EOF) {
        if (strcmp(command, "PAGE") == 0) {
            uint32_t page, entry;
            fscanf(file, "%X %X", &page, &entry);
            set_page_table(translator, page, entry);
            printf("pagina %X con entrada %X\n", page, entry);
        } 
        else if (strcmp(command, "TRANS") == 0) {
            uint32_t virtual_address;
            fscanf(file, "%X", &virtual_address);
            uint32_t physical_address = virtual_to_physical(translator, virtual_address);
            if (physical_address == UINT32_MAX) {
                printf("\nFallo de pagina de la direccion %X\n", virtual_address);
            } else {
                printf("\nVA = %X -> PA (16): %X\n", virtual_address, physical_address);
                printf("PA (2): ");
                print_binary(physical_address, translator->num_frames_bits + translator->page_size_bits, NULL);
                printf("\n");
            }
        } 
        else if (strcmp(command, "SHOWTABLE") == 0) {
            printf("\n======== Tabla de Paginas ========\n");
            printf("Pagina | Entrada (16) | Entrada (2)\n");
            printf("--------------------------------\n");

            for (uint32_t i = 0; i < translator->num_pages; i++) {
                uint32_t entry = translator->page_table[i];
                printf("  %3X  |     %3X      |    ", i, entry);
                print_binary(entry, 5 + translator->num_frames_bits, NULL);
                printf("\n");
            }
        }
    }

    printf("\n");
    system("Pause");

    fclose(file);
}
/*Limpia la pantalla*/
void cleanscreen() {
    #ifdef _WIN32
        system("cls");
    #else
      system("clear");
    #endif
}


int main() {
    int mode;
    int anchoConsola = 80; // Valor por defecto
    mostrarMenu(anchoConsola);
    scanf("%d", &mode);
    if (mode == 1) {
        cleanscreen();
        uint32_t physical_memory_size, virtual_memory_size, page_size;

        printf("\nIngrese el tamaño de la memoria fisica: ");
        scanf("%u", &physical_memory_size);
        
        printf("Ingrese el tamaño de la memoria virtual: ");
        scanf("%u", &virtual_memory_size);

        printf("Ingrese el tamaño de pagina: ");
        scanf("%u", &page_size);

        translator = init(physical_memory_size, virtual_memory_size, page_size);

        showInit(physical_memory_size, virtual_memory_size);
        
        if (!translator) {
            printf("Error al inicializar el traductor.\n");
            return 1;
        }
        
        int option;
        do {
            showMenu();

            scanf("%d", &option);
            
            switch(option) {
                case 1: showTable(); break;
                case 2: enterPageContent(); break;
                case 3: translateAddress(); break;
                case 4: printf("Saliendo...\n"); break;
                default: printf("Opcion invalida.\n");
            }
        } while(option != 4);

        destroy(translator);
    } 
    else if (mode == 2) {
        cleanscreen();
        char filename[100];
        printf("Ingrese el nombre del archivo con su extension (ejemplo, prueba.txt): ");
        scanf("%s", filename);
        loadFromFile(filename);
        destroy(translator);
    } 
    else if (mode == 3) {
        printf("Saliendo del programa...\n");
        return 0;
    }
    else {
        printf("Opcion invalida.\n");
    }

    return 0;
}
