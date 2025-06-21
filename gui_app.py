import pygame as pg
import os
import numpy as np
import cv2
import pandas as pd
from skimage.measure import label, regionprops_table
from src.gui_components import InputBox, Button # Class and GUI elements
from src import utils # Helper functions

# --- Constants --- 
SCREEN_WIDTH = 1280 # May need to be adjusted 
SCREEN_HEIGHT = 720 # Depending on local machine
CONTROL_PANEL_WIDTH = 350 
IMAGE_AREA_WIDTH = SCREEN_WIDTH - CONTROL_PANEL_WIDTH

# Colours
COLOR_BACKGROUND = (20, 20, 30)
COLOR_PANEL = (40, 40, 50)
COLOR_TEXT = (220, 220, 220)
COLOR_LABEL = (150, 150, 170)
COLOR_SAVE_INACTIVE = (30, 150, 80) # New button colours
COLOR_SAVE_ACTIVE = (50, 180, 100)

# --- Helper funcitons ---

# Scan data directory and return a list of all image file paths.
def get_image_files(root_dir):
    image_paths = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')): # Extend support for other image types
                image_paths.append(os.path.join(dirpath, filename))
    print(f"Found {len(image_paths)} images.") # For testing
    return sorted(image_paths) # Sort to ensure consistent order

# load image and return PyGame surface
def load_and_scale_for_display(image_bgr, display_area_size):
    img_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB) # Load using CV to keep colour channels correct (BGR)
    # Create a PyGame surface from the NumPy array
    img_surface = pg.surfarray.make_surface(img_rgb.swapaxes(0, 1))

    # Scale the image to fit the designated area while maintaining AR
    img_rect = img_surface.get_rect()
    area_width, area_height = display_area_size
    scale = min(area_width / img_rect.width, area_height / img_rect.height)
    new_size = (int(img_rect.width * scale), int(img_rect.height * scale))

    scaled_image = pg.transform.smoothscale(img_surface, new_size) # trying smoothscale func.
    return scaled_image

def convert_labels_to_viridis_surface(labels, size):
    if labels.max() == 0: # Handle case with no labels found
        return pg.Surface(size, pg.SRCALPHA) # Return a blank transparent surface

    # Normalize the labels to the 0-255 range for colormapping
    normalized_labels = (255 * labels / labels.max()).astype(np.uint8)

    # Apply the Viridis colormap
    viridis_bgr = cv2.applyColorMap(normalized_labels, cv2.COLORMAP_VIRIDIS)
    
    # Convert from BGR (OpenCV) to RGBA for PyGame transparency
    viridis_rgba = cv2.cvtColor(viridis_bgr, cv2.COLOR_BGR2RGBA)

    # Create a transparency mask: 0 for background (label 0), 180 for grains
    alpha_channel = np.where(labels > 0, 180, 0).astype(np.uint8)
    
    # Apply the transparency to the RGBA image
    viridis_rgba[:, :, 3] = alpha_channel

    # Create the final PyGame surface
    colored_surface = pg.image.frombuffer(viridis_rgba.tobytes(), viridis_rgba.shape[1::-1], 'RGBA')
    
    scaled_surface = pg.transform.smoothscale(colored_surface, size)
    return scaled_surface


# Main GUI function with updated logic
def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("Metallurgical Image Analyzer v2.0")
    clock = pg.time.Clock()
    font_label = pg.font.Font(None, 28)
    font_info = pg.font.Font(None, 24)

    #Load Image Paths 
    image_files = get_image_files('images/raw')
    if not image_files: # Basic error catching
        print("No images found in the directory. Exiting.")
        return
    
    current_image_index = 0 # Counter init. for navigation
    current_image_bgr = cv2.imread(image_files[current_image_index])
    current_display_surface = load_and_scale_for_display(current_image_bgr, (IMAGE_AREA_WIDTH, SCREEN_HEIGHT))
    processed_mask_surface = None
    invert_mask_state = False
    is_mask_visible = True # Used to temporarily hide mask
    
     # Saving parameters
    latest_df = None
    latest_labels = None

    def update_image_display(index):
        path = image_files[index]
        image_bgr = cv2.imread(path)

        # Error handling for image reader
        if image_bgr is None:
            print(f"ERROR: Failed to load image at {path}. Skipping.")
            # Return placeholder values
            error_font = pg.font.Font(None, 48)
            error_surf = error_font.render("Error: Could not load image", True, (255, 0, 0))
            return None, error_surf, error_surf
        display_surface = load_and_scale_for_display(image_bgr, (IMAGE_AREA_WIDTH, SCREEN_HEIGHT))
        
        sample_type = os.path.basename(os.path.dirname(path))
        filename = os.path.basename(path)
        info_text = f"{sample_type} | {filename} ({index + 1}/{len(image_files)})"
        info_surf = font_info.render(info_text, True, COLOR_TEXT)
        
        return image_bgr, display_surface, info_surf

    current_image_bgr, current_display_surface, current_info_surface = update_image_display(current_image_index)

    # Create GUI Elements
    y_offset = 60
    # sigma
    label1_surf = font_label.render("Gaussian Sigma:", True, COLOR_LABEL)
    input_box_sigma = InputBox(IMAGE_AREA_WIDTH + 50, y_offset, 140, 32, text='1.5')
    y_offset += 70
    # block_size
    label2_surf = font_label.render("Block Size (odd):", True, COLOR_LABEL)
    input_box_block = InputBox(IMAGE_AREA_WIDTH + 50, y_offset, 140, 32, text='115')
    y_offset += 70
    # threshold_factor
    label3_surf = font_label.render("Threshold Factor:", True, COLOR_LABEL)
    input_box_thresh = InputBox(IMAGE_AREA_WIDTH + 50, y_offset, 140, 32, text='1.0')
    y_offset += 70
    # min_size
    label4_surf = font_label.render("Min Object Size (px):", True, COLOR_LABEL)
    input_box_min_size = InputBox(IMAGE_AREA_WIDTH + 50, y_offset, 140, 32, text='50')
    y_offset += 70
    # hole_size
    label5_surf = font_label.render("Max Hole Size (px):", True, COLOR_LABEL)
    input_box_hole_size = InputBox(IMAGE_AREA_WIDTH + 50, y_offset, 140, 32, text='50')
    y_offset += 90

    input_boxes = [input_box_sigma, input_box_block, input_box_thresh, input_box_min_size, input_box_hole_size]

    # Create Save function
    def save_results():
        if latest_df is None or latest_labels is None:
            print("No results to save. Please process an image first.")
            return

        # Get the current image path and extract the sample type (e.g. "X-6")
        current_path = image_files[current_image_index]
        sample_type = os.path.basename(os.path.dirname(current_path))
        
        # Get the base name of the current image file
        base_filename = os.path.splitext(os.path.basename(current_path))[0]

        # Define output paths including  sample_type subdirectory
        output_data_dir = os.path.join("output/data", sample_type)
        output_img_dir = os.path.join("output/comparison_images", sample_type)
        
        # Create subdirectories if they dont exist
        os.makedirs(output_data_dir, exist_ok=True)
        os.makedirs(output_img_dir, exist_ok=True)

        # Save the df to CSV path
        csv_path = os.path.join(output_data_dir, f"{base_filename}_data.csv")
        latest_df.to_csv(csv_path, index=False)
        print(f"Data saved to {csv_path}")

        # Save  comparison image to PNG path
        img_path = os.path.join(output_img_dir, f"{base_filename}_comparison.png")
        # Call utility func.
        utils.create_comparison_image(current_image_bgr, latest_labels, img_path)
        print(f"Comparison image saved to {img_path}")

    # Processing function to be called by the button 
    def run_processing():
        nonlocal processed_mask_surface, latest_df, latest_labels # Using nonlocal to modify the outer scope variable
        print(" button clicked") #Debugging
        # Get values from input boxes
        try:
            sigma = float(input_box_sigma.text)
            block_size = int(input_box_block.text)
            threshold_factor = float(input_box_thresh.text)
            min_size = int(input_box_min_size.text)
            hole_size = int(input_box_hole_size.text)
        except ValueError:
            print("Invalid input! Please enter valid numbers.")
            return

        # Call the utility function
         # 1. Get the initial processed mask from your utility function
        _, cleaned_mask, _ = utils.segment_and_extract(
            image_bgr=current_image_bgr,
            sigma=sigma,
            block_size=block_size,
            threshold_factor=threshold_factor,
            min_size=min_size,
            hole_size=hole_size
        )

        # --- MODIFICATION START: Invert the mask if the toggle is ON ---
        if invert_mask_state:
            print("Inverting mask...")
            cleaned_mask = ~cleaned_mask
        
        # 2. Re-label and extract properties from the FINAL mask (whether inverted or not)
        labels = label(cleaned_mask)
        properties = [
            'area', 'perimeter', 'eccentricity', 'solidity', 'equivalent_diameter',
            'orientation', 'major_axis_length', 'minor_axis_length'
        ]
        # Ensure we handle images that result in no labels after inversion
        if labels.max() > 0:
            props_table = regionprops_table(labels, properties=properties)
            df = pd.DataFrame(props_table)
        else:
            df = pd.DataFrame(columns=properties) # Create empty dataframe
        
        print(f"Processing complete. Found {len(df)} grains.")
        
        # 3. Store and visualize the final results
        latest_df = df
        latest_labels = labels
        processed_mask_surface = convert_labels_to_viridis_surface(
            labels, current_display_surface.get_size()
        )

    # Create button classes
    # Toggling Mask Visibility logic and button
    def toggle_mask_visibility():
        nonlocal is_mask_visible
        is_mask_visible = not is_mask_visible
        # Update the button text to reflect the state
        new_text = "Hide Mask" if is_mask_visible else "Show Mask"
        toggle_button.update_text(new_text)

    toggle_button = Button(
        x=IMAGE_AREA_WIDTH + 50, y=y_offset, w=250, h=40,
        text='Hide Mask', callback=toggle_mask_visibility
    )
    y_offset += 50 # Adjust Y position for the next button

    # Invert Mask logic and button
    def toggle_invert_state():
        nonlocal invert_mask_state
        invert_mask_state = not invert_mask_state
        new_text = f"Invert Mask: {'ON' if invert_mask_state else 'OFF'}"
        invert_button.update_text(new_text)

    invert_button = Button(
        x=IMAGE_AREA_WIDTH + 50, y=y_offset, w=250, h=40,
        text=f"Invert Mask: {'ON' if invert_mask_state else 'OFF'}",
        callback=toggle_invert_state
    )
    y_offset += 50 # Adjust Y position for the process button
    
    # Process Button uses function above on callback
    process_button = Button(
        x=IMAGE_AREA_WIDTH + 50, y=y_offset, w=250, h=50,
        text='Process Image', callback=run_processing
    )

    # Save Button also uses previously defined callback func.
    save_button = Button(
        x=IMAGE_AREA_WIDTH + 50, y=SCREEN_HEIGHT - 60, w=250, h=40,
        text='Approve & Save', callback=save_results,
        color_inactive=COLOR_SAVE_INACTIVE,
        color_active=COLOR_SAVE_ACTIVE
    )

    #  Main Game Loop 
    running = True
    while running:
        # Event Handling
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False # Exit loop
            
            #  keyboard navigation for images 
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RIGHT:
                    current_image_index = (current_image_index + 1) % len(image_files)
                    current_image_bgr, current_display_surface, current_info_surface = update_image_display(current_image_index)
                    processed_mask_surface = None # Clear ] mask
                elif event.key == pg.K_LEFT:
                    current_image_index = (current_image_index - 1 + len(image_files)) % len(image_files)
                    current_image_bgr, current_display_surface, current_info_surface = update_image_display(current_image_index)
                    processed_mask_surface = None # Clear  mask

            # Pass the event to each input box and button
            for box in input_boxes:
                box.handle_event(event)
            toggle_button.handle_event(event)
            save_button.handle_event(event)
            process_button.handle_event(event)
            invert_button.handle_event(event)


        #  Drawing 
        screen.fill(COLOR_BACKGROUND)

        # Draw the current image
        img_rect = current_display_surface.get_rect(center=(IMAGE_AREA_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(current_display_surface, img_rect)
        if processed_mask_surface and is_mask_visible:
            screen.blit(processed_mask_surface, img_rect)
        screen.blit(current_info_surface, (20, SCREEN_HEIGHT - 40))

        # Control Panel 
        pg.draw.rect(screen, COLOR_PANEL, (IMAGE_AREA_WIDTH, 0, CONTROL_PANEL_WIDTH, SCREEN_HEIGHT))
        y_offset = 30
        screen.blit(label1_surf, (IMAGE_AREA_WIDTH + 50, y_offset))
        y_offset += 70
        screen.blit(label2_surf, (IMAGE_AREA_WIDTH + 50, y_offset))
        y_offset += 70
        screen.blit(label3_surf, (IMAGE_AREA_WIDTH + 50, y_offset))
        y_offset += 70
        screen.blit(label4_surf, (IMAGE_AREA_WIDTH + 50, y_offset))
        y_offset += 70
        screen.blit(label5_surf, (IMAGE_AREA_WIDTH + 50, y_offset))

        for box in input_boxes:
            box.draw(screen)
        save_button.draw(screen) # Draw the buttons
        invert_button.draw(screen)
        process_button.draw(screen)
        toggle_button.draw(screen)
        

        #Update display
        pg.display.flip()
        clock.tick(30)

    pg.quit()
if __name__ == '__main__':
    main()