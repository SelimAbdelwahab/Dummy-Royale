import pygame as pg
from pygame import Rect
from pygame.draw import circle, rect

from random import randint
from time import time
from math import cos, sin

from Scripts.player import Player
from Scripts.extra_functions import getDist, specialAngles


class Storm:
    def __init__(self, GAME_SURFACE: pg.Surface, MAP_SIZE: tuple, player: Player):
        self.GAME_SURFACE = GAME_SURFACE
        self.GAME_SURFACE_DIMS = GAME_SURFACE.get_size()
        self.SCREEN_RECT = Rect(0, 0, *self.GAME_SURFACE_DIMS)

        self.MAP_SIZE = MAP_SIZE
        self.player = player

        self.stormColor = (226, 151, 227)

        self.MAIN_BACKGROUND = pg.Surface(self.MAP_SIZE)
        self.MAIN_BACKGROUND.set_colorkey((0, 0, 0))
        self.MAIN_BACKGROUND.set_alpha(100)
        self.MAIN_BACKGROUND.fill(self.stormColor)

        self.STORM_BACKGROUND = self.MAIN_BACKGROUND.copy()
        self.STORM_BACKGROUND = self.STORM_BACKGROUND.convert_alpha()

        self.COPY_STORM = self.MAIN_BACKGROUND.copy()

        # self.desiredX, self.desiredY = randint(0, self.MAP_SIZE[0]), randint(0, self.MAP_SIZE[1])
        self.desiredX, self.desiredY = self.MAP_SIZE[0] / 2, self.MAP_SIZE[1] / 2
        self.x, self.y = self.desiredX, self.desiredY

        # self.r = (self.MAP_SIZE[0] + self.MAP_SIZE[1]) / 1.5
        # self.desiredR = (self.MAP_SIZE[0] + self.MAP_SIZE[1]) / 4
        # self.r = (self.MAP_SIZE[0] + self.MAP_SIZE[1]) / 4
        # self.desiredR = (self.MAP_SIZE[0] + self.MAP_SIZE[1]) / 8
        self.r = 1000
        self.desiredR = 500

        self.SURFACES = []

        for idx, n in enumerate(reversed(range(500, 1000))):
            self.SURFACES.append(self.MAIN_BACKGROUND.copy())
            circle(self.SURFACES[idx], (0, 0, 0), (self.x, self.y), n)

        self.currentStormIdx = 0

        self.dmg = 1

        self.ready = False
        self.active = False

        self.timeTillActive = 1
        self.previousTime = time()

        self.displacement = (0, 0)

        self.increments = 0
        self.maxIncrements = 3

        print(self.x, self.y)

    def inCameraView(self, d: tuple):
        dx, dy = d
        x = self.x + dx
        y = self.y + dy
        r = self.r

        points = tuple((x + r * cos(angle), y - r * sin(angle)) for angle in specialAngles)
        if True in tuple(self.SCREEN_RECT.collidepoint(point) for point in points):
            # if x - r >= 0 and x + r <= w and y - r >= 0 and y + r <= h:
            # Circle Zone is visible on screen
            return 1
        elif getDist(self.player.getMap(), (self.x, self.y)) > (self.player.body["r"] + self.r) ** 2:
            # Player is within circle, however it is larger than the screen so no point in displaying it
            return 2

    def update(self, displacement):
        self.displacement = displacement

        if self.ready:
            render = self.inCameraView(displacement)
            if self.active:
                self.updateRadius()
                self.move()

                if render == 1:
                    self.updateStorm(displacement)
            elif self.increments < self.maxIncrements:
                self.updateTime()

            # if render == 1:
            #     self.renderStorm()
            # elif render == 2:
            #     self.renderBackground()
            self.renderStorm()

        else:
            self.updateTime(True)

    def updateStorm(self, d: tuple):
        pass
        # dx, dy = d
        # x = self.x + dx
        # y = self.y + dy
        # r = self.r
        #
        # points = tuple((x + r * cos(angle), y - r * sin(angle)) for angle in specialAngles[::4])
        #
        # if True in tuple(self.SCREEN_RECT.collidepoint(point) for point in points):
        #     circle(self.COPY_STORM, self.stormColor, (self.x, self.y), self.r * 1.05)
        # else:
        #     rect(self.COPY_STORM, self.stormColor,
        #          Rect(-self.displacement[0], -self.displacement[1], *self.GAME_SURFACE_DIMS))
        # # self.COPY_STORM = self.STORM_BACKGROUND.copy()
        # circle(self.COPY_STORM, (0, 0, 0), (self.x, self.y), self.r)

    def renderStorm(self):
        self.GAME_SURFACE.blit(self.SURFACES[self.currentStormIdx], (0, 0),
                               Rect(-self.displacement[0], -self.displacement[1], *self.GAME_SURFACE_DIMS))

    def renderBackground(self):
        self.GAME_SURFACE.blit(self.STORM_BACKGROUND, (0, 0),
                               Rect(-self.displacement[0], -self.displacement[1], *self.GAME_SURFACE_DIMS))

    def updateTime(self, setReady=False):
        if setReady:
            if time() - self.previousTime > self.timeTillActive:
                self.ready = True
                self.active = True
        else:
            if time() - self.previousTime > self.timeTillActive:
                self.active = True

    def updateRadius(self):
        if self.r > self.desiredR:
            self.currentStormIdx += 1
        else:
            self.active = False

            self.r = self.desiredR
            self.desiredR /= 2

            self.previousTime = time()
            self.desiredX, self.desiredY = randint(0, self.MAP_SIZE[0]), randint(0, self.MAP_SIZE[1])

            self.timeTillActive += 2
            self.COPY_STORM = self.COPY_STORM.convert_alpha()
            circle(self.COPY_STORM, (0, 0, 0), (self.x, self.y), self.r)

            self.increments += 1

    def move(self):
        if self.x != self.desiredX:
            if self.x > self.desiredX:
                self.x -= 1
            elif self.x < self.desiredX:
                self.x += 1

        if self.y != self.desiredY:
            if self.y > self.desiredY:
                self.y -= 1
            elif self.y < self.desiredY:
                self.y += 1
