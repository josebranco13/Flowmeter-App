from gpiozero import Button
from signal import pause

# Define the GPIO pins for each specific button
BUTTON_CONFIG = {
    "Cima": 20,
    "Baixo": 16,
    "Vermelho": 5,
    "Verde": 1,
    "Azul": 7
}

# Dictionary to store the initialized Button objects
buttons = {}

def button_pressed(button_name):
    """Callback function triggered when a button is pressed."""
    print(f"[{button_name}] was pressed!")

def button_released(button_name):
    """Callback function triggered when a button is released."""
    print(f"[{button_name}] was released!")

# Initialize buttons and assign their event handlers
for name, pin in BUTTON_CONFIG.items():
    # gpiozero automatically configures the internal pull-up resistor by default
    btn = Button(pin)
    
    # We use a lambda function with a default argument (n=name) 
    # to "capture" the specific button's name during the loop.
    btn.when_pressed = lambda n=name: button_pressed(n)
    btn.when_released = lambda n=name: button_released(n)
    
    buttons[name] = btn

print("Program is running. Press any of the buttons (Press Ctrl+C to exit)...")

# Keep the program running to listen for events
pause()
