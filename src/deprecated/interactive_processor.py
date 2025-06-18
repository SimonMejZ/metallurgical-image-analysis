"""
This file was deprecated with version 1.1 and replaced with a new GUI script

This file is safe to remove

Refer to the README.md to see how the new app is used

Moved on 19/06/25 - SMZ
"""
import os
import cv2
import webbrowser

# Import the helper functions from utils file - NEW PATH (src)
from src.utils import (segment_and_extract,create_interactive_visualization,create_comparison_image)

# --- Configuration: Define base directories --- (Changed to run from root direc.)
BASE_INPUT_DIR = 'images/raw'
BASE_OUTPUT_CSV = 'data'
BASE_OUTPUT_MASKS = 'images/processed'
BASE_OUTPUT_COMPARISON = 'output/comparison_images'
BASE_OUTPUT_HTML = 'output/interactive_plots'
TEMP_HTML_PATH = 'output/temp_interactive.html' # For temporary viewing in browser - Make up for lack of inline Notebook viewing

# Helper function to get and validate user input.
def get_user_input(prompt, default, type_converter):
    while True:
        try:
            value = input(f"{prompt} (default: {default}): ")
            if value == "":
                return default
            return type_converter(value)
        except ValueError:
            print("Invalid input. Please enter a valid number.")

# Main function to run the interactive processing loop.
def main():
    # Keep track of the last used parameters to suggest as defaults
    params = {
        'sigma': 5.0, 'block_size': 251, 'threshold_factor': 0.8,
        'min_size': 2000, 'hole_size': 1000
    }
    
    # Loop through all images in the raw directory structure
    for dirpath, _, filenames in os.walk(BASE_INPUT_DIR):
        for image_file in filenames:
            if not image_file.lower().endswith('.jpg'): # Make sure images are saved as JPGs
                continue

            full_image_path = os.path.join(dirpath, image_file)
            original_image = cv2.imread(full_image_path)

            # This is the inner loop for getting user approval
            while True:
                # Get parameters from the user usnog helper function
                # General use: param[] = func({prompt}, {default}, {dtype})
                params['sigma'] = get_user_input("Enter sigma value", params['sigma'], float)
                params['block_size'] = get_user_input("Enter block_size", params['block_size'], int)
                params['threshold_factor'] = get_user_input("Enter threshold_factor", params['threshold_factor'], float)
                params['min_size'] = get_user_input("Enter min_size", params['min_size'], int)
                params['hole_size'] = get_user_input("Enter hole_size", params['hole_size'], int)

                # Process the image with the given parameters - call master processing function - now in src folder
                df_results, mask_image, labels = segment_and_extract(original_image, **params)
                
                # --- Display Results for Approval ---
                # Show the mask image in a window
                cv2.imshow(f"Generated Mask for {image_file}", mask_image.astype('uint8') * 255)
                cv2.waitKey(0) # Wait for a key press
                cv2.destroyAllWindows() 

                # Show the interactive plot in the browser
                # Calls master Plotly function - Now in src folder
                create_interactive_visualization(labels, original_image, TEMP_HTML_PATH)
                print(f"Opening interactive plot in browser...")
                webbrowser.open('file://' + os.path.realpath(TEMP_HTML_PATH))
                
                # --- Get User Approval ---
                satisfied = input("Are you satisfied with this result? (y/n): ").lower()
                
                if satisfied == 'y':
                    print("Result approved. Saving files...")
                    
                    # --- Setup Paths for Saving ---
                    sample_type = os.path.basename(dirpath)
                    base_name = os.path.splitext(image_file)[0]
                    
                    # Create corresponding output directories if they don't exist
                    for path in [BASE_OUTPUT_CSV, BASE_OUTPUT_MASKS, BASE_OUTPUT_COMPARISON, BASE_OUTPUT_HTML]:
                        os.makedirs(os.path.join(path, sample_type), exist_ok=True)
                    
                    # Construct full output paths
                    csv_path = os.path.join(BASE_OUTPUT_CSV, sample_type, f"{base_name}_properties.csv")
                    mask_path = os.path.join(BASE_OUTPUT_MASKS, sample_type, f"{base_name}_mask.png")
                    comparison_path = os.path.join(BASE_OUTPUT_COMPARISON, sample_type, f"{base_name}_comparison.png")
                    html_path = os.path.join(BASE_OUTPUT_HTML, sample_type, f"{base_name}_interactive.html")
                    
                    # --- Save Final Files ---
                    df_results.to_csv(csv_path, index=False)
                    cv2.imwrite(mask_path, mask_image.astype('uint8') * 255)
                    create_comparison_image(original_image, labels, comparison_path)
                    create_interactive_visualization(labels, original_image, html_path)
                    
                    print(f"  -> Saved data to {csv_path}")
                    print(f"  -> Saved mask, comparison, and interactive plot.")
                    break # Exit the 'while' loop and move to the next image
                else:
                    print("Result rejected. Please enter new parameters.")

    print("\n All images processed.")

if __name__ == '__main__':
    main()