#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include "memory_traslate.c"

int main() {
    srand(time(NULL));

    uint32_t n;
    uint32_t virtual_size;
    uint32_t physical_size;
    uint32_t page_size;

    printf("Ingresa el tamano de memoria virtual: ");
    scanf("%i", &virtual_size);
    printf("%x\n", virtual_size);
    printf("Ingresa el tamano de memoria fisica: ");
    scanf("%i", &physical_size);
    printf("Ingresa el tamano de pagina: ");
    scanf("%i", &page_size);
    
    AddressTranslator* translator = init(physical_size, virtual_size, page_size);

    for (int i = 0; i < translator->num_pages; i++) {
        set_page_table(translator, i, rand());
    }

    for (unsigned int i = 0; i < translator->num_pages; ++i) {
        printf("%u | ", i);
        print_binary(translator->page_table[i]);
        printf("\n");
    }

    uint32_t virtual_address;
    printf("\nIngresa la direccion virtual: ");
    scanf("%i", &virtual_address);
    printf("%x\n", virtual_address);

    uint32_t physical_address = virtual_to_physical(translator, virtual_address);
    if (physical_address == -1) {
        printf("\nFallo de página...");
    } else {
        printf("\nDireccion fisica: 0x%X\n", physical_address);
        print_binary(physical_address);
    }
    
    return 0;
}