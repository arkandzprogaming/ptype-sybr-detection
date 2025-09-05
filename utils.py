import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt


def pixel_average_analysis(gray, section_rows=3, section_cols=4, verbose=True, figure=True):
    '''
    SYNOPSIS
	    Applying (manually-adjusted) section divisions on a gray image to make ROI on image (brightest section).

    ARGUMENTS
	    gray         - Grayscale of standard 8-bit JPEG image buffer from OpenCV (with subtracted background).
	    section_rows - Number of section rows.
	    section_cols - Number of section columns.
	    verbose      - Outputs more information.
        figure       - Outputs plt figures.
    '''
    # Calculate overall average
    overall_avg = np.mean(gray)
    if verbose:
        print(f"Overall average pixel value: {overall_avg:.2f}")

    # Divide image into sections
    height, width = gray.shape
    section_rows = section_rows
    section_cols = section_cols

    row_size = height // section_rows
    col_size = width // section_cols

    if verbose:
        print(f"\nImage dimensions: {width} x {height}")
        print(f"Section size: {col_size} x {row_size}")
    # print("\nAverage pixel values by section:")

    # Create a matrix to store section averages
    section_averages = np.zeros((section_rows, section_cols))

    for i in range(section_rows):
        for j in range(section_cols):
            # Calculate section boundaries
            start_row = i * row_size
            end_row = (i + 1) * row_size if i < section_rows - 1 else height
            start_col = j * col_size
            end_col = (j + 1) * col_size if j < section_cols - 1 else width
            
            # Extract section
            section = gray[start_row:end_row, start_col:end_col]
	    
            # Calculate average for this section
            section_avg = np.mean(section)
            section_averages[i, j] = section_avg
            
            # print(f"Section [{i+1},{j+1}]: {section_avg:.2f}")

    # Display statistics
    if verbose:
        print(f"\nSectioned image analysis:")
        print(f"Min section average: {np.min(section_averages):.2f}")
        print(f"Max section average: {np.max(section_averages):.2f}")
        print(f"Standard deviation across sections: {np.std(section_averages):.2f}")

    # Visualize the section averages as a heatmap
    if figure:
        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.imshow(gray, cmap='gray')
        plt.title('Grayscale Image')
        plt.axis('off')

        plt.subplot(1, 2, 2)
        plt.imshow(section_averages, cmap='viridis', interpolation='nearest')
        plt.title('Average Pixel Values by Section')
        plt.colorbar(label='Average Pixel Value')
        plt.xlabel('Column Section')
        plt.ylabel('Row Section')

        # Add text annotations to show values
        for i in range(section_rows):
            for j in range(section_cols):
                plt.text(j, i, f'{section_averages[i,j]:.1f}', 
                        ha='center', va='center', color='white', fontweight='bold')

        plt.tight_layout()
        plt.show()

    return overall_avg, np.max(section_averages), np.min(section_averages)


def subtract_background(gray, background):
    '''
    SYNOPSIS
	    Subtracts background pixels from a gray image. Camera needs to be on the same position and orientation for both images.
    ARGUMENTS
	    gray       - Gray image to subtract the background from.
	    background - Image containing background without the proper subject.
    '''
    img_float = gray.astype(np.float32)
    bg_float = background.astype(np.float32)
    
    # Subtract background and clip to valid range
    result = np.clip(img_float - bg_float, 0, 255)
    return result.astype(np.uint8)


def get_roi(fluo, suback_fluog, therhold_value=8, verbose=True, figure=True):
    '''
    SYNOPSIS
        Automatically determines ROI in image using thresholding and contours. Size of ROI is unspecifiable, except the subset of pixels (percentage) of its original size and shape.
    ARGUMENTS
        fluo            - Color image (B,G,R) in standard 8-bit jpeg format
        suback_fluog    - Image with subtracted background: output of subtract_background(cv.cvtColor(fluo, cv.COLOR_BGR2GRAY), background)
        threshold_value - Pixel value between 0 to 255 to act as threshold for masking purposes. All pixel values greater than threshold become 255, otherwise 0.
        verbose         - Outputs more information. 
        figure          - Outputs plt figures.
    '''
    # Pixels brighter than 8 will become white (255), others black (0).
    threshold_value = therhold_value
    _, mask = cv.threshold(suback_fluog, threshold_value, 255, cv.THRESH_BINARY)

    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    if contours:
        # Find the largest contour by area
        largest_contour = max(contours, key=cv.contourArea)

        x, y, w, h = cv.boundingRect(largest_contour)
        cv.rectangle(fluo, (x, y), (x+w, y+h), (0, 0, 255), 2)

        if verbose:
            print(f"Found object with bounding box: x={x}, y={y}, width={w}, height={h}")
    else:
        if verbose:
            print("No object found meeting the threshold criteria.")

    if figure:
        plt.figure(figsize=(15, 5))

        # Original image with ROI marked
        plt.subplot(1, 3, 1)
        plt.imshow(cv.cvtColor(fluo, cv.COLOR_BGR2RGB))  # Convert BGR to RGB for proper display
        plt.title('Original Image with ROI Marked')
        plt.axis('off')

        # Grayscale image
        plt.subplot(1, 3, 2)
        plt.imshow(suback_fluog, cmap='gray')
        plt.title('Subtracted Grayscale Image')
        plt.axis('off')

        # Mask from thresholding
        plt.subplot(1, 3, 3)
        plt.imshow(mask, cmap='gray')
        plt.title('Mask from Thresholding')
        plt.axis('off')

        plt.tight_layout()
        plt.show()

    return x, y, w, h


def pixel_roi_analysis(gray, x, y, w, h, subset=1, verbose=True, figure=True):
    '''
    SYNOPSIS
        Takes gray image and generated ROI variables to analyse average pixel value about. 
    ARGUMENTS
        gray       - Gray image with background subtracted from.
        x, y, w, h - ROI variables
        subset     - Value between 0 and 1 to indicate a percentage of ROI size to analyse.
        verbose    - Outputs more information. 
        figure     - Outputs plt figures.
    '''
    # Calculate overall average
    overall_avg = np.mean(gray)
    if verbose:
        print(f"Overall average pixel value: {overall_avg:.2f}")

    height, width = gray.shape

    if verbose:
        print(f"\nImage dimensions: {width} x {height}")
        print(f"ROI area: Row: {x}:{x+w}, Column: {y}:{y+h}")
        print(f"ROI size: {w} x {h}")

    # Subset dictates percentage of innermost ROI pixels
    subset = subset     # Value between 0 and 1 (fraction of ROI pixels)
    if subset == 1:
        x = x
        y = y
        w = w
        h = h
    else:
        half_w = w // 2
        add_x = int(half_w * (1 - subset))
        x = x + add_x
        w = int(w * subset)

        half_h = h // 2
        add_y = int(half_h * (1 - subset))
        y = y + add_y
        h = int(h * subset)

    roi_section = gray[y:y+h, x:x+w]
    average_at_roi = np.mean(roi_section)
    std_dev_at_roi = np.std(roi_section)

    # Get image with ROI pixels replaced with average
    gray_avg_roi = gray.copy()
    for i in range(y, y + h):
        for j in range(x, x + w):
            gray_avg_roi[i, j] = average_at_roi

    # Display statistics
    if verbose:
        print(f"\Pixel analysis:")
        print(f"Average pixel value at ROI: {average_at_roi:.2f}")
        print(f"Standard deviation at ROI: {std_dev_at_roi:.2f}")

    # Visualize the section averages as a heatmap
    if figure:
        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.imshow(gray, cmap='gray')
        plt.title('Grayscale Image')
        plt.axis('off')

        plt.subplot(1, 2, 2)
        plt.imshow(gray_avg_roi, cmap='viridis', interpolation='nearest')
        plt.title('Average Pixel Value at ROI')
        plt.colorbar(label='Average Pixel Value ROI')
        plt.xlabel('Column Section')
        plt.ylabel('Row Section')

        # Add text annotations to show values
        plt.text(j, i, f'{average_at_roi:.1f}', ha='center', va='center', color='white', fontweight='bold')

        plt.tight_layout()

        plt.show()

    return overall_avg, average_at_roi


if __name__ == '__main__':
    # fluo1 = cv.imread('./test_utils/test_img.jpg')
    # background_model = cv.imread('./test_utils/test_bg.jpg')
    fluo1 = cv.imread('./img_full_0029.jpg')
    fluo1g = cv.cvtColor(fluo1, cv.COLOR_BGR2GRAY)
    background_model = cv.imread('./27072025/img_full_bg.jpg')
    back_gray = cv.cvtColor(background_model, cv.COLOR_BGR2GRAY)
    suback_fluog1 = subtract_background(fluo1g, back_gray)
    avg1g, max1g, min1g = pixel_average_analysis(suback_fluog1, section_rows=12, section_cols=16, verbose=True, figure=True)
    
    # print(f"Maximum intensity region: {max1g}")
    # print(f"Minimum intensity region: {min1g}")
