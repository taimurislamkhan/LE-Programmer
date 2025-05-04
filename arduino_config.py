import os
import json

# Constants
CONFIG_FILE = "arduino_config.json"
HEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Hex")
BLINK_HEX = os.path.join(HEX_DIR, "LED_Blink.ino.hex")
UPDI_HEX = os.path.join(HEX_DIR, "jtag2updi.ino.hex")

def save_config(config):
    """Save configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_config():
    """Load configuration from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            # Ensure all required keys exist
            if "updi_programmer" not in config:
                config["updi_programmer"] = None
            if "target_arduino" not in config:
                config["target_arduino"] = None
            
            return config
        except json.JSONDecodeError:
            print(f"Error: {CONFIG_FILE} is not a valid JSON file.")
    
    # Return default configuration if file doesn't exist or is invalid
    return {
        "updi_programmer": None,
        "target_arduino": None
    }
