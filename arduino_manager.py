import os
import sys

# Import modular components
from arduino_utils import clear_screen
from arduino_operations import setup_arduinos, program_arduino, read_arduino, change_address
from arduino_advanced import check_dependencies, compile_attiny_code, upload_attiny_code, run_le_test

# Create Hex directory if it doesn't exist
HEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Hex")
if not os.path.exists(HEX_DIR):
    os.makedirs(HEX_DIR)

def main_menu():
    """Display the main menu and handle user input."""
    while True:
        clear_screen()
        print("=== Arduino Programmer ===")
        print("1. Setup")
        print("2. Program")
        print("3. Read")
        print("4. Check Dependencies")
        print("5. Exit")
        
        try:
            choice = int(input("\nEnter your choice (1-5): "))
            
            if choice == 1:
                setup_arduinos()
            elif choice == 2:
                program_arduino()
            elif choice == 3:
                read_arduino()
            elif choice == 4:
                check_dependencies()
            elif choice == 5:
                print("Exiting...")
                sys.exit(0)
            # Hidden options - not shown in menu but code remains
            elif choice == 6:
                compile_attiny_code()
            elif choice == 7:
                upload_attiny_code()
            elif choice == 8:
                run_le_test()
            elif choice == 9:
                change_address()
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
                input("Press Enter to continue...")
        
        except ValueError:
            print("Invalid input. Please enter a number.")
            input("Press Enter to continue...")
        except Exception as e:
            print(f"Error: {str(e)}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main_menu()
