import pyautogui

# --- Step 1: Get the Top-Left Corner ---
input("Move your mouse to the TOP-LEFT corner of the region and press Enter...")
x1, y1 = pyautogui.position()
print(f"Top-left corner recorded at: ({x1}, {y1})")

# --- Step 2: Get the Bottom-Right Corner ---
input("\nNow, move your mouse to the BOTTOM-RIGHT corner of the region and press Enter...")
x2, y2 = pyautogui.position()
print(f"Bottom-right corner recorded at: ({x2}, {y2})")

# --- Step 3: Calculate the Region ---
# The 'left' is the smaller x-coordinate, 'top' is the smaller y-coordinate.
left = x1
top = y1
width = x2 - x1
height = y2 - y1

# Ensure width and height are positive
if width < 0 or height < 0:
    print("\nError: The bottom-right corner must have larger coordinates than the top-left corner.")
else:
    # The final region tuple, ready to be used in your main script
    region_tuple = (left, top, width, height)
    print("\n----------------------------------------------------")
    print(f"✅ Your calculated region is: {region_tuple}")
    print("----------------------------------------------------")
    print("You can now use this tuple in functions like pyautogui.screenshot(region=your_region)")
