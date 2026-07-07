import RPi.GPIO as GPIO
import time

# --- Configuration ---
# GPIO Pins mapped left to right as requested: 14, 15, 18, 27, 22, 24, 25
ROW_PINS = [25, 24, 22, 27]
COL_PINS = [18, 15, 14]

# Layout matching image_edf681.png
KEYPAD = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#']
]

def setup():
    """Initializes the GPIO pins for the keypad."""
    # Use BCM GPIO numbering
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Set row pins as outputs, initialized to HIGH
    for row_pin in ROW_PINS:
        GPIO.setup(row_pin, GPIO.OUT)
        GPIO.output(row_pin, GPIO.HIGH)

    # Set column pins as inputs with internal pull-up resistors enabled
    for col_pin in COL_PINS:
        GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def read_keypad():
    """Scans the keypad matrix and returns the pressed key."""
    pressed_key = None

    for i, row_pin in enumerate(ROW_PINS):
        # Drive the current row LOW to check for connections
        GPIO.output(row_pin, GPIO.LOW)

        for j, col_pin in enumerate(COL_PINS):
            # If a button is pressed, the column pin will be pulled LOW by the row
            if GPIO.input(col_pin) == GPIO.LOW:
                pressed_key = KEYPAD[i][j]
                
                # Debounce and wait for key release to prevent multiple triggers
                while GPIO.input(col_pin) == GPIO.LOW:
                    time.sleep(0.01)

        # Reset the row to HIGH before checking the next one
        GPIO.output(row_pin, GPIO.HIGH)

    return pressed_key

if __name__ == '__main__':
    try:
        setup()
        print("Keypad initialized successfully.")
        print("Press any key (Press Ctrl+C to exit)...")
        
        while True:
            key = read_keypad()
            if key:
                print(f"Key Pressed: {key}")
            
            # Small delay to reduce CPU usage
            time.sleep(0.05) 

    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    finally:
        # Always clean up GPIO pins on exit
        GPIO.cleanup()
