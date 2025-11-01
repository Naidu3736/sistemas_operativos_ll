import sys
from mmu import MMU
from nru import NRU
from terminal_ui import TerminalUI
import time


# --- Funciones de Flujo del Programa ---
def run_system_mode():
    """Ejecuta el sistema cargado con tabla de páginas"""
    ui = TerminalUI()
    
    # Cargar configuración y tabla de páginas desde archivo
    if not ui.load_config_and_page_table():
        input("\nPresione Enter para continuar...")
        return
        
    # Bucle principal del sistema cargado
    while True:
        ui.set_reaction("IDLE")
        ui.refresh_screen()
        option = ui.show_system_menu()

        if option == '1':
            # Traducir dirección virtual
            try:
                v_addr_str = input("\nIngrese dirección virtual (hexadecimal, ej: 100, 200, 300): ")
                v_addr = int(v_addr_str, 16)
                
                page_num = v_addr // ui.mmu.page_size
                offset = v_addr % ui.mmu.page_size
                ui.set_status(f"Dirección virtual: 0x{v_addr:03X}h -> Página: {page_num}, Offset: 0x{offset:02X}h")
                ui.refresh_screen()
                time.sleep(1)
                
                # Realizar traducción
                p_addr, status = ui.virtual_to_physical_with_nru(v_addr)
                ui.refresh_screen()
                
                if status != "ERROR":
                    ui.set_status(f"✓ {status} - Dirección física: 0x{p_addr:03X}h (Marco: 0x{p_addr//ui.mmu.page_size:X}, Offset: 0x{p_addr%ui.mmu.page_size:02X}h)")
                else:
                    ui.set_status("✗ Error: No se pudo traducir la dirección")

            except (ValueError, TypeError):
                ui.set_status("✗ Error: Dirección inválida")

        elif option == '2':
            # Mostrar estado actual
            present_pages = ui.mmu.get_present_pages()
            free_frames = ui.mmu.get_free_frames()
            ui.set_status(f"Estado: {len(present_pages)} páginas en memoria, {len(free_frames)} marcos libres, Contador NRU: {ui.nru.reference_count}")
            ui.refresh_screen()

        elif option == '3':
            print("Volviendo al menu principal...")
            time.sleep(1)
            break
        
        else:
            ui.set_status("Opción inválida")
        
        input("\nPresione Enter para continuar...")

# --- Bucle Principal del Programa ---
if __name__ == "__main__":
    """Punto de entrada principal del script."""
    ui = TerminalUI()
    while True:
        choice = ui.show_main_menu()
        if choice == '1':
            run_system_mode()
        elif choice == '2':
            print("Saliendo del programa.")
            break
        else:
            print("Opción inválida, por favor intente de nuevo.")
            time.sleep(1)