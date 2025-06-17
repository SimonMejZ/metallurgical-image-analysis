import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from skimage.filters import gaussian, threshold_local
from skimage.measure import label, regionprops_table, find_contours, regionprops
from skimage.morphology import remove_small_objects, remove_small_holes, opening, disk

# Main Processing Function - GENERAL
def segment_and_extract(image_bgr, sigma, block_size, threshold_factor, min_size, hole_size):
    """
    Takes an image and processing parameters, and returns the segmented data.
    """
    img_grey = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    img_gaus = gaussian(img_grey, sigma=sigma)
    
    #Ensure block siex is odd SciKit requirement
    if block_size % 2 == 0:
        block_size += 1
        
    local_thresh = threshold_local(img_gaus, block_size)
    binary_mask = img_gaus > local_thresh * threshold_factor
    
    cleaned_mask = opening(binary_mask, disk(2)) 
    cleaned_mask = remove_small_objects(cleaned_mask, min_size=min_size)
    cleaned_mask = remove_small_holes(cleaned_mask, area_threshold=hole_size)
    
    labels = label(cleaned_mask)
    
    # List of properties to be extracted
    properties = [
        'area', 'perimeter', 'eccentricity', 'solidity', 'equivalent_diameter',
        'orientation', 'major_axis_length', 'minor_axis_length'
    ]
    
    props_table = regionprops_table(labels, intensity_image=img_grey, properties=properties)
    df = pd.DataFrame(props_table)
    
    return df, cleaned_mask, labels

# Visualisation function. Interactive HTML with Plotly
def create_interactive_visualization(labels, original_image, output_html_path):
    fig = go.Figure(go.Image(z=cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)))
    props = regionprops(labels)
    
    for index in range(labels.max()):
        contour = find_contours(labels == (index + 1), 0.5)[0]
        y, x = contour.T
        
        current_prop = props[index]
        hover_info = (f"<b>Grain ID: {current_prop.label}</b><br>" # HTML Code
                      f"Area: {current_prop.area} pixels<br>"
                      f"Solidity: {current_prop.solidity:.3f}<br>"
                      f"Eccentricity: {current_prop.eccentricity:.3f}")

        # Code from lecture, Slide 17 but modified to fit better
        fig.add_trace(go.Scatter(
            x=x, y=y, mode='lines', fill='toself', showlegend=False,
            hovertemplate=hover_info, hoveron='points+fills',
            line=dict(color='rgba(0, 255, 0, 0.7)', width=2)
        ))
    
    fig.update_layout(title='Interactive Grain Segmentation')
    fig.write_html(output_html_path)

# Comparison Image function, side by side comparison as PNG - Not changed - Matplot version
def create_comparison_image(original_image, final_mask, output_image_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    ax = axes.ravel()
    
    ax[0].imshow(cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY), cmap='gray')
    ax[0].set_title('Original Image')
    ax[0].axis('off')
    
    ax[1].imshow(final_mask, cmap='viridis') # better formatting
    ax[1].set_title('Segmented Grains Mask')
    ax[1].axis('off')
    
    plt.tight_layout()
    plt.savefig(output_image_path)
    plt.close(fig) # In case of bad memory usage