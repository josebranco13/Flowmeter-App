import RPi.GPIO as GPIO
import time

# --- Configuration ---
FLOW_SENSOR_PIN = 21
# 7.5 pulses per second = 1 L/min. 
# Therefore, 1 Liter = 7.5 * 60 seconds = 450 pulses.
PULSES_PER_LITER = 450.0 

# Global variables for tracking state
total_pulses = 0
first_pulse_time = 0.0
last_pulse_time = 0.0

def count_pulse(channel):
    """Callback function triggered by the hardware interrupt."""
    global total_pulses, first_pulse_time, last_pulse_time
    
    # If this is the first pulse of a new flow event, record the start time
    if total_pulses == 0:
        first_pulse_time = time.time()
        
    total_pulses += 1
    # Constantly update the last seen pulse time
    last_pulse_time = time.time()

def setup():
    """Initializes the GPIO pins and interrupts."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(FLOW_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(FLOW_SENSOR_PIN, GPIO.FALLING, callback=count_pulse)

def main():
    global total_pulses
    setup()
    
    is_flowing = False
    
    print("System ready. Waiting for water flow... (Press Ctrl+C to exit)")
    
    try:
        while True:
            # Check the state twice a second
            time.sleep(0.5) 
            current_time = time.time()
            
            # 1. Detect start of flow
            if total_pulses > 0 and not is_flowing:
                is_flowing = True
                print("\n[+] Water started flowing!")
            
            # 2. Detect end of flow (if no pulses received for 1.5 seconds)
            if is_flowing and (current_time - last_pulse_time > 1.5):
                is_flowing = False
                
                # Calculate the exact duration between the first and last pulse
                flow_duration_sec = last_pulse_time - first_pulse_time
                
                print("[-] Water stopped.")
                
                # Prevent division by zero if it was just a tiny splash (1 pulse)
                if flow_duration_sec > 0:
                    # Calculate metrics
                    total_liters = total_pulses / PULSES_PER_LITER
                    flow_duration_min = flow_duration_sec / 60.0
                    avg_flow_rate = total_liters / flow_duration_min
                    
                    print("-" * 35)
                    print(f"Flow Duration: {flow_duration_sec:.2f} seconds")
                    print(f"Total Volume:  {total_liters:.3f} Liters")
                    print(f"Avg Flow Rate: {avg_flow_rate:.2f} L/min")
                    print("-" * 35)
                else:
                    print("-> Flow was too brief to calculate averages.")
                
                # Reset the counter to be ready for the next time water starts
                total_pulses = 0
                
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Cleaning up...")
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    main()
