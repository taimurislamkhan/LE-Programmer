import os
import subprocess
import sys
import json
import shutil
import tempfile
import time

class ArduinoCompiler:
    def __init__(self):
        # Paths to Arduino tools and libraries
        self.arduino_path = self._find_arduino_path()
        self.avr_gcc_path = self._find_avr_gcc_path()
        self.core_path = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Arduino15', 'packages', 'megaTinyCore', 'hardware', 'megaavr', '2.6.10')
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'arduino_compiler')
        
        # Create temp directory if it doesn't exist
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def _find_arduino_path(self):
        """Find the Arduino installation directory."""
        possible_paths = [
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Arduino'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Arduino')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _find_avr_gcc_path(self):
        """Find the avr-gcc tools path."""
        possible_paths = [
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Arduino15', 'packages', 'DxCore', 'tools', 'avr-gcc', '7.3.0-atmel3.6.1-azduino7b1', 'bin'),
            os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Arduino15', 'packages', 'arduino', 'tools', 'avr-gcc', '7.3.0-atmel3.6.1-azduino7b1', 'bin')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def compile_attiny1616(self, sketch_path, output_dir=None):
        """Compile an Arduino sketch for ATtiny1616."""
        if not os.path.exists(sketch_path):
            print(f"Error: Sketch file {sketch_path} not found.")
            return False
        
        # If output_dir is not specified, use the sketch directory
        if output_dir is None:
            output_dir = os.path.dirname(sketch_path)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Get sketch name without extension
        sketch_name = os.path.basename(sketch_path)
        if sketch_name.endswith('.ino'):
            sketch_name = sketch_name[:-4]
        
        # Create a temporary directory for compilation
        build_dir = os.path.join(self.temp_dir, sketch_name)
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir)
        
        # Copy the sketch to the build directory
        sketch_copy = os.path.join(build_dir, os.path.basename(sketch_path))
        shutil.copy2(sketch_path, sketch_copy)
        
        print(f"Compiling {sketch_name} for ATtiny1616...")
        
        # Check if required tools are available
        if not self.avr_gcc_path:
            print("Error: avr-gcc tools not found. Please install the Arduino IDE with megaTinyCore.")
            return False
        
        # Paths to core files
        core_dir = os.path.join(self.core_path, 'cores', 'megatinycore')
        variant_dir = os.path.join(self.core_path, 'variants', 'txy6')
        wire_lib_dir = os.path.join(self.core_path, 'libraries', 'Wire', 'src')
        
        # Check if core files exist
        if not os.path.exists(core_dir):
            print(f"Error: Core directory {core_dir} not found.")
            return False
        
        if not os.path.exists(variant_dir):
            print(f"Error: Variant directory {variant_dir} not found.")
            return False
        
        # Compile the sketch
        try:
            # Step 1: Create a combined sketch file with all function prototypes
            print("Creating combined sketch file...")
            
            # Read the sketch file
            with open(sketch_copy, 'r') as f:
                sketch_content = f.read()
            
            # Extract function declarations
            function_declarations = []
            function_pattern = r'\b(void|int|float|double|boolean|bool|char|byte|unsigned|long|short|size_t|String)\s+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{'
            
            import re
            matches = re.finditer(function_pattern, sketch_content)
            
            # Arduino special functions that should not have prototypes
            arduino_special_functions = ['setup', 'loop']
            
            for match in matches:
                return_type = match.group(1)
                function_name = match.group(2)
                
                # Skip Arduino special functions
                if function_name in arduino_special_functions:
                    continue
                
                # Find the function signature (everything up to the opening brace)
                start_pos = match.start()
                signature_end = sketch_content.find('{', start_pos)
                if signature_end != -1:
                    signature = sketch_content[start_pos:signature_end].strip()
                    # Add semicolon to make it a prototype
                    function_declarations.append(f"{signature};")
            
            # Create a new sketch file with function prototypes at the top
            combined_sketch = os.path.join(build_dir, f"{sketch_name}_combined.ino")
            
            # Find the first include statement or the first non-comment, non-empty line
            include_pattern = r'#include\s+[<"].*[>"]'
            first_include = re.search(include_pattern, sketch_content)
            
            if first_include:
                insert_pos = first_include.start()
                new_content = sketch_content[:insert_pos] + '\n// Function prototypes\n' + '\n'.join(function_declarations) + '\n\n' + sketch_content[insert_pos:]
            else:
                # If no include is found, add prototypes at the top after any initial comments
                new_content = '// Function prototypes\n' + '\n'.join(function_declarations) + '\n\n' + sketch_content
            
            with open(combined_sketch, 'w') as f:
                f.write(new_content)
            
            # Create a temporary .cpp file for Arduino compilation
            # This is necessary because Arduino expects .ino files to be preprocessed in a specific way
            print("Creating temporary .cpp file...")
            cpp_file = os.path.join(build_dir, f"{sketch_name}.cpp")
            
            # Add Arduino header at the top
            with open(cpp_file, 'w') as f:
                f.write('#include <Arduino.h>\n\n')
                f.write(new_content)
            
            # Step 2: Preprocess the sketch
            print("Preprocessing sketch...")
            preprocessed_file = os.path.join(build_dir, f"{sketch_name}_preprocessed.cpp")
            
            preprocess_cmd = [
                os.path.join(self.avr_gcc_path, "avr-g++"),
                "-c", "-g", "-Os", "-Wall", "-std=gnu++17", "-fpermissive",
                "-Wno-sized-deallocation", "-fno-exceptions", "-ffunction-sections",
                "-fdata-sections", "-fno-threadsafe-statics", "-Wno-error=narrowing",
                "-flto", "-mrelax", "-w", "-x", "c++", "-E", "-CC",
                "-mmcu=attiny1616", "-DF_CPU=20000000L", "-DCLOCK_SOURCE=0",
                "-DTWI_MORS", "-DMILLIS_USE_TIMERD0", "-DCORE_ATTACH_ALL",
                "-DUSE_TIMERD0_PWM", "-DARDUINO=10607", "-DARDUINO_AVR_ATtiny1616",
                "-DARDUINO_ARCH_MEGAAVR", f'-DMEGATINYCORE="2.6.10"',
                "-DMEGATINYCORE_MAJOR=2UL", "-DMEGATINYCORE_MINOR=6UL",
                "-DMEGATINYCORE_PATCH=10UL", "-DMEGATINYCORE_RELEASED=1",
                "-DARDUINO_attinyxy6",
                f"-I{os.path.join(core_dir, 'api', 'deprecated')}",
                f"-I{core_dir}",
                f"-I{variant_dir}",
                f"-I{wire_lib_dir}",
                cpp_file,
                "-o", preprocessed_file
            ]
            
            self._run_command(preprocess_cmd)
            
            # Step 2: Compile the sketch
            print("Compiling sketch...")
            compiled_file = os.path.join(build_dir, f"{sketch_name}.o")
            
            compile_cmd = [
                os.path.join(self.avr_gcc_path, "avr-g++"),
                "-c", "-g", "-Os", "-Wall", "-std=gnu++17", "-fpermissive",
                "-Wno-sized-deallocation", "-fno-exceptions", "-ffunction-sections",
                "-fdata-sections", "-fno-threadsafe-statics", "-Wno-error=narrowing",
                "-MMD", "-flto", "-mrelax",
                "-mmcu=attiny1616", "-DF_CPU=20000000L", "-DCLOCK_SOURCE=0",
                "-DTWI_MORS", "-DMILLIS_USE_TIMERD0", "-DCORE_ATTACH_ALL",
                "-DUSE_TIMERD0_PWM", "-DARDUINO=10607", "-DARDUINO_AVR_ATtiny1616",
                "-DARDUINO_ARCH_MEGAAVR", f'-DMEGATINYCORE="2.6.10"',
                "-DMEGATINYCORE_MAJOR=2UL", "-DMEGATINYCORE_MINOR=6UL",
                "-DMEGATINYCORE_PATCH=10UL", "-DMEGATINYCORE_RELEASED=1",
                "-DARDUINO_attinyxy6",
                f"-I{os.path.join(core_dir, 'api', 'deprecated')}",
                f"-I{core_dir}",
                f"-I{variant_dir}",
                f"-I{wire_lib_dir}",
                cpp_file,  # Use the cpp file directly instead of preprocessed file
                "-o", compiled_file
            ]
            
            self._run_command(compile_cmd)
            
            # Step 3: Compile Wire library
            print("Compiling Wire library...")
            wire_cpp = os.path.join(wire_lib_dir, "Wire.cpp")
            wire_o = os.path.join(build_dir, "Wire.o")
            
            wire_cmd = [
                os.path.join(self.avr_gcc_path, "avr-g++"),
                "-c", "-g", "-Os", "-Wall", "-std=gnu++17", "-fpermissive",
                "-Wno-sized-deallocation", "-fno-exceptions", "-ffunction-sections",
                "-fdata-sections", "-fno-threadsafe-statics", "-Wno-error=narrowing",
                "-MMD", "-flto", "-mrelax",
                "-mmcu=attiny1616", "-DF_CPU=20000000L", "-DCLOCK_SOURCE=0",
                "-DTWI_MORS", "-DMILLIS_USE_TIMERD0", "-DCORE_ATTACH_ALL",
                "-DUSE_TIMERD0_PWM", "-DARDUINO=10607", "-DARDUINO_AVR_ATtiny1616",
                "-DARDUINO_ARCH_MEGAAVR", f'-DMEGATINYCORE="2.6.10"',
                "-DMEGATINYCORE_MAJOR=2UL", "-DMEGATINYCORE_MINOR=6UL",
                "-DMEGATINYCORE_PATCH=10UL", "-DMEGATINYCORE_RELEASED=1",
                "-DARDUINO_attinyxy6",
                f"-I{os.path.join(core_dir, 'api', 'deprecated')}",
                f"-I{core_dir}",
                f"-I{variant_dir}",
                f"-I{wire_lib_dir}",
                wire_cpp,
                "-o", wire_o
            ]
            
            self._run_command(wire_cmd)
            
            # Step 4: Compile twi.c
            twi_c = os.path.join(wire_lib_dir, "twi.c")
            twi_o = os.path.join(build_dir, "twi.o")
            
            twi_cmd = [
                os.path.join(self.avr_gcc_path, "avr-gcc"),
                "-c", "-g", "-Os", "-Wall", "-std=gnu11", "-ffunction-sections",
                "-fdata-sections", "-MMD", "-flto", "-mrelax",
                "-mmcu=attiny1616", "-DF_CPU=20000000L", "-DCLOCK_SOURCE=0",
                "-DTWI_MORS", "-DMILLIS_USE_TIMERD0", "-DCORE_ATTACH_ALL",
                "-DUSE_TIMERD0_PWM", "-DARDUINO=10607", "-DARDUINO_AVR_ATtiny1616",
                "-DARDUINO_ARCH_MEGAAVR", f'-DMEGATINYCORE="2.6.10"',
                "-DMEGATINYCORE_MAJOR=2UL", "-DMEGATINYCORE_MINOR=6UL",
                "-DMEGATINYCORE_PATCH=10UL", "-DMEGATINYCORE_RELEASED=1",
                "-DARDUINO_attinyxy6",
                f"-I{os.path.join(core_dir, 'api', 'deprecated')}",
                f"-I{core_dir}",
                f"-I{variant_dir}",
                f"-I{wire_lib_dir}",
                twi_c,
                "-o", twi_o
            ]
            
            self._run_command(twi_cmd)
            
            # Step 5: Compile twi_pins.c
            twi_pins_c = os.path.join(wire_lib_dir, "twi_pins.c")
            twi_pins_o = os.path.join(build_dir, "twi_pins.o")
            
            twi_pins_cmd = [
                os.path.join(self.avr_gcc_path, "avr-gcc"),
                "-c", "-g", "-Os", "-Wall", "-std=gnu11", "-ffunction-sections",
                "-fdata-sections", "-MMD", "-flto", "-mrelax",
                "-mmcu=attiny1616", "-DF_CPU=20000000L", "-DCLOCK_SOURCE=0",
                "-DTWI_MORS", "-DMILLIS_USE_TIMERD0", "-DCORE_ATTACH_ALL",
                "-DUSE_TIMERD0_PWM", "-DARDUINO=10607", "-DARDUINO_AVR_ATtiny1616",
                "-DARDUINO_ARCH_MEGAAVR", f'-DMEGATINYCORE="2.6.10"',
                "-DMEGATINYCORE_MAJOR=2UL", "-DMEGATINYCORE_MINOR=6UL",
                "-DMEGATINYCORE_PATCH=10UL", "-DMEGATINYCORE_RELEASED=1",
                "-DARDUINO_attinyxy6",
                f"-I{os.path.join(core_dir, 'api', 'deprecated')}",
                f"-I{core_dir}",
                f"-I{variant_dir}",
                f"-I{wire_lib_dir}",
                twi_pins_c,
                "-o", twi_pins_o
            ]
            
            self._run_command(twi_pins_cmd)
            
            # Step 6: Use the existing core.a file
            print("Using existing core.a file...")
            core_a = os.path.join(os.path.dirname(sketch_path), "core.a")
            
            if not os.path.exists(core_a):
                print(f"Error: core.a not found at {core_a}")
                return False
            
            print(f"Found core.a at: {core_a}")
            
            # Step 7: Link everything together
            print("Linking...")
            elf_file = os.path.join(build_dir, f"{sketch_name}.elf")
            
            link_cmd = [
                os.path.join(self.avr_gcc_path, "avr-gcc"),
                "-Wall", "-Os", "-g", "-flto", "-fuse-linker-plugin",
                "-Wl,--gc-sections", "-Wl,--section-start=.text=0x0",
                "-mrelax", "-mmcu=attiny1616",
                "-o", elf_file,
                compiled_file, wire_o, twi_o, twi_pins_o, core_a,
                f"-L{build_dir}", "-lm"
            ]
            
            self._run_command(link_cmd)
            
            # Step 7: Generate hex file
            print("Generating hex file...")
            hex_file = os.path.join(build_dir, f"{sketch_name}.hex")
            
            hex_cmd = [
                os.path.join(self.avr_gcc_path, "avr-objcopy"),
                "-O", "ihex", "-R", ".eeprom",
                elf_file, hex_file
            ]
            
            self._run_command(hex_cmd)
            
            # Copy the hex file to the output directory
            output_hex = os.path.join(output_dir, f"{sketch_name}.hex")
            shutil.copy2(hex_file, output_hex)
            
            print(f"Compilation successful! Hex file saved to: {output_hex}")
            return True
            
        except Exception as e:
            print(f"Error during compilation: {str(e)}")
            return False
    
    def _run_command(self, cmd):
        """Run a command and print its output."""
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                print(f"Command failed with return code {process.returncode}")
                print(f"Command: {' '.join(cmd)}")
                print(f"Error output: {stderr}")
                raise Exception(f"Command failed with return code {process.returncode}")
            
            return stdout
        except Exception as e:
            print(f"Error running command: {str(e)}")
            raise

def main():
    """Main function for standalone usage."""
    if len(sys.argv) < 2:
        print("Usage: python arduino_compiler.py <sketch_path> [output_dir]")
        return
    
    sketch_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    compiler = ArduinoCompiler()
    compiler.compile_attiny1616(sketch_path, output_dir)

if __name__ == "__main__":
    main()
