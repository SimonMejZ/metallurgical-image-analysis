import pygame as pg
from src.gui_components import InputBox

# --- Constants ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CONTROL_PANEL_WIDTH = 300
IMAGE_AREA_WIDTH = SCREEN_WIDTH - CONTROL_PANEL_WIDTH

# Colours
COLOR_BACKGROUND = (20, 20, 30)
COLOR_PANEL = (40, 40, 50)
COLOR_TEXT = (220, 220, 220)

def main():
    """Main function to run the GUI application."""
    pg.init()
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("Metallurgical Image Analyzer v2.0")
    clock = pg.time.Clock()

    # --- Create GUI Elements ---
    # Example input box
    input_box1 = InputBox(
        IMAGE_AREA_WIDTH + 50, 100, 140, 32, text='11'
    )
    input_box2 = InputBox(
        IMAGE_AREA_WIDTH + 50, 200, 140, 32, text='5'
    )
    input_boxes = [input_box1, input_box2]

    # --- Main Game Loop ---
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            # Pass the event to each input box
            for box in input_boxes:
                box.handle_event(event)

        # --- Drawing ---
        screen.fill(COLOR_BACKGROUND)

        # Draw Control Panel Background
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