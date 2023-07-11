import pygame as pg
from pygame.draw import *

from random import randint, randrange

from math import atan2, cos, sin, pi
from copy import copy
from time import time

from Scripts.weapons import *
from Scripts.extra_functions import getBoundingSectors


class Body:
    __slots__ = "x", "y", "r", "d"

    def __init__(self, x: float, y: float, r: float, d: float):
        self.x = x
        self.y = y
        self.r = r
        self.d = d


class Hand:
    __slots__ = "x", "y", "r"

    def __init__(self, x: float, y: float, r: float):
        self.x = x
        self.y = y
        self.r = r


class Enemy:
    def __init__(self, username: pg.Surface, GAME_SURFACE: pg.Surface, WEAPON_SURF: pg.Surface, BULLET_SURF: pg.Surface, ID: int,
                 color: tuple,
                 MAP_SIZE: tuple,
                 GSTEP: tuple,
                 startPos: tuple,
                 externalFuncs: tuple,
                 bullets: list):
        pg.init()

        self.alive = True
        self.readyStart = False
        self.forceStop = False
        self.active = True

        self.username = username
        self.rut_size = username.get_size()

        self.ID = ID
        self.color = color

        self.GAME_SURFACE = GAME_SURFACE
        self.GAME_SURFACE_DIMS = GAME_SURFACE.get_size()
        self.GAME_SURFACE_CENTER = (GAME_SURFACE.get_width() / 2, GAME_SURFACE.get_height() / 2)

        self.WEAPON_SURF = WEAPON_SURF
        self.BULLET_SURF = BULLET_SURF

        self.healthRenderDistX = 400
        self.healthRenderDistY = 400

        self.MAP_SIZE = MAP_SIZE
        self.GSTEP = GSTEP

        self.checkCollision, self.punchCrateColl, self.punchEntityColl, self.checkEntityOverWeapon, self.spawnWeapon = externalFuncs

        self.bullets = bullets

        self.completeBodyR = 20
        self.completeHandR = 10

        self.body = Body(startPos[0], startPos[1], 0, self.completeBodyR * 2)
        self.leftHand = Hand(self.body.x - self.completeBodyR * cos(pi / 5),
                             self.body.y - self.completeBodyR * sin(pi / 5), 0)
        self.rightHand = Hand(self.body.x + self.completeBodyR * cos(pi / 5),
                              self.body.y - self.completeBodyR * sin(pi / 5), 0)

        self.inCameraView = False
        self.sector = self.getGrid()

        self.health = 100
        self.healthRegenerateTime = 0

        self.maxHealth = self.health

        self.constVel = 5
        self.vel = self.constVel
        self.velNormalize = 2 ** 0.5

        self.deltaTime = 0

        self.displacement = (0, 0)

        # Variables for pathfinding
        self.grid = None

        self.path = []
        self.openSet = []
        self.closedSet = []

        self.tracePath = []
        self.tempPath = None

        self.editedGridPos = []

        self.endPos = None
        self.end = None

        self.searchingForPath = False
        self.foundPath = False

        # Angles
        self.handAngle = 0
        self.angleOffsets = (pi / 4, pi / 6)
        self.angleOffset = self.angleOffsets[0]
        self.moveAngle = 0

        self.crateList = []
        self.crateTarget = None

        self.enemiesList = []
        self.enemyTarget = None

        self.groundWeaponsList = []
        self.groundWeaponTarget = None

        """
            Enemy Priority:
                1: Find Crate,
                2: Find Weapon,
                3: Find Enemy
        """
        self.priority = 3

        self.punching = 0
        self.punchingHand = randint(1, 2)
        self.punchDelay = time()
        self.punchIdx = 0
        self.direction = 1
        self.punchCoolDown = time()
        self.punchCoolDownTime = randrange(1, 2)

        self.GAME_SURFACERect = pg.Rect(0, 0, *self.GAME_SURFACE.get_size())
        self.collideAngles = (0, pi / 2, pi / 2 * pi / 3)

        self.weapon = None

    def checkInCameraView(self, d: tuple):
        """
        :param d: displacement
        :return:
        """
        return (self.body.x + self.body.r + d[0] >= 0) and (
                self.body.x - self.body.r + d[0] <= self.GAME_SURFACE_DIMS[0]) and (
                       self.body.y + self.body.r + d[1] >= 0) and (
                       self.body.y - self.body.r + d[1] <= self.GAME_SURFACE_DIMS[1])

    def checkHealthInView(self, d: tuple):
        """
        :param d: displacement
        :return:
        """
        return (self.body.x + self.body.r + d[0] >= self.GAME_SURFACE_DIMS[0] / 2 - self.healthRenderDistX) and (
                self.body.x - self.body.r + d[0] <= self.GAME_SURFACE_DIMS[0] / 2 + self.healthRenderDistX) and (
                       self.body.y + self.body.r + d[1] >= self.GAME_SURFACE_DIMS[
                   1] / 2 - self.healthRenderDistY) and (
                       self.body.y - self.body.r + d[1] <= self.GAME_SURFACE_DIMS[1] / 2 + self.healthRenderDistY)

    def getGrid(self):
        return int(self.body.x / self.GSTEP[0]), int(self.body.y / self.GSTEP[1])

    def get_game_surface(self):
        return self.body.x + self.displacement[0], self.body.y + self.displacement[1]

    def getMapRect(self):
        return pg.Rect(self.body.x - self.body.r, self.body.y - self.body.r, self.body.d, self.body.d)

    def getMap(self):
        return self.body.x, self.body.y

    def getDist(self, a: tuple, b: tuple):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def findNearestCrate(self):
        winner = 0
        shortDist = 10000000000

        selfPos = self.getMap()

        for idx, crate in enumerate(self.crateList):
            distance = self.getDist(selfPos, crate.getMap())

            if crate.sector == self.sector:
                winner = idx
                break

            if distance < shortDist:
                winner = idx
                shortDist = distance

        try:
            self.crateTarget = self.crateList[winner]
        except IndexError as e:
            return

    def findNearestWeapon(self):
        sectors = getBoundingSectors(self.sector)

        winner = 0
        shortDist = 10000000000

        selfPos = self.getMap()

        for idx, weapon in enumerate(self.groundWeaponsList):
            distance = self.getDist(selfPos, weapon.pos)

            if not weapon.attainable:
                continue

            if weapon.sector in sectors:
                winner = idx
                break

            if distance < shortDist:
                winner = idx
                shortDist = distance

        try:
            self.groundWeaponTarget = self.groundWeaponsList[winner]
        except IndexError:
            self.priority = 1
            return

    def findNearestEnemy(self):
        sectors = getBoundingSectors(self.sector)

        winner = 0
        shortDist = 10000000000

        selfPos = self.getMap()

        for enemy in self.enemiesList:
            if enemy == self:
                continue

            distance = self.getDist(selfPos, enemy.getMap())

            if enemy.sector in sectors:
                winner = enemy
                break

            if distance < shortDist:
                winner = enemy
                shortDist = distance

        self.enemyTarget = winner

    def setupPath(self, endPos):
        self.endPos = endPos

        self.path.clear()
        self.openSet.clear()
        self.closedSet.clear()

        self.tracePath.clear()
        self.tempPath = None

        for pos in self.editedGridPos:
            self.grid[pos[0]][pos[1]].pos = [pos[0], pos[1]]
            self.grid[pos[0]][pos[1]].f = 0
            self.grid[pos[0]][pos[1]].g = 0
            self.grid[pos[0]][pos[1]].h = 0
            self.grid[pos[0]][pos[1]].previous = None

        self.editedGridPos.clear()

        start = (int(self.getMap()[0] / (self.GSTEP[0])), int(self.getMap()[1] / (self.GSTEP[1])))
        end = (int(endPos[0] / (self.GSTEP[0])), int(endPos[1] / (self.GSTEP[1])))

        start = self.grid[start[0]][start[1]]
        self.end = self.grid[end[0]][end[1]]

        if start.wall:
            for neighbor in start.neighbors:
                neighborGrid = self.grid[neighbor[0]][neighbor[1]]
                if not neighborGrid.wall:
                    start = neighborGrid
                    break

        if self.end.wall:
            for neighbor in self.end.neighbors:
                neighborGrid = self.grid[neighbor[0]][neighbor[1]]
                if not neighborGrid.wall:
                    self.end = neighborGrid
                    break

        self.openSet.append(start)

        self.foundPath = False
        self.searchingForPath = True

    def tracePathBack(self):
        self.tempPath = self.grid[self.tempPath.previous[0]][self.tempPath.previous[1]]

        if self.tempPath.previous:
            self.tracePath.append(self.tempPath.previous)

    def findPath(self):
        try:
            winner = 0

            for idx, possiblePos in enumerate(self.openSet):
                if possiblePos.f < self.openSet[winner].f:
                    winner = idx
                    break

            current = self.openSet[winner]

            if current is self.end:
                if not len(self.tracePath):
                    self.tempPath = current
                    self.tracePath = [self.tempPath.previous]

                if self.tempPath.previous:
                    self.tracePathBack()
                else:
                    self.path = [
                        (p[0] * self.GSTEP[0] + self.GSTEP[0] / 2, p[1] * self.GSTEP[1] + self.GSTEP[1] / 2)
                        for p
                        in self.tracePath]
                    self.path.reverse()

                    self.foundPath = True
                    self.searchingForPath = False

                return

            self.openSet.pop(winner)
            self.closedSet.append(current)

            neighbors = current.neighbors

            for neighbor in neighbors:
                neighbor = self.grid[neighbor[0]][neighbor[1]]

                if neighbor not in self.closedSet and not neighbor.wall:

                    tempG = current.g + 1

                    if neighbor not in self.openSet:
                        self.openSet.append(neighbor)
                    elif tempG >= neighbor.g:
                        continue

                    neighbor.h = abs(neighbor.pos[0] - self.end.pos[0]) + abs(neighbor.pos[1] - self.end.pos[1])
                    neighbor.f = neighbor.g + neighbor.h

                    neighbor.previous = current.pos

                    self.editedGridPos.append(copy(neighbor.pos))
        except IndexError:
            if self.priority == 1:
                self.findNearestCrate()
            elif self.priority == 2:
                self.findNearestWeapon()
            else:
                self.findNearestEnemy()

    def priorityOne(self):
        if self.crateTarget not in self.crateList:
            self.crateTarget = None

        try:
            self.endPos = self.crateTarget.getMap()
        except Exception as e:
            # print("P1 error:", e)
            self.findNearestCrate()

            if self.crateTarget:
                self.endPos = self.crateTarget.getMap()
            else:
                if len(self.groundWeaponsList):
                    self.priority = 2
                elif not len(self.crateList):
                    self.priority = 3

    def priorityTwo(self):
        if self.groundWeaponTarget not in self.groundWeaponsList:
            self.groundWeaponTarget = None

        try:
            self.endPos = self.groundWeaponTarget.pos
        except (AttributeError, IndexError, TypeError) as e:
            # print("P2 1 error: ", e)
            if self.weapon is None and len(self.crateList):
                self.priority = 1

            else:
                try:
                    self.findNearestWeapon()
                    self.endPos = self.groundWeaponTarget.pos
                except (AttributeError, TypeError):
                    # print("P2 2 error: ", e)
                    self.priority = 3

    def priorityThree(self):
        if self.enemyTarget not in self.enemiesList:
            self.enemyTarget = None

        try:
            self.endPos = self.enemyTarget.getMap()
        except (AttributeError, IndexError, TypeError) as e:
            # print("P3 1 error: ", e)
            if self.weapon is None and len(self.groundWeaponsList):
                self.priority = 2
            elif self.weapon is None and len(self.crateList):
                self.priority = 1
            else:
                try:
                    self.findNearestEnemy()
                    self.endPos = self.enemyTarget.getMap()
                except AttributeError as e:
                    # print("P3 2 error: ", e)
                    self.priority = 3

    def clearPriorities(self, priority):
        if priority == 1:
            self.crateTarget = None
            self.priority = 2
        elif priority == 2:
            self.groundWeaponTarget = None
            self.priority = 3
        elif priority == 3:
            self.enemyTarget = None
            self.priority = 1

    def update(self, displacement, dt):
        self.displacement = displacement
        self.deltaTime = dt

        if (self.health > 0 and self.readyStart) and not self.forceStop and self.active:
            self.regenerateHealth()
            hasWeapon = self.weapon is not None

            if hasWeapon:
                self.priority = 3
            else:
                # Priority is one --> Search for crate
                if self.priority == 1 and not hasWeapon:
                    self.priorityOne()

                    if self.crateTarget is None:
                        self.clearPriorities(1)
                        return

                # Priority is two --> search for weapons on ground
                if self.priority == 2 and not hasWeapon:
                    self.priorityTwo()

                    if self.groundWeaponTarget is None:
                        self.clearPriorities(2)
                        return

            # Priority is three --> search for enemy
            if self.priority == 3:
                self.priorityThree()

                if self.enemyTarget is None:
                    self.clearPriorities(3)
                    return

            distToTarget = self.getDist(self.getMap(), self.endPos)

            if not hasWeapon or (self.weapon.ammo <= 0 and self.weapon.clip <= 0):
                threshold = self.body.r

                self.angleOffset = self.angleOffsets[0]
                self.vel = self.constVel

            else:
                threshold = self.weapon.range

                self.angleOffset = self.angleOffsets[1]
                self.vel = self.constVel * self.weapon.mobility

            if not len(self.path) and threshold < distToTarget < (self.GSTEP[0] + self.GSTEP[1]) * 2:
                self.path = [self.endPos]

            elif not len(self.path) and distToTarget > threshold:
                if not self.searchingForPath and not self.foundPath:
                    self.setupPath(self.endPos)

                elif self.searchingForPath and not self.foundPath:
                    self.findPath()

                else:
                    self.foundPath = False
                    self.searchingForPath = False

            elif len(self.path) and self.priority == 3 and self.getDist(self.getMap(),
                                                                        self.enemyTarget.getMap()) < self.getDist(
                self.enemyTarget.getMap(), self.path[-1]):
                self.path.clear()

                self.searchingForPath = False
                self.foundPath = False

            elif len(self.path) and not self.punching:
                self.move()

            if self.weapon is None or (self.weapon.ammo <= 0 and self.weapon.clip <= 0):
                if self.priority == 1:
                    distToCrate = self.getDist(self.getMap(), self.crateTarget.getCenter())

                    if int(distToCrate) <= self.crateTarget.w + self.body.r:
                        if not self.punching:
                            self.path.clear()
                            self.punching = 1
                elif self.priority == 2:
                    if distToTarget <= self.body.r:
                        self.pickUpWeapon()

                elif self.priority == 3:
                    if distToTarget <= self.body.d and time() - self.punchCoolDown > self.punchCoolDownTime:
                        if not self.punching:
                            self.punching = 1
            else:
                self.priority = 3
                self.weapon.update(self.getMap(), pi - self.handAngle, (0, 0))

                if distToTarget < self.weapon.range:
                    self.weapon.checkInput(True)

            if self.punching:
                if time() - self.punchDelay > 0.01:
                    self.punch()

                    self.punchDelay = time()
            else:
                self.updateHands()

            self.updateHandAngle()
            self.updateMoveAngle()
        else:
            if not self.readyStart:
                self.playStartAni()

            if self.health <= 0 or self.forceStop:
                self.playDeadAni()

    def draw(self):
        if self.checkInCameraView(self.displacement):
            if self.checkHealthInView(self.displacement) and self.health > 0 and not self.forceStop:
                self.drawHealth()

            self.drawBody()
            self.drawHands()

            self.inCameraView = True
        else:
            self.inCameraView = False

    def render_username(self):
        if self.checkHealthInView(self.displacement):
            offset_y = self.body.d * 1.8 - self.rut_size[1]
        else:
            offset_y = self.body.d * 1.2 - self.rut_size[1]

        self.GAME_SURFACE.blit(self.username, (self.get_game_surface()[0] - self.rut_size[0] / 2, self.get_game_surface()[1] - offset_y))

    def regenerateHealth(self):
        if self.health < 100:
            if time() - self.healthRegenerateTime > 10:
                self.health += 1

    def updateHandAngle(self):
        if self.priority == 1:
            try:
                wantedAngle = atan2(self.body.y - self.crateTarget.getCenter()[1],
                                    self.body.x - self.crateTarget.getCenter()[0])
                self.handAngle = wantedAngle
            except AttributeError:
                return

        elif self.priority == 2:
            try:
                wantedAngle = atan2(self.body.y - self.groundWeaponTarget.pos[1],
                                    self.body.x - self.groundWeaponTarget.pos[0])
                self.handAngle = wantedAngle
            except TypeError:
                self.priority = 1

        elif self.priority == 3:
            try:
                wantedAngle = atan2(self.body.y - self.enemyTarget.getMap()[1],
                                    self.body.x - self.enemyTarget.getMap()[0])
                self.handAngle = wantedAngle
            except AttributeError:
                self.priority = 1

    def updateMoveAngle(self):
        try:
            self.moveAngle = atan2(self.path[0][1] - self.body.y, self.path[0][0] - self.body.x)
        except IndexError as e:
            # print("Move Angle err", e)
            self.moveAngle = self.handAngle

    def drawHealth(self):
        # Display health
        getMap = self.getMap()

        healthRect = (
            getMap[0] - self.body.r + self.displacement[0],
            (getMap[1] - self.body.d) + self.displacement[1],
            self.body.d * (self.health / self.maxHealth), 13)

        healthRectOutline = (
            getMap[0] - self.body.r + self.displacement[0],
            (getMap[1] - self.body.d) + self.displacement[1],
            self.body.d, 13)

        rect(self.GAME_SURFACE, (192, 57, 43), pg.Rect(healthRect))
        rect(self.GAME_SURFACE, (0, 0, 0), pg.Rect(healthRectOutline), width=3)

    def drawBody(self):
        # Body
        circle(self.GAME_SURFACE, self.color,
               (self.body.x + self.displacement[0], self.body.y + self.displacement[1]), self.body.r)

        # Outline
        circle(self.GAME_SURFACE, (0, 0, 0),
               (self.body.x + self.displacement[0], self.body.y + self.displacement[1]),
               self.body.r, width=3)

    def drawHands(self):
        # Left hand
        circle(self.GAME_SURFACE, self.color,
               (self.leftHand.x + self.displacement[0], self.leftHand.y + self.displacement[1]),
               self.leftHand.r)

        # Outline
        circle(self.GAME_SURFACE, (0, 0, 0),
               (self.leftHand.x + self.displacement[0], self.leftHand.y + self.displacement[1]),
               self.leftHand.r, width=2)

        # Right Hands
        circle(self.GAME_SURFACE, self.color,
               (self.rightHand.x + self.displacement[0], self.rightHand.y + self.displacement[1]),
               self.rightHand.r)

        # Outline
        circle(self.GAME_SURFACE, (0, 0, 0),
               (self.rightHand.x + self.displacement[0], self.rightHand.y + self.displacement[1]),
               self.rightHand.r, width=2)

    def updateHands(self):
        leftHandPos = (self.body.x - self.body.r * cos(self.handAngle - self.angleOffset),
                       self.body.y - self.body.r * sin(self.handAngle - self.angleOffset))

        rightHandPos = (self.body.x - self.body.r * cos(self.handAngle + self.angleOffset),
                        self.body.y - self.body.r * sin(self.handAngle + self.angleOffset))

        self.leftHand.x, self.leftHand.y = leftHandPos
        self.rightHand.x, self.rightHand.y = rightHandPos

    def drawPath(self):
        for path in self.path:
            circle(self.GAME_SURFACE, (93, 173, 226), (path[0] + self.displacement[0], path[1] + self.displacement[1]),
                   40, width=9)

    def move(self):
        vel = self.vel * self.deltaTime
        collision, pointsCollided, pointLoc, obj = self.checkCollision(self.getMap(), self.sector, self.body.r)

        changeInX = vel * cos(self.moveAngle)
        changeInY = vel * sin(self.moveAngle)

        if True not in pointsCollided:
            self.body.x += changeInX
            self.body.y += changeInY

        else:
            # WASD
            inputs = [False for _ in range(4)]
            up, left, down, right = 0, 0, 0, 0

            if changeInY > 0:
                inputs[2] = True
            elif changeInY < 0:
                inputs[0] = True

            if changeInX > 0:
                inputs[3] = True
            elif changeInX < 0:
                inputs[1] = True

            if collision[2:7]:
                myPos = self.getMap()
                objPos = obj.getMap()

                x1 = self.getDist((myPos[0], 0),
                                  (objPos[0], 0))
                x2 = self.getDist((self.getMap()[0], 0),
                                  (objPos[0] + obj.w, 0))

                if x1 < x2:
                    left = 1
                else:
                    right = 1

            elif pointsCollided[0:3] or pointsCollided[14:16]:
                myPos = self.getMap()
                objPos = obj.getMap()

                y1 = self.getDist((0, myPos[1]),
                                  (0, objPos[1]))
                y2 = self.getDist((0, myPos[1]),
                                  (0, objPos[1] + obj.h))

                if y1 < y2:
                    up = 1
                else:
                    down = 1

            if pointsCollided[6:11]:
                myPos = self.getMap()
                objPos = obj.getMap()

                y1 = self.getDist((0, myPos[1]),
                                  (0, objPos[1]))
                y2 = self.getDist((0, myPos[1]),
                                  (0, objPos[1] + obj.h))

                if y1 < y2:
                    up += 1
                else:
                    down += 1

            elif pointsCollided[10:15]:
                myPos = self.getMap()
                objPos = obj.getMap()

                x1 = self.getDist((myPos[0], 0),
                                  (objPos[0], 0))
                x2 = self.getDist((self.getMap()[0], 0),
                                  (objPos[0] + obj.w, 0))

                if x1 < x2:
                    left = 1
                    right = 0
                else:
                    right = 1
                    left = 0

            changeInX = right - left
            changeInY = down - up

            if abs(changeInX) + abs(changeInY) > 1:
                changeInX /= self.velNormalize
                changeInY /= self.velNormalize

            self.body.x += vel * changeInX
            self.body.y += vel * changeInY

        if abs(self.body.x - self.path[0][0]) + abs(self.body.y - self.path[0][1]) < self.body.r:
            self.path.pop(0)

        self.sector = self.getGrid()

    def punch(self):
        changeInX = 2 * cos(self.handAngle)
        changeInY = 2 * sin(self.handAngle)

        if self.punchIdx < 10:
            if self.punchingHand == 1:
                self.leftHand.x -= changeInX
                self.leftHand.y -= changeInY

            elif self.punchingHand == 2:
                self.rightHand.x -= changeInX
                self.rightHand.y -= changeInY

            self.punchIdx += 1

        elif self.punchIdx < 20:
            if self.punchIdx == 10:
                if self.punchingHand == 1:
                    handPos = (self.leftHand.x, self.leftHand.y)
                    handR = self.leftHand.r
                else:
                    handPos = (self.rightHand.x, self.rightHand.y)
                    handR = self.rightHand.r

                crateColl = self.punchCrateColl(handPos, self.sector, handR, 15)
                entityColl = self.punchEntityColl(handPos, handR, self)

                if crateColl or entityColl:
                    self.path.clear()

                if crateColl == 1:
                    self.pickUpWeapon()
                    self.priority = 2

            if self.punchingHand == 1:
                self.leftHand.x += changeInX
                self.leftHand.y += changeInY

            elif self.punchingHand == 2:
                self.rightHand.x += changeInX
                self.rightHand.y += changeInY

            self.punchIdx += 1
        else:
            self.punchingHand = randint(1, 2)
            self.punching = False
            self.punchIdx = 0

            self.punchCoolDown = time()
            self.punchCoolDownTime = randrange(1, 2)

            self.updateHandAngle()
            self.updateHands()

    def pickUpWeapon(self):
        if not self.groundWeaponTarget:
            try:
                self.findNearestWeapon()
            except Exception as e:
                print(e)
                self.priority = 1

        weapon = None
        possibleWeapon = self.checkEntityOverWeapon(self.getMap(), self.sector, self.getMapRect())

        if possibleWeapon is not None:
            if possibleWeapon.name == "M1911":
                weapon = M1911(self.GAME_SURFACE, self.WEAPON_SURF, self.BULLET_SURF, self.GSTEP, self.getMap(), self,
                               possibleWeapon.clip,
                               possibleWeapon.ammo)

            elif possibleWeapon.name == "Revolver":
                weapon = Revolver(self.GAME_SURFACE, self.WEAPON_SURF, self.BULLET_SURF, self.GSTEP, self.getMap(), self,
                                  possibleWeapon.clip,
                                  possibleWeapon.ammo)

            elif possibleWeapon.name == "AWP":
                weapon = AWP(self.GAME_SURFACE, self.WEAPON_SURF, self.BULLET_SURF, self.GSTEP, self.getMap(), self,
                             possibleWeapon.clip,
                             possibleWeapon.ammo)

            if weapon is not None:
                self.weapon = weapon
            self.priority = 3

    def playStartAni(self):
        changeBody = self.deltaTime * 0.4
        changeHand = changeBody * (self.completeHandR / self.completeBodyR)

        if self.body.r < self.completeBodyR:
            self.body.r += changeBody

        if self.leftHand.r < self.completeHandR:
            self.leftHand.r += changeHand
            self.rightHand.r += changeHand

        if self.body.r >= self.completeBodyR and self.leftHand.r > self.completeHandR and self.rightHand.r > self.completeHandR:
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

    def dropLoot(self):
        if self.weapon is not None:
            self.spawnWeapon(self.getMap(), self.sector, self.weapon.weaponID, self.weapon.clip, self.weapon.ammo)
            self.weapon = None
        else:
            return
