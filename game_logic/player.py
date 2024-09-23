from game_logic.utils import load_player_data
from game_logic.evaluator import SpellEvaluation, FieldEvaluation, EnemyEvaluation

MP_MAP = {
    "supernatural": 100,
    "non-natural": 10,
    "natural": 1,
    "extreme": 10,
    "high": 8,
    "medium": 4,
    "low": 1,
}

DAMAGE_MAP = {
    "extreme": 100,
    "high": 80,
    "medium": 40,
    "low": 10,
}


class Player:
    def __init__(self, hp, mp):
        self.hp = hp
        self.max_hp = hp
        self.mp = mp
        self.max_mp = mp

    @classmethod
    def appear(cls):
        data = load_player_data("player")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data):
        player = cls(hp=data["hp"], mp=data["mp"])
        player.max_hp = data["max_hp"]
        player.max_mp = data["max_mp"]
        return player

    def to_dict(self):
        return {"hp": self.hp, "max_hp": self.max_hp,
                "mp": self.mp, "max_mp": self.max_mp}

    def take_damage(self, attack):
        self.hp -= attack.damage
        if self.hp < 0:
            self.hp = 0

    def is_defeated(self):
        return self.hp <= 0 or self.mp <= 0

    def attack(self, spell_eval: SpellEvaluation, field_eval: FieldEvaluation, enemy_eval: EnemyEvaluation):
        # MPの算出
        mp = MP_MAP[spell_eval.naturality]*MP_MAP[spell_eval.cost]
        # 効果量の算出
        damage = DAMAGE_MAP[spell_eval.cost] * ((spell_eval.coolness + field_eval.harnessing + enemy_eval.aiming_weakpoint) / 10)
        # 結果メッセージの作成
        if spell_eval.category == "attack":
            result_msg = f"{damage} ダメージを与えた！"
        elif spell_eval.category == "heal":
            result_msg = f"{damage} 回復した！"
        elif spell_eval.category == "buff":
            result_msg = f"バフがかかった！"
        elif spell_eval.category == "debuff":
            result_msg = f"デバフがかかった！"
        enemy_msg = enemy_eval.enemy_message
        field_msg = field_eval.aftermath
        
        # mp消費
        if self.mp < mp:
            damage = 0
            result_msg = "MPが足りない！"
            enemy_msg = ""
            field_msg = ""
        else:
            self.mp -= mp
        
        return PlayerAttack(
            spell=spell_eval,
            mp=mp,
            damage=damage,
            result_msg=result_msg,
            enemy_msg=enemy_msg,
            field_msg=field_msg,
        )


class PlayerAttack:
    def __init__(self, spell: SpellEvaluation, mp, damage, result_msg, enemy_msg, field_msg):
        self.spell = spell
        self.mp = mp
        self.damage = damage
        self.result_msg = result_msg
        self.enemy_msg = enemy_msg
        self.field_msg = field_msg

    @classmethod
    def from_dict(cls, data):
        attack = cls(
            spell=SpellEvaluation.from_dict(data["spell"]),
            mp=data["mp"],
            damage=data["damage"],
            result_msg=data["result_msg"],
            enemy_msg=data["enemy_msg"],
            field_msg=data["field_msg"],
        )
        return attack

    def to_dict(self):
        return {
            "from": "player",
            "spell": self.spell.to_dict(),
            "mp": self.mp,
            "damage": self.damage,
            "result_msg": self.result_msg,
            "enemy_msg": self.enemy_msg,
            "field_msg": self.field_msg,
        }
