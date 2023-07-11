import pygame as pg
from pygame.draw import *


class Button:
    def __init__(self, SCREEN: pg.Surface, x: float, y: float, size: tuple, bgColor: tuple, text: str, font: pg.font,
                 textColor: tuple, alignX="l", alignY="t", btnRound: int = -1, offset=(0, 0), scale=(1, 1)):
        self.SCREEN = SCREEN
        self.x, self.y = x, y

        self.size = size

        if alignX == "r":
            self.rect = pg.Rect(self.x - size[0], self.y, *size)
        elif alignX == "c":
            self.rect = pg.Rect(self.x - size[0] / 2, self.y, *size)
        elif alignX == "l":
            self.rect = pg.Rect(self.x, self.y, *size)
        else:
            raise ValueError(
                f"Unexpected argument align={alignX}. Expected one of 'l' (left), 'r' (right), or 'c' (center).")

        self.alignX = alignX

        if alignY == "t":
            self.rect = pg.Rect(self.rect[0], self.y, *size)
        elif alignY == "c":
            self.rect = pg.Rect(self.rect[0], self.y - size[1] / 2, *size)
        elif alignY == "b":
            self.rect = pg.Rect(self.rect[0], self.y - size[1], *size)
        else:
            raise ValueError(
                f"Unexpected argument align={alignY}. Expected one of 't' (top), 'c' (center), or 'b' (bottom).")

        self.ghostRect = pg.Rect(self.rect[0] * scale[0], self.rect[1] * scale[1], size[0] * scale[0],
                                 size[1] * scale[1])

        self.alignY = alignY

        self.bgColor = bgColor
        self.textColor = textColor

        self.text = []

        for t in text.split("\n"):
            self.text.append(font.render(t, True, textColor))

        self.textSize = [text.get_size() for text in self.text]

        self.mouseWasDown = False

        self.hover = False

        if btnRound < 0:
            self.btnRound = border_radius = self.rect[3] // 2
        else:
            self.btnRound = btnRound

        self.xOff, self.yOff = offset

    def redefine(self, text):
        self.text = pg.font.render(text, False, self.textColor)

    def reAlign(self):
        if self.alignX == "r":
            self.rect = pg.Rect(self.x + self.size[0], self.y, *self.size)
        elif self.alignX == "c":
            self.rect = pg.Rect(self.x - self.size[0] / 2, self.y, *self.size)
        elif self.alignX == "l":
            self.rect = pg.Rect(self.x, self.y, *self.size)
        else:
            raise ValueError(
                f"Unexpected argument align={self.alignX}. Excpected one of 'l' (left), 'r' (right), or 'c' (center).")

        if self.alignY == "t":
            self.rect = pg.Rect(self.rect[0], self.y, *self.size)
        elif self.alignY == "c":
            self.rect = pg.Rect(
                self.rect[0], self.y - self.size[1] / 2, *self.size)
        elif self.alignY == "b":
            self.rect = pg.Rect(
                self.rect[0], self.y + self.size[1], *self.size)
        else:
            raise ValueError(
                f"Unexpected argument align={self.alignY}. Excpected one of 't' (top), 'c' (center), or 'b' (bottom).")

    def update(self, ev, act=True):
        self.draw()

        # if act:
        self.checkPressed(ev)
        if ev.type == pg.MOUSEBUTTONUP and self.mouseWasDown:
            if self.checkMouseOver():
                return True
            else:
                self.mouseWasDown = False
        # else:
        #     self.mouseWasDown = False
        #     self.hover = False

    def draw(self):
        surf = pg.Surface(self.size)
        surf.set_colorkey((50, 50, 50))
        surf.fill((50, 50, 50))

        hover = self.checkMouseOver()

        if hover:
            surf.set_alpha(255)
        else:
            surf.set_alpha(100)

        rect(surf, self.bgColor, (0, 0, *self.size), border_radius=self.btnRound)

        textOffset = self.size[1] / (len(self.text) + 1)

        for idx, text in enumerate(self.text):
            surf.blit(text, (self.size[0] / 2 - self.textSize[idx][0] / 2,
                             textOffset * (idx + 1) - self.textSize[idx][1] / 2))

        x, y, *null = self.rect
        del null

        self.SCREEN.blit(surf, (x, y))

    def checkMouseOver(self):
        mousePos = pg.mouse.get_pos()

        if self.ghostRect.collidepoint((mousePos[0] - self.xOff, mousePos[1] - self.yOff)):
            return True

        return False

    def checkPressed(self, ev):
        if ev.type == pg.MOUSEBUTTONDOWN:
            if ev.button == 1 and self.checkMouseOver():
                self.mouseWasDown = True
