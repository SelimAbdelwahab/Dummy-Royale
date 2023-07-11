from math import atan2, sin, cos, pi
import pygame as pg
import pygame.gfxdraw
from time import time
import base64


class Gun:
    __slots__ = "x", "y", "shooter", "angle", "textFont", "countdownFont"

    def __init__(self, pos: tuple, shooter: object):
        pg.init()

        self.x = pos[0] - self.wTop / 2
        self.y = pos[1] + self.hTop

        self.shooter = shooter
        self.angle = 0

        if not self.AI:
            self.textFont = pg.font.SysFont("arial", 26)
            self.countdownFont = pg.font.SysFont("calibri", 21)

    def parentUpdate(self, pos: tuple, angle: float):
        self.move(pos, angle)
        self.drawTop()

    def drawTop(self):
        # Convert angle from RAD to DEG for pygame compatibility
        theta = (self.angle * 180 / pi)

        # NewTop rotated surface
        surf = pg.transform.rotate(self.SURFACE, theta - 90).convert()

        # NewTop surface Dimensions since as theTope surface is rotated it increases
        *null, wTop, hTop = (surf.get_rect())

        self.WEAPON_SURF.blit(surf,
                              (self.x - wTop / 2 + self.displacement[0], self.y - hTop / 2 + self.displacement[1]))

    def get_surface_data(self):
        theta = (self.angle * 180 / pi)

        return {
            "weapon_name": self.weaponID,
            "theta": theta
        }

    def move(self, pos, angle):
        self.angle = angle

        x0 = (self.shooter.body.r * 0.75 + self.hTop / 3) * cos(self.angle)
        y0 = (self.shooter.body.r * 0.75 + self.hTop / 3) * sin(self.angle)

        self.x = pos[0] + x0
        self.y = pos[1] - y0

    def getMag(self):
        return f"{self.clip}/{self.ammo}"

    def reload(self):
        if time() - self.reloadCT > self.reloadTime:
            # Check how much ammo is in clip:
            remainInClip = self.clip

            self.ammo = self.ammo + remainInClip

            if self.ammo <= self.mag:
                self.clip = self.ammo
            else:
                self.clip = self.mag

            self.ammo -= self.mag

            if self.ammo < 0:
                self.ammo = 0

            self.reloading = False
            self.shooter.forceUIUpdate = True

    def displayReloading(self):
        rect = (self.shooter.body.x - 53, 53, 106, 106)

        theta0 = -(2 * pi) * ((time() - self.reloadCT) / self.reloadTime)
        theta1 = 0

        pg.gfxdraw.filled_circle(self.GAME_SURFACE, int(self.shooter.body.x), int(rect[1] + rect[3] / 2),
                                 int(rect[3] / 2),
                                 (0, 0, 0, 150))

        pg.draw.arc(self.GAME_SURFACE, (255, 255, 255), rect, theta0 + pi / 2, theta1 + pi / 2, width=6)

        countdown = self.countdownFont.render(str(abs(round((self.reloadTime - (time() - self.reloadCT)), 1))),
                                              True, (255, 255, 255))
        text = self.textFont.render("Reloading", True, (255, 255, 255))

        rectTxtBg = (self.shooter.body.x - text.get_size()[0] / 2 - 13, rect[1] + rect[3] * 1.2,
                     text.get_size()[0] + 26, 40)

        pg.gfxdraw.box(self.GAME_SURFACE, rectTxtBg, (0, 0, 0, 150))

        self.GAME_SURFACE.blit(countdown,
                               (self.shooter.body.x - countdown.get_size()[0] / 2,
                                rect[1] + rect[3] / 2 - countdown.get_size()[1] / 2))
        self.GAME_SURFACE.blit(text, (
            self.shooter.body.x - text.get_size()[0] / 2, rectTxtBg[1] + rectTxtBg[3] / 2 - text.get_size()[1] / 2))
