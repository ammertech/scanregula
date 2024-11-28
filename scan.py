import ctypes
from ctypes import c_uint32, c_int, POINTER, byref
import os

# Set environment variable for logging
os.environ["REGULA_LOG"] = "1"

# Path to SDK library
LIBRARY_PATH = "/usr/lib/regula/sdk/libPasspR40.so"

# Command constants
RPRM_COMMAND_DEVICE_COUNT = 0x01
RPRM_COMMAND_DEVICE_CONNECT = 0x04
RPRM_COMMAND_DEVICE_DISCONNECT = 0x06
RPRM_COMMAND_PROCESS = 0x10

# Define Result Types
RESULT_TYPE_RAWIMAGE = 0x00000001 

def load_library(path):
    try:
        lib = ctypes.CDLL(path)
        print("SDK library successfully loaded")
        return lib
    except OSError as e:
        raise RuntimeError(f"Error loading SDK library: {e}")

def initialize_sdk(lib):
    try:
        init_func = lib._Initialize
        init_func.restype = c_int
        result = init_func()
        print(f"Initialize result: {result}")
        return result == 0
    except Exception as e:
        print(f"Error initializing SDK: {e}")
        return False

def execute_command(lib, command, in_param=None, out_param=None):
    try:
        cmd_func = lib._ExecuteCommand
        cmd_func.restype = c_int
        cmd_func.argtypes = [c_int, c_int, POINTER(c_int)]
        
        in_param_value = 0 if in_param is None else in_param
        out_param_value = c_int(0) if out_param is None else out_param
        
        result = cmd_func(command, in_param_value, byref(out_param_value))
        print(f"Command 0x{command:02X} result: {result}")
        
        if result == 0:
            return out_param_value.value
        return None
    except Exception as e:
        print(f"Error executing command: {e}")
        return None

def start_scan(lib):
    try:
        print("\nStarting scan process...")
        result = execute_command(lib, RPRM_COMMAND_PROCESS)
        if result is not None:
            print("Scan command sent successfully")
            return True
        return False
    except Exception as e:
        print(f"Error while scanning: {e}")
        return False

def main():
    try:
        print("REGULA_LOG is enabled")
        
        # Load SDK
        lib = ctypes.CDLL(LIBRARY_PATH)
        print("SDK library successfully loaded")
        
        # Initialize SDK
        if not initialize_sdk(lib):
            return
        
        # Count devices
        count = execute_command(lib, RPRM_COMMAND_DEVICE_COUNT)
        print(f"Devices found: {count if count is not None else 0}")
        
        if count and count > 0:
            # Connect to scanner
            connect_result = execute_command(lib, RPRM_COMMAND_DEVICE_CONNECT, -1)
            if connect_result is not None:
                print("Scanner connected")
                
                # Start scan
                start_scan(lib)
                
                # Disconnect scanner
                execute_command(lib, RPRM_COMMAND_DEVICE_DISCONNECT)
                print("Scanner disconnected")
        
        # Free SDK
        free_func = lib._Free
        free_func.restype = c_int
        result = free_func()
        print(f"Free result: {result}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
