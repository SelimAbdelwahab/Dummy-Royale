from pygame.mouse import get_pos as mouseGetPos, get_pressed as mouseGetPressed
from pygame.key import get_pressed as keyboardGetPressed
from pygame.draw import *
from pygame import Rect

from Scripts.weapons import *
import Scripts.game_objects as go

from math import atan2, cos, sin, pi
from random import randint
from time import time


class Body:
    # __slots__ = "x", "y", "r", "d"

    def __init__(self, x: float, y: float, r: float, d: float):
        self.x = x
        self.y = y
        self.r = r
        self.d = d


class Hand:
    # __slots__ = "x", "y", "r"

    def __init__(self, x: float, y: float, r: float):
        self.x = x
        self.y = y
        self.r = r


class Player:
    def __init__(self, username_text: str, username: pg.Surface, GAME_SURFACE: pg.Surface, WEAPON_SURF: pg.Surface, BULLET_SURF:
    pg.Surface, MAP_SIZE: tuple, color: tuple, scale: tuple, displacement, GSTEP, externalFunction,
                 bullets: list):
        pg.init()

        self.username_text = username_text
        self.username = username
        self.rut_size = username.get_size()

        self.alive = True
        self.readyStart = False
        self.forceStop = False
        self.deadWithAni = False
        self.kills = 0
        self.shooter = None

        self.path = None
        self.ID = 0

        self.GAME_SURFACE = GAME_SURFACE
        self.GAME_SURFACE_DIMS = GAME_SURFACE.get_size()

        self.WEAPON_SURF = WEAPON_SURF
        self.BULLET_SURF = BULLET_SURF

        self.MAP_SIZE = MAP_SIZE

        self.displacement = displacement

        self.SFX, self.SFY = scale
        self.GSTEP = GSTEP

        self.punchEntityColl = externalFunction

        self.bullets = bullets

        self.HEALTH_VISUALS = pg.image.load("Assets/game/player/UI/Health Effect.png")
        self.HEALTH_VISUALS.set_colorkey((0, 0, 0))
        self.HEALTH_VISUALS.set_alpha(200)
        self.HEALTH_VISUALS = self.HEALTH_VISUALS.convert_alpha()

        self.HEALTH_VISUALS = pg.Surface(self.GAME_SURFACE_DIMS)
        self.HEALTH_VISUALS.set_colorkey((0, 0, 0))
        self.HEALTH_VISUALS.set_alpha(100)
        self.HEALTH_VISUALS.fill((255, 0, 0))
        circle(self.HEALTH_VISUALS, (0, 0, 0), (self.GAME_SURFACE_DIMS[0] / 2, self.GAME_SURFACE_DIMS[1] / 2), 500)

        self.HEALTH_VISUALS = self.HEALTH_VISUALS.convert_alpha()

        special_flags = 0
        self.special_flags = pg.BLEND_ALPHA_SDL2

        self.BL_UI_SURF = pg.Surface((400, 135))
        self.BL_UI_SURF.set_colorkey((100, 100, 100))
        self.BL_UI_SURF_DIMS = self.BL_UI_SURF.get_size()

        self.BG_BL_SURF = pg.Surface(self.BL_UI_SURF_DIMS)
        self.BG_BL_SURF.set_alpha(200)
        self.BG_BL_SURF.fill((133, 146, 158), special_flags=special_flags)
        self.BG_BL_SURF = self.BG_BL_SURF.convert_alpha()

        self.BR_UI_SURF = tuple(pg.Surface((270, 135)) for _ in range(3))

        for surf in self.BR_UI_SURF:
            surf.set_colorkey((100, 100, 100))

        self.BR_UI_SURF_DIMS = self.BR_UI_SURF[0].get_size()
        self.BG_BR_SURF = pg.Surface((self.BR_UI_SURF_DIMS[0], self.BR_UI_SURF_DIMS[1] * len(self.BR_UI_SURF)))
        self.BG_BR_SURF.set_alpha(200)
        self.BG_BR_SURF.fill((133, 146, 158), special_flags=special_flags)
        self.BG_BR_SURF = self.BG_BR_SURF.convert_alpha()

        self.UI_FONT = pg.font.SysFont("Arial", 32)

        self.forceUIUpdate = True

        self.health = 100
        self.healthRegenerateTime = 0

        self.healthBarColors = ((118, 215, 196), (229, 152, 102), (231, 76, 60))
        self.healthState = 0
        self.healthFlashTimer = 0

        self.maxHealth = self.health
        self.previousHealth = 0

        self.completeBodyR = 20
        self.completeHandR = 10

        self.color = color

        self.body = Body(self.GAME_SURFACE_DIMS[0] / 2, self.GAME_SURFACE_DIMS[1] / 2, 0, self.completeBodyR * 2)
        self.leftHand = Hand(self.body.x - self.completeBodyR * cos(pi / 5),
                             self.body.y - self.completeBodyR * sin(pi / 5), 0)
        self.rightHand = Hand(self.body.x + self.completeBodyR * cos(pi / 5),
                              self.body.y - self.completeBodyR * sin(pi / 5), 0)

        self.constVel = 5
        self.vel = self.constVel
        self.velNormalize = 2 ** 0.5

        self.angle = 0
        self.angleOffsets = (pi / 4, pi / 6)
        self.angleOffset = self.angleOffsets[0]
        self.deltaTime = 0

        # Key inputs
        self.WASD = [False for _ in range(4)]

        self.punching = False
        self.punchingHand = randint(1, 2)
        self.punchDelay = time()
        self.punchIdx = 0
        self.direction = 1

        """
            Punching Info:
                Punching Hands:
                    1: Left Hand,
                    2: Right Hand
                
                Direction:
                    1: Travelling Forward
                    2: returning Back
        """

        self.inventory = ["fists", None, None]
        self.fistTextRender = self.UI_FONT.render(self.inventory[0].upper(), True,
                                                  (255, 255, 255)), self.UI_FONT.render(
            "INFINITE", True, (255, 255, 255))
        self.weaponTextRenders = ["", ""]

        self.pastInventory = None

        self.inventoryIdx = 0
        self.previousIdx = None
        self.weaponPickUpDelay = time()

        self.sector = self.getGrid()

    def get_data_send_info(self):
        pos = self.getMap()

        if self.inventoryIdx > 0 and self.alive:
            weapon_surf = self.inventory[self.inventoryIdx].get_surface_data()
        else:
            weapon_surf = None

        return {
            "username": self.username_text,
            "color": self.color,
            "pos": pos,
            "sector": self.getGrid(),
            "angle": self.angle,
            "body_r": self.body.r,
            "left_hand": {
                "r": self.leftHand.r,
                "pos": (self.leftHand.x - self.displacement[0],
                        self.leftHand.y - self.displacement[1])
            },
            "right_hand": {
                "r": self.leftHand.r,
                "pos": (self.rightHand.x - self.displacement[0],
                        self.rightHand.y - self.displacement[1])
            },
            "weapon_surface": weapon_surf,
            "kills": self.kills,
            "shooter": self.shooter,
            "is_alive": self.alive
        }

    def getGrid(self):
        return int((self.body.x - self.displacement[0]) / self.GSTEP[0]), int(
            (self.body.y - self.displacement[1]) / self.GSTEP[1])

    def getMap(self):
        return self.body.x - self.displacement[0], self.body.y - self.displacement[1]

    def getGAME_SURFACE(self):
        return self.body.x, self.body.y

    def update(self, dt: float, can_play=True):
        self.deltaTime = dt

        if (self.health > 0 and self.readyStart) and not self.forceStop:
            self.regenerateHealth()
            self.updateAngle()

            if self.checkInput() and can_play:
                self.move()

            if self.punching and can_play:
                if time() - self.punchDelay > 0.01:
                    self.punch()

                    self.punchDelay = time()
            else:
                self.updateHands()

            if self.inventoryIdx:
                self.vel = self.constVel * self.inventory[self.inventoryIdx].mobility

                self.inventory[self.inventoryIdx].update(self.getMap(), self.angle, (0, 0))
            else:
                self.vel = self.constVel
        else:
            if not self.readyStart:
                self.playStartAni()

            if self.health <= 0 or self.forceStop:
                self.playDeadAni()

        # self.drawViewRadius()
        return tuple(self.displacement)

    def draw(self):
        self.drawBody()
        self.drawHands()

    def displayUI(self):
        if self.health >= 70:
            self.healthState = 0
        elif 40 < self.health < 70:
            self.healthState = 1
        else:
            self.healthState = 2

        if self.inventoryIdx:
            if self.inventory[self.inventoryIdx].reloading:
                self.inventory[self.inventoryIdx].displayReloading()

        if self.previousHealth != self.health or self.forceUIUpdate or self.healthState == 2:
            self.BL_UI_SURF.fill(self.BL_UI_SURF.get_colorkey())
            displayHealth = True

            if self.healthState == 2:
                healthPercent = self.health / 40

                if 2 * healthPercent < (time() - self.healthFlashTimer) < 2.4 * healthPercent:
                    displayHealth = False

                elif time() - self.healthFlashTimer > 2.4 * healthPercent:
                    displayHealth = True

                    if time() - self.healthFlashTimer > 2.9 * healthPercent:
                        self.healthFlashTimer = time()
                    else:
                        self.GAME_SURFACE.blit(self.HEALTH_VISUALS, (0, 0))

            else:
                self.healthFlashTimer = time()

            if displayHealth:
                perc = self.health / self.maxHealth

                if perc < 0:
                    perc = 0

                rect(self.BL_UI_SURF, (231 + perc * (118 - 231), 76 + perc * (215 - 76), 60 + perc * (196 - 60)),
                     Rect(13, self.BL_UI_SURF_DIMS[1] - 63,
                          (self.BL_UI_SURF_DIMS[0] - 26) * (self.health / self.maxHealth), 50))

            rect(self.BL_UI_SURF, (0, 0, 0),
                 Rect(13, self.BL_UI_SURF_DIMS[1] - 63, self.BL_UI_SURF_DIMS[0] - 26,
                      50),
                 width=3)

            if self.inventoryIdx == 0:
                ammoText = self.fistTextRender[1]
            else:
                ammoText = self.UI_FONT.render(str(self.inventory[self.inventoryIdx].getMag()), True, (255, 255, 255))

            self.BL_UI_SURF.blit(ammoText, (self.BL_UI_SURF_DIMS[0] - ammoText.get_width() - 20, 10))

            self.previousHealth = self.health

        if self.forceUIUpdate:
            for idx, surf in enumerate(self.BR_UI_SURF):
                surf.fill(surf.get_colorkey())

                rect(surf, (0, 0, 0), surf.get_rect(), width=4)

                if idx == 0:
                    weaponID = self.UI_FONT.render("FISTS", True, (255, 255, 255))
                    surf.blit(weaponID, (20, surf.get_height() / 2 - weaponID.get_height() / 2))
                    continue

                if self.inventory[idx] is not None:
                    weapon = self.inventory[idx]

                    weaponID = self.UI_FONT.render(weapon.weaponID, True, (255, 255, 255))
                    surf.blit(weaponID, (20, surf.get_height() / 2 - weaponID.get_height() / 2))

                    imgDims = weapon.imageSideDims
                    surf.blit(weapon.imageSide,
                              (surf.get_width() - imgDims[0] - 20, surf.get_height() / 2 - imgDims[1] / 2))

            self.forceUIUpdate = False

        self.GAME_SURFACE.blit(self.BG_BR_SURF,
                               (self.GAME_SURFACE_DIMS[0] - self.BG_BR_SURF.get_width(),
                                self.GAME_SURFACE_DIMS[1] - self.BG_BR_SURF.get_height()))

        for idx, surf in enumerate(self.BR_UI_SURF):
            self.GAME_SURFACE.blit(surf, (
                self.GAME_SURFACE_DIMS[0] - surf.get_width(),
                self.GAME_SURFACE_DIMS[1] - surf.get_height() * (idx + 1)))

        self.GAME_SURFACE.blit(self.BG_BL_SURF, (0, self.GAME_SURFACE_DIMS[1] - self.BL_UI_SURF_DIMS[1]))
        self.GAME_SURFACE.blit(self.BL_UI_SURF, (0, self.GAME_SURFACE_DIMS[1] - self.BL_UI_SURF_DIMS[1]))

        rect(self.GAME_SURFACE, (115, 198, 182), pg.Rect(self.GAME_SURFACE_DIMS[0] - self.BR_UI_SURF_DIMS[0],
                                                         self.GAME_SURFACE_DIMS[1] - (self.inventoryIdx + 1) *
                                                         self.BR_UI_SURF_DIMS[1],
                                                         *self.BR_UI_SURF_DIMS), width=4)

        self.GAME_SURFACE.blit(self.username,
                               (self.GAME_SURFACE_DIMS[0] / 2 - self.rut_size[0] / 2,
                                self.body.y - self.body.d - self.rut_size[1]))

    def regenerateHealth(self):
        if self.health < 100:
            if time() - self.healthRegenerateTime > 10:
                self.health += 1

        if self.health > 100:
            self.health = 100

    def updateAngle(self):
        mx, my = mouseGetPos()
        self.angle = atan2(self.body.y - my, mx - self.body.x)

    def drawBody(self):
        # Body
        circle(self.GAME_SURFACE, self.color, (self.body.x, self.body.y), self.body.r)

        # Outline
        circle(self.GAME_SURFACE, (0, 0, 0), (self.body.x, self.body.y), self.body.r, width=3)

    def drawHands(self):
        # Left hand
        circle(self.GAME_SURFACE, self.color, (self.leftHand.x, self.leftHand.y), self.leftHand.r)

        # Outline
        circle(self.GAME_SURFACE, (0, 0, 0), (self.leftHand.x, self.leftHand.y), self.leftHand.r, width=2)

        # Right Hands
        circle(self.GAME_SURFACE, self.color, (self.rightHand.x, self.rightHand.y), self.rightHand.r)

        # Outline
        circle(self.GAME_SURFACE, (0, 0, 0), (self.rightHand.x, self.rightHand.y), self.rightHand.r, width=2)

    def updateHands(self):
        leftHandPos = (self.body.x + self.body.r * cos(self.angle - self.angleOffset),
                       self.body.y - self.body.r * sin(self.angle - self.angleOffset))

        rightHandPos = (self.body.x + self.body.r * cos(self.angle + self.angleOffset),
                        self.body.y - self.body.r * sin(self.angle + self.angleOffset))

        self.leftHand.x, self.leftHand.y = leftHandPos
        self.rightHand.x, self.rightHand.y = rightHandPos

    def checkInput(self):
        key = keyboardGetPressed()
        mouseDown = mouseGetPressed(3)[0]
        moved = False

        if key[pg.K_w] or key[pg.K_UP]:
            self.WASD[0] = True
            moved = True
        else:
            self.WASD[0] = False

        if key[pg.K_a] or key[pg.K_LEFT]:
            self.WASD[1] = True
            moved = True
        else:
            self.WASD[1] = False

        if key[pg.K_s] or key[pg.K_DOWN]:
            self.WASD[2] = True
            moved = True
        else:
            self.WASD[2] = False

        if key[pg.K_d] or key[pg.K_RIGHT]:
            self.WASD[3] = True
            moved = True
        else:
            self.WASD[3] = False

        if mouseDown and not self.punching and not self.inventoryIdx:
            self.punching = True

        self.interactInput(key)
        return moved

    def move(self):
        vel = self.vel * self.deltaTime

        getMap = self.getMap()
        boundary = go.GAME_MAP.checkEntityOutOfMap(getMap, self.body.r)
        collision, pointsCollided, pointLoc, null = go.GAME_MAP.checkEntityCrateCollision(getMap, self.sector,
                                                                                          self.body.r)

        # Movement Strength
        up, left, down, right = 0, 0, 0, 0

        if self.WASD[0] and not boundary[0]:
            if True in pointsCollided[1:4]:
                left = 1
            elif True in pointsCollided[5:8]:
                right = 1
            else:
                if collision[0]:
                    up = 0
                else:
                    up = 1

        if self.WASD[2] and not boundary[2]:
            if True in pointsCollided[9:12]:
                right = 1
            elif True in pointsCollided[13:16]:
                left = 1
            else:
                if collision[2]:
                    down = 0
                else:
                    down = 1

        if self.WASD[1] and not boundary[1]:
            if True in pointsCollided[5:8] and down == 0:
                down = 1
            elif True in pointsCollided[9:12] and up == 0:
                up = 1
            else:
                if collision[1]:
                    left = 0
                else:
                    left = 1

        if self.WASD[3] and not boundary[3]:
            if True in pointsCollided[1:4] and down == 0:
                down = 1
            elif True in pointsCollided[13:16] and up == 0:
                up = 1
            else:
                if collision[3]:
                    right = 0
                else:
                    right = 1

        changeInX = left - right
        changeInY = up - down

        if abs(changeInX) + abs(changeInY) > 1:
            changeInX /= self.velNormalize
            changeInY /= self.velNormalize

        self.displacement[0] += vel * changeInX
        self.displacement[1] += vel * changeInY

        self.sector = self.getGrid()

    def punch(self):
        changeInX = 2 * cos(self.angle)
        changeInY = 2 * sin(self.angle)

        if self.punchIdx < 10:
            if self.punchingHand == 1:
                self.leftHand.x += changeInX
                self.leftHand.y -= changeInY

            elif self.punchingHand == 2:
                self.rightHand.x += changeInX
                self.rightHand.y -= changeInY

            self.punchIdx += 1

        elif self.punchIdx < 20:
            if self.punchIdx == 10:
                if self.punchingHand == 1:
                    handPos = (self.leftHand.x - self.displacement[0], self.leftHand.y - self.displacement[1])
                    handR = self.leftHand.r
                else:
                    handPos = (self.rightHand.x - self.displacement[0], self.rightHand.y - self.displacement[1])
                    handR = self.rightHand.r

                go.GAME_MAP.checkContactCrateCollision(handPos, self.sector, handR, 15)
                self.punchEntityColl(handPos, handR, self)

            if self.punchingHand == 1:
                self.leftHand.x -= changeInX
                self.leftHand.y += changeInY

            elif self.punchingHand == 2:
                self.rightHand.x -= changeInX
                self.rightHand.y += changeInY

            self.punchIdx += 1
        else:
            self.punchingHand = randint(1, 2)
            self.punching = False
            self.punchIdx = 0
            self.updateHands()

    def interactInput(self, key):
        weapon1Equipped = self.inventory[1]
        weapon2Equipped = self.inventory[2]

        if key[pg.K_1]:
            self.forceUIUpdate = True

            self.inventoryIdx = 0
            self.angleOffset = self.angleOffsets[0]

        elif key[pg.K_2] and weapon1Equipped is not None:
            self.forceUIUpdate = True

            self.inventoryIdx = 1
            self.angleOffset = self.angleOffsets[1]

        elif key[pg.K_3] and weapon2Equipped is not None:
            self.forceUIUpdate = True

            self.inventoryIdx = 2
            self.angleOffset = self.angleOffsets[1]

        if key[pg.K_f] and time() - self.weaponPickUpDelay >= 1:
            weapon = None
            possibleWeapon = go.GAME_MAP.checkEntityOverWeapon(self.getMap(), self.sector, self.body.r)

            if possibleWeapon is not None:
                self.forceUIUpdate = True

                if possibleWeapon.name == "M1911":
                    weapon = M1911(self.GAME_SURFACE, self.WEAPON_SURF, self.BULLET_SURF, self.GSTEP, self.getMap(),
                                   self,
                                   possibleWeapon.clip,
                                   possibleWeapon.ammo)

                elif possibleWeapon.name == "Revolver":
                    weapon = Revolver(self.GAME_SURFACE, self.WEAPON_SURF, self.BULLET_SURF, self.GSTEP, self.getMap(),
                                      self,
                                      possibleWeapon.clip,
                                      possibleWeapon.ammo)

                elif possibleWeapon.name == "AWP":
                    weapon = AWP(self.GAME_SURFACE, self.WEAPON_SURF, self.BULLET_SURF, self.GSTEP, self.getMap(), self,
                                 possibleWeapon.clip,
                                 possibleWeapon.ammo)

                if weapon1Equipped is None:
                    self.inventory[1] = weapon
                    self.weaponTextRenders[0] = self.UI_FONT.render(weapon.weaponID.upper(), True, (255, 255, 255))
                    self.inventoryIdx = 1

                elif weapon2Equipped is None:
                    self.inventory[2] = weapon
                    self.weaponTextRenders[1] = self.UI_FONT.render(weapon.weaponID.upper(), True, (255, 255, 255))
                    self.inventoryIdx = 2
                else:
                    if self.inventoryIdx == 0:
                        idx = 1
                    else:
                        idx = self.inventoryIdx

                    go.GAME_MAP.spawnWeapon(self.getMap(), self.sector, self.inventory[idx].weaponID,
                                            self.inventory[idx].clip,
                                            self.inventory[idx].ammo)
                    self.inventory[idx] = weapon

                self.angleOffset = self.angleOffsets[1]

            self.weaponPickUpDelay = time()

    def playStartAni(self):
        changeBody = self.deltaTime * 0.4
        changeHand = changeBody * (self.completeHandR / self.completeBodyR)

        if self.body.r < self.completeBodyR:
            self.body.r += changeBody

        if self.leftHand.r < self.completeHandR:
            self.leftHand.r += changeHand
            self.rightHand.r += changeHand

        if self.body.r >= self.completeBodyR and self.leftHand.r > self.completeHandR and self.rightHand.r > \
                self.completeHandR:
            self.body.r = self.completeBodyR

            self.leftHand.r = self.completeHandR
            self.rightHand.r = self.completeHandR

            self.readyStart = True

    def playDeadAni(self):
        changeBody = self.deltaTime * 0.4
        changeHand = changeBody * (self.completeHandR / self.completeBodyR)

        if self.body.r < 0:
            self.alive = False
        else:
            self.body.r -= changeBody
            self.leftHand.r -= changeHand
            self.rightHand.r -= changeHand

    def dropLoot(self, spawnWeaponFunc):
        offsetPos = (0, 0)
        x, y = self.getMap()
        if self.inventory[1] is not None:
            spawnWeaponFunc((x, y), self.sector, self.inventory[1].weaponID, self.inventory[1].clip,
                            self.inventory[1].ammo)

            offsetPos = 100

        if self.inventory[2] is not None:
            if offsetPos == (0, 0):
                sector = self.sector
            else:
                sector = int((x + offsetPos[0] - self.displacement[0]) / self.GSTEP[0]), int(
                    (y + offsetPos[1] - self.displacement[1]) / self.GSTEP[1])

            spawnWeaponFunc((x + offsetPos[0], y + offsetPos[1]), sector, self.inventory[2].weaponID,
                            self.inventory[2].clip,
                            self.inventory[2].ammo)
