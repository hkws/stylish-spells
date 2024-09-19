class Player:
    def __init__(self, hp):
        self.hp = hp
        self.max_hp = hp

    @classmethod
    def from_dict(cls, data):
        player = cls(hp=data["hp"])
        player.max_hp = data["max_hp"]
        return player

    def take_damage(self, attack):
        self.hp -= attack.damage
        if self.hp < 0:
            self.hp = 0

    def is_defeated(self):
        return self.hp <= 0

    def to_dict(self):
        return {"hp": self.hp, "max_hp": self.max_hp}

    def attack(self, spell):
        return PlayerAttack(
            spell=spell,
            mp=len(spell),
            damage=20,
            result_msg="ダメージを与えた！",
            enemy_msg="ぐおおおお、やるではないか",
        )


class PlayerAttack:
    def __init__(self, spell, mp, damage, result_msg, enemy_msg):
        self.spell = spell
        self.mp = mp
        self.damage = damage
        self.result_msg = result_msg
        self.enemy_msg = enemy_msg

    @classmethod
    def from_dict(cls, data):
        attack = cls(
            spell=data["spell"],
            mp=data["mp"],
            damage=data["damage"],
            result_msg=data["result_msg"],
            enemy_msg=data["enemy_msg"],
        )
        return attack

    def to_dict(self):
        return {
            "from": "player",
            "spell": self.spell,
            "mp": self.mp,
            "damage": self.damage,
            "result_msg": self.result_msg,
            "enemy_msg": self.enemy_msg,
        }
