from flask import Flask, render_template, request, jsonify
import redis
from game_logic.enemy import Enemy
from game_logic.player import Player
from game_logic.battle import Battle, PlayerAttack, EnemyAttack
import os
import json

redis_host = os.environ.get("REDISHOST", "127.0.0.1")
redis_port = int(os.environ.get("REDISPORT", 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
app = Flask(__name__)


def save_battle_state(battle: Battle):
    battle_id = battle.get_id()
    redis_client.set(battle_id, json.dumps(battle.to_dict()))


def load_battle_state(battle_id):
    state = redis_client.get(battle_id)
    if state is None:
        return None
    return json.loads(state)


def restore_battle_state(battle_id):
    state = load_battle_state(battle_id)
    if state is None:
        return None
    return Battle.from_dict(state)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/battle")
def battle_enemy():
    return render_template("battle.html")


@app.route("/battle/<battle_id>")
def battle_detail(battle_id):
    return jsonify(load_battle_state(battle_id))


@app.route("/start_game", methods=["POST"])
def start_game():
    body = request.get_json()
    if body.get("level", None) is None:
        return jsonify({"error": "No level"}), 400

    level = int(body.get("level"))

    if level == 1:
        enemy = Enemy("Slime", 50, 10, "slime.png")
    elif level == 2:
        enemy = Enemy("Stone Golem", 100, 20, "golem.png")
    elif level == 3:
        enemy = Enemy("Dragon", 200, 30, "dragon.png")
    else:
        return jsonify({"error": "Invalid level"}), 400

    player = Player(100)
    battle = Battle(player, enemy)
    save_battle_state(battle)

    return jsonify(load_battle_state(battle.get_id()))


@app.route("/cast_spell", methods=["POST"])
def cast_spell():
    body = request.get_json()
    if body.get("battle_id", None) is None:
        return jsonify({"error": "Invalid battle_id"}), 400
    if body.get("spell", None) is None:
        return jsonify({"error": "Invalid spell"}), 400

    battle_id = body["battle_id"]
    battle = restore_battle_state(battle_id)
    player = battle.player
    enemy = battle.enemy

    spell = body["spell"]
    attack = player.attack(spell)

    enemy.take_damage(attack)
    battle.attack(attack)
    if enemy.is_defeated():
        battle.end(True)
    save_battle_state(battle)

    return jsonify(
        {
            "deal": attack.to_dict(),
            "state": load_battle_state(battle.get_id()),
        }
    )


@app.route("/enemy_attack", methods=["POST"])
def enemy_attack():
    body = request.get_json()
    if body.get("battle_id", None) is None:
        return jsonify({"error": "Invalid battle_id"}), 400

    battle_id = body["battle_id"]
    battle = restore_battle_state(battle_id)
    player = battle.player
    enemy = battle.enemy

    attack = enemy.attack()
    player.take_damage(attack)
    battle.attack(attack)
    if player.is_defeated():
        battle.end(False)
    save_battle_state(battle)

    return jsonify(
        {
            "deal": attack.to_dict(),
            "state": load_battle_state(battle_id),
        }
    )


@app.route("/result/<battle_id>")
def result(battle_id):
    battle = restore_battle_state(battle_id)
    stats = battle.log.get_stats()
    return render_template("result.html", **stats.to_dict())


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    app.run(debug=True)
