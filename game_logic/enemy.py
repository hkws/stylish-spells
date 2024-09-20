from game_logic.utils import load_enemy_data
from game_logic.evaluator import EnemyEvaluation

class Enemy:
    def __init__(self, id, name, hp, power, image):
        self.id = id
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.power = power
        self.image = image
        self.state = None

    @classmethod
    def spawn(cls, enemy_id):
        data = load_enemy_data(enemy_id)
        enemy = cls.from_dict(data)
        enemy.state = data["default_state"]
        return enemy

    @classmethod
    def from_dict(cls, data):
        enemy = cls(
            id=data["id"],
            name=data["name"],
            hp=data["hp"],
            power=data["power"],
            image=data["image"],
        )
        enemy.max_hp = data["max_hp"] if "max_hp" in data else data["hp"]
        enemy.state = data["state"] if "state" in data else ""
        return enemy

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "power": self.power,
            "image": self.image,
            "state": self.state,
        }

    def take_damage(self, attack):
        self.hp -= attack.damage
        if self.hp < 0:
            self.hp = 0

    def attack(self):
        return EnemyAttack(
            spell="我が力を見よ！",
            damage=self.power,
            result_msg="凄まじい衝撃が走る！",
            enemy_msg="ふははは、どうだ我が力は！",
        )

    def is_defeated(self):
        return self.hp <= 0

    def update_state(self, state: EnemyEvaluation):
        self.state = state.enemy_state


class EnemyAttack:
    def __init__(self, spell, damage, result_msg, enemy_msg):
        self.spell = spell
        self.damage = damage
        self.result_msg = result_msg
        self.enemy_msg = enemy_msg

    @classmethod
    def from_dict(cls, data):
        attack = cls(
            spell=data["spell"],
            damage=data["damage"],
            result_msg=data["result_msg"],
            enemy_msg=data["enemy_msg"],
        )
        return attack

    def to_dict(self):
        return {
            "from": "enemy",
            "spell": self.spell,
            "damage": self.damage,
            "result_msg": self.result_msg,
            "enemy_msg": self.enemy_msg,
        }
