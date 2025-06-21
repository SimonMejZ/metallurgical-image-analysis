import pygame as pg

pg.font.init()
COLOR_INACTIVE = pg.Color('lightskyblue3')
COLOR_ACTIVE = pg.Color('dodgerblue2')
FONT = pg.font.Font(None, 32)

class InputBox:
    """Clickable, user-editable text input box."""
    def __init__(self, x, y, w, h, text=''):
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False
        self.is_numeric = True # Assume numeric input unless specified

    def handle_event(self, event):
        """Handles events for the input box."""
        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    print(f"Input value: {self.text}")
                    self.active = False
                    self.color = COLOR_INACTIVE
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    char = event.unicode
                    if self.is_numeric:
                        if char.isdigit() or (char == '.' and '.' not in self.text):
                            self.text += char
                    else:
                         self.text += char
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, (255, 255, 255))

    def update(self):
        """Resize the box if the text is too long."""
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        """Draw the input box and its text on the screen."""
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        pg.draw.rect(screen, self.color, self.rect, 2)

class Button:
    """A clickable button."""
    def __init__(self, x, y, w, h, text='Click', callback=None, color_inactive=None, color_active=None):
        self.rect = pg.Rect(x, y, w, h)
        self.color_inactive = color_inactive or COLOR_INACTIVE
        self.color_active = color_active or COLOR_ACTIVE
        self.color = self.color_inactive
        
        # Added colour changing and text capabilities
        self.text = text
        self.font = FONT # Store font for text updates
        self.txt_surface = self.font.render(text, True, (255, 255, 255))
        self.callback = callback
        self.clicked = False

    def handle_event(self, event):
        """Handles events for the button."""
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
                self.color = self.color_active
        if event.type == pg.MOUSEBUTTONUP:
            if self.clicked and self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback() # Execute the callback function
            self.clicked = False
            self.color = self.color_inactive
    
    # New functions for customisation
    def update_text(self, new_text):
        """Updates the button's text and re-renders its surface."""
        self.text = new_text
        self.txt_surface = self.font.render(self.text, True, (255, 255, 255))

    def draw(self, screen):
        """Draw the button on the screen."""
        pg.draw.rect(screen, self.color, self.rect)
        text_rect = self.txt_surface.get_rect(center=self.rect.center)
        screen.blit(self.txt_surface, text_rect)