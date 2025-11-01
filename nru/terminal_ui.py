import os
import time
from mmu import MMU
from nru import NRU

# --- Clase para el Manejo de la Interfaz de Usuario ---
class TerminalUI:
    """
    Gestiona toda la salida a la consola con NRU
    """
    REACTIONS = {
        "IDLE":    "(^.^)",      # Estado Neutral / Esperando
        "HIT":     "(^o^)",      # Acierto de Página
        "FAULT":   "(o_o)",      # Fallo de Página
        "REPLACE": "(>_<;)",     # Reemplazo de página con NRU
        "VICTIM":  "(•̀_•́)"       # Víctima encontrada
    }

    def __init__(self, console_width=80):
        self.width = console_width
        self.current_reaction = "IDLE"
        self.status_message = ""
        self.mmu = None
        self.nru = None

    def set_mmu_nru(self, mmu, nru):
        """Establece las instancias de MMU y NRU"""
        self.mmu = mmu
        self.nru = nru

    def set_reaction(self, state):
        """Establece la reacción actual del simulador."""
        if state in self.REACTIONS:
            self.current_reaction = state
            
    def set_status(self, message):
        """Establece el mensaje de estado."""
        self.status_message = message

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def center_text(self, text):
        spaces = (self.width - len(text)) // 2
        print(" " * max(0, spaces) + text)
        
    def show_main_menu(self):
        """Muestra el menú principal"""
        self.clear_screen()
        print("\n\n")
        self.center_text("╔════════════════════════════════════════════════════════════════╗")
        self.center_text("║    ███████╗██╗███╗   ███╗██╗   ██╗██╗      █████╗ ██████╗     ║")
        self.center_text("║    ██╔════╝██║████╗ ████║██║   ██║██║     ██╔══██╗██╔══██╗    ║")
        self.center_text("║    ███████╗██║██╔████╔██║██║   ██║██║     ███████║██║  ██║    ║")
        self.center_text("║    ╚════██║██║██║╚██╔╝██║██║   ██║██║     ██╔══██║██║  ██║    ║")
        self.center_text("║    ███████║██║██║ ╚═╝ ██║╚██████╔╝███████╗██║  ██║██████╔╝    ║")
        self.center_text("║    ╚══════╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═════╝     ║")
        self.center_text("║                                                               ║")
        self.center_text("║           ███╗   ██╗██████╗ ██╗   ██╗                         ║")
        self.center_text("║           ████╗  ██║██╔══██╗██║   ██║                         ║")
        self.center_text("║           ██╔██╗ ██║██████╔╝██║   ██║                         ║")
        self.center_text("║           ██║╚██╗██║██╔══██╗██║   ██║                         ║")
        self.center_text("║           ██║ ╚████║██║  ██║╚██████╔╝                         ║")
        self.center_text("║           ╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝                          ║")
        self.center_text("║                                                               ║")
        self.center_text("║           NOT RECENTLY USED PAGE REPLACEMENT                  ║")
        self.center_text("╚════════════════════════════════════════════════════════════════╝")
        print("\n")
        self.center_text("\033[1;31m ---- MENU PRINCIPAL ---- \033[0m")
        self.center_text("===============================")
        self.center_text("1. Iniciar Sistema (Cargar tabla de páginas)")
        self.center_text("2. Salir")
        print()
        self.center_text("===============================")
        return input("Seleccione una opcion: ").strip()

    def show_system_menu(self):
        """Muestra el menú del sistema cargado"""
        print("\n======== SISTEMA DE MEMORIA VIRTUAL - NRU ========")
        print("1. Traducir dirección virtual a física")
        print("2. Mostrar estado actual")
        print("3. Volver al menu principal")
        return input("Seleccione una opcion: ").strip()
        
    def draw_layout(self):
        """Dibuja el encabezado principal"""
        self.clear_screen()
        reaction_str = self.REACTIONS.get(self.current_reaction, "(?.?)")
        print(f"Simulador NRU {reaction_str} - Algoritmo Not Recently Used")
        print("=" * 80)

    def update_display(self):
        """Dibuja el estado de las tablas usando MMU"""
        if not self.mmu:
            return
            
        print("\n--- TABLA DE PÁGINAS ---\t\t\t--- MEMORIA FÍSICA (MARCOS) ---")
        print(f"{'Pág':<4} | {'Hex':<4} | {'Binario':<12}\t\t\t{'Marco':<5} | {'Página':<6} | R|M")
        print("-" * 42 + "\t" + "-" * 25)
        
        num_rows = max(self.mmu.num_pages, self.mmu.num_frames)

        for i in range(num_rows):
            # Mostrar tabla de páginas
            if i < self.mmu.num_pages:
                entry = self.mmu.page_table[i]
                binary_str = self.mmu.print_binary(entry, 8)
                hex_val = f"{entry:02X}"

                page_str = f"{i:<4} | {hex_val:<4} | {binary_str:<12} "
                print(page_str, end="\t\t\t")
            else:
                print(" " * 50, end="\t\t\t")
            
            # Mostrar tabla de marcos
            if i < self.mmu.num_frames:
                page_in_frame = self.mmu.get_page_from_frame(i)
                if page_in_frame != -1:
                    r_bit = "1" if self.mmu.get_reference_bit(page_in_frame) else "0"
                    m_bit = "1" if self.mmu.get_modified_bit(page_in_frame) else "0"
                    frame_str = f"{i:<5} | {page_in_frame:<6} | {r_bit}|{m_bit}"
                else:
                    frame_str = f"{i:<5} | {'Libre':<6} | -|-"
                print(frame_str)
            else:
                print()
                
    def refresh_screen(self):
        """Limpia y redibuja la pantalla completa"""
        self.draw_layout()
        self.update_display()
        print(f"\n{self.status_message}")

    def virtual_to_physical_with_nru(self, virtual_address):
        """Traducción con manejo de fallos de página usando NRU"""
        if not self.mmu:
            return None, "ERROR"
            
        # Convertir dirección virtual a física
        phys_addr = self.mmu.virtual_to_physical(virtual_address)
        
        if phys_addr is not None:
            self.set_reaction("HIT")
            return phys_addr, "HIT"
        else:
            # Fallo de página - usar NRU para seleccionar víctima
            self.set_reaction("FAULT")
            page_num = virtual_address // self.mmu.page_size
            
            # Verificar si hay marcos libres primero
            free_frames = self.mmu.get_free_frames()
            if free_frames:
                # Usar marco libre
                frame = free_frames[0]
                self.mmu.allocate_frame(frame, page_num)
                self.set_status(f"Fallo de página - Marco libre {frame} asignado a página {page_num}")
            else:
                # No hay marcos libres - usar NRU para reemplazo
                victim_page = self.nru.select_victim(self.mmu)
                
                if victim_page is not None:
                    self.set_reaction("VICTIM")
                    victim_frame = self.mmu.get_frame_number(victim_page)
                    
                    # Mostrar información de la víctima
                    victim_r = self.mmu.get_reference_bit(victim_page)
                    victim_m = self.mmu.get_modified_bit(victim_page)
                    self.set_status(f"NRU selecciona víctima: Página {victim_page} (R={victim_r}, M={victim_m}) en Marco {victim_frame}")
                    
                    # Liberar marco de la víctima
                    self.mmu.free_frame(victim_frame)
                    
                    # Asignar marco a la nueva página
                    self.mmu.allocate_frame(victim_frame, page_num)
                    self.set_reaction("REPLACE")
                else:
                    self.set_status("Error: No se pudo encontrar víctima para reemplazo")
                    return None, "ERROR"
            
            # Reintentar acceso
            phys_addr = self.mmu.virtual_to_physical(virtual_address)
            if phys_addr:
                return phys_addr, "REPLACE"
            
            return None, "ERROR"

    def load_config_and_page_table(self):
        """Carga la configuración y tabla de páginas desde archivo"""
        filename = input("Ingrese el nombre del archivo con la configuración y tabla de páginas: ")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                # Leer configuración (primera línea)
                config_line = f.readline().strip()
                phys_mem, virt_mem, page_sz = map(int, config_line.split())
                
                # Crear MMU y NRU con la configuración del archivo
                self.mmu = MMU(phys_mem, virt_mem, page_sz)
                self.nru = NRU(reset_interval=5)
                
                # Mostrar configuración cargada
                self.set_status(f"Configuración cargada: MemFísica={phys_mem}B, MemVirtual={virt_mem}B, Página={page_sz}B")
                self.refresh_screen()
                time.sleep(2)
                
                # Cargar tabla de páginas
                lines_loaded = 0
                for line in f:
                    parts = line.strip().split()
                    if not parts or parts[0].startswith('#'):
                        continue
                    if parts[0].upper() == "PAGE":
                        page = int(parts[1])
                        entry = int(parts[2])
                        self.mmu.set_page_table(page, entry)
                        
                        # Actualizar tabla de marcos si está presente
                        if self.mmu.get_present_bit(page):
                            frame = self.mmu.get_frame_number(page)
                            self.mmu.set_frame_table(frame, page)
                            
                        lines_loaded += 1
                        self.set_status(f"Cargando página {page} -> {entry:02X}h")
                        self.refresh_screen()
                        time.sleep(0.3)
                
                self.set_status(f"✓ Sistema inicializado: {lines_loaded} páginas cargadas")
                return True
                
        except FileNotFoundError:
            self.set_status(f"✗ Error: No se encontró el archivo '{filename}'")
            return False
        except ValueError as e:
            self.set_status(f"✗ Error en formato del archivo: {e}")
            return False
        except Exception as e:
            self.set_status(f"✗ Error al cargar archivo: {e}")
            return False