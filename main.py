import json, pickle
import os
import sys
from copy import deepcopy
from math import pi, sin, cos, atan2
from random import randint, choice as rdChoice
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR
from threading import Thread
from time import time
import asyncio
import base64
from cryptography.fernet import Fernet

import socket
from _thread import *

from pygame import draw, display, time as pyTime

from Scripts.button import *
from Scripts.text_field import TextField
from Scripts.extra_functions import specialAngles, getBoundingSectors, Upper_Lower_string, list_of_names

from Network.network import Network
import Network.server as server

import Scripts.game_objects as go


def compareDiDist(a: tuple, b: tuple, compareVal: tuple):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 <= (compareVal[0] + compareVal[1]) ** 2


def setEnemyGrid(entitiesList: list, enemiesList: list, cratesList: list, groundWeaponsList: list, grid):
    try:
        enemies = 100 / len(enemiesList) / 100
    except ZeroDivisionError:
        return

    dotDotDotCounter = 1
    animationDelay = time()

    for idx, enemy in enumerate(enemiesList):
        load((idx + 1) * enemies, f"Generating enemies{''.join(['.' for _ in range(dotDotDotCounter)])}")

        if time() - animationDelay > 0.5:
            dotDotDotCounter += 1

            if dotDotDotCounter > 3:
                dotDotDotCounter = 0

            animationDelay = time()

        enemy.grid = deepcopy(grid)

        enemy.crateList = cratesList
        enemy.enemiesList = entitiesList
        enemy.groundWeaponsList = groundWeaponsList

        entitiesList.append(enemy)


def load(status: float, msg: str = ""):
    go.loading = True

    ev = pg.event.poll()

    if ev.type == pg.QUIT:
        sys.exit()

    elif ev.type == pg.KEYDOWN:
        if ev.key == pg.K_ESCAPE:
            sys.exit()

    SCREEN.fill((0, 0, 0))

    draw.rect(SCREEN, (118, 215, 196), pg.Rect(100 * SFX, HEIGHT - 200 * SFY, (WIDTH - 200 * SFX) * status, 50 * SFY),
              border_radius=int(4 * SFX + 4 * SFY))
    draw.rect(SCREEN, (211, 84, 0), pg.Rect(100 * SFX, HEIGHT - 200 * SFY, (WIDTH - 200 * SFX), 50 * SFY),
              width=int(5 * SFX + 5 * SFY), border_radius=int(4 * SFX + 4 * SFY))

    loadingText = DEFAULT_FONT.render(f"Loading {round(status * 100, 2)}%", True, (215, 219, 221))
    loadingMsg = DEFAULT_FONT.render(msg, True, (255, 255, 255))

    blitText(SCREEN, loadingText, (100 * SFX, HEIGHT - 100 * SFY))
    blitText(SCREEN, loadingMsg, (100 * SFX, HEIGHT - 250 * SFY))

    display.flip()


class Game:
    def __init__(self, GAME_SURFACE: pg.Surface, GAME_SURFACE_DIMS: tuple, mode: str, player_color: tuple,
                 player_username):
        self.GAME_SURFACE = GAME_SURFACE
        self.GS_WIDTH, self.GS_HEIGHT = GAME_SURFACE_DIMS

        self.mode = mode

        self.continueBtn = Button(GAME_SURFACE, 100, self.GS_HEIGHT - 100, (200, 100), (86, 101, 115), "Continue!",
                                  BTN_SMALL_FONT, (255, 255, 255), alignX="l", alignY="b", btnRound=20)

        # offline variables
        self.numOfEnemies = 99
        self.enemies = None

        # online variables
        self.net = None

        # online & offline variables
        self.player = None
        self.gameMap = None
        self.entities = []
        self.bullets = []

        self.crates_affected = []
        self.weapons_spawned = []
        self.picked_up_weapons = []
        self.entities_hit = []
        self.upload_bullets = []

        self.taken_hits = []
        self.kills_attained = []

        """
            entities_hit example:
                entity_key: str(...),
                "dmg": float(...)
        """

        self.displacement = [randint(-3300, 600), randint(-3600, 300)]
        # self.displacement = [(self.GS_WIDTH / 2 - 2000),
        #                      (self.GS_HEIGHT / 2 - 2000)]
        self.spectating = None
        self.spectating_text = GAME_LARGE_FONT.render("Currently spectating.", True, (255, 255, 255))
        self.placementText = None

        self.match_complete = False

        self.username_font = pg.font.SysFont("calibre", 20, bold=True)

        if mode == "offline":
            self.setup_offline_game(player_color, player_username)
        else:
            self.setup_online_game(player_color, player_username)

        self.on_players_alive = 0
        self.players_alive_text = FPS_FONT.render(f"PLAYERS ALIVE: 0", True, (255, 255, 255))

    def setup_offline_game(self, player_color: tuple, player_username: str):
        from Scripts.enemy import Enemy
        from Scripts.game_map import GameMap
        from Scripts.player import Player

        # Variables for game state: game (2)
        self.gameMap = GameMap(self, self.GAME_SURFACE, load)
        go.GAME_MAP = self.gameMap

        self.player = Player(player_username, self.username_font.render(player_username, True, (255, 255, 255)), self.GAME_SURFACE, self.gameMap.WEAPON_SURF, self.gameMap.BULLET_SURF,
                             self.gameMap.MAP_SIZE, player_color,
                             (SFX, SFY),
                             self.displacement,
                             self.gameMap.GSTEP,
                             self.punchEntityCollision, self.bullets)

        # storm = Storm(GAME_SURFACE, gameMap.MAP_SIZE, player)

        self.entities = [self.player]

        self.enemies = [
            Enemy(self.username_font.render(rdChoice(list_of_names), True, (255, 255, 255)), self.GAME_SURFACE, self.gameMap.WEAPON_SURF, self.gameMap.BULLET_SURF, i + 1,
                  data["colors"][rdChoice(tuple(data["colors"].keys()))][randint(0, 8)]["rgb"],
                  self.gameMap.MAP_SIZE, self.gameMap.GSTEP,
                  (randint(100, self.gameMap.MAP_SIZE[0] - 100), randint(100, self.gameMap.MAP_SIZE[1] - 100)), (
                      self.gameMap.checkEntityCrateCollision, self.gameMap.checkContactCrateCollision,
                      self.punchEntityCollision,
                      self.gameMap.checkEntityOverWeapon, self.gameMap.spawnWeapon), self.bullets)
            for i in range(self.numOfEnemies)]

        enemyGrid = Thread(target=setEnemyGrid,
                           args=(self.entities, self.enemies, self.gameMap.crates, self.gameMap.groundWeapons,
                                 self.gameMap.grid))

        enemyGrid.start()
        enemyGrid.join()

        for enemy in self.enemies:
            enemy.findNearestCrate()

    def setup_online_game(self, player_color: tuple, player_username: pg.Surface):
        from Scripts.game_map import GameMap
        from Scripts.player import Player

        # self.player = pass
        self.gameMap = GameMap(self, self.GAME_SURFACE, load)
        self.net = Network(Upper_Lower_string(9))

        game_info = self.net.on_connect_data["map_info"]

        print("Game Info: ", game_info)
        # print(game_info["ground_tile"])
        self.gameMap.setup_map(game_info["ground_tile"], game_info["crate_pos"])
        go.GAME_MAP = self.gameMap

        self.player = Player(player_username, self.username_font.render(player_username, True, (255, 255, 255)), self.GAME_SURFACE, self.gameMap.WEAPON_SURF, self.gameMap.BULLET_SURF,
                             self.gameMap.MAP_SIZE, player_color,
                             (SFX, SFY),
                             self.displacement,
                             self.gameMap.GSTEP,
                             self.punchEntityCollision, self.bullets)

        # if self.net.on_connect_data["server_data"]["status"] == "play":
        #     self.player.alive = False
        #     self.spectating_text = GAME_LARGE_FONT.render("Joined ongoing match. Currently spectating.", True,
        #                                                   (255, 255, 255))

        defaultSurface = pg.Surface((10, 10))
        defaultSurface.set_colorkey((132, 132, 132))
        defaultSurface.fill(defaultSurface.get_colorkey())

        # M1911 images
        M1911_IMAGE_TOP = pg.image.load("assets/game/guns/M1911_top.png").convert()
        M1911_IMAGE_TOP = pg.transform.scale(M1911_IMAGE_TOP, (round(M1911_IMAGE_TOP.get_size()[0] / 11.25),
                                                               round(M1911_IMAGE_TOP.get_size()[1] / 11.25)))

        M1911_IMAGE_TOP_SIZE = M1911_IMAGE_TOP.get_size()

        self.M1911_SURFACE = pg.transform.scale(defaultSurface, M1911_IMAGE_TOP_SIZE)
        self.M1911_SURFACE.blit(M1911_IMAGE_TOP, (0, 0))

        # Revolver images
        REVOLVER_IMAGE_TOP = pg.image.load("assets/game/guns/revolver_top.png").convert()
        REVOLVER_IMAGE_TOP = pg.transform.scale(REVOLVER_IMAGE_TOP, (round(REVOLVER_IMAGE_TOP.get_size()[0] / 6.75),
                                                                     round(REVOLVER_IMAGE_TOP.get_size()[1] / 11.25)))
        REVOLVER_IMAGE_TOP_SIZE = REVOLVER_IMAGE_TOP.get_size()

        self.Revolver_SURFACE = pg.transform.scale(defaultSurface, REVOLVER_IMAGE_TOP_SIZE)
        self.Revolver_SURFACE.blit(REVOLVER_IMAGE_TOP, (0, 0))

        # AWP images
        AWP_IMAGE_TOP = pg.image.load("assets/game/guns/AWP_top.png").convert()
        AWP_IMAGE_TOP = pg.transform.scale(AWP_IMAGE_TOP,
                                           (round(AWP_IMAGE_TOP.get_size()[0] / 3.375),
                                            round(AWP_IMAGE_TOP.get_size()[1] / 6.75)))

        AWP_IMAGE_TOP_SIZE = AWP_IMAGE_TOP.get_size()

        self.AWP_SURFACE = pg.transform.scale(defaultSurface, AWP_IMAGE_TOP_SIZE)
        self.AWP_SURFACE.blit(AWP_IMAGE_TOP, (0, 0))

    def punchEntityCollision(self, pos: tuple, r: int, puncher: object):
        if self.mode == "offline":
            self.s_punchEntityCollision(pos, r, puncher)
        elif self.mode == "online":
            self.o_punchEntityCollision(pos, r, puncher)

    def s_punchEntityCollision(self, pos: tuple, r: int, puncher: object):
        points = tuple((pos[0] - r * cos(angle), pos[1] - r * sin(angle)) for angle in specialAngles[::4])
        puncherSectors = getBoundingSectors(puncher.sector)
        collided = False

        for idx, entity in enumerate(self.entities):
            if type(entity) is dict:
                return
            if entity is puncher or entity.sector not in puncherSectors:
                continue

            for point in points:
                if compareDiDist(point, entity.getMap(), (r, entity.body.r)):
                    entity.health -= 15
                    entity.healthRegenerateTime = time()

                    if idx != 0:
                        entity.enemyTarget = puncher
                        entity.priority = 3
                        entity.healthRegenerateTime = time()

                        puncher.priority = 3
                        puncher.enemyTarget = entity

                    collided = True

            if collided:
                break

    def o_punchEntityCollision(self, pos: tuple, r: int, puncher: object):
        points = tuple((pos[0] - r * cos(angle), pos[1] - r * sin(angle)) for angle in specialAngles[::4])
        puncherSectors = getBoundingSectors(puncher.sector)
        collided = False

        for entity in self.entities:
            key = tuple(entity.keys())[0]
            entity_data = entity[key]["player"]

            if tuple(entity_data["sector"]) not in puncherSectors or key == self.net.user_id:
                continue

            for point in points:
                if compareDiDist(point, entity_data["pos"], (r, entity_data["body_r"])):
                    self.entities_hit.append({
                        key: {
                            "pos": pos,
                            "dmg": 15,
                            "regenerate_timer": time(),
                            "sender": self.net.user_id,
                            "received": True
                        }
                    })

                    collided = True
                    break

            if collided:
                break

    def bulletEntityColl(self, pos: tuple, bulletSector: tuple, r: int, dmg: float, shooter: object):
        if self.mode == "offline":
            return self.s_bulletEntityColl(pos, bulletSector, r, dmg, shooter)
        elif self.mode == "online":
            return self.o_bulletEntityColl(pos, bulletSector, r, dmg)

    def s_bulletEntityColl(self, pos: tuple, bulletSector: tuple, r: int, dmg: float, shooter: object):
        collided = False
        bulletSectors = getBoundingSectors(bulletSector)

        for idx, entity in enumerate(self.entities):
            if entity.sector not in bulletSectors or shooter is entity:
                continue

            if compareDiDist(pos, entity.getMap(), (r, entity.body.r)):
                entity.health -= dmg
                entity.healthRegenerateTime = time()

                if idx > 0:
                    shooterAlive = shooter in self.entities

                    if shooterAlive:
                        if entity.enemyTarget:
                            # if entity.getDist(entity.getMap(),
                            #                   entity.enemyTarget.getMap()) > entity.getDist(
                            #     entity.getMap(), shooter.getMap()):
                            entity.enemyTarget = shooter
                        else:
                            entity.enemyTarget = shooter

                        entity.priority = 3

                        shooter.priority = 3
                        shooter.enemyTarget = entity

                collided = True
                return collided

            return collided

    def o_bulletEntityColl(self, pos: tuple, bulletSector: tuple, r: int, dmg: float):
        collided = False
        bulletSectors = getBoundingSectors(bulletSector)

        for entity in self.entities:
            key = tuple(entity.keys())[0]

            if key == self.net.user_id:
                continue

            entity_data = entity[key]["player"]

            entity_pos = entity_data["pos"][0] + self.displacement[0], entity_data["pos"][1] + self.displacement[1]
            entity_pos = entity_data["pos"]

            if tuple(entity_data["sector"]) not in bulletSectors:
                continue

            if compareDiDist(pos, entity_pos, (r, entity_data["body_r"])):
                self.entities_hit.append({
                    key: {
                        "pos": pos,
                        "dmg": dmg,
                        "regenerate_timer": time(),
                        "sender": self.net.user_id,
                        "received": False
                    }
                })

                collided = True
                return collided

            return collided

    def update(self, ev, dt: float):
        if self.mode == "offline":
            self.update_offline(ev, dt)
        elif self.mode == "online":
            asyncio.run(self.update_online(ev, dt))

        if self.match_complete:
            return True, self.placementText

    def update_offline(self, ev, dt: float):
        rect(self.GAME_SURFACE, (0, 0, 0), (0, 0, self.GS_WIDTH, self.GS_HEIGHT))
        self.gameMap.update(self.displacement)

        for i, bullet in sorted(enumerate(self.bullets), reverse=True):
            bullet.update(self.displacement, dt, (self.GS_WIDTH, self.GS_HEIGHT))

            pos = bullet.getMap()
            sector = bullet.getGrid()

            remove = False

            if bullet.dmg <= 0:
                if bullet.r <= 0:
                    remove = True
                else:
                    bullet.r -= dt

            elif sector[0] in self.gameMap.sectorHoriEdges or sector[1] in self.gameMap.sectorVertEdges:
                if bullet.checkBoundary():
                    remove = True

            elif self.gameMap.checkContactCrateCollision(pos, sector, bullet.r, bullet.dmg, True):
                remove = True

            elif self.bulletEntityColl(pos, sector, bullet.r, bullet.dmg, bullet.shooter):
                remove = True

            if remove:
                self.bullets.pop(i)

        for enemy in self.enemies:
            enemy.update(self.displacement, dt)

        if self.player.alive:
            newDisplacement = self.player.update(dt)
        else:
            if self.player in self.entities and len(self.entities) > 1:
                self.placementText = GAME_LARGE_FONT.render(f"You placed #{len(self.entities)}", True, (255, 255, 255))
                self.entities.pop(0)

                newDisplacement = (0, 0)
            elif len(self.enemies):
                if self.spectating is None or self.spectating not in self.enemies:
                    self.spectating = rdChoice(self.enemies)

                newDisplacement = (
                    self.GS_WIDTH / 2 - self.spectating.getMap()[0], self.GS_HEIGHT / 2 - self.spectating.getMap()[1])

        self.gameMap.drawAfterUpdate()

        for i, enemy in sorted(enumerate(self.enemies), reverse=True):
            enemy.draw()

            if enemy.alive is False:
                enemy.dropLoot()
                self.entities.remove(enemy)
                self.enemies.pop(i)

        self.player.draw()

        for enemy in self.enemies:
            if enemy.checkInCameraView(self.displacement):
                enemy.render_username()

        if self.player.alive:
            self.player.displayUI()
            pass
        else:
            if self.continueBtn.update(ev) or len(self.entities) <= 0:
                self.match_complete = True

            spectatingText = GAME_LARGE_FONT.render("Currently spectating", True, (255, 255, 255))
            blitText(self.GAME_SURFACE, spectatingText, (self.GS_WIDTH / 2 - spectatingText.get_width() / 2, 10))

        if len(self.entities) == 1:
            if not self.entities[0].alive:
                if self.entities[0] is self.player:
                    self.placementText = GAME_LARGE_FONT.render("You placed #1", True, (255, 255, 255))

                self.match_complete = True
                return

            self.entities[0].forceStop = True

        # After all game entities have been rendered
        if len(self.gameMap.gridPosUpdates):
            for enemy in self.enemies:
                for pos in self.gameMap.gridPosUpdates:
                    enemy.grid[pos[0]][pos[1]].wall = False

            self.gameMap.gridPosUpdates.clear()

        PLAYERS_ALIVE_TEXT = GAME_INFO_FONT.render(f"Players Remaining {len(self.entities)}", True, (255, 255, 255))

        blitText(self.GAME_SURFACE, PLAYERS_ALIVE_TEXT, (self.GS_WIDTH - PLAYERS_ALIVE_TEXT.get_width() - 10, 10))

        self.displacement = newDisplacement

    def reset_uploads(self):
        self.crates_affected.clear()
        self.weapons_spawned.clear()
        self.picked_up_weapons.clear()
        self.upload_bullets.clear()
        self.entities_hit.clear()
        self.taken_hits.clear()
        self.kills_attained.clear()
        self.player.shooter = None

    async def update_online(self, ev, dt: float):
        data_send = {
            self.net.user_id: {
                "player": self.player.get_data_send_info(),
                "upload_updates": {
                    "crates_affected": self.crates_affected,
                    "spawned_weapons": self.weapons_spawned,
                    "picked_up_weapons": self.picked_up_weapons,
                    "bullets": self.upload_bullets,
                    "entities_hit": self.entities_hit,
                    "is_alive": self.player.alive,
                    "taken_hits": self.taken_hits,
                    "kills_attained": self.kills_attained
                }
            },
            "index": self.net.id,
        }
        data_dump = json.dumps(data_send)

        self.entities, ping = await parse_data(self.net.send(data_dump))
        self.reset_uploads()

        ping_text = FPS_FONT.render(f"PING: {str(round(ping * 1000))}", True, (255, 255, 255))

        index = 0
        for idx, entity in enumerate(self.entities):
            key = tuple(entity.keys())[0]

            if key == self.net.user_id:
                index = entity["index"]
                break

        self.net.id = index

        server_data = self.entities[index]["server_data"]
        num_of_players_alive = self.entities[index]["updates"]["players_alive"]
        player_ids = self.entities[index]["updates"]["player_ids"]

        if self.on_players_alive != num_of_players_alive:
            self.on_players_alive = num_of_players_alive

            self.players_alive_text = FPS_FONT.render(f"PLAYERS ALIVE: {num_of_players_alive}", True,
                                                      (255, 255, 255))

        if server_data["status"] == "pre_game_lobby":
            can_play = False
            players_needed = server_data['players_needed_to_start'] - server_data['player_count']

            server_info_text = GAME_LARGE_FONT.render(
                f"{server_data['player_count']} player connected! Waiting for "
                f"{players_needed} more to start...",
                True, (255, 255, 255))
        elif server_data["status"] == "match_init":
            can_play = False
            server_info_text = GAME_LARGE_FONT.render(f"Match is starting in {server_data['time_till_start']} seconds!",
                                                      True, (255, 255, 255))
        else:
            can_play = True
            server_info_text = None

        rect(self.GAME_SURFACE, (0, 0, 0), (0, 0, self.GS_WIDTH, self.GS_HEIGHT))

        self.gameMap.update(self.displacement)

        # Check if player has been hit with bullet
        for hit in self.entities[index]["updates"]["entities_hit"]:
            key = tuple(hit.keys())[0]

            if key == self.net.user_id:
                # if hit in self.taken_hits:
                #     continue
                hit["revived"] = True
                self.taken_hits.append(hit)

                self.taken_hits.append(hit)
                self.player.health -= hit[key]["dmg"]
                self.player.healthRegenerateTime = hit[key]["regenerate_timer"]
                self.player.shooter = hit[key]["sender"]

            if self.player.health <= 0:
                self.placementText = GAME_LARGE_FONT.render(f"You placed #{len(self.entities)}", True,
                                                            (255, 255, 255))

        # for kill in self.entities[index]["updates"]["kills"]:
        #     if kill["sender"] == self.net.user_id:
        #         self.player.kills += 1
        #         self.kills_attained.append(kill)

        for i, bullet in sorted(enumerate(self.bullets), reverse=True):
            bullet.update(self.displacement, dt, (self.GS_WIDTH, self.GS_HEIGHT), render=False)

            pos = bullet.getMap()
            sector = bullet.getGrid()

            remove = False

            if bullet.dmg <= 0:
                if bullet.r <= 0:
                    remove = True
                else:
                    bullet.r -= dt

            if sector[0] in self.gameMap.sectorHoriEdges or sector[1] in self.gameMap.sectorVertEdges:
                if bullet.checkBoundary():
                    remove = True

            if self.gameMap.checkContactCrateCollision(pos, sector, bullet.r, bullet.dmg, True):
                remove = True

            if self.bulletEntityColl(pos, sector, bullet.r, bullet.dmg, bullet.shooter):
                remove = True

            if remove:
                self.bullets.pop(i)
            else:
                self.upload_bullets.append(bullet.get_data())

        for bullet in self.entities[index]["updates"]["bullets"]:
            self.draw_online_bullet(bullet)

        if self.player.alive:
            self.displacement = self.player.update(dt, can_play)

        for player_data in self.entities:
            keys = tuple(player_data.keys())

            player_key = keys[0]

            if type(player_data) is not dict or player_key == self.net.user_id or not player_data[player_key]["player"][
                "is_alive"]:
                continue

            if player_data[player_key]["player"]["weapon_surface"] is not None:
                self.draw_online_player_weapon(player_data[player_key]["player"])

        self.gameMap.drawAfterUpdate()

        for idx, player_data in enumerate(self.entities):
            if type(player_data) is not dict:
                continue

            keys = tuple(player_data.keys())

            player_key = keys[0]

            player = player_data[player_key]

            if player_key == self.net.user_id:
                updates = player_data["updates"]

                for ac in updates["crates_affected"]:
                    for crate_idx, crate in sorted(enumerate(self.gameMap.crates), reverse=True):
                        if ac["sector"][0] == crate.sector[0] and ac["sector"][1] == crate.sector[1]:
                            crate.health = ac["health"]

                            if crate.health <= 0:
                                self.gameMap.remove_crate(crate, crate_idx)

                for sw in updates["spawned_weapons"]:
                    found = False
                    for weapon in self.gameMap.groundWeapons:
                        if sw["sector"][0] == weapon.sector[0] and sw["sector"][1] == weapon.sector[1]:
                            found = True

                    if not found:
                        self.gameMap.spawnWeapon(sw["pos"], sw["sector"], sw["weapon_name"], sw["clip"], sw["ammo"],
                                                 True)

                for pw in updates["picked_up_weapons"]:
                    for weapon in self.gameMap.groundWeapons:
                        if int(pw["pos"][0]) == int(weapon.pos[0]) and int(pw["pos"][1]) == int(weapon.pos[1]):
                            weapon.pickedUp = True

                if len(updates["picked_up_weapons"]):
                    self.gameMap.updateGroundWeapons()
                continue

            player_draw_data = player["player"]
            if not player_draw_data["is_alive"]:
                continue

            if len(player_draw_data["left_hand"]):
                self.draw_online_player(player["player"])

        self.player.draw()

        if self.player.alive:
            self.player.displayUI()
        else:
            self.GAME_SURFACE.blit(self.spectating_text, (self.GS_WIDTH / 2 - self.spectating_text.get_width() / 2, 10))
            if self.continueBtn.update(ev) or len(self.entities) <= 0:
                self.match_complete = True
                self.net.disconnect()

        if server_info_text:
            self.GAME_SURFACE.blit(server_info_text, (self.GS_WIDTH / 2 - server_info_text.get_width() / 2, 10))

        if num_of_players_alive <= 1 and server_data["status"] == "play":
            if self.player.alive:
                if self.player.body.r > 0:
                    self.player.playDeadAni()
                else:
                    self.placementText = GAME_LARGE_FONT.render("You placed #1", True, (255, 255, 255))
                    self.player.alive = False

        self.draw_player_ids(player_ids, server_data["status"])

        self.GAME_SURFACE.blit(ping_text, (self.GS_WIDTH - 10 - ping_text.get_width(), 10))
        self.GAME_SURFACE.blit(self.players_alive_text,
                               (self.GS_WIDTH - 10 - self.players_alive_text.get_width(), 20 + ping_text.get_height()))

    def draw_online_bullet(self, bullet_data):
        x, y = bullet_data["pos"]
        r = bullet_data["r"]

        circle(self.gameMap.BULLET_SURF, (245, 176, 65), (x, y), r)
        circle(self.gameMap.BULLET_SURF, (0, 0, 0), (x, y), r, width=int(r / 2))

    def draw_online_player_weapon(self, player_data: dict):
        weapon_name = player_data["weapon_surface"]["weapon_name"]

        if weapon_name == "M1911":
            SURFACE = self.M1911_SURFACE
        elif weapon_name == "Revolver":
            SURFACE = self.Revolver_SURFACE
        elif weapon_name == "AWP":
            SURFACE = self.AWP_SURFACE

        surf = pg.transform.rotate(SURFACE, player_data["weapon_surface"]["theta"] - 90).convert()

        wTop, hTop = surf.get_size()

        xOff = (player_data["body_r"] * 0.75 + hTop / 3) * cos(player_data["angle"])
        yOff = (player_data["body_r"] * 0.75 + hTop / 3) * sin(player_data["angle"])

        blit_pos = (player_data["pos"][0] - wTop / 2 + xOff, player_data["pos"][1] - hTop / 2 - yOff)

        self.gameMap.WEAPON_SURF.blit(surf, blit_pos)

    def draw_online_player(self, player_data: dict):
        pos = player_data["pos"][0] + self.displacement[0], player_data["pos"][1] + self.displacement[1]
        r = player_data["body_r"]

        if not (pos[0] + r > 0 and pos[0] - r < self.GS_WIDTH and pos[1] + r > 0 and pos[1] - r < self.GS_HEIGHT):
            return

        username_text = self.username_font.render(player_data["username"], True, (255, 255, 255))
        self.GAME_SURFACE.blit(username_text, (
            pos[0] - username_text.get_width() / 2, pos[1] - r * 2 - username_text.get_height()))

        left_hand_pos = player_data["left_hand"]["pos"][0] + self.displacement[0], player_data["left_hand"]["pos"][
            1] + self.displacement[1]

        right_hand_pos = player_data["right_hand"]["pos"][0] + self.displacement[0], player_data["right_hand"]["pos"][
            1] + self.displacement[1]

        circle(self.GAME_SURFACE, player_data["color"], (pos[0], pos[1]),
               r)
        circle(self.GAME_SURFACE, (0, 0, 0), (pos[0], pos[1]),
               r, width=3)

        circle(self.GAME_SURFACE, player_data["color"],
               (left_hand_pos[0], left_hand_pos[1]),
               player_data["left_hand"]["r"])
        circle(self.GAME_SURFACE, (0, 0, 0),
               (left_hand_pos[0], left_hand_pos[1]),
               player_data["left_hand"]["r"], width=2)

        circle(self.GAME_SURFACE, player_data["color"],
               (right_hand_pos[0], right_hand_pos[1]),
               player_data["right_hand"]["r"])
        circle(self.GAME_SURFACE, (0, 0, 0),
               (right_hand_pos[0], right_hand_pos[1]),
               player_data["right_hand"]["r"], width=2)

    def draw_player_ids(self, player_ids: list[dict], server_status: str):
        rendered_texts = []

        max_width = 0

        for p_id in player_ids:
            if server_status != "play":
                text = f"{p_id['name']} | ID: {p_id['user_id']}"
            else:
                text = f"{p_id['name']} | KILLS: {p_id['kills']}"

            color = (255, 255, 255) if p_id["user_id"] != self.net.user_id else (88, 214, 141)

            rd_text = DEFAULT_FONT.render(text, True, color)
            rendered_texts.append(rd_text)

            if rd_text.get_width() > max_width:
                max_width = rd_text.get_width()

        skip = 40
        height = skip * len(rendered_texts)
        width = max_width + 20

        bg_surf = pg.Surface((width, height))
        bg_surf.fill((0, 0, 0))
        bg_surf.set_alpha(150)

        self.GAME_SURFACE.blit(bg_surf, (0, 75))

        for idx, rd_text in enumerate(rendered_texts):
            self.GAME_SURFACE.blit(rd_text, (10, 75 + rd_text.get_height() / 2 + idx * skip))


def main():
    """
        Game states
        1: intro,
        2: game,
        3: online match
        4: game over,
        5: character adjustments,
        6: help screen
        7: settings (possibly)
    """
    currentColor = tuple(data["colors"][data["colorSelected"][0]][data["colorSelected"][1]]["rgb"])
    playerColor = currentColor

    gamestate = 1
    SCALE = (SFX, SFY)

    # Variables for game state: intro (1)
    toGameOffScreenBtn = Button(SCREEN, WIDTH / 2, HEIGHT - 20, (200, 100), (86, 101, 115), "Offline!",
                                BTN_LARGE_FONT, (255, 255, 255), alignX="c", alignY="b", btnRound=20)
    toGameOnScreenBtn = Button(SCREEN, WIDTH / 2, HEIGHT - 140, (200, 100), (86, 101, 115), "Online!",
                               BTN_LARGE_FONT, (255, 255, 255), alignX="c", alignY="b", btnRound=20)

    toHelpScreenBtn = Button(SCREEN, 200, HEIGHT - 100, (133, 66), (86, 101, 115), "Help!",
                             BTN_SMALL_FONT, (255, 255, 255), alignX="l", alignY="b", btnRound=10)

    toCustomizeScreenBtn = Button(SCREEN, WIDTH - 200, HEIGHT - 100, (133, 66), (86, 101, 115),
                                  "Customize!", BTN_SMALL_FONT, (255, 255, 255), alignX="r", alignY="b",
                                  btnRound=10)

    player_username = TextField(SCREEN, data["name"], DEFAULT_FONT, playerColor)

    # Variables for the game
    DEFAULT_SCREEN_SIZE = (1280, 720)
    # GAME_SURFACE = pg.Surface(DEFAULT_SCREEN_SIZE)
    GAME_SURFACE = SCREEN
    go.GAME_SURFACE = GAME_SURFACE

    game = None
    # Variables for game over screen
    toHomeScreenBtn = Button(SCREEN, WIDTH / 2, HEIGHT - 250 * SFY, (300 * SFX, 150 * SFY), (40, 116, 166), "Home",
                             BTN_LARGE_FONT, (255, 255, 255), alignX="c", alignY="b", btnRound=int(10 * SFX + 10 * SFY))

    quitBtn = Button(SCREEN, WIDTH / 2, HEIGHT - 50 * SFY, (300 * SFX, 150 * SFY), (231, 76, 60), "Quit",
                     BTN_LARGE_FONT, (255, 255, 255), alignX="c", alignY="b", btnRound=int(10 * SFX + 10 * SFY))

    placementText = None

    # Variables for costume screen
    customizeBuyBtn = Button(SCREEN, WIDTH - 75 * SFX, HEIGHT - 100 * SFY, (200 * SFX, 100 * SFY), (22, 160, 133),
                             "Buy",
                             BTN_SMALL_FONT, (255, 255, 255), alignX="r", alignY="b", btnRound=int(5 * SFX + 5 * SFY))

    customizeBackBtn = Button(SCREEN, 75 * SFX, HEIGHT - 100 * SFY, (200 * SFX, 100 * SFY), (86, 101, 115), "Back",
                              BTN_SMALL_FONT, (255, 255, 255), alignX="l", alignY="b", btnRound=int(5 * SFX + 5 * SFY))

    selected = None
    onColor = None

    # Variables for help screen
    helpHomeBtn = Button(SCREEN, 75 * SFX, HEIGHT - 100 * SFY, (200 * SFX, 100 * SFY), (86, 101, 115), "Home",
                         BTN_LARGE_FONT, (255, 255, 255), alignX="l", alignY="b", btnRound=int(5 * SFX + 5 * SFY))

    infoMsg = "You are on an island surrounded by dark abys,\nYour only goal is to kill. After all, that's the only way to survive.\nEquipped with nothing, you'll need to break crates to find weapons\nor if you're brave enough, you can punch your way to victory."
    infoMsgList = infoMsg.split("\n")
    renderedInfoText = [HELP_FONT.render(msg, True, (255, 255, 255)) for msg in infoMsgList]

    controlMsg = "WASD or Arrow Keys To Move\nF Key To Pick Up Weapons\nR Key To Reload\nMouse Button or Q Key To Punch/Shoot\n1, 2, 3 Num Keys To Switch Weapons (1 Is Always Fists)\nESC To Quit"
    controlMsgList = controlMsg.split("\n")
    renderedControlText = [DEFAULT_FONT.render(msg, True, (255, 255, 255)) for msg in controlMsgList]

    while 1:
        cursorPos = pg.mouse.get_pos()

        ev = pg.event.poll()
        FPS = clock.tick(ATTEMPTED_FPS)
        dt = (FPS * TARGETED_FPS) / 1000

        if go.loading:
            go.loading = False
            continue

        if (ev.type == pg.KEYDOWN and ev.key == pg.K_ESCAPE) or ev.type == pg.QUIT:
            if game is not None:
                if game.net is not None:
                    game.net.disconnect()

            sys.exit()

        if gamestate == 1:
            SCREEN.fill((44, 62, 80))

            if player_username.text != data["name"]:
                data["name"] = player_username.text
                updateData()

            # State change checks:
            if toGameOffScreenBtn.update(ev):
                game = Game(GAME_SURFACE, GAME_SURFACE.get_size(), "offline", playerColor, player_username.text)
                gamestate = 2
            elif toGameOnScreenBtn.update(ev):
                game = Game(GAME_SURFACE, GAME_SURFACE.get_size(), "online", playerColor, player_username.text)
                gamestate = 2

            elif toHelpScreenBtn.update(ev):
                gamestate = 6

            elif toCustomizeScreenBtn.update(ev):
                currentColor = None
                gamestate = 5

            player_username.update()
        elif gamestate == 2:
            match_complete = game.update(ev, dt)

            if match_complete:
                placementText = match_complete[1]
                gamestate = 4
            # SCREEN.blit(GAME_SURFACE, (0, 0))
            # SCREEN.blit(pg.transform.smoothscale(GAME_SURFACE, DEFAULT_SCREEN_SIZE), (0, 0))
            # pg.transform.scale(GAME_SURFACE, SIZE, SCREEN)
        elif gamestate == 4:
            SCREEN.fill((39, 55, 70))

            if toHomeScreenBtn.update(ev):
                gamestate = 1

            elif quitBtn.update(ev):
                sys.exit()

            blitText(SCREEN, placementText, (WIDTH / 2 - placementText.get_width() / 2, 50 * SFY))
        elif gamestate == 5:
            SCREEN.fill((44, 62, 80))
            mousePos = pg.mouse.get_pos()
            x, y = 200, HEIGHT / 2
            r = 100

            angle = atan2(mousePos[1] - y, mousePos[0] - x)

            pos1 = x + r * cos(angle - pi / 4), y + r * sin(angle - pi / 4)
            pos2 = x + r * cos(angle + pi / 4), y + r * sin(angle + pi / 4)

            coinsText = DEFAULT_FONT.render(f"Coins: ${data['coins']}", 1, (255, 255, 255))

            # Mock player
            circle(SCREEN, currentColor if currentColor else playerColor, (x, y), r)
            circle(SCREEN, (0, 0, 0), (x, y), r, width=6)

            circle(SCREEN, currentColor if currentColor else playerColor, pos1, 50)
            circle(SCREEN, (0, 0, 0), pos1, 50, width=6)

            circle(SCREEN, currentColor if currentColor else playerColor, pos2, 50)
            circle(SCREEN, (0, 0, 0), pos2, 50, width=6)

            if onColor is None:
                for idx, (key, val) in enumerate(data["colors"].items()):
                    if idx < 3:
                        x = 2 - idx
                        y = 0
                    elif idx < 6:
                        x = 5 - idx
                        y = 1
                    else:
                        x = 8 - idx
                        y = 2

                    bgSurf = pg.Surface((100, 100))
                    bgSurf.set_colorkey((0, 0, 0))
                    bgSurf.fill(bgSurf.get_colorkey())

                    posX = (WIDTH - 50) - (83 * x)
                    xyOffset = 50
                    posY = 200 + 83 * y

                    if (posX - mousePos[0]) ** 2 + (posY - mousePos[1]) ** 2 < xyOffset ** 2:
                        bgSurf.set_alpha(255)

                        if ev.type == pg.MOUSEBUTTONDOWN:
                            onColor = key
                    else:
                        bgSurf.set_alpha(150)

                    circle(bgSurf, tuple(val[4]["rgb"]), (bgSurf.get_width() / 2, bgSurf.get_height() / 2), 33)

                    SCREEN.blit(bgSurf, (posX - xyOffset, posY - xyOffset))
                    circle(SCREEN, (0, 0, 0), (posX, posY), 40, width=6)
            else:
                for idx, val in enumerate(data["colors"][onColor]):
                    if idx < 3:
                        x = 2 - idx
                        y = 0
                    elif idx < 6:
                        x = 5 - idx
                        y = 1
                    else:
                        x = 8 - idx
                        y = 2

                    bgSurf = pg.Surface((100, 100))
                    bgSurf.set_colorkey((0, 0, 0))
                    bgSurf.fill(bgSurf.get_colorkey())

                    posX = (WIDTH - 50) - (83 * x)
                    xyOffset = 50
                    posY = 200 + 83 * y

                    if (posX - mousePos[0]) ** 2 + (posY - mousePos[1]) ** 2 < xyOffset ** 2:
                        bgSurf.set_alpha(255)

                        if ev.type == pg.MOUSEBUTTONDOWN:
                            selected = idx

                            currentColor = tuple(data["colors"][onColor][selected]["rgb"])
                    else:
                        bgSurf.set_alpha(150)

                    circle(bgSurf, tuple(val["rgb"]), (bgSurf.get_width() / 2, bgSurf.get_height() / 2), 33)

                    SCREEN.blit(bgSurf, (posX - xyOffset, posY - xyOffset))
                    circle(SCREEN, (0, 0, 0), (posX, posY), 40, width=6)

            if onColor and selected is not None:
                color = data["colors"][onColor][selected]
                if color["unlocked"] is False:

                    if data["coins"] > color["price"]:
                        purchasable = True
                        msg = f"You do not own {str(onColor).capitalize()} {selected + 1}. Purchase? ${color['price']}"
                    else:
                        purchasable = False
                        msg = f"Not enough coins to purchase {str(onColor).capitalize()} {selected + 1}."

                    msg = DEFAULT_FONT.render(msg, True, (255, 255, 255))

                    blitText(SCREEN, msg, (WIDTH - msg.get_width() - 50, HEIGHT - 200))

                    if purchasable:
                        if customizeBuyBtn.update(ev):
                            color["unlocked"] = True
                            data["coins"] -= color["price"]
                            data["colorSelected"] = [onColor, selected]

                            updateData()

            if customizeBackBtn.update(ev):
                if onColor is None:
                    player_username.change_text_color(playerColor)
                    gamestate = 1

                elif selected is not None:
                    if data["colors"][onColor][selected]["unlocked"]:
                        currentColor = data["colors"][onColor][selected]["rgb"]
                        playerColor = currentColor
                        data["colorSelected"] = [onColor, selected]
                        updateData()

                    onColor = None
                    selected = None
                else:
                    onColor = None
                    selected = None

            blitText(SCREEN, coinsText, (WIDTH - coinsText.get_width() - 50, 50))
        elif gamestate == 6:
            SCREEN.fill((50, 50, 50))

            for i, text in enumerate(renderedInfoText):
                SCREEN.blit(text, (WIDTH / 2 - text.get_size()[0] / 2, (30 + 70 * i) * SFY))

                if text == renderedInfoText[-1]:
                    calc = HEIGHT / 2 - ((30 + 70 * i) / 2) * SFY + text.get_size()[1]
                    pg.draw.line(SCREEN, (200, 200, 200), (30 * SFX, calc), (WIDTH - 30 * SFX, calc),
                                 width=int(12.5 * SFX + 12.5 * SFY))

            for i, text in enumerate(renderedControlText):
                SCREEN.blit(text, (75 * SFX, HEIGHT / 2 + (50 * i) * SFY))

            if helpHomeBtn.update(ev):
                gamestate = 1
        else:
            print("Fatal Error: Invalid gamestate")
            sys.exit(1)

        FPS_TEXT = FPS_FONT.render(f"FPS: {round(clock.get_fps())}", True, (255, 255, 255))
        blitText(SCREEN, FPS_TEXT, (10 * SFX, 10 * SFX))

        circle(SCREEN, (255, 255, 255), cursorPos, 4)
        SCREEN.blit(CROSSHAIR, (cursorPos[0] - CROSSHAIR_BLIT_OFFSET[0], cursorPos[1] - CROSSHAIR_BLIT_OFFSET[1]))

        display.flip()


async def parse_data(d):
    try:
        data_received = json.loads(d[0])

        return data_received, d[1]
    except Exception as e:
        print("Data: ", d[0], d[1])
        print("Error: ", e)
        sys.exit()


def blitText(SURFACE: pg.Surface, renderedText, pos: "(x, y)"):
    SURFACE.blit(renderedText, pos)


def updateData():
    os.chmod(DATA_FILE_PATH, S_IWUSR | S_IREAD)

    with open(DATA_FILE_PATH, "w") as file:
        json.dump(data, file, separators=(",", ":"), indent=2)
        file.close()

    os.chmod(DATA_FILE_PATH, S_IREAD | S_IRGRP | S_IROTH)


if __name__ == '__main__':
    DATA_FILE_PATH = "./data/data.json"
    # fernet_key = Fernet.generate_key()
    # fernet_encrypt = Fernet(fernet_key)

    # Set global vars
    with open(DATA_FILE_PATH) as file:
        data = json.load(file)
        file.close()

    pg.init()
    # Screen Ratio 16:9

    # Set title and icon
    pg.display.set_caption("Dummy Royale")
    icon = pg.image.load("Resources/Icon/Dummy Royale Icon.ico")
    pg.display.set_icon(icon)

    # For testing
    SIZES = [(1400, 800), (1000, 300), (40, 20), (randint(100, 1920), randint(100, 1080)), (960, 540),
             (2000, 800), (1000, 1000), (2560, 1440), (round(1920 * 2 / 3), round(1080 * 2 / 3)), (1536, 864)]
    SIZE = (1280, 720)

    FLAGS = pg.DOUBLEBUF

    # Setup Vars
    # FLAGS = pg.FULLSCREEN | pg.DOUBLEBUF | pg.HWACCEL | pg.HWSURFACE
    # SIZE = display.list_modes()[0]

    SCREEN = display.set_mode(SIZE, FLAGS)

    WIDTH, HEIGHT = SCREEN.get_size()

    SFX, SFY = (WIDTH / 1920, HEIGHT / 1080)

    # Clock
    clock = pyTime.Clock()

    # Fonts
    DEFAULT_FONT = pg.font.SysFont("calibre", 30)

    GAME_INFO_FONT = pg.font.SysFont("calibre", 20, bold=True)
    GAME_LARGE_FONT = pg.font.SysFont("arial", 40, bold=True)

    BTN_SMALL_FONT = pg.font.SysFont("impact", 20)
    BTN_LARGE_FONT = pg.font.SysFont("pixel", 40)

    HELP_FONT = pg.font.SysFont("times", 26)

    FPS_FONT = pg.font.SysFont("calibre", 26)

    ATTEMPTED_FPS = 60
    TARGETED_FPS = 60

    pg.mouse.set_cursor((8, 8), (0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0))
    CROSSHAIR = pg.image.load("Assets/cursor/crosshair.png").convert_alpha()
    CROSSHAIR_BLIT_OFFSET = (CROSSHAIR.get_width() / 2, CROSSHAIR.get_height() / 2)

    go.LOAD_FUNC = load
    go.loading = False

    random_names = ("John", "Bob", "Ant", "Arnold", "Vector", "Shaun", "Shep", "Paul", "Bethe")

    # Call main loop
    main()
