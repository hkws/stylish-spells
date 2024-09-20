import json

def load_enemy_data(id):
    with open("data/enemy.json", "r") as f:
        enemies = json.load(f)
    for enemy in enemies:
        if enemy["id"] == id:
            return enemy
    else:
        raise Exception("Enemy not found")


def load_field_data(id):
    with open("data/field.json", "r") as f:
        fields = json.load(f)
    for field in fields:
        if field["id"] == id:
            return field
    else:
        raise Exception("Field not found")
    
def load_player_data(id):
    with open("data/player.json", "r") as f:
        player = json.load(f)
    return player