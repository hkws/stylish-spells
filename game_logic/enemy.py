class Enemy:
    def __init__(self, name, hp, power, image):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.power = power
        self.image = image

    @classmethod
    def from_dict(cls, data):
        enemy = cls(
            name=data["name"],
            hp=data["hp"],
            power=data["power"],
            image=data["image"],
        )
        enemy.max_hp = data["max_hp"]
        return enemy

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

    def to_dict(self):
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "power": self.power,
            "image": self.image,
        }


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
