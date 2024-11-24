import ctypes
from ctypes import c_uint32, c_int, Structure, c_char, POINTER, byref, c_void_p, c_byte

# Pfad zur SDK-Bibliothek
LIBRARY_PATH = "/usr/lib/regula/sdk/libPasspR40.so"

# Kommando Konstanten
RPRM_COMMAND_DEVICE_COUNT = 0x00000001
RPRM_COMMAND_DEVICE_CONNECT = 0x00000004
RPRM_COMMAND_DEVICE_DISCONNECT = 0x00000006
RPRM_COMMAND_PROCESS = 0x00000010            # Scan und Verarbeitung starten

# Result Types
class RPRM_ResultType:
    EMPTY = 0
    RAW_IMAGE = 1
    FILE_IMAGE = 2
    MRZ_OCR_EXTENDED = 3
    BARCODES = 5
    GRAPHICS = 6
    DEVICE_INFO = 31

# Result Container Struktur
class TResultContainer(Structure):
    _fields_ = [
        ("result_type", c_uint32),
        ("light", c_uint32),
        ("buf_length", c_uint32),
        ("buffer", c_void_p),
        ("XML_length", c_uint32),
        ("XML_buffer", POINTER(c_byte)),
        ("list_idx", c_uint32),
        ("page_idx", c_uint32)
    ]

def load_library(path):
    try:
        lib = ctypes.CDLL(path)
        print("SDK-Bibliothek erfolgreich geladen.")
        return lib
    except OSError as e:
        raise RuntimeError(f"Fehler beim Laden der SDK-Bibliothek: {e}")

def initialize_sdk(lib):
    try:
        init_func = get_function(lib, "_Initialize", c_int)
        result = init_func()
        if result != 0:
            raise RuntimeError(f"Fehler bei der SDK-Initialisierung: {result}")
        print("SDK erfolgreich initialisiert.")
    except Exception as e:
        raise RuntimeError(f"Fehler bei der SDK-Initialisierung: {e}")

def free_sdk(lib):
    try:
        free_func = get_function(lib, "_Free", c_int)
        result = free_func()
        if result != 0:
            raise RuntimeError(f"Fehler beim Freigeben des SDK: {result}")
        print("SDK erfolgreich freigegeben.")
    except Exception as e:
        raise RuntimeError(f"Fehler beim Freigeben des SDK: {e}")

def get_function(lib, func_name, restype, argtypes=None):
    try:
        func = getattr(lib, func_name)
        func.restype = restype
        if argtypes:
            func.argtypes = argtypes
        return func
    except AttributeError as e:
        raise RuntimeError(f"Fehler: Funktion '{func_name}' nicht in der Bibliothek gefunden: {e}")

def execute_command(lib, command, in_param=None, out_param=None):
    command_func = get_function(lib, "_ExecuteCommand", c_int, [c_int, c_int, POINTER(c_int)])
    
    in_param_value = 0 if in_param is None else in_param
    out_param_value = c_int(0) if out_param is None else out_param
    
    result = command_func(command, in_param_value, byref(out_param_value))
    if result != 0:
        raise RuntimeError(f"Fehler bei der Ausführung des Befehls {hex(command)}: {result}")
    
    return out_param_value.value

def process_scan(lib):
    try:
        # Result Container vorbereiten
        result_container = TResultContainer()
        result_container.result_type = RPRM_ResultType.RAW_IMAGE  # Wir erwarten ein Raw Image
        
        # Scan-Prozess starten
        print("\nStarte Scan-Vorgang...")
        
        # Process Befehl ausführen mit Result Container als Output
        command_func = get_function(lib, "_ExecuteCommand", c_int, 
                                  [c_int, c_int, POINTER(TResultContainer)])
        
        result = command_func(RPRM_COMMAND_PROCESS, 0, byref(result_container))
        
        if result != 0:
            raise RuntimeError(f"Fehler beim Scannen: {result}")
        
        print("Scan abgeschlossen!")
        print(f"Result Type: {result_container.result_type}")
        print(f"Buffer Length: {result_container.buf_length}")
        print(f"Light Schema: 0x{result_container.light:08X}")
        
        return result_container
        
    except Exception as e:
        print(f"Fehler beim Scan-Vorgang: {e}")
        return None

def get_device_count(lib):
    count = c_int(0)
    return execute_command(lib, RPRM_COMMAND_DEVICE_COUNT, None, count)

def connect_device(lib, device_index):
    return execute_command(lib, RPRM_COMMAND_DEVICE_CONNECT, device_index)

def disconnect_device(lib):
    return execute_command(lib, RPRM_COMMAND_DEVICE_DISCONNECT)

def get_sdk_version(lib):
    version_func = get_function(lib, "_LibraryVersion", c_uint32)
    version = version_func()
    major_version = (version >> 16) & 0xFFFF
    minor_version = version & 0xFFFF
    return major_version, minor_version

def main():
    sdk_library = None
    try:
        # SDK laden
        sdk_library = load_library(LIBRARY_PATH)
        
        # SDK initialisieren
        initialize_sdk(sdk_library)
        
        # SDK-Version ausgeben
        major, minor = get_sdk_version(sdk_library)
        print(f"SDK-Version: {major}.{minor}")
        
        # Anzahl der verbundenen Geräte abrufen
        device_count = get_device_count(sdk_library)
        print(f"Gefundene Geräte: {device_count}")
        
        if device_count > 0:
            # Mit dem ersten gefundenen Gerät verbinden
            connect_device(sdk_library, 0)
            print("Erfolgreich mit dem Scanner verbunden!")
            
            # Scan durchführen
            result = process_scan(sdk_library)
            
            # Gerät wieder trennen
            disconnect_device(sdk_library)
            print("Scanner getrennt.")
        else:
            print("Keine Geräte gefunden!")

    except RuntimeError as e:
        print(e)
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
    finally:
        # SDK freigeben, wenn es initialisiert wurde
        if sdk_library:
            try:
                free_sdk(sdk_library)
            except Exception as e:
                print(f"Fehler beim Freigeben des SDK: {e}")

if __name__ == "__main__":
    main()
