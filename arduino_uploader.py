import os
import subprocess
import sys
import json
import serial
import serial.tools.list_ports
import time
import shutil

class ArduinoUploader:
    def __init__(self):
        # Paths to Arduino tools
        self.avrdude_path = self._find_avrdude_path()
        self.avrdude_conf = self._find_avrdude_conf()
        
    def _find_avrdude_path(self):
        """Find avrdude executable path."""
        possible_paths = [
            # DxCore paths
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Arduino15', 'packages', 'DxCore', 'tools', 'avrdude', '6.3.0-arduino17or18', 'bin', 'avrdude.exe'),
            # MegaTinyCore paths
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Arduino15', 'packages', 'megaTinyCore', 'tools', 'avrdude', '6.3.0-arduino17or18', 'bin', 'avrdude.exe'),
            # Arduino AVR paths
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Arduino15', 'packages', 'arduino', 'tools', 'avrdude', '6.3.0-arduino17', 'bin', 'avrdude.exe'),
            # Standard Arduino installation paths
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Arduino', 'hardware', 'tools', 'avr', 'bin', 'avrdude.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Arduino', 'hardware', 'tools', 'avr', 'bin', 'avrdude.exe')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _find_avrdude_conf(self):
        """Find avrdude.conf file."""
        if not self.avrdude_path:
            return None
            
        # First check in the same directory as avrdude
        avrdude_dir = os.path.dirname(self.avrdude_path)
        conf_path = os.path.join(avrdude_dir, 'avrdude.conf')
        if os.path.exists(conf_path):
            return conf_path
            
        # Check in parent directory's etc folder
        conf_path = os.path.join(os.path.dirname(avrdude_dir), 'etc', 'avrdude.conf')
        if os.path.exists(conf_path):
            return conf_path
            
        # Check MegaTinyCore specific location
        conf_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Arduino15', 'packages', 'megaTinyCore', 'hardware', 'megaavr', '2.6.10', 'avrdude.conf')
        if os.path.exists(conf_path):
            return conf_path
            
        return None
    
    def find_arduino_ports(self):
        """Find all connected Arduino devices."""
        arduino_ports = []
        ports = list(serial.tools.list_ports.comports())
        
        for port in ports:
            # Arduino boards typically have "Arduino" or "CH340" in their description
            arduino_ports.append({
                "port": port.device,
                "description": port.description,
                "hwid": port.hwid
            })
        
        return arduino_ports
    
    def upload_to_attiny1616(self, hex_file, port, fuse_settings=None, verbose=True):
        """Upload a hex file to an ATtiny1616 using UPDI programmer."""
        if not self.avrdude_path:
            print("Error: avrdude not found. Please install Arduino IDE with megaTinyCore.")
            return False
            
        if not self.avrdude_conf:
            print("Error: avrdude.conf not found.")
            return False
            
        if not os.path.exists(hex_file):
            print(f"Error: Hex file {hex_file} not found.")
            return False
            
        # Verify the port exists
        try:
            # Try to open the port briefly to check if it's available
            ser = serial.Serial(port, 115200, timeout=1)
            ser.close()
            print(f"Port {port} is available.")
        except serial.SerialException as e:
            print(f"Error: Could not open port {port}. {str(e)}")
            print("Please check if the Arduino is properly connected and the port is correct.")
            return False
            
        # Default fuse settings for ATtiny1616 with 20MHz clock
        if fuse_settings is None:
            fuse_settings = {
                "fuse0": "0b00000000",  # APPEND disabled, BOOTEND = 0
                "fuse2": "0x02",        # OSCLOCK disabled, EESAVE disabled, BODCFG = 2
                "fuse5": "0b11000101",  # 20MHz oscillator, RUNSTDBY disabled, STARTUP = 1 (16ms)
                "fuse6": "0x04",        # SYSCFG0 = 0x04 (default)
                "fuse7": "0x00",        # SYSCFG1 = 0x00 (default)
                "fuse8": "0x00"         # BOOTSIZE = 0 (default)
            }
            
        # Build the avrdude command
        cmd = [
            self.avrdude_path,
            f"-C{self.avrdude_conf}",
            "-v",                    # Verbose output
            "-V",                    # Disable auto-verify
            "-pattiny1616",          # Target device
            "-cjtag2updi",           # Programmer type (UPDI)
            f"-P{port}",             # Serial port
            "-b115200"               # Baud rate
        ]
        
        # Add fuse settings
        for fuse, value in fuse_settings.items():
            cmd.append(f"-U{fuse}:w:{value}:m")
            
        # Add hex file
        cmd.append(f"-Uflash:w:{hex_file}:i")
        
        print("Uploading to ATtiny1616...")
        print(f"Using avrdude at: {self.avrdude_path}")
        print(f"Using configuration: {self.avrdude_conf}")
        print(f"Command: {' '.join(cmd)}")
        
        try:
            # Use a timeout to prevent hanging indefinitely
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("Upload successful!")
                return True
            else:
                print(f"Upload failed with return code: {result.returncode}")
                if result.stderr:
                    print(f"Error output: {result.stderr}")
                if result.stdout:
                    print(f"Standard output: {result.stdout}")
                return False
        except subprocess.TimeoutExpired:
            print("Upload timed out after 60 seconds.")
            print("This could be due to communication issues with the Arduino.")
            print("Please check your connections and try again.")
            return False
        except Exception as e:
            print(f"Error during upload: {str(e)}")
            return False

def main():
    """Main function for standalone usage."""
    if len(sys.argv) < 3:
        print("Usage: python arduino_uploader.py <hex_file> <port>")
        return
    
    hex_file = sys.argv[1]
    port = sys.argv[2]
    
    uploader = ArduinoUploader()
    uploader.upload_to_attiny1616(hex_file, port)

if __name__ == "__main__":
    main()
