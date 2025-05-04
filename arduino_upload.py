import os
import time
import subprocess
import serial

from arduino_utils import find_avrdude, is_avrdude_available
from arduino_config import HEX_DIR

def upload_hex_direct(port, hex_file, baudrate=115200):
    """Upload a hex file to an Arduino using direct serial communication.
    This is a simplified version that works for basic Arduino uploads when avrdude is not available.
    
    Note: This is a fallback method and may not work for all Arduino boards.
    """
    try:
        # Read the hex file
        with open(hex_file, 'r') as f:
            hex_data = f.read()
        
        # Open serial connection
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Allow time for Arduino to reset
        
        # Send the hex data
        ser.write(hex_data.encode())
        ser.flush()
        
        # Close the connection
        ser.close()
        
        print(f"Hex file sent to {port}.")
        return True
    except Exception as e:
        print(f"Error during direct upload: {str(e)}")
        return False

def upload_hex(port, hex_file, is_updi=False):
    """Upload a hex file to an Arduino."""
    # Check if the hex file exists
    if not os.path.exists(hex_file):
        print(f"Error: Hex file not found at {hex_file}")
        return False
    
    # Get avrdude path
    avrdude_path = find_avrdude()
    
    # If avrdude is not available, try direct upload
    if not avrdude_path:
        print("Warning: avrdude not found in system path or Arduino installation.")
        print("Attempting direct upload method (limited functionality).")
        return upload_hex_direct(port, hex_file)
        
    # Verify the port exists and is available
    try:
        # Try to open the port briefly to check if it's available
        ser = serial.Serial(port, 9600, timeout=1)
        ser.close()
        print(f"Port {port} is available.")
    except serial.SerialException as e:
        print(f"Error: Could not open port {port}. {str(e)}")
        print("Please check if the Arduino is properly connected and the port is correct.")
        return False
    
    try:
        # Find avrdude.conf
        avrdude_dir = os.path.dirname(avrdude_path)
        avrdude_conf = os.path.join(os.path.dirname(avrdude_dir), "etc", "avrdude.conf")
        
        # If avrdude.conf doesn't exist in the expected location, try to find it
        if not os.path.exists(avrdude_conf):
            # Try common locations
            possible_conf_locations = [
                os.path.join(avrdude_dir, "avrdude.conf"),
                os.path.join(os.path.dirname(avrdude_dir), "etc", "avrdude.conf"),
                os.path.join(os.path.dirname(os.path.dirname(avrdude_dir)), "etc", "avrdude.conf")
            ]
            
            for conf_location in possible_conf_locations:
                if os.path.exists(conf_location):
                    avrdude_conf = conf_location
                    break
        
        if is_updi:
            # For UPDI upload (ATtiny1616)
            cmd = [
                avrdude_path, 
                "-C", avrdude_conf, 
                "-v", 
                "-p", "attiny1614",  # ATtiny1616 uses the same parameters as ATtiny1614
                "-c", "jtag2updi", 
                "-P", port, 
                "-U", f"flash:w:{hex_file}:i"
            ]
        else:
            # For regular Arduino upload (e.g., Arduino Uno)
            cmd = [
                avrdude_path, 
                "-C", avrdude_conf, 
                "-v", 
                "-p", "atmega328p",  # Arduino Uno uses ATmega328P
                "-c", "arduino", 
                "-P", port, 
                "-b", "115200", 
                "-D", 
                "-U", f"flash:w:{hex_file}:i"
            ]
        
        print(f"Using avrdude at: {avrdude_path}")
        print(f"Using configuration: {avrdude_conf}")
        print(f"Command: {' '.join(cmd)}")
        
        print(f"\nUploading {hex_file} to Arduino at {port}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Upload successful!")
            return True
        else:
            print(f"Upload failed with return code: {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
            return False
    
    except FileNotFoundError:
        print("Error: avrdude executable not found.")
        print("Please install avrdude or ensure it's in your system PATH.")
        return False
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        return False
