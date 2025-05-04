import os
import time
import serial
import subprocess

from arduino_utils import clear_screen, find_arduino_ports
from arduino_config import load_config, save_config, HEX_DIR, BLINK_HEX, UPDI_HEX
from arduino_upload import upload_hex
from serial_helper import open_serial_with_flush

try:
    from address_changer import AddressChanger
except ImportError:
    print("Warning: address_changer module not found. Address change features will be disabled.")

def setup_arduinos():
    """Setup option: Scan for Arduinos, configure UPDI programmer and target Arduino."""
    clear_screen()
    print("=== Arduino Setup ===")
    
    # Find all connected Arduino devices
    arduino_ports = find_arduino_ports()
    
    if not arduino_ports:
        print("No Arduino devices found. Please connect an Arduino and try again.")
        input("Press Enter to continue...")
        return
    
    # Load existing configuration
    config = load_config()
    
    # Check if saved ports are still available
    available_ports = [port["port"] for port in arduino_ports]
    
    if config["updi_programmer"] and config["updi_programmer"]["port"] not in available_ports:
        print(f"Warning: Previously configured UPDI programmer port {config['updi_programmer']['port']} is not available.")
        config["updi_programmer"] = None
    
    if config["target_arduino"] and config["target_arduino"]["port"] not in available_ports:
        print(f"Warning: Previously configured target Arduino port {config['target_arduino']['port']} is not available.")
        config["target_arduino"] = None
    
    print(f"\nFound {len(arduino_ports)} Arduino device(s):")
    for i, port in enumerate(arduino_ports):
        print(f"{i+1}. Arduino at {port['port']} - {port['description']}")
    
    # Upload LED_Blink.ino.hex to one of the Arduinos to identify it
    print("\n=== Arduino Identification ===")
    print("We'll upload a blinking sketch to help identify one of the Arduinos.")
    
    try:
        choice = int(input("\nSelect an Arduino to upload the blink sketch (enter number): "))
        if choice < 1 or choice > len(arduino_ports):
            print("Invalid choice.")
            input("Press Enter to continue...")
            return
        
        selected_port = arduino_ports[choice-1]
        
        # Upload the blink sketch
        if os.path.exists(BLINK_HEX):
            print(f"\nUploading {BLINK_HEX} to {selected_port['port']}...")
            if upload_hex(selected_port['port'], BLINK_HEX):
                print("Upload successful! The Arduino's LED should now be blinking.")
                print("Please observe which Arduino is blinking.")
            else:
                print("Upload failed. Please try again.")
                input("Press Enter to continue...")
                return
        else:
            print(f"Error: Blink hex file not found at {BLINK_HEX}")
            print("Please make sure the file exists and try again.")
            input("Press Enter to continue...")
            return
        
        # Ask if this is the UPDI programmer
        is_updi = input("\nIs the blinking Arduino the one you want to use as UPDI programmer? (y/n): ").lower().strip()
        
        if is_updi == 'y':
            # Set this as the UPDI programmer
            config["updi_programmer"] = selected_port
            print(f"UPDI programmer set to: {config['updi_programmer']['port']} - {config['updi_programmer']['description']}")
            
            # Upload the jtag2updi sketch
            if os.path.exists(UPDI_HEX):
                print(f"\nUploading {UPDI_HEX} to {config['updi_programmer']['port']}...")
                if upload_hex(config['updi_programmer']['port'], UPDI_HEX):
                    print("Upload successful! The Arduino is now configured as a UPDI programmer.")
                else:
                    print("Upload failed. Please try again.")
                    input("Press Enter to continue...")
                    return
            else:
                print(f"Error: UPDI programmer hex file not found at {UPDI_HEX}")
                print("Please make sure the file exists and try again.")
                input("Press Enter to continue...")
                return
            
            # Find other Arduinos for target
            target_options = []
            for port in arduino_ports:
                if port["port"] != config["updi_programmer"]["port"]:
                    target_options.append(port)
            
            if not target_options:
                print("\nNo additional Arduino found besides the UPDI programmer.")
                print("Please connect another Arduino to use as the target device.")
                input("Press Enter to continue...")
                return
            
            # If only one other Arduino, select it automatically
            if len(target_options) == 1:
                config["target_arduino"] = target_options[0]
                print(f"\nAutomatically selected the only other Arduino as target: {config['target_arduino']['port']} - {config['target_arduino']['description']}")
            else:
                # Let user select from multiple options
                print("\nSelect the target Arduino:")
                for i, port in enumerate(target_options):
                    print(f"{i+1}. Arduino at {port['port']} - {port['description']}")
                
                try:
                    choice = int(input("\nSelect the target Arduino (enter number): "))
                    if choice < 1 or choice > len(target_options):
                        print("Invalid choice.")
                        input("Press Enter to continue...")
                        return
                    
                    config["target_arduino"] = target_options[choice-1]
                    print(f"Target Arduino set to: {config['target_arduino']['port']} - {config['target_arduino']['description']}")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    input("Press Enter to continue...")
                    return
        else:
            # The blinking Arduino is the target, so we need to select the UPDI programmer
            config["target_arduino"] = selected_port
            print(f"Target Arduino set to: {config['target_arduino']['port']} - {config['target_arduino']['description']}")
            
            # Find other Arduinos for UPDI programmer
            updi_options = []
            for port in arduino_ports:
                if port["port"] != config["target_arduino"]["port"]:
                    updi_options.append(port)
            
            if not updi_options:
                print("\nNo additional Arduino found besides the target.")
                print("Please connect another Arduino to use as the UPDI programmer.")
                input("Press Enter to continue...")
                return
            
            # If only one other Arduino, select it automatically
            if len(updi_options) == 1:
                config["updi_programmer"] = updi_options[0]
                print(f"\nAutomatically selected the only other Arduino as UPDI programmer: {config['updi_programmer']['port']} - {config['updi_programmer']['description']}")
            else:
                # Let user select from multiple options
                print("\nSelect the UPDI programmer:")
                for i, port in enumerate(updi_options):
                    print(f"{i+1}. Arduino at {port['port']} - {port['description']}")
                
                try:
                    choice = int(input("\nSelect the UPDI programmer (enter number): "))
                    if choice < 1 or choice > len(updi_options):
                        print("Invalid choice.")
                        input("Press Enter to continue...")
                        return
                    
                    config["updi_programmer"] = updi_options[choice-1]
                    print(f"UPDI programmer set to: {config['updi_programmer']['port']} - {config['updi_programmer']['description']}")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    input("Press Enter to continue...")
                    return
            
            # Upload the jtag2updi sketch to the UPDI programmer
            if os.path.exists(UPDI_HEX):
                print(f"\nUploading {UPDI_HEX} to {config['updi_programmer']['port']}...")
                if upload_hex(config['updi_programmer']['port'], UPDI_HEX):
                    print("Upload successful! The Arduino is now configured as a UPDI programmer.")
                else:
                    print("Upload failed. Please try again.")
                    input("Press Enter to continue...")
                    return
            else:
                print(f"Error: UPDI programmer hex file not found at {UPDI_HEX}")
                print("Please make sure the file exists and try again.")
                input("Press Enter to continue...")
                return
    except ValueError:
        print("Invalid input. Please enter a number.")
        input("Press Enter to continue...")
        return
    
    # Upload LE_Reader.ino.hex to the target Arduino
    print("\n=== Uploading LE_Reader to Target Arduino ===")
    print("Now we'll upload the LE_Reader sketch to the target Arduino.")
    
    le_reader_hex = os.path.join(HEX_DIR, "LE_Reader.ino.hex")
    if os.path.exists(le_reader_hex):
        print(f"\nUploading LE_Reader.ino.hex to {config['target_arduino']['port']}...")
        if upload_hex(config['target_arduino']['port'], le_reader_hex):
            print("Upload successful! The Arduino is now ready to read values from the Linear Encoder.")
            config["le_reader_uploaded"] = True
        else:
            print("Upload failed. Please try again.")
            input("Press Enter to continue...")
            return
    else:
        print(f"Error: LE_Reader.ino.hex file not found at {le_reader_hex}")
        print("Please make sure the file exists and try again.")
        input("Press Enter to continue...")
        return
    
    # Save configuration
    save_config(config)
    print("\nSetup completed successfully!")
    print("\nSummary:")
    print(f"- UPDI Programmer: {config['updi_programmer']['port']} - {config['updi_programmer']['description']}")
    print(f"- Target Arduino: {config['target_arduino']['port']} - {config['target_arduino']['description']}")
    print("\nYou can now use Option 2 (Program) to calibrate your Linear Encoder.")
    
    input("Press Enter to continue...")

def program_arduino():
    """Program option: Upload test and reader files, collect sine/cosine values, and update settings."""
    clear_screen()
    print("=== Automated Programming and Calibration ===")
    print("This will perform the following steps:")
    print("1. Upload LE_Test.ino.hex to the ATtiny1616 via UPDI")
    print("2. Upload LE_Reader.ino.hex to the Arduino Uno")
    print("3. Collect sine and cosine values from the Arduino")
    print("4. Calculate average values and update the LE_Final sketch")
    print("\nMake sure both devices are connected.")
    input("Press Enter to continue...")
    
    # Load configuration
    config = load_config()
    if not config["updi_programmer"]:
        print("\nUPDI programmer not configured. Please run Setup first.")
        input("Press Enter to continue...")
        return
    
    # Find all connected Arduino devices
    arduino_ports = find_arduino_ports()
    if len(arduino_ports) < 2:
        print("\nNot enough Arduino devices found. Please connect both the UPDI programmer and the Arduino Uno.")
        input("Press Enter to continue...")
        return
    
    # Verify UPDI programmer is connected
    updi_port = None
    for port in arduino_ports:
        if port["port"] == config["updi_programmer"]["port"]:
            updi_port = port["port"]
            break
    
    if not updi_port:
        print(f"\nUPDI programmer not found at {config['updi_programmer']['port']}.")
        print("Please run Setup again to configure the UPDI programmer.")
        input("Press Enter to continue...")
        return
    
    # Get the Arduino Uno port from the configuration
    arduino_port = None
    if config["target_arduino"] and config["target_arduino"]["port"]:
        arduino_port = config["target_arduino"]["port"]
        
        # Verify the port is still connected
        arduino_port_found = False
        for port in arduino_ports:
            if port["port"] == arduino_port:
                arduino_port_found = True
                break
        
        if not arduino_port_found:
            print(f"\nTarget Arduino not found at {arduino_port}.")
            print("Please run Setup again to configure the target Arduino.")
            input("Press Enter to continue...")
            return
    else:
        print("\nTarget Arduino not configured in settings.")
        print("Please run Setup first to configure both UPDI programmer and target Arduino.")
        input("Press Enter to continue...")
        return
    
    print(f"\nUsing UPDI programmer on port: {updi_port}")
    print(f"Using target Arduino on port: {arduino_port}")
    
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
    
    # Check if LE_Final directory exists
    le_final_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LE_Final")
    if not os.path.exists(le_final_dir):
        print(f"Error: LE_Final directory not found at {le_final_dir}")
        print("Please make sure the LE_Final directory exists with the sketch files.")
        input("Press Enter to continue...")
        return
    
    # Ask user for the address
    try:
        address = int(input("\nEnter the ADDRESS (0-255) for the device: "))
        if not (0 <= address <= 255):
            print("ADDRESS must be between 0 and 255.")
            input("Press Enter to continue...")
            return
    except ValueError:
        print("Invalid input. Please enter a valid integer for ADDRESS.")
        input("Press Enter to continue...")
        return
    
    # Step 1: Upload LE_Test.ino.hex to ATtiny1616
    print(f"\n1. Uploading LE_Test.ino.hex to ATtiny1616 via UPDI programmer on {updi_port}...")
    
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
        
        if not uploader.upload_to_attiny1616(le_test_hex, updi_port, fuse_settings):
            print("\nFailed to upload LE_Test.ino.hex to ATtiny1616.")
            input("Press Enter to continue...")
            return
    except Exception as e:
        print(f"\nError during upload to ATtiny1616: {str(e)}")
        input("Press Enter to continue...")
        return
    
    # Step 2: Upload LE_Reader.ino.hex to Arduino Uno (if not already uploaded)
    if config.get("le_reader_uploaded", False):
        print(f"\n2. LE_Reader.ino.hex already uploaded to Arduino Uno on {arduino_port}. Skipping...")
    else:
        print(f"\n2. Uploading LE_Reader.ino.hex to Arduino Uno on {arduino_port}...")
        if not upload_hex(arduino_port, le_reader_hex):
            print("\nFailed to upload LE_Reader.ino.hex to Arduino Uno.")
            input("Press Enter to continue...")
            return
        config["le_reader_uploaded"] = True
        save_config(config)
    
    # Step 3: Read and analyze serial output from Arduino Uno
    print(f"\n3. Reading serial data from Arduino Uno on {arduino_port}...")
    print("\nReading cosine and sine values...")
    print("\nWaiting for data...")
    
    try:
        # Open serial connection with proper buffer flushing
        ser = open_serial_with_flush(arduino_port, 115200, 1)
        
        # Initialize data collection
        cosine_values = []
        sine_values = []
        device_addresses = []
        count = 0
        max_samples = 10  # Number of samples to collect
        
        print("\nReading values (waiting for 10 samples):")
        print("----------------------------------------")
        print("Sample\tAddr\tCosine\tSine")
        print("----------------------------------------")
        
        # Read data until we have enough samples
        timeout_counter = 0
        max_timeout = 30  # 30 seconds timeout
        
        while count < max_samples and timeout_counter < max_timeout:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                if ',' in line and line.count(',') == 2:  # Make sure we have valid data in format address,cosine,sine
                    try:
                        address_str, cosine_str, sine_str = line.split(',')
                        device_address = int(address_str)
                        cosine = float(cosine_str)
                        sine = float(sine_str)
                        
                        device_addresses.append(device_address)
                        cosine_values.append(cosine)
                        sine_values.append(sine)
                        
                        count += 1
                        print(f"{count}\t{device_address}\t{cosine:.2f}\t{sine:.2f}")
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
            input("Press Enter to continue...")
            return
        
        # Calculate averages
        avg_cosine = int(sum(cosine_values) / len(cosine_values))
        avg_sine = int(sum(sine_values) / len(sine_values))
        
        print("\n----------------------------------------")
        print(f"Average Cosine: {avg_cosine}")
        print(f"Average Sine: {avg_sine}")
        print("----------------------------------------")
        
        # Calculate magnitude (optional)
        magnitude = (avg_cosine**2 + avg_sine**2)**0.5
        print(f"Magnitude: {magnitude:.2f}")
        
        # Save results to a file
        results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration_results.txt")
        with open(results_file, 'w') as f:
            f.write(f"Calibration Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Device Address: {address}\n")
            f.write("----------------------------------------\n")
            f.write("Sample\tCosine\tSine\n")
            for i in range(len(cosine_values)):
                f.write(f"{i+1}\t{cosine_values[i]:.2f}\t{sine_values[i]:.2f}\n")
            f.write("----------------------------------------\n")
            f.write(f"Average Cosine: {avg_cosine}\n")
            f.write(f"Average Sine: {avg_sine}\n")
            f.write(f"Magnitude: {magnitude:.2f}\n")
        
        print(f"\nResults saved to {results_file}")
        
        # Step 4: Update LE_Final with the new values
        print("\n4. Updating LE_Final sketch with new values...")
        
        try:
            # Create AddressChanger instance
            from address_changer import AddressChanger
            changer = AddressChanger(le_final_dir)
            
            # Update the settings
            if changer.update_settings(address, avg_sine, avg_cosine):
                print("\nLE_Final sketch updated successfully!")
                
                # Ask if user wants to compile and upload
                compile_choice = input("\nDo you want to compile and upload these changes to ATtiny1616? (y/n): ").lower().strip()
                if compile_choice == 'y':
                    # Compile the sketch
                    hex_file = changer.compile_sketch()
                    if hex_file and os.path.exists(hex_file):
                        # Upload to ATtiny1616
                        if changer.upload_to_attiny(hex_file, updi_port):
                            print("\nCalibration and programming completed successfully!")
                        else:
                            print("\nSettings updated but upload failed.")
                    else:
                        print("\nSettings updated but compilation failed.")
            else:
                print("\nFailed to update LE_Final sketch.")
        except Exception as e:
            print(f"\nError updating LE_Final sketch: {str(e)}")
        
        print("\nCalibration process completed.")
    
    except serial.SerialException as e:
        print(f"\nSerial error: {str(e)}")
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
    except Exception as e:
        print(f"\nError during serial reading: {str(e)}")
    finally:
        # Make sure to close the serial connection
        try:
            ser.close()
        except:
            pass
    
    input("Press Enter to continue...")

def read_arduino():
    """Read option: Read sine and cosine values from the Arduino running LE_Reader."""
    clear_screen()
    print("=== Read Sine and Cosine Values ===")
    print("This will read sine and cosine values from an Arduino running the LE_Reader sketch.")
    print("NOTE: The Arduino must already have the LE_Reader sketch uploaded.")
    print("\nMake sure the Arduino is connected and the LE device is powered on.")
    input("Press Enter to continue...")
    
    # Load configuration
    config = load_config()
    
    # Find all connected Arduino devices
    arduino_ports = find_arduino_ports()
    if not arduino_ports:
        print("\nNo Arduino devices found. Please connect an Arduino and try again.")
        input("Press Enter to continue...")
        return
    
    # Get the Arduino port from the configuration
    arduino_port = None
    if config["target_arduino"] and config["target_arduino"]["port"]:
        arduino_port = config["target_arduino"]["port"]
        
        # Verify the port is still connected
        arduino_port_found = False
        for port in arduino_ports:
            if port["port"] == arduino_port:
                arduino_port_found = True
                break
        
        if not arduino_port_found:
            print(f"\nTarget Arduino not found at {arduino_port}.")
            print("Please run Setup again to configure the target Arduino.")
            input("Press Enter to continue...")
            return
    else:
        print("\nTarget Arduino not configured in settings.")
        print("Please run Setup first to configure the target Arduino.")
        input("Press Enter to continue...")
        return
    
    print(f"\nUsing target Arduino on port: {arduino_port}")
    
    # Read serial data from the Arduino
    print(f"\nReading data from Arduino on {arduino_port}...")
    print("\nWaiting for data...")
    
    try:
        # Open serial connection with proper buffer flushing
        ser = open_serial_with_flush(arduino_port, 115200, 1)
        
        # Initialize data collection
        cosine_values = []
        sine_values = []
        device_addresses = []
        count = 0
        max_samples = 20  # Number of samples to collect
        
        print("\nReading values (press Ctrl+C to stop):")
        print("----------------------------------------")
        print("Sample\tAddr\tCosine\tSine")
        print("----------------------------------------")
        
        # Read data until we have enough samples or user interrupts
        timeout_counter = 0
        max_timeout = 60  # 60 seconds timeout
        
        try:
            while count < max_samples and timeout_counter < max_timeout:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if ',' in line and line.count(',') == 2:  # Make sure we have valid data in format address,cosine,sine
                        try:
                            address_str, cosine_str, sine_str = line.split(',')
                            device_address = int(address_str)
                            cosine = float(cosine_str)
                            sine = float(sine_str)
                            
                            device_addresses.append(device_address)
                            cosine_values.append(cosine)
                            sine_values.append(sine)
                            
                            count += 1
                            print(f"{count}\t{device_address}\t{cosine:.2f}\t{sine:.2f}")
                            timeout_counter = 0  # Reset timeout counter on successful read
                        except ValueError:
                            # Skip invalid data
                            pass
                else:
                    time.sleep(0.1)
                    timeout_counter += 0.1
        except KeyboardInterrupt:
            print("\nReading stopped by user.")
        
        # Close the serial connection
        ser.close()
        
        if count == 0:
            print("\nNo data received. Make sure the Arduino is running the LE_Reader sketch")
            print("and that the LE device is powered on and functioning correctly.")
            input("Press Enter to continue...")
            return
        
        # Calculate statistics
        avg_cosine = sum(cosine_values) / len(cosine_values)
        avg_sine = sum(sine_values) / len(sine_values)
        
        # Find min and max values
        min_cosine = min(cosine_values)
        max_cosine = max(cosine_values)
        min_sine = min(sine_values)
        max_sine = max(sine_values)
        
        # Calculate magnitude
        magnitudes = [(c**2 + s**2)**0.5 for c, s in zip(cosine_values, sine_values)]
        avg_magnitude = sum(magnitudes) / len(magnitudes)
        
        print("\n----------------------------------------")
        print(f"Samples collected: {count}")
        print(f"Average Cosine: {avg_cosine:.2f} (range: {min_cosine:.2f} to {max_cosine:.2f})")
        print(f"Average Sine: {avg_sine:.2f} (range: {min_sine:.2f} to {max_sine:.2f})")
        print(f"Average Magnitude: {avg_magnitude:.2f}")
        print("----------------------------------------")
        
        # Suggest integer values for address_changer
        int_cosine = int(avg_cosine)
        int_sine = int(avg_sine)
        
        print("\nRecommended values for Address Changer:")
        print(f"COSINE: {int_cosine}")
        print(f"SINE: {int_sine}")
        
        # Save results to a file
        results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reading_results.txt")
        with open(results_file, 'w') as f:
            f.write(f"Reading Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("----------------------------------------\n")
            f.write("Sample\tCosine\tSine\tMagnitude\n")
            for i in range(len(cosine_values)):
                f.write(f"{i+1}\t{cosine_values[i]:.2f}\t{sine_values[i]:.2f}\t{magnitudes[i]:.2f}\n")
            f.write("----------------------------------------\n")
            f.write(f"Average Cosine: {avg_cosine:.2f} (range: {min_cosine:.2f} to {max_cosine:.2f})\n")
            f.write(f"Average Sine: {avg_sine:.2f} (range: {min_sine:.2f} to {max_sine:.2f})\n")
            f.write(f"Average Magnitude: {avg_magnitude:.2f}\n")
            f.write("\nRecommended values for Address Changer:\n")
            f.write(f"COSINE: {int_cosine}\n")
            f.write(f"SINE: {int_sine}\n")
        
        print(f"\nResults saved to {results_file}")
    
    except serial.SerialException as e:
        print(f"\nSerial error: {str(e)}")
        print("Make sure the Arduino is properly connected and not in use by another program.")
    except Exception as e:
        print(f"\nError during reading: {str(e)}")
    finally:
        # Make sure to close the serial connection
        try:
            ser.close()
        except:
            pass
    
    input("\nPress Enter to continue...")

def change_address():
    """Change address, sine, and cosine values in LE_Final settings.h file."""
    clear_screen()
    print("=== Change Address, Sine, and Cosine Values ===")
    
    # Check if LE_Final directory exists
    le_final_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LE_Final")
    if not os.path.exists(le_final_dir):
        print(f"Error: LE_Final directory not found at {le_final_dir}")
        print("Please make sure the LE_Final directory exists with the sketch files.")
        input("Press Enter to continue...")
        return
    
    try:
        # Create AddressChanger instance
        from address_changer import AddressChanger
        changer = AddressChanger(le_final_dir)
        
        # Load configuration to get UPDI programmer port
        config = load_config()
        updi_port = None
        if config["updi_programmer"]:
            updi_port = config["updi_programmer"]["port"]
            
            # Verify UPDI programmer is still connected
            arduino_ports = find_arduino_ports()
            updi_port_found = False
            
            for port in arduino_ports:
                if port["port"] == updi_port:
                    updi_port_found = True
                    break
            
            if not updi_port_found:
                print(f"UPDI programmer not found at {updi_port}.")
                print("Please reconnect the UPDI programmer or run Setup again.")
                updi_port = None
        
        # Run the workflow
        changer.change_address_workflow(updi_port)
    
    except ImportError:
        print("Error: address_changer module not found.")
        print("Please make sure the address_changer.py file is in the same directory.")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    input("Press Enter to continue...")
