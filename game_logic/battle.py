import json
import uuid
import datetime
from game_logic.player import Player, PlayerAttack
from game_logic.enemy import Enemy, EnemyAttack
from game_logic.field import Field
from game_logic.evaluator import AttackEvaluator


class Battle:

    def __init__(self, id, player, enemy, field, log, _end, evaluator):
        self.id = id
        self.player = player
        self.enemy = enemy
        self.field = field
        self.log = log
        self._end = _end
        self.evaluator = evaluator
    
    @classmethod
    def instantiate(cls, enemy_id, field_id):
        id = str(uuid.uuid4())
        player: Player = Player.appear()
        enemy: Enemy = Enemy.spawn(enemy_id)
        field: Field = Field.form(field_id)
        log = BattleLog()
        log.start()
        _end = False
        evaluator: AttackEvaluator = AttackEvaluator(field_id, enemy_id)
        return cls(id, player, enemy, field, log, _end, evaluator)

    @classmethod
    def from_dict(cls, data):
        id = data["id"]
        player = Player.from_dict(data["player"])
        enemy = Enemy.from_dict(data["enemy"])
        field = Field.from_dict(data["field"])
        log = BattleLog.from_dict(data["log"])
        _end = data["_end"]
        evaluator = AttackEvaluator(field.id, enemy.id)
        return cls(id, player, enemy, field, log, _end, evaluator)

    def to_dict(self):
        return {
            "id": self.id,
            "in_battle": self.in_battle(),
            "player": self.player.to_dict(),
            "enemy": self.enemy.to_dict(),
            "field": self.field.to_dict(),
            "log": self.log.to_dict(),
            "_end": self._end,
        }

    def get_id(self):
        return self.id

    def attack_enemy(self, redis_client, spell):
        # evaluation
        spell_eval, field_eval, enemy_eval = self.evaluator.evaluate(spell, self.field.state, self.enemy.state)
        
        # attack
        attack = self.player.attack(spell_eval, field_eval, enemy_eval)
        self.enemy.take_damage(attack)
        if self.enemy.is_defeated():
            self.end(True)
        if self.player.is_defeated():
            self.end(False)

        state = load_battle_state(redis_client, self.get_id())
        if state is not None and state["_end"]:
            return None
        self.log.save_attack(attack)
        
        # update state
        self.field.update_state(field_eval)
        self.enemy.update_state(enemy_eval)
        return attack
    
    def attack_player(self):
        attack = self.enemy.attack()
        self.player.take_damage(attack)
        if self.player.is_defeated():
            self.end(False)
        return attack

    def end(self, victory):
        self.log.end(victory)
        self._end = True

    def in_battle(self):
        return not self._end


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
        assert self.finished_at is not None
        assert self.started_at is not None

        max_dmg = 0
        max_dmg_spell = None
        max_dmg_per_mp = 0
        max_dmg_per_mp_spell = None
        for attack in self.attacks:
            if not isinstance(attack, PlayerAttack):
                continue
            if max_dmg < attack.damage:
                max_dmg = attack.damage
                max_dmg_spell = attack.spell.spell
            if max_dmg_per_mp < attack.damage / attack.mp:
                max_dmg_per_mp = attack.damage / attack.mp
                max_dmg_per_mp_spell = attack.spell.spell

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


def save_battle_state(redis_client, battle: Battle):
    battle_id = battle.get_id()
    redis_client.set(battle_id, json.dumps(battle.to_dict()))


def load_battle_state(redis_client, battle_id):
    state = redis_client.get(battle_id)
    if state is None:
        return None
    return json.loads(state) # type: ignore


def restore_battle_state(redis_client, battle_id):
    state = load_battle_state(redis_client, battle_id)
    if state is None:
        return None
    return Battle.from_dict(state)