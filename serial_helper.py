import time
import serial

def open_serial_with_flush(port, baud_rate=115200, timeout=1):
    """
    Open a serial connection and properly flush all buffers to ensure fresh data.
    
    Args:
        port (str): Serial port to open
        baud_rate (int): Baud rate for the connection
        timeout (int): Read timeout in seconds
        
    Returns:
        serial.Serial: Open serial connection with flushed buffers
    """
    # Open the serial connection
    ser = serial.Serial(port, baud_rate, timeout=timeout)
    
    # Wait for connection to establish
    time.sleep(2)
    
    # Flush any stale data in the buffer
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    
    # Additional wait to ensure buffer is truly cleared
    time.sleep(0.5)
    
    # Discard any data that might have arrived during the flush
    while ser.in_waiting > 0:
        ser.read(ser.in_waiting)
    
    return ser
