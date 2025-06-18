import pygame as pg

pg.font.init()
COLOR_INACTIVE = pg.Color('lightskyblue3')
COLOR_ACTIVE = pg.Color('dodgerblue2')
FONT = pg.font.Font(None, 32)

class InputBox:
    """A class to create a clickable, user-editable text input box."""
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