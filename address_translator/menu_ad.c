#include <stdio.h>

// Función que centra el texto según el ancho de la consola
void centrarTexto(const char* texto, int anchoConsola) {
    int longitud = 0;
    const char* ptr = texto;
    while (*ptr != '\0') { longitud++; ptr++; }
    int espacios = (anchoConsola - longitud) / 2;
    if (espacios < 0) espacios = 0;
    for (int i = 0; i < espacios; i++) printf(" ");
    printf("%s\n", texto);
}

void mostrarMenu(int anchoConsola)
{
    printf("\n\n\n");

    // Línea superior decorativa
    centrarTexto("==================================================================", anchoConsola);

    // ASCII Art del título
    centrarTexto("    __  ___________  _______  ______  __", anchoConsola);
    centrarTexto("   /  |/  / ____/  |/  / __ \\/ __ \\ \\/ /", anchoConsola);
    centrarTexto("  / /|_/ / __/ / /|_/ / / / / /_/ /\\  / ", anchoConsola);
    centrarTexto(" / /  / / /___/ /  / / /_/ / _, _/ / / ", anchoConsola);
    centrarTexto("/_/  /_/_____/_/  /_/\\____/_/ |_| /_/ ", anchoConsola);
    centrarTexto("                                       ", anchoConsola);
    centrarTexto("  __________  ___    _   _______ __    ___  __________  ____", anchoConsola);
    centrarTexto(" /_  __/ __ \\/   |  / | / / ___// /  /   |/_  __/ __ \\/ __ \\", anchoConsola);
    centrarTexto("  / / / /_/ / /| | /  |/ /\\__ \\/ / / / || / / / / / / /_/ /", anchoConsola);
    centrarTexto(" / / / _, _/ ___ |/ /|  /___/ / /___/ ___ |/ / / /_/ / _, _/", anchoConsola);
    centrarTexto("/_/ /_/ |_/_/  |_/_/ |_//____/_____/_/  |_/_/  \\____/_/ |_|\n", anchoConsola);

    // Línea inferior decorativa
    centrarTexto("==================================================================", anchoConsola);

    printf("\n");

    // Título del menú en rojo
    printf("\033[1;31m"); // Color rojo
    centrarTexto(" ----MENU PRINCIPAL---- ", anchoConsola);
    printf("\033[0m"); // Resetea color

    centrarTexto("===============================", anchoConsola);
    printf("\n");
    centrarTexto("Seleccione el modo", anchoConsola);
    printf("\n");
    centrarTexto("1. Interactivo (Por teclado)", anchoConsola);
    printf("\n");
    centrarTexto("2. Lectura de archivo", anchoConsola);
    printf("\n");
    centrarTexto("3. Salir", anchoConsola);
    printf("\n");
    centrarTexto("===============================", anchoConsola);
    printf("\n");
    centrarTexto("Seleccione una opcion: ", anchoConsola);
}
