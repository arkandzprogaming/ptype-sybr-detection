from picamera2 import Picamera2
import numpy as np
import time

'''
SYNOPSIS
    Functions to capture still images with specifiable attributes, including output encoding, dimension, buffer count, etc. 
'''

# Configure camera
def config_still(picam2, format='opencv', w=800, h=600, buf=4):
    if format == 'opencv':
        color = 'RGB888'
    elif format == 'alpha-opencv':
        color = 'XRGB8888'
    else:
        print(f"Unexpected format: {format}\nTry 'opencv' or 'alpha-opencv'")

    config = picam2.create_still_configuration(
        buffer_count=buf,
        main={"format": color, "size": (w, h)}
        ,controls={"AwbEnable": True, "AwbMode": 0}
    )
    picam2.configure(config)
    print("Camera configured.")

# Capture an image on key press
def capture_on_key(picam2, w, h, control=False):
    match w - h:
        case 160:
            size_str = 'vga'
        case 200:
            size_str = 'svga'
        case 648:
            size_str = 'full'
        case _:
            size_str = f"{w}x{h}"
    n = -1
    while True:
        if input('Waiting for capture signal (L)... ').upper() == 'L' :
            if control:
                with picam2.controls as controls:
                    #controls.ExposureTime = int(input("ExposureTime: [default 20000] "))
                    #controls.AnalogueGain = int(input("AnalogueGain: [default 1.0] "))
                    controls.AwbEnable = bool(input("AwbEnable: [default True] "))
                    if controls.AwbEnable:
                        controls.AwbMode = int(input("AwbMode: [default 0 (Auto)] "))
                time.sleep(1.5)

            n = n + 1
            filename_jpg = f"img_{size_str}_{n:04d}.jpg"
            picam2.capture_file(filename_jpg)
            print("Capture complete.")
        else:
            break

# Capture an image once every specifiable period
def capture_on_period(picam2, w, h, t=5000):
    match w - h:
        case 160:
            size_str = 'vga'
        case 200:
            size_str = 'svga'
        case 648:
            size_str = 'full'
        case _:
            size_str = f"{w}x{h}"
    n = -1
    try:
        while True:
            n = n + 1
            filename_jpg = f"img_{size_str}_{n:04d}.jpg"

            picam2.capture_file(filename_jpg)
            print(f"[cap = {n+1}] Capture complete.")
            print("Preparing to capture... (Exit with Ctrl+C)")
            time.sleep(t / 1000)
    except KeyboardInterrupt:
        print(f": Number of images captured: {n + 1}.\nExiting function...")

    return n + 1, size_str

# Capture image once
def capture_once(picam2, w, h, control=False, bg=False):
    match w - h:
        case 160:
            size_str = 'vga'
        case 200:
            size_str = 'svga'
        case 648:
            size_str = 'full'
        case _:
            size_str = f"{w}x{h}"
    if bg:
        filename_jpg = f"./img_{size_str}_bg.jpg"
    else:
        filename_jpg = f"./img_{size_str}_once.jpg"

    if control:
        with picam2.controls as controls:
            # controls.AwbMode = int(input("AwbMode: [default 0 (Auto)] "))
            controls.AwbEnable = bool(input("AwbEnable: [default True] "))
            if controls.AwbEnable:
                controls.AwbMode = int(input("AwbMode: [default 0 (Auto)] "))

    time.sleep(1.5)
    picam2.capture_file(filename_jpg)
    print("Capture complete.\n")

    return filename_jpg, size_str


if __name__ == "__main__":
    picam2 = Picamera2()
    w = 2592
    h = 1944
    t = 15000
    buf = 4

    config_still(picam2, format='opencv', w=w, h=h, buf=buf)
    picam2.start()
    print("Camera started. Give it a moment to adjust...")
    time.sleep(2)

    ans = input("Specify type of test: [once/onkey/period] ")
    if ans == "once":
        sceneType = bool(input("Background? [Press Enter if false] "))
        capture_once(picam2, w, h, control=True, bg = sceneType)
    elif ans == "onkey":
        capture_on_key(picam2, w, h, control=True)
    elif ans == "period":
        capture_on_period(picam2, w, h, t=t)
    else:
        print(f"Error. No choice {ans} is available.")

    picam2.close()
