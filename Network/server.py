import socket
from _thread import *
import sys
import json, pickle
import random
from time import time

from copy import deepcopy

from Scripts.game_map import GameMap
import Scripts.game_objects as go

number_of_clients = 0


def get_server_data():
    with open("./server_data.json") as read_data:
        return json.load(read_data)


def update_server_data(data: dict):
    with open("./server_data.json", "w") as write_data:
        json.dump(data, write_data, indent=2)


def reset_server_data(config):
    global server_data, crates_affected_pop_at, spawned_weapons_pop_at, picked_up_weapons_pop_at, bullets_pop_at, \
        entities_hit_pop_at

    players.clear()

    crates_affected.clear()
    crates_affected_pop_at = 0

    spawned_weapons.clear()
    spawned_weapons_pop_at = 0

    picked_up_weapons.clear()
    picked_up_weapons_pop_at = 0

    bullets.clear()
    bullets_pop_at = 0

    entities_hit.clear()
    entities_hit_pop_at = 0

    server_data = deepcopy(config)


def create_map():
    rows = 40
    cols = 40

    ground = list(range(rows))
    crates_pos = []

    for i in range(cols):
        ground[i] = list(range(40))

    for x in range(rows):
        for y in range(cols):
            ground[x][y] = random.randint(0, 1)

            if random.randint(1, 8) <= 2:
                crates_pos.append((x, y))

    return {
        "ground_tile": ground,
        "crate_pos": crates_pos
    }


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


if __name__ == "__main__":
    map_info = create_map()

    with open("./server_config.json") as server_config_file:
        server_config = json.load(server_config_file)
        server_config_file.close()

    match_start_time = time()

    players = []
    crates_affected = []
    crates_affected_pop_at = 0

    spawned_weapons = []
    spawned_weapons_pop_at = 0

    picked_up_weapons = []
    picked_up_weapons_pop_at = 0

    bullets = []
    bullets_pop_at = 0

    entities_hit = []
    entities_hit_pop_at = 0

    kills = []
    kills_pop_at = 0

    server_data = {}
    reset_server_data(server_config)
    update_server_data(server_data)

    looped = False

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # server = socket.gethostbyname(socket.gethostname())
    server = get_ip()
    port = 5555

    server_ip = socket.gethostbyname(server)
    print("Server IP: " + server_ip)

    try:
        s.bind((server, port))

    except socket.error as e:
        print(str(e))

    s.listen(server_data["max_players"])
    print("Waiting for a connection")


    def threaded_client(conn):
        global number_of_clients, looped, match_start_time, \
            crates_affected_pop_at, \
            spawned_weapons_pop_at, \
            picked_up_weapons_pop_at, \
            bullets_pop_at, \
            entities_hit_pop_at, \
            kills_pop_at

        user_id = conn.recv(2048).decode()
        players[-1] = {
            user_id: {
                "player": {
                    "username": "",
                    "color": (0, 0, 0),
                    "pos": (0, 0),
                    "sector": (0, 0),
                    "angle": 0,
                    "body_r": 0,
                    "left_hand": {
                        "r": 0,
                        "pos": (0, 0)
                    },
                    "right_hand": {
                        "r": 0,
                        "pos": (0, 0)
                    },
                    "weapon_surface": None,
                    "is_alive": True,
                    "kills": 0,
                    "shooter": None
                },
                "upload_updates": {
                    "crates_affected": [],
                    "spawned_weapons": [],
                    "picked_up_weapons": [],
                    "bullets": [],
                    "entities_hit": [],
                    "kills": 0,
                    "shooter": None,
                    "is_alive": True,
                    "kills_attained": []
                }
            },
            "updates": {
                "crates_affected": [],
                "spawned_weapons": [],
                "picked_up_weapons": []
            },
            "index": len(players) - 1
        }
        conn.send(str.encode(json.dumps({
            "map_info": map_info,
            "server_data": server_data
        })))

        server_data["player_count"] = len(players)
        update_server_data(server_data)

        if server_data["player_count"] == server_data["players_needed_to_start"]:
            server_data["status"] = "match_init"

        update_server_data(server_data)
        match_start_time = time()

        print(players)

        while True:
            index = 0

            try:
                data = conn.recv(10000)

                reply = json.loads(data)
                key_id = tuple(reply.keys())[0]

                counted = 0

                for player in players:
                    if tuple(player.keys())[0] == key_id:
                        index = counted
                        break

                    counted += 1

                if not data:
                    conn.send(str.encode("Goodbye"))
                    break
                else:
                    players_alive = 0
                    player_ids = []

                    for idx, player in enumerate(players):
                        keys = tuple(player.keys())
                        uploads = reply[key_id]["upload_updates"]
                        is_alive = player[keys[0]]["player"]["is_alive"]

                        if is_alive:
                            players_alive += 1
                            if server_data["status"] != "play":
                                player_ids.append({
                                    "name": player[keys[0]]["player"]["username"],
                                    "user_id": keys[0]
                                })
                            else:
                                player_ids.append({
                                    "name": player[keys[0]]["player"]["username"],
                                    "user_id": keys[0],
                                    "kills": player[keys[0]]["player"]["kills"]
                                })
                        else:
                            if player[keys[0]]["player"]["shooter"] is not None:
                                kills.append({
                                    "sender": player[keys[0]]["player"]["shooter"],
                                    "timestamp": time()
                                })

                        if keys[0] == key_id:
                            for t_hit in uploads["taken_hits"]:
                                t_hit_pos = t_hit[tuple(t_hit.keys())[0]]["pos"]
                                for e_hit_idx, e_hit in sorted(enumerate(entities_hit), reverse=True):
                                    e_hit_pos = e_hit[tuple(e_hit.keys())[0]]["pos"]
                                    if int(t_hit_pos[0]) == int(e_hit_pos[0]) and int(t_hit_pos[1]) == int(
                                            e_hit_pos[1]):
                                        entities_hit.pop(e_hit_idx)

                            # for ak in uploads["kills_attained"]:
                            #     for k_idx, kill in sorted(enumerate(kills), reverse=True):
                            #         if ak["timestamp"] == kill["timestamp"]:
                            #             kills.pop(k_idx)

                            if len(uploads["crates_affected"]):
                                for u_crate in uploads["crates_affected"]:
                                    found = False
                                    found_with_idx = False
                                    u_idx = -1

                                    for s_idx, s_crate in enumerate(crates_affected):

                                        if u_crate["sector"] == s_crate["sector"]:
                                            found = True

                                            if u_crate["health"] != s_crate["health"]:
                                                found_with_idx = True
                                                u_idx = s_idx

                                    if not found:
                                        crates_affected.append({
                                            "sector": u_crate["sector"],
                                            "health": u_crate["health"]
                                        })

                                    if found_with_idx:
                                        crates_affected[u_idx]["sector"] = u_crate["sector"]
                                        crates_affected[u_idx]["health"] = u_crate["health"]

                            if len(uploads["spawned_weapons"]):
                                for u_weapon in uploads["spawned_weapons"]:
                                    found = False

                                    for s_weapon in spawned_weapons:

                                        if u_weapon["sector"] == s_weapon["sector"]:
                                            found = True

                                    if not found:
                                        spawned_weapons.append({
                                            "pos": u_weapon["pos"],
                                            "sector": u_weapon["sector"],
                                            "weapon_name": u_weapon["weapon_name"],
                                            "clip": u_weapon["clip"],
                                            "ammo": u_weapon["ammo"]
                                        })

                            if len(uploads["picked_up_weapons"]):
                                for p_weapon in uploads["picked_up_weapons"]:
                                    picked_up_weapons.append(p_weapon)

                            bullets.extend(uploads["bullets"])
                            entities_hit.extend(uploads["entities_hit"])

                    if 0 <= index < len(players):
                        reply["updates"] = {
                            "crates_affected": crates_affected,
                            "spawned_weapons": spawned_weapons,
                            "picked_up_weapons": picked_up_weapons,
                            "bullets": bullets,
                            "entities_hit": entities_hit,
                            "kills": kills,
                            "players_alive": players_alive,
                            "player_ids": player_ids
                        }
                        reply["index"] = index
                        reply["server_data"] = {
                            "status": server_data["status"],
                            "players_needed_to_start": server_data["players_needed_to_start"],
                            "player_count": server_data["player_count"],
                            "time_till_start": round(server_data["match_start_time"] - (time() - match_start_time), 1)
                        }

                        players[index] = reply

                    reply = players

                conn.sendall(str.encode(json.dumps(reply, indent=2)))

                if index == len(players) - 1:
                    if looped:
                        if server_data["status"] == "match_init" and time() - match_start_time > server_data[
                            "match_start_time"]:
                            server_data["status"] = "play"

                        del crates_affected[:crates_affected_pop_at]
                        del spawned_weapons[:spawned_weapons_pop_at]
                        del picked_up_weapons[:picked_up_weapons_pop_at]
                        del bullets[:bullets_pop_at]
                        del entities_hit[:entities_hit_pop_at]
                        del kills[:kills_pop_at]

                        looped = False
                    else:
                        crates_affected_pop_at = len(crates_affected)
                        spawned_weapons_pop_at = len(spawned_weapons)
                        picked_up_weapons_pop_at = len(picked_up_weapons)
                        bullets_pop_at = len(bullets)
                        entities_hit_pop_at = len(entities_hit)
                        kills_pop_at = len(kills)

                        looped = True

            except Exception as e:
                print(e)
                break

        if 0 <= index < len(players):
            players.pop(index)
        number_of_clients -= 1

        print("Connection Closed")
        conn.close()


    while True:
        conn, addr = s.accept()
        print("Connected to: ", addr)

        if len(players) <= 0 and server_data["status"] == "play":
            reset_server_data(server_config)
            server_data["map_info"] = map_info

            update_server_data(server_data)

        new_pos = {
            "0": 0
        }

        players.append(new_pos)

        number_of_clients += 1

        start_new_thread(threaded_client, (conn,))
