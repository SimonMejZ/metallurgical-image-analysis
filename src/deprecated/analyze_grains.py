"""
This file is no longer in use but rather kept as a record of the old workflow.

This file has been separated into a utility file containing the helper functions, and a UI script used by the user.

Refer to the README.md to see how the new workflow is used

Moved on 17/06/2025
"""

import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from skimage.measure import find_contours, regionprops
from skimage.filters import gaussian, threshold_local
from skimage.measure import label, regionprops_table
from skimage.morphology import remove_small_objects, remove_small_holes, opening, disk
import os

def process_image(image_path, sigma, block_size, threshold_factor, min_size, hole_size):
    """
    Loads, processes, and analyses a single metallurgical image from the images/raw directory
    
    Arguments:
        image_path (str): The full path to the input image.
        sigma (int): The sigma value for the blur.
        block_size (int): The block size for local thresholding.
        threshold_factor (float): A factor to adjust the threshold.
        min_size (int): The minimum size (in pixels) for objects to keep.
        hole_size (int): The maximum size (in pixels) for holes to fill.
    """
    
    # ---Load and preprocess the image---
    original_image = cv2.imread(image_path)
    
    img_grey = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
    img_gaus = gaussian(img_grey, sigma=sigma)
    
    # ---Apply thresholding---
  
    #Ensure block_size is odd
    if block_size % 2 == 0:
        block_size += 1
        
    local_thresh = threshold_local(img_gaus, block_size)
    binary_mask = img_gaus > local_thresh * threshold_factor
    
    # ---Clean up the mask using morphology---
    #  'opening' operation removes small objects
    cleaned_mask = opening(binary_mask, disk(2)) 
    cleaned_mask = remove_small_objects(cleaned_mask, min_size=min_size)
    cleaned_mask = remove_small_holes(cleaned_mask, area_threshold=hole_size)
    
    # ---Label and extract properties---
    labels = label(cleaned_mask)
    properties = [
        'area', 
        'perimeter', 
        'eccentricity', 
        'solidity',
        'equivalent_diameter', # The diameter of a circle with the same area as the grain
        'orientation',         # Angle of the major axis from the horizontal
        'major_axis_length',
        'minor_axis_length'
    ]
    
    # We pass the grayscale image to measure intensity properties
    props_table = regionprops_table(
        labels, 
        intensity_image=img_grey, 
        properties=properties
    )
    
    df = pd.DataFrame(props_table)

    return df, cleaned_mask, labels, original_image

def create_comparison_image(original_image, final_mask, output_image_path):
    """
    Creates and saves a side-by-side comparison PNG of the original and the mask.
    """
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    ax = axes.ravel()
    
    ax[0].imshow(cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY), cmap='gray')
    ax[0].set_title('Original Image')
    ax[0].axis('off')
    
    ax[1].imshow(final_mask, cmap='viridis') # Using viridis to see labels
    ax[1].set_title('Segmented Grains Mask')
    ax[1].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_image_path)
    plt.close(fig) # Close the figure to free up memory

def create_interactive_visualization(labels, original_image, output_html_path):
    """
    Creates an interactive Plotly HTML file with grain boundaries overlaid.
    """
    fig = go.Figure(go.Image(z=cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)))
    
    # Get properties for hover-over text
    props = regionprops(labels)
    
    for index in range(labels.max()):
        # Find the contour of the current grain
        contour = find_contours(labels == (index + 1), 0.5)[0]
        y, x = contour.T
        
        # Get properties for this specific grain
        current_prop = props[index]
        hover_info = (f"<b>Grain ID: {current_prop.label}</b><br>"
                      f"Area: {current_prop.area} pixels<br>"
                      f"Solidity: {current_prop.solidity:.3f}<br>"
                      f"Eccentricity: {current_prop.eccentricity:.3f}")

        fig.add_trace(go.Scatter(
            x=x, y=y, 
            mode='lines', 
            fill='toself', 
            showlegend=False,
            hovertemplate=hover_info,
            hoveron='points+fills',
            line=dict(color='rgba(0, 255, 0, 0.7)', width=2)
        ))
    
    fig.update_layout(title='Interactive Grain Segmentation', hovermode='closest')
    fig.write_html(output_html_path)

if __name__ == '__main__':    
    # ---Configuration---

    # Define input and output folders
    BASE_INPUT_DIR = 'images/raw'
    BASE_OUTPUT_CSV = 'data'
    BASE_OUTPUT_MASKS = 'images/processed'
    BASE_OUTPUT_COMPARISON = 'output/comparison_images'
    BASE_OUTPUT_HTML = 'output/interactive_plots'

    # --- Processing ---
    for dirpath, _, filenames in os.walk(BASE_INPUT_DIR):
            for image_file in filenames:
                if image_file.lower().endswith(('.jpg', '.png', '.tif')):
                    
                    #Setup Paths
                    full_image_path = os.path.join(dirpath, image_file)
                    print(f"Processing {full_image_path}...")
                    
                    # Get Sample name (metal type)
                    sample_type = os.path.basename(dirpath)
                    base_name = os.path.splitext(image_file)[0]
                    
                    # Create corresponding output directories if they don't exist
                    os.makedirs(os.path.join(BASE_OUTPUT_CSV, sample_type), exist_ok=True)
                    os.makedirs(os.path.join(BASE_OUTPUT_MASKS, sample_type), exist_ok=True)
                    os.makedirs(os.path.join(BASE_OUTPUT_COMPARISON, sample_type), exist_ok=True)
                    os.makedirs(os.path.join(BASE_OUTPUT_HTML, sample_type), exist_ok=True)
                    
                    # Construct full output paths
                    csv_path = os.path.join(BASE_OUTPUT_CSV, sample_type, f"{base_name}_properties.csv")
                    mask_path = os.path.join(BASE_OUTPUT_MASKS, sample_type, f"{base_name}_mask.png")
                    comparison_path = os.path.join(BASE_OUTPUT_COMPARISON, sample_type, f"{base_name}_comparison.png")
                    html_path = os.path.join(BASE_OUTPUT_HTML, sample_type, f"{base_name}_interactive.html")

                    # --- Run Processing and Visualization ---
                    try:
                        # You might need to adjust these parameters per sample type later
                        df_results, mask_image, labels, original_image = process_image(
                            image_path=full_image_path,
                            sigma=5,
                            block_size=251,
                            threshold_factor=0.8,
                            min_size=2000,
                            hole_size=1000
                        )
                        
                        # Save the core data and mask
                        df_results.to_csv(csv_path, index=False)
                        mask_to_save = (mask_image.astype(np.uint8)) * 255
                        cv2.imwrite(mask_path, mask_to_save)
                        
                        # Generate the new visualizations
                        create_interactive_visualization(labels, original_image, html_path)
                        create_comparison_image(original_image, labels, comparison_path)
                        
                        print(f"  -> Results saved for {base_name}")

                    except Exception as e:
                        print(f"  -> ERROR processing {image_file}: {e}")
                    
                    print("-" * 20)

    print("All image processing complete.")
