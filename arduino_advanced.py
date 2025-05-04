import os
import time
import serial
import subprocess

from arduino_utils import clear_screen, find_arduino_ports, find_avrdude
from arduino_config import load_config, HEX_DIR
from arduino_upload import upload_hex

try:
    from arduino_compiler import ArduinoCompiler
except ImportError:
    print("Warning: arduino_compiler module not found. Compilation features will be disabled.")
    
try:
    from arduino_uploader import ArduinoUploader
except ImportError:
    print("Warning: arduino_uploader module not found. ATtiny1616 upload features will be disabled.")

def check_dependencies():
    """Check if all required dependencies are available."""
    print("Checking dependencies...")
    
    # Check for PySerial
    try:
        import serial
        print("✓ PySerial is installed.")
    except ImportError:
        print("✗ PySerial is not installed. Please install it using 'pip install pyserial'.")
    
    # Check for avrdude
    avrdude_path = find_avrdude()
    if avrdude_path:
        print(f"✓ avrdude found at: {avrdude_path}")
        
        # Check for avrdude.conf
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
        
        if os.path.exists(avrdude_conf):
            print(f"✓ avrdude.conf found at: {avrdude_conf}")
        else:
            print("✗ avrdude.conf not found. This may cause issues when using avrdude.")
    else:
        print("✗ avrdude not found in system path or common Arduino installation locations.")
        print("  Some functionality will be limited.")
        print("  For full functionality, please install Arduino IDE or ensure avrdude is in your system PATH.")
        print("  Common Arduino installation locations checked:")
        print("    - C:\\Program Files\\Arduino\\hardware\\tools\\avr\\bin\\avrdude.exe")
        print("    - C:\\Program Files (x86)\\Arduino\\hardware\\tools\\avr\\bin\\avrdude.exe")
    
    # Check for hex files
    blink_hex = os.path.join(HEX_DIR, "LED_Blink.ino.hex")
    updi_hex = os.path.join(HEX_DIR, "jtag2updi.ino.hex")
    
    if os.path.exists(blink_hex):
        print(f"✓ Blink hex file found: {blink_hex}")
    else:
        print(f"✗ Blink hex file not found: {blink_hex}")
    
    if os.path.exists(updi_hex):
        print(f"✓ UPDI programmer hex file found: {updi_hex}")
    else:
        print(f"✗ UPDI programmer hex file not found: {updi_hex}")
    
    print("\nSystem information:")
    import platform
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    
    input("\nPress Enter to continue...")

def compile_attiny_code():
    """Compile code for the ATtiny1616 controller."""
    clear_screen()
    print("=== Compile ATtiny Code ===")
    
    try:
        from arduino_compiler import ArduinoCompiler
        compiler = ArduinoCompiler()
    except ImportError:
        print("Error: arduino_compiler module not found.")
        print("Please make sure the arduino_compiler.py file is in the same directory.")
        input("Press Enter to continue...")
        return
    
    # Check if LE_Final directory exists
    le_final_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LE_Final")
    if not os.path.exists(le_final_dir):
        print(f"Error: LE_Final directory not found at {le_final_dir}")
        print("Please make sure the LE_Final directory exists with the sketch files.")
        input("Press Enter to continue...")
        return
    
    # Check if LE_Final.ino exists
    le_final_ino = os.path.join(le_final_dir, "LE_Final.ino")
    if not os.path.exists(le_final_ino):
        print(f"Error: LE_Final.ino not found at {le_final_ino}")
        print("Please make sure the LE_Final.ino file exists in the LE_Final directory.")
        input("Press Enter to continue...")
        return
    
    # Create a directory for the compiled output
    output_dir = os.path.join(le_final_dir, "build")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Compile the sketch
    print(f"Compiling LE_Final.ino for ATtiny1616...")
    success = compiler.compile_attiny1616(le_final_ino, output_dir)
    
    if success:
        # Get the path to the compiled hex file
        hex_file = os.path.join(output_dir, "LE_Final.hex")
        
        # Copy the hex file to the Hex directory for easy access
        if os.path.exists(hex_file):
            import shutil
            target_hex = os.path.join(HEX_DIR, "LE_Final.ino.hex")
            shutil.copy2(hex_file, target_hex)
            print(f"Compilation successful!")
            print(f"Hex file copied to: {target_hex}")
        else:
            print("Hex file not found after compilation.")
    else:
        print("Compilation failed.")
    
    input("Press Enter to continue...")

def upload_attiny_code():
    """Upload code to ATtiny1616 using UPDI programmer."""
    clear_screen()
    print("=== Upload to ATtiny1616 ===")
    
    # Load configuration
    config = load_config()
    
    if not config["updi_programmer"]:
        print("UPDI programmer not configured. Please run Setup first.")
        input("Press Enter to continue...")
        return
    
    # Check if the UPDI programmer is still connected
    arduino_ports = find_arduino_ports()
    updi_port_found = False
    
    for port in arduino_ports:
        if port["port"] == config["updi_programmer"]["port"]:
            updi_port_found = True
            break
    
    if not updi_port_found:
        print(f"UPDI programmer not found at {config['updi_programmer']['port']}.")
        print("Please reconnect the UPDI programmer or run Setup again.")
        input("Press Enter to continue...")
        return
    
    # List available hex files
    hex_files = [f for f in os.listdir(HEX_DIR) if f.endswith('.hex')]
    
    if not hex_files:
        print(f"No hex files found in {HEX_DIR}.")
        input("Press Enter to continue...")
        return
    
    print("Available hex files:")
    for i, hex_file in enumerate(hex_files):
        print(f"{i+1}. {hex_file}")
    
    try:
        choice = int(input("\nEnter the number of the hex file to upload: "))
        if choice < 1 or choice > len(hex_files):
            print("Invalid choice.")
            input("Press Enter to continue...")
            return
        
        selected_hex = os.path.join(HEX_DIR, hex_files[choice-1])
        
        # Upload to ATtiny1616 using UPDI programmer
        try:
            from arduino_uploader import ArduinoUploader
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
            
            print(f"\nUploading {selected_hex} to ATtiny1616 via UPDI programmer on {config['updi_programmer']['port']}...")
            
            if uploader.upload_to_attiny1616(selected_hex, config['updi_programmer']['port'], fuse_settings):
                print("Upload successful!")
            else:
                print("Upload failed.")
        
        except ImportError:
            print("Error: arduino_uploader module not found.")
            print("Please make sure the arduino_uploader.py file is in the same directory.")
    
    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    input("Press Enter to continue...")

def run_le_test():
    """Run the LE Test: Upload LE_Reader to Arduino, LE_Test to ATtiny1616, and analyze serial output."""
    clear_screen()
    print("=== Run LE Test ===")
    print("This will upload LE_Reader to the Arduino Uno and LE_Test to the ATtiny1616,")
    print("then read and analyze the serial output from the Arduino.")
    
    # Load configuration
    config = load_config()
    
    if not config["updi_programmer"]:
        print("\nUPDI programmer not configured. Please run Setup first.")
        input("Press Enter to continue...")
        return
    
    if not config["target_arduino"]:
        print("\nTarget Arduino not configured. Please run Setup first.")
        input("Press Enter to continue...")
        return
    
    # Check if the required hex files exist
    le_reader_hex = os.path.join(HEX_DIR, "LE_Reader.ino.hex")
    le_test_hex = os.path.join(HEX_DIR, "LE_Test.ino.hex")
    
    if not os.path.exists(le_reader_hex):
        print(f"\nError: LE_Reader.ino.hex not found in {HEX_DIR}")
        input("Press Enter to continue...")
        return
    
    if not os.path.exists(le_test_hex):
        print(f"\nError: LE_Test.ino.hex not found in {HEX_DIR}")
        input("Press Enter to continue...")
        return
    
    # Check if the devices are still connected
    arduino_ports = find_arduino_ports()
    updi_port_found = False
    target_port_found = False
    
    for port in arduino_ports:
        if port["port"] == config["updi_programmer"]["port"]:
            updi_port_found = True
        if port["port"] == config["target_arduino"]["port"]:
            target_port_found = True
    
    if not updi_port_found:
        print(f"\nUPDI programmer not found at {config['updi_programmer']['port']}.")
        print("Please reconnect the UPDI programmer or run Setup again.")
        input("Press Enter to continue...")
        return
    
    if not target_port_found:
        print(f"\nTarget Arduino not found at {config['target_arduino']['port']}.")
        print("Please reconnect the target Arduino or run Setup again.")
        input("Press Enter to continue...")
        return
    
    # Step 1: Upload LE_Test to ATtiny1616
    print(f"\n1. Uploading LE_Test to ATtiny1616 via UPDI programmer on {config['updi_programmer']['port']}...")
    
    try:
        from arduino_uploader import ArduinoUploader
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
        
        if not uploader.upload_to_attiny1616(le_test_hex, config['updi_programmer']['port'], fuse_settings):
            print("\nFailed to upload LE_Test to ATtiny1616.")
            input("Press Enter to continue...")
            return
    except ImportError:
        print("\nError: arduino_uploader module not found.")
        print("Please make sure the arduino_uploader.py file is in the same directory.")
        input("Press Enter to continue...")
        return
    
    # Step 2: Upload LE_Reader to Arduino Uno
    print(f"\n2. Uploading LE_Reader to Arduino Uno on {config['target_arduino']['port']}...")
    if not upload_hex(config['target_arduino']['port'], le_reader_hex):
        print("\nFailed to upload LE_Reader to Arduino Uno.")
        input("Press Enter to continue...")
        return
    
    # Step 3: Read and analyze serial output from Arduino Uno
    print(f"\n3. Reading serial data from Arduino Uno on {config['target_arduino']['port']}...")
    print("\nReading cosine and sine values...")
    print("\nWaiting for data...")
    
    try:
        # Open serial connection
        ser = serial.Serial(config['target_arduino']['port'], 115200, timeout=1)
        time.sleep(2)  # Allow time for serial connection to establish
        
        # Initialize data collection
        cosine_values = []
        sine_values = []
        count = 0
        max_samples = 10  # Number of samples to collect
        
        print("\nReading values (waiting for 10 samples):")
        print("----------------------------------------")
        print("Sample\tCosine\tSine")
        print("----------------------------------------")
        
        # Read data until we have enough samples
        timeout_counter = 0
        max_timeout = 30  # 30 seconds timeout
        
        while count < max_samples and timeout_counter < max_timeout:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if ',' in line:  # Make sure we have valid data
                    try:
                        cosine_str, sine_str = line.split(',')
                        cosine = float(cosine_str)
                        sine = float(sine_str)
                        
                        cosine_values.append(cosine)
                        sine_values.append(sine)
                        
                        count += 1
                        print(f"{count}\t{cosine:.2f}\t{sine:.2f}")
                        timeout_counter = 0  # Reset timeout counter on successful read
                    except ValueError:
                        # Skip invalid data
                        pass
            else:
                time.sleep(0.1)
                timeout_counter += 0.1
        
        # Close the serial connection
        ser.close()
        
        if count < max_samples:
            print("\nTimeout waiting for data. Check connections and try again.")
        else:
            # Calculate averages
            avg_cosine = sum(cosine_values) / len(cosine_values)
            avg_sine = sum(sine_values) / len(sine_values)
            
            print("\n----------------------------------------")
            print(f"Average Cosine: {avg_cosine:.2f}")
            print(f"Average Sine: {avg_sine:.2f}")
            print("----------------------------------------")
            
            # Calculate magnitude (optional)
            magnitude = (avg_cosine**2 + avg_sine**2)**0.5
            print(f"Magnitude: {magnitude:.2f}")
            
            # Save results to a file
            results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.txt")
            with open(results_file, 'w') as f:
                f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("----------------------------------------\n")
                f.write("Sample\tCosine\tSine\n")
                for i in range(len(cosine_values)):
                    f.write(f"{i+1}\t{cosine_values[i]:.2f}\t{sine_values[i]:.2f}\n")
                f.write("----------------------------------------\n")
                f.write(f"Average Cosine: {avg_cosine:.2f}\n")
                f.write(f"Average Sine: {avg_sine:.2f}\n")
                f.write(f"Magnitude: {magnitude:.2f}\n")
            
            print(f"\nResults saved to {results_file}")
    
    except serial.SerialException as e:
        print(f"\nSerial error: {str(e)}")
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    except Exception as e:
        print(f"\nError during serial reading: {str(e)}")
    finally:
        # Make sure to close the serial connection
        try:
            ser.close()
        except:
            pass
    
    print("\nTest completed.")
    input("Press Enter to continue...")
