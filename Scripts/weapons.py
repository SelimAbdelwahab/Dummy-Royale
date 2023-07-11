import pygame as pg
from pygame.mouse import get_pressed as mouseGetPreseed
from pygame.key import get_pressed as keyGetPressed

from Scripts.gun import Gun
from Scripts.bullet import Bullet

from time import time
from math import cos, sin

pg.init()

defaultSurface = pg.Surface((10, 10))
defaultSurface.set_colorkey((132, 132, 132))
defaultSurface.fill(defaultSurface.get_colorkey())

# M1911 images
M1911_IMAGE_TOP = pg.image.load("assets/game/guns/M1911_top.png").convert()
M1911_IMAGE_TOP = pg.transform.scale(M1911_IMAGE_TOP, (round(M1911_IMAGE_TOP.get_size()[0] / 11.25),
                                                       round(M1911_IMAGE_TOP.get_size()[1] / 11.25)))

M1911_IMAGE_TOP_SIZE = M1911_IMAGE_TOP.get_size()

M1911_IMAGE_SIDE = pg.image.load("assets/game/guns/M1911_side.png")
M1911_IMAGE_SIDE = pg.transform.scale(M1911_IMAGE_SIDE,
                                      (round(M1911_IMAGE_SIDE.get_size()[0] / 6),
                                       round(M1911_IMAGE_SIDE.get_size()[1] / 6)))
M1911_IMAGE_SIDE_SIZE = M1911_IMAGE_SIDE.get_size()

# Revolver images
REVOLVER_IMAGE_TOP = pg.image.load("assets/game/guns/revolver_top.png").convert()
REVOLVER_IMAGE_TOP = pg.transform.scale(REVOLVER_IMAGE_TOP, (round(REVOLVER_IMAGE_TOP.get_size()[0] / 6.75),
                                                             round(REVOLVER_IMAGE_TOP.get_size()[1] / 11.25)))
REVOLVER_IMAGE_TOP_SIZE = REVOLVER_IMAGE_TOP.get_size()

REVOLVER_IMAGE_SIDE = pg.image.load("assets/game/guns/Revolver_side.png")
REVOLVER_IMAGE_SIDE = pg.transform.scale(REVOLVER_IMAGE_SIDE,
                                         (round(REVOLVER_IMAGE_SIDE.get_size()[0] / 6),
                                          round(REVOLVER_IMAGE_SIDE.get_size()[1] / 6)))

REVOLVER_IMAGE_SIDE_SIZE = REVOLVER_IMAGE_SIDE.get_size()

# AWP images
AWP_IMAGE_TOP = pg.image.load("assets/game/guns/AWP_top.png").convert()
AWP_IMAGE_TOP = pg.transform.scale(AWP_IMAGE_TOP,
                                   (round(AWP_IMAGE_TOP.get_size()[0] / 3.375),
                                    round(AWP_IMAGE_TOP.get_size()[1] / 6.75)))

AWP_IMAGE_TOP_SIZE = AWP_IMAGE_TOP.get_size()

AWP_IMAGE_SIDE = pg.image.load("assets/game/guns/AWP_side.png")
AWP_IMAGE_SIDE = pg.transform.scale(AWP_IMAGE_SIDE, (133, 40))

AWP_IMAGE_SIDE_SIZE = AWP_IMAGE_SIDE.get_size()


class M1911(Gun):
    __slots__ = "weaponID", "range", "mobility", "GAME_SURFACE", "WEAPON_SURF", "BULLET_SURF", "GSTEP", "pos", \
                "shooter", "angle", "AI", "AITimeout", "selected", "shootCT", "fRate", "mag", "clip", "ammo", \
                "reloadTime", "reloadCT", "reloading", "bulletDmg", "bulletVel", "bulletLoc", "imageTop", "imageSide", \
                "imageSideDims", "wTop", "hTop", "wSide", "hSide", "SURFACE", "mouseWasDown", "displacement"

    def __init__(self, GAME_SURFACE: pg.Surface, WEAPON_SURF: pg.Surface, BULLET_SURF: pg.Surface, GSTEP: tuple,
                 pos: tuple,
                 shooter: object,
                 clip=1,
                 ammo=1):
        pg.init()

        self.weaponID = "M1911"

        self.range = 400
        self.mobility = 1 / 1.2

        self.GAME_SURFACE = GAME_SURFACE
        self.WEAPON_SURF = WEAPON_SURF
        self.BULLET_SURF = BULLET_SURF
        self.GSTEP = GSTEP

        self.pos = pos

        self.shooter = shooter

        self.angle = 0

        self.AI = True if "enemy" in str(type(shooter)) else False
        self.AITimeout = time()
        self.selected = True

        self.shootCT = time()
        self.fRate = 0.4
        self.mag = 16
        self.clip = clip if clip is not None else self.mag
        self.ammo = ammo if ammo is not None else 52

        self.reloadTime = 1
        self.reloadCT = time()
        self.reloading = False

        self.bulletDmg = 15
        self.bulletVel = 10

        self.bulletLoc = None

        self.imageTop = M1911_IMAGE_TOP

        self.wTop, self.hTop = M1911_IMAGE_TOP_SIZE

        if not self.AI:
            self.imageSide = M1911_IMAGE_SIDE
            self.imageSideDims = M1911_IMAGE_SIDE_SIZE

            self.wSide, self.hSide = M1911_IMAGE_SIDE_SIZE

        self.SURFACE = pg.transform.scale(defaultSurface, (self.wTop, self.hTop))

        # Blit the imageTop to the surface
        self.SURFACE.blit(self.imageTop, (0, 0))

        self.mouseWasDown = False

        self.displacement = (0, 0)

        super().__init__(pos, shooter)

    def update(self, pos: tuple, angle: float, displacement: tuple):
        self.bulletLoc = pos
        self.displacement = displacement

        if self.AI is False or self.shooter.inCameraView:
            self.parentUpdate(pos, angle)

        if not self.reloading:
            if self.clip > 0:
                if not self.AI:
                    self.checkInput()
                self.reloadCT = time()
            elif self.ammo > 0:
                self.reloading = True
                self.reload()
        else:
            self.reload()

    def checkInput(self, AIOverride=False):
        if AIOverride:
            mouse = True
        else:
            mouse = True in mouseGetPreseed()

        keys = keyGetPressed()
        keyR = keys[pg.K_r]
        keyQ = keys[pg.K_q]

        if not self.reloading:
            if (mouse or keyQ) and not self.mouseWasDown:
                if self.clip > 0:
                    self.shoot()
                    self.AITimeout = time()
                else:
                    self.reloading = True
            else:
                if (not mouse and not keyQ) and self.mouseWasDown:
                    self.mouseWasDown = False

        if keyR and self.clip != self.mag:
            self.reloading = True

        if self.AI and self.mouseWasDown and time() - self.AITimeout > self.fRate:
            self.mouseWasDown = False

    def shoot(self):
        if time() - self.shootCT > self.fRate:
            # bx = self.x + self.shooter.body.r * cos(self.angle)
            # by = self.y - self.shooter.body.r * sin(self.angle)
            bx = self.bulletLoc[0] + self.shooter.body.r * cos(self.angle)
            by = self.bulletLoc[1] - self.shooter.body.r * sin(self.angle)

            self.shooter.bullets.append(
                Bullet(self.BULLET_SURF, self.shooter.MAP_SIZE, self.GSTEP, self.shooter, bx, by,
                       self.angle, self.bulletVel, self.weaponID,
                       self.bulletDmg))
            # pg.mixer.Sound.play(self.gunshot)

            self.clip -= 1
            self.mouseWasDown = True
            self.shootCT = time()

            if not self.AI:
                self.shooter.forceUIUpdate = True


class Revolver(Gun):
    __slots__ = "weaponID", "range", "mobility", "GAME_SURFACE", "WEAPON_SURF", "BULLET_SURF", "GSTEP", "pos", \
                "shooter", "angle", "AI", "AITimeout", "selected", "shootCT", "fRate", "mag", "clip", "ammo", \
                "reloadTime", "reloadCT", "reloading", "bulletDmg", "bulletVel", "bulletLoc", "imageTop", "imageSide", \
                "imageSideDims", "wTop", "hTop", "wSide", "hSide", "SURFACE", "mouseWasDown", "displacement"

    def __init__(self, GAME_SURFACE: pg.Surface, WEAPON_SURF: pg.Surface, BULLET_SURF: pg.Surface, GSTEP: tuple,
                 pos: tuple,
                 shooter: object,
                 clip=6,
                 ammo=32):
        pg.init()

        self.range = 800
        self.mobility = 1 / 2

        self.GAME_SURFACE = GAME_SURFACE
        self.WEAPON_SURF = WEAPON_SURF
        self.BULLET_SURF = BULLET_SURF
        self.GSTEP = GSTEP

        self.pos = pos

        self.shooter = shooter

        self.angle = 0

        self.AI = True if "enemy" in str(type(shooter)) else False
        self.AITimeout = time()
        self.selected = True

        self.weaponID = "Revolver"

        self.shootCT = time()
        self.fRate = 1.3
        self.mag = 6
        self.clip = clip if clip is not None else self.mag
        self.ammo = ammo if ammo is not None else 32

        self.reloadTime = 0.5
        self.reloadCT = time()
        self.reloading = False

        self.bulletDmg = 27
        self.bulletVel = 8

        self.bulletLoc = None

        self.imageTop = REVOLVER_IMAGE_TOP
        self.wTop, self.hTop = REVOLVER_IMAGE_TOP_SIZE

        if not self.AI:
            self.imageSide = REVOLVER_IMAGE_SIDE
            self.imageSideDims = REVOLVER_IMAGE_SIDE_SIZE

            self.wSide, self.hSide = REVOLVER_IMAGE_SIDE_SIZE

        self.SURFACE = pg.transform.scale(defaultSurface, (self.wTop, self.hTop))

        # Blit the imageTop to the surface
        self.SURFACE.blit(self.imageTop, (0, 0))

        self.mouseWasDown = False

        self.displacement = (0, 0)

        super().__init__(pos, shooter)

    def update(self, pos: tuple, angle: float, displacement: tuple):
        self.displacement = displacement
        self.bulletLoc = pos

        if self.AI is False or self.shooter.inCameraView:
            self.parentUpdate(pos, angle)

        if not self.reloading:
            if self.clip > 0:
                if not self.AI:
                    self.checkInput()
                self.reloadCT = time()
            elif self.ammo > 0:
                self.reloading = True
                self.reload()
        else:
            self.reload()

    def checkInput(self, AIOverride=False):
        if AIOverride:
            mouse = True
        else:
            mouse = True in mouseGetPreseed()

        keys = keyGetPressed()
        keyR = keys[pg.K_r]
        keyQ = keys[pg.K_q]

        if not self.reloading:
            if (mouse or keyQ) and not self.mouseWasDown:
                if self.clip > 0:
                    self.shoot()
                    self.AITimeout = time()
                else:
                    self.reloading = True
            else:
                if (not mouse and not keyQ) and self.mouseWasDown:
                    self.mouseWasDown = False

        if keyR and self.clip != self.mag:
            self.reloading = True

        if self.AI and self.mouseWasDown and time() - self.AITimeout > self.fRate:
            self.mouseWasDown = False

    def shoot(self):
        if time() - self.shootCT > self.fRate:
            # bx = self.x + self.shooter.body.r * cos(self.angle)
            # by = self.y - self.shooter.body.r * sin(self.angle)
            bx = self.bulletLoc[0] + self.shooter.body.r * cos(self.angle)
            by = self.bulletLoc[1] - self.shooter.body.r * sin(self.angle)

            self.shooter.bullets.append(
                Bullet(self.BULLET_SURF, self.shooter.MAP_SIZE, self.GSTEP, self.shooter, bx, by,
                       self.angle, self.bulletVel, self.weaponID,
                       self.bulletDmg))

            self.clip -= 1
            self.mouseWasDown = True
            self.shootCT = time()

            if not self.AI:
                self.shooter.forceUIUpdate = True


class AWP(Gun):
    __slots__ = "weaponID", "range", "mobility", "GAME_SURFACE", "WEAPON_SURF", "BULLET_SURF", "GSTEP", "pos", \
                "shooter", "angle", "AI", "AITimeout", "selected", "shootCT", "fRate", "mag", "clip", "ammo", \
                "reloadTime", "reloadCT", "reloading", "bulletDmg", "bulletVel", "bulletLoc", "imageTop", "imageSide", \
                "imageSideDims", "wTop", "hTop", "wSide", "hSide", "SURFACE", "mouseWasDown", "displacement", "HOTKEYSURFACE"

    def __init__(self, GAME_SURFACE: pg.Surface, WEAPON_SURF: pg.Surface, BULLET_SURF: pg.Surface, GSTEP: tuple,
                 pos: tuple,
                 shooter: object,
                 clip=3,
                 ammo=15):

        pg.init()

        self.range = 800
        self.mobility = 1 / 2.5

        self.GAME_SURFACE = GAME_SURFACE
        self.WEAPON_SURF = WEAPON_SURF
        self.BULLET_SURF = BULLET_SURF
        self.GSTEP = GSTEP

        self.pos = pos

        self.shooter = shooter

        self.AI = True if "enemy" in str(type(shooter)) else False
        self.AITimeout = time()
        self.selected = True

        self.weaponID = "AWP"

        self.shootCT = time()
        self.fRate = 1
        self.mag = 5
        self.clip = clip if clip is not None else self.mag
        self.ammo = ammo if ammo is not None else 15

        self.reloadTime = 2
        self.reloadCT = time()
        self.reloading = False

        self.bulletDmg = 40
        self.bulletVel = 13

        self.bulletLoc = None

        self.imageTop = AWP_IMAGE_TOP

        self.wTop, self.hTop = AWP_IMAGE_TOP_SIZE

        if not self.AI:
            self.imageSide = AWP_IMAGE_SIDE
            self.imageSideDims = AWP_IMAGE_SIDE_SIZE

            self.wSide, self.hSide = AWP_IMAGE_SIDE_SIZE

            self.HOTKEYSURFACE = pg.Surface((self.wSide, self.hSide))
            self.HOTKEYSURFACE.fill((255, 255, 255))
            self.HOTKEYSURFACE.set_colorkey((255, 255, 255))
            self.HOTKEYSURFACE.blit(self.imageSide, (0, 0))

        self.SURFACE = pg.transform.scale(defaultSurface, (self.wTop, self.hTop))

        # Blit the imageTop to the surface
        self.SURFACE.blit(self.imageTop, (0, 0))

        self.mouseWasDown = False

        self.displacement = (0, 0)

        super().__init__(pos, shooter)

    def update(self, pos: tuple, angle: float, displacement=(0, 0)):
        self.bulletLoc = pos
        self.displacement = displacement

        if self.AI is False or self.shooter.inCameraView:
            self.parentUpdate(pos, angle)

        if not self.reloading:
            if self.clip > 0:
                if not self.AI:
                    self.checkInput()
                self.reloadCT = time()
            elif self.ammo > 0 and self.selected:
                self.reloading = True
                self.reload()
        else:
            if self.selected:
                self.reload()

    def checkInput(self, AIOverride=False):
        if AIOverride:
            mouse = True
        else:
            mouse = True in mouseGetPreseed()

        keys = keyGetPressed()
        keyR = keys[pg.K_r]
        keyQ = keys[pg.K_q]

        if not self.reloading:
            if (mouse or keyQ) and not self.mouseWasDown:
                if self.clip > 0:
                    self.shoot()
                    self.AITimeout = time()
                else:
                    self.reloading = True
            else:
                if (not mouse and not keyQ) and self.mouseWasDown:
                    self.mouseWasDown = False

        if keyR and self.clip != self.mag:
            self.reloading = True

        if self.AI and self.mouseWasDown and time() - self.AITimeout > self.fRate:
            self.mouseWasDown = False

    def shoot(self):
        if time() - self.shootCT > self.fRate:
            # bx = self.x + self.shooter.body.r * cos(self.angle)
            # by = self.y - self.shooter.body.r * sin(self.angle)
            bx = self.bulletLoc[0] + self.shooter.body.r * cos(self.angle)
            by = self.bulletLoc[1] - self.shooter.body.r * sin(self.angle)

            self.shooter.bullets.append(
                Bullet(self.BULLET_SURF, self.shooter.MAP_SIZE, self.GSTEP, self.shooter, bx, by,
                       self.angle, self.bulletVel, self.weaponID,
                       self.bulletDmg))

            self.clip -= 1
            self.mouseWasDown = True
            self.shootCT = time()

            if not self.AI:
                self.shooter.forceUIUpdate = True
