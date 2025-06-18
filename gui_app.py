import pygame as pg
import os
import numpy as np
import cv2
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

# Convert np mask to pygame surface
def convert_mask_to_surface(mask, size):
    # Create a 3-channel RGBA surface where the mask is red
    rgba_mask = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
    rgba_mask[mask == 255] = [255, 0, 0, 128] # Red, with 50% transparency

    # Convert to a PyGame surface
    mask_surface = pg.image.frombuffer(rgba_mask.flatten(), mask.shape[::-1], 'RGBA')

    # Scale it to the display size
    scaled_mask = pg.transform.smoothscale(mask_surface, size)
    return scaled_mask


# Main GUi function with updated logic
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
    
    current_image_index = 0 # Counter init.
    current_image_bgr = cv2.imread(image_files[current_image_index])
    current_display_surface = load_and_scale_for_display(current_image_bgr, (IMAGE_AREA_WIDTH, SCREEN_HEIGHT))
    processed_mask_surface = None


    def update_image_display(index):
        path = image_files[index]
        image_bgr = cv2.imread(path)
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

    # Processing function to be called by the button 
    def run_processing():
        nonlocal processed_mask_surface # Using nonlocal to modify the outer scope variable
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
        df, cleaned_mask, labels = utils.segment_and_extract(
            image_bgr=current_image_bgr,
            sigma=sigma,
            block_size=block_size,
            threshold_factor=threshold_factor,
            min_size=min_size,
            hole_size=hole_size
        )
        print(f"Processing complete. Found {len(df)} grains.")

        # Convert the resulting numpy mask to a displayable PyGame surface
        processed_mask_surface = convert_mask_to_surface(
            cleaned_mask, current_display_surface.get_size()
        )

    # Create process button
    process_button = Button(x=IMAGE_AREA_WIDTH + 50, y=y_offset, w=250, h=50, text='Process Image', callback=run_processing)


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
                    current_image_index = (current_image_index + 1) % len(image_files) # Ensure smooth
                    current_image_surface, current_info_surface = update_image_display(current_image_index)
                    processed_mask_surface = None # Clear ] mask
                elif event.key == pg.K_LEFT:
                    current_image_index = (current_image_index - 1 + len(image_files)) % len(image_files)
                    current_image_surface, current_info_surface = update_image_display(current_image_index)
                    processed_mask_surface = None # Clear  mask

            # Pass the event to each input box and button
            for box in input_boxes:
                box.handle_event(event)
            process_button.handle_event(event)

        #  Drawing 
        screen.fill(COLOR_BACKGROUND)

        # Draw the current image
        img_rect = current_display_surface.get_rect(center=(IMAGE_AREA_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(current_display_surface, img_rect)
        if processed_mask_surface:
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
        process_button.draw(screen) # Draw the button

        #Update display
        pg.display.flip()
        clock.tick(30)

    pg.quit()
if __name__ == '__main__':
    main()