import sys
import argparse
import numpy as np

from picamera2 import Picamera2
import time
import picamutils as put

import cv2 as cv
import utils as ut

if __name__ == '__main__':
    # Capturing period. For 'captrure_on_period' only.
    # t = 5000
    parser = argparse.ArgumentParser()

    parser.add_argument('-w', '--width', type=int, default=2592, help="Width of the captured image.")
    parser.add_argument('-H', '--height', type=int, default=1944, help="Height of the captured image.")
    parser.add_argument('-t', '--period', type=int, default=5000, help="Time between captures in milliseconds.")
    parser.add_argument('-b', '--buffer', type=int, default=4, help="Camera buffer count.")
    parser.add_argument('-d', '--debug', type=int, default=0, help="Debug level. [0: no debug, 1: debug_picam, 2: debug_all]")
    
    args = parser.parse_args()
    
    # Debug level
    debug = args.debug

    ## START OF Camera Mode ##################
    picam2 = Picamera2()

    print("Entering Camera Mode...")
    put.config_still(picam2, format='opencv', w=args.width, h=args.height, buf=args.buffer)

    picam2.start()
    print("Camera started. CAUTION: Camera Module v1.3 does not support autofocus.")
    time.sleep(2)

    # Variables for capture_on_period
    n = -1
    size_str = ''

    # Capture background once
    bg_model = ''
    while True:
        ans = input("Capture new background image? [Y/n] ")
        if ans.upper() == 'N':
            size_str = input("Please specify the size of background: [vga/svga/full/w?xh?] ")
            bg_model = f"./img_{size_str}_bg.jpg"
            break
        elif ans.upper() == 'Y':
            bg_model, size_str = put.capture_once(picam2, w=args.width, h=args.height, bg=True)
            break
    if debug >= 1:
        print(f"\n  DEBUG: Path to background model: {bg_model}")

    # Capture fluorescence images on period
    while True:
        ans = input(f"Start capture on period (t = {args.period} ms)? [Y/n] ")
        if ans.upper() == 'Y':    
            n, _ = put.capture_on_period(picam2, args.width, args.height, t=args.period)
            picam2.close()
            print("Camera closed. All images saved to disk.\n")
            break
        elif ans.upper() == 'N':
            picam2.close()
            print("Camera closed. No new images saved to disk.\n")
            break

    # Prompt to enter analysis mode
    while True:
        ans = input("Enter Analysis Mode? [Y/n] ")
        if ans.upper() == 'N':
            print("Exiting program before analysis...")
            sys.exit()
        elif ans.upper() == 'Y':
            break
            
    ## END OF Camera Mode ###################

    
    ## START OF Analysis Mode ################
    # Background model
    background_model = cv.imread(bg_model)
    back_gray = cv.cvtColor(background_model, cv.COLOR_BGR2GRAY)

    # Foreground fluorescence analysis (using manually-adjusted section divisions)
    if n == -1:
        n = int(input("Enter the number of images to analyse: "))
    if debug == 2:
        print(f"\n  DEBUG: Number of images previously captured to analyse: {n}")

    max_list = np.zeros(n)
    for i in range(0, n):
        fluo = cv.imread(f"./img_{size_str}_{i:04d}.jpg")
        if debug == 2:
            print(f"\n  DEBUG: Path to read image: ./img_{size_str}_{i:04d}.jpg")
        fluo_g = cv.cvtColor(fluo, cv.COLOR_BGR2GRAY)
        suback_fluog = ut.subtract_background(fluo_g, back_gray)
        avg, max_val, min_val = ut.pixel_average_analysis(suback_fluog, section_rows=6, section_cols=8, verbose=False, figure=False)
        print(f"Image {i}: Average: {avg:.2f}, Max: {max_val:.2f}, Min: {min_val:.2f}")

        max_list[i] = max_val
    
    ## END OF Analysis Mode ##################
    
    if debug == 2:
        print(f"\n  DEBUG: max_list of length {np.shape(max_list)[0]}: ")
        for a in enumerate(max_list):
            print(f"  {a}")

    print('\n')
    print(f"Min: {min(max_list):.2f}")
    print(f"Max: {max(max_list):.2f}")
    print(f"Range: {max(max_list) - min(max_list):.2f}")
