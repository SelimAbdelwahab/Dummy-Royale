import pygame as pg
from pygame import Rect
from pygame.draw import rect
from time import time
from random import choice as rdChoice, randint as rdint
from math import sin, cos, pi
from Scripts.crate import Crate
from Scripts.extra_functions import *


class GROUND_WEAPON_ID:
    __slots__ = "name", "img"

    def __init__(self, name: str, img: pg.Surface):
        self.name = name
        self.img = img


class GROUND_WEAPON:
    __slots__ = "name", "pos", "sector", "rect", "img", "clip", "ammo", "blitted", "pickedUp", "attainable"

    def __init__(self, name: str, pos: tuple, sector: tuple, rect: pg.rect, img: pg.Surface, clip: int, ammo: int,
                 blitted: bool, pickedUp: bool, attainable: bool):
        self.name = name
        self.pos = pos
        self.sector = sector
        self.rect = rect
        self.img = img
        self.clip = clip
        self.ammo = ammo
        self.blitted = blitted
        self.pickedUp = pickedUp
        self.attainable = attainable


class GameMap:
    def __init__(self, Game, GAME_SURFACE: pg.Surface, loadFunc):
        """

        :type GAME_SURFACE: `Pygame Surface (Object)`
        """

        pg.init()

        self.game = Game
        self.GAME_SURFACE = GAME_SURFACE
        self.GAME_SURFACE_DIMS = GAME_SURFACE.get_size()

        self.GSTEP = (100, 100)

        self.displacement = (0, 0)
        self.MAP_SIZE = (4000, 4000)

        self.sectorHoriEdges = (0, int(4000 / self.GSTEP[0]))
        self.sectorVertEdges = (0, int(4000 / self.GSTEP[1]))

        self.BG_SURFACE = pg.Surface(self.MAP_SIZE)
        self.BG_SURFACE.set_colorkey((0, 0, 0))

        self.ENTITY_SURF = pg.Surface(self.MAP_SIZE).convert()
        self.ENTITY_SURF.set_colorkey((255, 255, 255))
        self.ENTITY_SURF.fill(self.ENTITY_SURF.get_colorkey())

        self.GROUND_WEAPON_SURF = pg.Surface(self.MAP_SIZE)
        self.GROUND_WEAPON_SURF.set_colorkey((0, 0, 0))
        self.GROUND_WEAPON_SURF.fill(self.GROUND_WEAPON_SURF.get_colorkey())

        self.BULLET_SURF = pg.Surface(self.MAP_SIZE).convert()
        self.BULLET_SURF.set_colorkey((255, 255, 255))
        self.BULLET_SURF.fill(self.BULLET_SURF.get_colorkey())

        self.WEAPON_SURF = pg.Surface(self.MAP_SIZE).convert()
        self.WEAPON_SURF.set_colorkey((132, 132, 132))
        self.WEAPON_SURF.fill(self.WEAPON_SURF.get_colorkey())

        # groundTile, gtSF = resizeImage("Assets/game/TileSets/RPG Nature Tileset.png", 5, scale)
        groundTile = pg.image.load("Assets/game/TileSets/RPG Nature Tileset.png").convert()
        scaleTo = (groundTile.get_width() * (self.GSTEP[0] / 48), groundTile.get_height() * (self.GSTEP[1] / 48))
        self.groundTile, gtSF = scaleImageTo("Assets/game/TileSets/RPG Nature Tileset.png", scaleTo)
        self.groundTileInfo = [
            (round((i * 33) * gtSF[0]), round(65 * gtSF[1]), round(30 * gtSF[0]), round(31 * gtSF[1])) for
            i in
            range(3) if i != 1]

        self.crateTile, ctSF = resizeImage("Assets/game/TileSets/tilesheet_complete.png", 1, (1, 1))
        self.crateTileInfo = pg.Rect(1285 * ctSF[0], 261 * ctSF[1], 54 * ctSF[0], 54 * ctSF[1])

        self.crates = []
        self.cratesInNeedOfUpdating = []

        for x in range(0, self.MAP_SIZE[0], self.groundTileInfo[0][2]):
            for y in range(0, self.MAP_SIZE[1], self.groundTileInfo[0][3]):
                self.BG_SURFACE.blit(self.groundTile, (x, y), pg.Rect(rdChoice(self.groundTileInfo)))

        for x in range(0, self.MAP_SIZE[0] + self.groundTileInfo[0][2], self.groundTileInfo[0][2] * 3):
            pg.draw.line(self.BG_SURFACE, (100, 100, 100), (x, 0), (x, self.MAP_SIZE[1]), width=5)

        for y in range(0, self.MAP_SIZE[1] + self.groundTileInfo[0][3], self.groundTileInfo[0][3] * 3):
            pg.draw.line(self.BG_SURFACE, (100, 100, 100), (0, y), (self.MAP_SIZE[0], y), width=5)

        for x in range(0, self.MAP_SIZE[0], self.groundTileInfo[0][2] * 2):
            for y in range(0, self.MAP_SIZE[1], self.groundTileInfo[0][3] * 2):
                if self.groundTileInfo[0][2] < x < self.MAP_SIZE[0] - self.groundTileInfo[0][2] and \
                        self.groundTileInfo[0][3] < y < \
                        self.MAP_SIZE[1] - self.groundTileInfo[0][3]:
                    if rdint(1, 8) <= 2:
                        pos = (x, y)

                        sector = (int(pos[0] / self.GSTEP[0]), int(pos[1] / self.GSTEP[1]))
                        self.crates.append(Crate(GAME_SURFACE, self.ENTITY_SURF, (1, 1), pos, sector,
                                                 self.crateTile, self.crateTileInfo))

        self.weapons = [
            GROUND_WEAPON_ID("M1911", resizeImage("Assets/game/guns/M1911_side.png", 0.05)[0]),
            GROUND_WEAPON_ID("Revolver", resizeImage("Assets/game/guns/Revolver_side.png", 0.05)[0]),
            GROUND_WEAPON_ID("AWP", resizeImage("Assets/game/guns/AWP_side.png", 0.10)[0])
        ]

        self.groundWeapons = []

        self.grid = self.genGrid(loadFunc)
        self.gridPosUpdates = []

    def genGrid(self, load):
        class gridSpot:
            __slots__ = "pos", "f", "h", "g", "neighbors", "previous", "wall"

            def __init__(self, pos: tuple, f: float, h: float, g: float, neighbors: list, previous: object, wall: bool):
                self.pos = pos
                self.f = f
                self.h = h
                self.g = g
                self.neighbors = neighbors
                self.previous = previous
                self.wall = wall

        cols = round(self.MAP_SIZE[0] / (self.GSTEP[0]))
        rows = round(self.MAP_SIZE[1] / (self.GSTEP[1]))

        grid = list(range(cols))

        numberOfColsIter = 100 / cols / 100

        dotDotDotCounter = 1
        animationDelay = time()

        for i in grid:
            grid[i] = list(range(rows))

        for i in range(cols):
            load((i + 1) * numberOfColsIter,
                 f"Loading Map{''.join(['.' for _ in range(dotDotDotCounter)])}")

            if time() - animationDelay > 0.5:
                dotDotDotCounter += 1

                if dotDotDotCounter > 3:
                    dotDotDotCounter = 0

                animationDelay = time()

            for j in range(rows):
                wall = False
                rect = pg.Rect(i * self.GSTEP[0], j * self.GSTEP[1], *self.GSTEP)

                for crate in self.crates:
                    crateRect = pg.Rect(crate.getGR())

                    if rect.colliderect(crateRect):
                        wall = True
                        break

                grid[i][j] = gridSpot((i, j), 0, 0, 0, [], None, wall)

        for i in range(cols):
            for j in range(rows):
                try:
                    if i < cols - 1:
                        grid[i][j].neighbors.append(grid[i + 1][j].pos)
                except IndexError:
                    pass

                try:
                    if i > 0:
                        grid[i][j].neighbors.append(grid[i - 1][j].pos)
                except IndexError:
                    pass

                try:
                    if j < rows - 1:
                        grid[i][j].neighbors.append(grid[i][j + 1].pos)
                except IndexError:
                    pass

                try:
                    if j > 0:
                        grid[i][j].neighbors.append(grid[i][j - 1].pos)
                except IndexError:
                    pass
                try:
                    if i > 0 and j > 0:
                        grid[i][j].neighbors.append(grid[i - 1][j - 1].pos)
                except IndexError:
                    pass

                try:
                    if i < cols - 1 and j > 0:
                        grid[i][j].neighbors.append(grid[i + 1][j - 1].pos)
                except IndexError:
                    pass

                try:
                    if i > 0 and j < rows - 1:
                        grid[i][j].neighbors.append(grid[i - 1][j + 1].pos)
                except IndexError:
                    pass

                try:
                    if i < cols - 1 and j < rows - 1:
                        grid[i][j].neighbors.append(grid[i + 1][j + 1].pos)
                except IndexError:
                    pass

        return grid

    def setup_map(self, ground_tile: list, crate_pos: tuple):
        self.BG_SURFACE.fill(self.BG_SURFACE.get_colorkey())
        self.crates.clear()

        rows = 40
        cols = 40

        x_ind = 0
        y_ind = 0

        for x in range(0, self.MAP_SIZE[0], self.groundTileInfo[0][2]):
            if x_ind >= rows:
                x_ind = 0

            for y in range(0, self.MAP_SIZE[1], self.groundTileInfo[0][3]):
                if y_ind >= cols:
                    y_ind = 0

                self.BG_SURFACE.blit(self.groundTile, (x, y), pg.Rect(rdChoice(self.groundTileInfo)))

                self.BG_SURFACE.blit(self.groundTile, (x, y),
                                     pg.Rect(self.groundTileInfo[ground_tile[x_ind][y_ind]]))

                y_ind += 1
            x_ind += 1

        for pos in crate_pos:
            pos = pos[0] * self.GSTEP[0], pos[1] * self.GSTEP[1]
            sector = (int(pos[0] / self.GSTEP[0]), int(pos[1] / self.GSTEP[1]))
            self.crates.append(Crate(self.GAME_SURFACE, self.ENTITY_SURF, (1, 1), pos, sector,
                                     self.crateTile, self.crateTileInfo))

    def update(self, displacement):
        self.displacement = displacement

        self.drawBG()
        self.clearBulletRenders()
        self.clearWeaponRenders()
        self.drawEntities()

    def drawAfterUpdate(self):
        self.drawBullets()
        self.drawWeapons()

    def drawBG(self):
        self.GAME_SURFACE.blit(self.BG_SURFACE, (0, 0),
                               Rect(self.displacement[0] * -1, self.displacement[1] * -1, self.GAME_SURFACE_DIMS[0],
                                    self.GAME_SURFACE_DIMS[1]))

    def drawEntities(self):
        for crate in self.crates:
            crate.update(self.displacement)

        self.GAME_SURFACE.blit(self.ENTITY_SURF, (0, 0),
                               Rect(self.displacement[0] * -1, self.displacement[1] * -1, self.GAME_SURFACE_DIMS[0],
                                    self.GAME_SURFACE_DIMS[1]))

        self.GAME_SURFACE.blit(self.GROUND_WEAPON_SURF, (0, 0),
                               Rect(self.displacement[0] * -1, self.displacement[1] * -1, self.GAME_SURFACE_DIMS[0],
                                    self.GAME_SURFACE_DIMS[1]))

    def clearBulletRenders(self):
        rect(self.BULLET_SURF, self.BULLET_SURF.get_colorkey(),
             Rect(-self.displacement[0], -self.displacement[1], *self.GAME_SURFACE_DIMS))

    def drawBullets(self):
        self.GAME_SURFACE.blit(self.BULLET_SURF, (0, 0),
                               Rect(self.displacement[0] * -1, self.displacement[1] * -1, self.GAME_SURFACE_DIMS[0],
                                    self.GAME_SURFACE_DIMS[1]))

    def clearWeaponRenders(self):
        rect(self.WEAPON_SURF, self.WEAPON_SURF.get_colorkey(),
             Rect(-self.displacement[0], -self.displacement[1], *self.GAME_SURFACE_DIMS))

    def drawWeapons(self):
        self.GAME_SURFACE.blit(self.WEAPON_SURF, (0, 0),
                               Rect(self.displacement[0] * -1, self.displacement[1] * -1, self.GAME_SURFACE_DIMS[0],
                                    self.GAME_SURFACE_DIMS[1]))

    def updateGroundWeapons(self):
        for i, weapon in sorted(enumerate(self.groundWeapons), reverse=True):
            if weapon.pickedUp:
                pg.draw.rect(self.GROUND_WEAPON_SURF, self.GROUND_WEAPON_SURF.get_colorkey(), weapon.rect)
                self.groundWeapons.pop(i)

            else:
                if not weapon.blitted:
                    self.GROUND_WEAPON_SURF.blit(weapon.img, weapon.pos)
                    weapon.blitted = True
                else:
                    continue

    def spawnWeapon(self, pos: tuple, sector: tuple, weaponName="", clip=None, ammo=None, passed_as_main=False):
        idx = None

        if weaponName == "M1911":
            idx = 0
        elif weaponName == "Revolver":
            idx = 1
        elif weaponName == "AWP":
            idx = 2

        if idx is not None:
            weaponChoice = self.weapons[idx]
        else:
            weaponChoice = rdChoice(self.weapons)

        attainable = True
        if (clip and ammo) is not None:
            if clip == 0 and ammo == 0:
                attainable = False

        weaponSize = weaponChoice.img.get_size()
        weaponRect = pg.Rect(pos[0] - weaponSize[0] / 2, pos[1] - weaponSize[1] / 2, weaponSize[0] * 2,
                             weaponSize[1] * 2)

        GW = GROUND_WEAPON(weaponName if weaponName != "" else weaponChoice.name, pos, sector, weaponRect,
                           weaponChoice.img, clip, ammo, False, False, attainable)

        if not passed_as_main:
            self.game.weapons_spawned.append({
                "pos": pos,
                "sector": sector,
                "weapon_name": weaponName if weaponName != "" else weaponChoice.name,
                "clip": clip,
                "ammo": ammo
            })

        self.groundWeapons.append(GW)
        self.updateGroundWeapons()

    def checkEntityOutOfMap(self, pos, r):
        # Collision top, left, bottom, right. (W, A, S, D)
        checks = [False for _ in range(4)]

        if pos[1] - r <= 0:
            checks[0] = True

        if pos[0] - r <= 0:
            checks[1] = True

        if pos[1] + r >= self.MAP_SIZE[1]:
            checks[2] = True

        if pos[0] + r >= self.MAP_SIZE[0]:
            checks[3] = True

        return tuple(checks)

    def checkEntityCrateCollision(self, pos: tuple, sector: tuple, r):
        sectors = getBoundingSectors(sector)

        collision = [False for _ in range(4)]
        points = tuple((pos[0] + r * cos(angle), pos[1] - r * sin(angle)) for angle in specialAngles)
        pointsCollided = [False for _ in range(len(points))]
        collidedObj = None

        for crate in self.crates:
            if crate.sector not in sectors:
                continue
            crateRect = pg.Rect(crate.getGR())

            pointsCollided = tuple(crateRect.collidepoint(point) for point in points)

            # Top collision
            if pointsCollided[12]:
                collision[2] = True

            elif True in pointsCollided[1:4]:
                collision[0] = True
                collision[3] = True

            elif True in pointsCollided[5:8]:
                collision[0] = True
                collision[1] = True

            # Left collision
            if pointsCollided[8]:
                collision[1] = True

            # Bottom collision
            if pointsCollided[4]:
                collision[0] = True

            elif True in pointsCollided[9:12]:
                collision[2] = True
                collision[1] = True

            elif True in pointsCollided[13:17]:
                collision[2] = True
                collision[3] = True

            # Right collision
            if pointsCollided[0]:
                collision[3] = True

            if True in collision:
                collidedObj = crate
                break

        return collision, pointsCollided, points, collidedObj
        # return collision, [False], None, None

    def checkContactCrateCollision(self, pos: tuple, sector: tuple, r, dmg, onePoint=False):
        # Center, left, top, right, bottom, TL, TR, BL, BR
        sectors = getBoundingSectors(sector)

        if onePoint:
            points = [(pos[0], pos[1])]
        else:
            points = [(pos[0] - r * cos(angle), pos[1] - r * sin(angle)) for angle in specialAngles[::4]]
            points.append((pos[0], pos[1]))

        for i, crate in sorted(enumerate(self.crates), reverse=True):
            if crate.sector not in sectors:
                continue

            if True in [crate.getGR().collidepoint(point) for point in points]:
                self.cratesInNeedOfUpdating.append(crate)
                crate.health -= dmg

                found = False
                found_with_idx = False
                ca_idx = -1
                for idx, crate_affected in enumerate(self.game.crates_affected):
                    if crate.sector == crate_affected["sector"]:
                        found = True

                        if crate.health != crate_affected["health"]:
                            found_with_idx = True
                            ca_idx = idx

                if not found:
                    self.game.crates_affected.append({
                        "sector": crate.sector,
                        "health": crate.health
                    })

                if found_with_idx:
                    self.game.crates_affected[ca_idx]["sector"] = crate.sector
                    self.game.crates_affected[ca_idx]["health"] = crate.health

                if crate.health <= 0:
                    self.remove_crate(crate, i)

                    self.gridPosUpdates.append(crate.getGrid())
                    self.spawnWeapon(crate.pos, crate.sector)
                    return 1

                return 2

    def remove_crate(self, crate, i: int):
        crate.deleteSelf()
        self.crates.pop(i)

    def checkEntityOverWeapon(self, pos: tuple, sector: tuple, r):
        # Center, left, top, right, bottom, TL, TR, BL, BR
        sectors = getBoundingSectors(sector)

        points = None
        rect = None

        if type(r) is not pg.Rect:
            points = tuple((pos[0] - r * cos(angle), pos[1] - r * sin(angle)) for angle in specialAngles)
        else:
            rect = r

        for weapon in self.groundWeapons:
            # if weapon.sector not in sectors:
            #     continue

            if points is not None:
                if True in [weapon.rect.collidepoint(point) for point in points]:
                    weapon.pickedUp = True

                    self.game.picked_up_weapons.append({
                        "pos": weapon.pos
                    })
                    self.updateGroundWeapons()
                    return weapon
                else:
                    continue
            elif rect is not None:
                if weapon.rect.colliderect(rect):
                    weapon.pickedUp = True

                    self.game.picked_up_weapons.append({
                        "pos": weapon.pos
                    })
                    self.updateGroundWeapons()
                    return weapon
                else:
                    continue
            else:
                return
