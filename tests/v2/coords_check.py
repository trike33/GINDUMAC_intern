import pyautogui
import time
import sys

print("Press Ctrl+C to quit.")

try:
    while True:
        # Get and print the current mouse position
        x, y = pyautogui.position()
        position_str = f"X: {str(x).rjust(4)} Y: {str(y).rjust(4)}"
        
        # Overwrite the previous line in the terminal
        sys.stdout.write(position_str)
        sys.stdout.write('\b' * len(position_str)) # Move cursor back
        sys.stdout.flush()
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nDone.")
