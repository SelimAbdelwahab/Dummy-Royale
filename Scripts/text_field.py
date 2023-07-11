import pygame as pg
from time import time


class TextField:
    def __init__(self, SCREEN: pg.Surface, pre_defined_text: str, font: pg.font.Font, text_color: tuple):
        font.set_bold(True)

        self.SCREEN = SCREEN
        self.S_W, self.S_H = SCREEN.get_size()

        self.rendered_text = font.render(pre_defined_text, True, text_color)
        self.text_size = self.rendered_text.get_size()

        self.font = font
        self.text = pre_defined_text
        self.text_color = text_color
        self.allowed_chars = (pg.K_a, pg.K_b, pg.K_c, pg.K_d, pg.K_e, pg.K_f, pg.K_g, pg.K_h, pg.K_i, pg.K_j, pg.K_k,
                              pg.K_l, pg.K_m, pg.K_n, pg.K_o, pg.K_p, pg.K_q, pg.K_r, pg.K_s, pg.K_t, pg.K_u, pg.K_v,
                              pg.K_w, pg.K_x, pg.K_y, pg.K_z, pg.K_0, pg.K_1, pg.K_2, pg.K_3, pg.K_4, pg.K_5, pg.K_6,
                              pg.K_7, pg.K_8, pg.K_9, pg.K_UNDERSCORE, pg.K_DELETE, pg.K_BACKSPACE)

        self.background_color = (200, 200, 200)

        self.border_colors = ((0, 0, 0), (144, 148, 151), (255, 255, 255))
        self.border_color = self.border_colors[0]

        self.active = False
        self.max_input = 15

        if self.text_size[0] > 100:
            w_size = self.text_size[0]
        else:
            w_size = 100

        h_size = self.text_size[1]

        self.text_field_rect = pg.Rect(self.S_W / 2 - 20 - w_size / 2, self.S_H - 320 - h_size / 2,
                                       w_size + 40, h_size + 40)

        self.mouse_was_pressed = False
        self.press_time = 0
        self.key_press_time = 0

    def change_text_color(self, text_color: tuple):
        self.text_color = text_color
        self.rendered_text = self.font.render(self.text, True, text_color)

    def redefine(self):
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        self.text_size = self.rendered_text.get_size()

        if self.text_size[0] > 100:
            w_size = self.text_size[0]
        else:
            w_size = 100

        h_size = self.text_size[1]

        self.text_field_rect = pg.Rect(self.S_W / 2 - 20 - w_size / 2, self.S_H - 320 - h_size / 2,
                                       w_size + 40, h_size + 40)

    def update(self):
        mouse_pos = pg.mouse.get_pos()

        hover = self.check_mouse_hover(mouse_pos)

        if time() - self.press_time > 0.1:
            self.check_mouse_pressed(hover)

            self.press_time = time()

        if self.active and time() - self.key_press_time > 0.09:
            self.add_characters()

        self.draw()

    def draw(self):
        pg.draw.rect(self.SCREEN, self.background_color, self.text_field_rect)

        self.SCREEN.blit(self.rendered_text,
                         (self.S_W / 2 - self.text_size[0] / 2, self.S_H - 300 - self.text_size[1] / 2))

        pg.draw.rect(self.SCREEN, self.border_color, self.text_field_rect, width=4)

    def add_characters(self):
        self.key_press_time = time()
        keys = pg.key.get_pressed()

        shift_pressed = keys[pg.K_LSHIFT] or keys[pg.K_RSHIFT]

        if len(self.text) >= self.max_input:
            if keys[pg.K_DELETE] or keys[pg.K_BACKSPACE]:
                self.text = self.text[:len(self.text) - 1]
                self.redefine()
        else:
            if shift_pressed and keys[pg.K_MINUS]:
                self.text += "_"
                self.redefine()

                return
            for char in self.allowed_chars:
                if keys[char]:
                    if char == pg.K_DELETE or char == pg.K_BACKSPACE:
                        self.text = self.text[:len(self.text) - 1]
                    else:
                        if shift_pressed:
                            key = pg.key.name(char).upper()
                        else:
                            key = pg.key.name(char)

                        self.text += key

                    self.redefine()
                    break

    def check_mouse_pressed(self, hover: bool):
        mouse_down = True in pg.mouse.get_pressed(3)

        if mouse_down and self.active:
            self.active = False
        elif hover and mouse_down:
            self.mouse_was_pressed = True

        if self.mouse_was_pressed:
            self.active = not self.active

            self.mouse_was_pressed = False

    def check_mouse_hover(self, mouse_pos: tuple):
        if self.active:
            self.border_color = self.border_colors[2]
        else:
            self.border_color = self.border_colors[1]

            if self.text_field_rect.collidepoint(mouse_pos):
                return True
            else:
                self.border_color = self.border_colors[0]
