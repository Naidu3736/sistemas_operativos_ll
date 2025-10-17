
"""
@file    simulador_memoria.py
@brief   Implementación en Python de un traductor de direcciones de memoria virtual a física.
         Este script es una migración del proyecto original en C.

@university Benemerita Universidad Autónoma de Puebla
@facultad   Facultad de Ciencias de la Computación
@materia    Sistemas Operativos II

@author
  + Aparicio Martínez Francisco
  + Salinas Gil Diego

@date 10/09/2025

Objetivo:
  Implementar un sistema de traducción de direcciones mediante paginación en Python.

Descripción:
  Este sistema gestiona la traducción de direcciones virtuales a físicas
  usando una tabla de páginas, división de memoria en páginas de tamaño fijo,
  y el algoritmo de reemplazo de páginas "Clock".

Características:
  - Traducción unidireccional virtual → física.
  - Gestión de tabla de páginas.
  - Detección y manejo de fallos de página.
  - Algoritmo de reemplazo de páginas Clock (Segunda Oportunidad).
  - Modos de operación interactivo y por archivo.
  - Interfaz de texto enriquecida con arte ASCII y reacciones dinámicas.
"""

import os
import sys
import time

# Variable global para simular el puntero del traductor en C
translator = None

# --- Clase para el Manejo de la Lógica de Traducción ---
class AddressTranslator:
    """
    Traduce direcciones virtuales a físicas usando paginación.

    Esta clase encapsula toda la lógica de la memoria, incluyendo el tamaño de las
    páginas, el número de marcos, la tabla de páginas y las estructuras de datos
    necesarias para el algoritmo de reemplazo de páginas.

    Attributes:
        page_size (int): Tamaño de cada página en bytes.
        num_frames (int): Número total de marcos en la memoria física.
        num_pages (int): Número total de páginas en la memoria virtual.
        page_size_bits (int): Número de bits para el desplazamiento (offset).
        num_pages_bits (int): Número de bits para el número de página virtual.
        num_frames_bits (int): Número de bits para el número de marco físico.
        offset_mask (int): Máscara de bits para extraer el offset de una dirección.
        present_bit_mask (int): Máscara para el bit de presencia en una entrada de tabla.
        frame_number_mask (int): Máscara para extraer el número de marco de una entrada.
        page_table (list): Tabla que mapea páginas virtuales a marcos físicos.
        use_bit (list): Bit de uso para cada marco (para el algoritmo Clock).
        frame_to_page (list): Mapeo inverso de marco a página (para reemplazo).
        clock_pointer (int): Puntero del reloj para el algoritmo de reemplazo.
        occupied_frames (int): Contador de marcos actualmente en uso.
    """
    def __init__(self, physical_memory_size, virtual_memory_size, page_size):
        """
        Inicializa el traductor de direcciones.

        Args:
            physical_memory_size (int): Tamaño total de la memoria física en bytes.
            virtual_memory_size (int): Tamaño total de la memoria virtual en bytes.
            page_size (int): Tamaño de cada página en bytes.

        Raises:
            ValueError: Si los tamaños no son válidos o no son múltiplos del tamaño de página.
        """
        if not all([physical_memory_size, virtual_memory_size, page_size]) or \
           physical_memory_size % page_size != 0 or virtual_memory_size % page_size != 0:
            raise ValueError("Error en los tamaños de memoria o página.")

        self.page_size = page_size
        self.num_frames = physical_memory_size // page_size
        self.num_pages = virtual_memory_size // page_size
        self.page_size_bits = (page_size - 1).bit_length()
        self.num_pages_bits = (self.num_pages - 1).bit_length() if self.num_pages > 1 else 1
        self.num_frames_bits = (self.num_frames - 1).bit_length() if self.num_frames > 1 else 1
        self.offset_mask = (1 << self.page_size_bits) - 1
        self.present_bit_mask = 1 << self.num_frames_bits
        self.frame_number_mask = self.present_bit_mask - 1
        self.page_table = [0] * self.num_pages
        self.use_bit = [0] * self.num_frames
        self.frame_to_page = [-1] * self.num_frames
        self.clock_pointer = 0
        self.occupied_frames = 0

    def set_page_table_entry(self, page, entry):
        """
        Establece una entrada en la tabla de páginas.

        Args:
            page (int): El número de página virtual a modificar.
            entry (int): El nuevo valor para la entrada de la tabla (marco + flags).
        """
        if 0 <= page < self.num_pages:
            self.page_table[page] = entry

    def handle_page_fault(self, page_number, ui):
        """
        Maneja un fallo de página, actualizando la UI con reacciones.
        
        Args:
            page_number (int): La página virtual que causó el fallo.
            ui (TerminalUI): El objeto de la interfaz para actualizar la reacción.
        """
        ui.set_status(f"-> Fallo de pagina en la pagina {page_number}. Buscando marco...")
        
        if self.occupied_frames < self.num_frames:
            ui.set_reaction("FAULT")
            ui.refresh_screen()
            time.sleep(1.5)
            
            free_frame = self.frame_to_page.index(-1)
            self.page_table[page_number] = free_frame | self.present_bit_mask
            self.frame_to_page[free_frame] = page_number
            self.use_bit[free_frame] = 1
            self.occupied_frames += 1
            
            ui.set_status(f"-> Marco libre {free_frame} encontrado. Asignando pagina {page_number}.")
            ui.refresh_screen()
            time.sleep(1)
            return

        # Caso 2: No hay marcos libres
        ui.set_reaction("REPLACE")
        ui.set_status("-> Memoria llena. Ejecutando algoritmo Clock...")
        ui.refresh_screen()
        time.sleep(1)
        
        while True:
            if self.use_bit[self.clock_pointer] == 0:
                # --- VÍCTIMA ENCONTRADA ---
                ui.set_reaction("VICTIM")
                old_page = self.frame_to_page[self.clock_pointer]
                ui.set_status(f"-> Marco {self.clock_pointer} (pagina {old_page}) es la victima.")
                ui.refresh_screen()
                time.sleep(1.5)
                
                if old_page != -1:
                    self.page_table[old_page] = 0

                self.page_table[page_number] = self.clock_pointer | self.present_bit_mask
                self.frame_to_page[self.clock_pointer] = page_number
                self.use_bit[self.clock_pointer] = 1
                
                self.clock_pointer = (self.clock_pointer + 1) % self.num_frames
                return
            else:
                # --- SEGUNDA OPORTUNIDAD ---
                ui.set_reaction("CHANCE")
                ui.set_status(f"-> Marco {self.clock_pointer} tiene bit de uso 1. Dando segunda oportunidad.")
                
                # Actualiza el estado lógico
                self.use_bit[self.clock_pointer] = 0
                self.clock_pointer = (self.clock_pointer + 1) % self.num_frames
                
                # Refresca la pantalla para MOSTRAR el puntero en su nueva posición
                ui.refresh_screen()
                time.sleep(0.9)

    def virtual_to_physical(self, virtual_address, ui):
        """
        Traduce una dirección virtual a física, actualizando la UI.

        Args:
            virtual_address (int): La dirección virtual a traducir.
            ui (TerminalUI): El objeto de la interfaz para actualizar la reacción.
        
        Returns:
            tuple[int, str]: La dirección física y el estado ('HIT' o 'FAULT').
        """
        page_number = virtual_address >> self.page_size_bits
        offset = virtual_address & self.offset_mask

        if not (0 <= page_number < self.num_pages):
            ui.set_status("\nError: Direccion virtual fuera de rango.")
            ui.refresh_screen()
            return None, "ERROR"

        entry = self.page_table[page_number]

        if (entry & self.present_bit_mask) == 0:
            self.handle_page_fault(page_number, ui)
            entry = self.page_table[page_number]
        else:
            ui.set_reaction("HIT")
        
        frame_number = entry & self.frame_number_mask
        self.use_bit[frame_number] = 1

        return (frame_number << self.page_size_bits) | offset, "OK"

# --- Clase para el Manejo de la Interfaz de Usuario ---
class TerminalUI:
    """
    Gestiona toda la salida a la consola, incluyendo el menú principal,
    las tablas de estado, las reacciones y una línea de estado fija.
    """
    REACTIONS = {
        "IDLE":    "(^.^)",      # Estado Neutral / Esperando
        "HIT":     "(^o^)",      # Acierto de Página
        "FAULT":   "(o_o)",      # Fallo de Página (con espacio libre)
        "REPLACE": "(>_<;)",    # Fallo de Página (memoria llena, necesita reemplazar)
        "CHANCE":  "(^_~)",      # Dando una segunda oportunidad
        "VICTIM":  "(•̀_•́)"       # Víctima encontrada para reemplazo
    }

    def __init__(self, console_width=80):
        self.width = console_width
        self.current_reaction = "IDLE"
        self.status_message = ""

    def set_reaction(self, state):
        """Establece la reacción actual del simulador."""
        if state in self.REACTIONS:
            self.current_reaction = state
            
    def set_status(self, message):
        """Establece el mensaje de estado que se mostrará bajo las tablas."""
        self.status_message = message

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def center_text(self, text):
        spaces = (self.width - len(text)) // 2
        print(" " * max(0, spaces) + text)
        
    def show_main_menu(self):
        """Muestra el menú principal con arte ASCII y retorna la opción del usuario."""
        self.clear_screen()
        print("\n\n")
        self.center_text("==================================================================")
        self.center_text("    __  ___________  _______  ______  __")
        self.center_text("   /  |/  / ____/  |/  / __ \\/ __ \\ \\/ /")
        self.center_text("  / /|_/ / __/ / /|_/ / / / / /_/ /\\  / ")
        self.center_text(" / /  / / /___/ /  / / /_/ / _, _/ / / ")
        self.center_text("/_/  /_/_____/_/  /_/\\____/_/ |_| /_/ ")
        self.center_text("                                       ")
        self.center_text("  __________  ___    _   _______ __    ___  __________  ____")
        self.center_text(" /_  __/ __ \\/   |  / | / / ___// /  /   |/_  __/ __ \\/ __ \\")
        self.center_text("  / / / /_/ / /| | /  |/ /\\__ \\/ / / / || / / / / / / /_/ /")
        self.center_text(" / / / _, _/ ___ |/ /|  /___/ / /___/ ___ |/ / / /_/ / _, _/")
        self.center_text("/_/ /_/ |_/_/  |_/_/ |_//____/_____/_/  |_/_/  \\____/_/ |_|\n")
        self.center_text("==================================================================")
        print("\n")
        self.center_text("\033[1;31m ----MENU PRINCIPAL---- \033[0m")
        self.center_text("===============================")
        self.center_text("Seleccione el modo")
        print()
        self.center_text("1. Interactivo (Por teclado)")
        self.center_text("2. Lectura de archivo")
        self.center_text("3. Salir")
        print()
        self.center_text("===============================")
        return input("Seleccione una opcion: ").strip()

    def show_interactive_menu(self):
        """Muestra el menú para el modo interactivo."""
        print("\n======== Menu de Traductor de Direcciones ========")
        print("1. Mostrar tabla de paginas (se actualiza en vivo).")
        print("2. Ingresar contenido a tabla de paginas.")
        print("3. Traducir direccion virtual a fisica.")
        print("4. Salir al menu principal.")
        return input("Seleccione una opcion: ").strip()
        
    def draw_layout(self):
        """Dibuja el encabezado principal, incluyendo la reacción actual."""
        self.clear_screen()
        reaction_str = self.REACTIONS.get(self.current_reaction, "(?.?)")
        print(f"Simulador de Memoria Virtual {reaction_str}")
        print("=" * 80)

    def update_display(self):
        """Dibuja el estado de las tablas. No limpia la pantalla."""
        print("\n--- Tabla de Paginas ---\t\t\t--- Memoria Fisica (Marcos) ---")
        print(f"{'Pagina':<7} | {'Entrada(Hex)':<12} | {'Binario':<15}\t{'Puntero':<8} | {'Marco':<5} | {'Pagina':<7} | {'Bit Uso':<7}")
        print("-" * 42 + "\t" + "-" * 40)
        
        num_rows = max(translator.num_pages, translator.num_frames)
        total_entry_bits = translator.num_frames_bits + 1

        for i in range(num_rows):
            if i < translator.num_pages:
                entry = translator.page_table[i]
                binary_str = f'{entry:0{total_entry_bits}b}'
                page_str = f"{i:<7} | {entry:<12X} | {binary_str:<15}"
                print(page_str, end='\t')
            else:
                print(" " * 42, end='\t')
            
            if i < translator.num_frames:
                pointer = "👉" if i == translator.clock_pointer else "  "
                page_in_frame = translator.frame_to_page[i]
                page_disp = page_in_frame if page_in_frame != -1 else "Vacio"
                use_bit = translator.use_bit[i] if page_in_frame != -1 else "-"
                frame_str = f"{pointer:<8} | {i:<5} | {page_disp:<7} | {use_bit:<7}"
                print(frame_str)
            else:
                print()
                
    def refresh_screen(self):
        """Limpia y redibuja la pantalla completa, incluyendo el estado."""
        self.draw_layout()
        self.update_display()
        
        # Define una posición fija debajo de las tablas para el mensaje de estado
        num_rows = 0
        if translator: # Asegurarse que translator esté inicializado
             num_rows = max(translator.num_pages, translator.num_frames)
        status_y_pos = 6 + num_rows + 2  # 6 líneas de cabecera/espacio
        
        # Usamos secuencias ANSI para posicionar el cursor y limpiar la línea
        print(f"\033[{status_y_pos};0H", end="") # Mover cursor
        print("\033[K", end="") # Limpiar la línea
        print(self.status_message)

# --- Funciones de Flujo del Programa ---
def run_interactive_mode():
    """Ejecuta el bucle principal para el modo interactivo por teclado."""
    global translator
    ui = TerminalUI()
    try:
        phys_mem = int(input("Ingrese el tamano de la memoria fisica: "))
        virt_mem = int(input("Ingrese el tamano de la memoria virtual: "))
        page_sz = int(input("Ingrese el tamano de pagina: "))
        translator = AddressTranslator(phys_mem, virt_mem, page_sz)
    except (ValueError, TypeError) as e:
        print(f"Error en la entrada: {e}")
        time.sleep(2)
        return

    while True:
        ui.set_reaction("IDLE")
        ui.set_status("") # Limpia el mensaje de estado al inicio de cada ciclo
        ui.refresh_screen()
        option = ui.show_interactive_menu()

        if option == '2':
            try:
                page = int(input(f"Ingrese numero de pagina (0-{translator.num_pages - 1}): "))
                entry_str = input(f"Ingrese contenido para la pagina {page} (decimal o 0xHEX): ")
                entry = int(entry_str, 0)
                translator.set_page_table_entry(page, entry)
                ui.set_status("Entrada actualizada.")
            except (ValueError, TypeError):
                ui.set_status("Entrada invalida.")
        
        elif option == '3':
            try:
                v_addr_str = input("Ingrese direccion virtual (en hexadecimal): ")
                v_addr = int(v_addr_str, 16)
                p_addr, status = translator.virtual_to_physical(v_addr, ui)
                
                ui.refresh_screen()
                
                if status != "ERROR":
                    ui.set_status(f"Direccion Fisica: {p_addr:X}")
                    ui.refresh_screen()

            except (ValueError, TypeError):
                ui.set_status("Direccion invalida.")

        elif option == '4':
            print("Volviendo al menu principal...")
            time.sleep(1)
            break
        
        input("\nPresione Enter para continuar...")

def run_file_mode():
    """Ejecuta la lógica para leer y procesar un archivo de comandos."""
    global translator
    ui = TerminalUI()
    filename = input("Ingrese el nombre del archivo (ej: prueba.txt): ")
    try:
        with open(filename, 'r') as f:
            # Leer configuración inicial
            phys_mem, virt_mem, page_sz = map(int, f.readline().split())
            translator = AddressTranslator(phys_mem, virt_mem, page_sz)
            print("Traductor inicializado desde archivo.")
            ui.refresh_screen()
            time.sleep(2)

            # Procesar comandos
            for line in f:
                parts = line.strip().split()
                if not parts or parts[0].startswith('#'): continue
                command = parts[0].upper()

                if command == "PAGE":
                    page, entry = int(parts[1], 16), int(parts[2], 16)
                    translator.set_page_table_entry(page, entry)
                    ui.set_status(f"Cargando Pagina {page:X} con entrada {entry:X}")
                
                elif command == "TRANS":
                    v_addr = int(parts[1], 16)
                    ui.set_status(f"Traduciendo direccion virtual {v_addr:X}...")
                    p_addr, status = translator.virtual_to_physical(v_addr, ui)
                    if status != "ERROR":
                         ui.set_status(f"Direccion Fisica: {p_addr:X}")
                
                elif command == "SHOWTABLE":
                    ui.set_status("--- Estado Actual de la Memoria ---")
                
                ui.refresh_screen()
                time.sleep(1)
        
        input("\nProcesamiento del archivo finalizado. Presione Enter para volver al menu.")

    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo '{filename}'")
        time.sleep(2)
    except Exception as e:
        print(f"Ocurrio un error al procesar el archivo: {e}")
        time.sleep(2)

# --- Bucle Principal del Programa ---
if __name__ == "__main__":
    """Punto de entrada principal del script."""
    ui = TerminalUI()
    while True:
        choice = ui.show_main_menu()
        if choice == '1':
            run_interactive_mode()
        elif choice == '2':
            run_file_mode()
        elif choice == '3':
            print("Saliendo del programa.")
            break
        else:
            print("Opcion invalida, por favor intente de nuevo.")

            time.sleep(1)
