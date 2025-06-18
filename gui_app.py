import pygame as pg
import os
from src.gui_components import InputBox # Helper function

# --- Constants --- 
SCREEN_WIDTH = 1280 # May need to be adjusted 
SCREEN_HEIGHT = 720 # Depending on local machine
CONTROL_PANEL_WIDTH = 300 
IMAGE_AREA_WIDTH = SCREEN_WIDTH - CONTROL_PANEL_WIDTH

# Colours
COLOR_BACKGROUND = (20, 20, 30)
COLOR_PANEL = (40, 40, 50)
COLOR_TEXT = (220, 220, 220)

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
def load_and_scale_image(image_path, display_area_size):
    try:
        image = pg.image.load(image_path).convert() # use convert() for performance
    except pg.error as e:
        print(f"Error loading image {image_path}: {e}")
        return None

    # Scale the image to fit the designated area while maintaining AR
    img_rect = image.get_rect()
    area_width, area_height = display_area_size
    scale = min(area_width / img_rect.width, area_height / img_rect.height)
    new_size = (int(img_rect.width * scale), int(img_rect.height * scale))

    scaled_image = pg.transform.smoothscale(image, new_size) # trying smoothscale func.
    return scaled_image

# Main GUi function with updated logic
def main():
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("Metallurgical Image Analyzer v2.0")
    clock = pg.time.Clock()

    #Load Image Paths 
    image_files = get_image_files('images/raw')
    if not image_files: # Basic error catching
        print("No images found in the directory. Exiting.")
        return
    
    current_image_index = 0 # Counter init.
    current_image_surface = load_and_scale_image(image_files[current_image_index],(IMAGE_AREA_WIDTH, SCREEN_HEIGHT))

    # Create GUI Elements
    input_box1 = InputBox(IMAGE_AREA_WIDTH + 50, 100, 140, 32, text='11') # Call helper func.
    input_box2 = InputBox(IMAGE_AREA_WIDTH + 50, 200, 140, 32, text='5')
    input_boxes = [input_box1, input_box2] # Main list

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
                    current_image_surface = load_and_scale_image(image_files[current_image_index],(IMAGE_AREA_WIDTH, SCREEN_HEIGHT))
                elif event.key == pg.K_LEFT:
                    current_image_index = (current_image_index - 1 + len(image_files)) % len(image_files)
                    current_image_surface = load_and_scale_image(image_files[current_image_index],(IMAGE_AREA_WIDTH, SCREEN_HEIGHT)) # Reverse logic

            # Pass the event to each input box
            for box in input_boxes:
                box.handle_event(event)

        #  Drawing 
        screen.fill(COLOR_BACKGROUND)

        # Draw the current image
        if current_image_surface:
            # Center the image vertically
            img_rect = current_image_surface.get_rect(center=(IMAGE_AREA_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(current_image_surface, img_rect)

        # Control Panel Background
        pg.draw.rect(screen, COLOR_PANEL, (IMAGE_AREA_WIDTH, 0, CONTROL_PANEL_WIDTH, SCREEN_HEIGHT))

        # Draw GUI elements
        for box in input_boxes:
            box.draw(screen)

        # Update the display
        pg.display.flip()
        clock.tick(30)

    pg.quit()

if __name__ == '__main__':
    main()