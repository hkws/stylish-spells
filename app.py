from flask import Flask, render_template, request, jsonify
import redis
from game_logic.battle import Battle, save_battle_state, load_battle_state, restore_battle_state
import os

redis_host = os.environ.get("REDISHOST", "127.0.0.1")
redis_port = int(os.environ.get("REDISPORT", 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/battle")
def battle_enemy():
    return render_template("battle.html")


@app.route("/battle/<battle_id>")
def battle_detail(battle_id):
    return jsonify(load_battle_state(redis_client, battle_id))


@app.route("/start_game", methods=["POST"])
def start_game():
    body = request.get_json()
    if body.get("username", None) is None:
        return jsonify({"error": "No username"}), 400
    if body.get("enemy", None) is None:
        return jsonify({"error": "No enemy"}), 400
    enemy_id = body["enemy"]

    field_id = {
        "slime": "grassland",
        "golem": "ruins",
        "dragon": "volcano",
    }[enemy_id]

    battle = Battle.instantiate(enemy_id, field_id)
    save_battle_state(redis_client, battle)

    return jsonify(load_battle_state(redis_client, battle.get_id()))


@app.route("/cast_spell", methods=["POST"])
def cast_spell():
    body = request.get_json()
    if body.get("battle_id", None) is None:
        return jsonify({"error": "Invalid battle_id"}), 400
    if body.get("spell", None) is None:
        return jsonify({"error": "Invalid spell"}), 400

    battle_id = body["battle_id"]
    battle = restore_battle_state(redis_client, battle_id)
    if battle is None:
        return jsonify({"error": "Invalid battle_id"}), 400

    spell = body["spell"]
    attack = battle.attack_enemy(redis_client, spell)
    if attack is None:
        return jsonify({"error": "already finished"}), 400
    save_battle_state(redis_client, battle)

    return jsonify(
        {
            "deal": attack.to_dict(),
            "state": load_battle_state(redis_client, battle.get_id()),
        }
    )


@app.route("/enemy_attack", methods=["POST"])
def enemy_attack():
    body = request.get_json()
    if body.get("battle_id", None) is None:
        return jsonify({"error": "Invalid battle_id"}), 400

    battle_id = body["battle_id"]
    battle = restore_battle_state(redis_client, battle_id)
    if battle is None:
        return jsonify({"error": "Invalid battle_id"}), 400

    attack = battle.attack_player()
    save_battle_state(redis_client, battle)

    return jsonify(
        {
            "deal": attack.to_dict(),
            "state": load_battle_state(redis_client, battle_id),
        }
    )


@app.route("/result/<battle_id>")
def result(battle_id):
    battle = restore_battle_state(redis_client, battle_id)
    if battle is None:
        return jsonify({"error": "Invalid battle_id"}), 400
    stats = battle.log.get_stats()
    return render_template("result.html", **stats.to_dict())


if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    app.run(debug=True)
