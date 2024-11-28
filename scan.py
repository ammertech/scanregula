import ctypes
from ctypes import c_uint32, c_int, POINTER, byref
import time

# Pfad zur SDK-Bibliothek
LIBRARY_PATH = "/usr/lib/regula/sdk/libPasspR40.so"

# Kommando Konstanten
RPRM_COMMAND_DEVICE_COUNT = 0x01
RPRM_COMMAND_DEVICE_CONNECT = 0x04
RPRM_COMMAND_DEVICE_DISCONNECT = 0x06
RPRM_COMMAND_PROCESS = 0x10

def load_library(path):
    try:
        lib = ctypes.CDLL(path)
        print("SDK-Bibliothek erfolgreich geladen.")
        return lib
    except OSError as e:
        raise RuntimeError(f"Fehler beim Laden der SDK-Bibliothek: {e}")

def initialize_sdk(lib):
    try:
        init_func = lib._Initialize
        init_func.restype = c_int
        result = init_func()
        print(f"Initialize Ergebnis: {result}")
        return result == 0
    except Exception as e:
        print(f"Fehler bei der SDK-Initialisierung: {e}")
        return False

def execute_command(lib, command, in_param=None, out_param=None):
    try:
        cmd_func = lib._ExecuteCommand
        cmd_func.restype = c_int
        cmd_func.argtypes = [c_int, c_int, POINTER(c_int)]
        
        in_param_value = 0 if in_param is None else in_param
        out_param_value = c_int(0) if out_param is None else out_param
        
        result = cmd_func(command, in_param_value, byref(out_param_value))
        print(f"Befehl 0x{command:02X} Ergebnis: {result}")
        
        if result == 0:
            return out_param_value.value
        return None
    except Exception as e:
        print(f"Fehler beim Ausführen des Befehls: {e}")
        return None

def start_scan(lib):
    try:
        print("\nStarte Scan-Vorgang...")
        result = execute_command(lib, RPRM_COMMAND_PROCESS)
        if result is not None:
            print("Scan-Befehl erfolgreich gesendet.")
            return True
        return False
    except Exception as e:
        print(f"Fehler beim Scannen: {e}")
        return False

def main():
    try:
        # SDK laden
        lib = ctypes.CDLL(LIBRARY_PATH)
        print("SDK-Bibliothek erfolgreich geladen.")
        
        # SDK initialisieren
        if not initialize_sdk(lib):
            return
        
        # Geräte zählen
        count = execute_command(lib, RPRM_COMMAND_DEVICE_COUNT)
        print(f"Gefundene Geräte: {count if count is not None else 0}")
        
        if count and count > 0:
            # Mit Scanner verbinden
            connect_result = execute_command(lib, RPRM_COMMAND_DEVICE_CONNECT, -1)
            if connect_result is not None:
                print("Scanner verbunden")
                
                # Direkt Scan starten
                start_scan(lib)
                
                # Kurz warten
                time.sleep(2)
                
                # Scanner trennen
                execute_command(lib, RPRM_COMMAND_DEVICE_DISCONNECT)
                print("Scanner getrennt")
        
        # SDK freigeben
        free_func = lib._Free
        free_func.restype = c_int
        result = free_func()
        print(f"Free Ergebnis: {result}")
        
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    main()
