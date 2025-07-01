// I2C Scanner and Reader
// Scans addresses 0-127 once and continuously reads from found devices

#include <Wire.h>

// Number of bytes to request from each device found
#define BYTES_TO_REQUEST 6  // Just enough for sine and cosine values

bool scanComplete = false;
byte foundDevices[128]; // Array to store found device addresses
int deviceCount = 0;    // Number of devices found

void setup() {
  Wire.begin();        // join I2C bus as master
  Serial.begin(115200);  // start serial for output
  
  // Initialize foundDevices array
  for (int i = 0; i < 128; i++) {
    foundDevices[i] = 0; // 0 means not found/not valid
  }
}

void loop() {
  if (!scanComplete) {
    // First scan to find devices
    scanI2CBus();
    scanComplete = true;
  } else {
    // After scan is complete, continuously read from found devices
    readFromFoundDevices();
    delay(100); // 100ms delay between readings
  }
}

void scanI2CBus() {
  byte error, address;
  
  // Scan through all possible I2C addresses (0-127)
  for (address = 0; address <= 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    
    if (error == 0) {
      // Device found at this address, store it
      foundDevices[deviceCount++] = address;
    }
  }
}

void readFromFoundDevices() {
  // Read from each found device
  for (int i = 0; i < deviceCount; i++) {
    byte address = foundDevices[i];
    if (address > 0) { // Valid device address
      readFromDevice(address);
    }
  }
}

void readFromDevice(byte address) {
  // Request data from the device
  Wire.requestFrom(address, BYTES_TO_REQUEST);
  
  // Check if any data is available
  if (Wire.available()) {
    byte data[BYTES_TO_REQUEST];
    int index = 0;
    
    while (Wire.available() && index < BYTES_TO_REQUEST) {
      data[index] = Wire.read();
      index++;
    }
    
    // If we received enough data for sine and cosine
    if (index >= 5) {
      int abs1 = (data[0] << 8) | data[1]; // First two bytes for distance
      int cosine = (data[2] << 8) | data[3]; // First two bytes for cosine
      int sine = (data[4] << 8) | data[5];   // Next two bytes for sine
      
      // Print in format: address,cosine,sine
      // Serial.print(abs1);
      // Serial.print(',');
      Serial.print(address);
      Serial.print(',');
      Serial.print(cosine);
      Serial.print(',');
      Serial.println(sine);
    }
  }
}
