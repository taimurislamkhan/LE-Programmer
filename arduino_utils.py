import os
import sys
import platform
import shutil
import serial
import serial.tools.list_ports

def find_avrdude():
    """Find avrdude executable, first in PATH, then in common Arduino installation locations."""
    # First check if it's in the system PATH
    avrdude_path = shutil.which("avrdude")
    
    if avrdude_path:
        return avrdude_path
    
    # Check common Arduino installation locations
    if platform.system() == "Windows":
        common_locations = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Arduino", "hardware", "tools", "avr", "bin", "avrdude.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Arduino", "hardware", "tools", "avr", "bin", "avrdude.exe")
        ]
    elif platform.system() == "Darwin":  # macOS
        common_locations = [
            "/Applications/Arduino.app/Contents/Java/hardware/tools/avr/bin/avrdude",
            os.path.expanduser("~/Applications/Arduino.app/Contents/Java/hardware/tools/avr/bin/avrdude")
        ]
    else:  # Linux and others
        common_locations = [
            "/usr/bin/avrdude",
            "/usr/local/bin/avrdude"
        ]
    
    for location in common_locations:
        if os.path.exists(location):
            return location
    
    return None

def is_avrdude_available():
    """Check if avrdude is available in the system path or Arduino installation."""
    return find_avrdude() is not None

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def find_arduino_ports():
    """Find all connected Arduino devices."""
    arduino_ports = []
    
    for port in serial.tools.list_ports.comports():
        # Arduino devices typically have "Arduino" or "CH340" in their description
        # or they might have a USB VID:PID that matches known Arduino boards
        if ("Arduino" in port.description or 
            "CH340" in port.description or 
            "USB Serial" in port.description or
            "USB2.0-Serial" in port.description):
            arduino_ports.append({
                "port": port.device,
                "description": port.description
            })
    
    return arduino_ports
