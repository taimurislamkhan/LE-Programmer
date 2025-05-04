import os
import re
import sys
import time
from arduino_compiler import ArduinoCompiler
from arduino_uploader import ArduinoUploader

class AddressChanger:
    """Class to change address, sine, and cosine values in LE_Final settings.h file."""
    
    def __init__(self, le_final_dir=None):
        """Initialize the AddressChanger with the path to the LE_Final directory."""
        # Set default path if not provided
        if le_final_dir is None:
            le_final_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LE_Final")
        
        self.le_final_dir = le_final_dir
        self.ino_file = os.path.join(le_final_dir, "LE_Final.ino")
        
        # Check if the directory and ino file exist
        if not os.path.exists(le_final_dir):
            raise FileNotFoundError(f"LE_Final directory not found at {le_final_dir}")
        
        if not os.path.exists(self.ino_file):
            raise FileNotFoundError(f"LE_Final.ino file not found at {self.ino_file}")
    
    def read_current_settings(self):
        """Read the current settings from the LE_Final.ino file."""
        try:
            with open(self.ino_file, 'r') as f:
                content = f.read()
            
            # Extract current values using regex
            address_match = re.search(r'int\s+address\s*=\s*(\d+)', content)
            sine_match = re.search(r'int\s+sine_off\s*=\s*(\d+)', content)
            cosine_match = re.search(r'int\s+cosine_off\s*=\s*(\d+)', content)
            
            # Default values if not found
            address = int(address_match.group(1)) if address_match else 8
            sine = int(sine_match.group(1)) if sine_match else 0
            cosine = int(cosine_match.group(1)) if cosine_match else 0
            
            return {
                'address': address,
                'sine': sine,
                'cosine': cosine
            }
        except Exception as e:
            print(f"Error reading LE_Final.ino file: {str(e)}")
            return {'address': 8, 'sine': 0, 'cosine': 0}
    
    def update_settings(self, address, sine, cosine):
        """Update the LE_Final.ino file with new values."""
        try:
            # Read the current file content
            with open(self.ino_file, 'r') as f:
                lines = f.readlines()
            
            # Create new content line by line for better control
            new_lines = []
            changes_made = {'address': False, 'sine': False, 'cosine': False}
            
            for line in lines:
                # Check for each variable and replace if found
                if re.search(r'int\s+address\s*=', line):
                    new_lines.append(f"int address={address};\n")
                    changes_made['address'] = True
                elif re.search(r'int\s+sine_off\s*=', line):
                    new_lines.append(f"int sine_off={sine};\n")
                    changes_made['sine'] = True
                elif re.search(r'int\s+cosine_off\s*=', line):
                    new_lines.append(f"int cosine_off={cosine};\n")
                    changes_made['cosine'] = True
                else:
                    new_lines.append(line)
            
            # Write the updated content back to the file
            with open(self.ino_file, 'w') as f:
                f.writelines(new_lines)
            
            # Verify the changes were made
            if not all(changes_made.values()):
                missing = [var for var, changed in changes_made.items() if not changed]
                print(f"Warning: Could not find and update the following variables: {', '.join(missing)}")
                print("The file structure might be different than expected.")
            
            # Read the file again to verify changes
            updated_settings = self.read_current_settings()
            
            print(f"Settings updated successfully:")
            print(f"  ADDRESS: {address} (verified: {updated_settings['address']})")
            print(f"  SINE: {sine} (verified: {updated_settings['sine']})")
            print(f"  COSINE: {cosine} (verified: {updated_settings['cosine']})")
            
            # Check if the values match what we tried to set
            if (updated_settings['address'] != address or 
                updated_settings['sine'] != sine or 
                updated_settings['cosine'] != cosine):
                print("Warning: Some values may not have been updated correctly.")
                print("Please check the file manually.")
            
            return True
        except Exception as e:
            print(f"Error updating LE_Final.ino file: {str(e)}")
            return False
    
    def compile_sketch(self):
        """Compile the LE_Final sketch."""
        try:
            print("Compiling LE_Final sketch...")
            
            # Check if the compiler module is available
            compiler = ArduinoCompiler()
            
            # Create a directory for the compiled output
            output_dir = os.path.join(self.le_final_dir, "build")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            sketch_path = self.ino_file
            sketch_name = os.path.basename(sketch_path)
            if sketch_name.endswith('.ino'):
                sketch_name = sketch_name[:-4]
            
            print(f"Compiling {sketch_name} for ATtiny1616...")
            
            # Compile the sketch
            success = compiler.compile_attiny1616(sketch_path, output_dir)
            
            if success:
                # Get the path to the compiled hex file
                hex_file = os.path.join(output_dir, f"{sketch_name}.hex")
                
                # Copy the hex file to the Hex directory for easy access
                hex_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Hex")
                
                if os.path.exists(hex_file):
                    if os.path.exists(hex_dir):
                        target_hex = os.path.join(hex_dir, f"{sketch_name}.hex")
                        import shutil
                        shutil.copy2(hex_file, target_hex)
                        print(f"Hex file copied to: {target_hex}")
                    return hex_file
                else:
                    print("Hex file not found after compilation.")
                    return None
            else:
                print("Compilation failed.")
                return None
        except Exception as e:
            print(f"Error during compilation: {str(e)}")
            return None
    
    def upload_to_attiny(self, hex_file, updi_port):
        """Upload the compiled hex file to the ATtiny1616."""
        try:
            if not hex_file or not os.path.exists(hex_file):
                print(f"Error: Hex file not found at {hex_file}")
                return False
                
            print(f"Uploading to ATtiny1616 via {updi_port}...")
            uploader = ArduinoUploader()
            
            # Default fuse settings for ATtiny1616 with 20MHz clock
            fuse_settings = {
                "fuse0": "0b00000000",  # APPEND disabled, BOOTEND = 0
                "fuse2": "0x02",        # OSCLOCK disabled, EESAVE disabled, BODCFG = 2
                "fuse5": "0b11000101",  # 20MHz oscillator, RUNSTDBY disabled, STARTUP = 1 (16ms)
                "fuse6": "0x04",        # SYSCFG0 = 0x04 (default)
                "fuse7": "0x00",        # SYSCFG1 = 0x00 (default)
                "fuse8": "0x00"         # BOOTSIZE = 0 (default)
            }
            
            result = uploader.upload_to_attiny1616(hex_file, updi_port, fuse_settings)
            
            if result:
                print("Upload successful!")
                return True
            else:
                print("Upload failed.")
                return False
        except Exception as e:
            print(f"Error during upload: {str(e)}")
            return False
    
    def change_address_workflow(self, updi_port):
        """Run the complete workflow to change address, compile, and upload."""
        try:
            # Read current settings
            current_settings = self.read_current_settings()
            print("\nCurrent settings:")
            print(f"  ADDRESS: {current_settings['address']}")
            print(f"  SINE: {current_settings['sine']}")
            print(f"  COSINE: {current_settings['cosine']}")
            
            # Get new values from user
            print("\nEnter new values (leave blank to keep current value):")
            
            # Get address (must be an integer between 0 and 255)
            while True:
                address_input = input(f"New ADDRESS (0-255) [{current_settings['address']}]: ").strip()
                if not address_input:
                    address = current_settings['address']
                    break
                
                try:
                    address = int(address_input)
                    if 0 <= address <= 255:
                        break
                    else:
                        print("ADDRESS must be between 0 and 255. Please try again.")
                except ValueError:
                    print("Please enter a valid integer for ADDRESS.")
            
            # Get sine (must be a value between 0 and 1024)
            while True:
                sine_input = input(f"New SINE (0 to 1024) [{current_settings['sine']}]: ").strip()
                if not sine_input:
                    sine = current_settings['sine']
                    break
                
                try:
                    sine = int(sine_input)  # Changed to int instead of float
                    if 0 <= sine <= 1024:
                        break
                    else:
                        print("SINE must be between 0 and 1024. Please try again.")
                except ValueError:
                    print("Please enter a valid integer for SINE.")
            
            # Get cosine (must be a value between 0 and 1024)
            while True:
                cosine_input = input(f"New COSINE (0 to 1024) [{current_settings['cosine']}]: ").strip()
                if not cosine_input:
                    cosine = current_settings['cosine']
                    break
                
                try:
                    cosine = int(cosine_input)  # Changed to int instead of float
                    if 0 <= cosine <= 1024:
                        break
                    else:
                        print("COSINE must be between 0 and 1024. Please try again.")
                except ValueError:
                    print("Please enter a valid integer for COSINE.")
            
            # Confirm changes
            print("\nNew settings to apply:")
            print(f"  ADDRESS: {address}")
            print(f"  SINE: {sine}")
            print(f"  COSINE: {cosine}")
            
            confirm = input("\nApply these changes? (y/n): ").lower().strip()
            if confirm != 'y':
                print("Changes cancelled.")
                return False
            
            # Update settings file
            if not self.update_settings(address, sine, cosine):
                print("Failed to update settings. Operation cancelled.")
                return False
            
            # Ask if user wants to compile and upload
            compile_choice = input("\nDo you want to compile and upload these changes? (y/n): ").lower().strip()
            if compile_choice != 'y':
                print("Settings updated without compilation or upload.")
                return True
            
            # Compile the sketch using the same approach as option 4
            hex_file = self.compile_sketch()
            if not hex_file:
                print("Compilation failed. Operation cancelled.")
                return False
            
            # Upload to ATtiny1616
            if not self.upload_to_attiny(hex_file, updi_port):
                print("Upload failed. Operation cancelled.")
                return False
            
            print("\nAddress change completed successfully!")
            return True
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return False
        except Exception as e:
            print(f"\nError during address change: {str(e)}")
            return False


# For testing as standalone script
if __name__ == "__main__":
    try:
        le_final_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LE_Final")
        changer = AddressChanger(le_final_dir)
        
        # If UPDI port is provided as argument, use it
        updi_port = sys.argv[1] if len(sys.argv) > 1 else input("Enter UPDI port (e.g., COM3): ")
        
        changer.change_address_workflow(updi_port)
    except Exception as e:
        print(f"Error: {str(e)}")
