import uuid
import datetime
from game_logic.player import Player, PlayerAttack
from game_logic.enemy import Enemy, EnemyAttack


class Battle:
    def __init__(self, player, enemy):
        self.id = str(uuid.uuid4())
        self.player: Player = player
        self.enemy: Enemy = enemy
        self.log = BattleLog()
        self.log.start()
        self._end = False

    @classmethod
    def from_dict(cls, data):
        battle = cls(player=None, enemy=None)
        battle.id = data["id"]
        battle.player = Player.from_dict(data["player"])
        battle.enemy = Enemy.from_dict(data["enemy"])
        battle.log = BattleLog.from_dict(data["log"])
        return battle

    def get_id(self):
        return self.id

    def attack(self, attack):
        self.log.save_attack(attack)

    def end(self, victory):
        self.log.end(victory)
        self._end = True

    def in_battle(self):
        return not self._end

    def to_dict(self):
        return {
            "id": self.id,
            "in_battle": self.in_battle(),
            "player": self.player.to_dict(),
            "enemy": self.enemy.to_dict(),
            "log": self.log.to_dict(),
        }


class BattleLog:
    def __init__(self):
        self.started_at = None
        self.finished_at = None
        self.attacks: list[PlayerAttack | EnemyAttack] = []
        self.victory = None

    @classmethod
    def from_dict(cls, data):
        log = cls()
        log.started_at = (
            datetime.datetime.strptime(data["started_at"], "%Y-%m-%d %H:%M:%S")
            if data["started_at"]
            else None
        )
        log.finished_at = (
            datetime.datetime.strptime(data["finished_at"], "%Y-%m-%d %H:%M:%S")
            if data["finished_at"]
            else None
        )
        attacks = []
        for atk in data["attacks"]:
            if atk["from"] == "player":
                attacks.append(PlayerAttack.from_dict(atk))
            elif atk["from"] == "enemy":
                attacks.append(EnemyAttack.from_dict(atk))
            else:
                raise Exception("invalid attack")
        log.attacks = attacks
        log.victory = data["victory"]
        return log

    def to_dict(self):
        return {
            "started_at": (
                datetime.datetime.strftime(self.started_at, "%Y-%m-%d %H:%M:%S")
                if self.started_at
                else None
            ),
            "finished_at": (
                datetime.datetime.strftime(self.finished_at, "%Y-%m-%d %H:%M:%S")
                if self.finished_at
                else None
            ),
            "attacks": [attack.to_dict() for attack in self.attacks],
            "victory": self.victory,
        }

    def start(self):
        if self.started_at is not None:
            raise Exception("already started")
        self.started_at = datetime.datetime.now()

    def end(self, victory):
        if self.finished_at is not None:
            raise Exception("already finished")
        self.finished_at = datetime.datetime.now()
        self.victory = victory

    def save_attack(self, attack):
        self.attacks.append(attack)

    def get_stats(self):
        max_dmg = 0
        max_dmg_spell = None
        max_dmg_per_mp = 0
        max_dmg_per_mp_spell = None
        for attack in self.attacks:
            if not isinstance(attack, PlayerAttack):
                continue
            if max_dmg < attack.damage:
                max_dmg = attack.damage
                max_dmg_spell = attack.spell
            if max_dmg_per_mp < attack.damage / attack.mp:
                max_dmg_per_mp = attack.damage / attack.mp
                max_dmg_per_mp_spell = attack.spell

        return BattleStats(
            **{
                "max_damage": max_dmg,
                "max_damage_spell": max_dmg_spell,
                "max_damage_per_mp": max_dmg_per_mp,
                "max_damage_per_mp_spell": max_dmg_per_mp_spell,
                "battle_time": (self.finished_at - self.started_at).total_seconds(),
                "victory": self.victory,
            }
        )


class BattleStats:
    def __init__(
        self,
        battle_time,
        max_damage,
        max_damage_spell,
        max_damage_per_mp,
        max_damage_per_mp_spell,
        victory,
    ):
        self.battle_time = battle_time
        self.max_damage = max_damage
        self.max_damage_spell = max_damage_spell
        self.max_damage_per_mp = max_damage_per_mp
        self.max_damage_per_mp_spell = max_damage_per_mp_spell
        self.victory = victory

    def to_dict(self):
        return {
            "battle_time": self.battle_time,
            "max_damage": self.max_damage,
            "max_damage_spell": self.max_damage_spell,
            "max_damage_per_mp": self.max_damage_per_mp,
            "max_damage_per_mp_spell": self.max_damage_per_mp_spell,
            "victory": self.victory,
        }
