import os
import json
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, GenerationConfig
from game_logic.utils import load_field_data, load_enemy_data

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "teak-flash-436008-q2")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
MODEL = os.environ.get("GOOGLE_CLOUD_VERTEX_MODEL", "gemini-1.5-flash-001")


SAFETY_SETTING = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
]


class Evaluator:
    def __init__(self, system_instruction, response_schema) -> None:
        vertexai.init(project=PROJECT, location=LOCATION)
        self.model = GenerativeModel(MODEL, system_instruction=[system_instruction])
        self.config = GenerationConfig(
            max_output_tokens=8192,
            temperature=1,
            top_p=0.95,
            response_mime_type="application/json",
            response_schema=response_schema,
        )
        self.safety_settings = SAFETY_SETTING

    def generate(self, prompt):
        response = self.model.generate_content(
            prompt,
            generation_config=self.config,
            safety_settings=self.safety_settings,
        )
        response_obj = response.to_dict()
        try:
            return json.loads(response_obj["candidates"][0]["content"]["parts"][0]["text"])
        except:
            raise Exception("Response is not in the expected format: {}".format(response_obj))


class SpellEvaluation:
    def __init__(self, spell, category, naturality, cost, coolness):
        self.spell = spell
        self.category = category
        self.naturality = naturality
        self.cost = cost
        self.coolness = coolness

    @classmethod
    def from_dict(cls, data):
        return cls(
            spell=data["spell"],
            category=data["category"],
            naturality=data["naturality"],
            cost=data["cost"],
            coolness=data["coolness"],
        )

    def to_dict(self):
        return {
            "spell": self.spell,
            "category": self.category,
            "naturality": self.naturality,
            "cost": self.cost,
            "coolness": self.coolness,
        }


class SpellEvaluator:
    SYSTEM_INSTRUCTION = """
あなたはロールプレイングゲームの戦闘システムの一部として、ユーザーが入力した呪文詠唱を評価します。以下の指示、情報に従って振る舞ってください。 

## 入力
プレイヤーが詠唱した呪文が入力されます。
```
風よ、集い吹き荒れ敵を吹き飛ばせ！
```

## 出力
入力を踏まえて、以下のkeyを持つJSONを出力してください。

### category
入力された呪文の効果について、以下のいずれかのカテゴリに分類してください。
- "attack": 敵にダメージを与える呪文
- "heal": 味方のHPやMPを回復させる呪文
- "buff": 味方の能力を強化する呪文
- "debuff": 敵の能力を弱体化させる呪文

### naturality
入力された呪文について、以下のtierのいずれかに分類してください。
- "supernatural": 神や天使、悪魔といった超自然的存在の力を借りている呪文
- "non-natural": 地球の自然法則、物理法則から外れる呪文
- "natural": 地球と同様の物理法則や自然の力を利用している呪文

### cost
入力された呪文の発動に必要なコストを、以下のいずれかのtierに分類してください。
- "extreme"
    - categoryがattackの場合: 超自然的な力を借りたり、世界を変えたり壊すほどの大規模な効果を持つ呪文。
    - categoryがhealの場合: 生命を蘇生させる、あるいはHPやMPを自動回復させるような効果を持つ呪文
    - categoryがbuffの場合: 対象の味方を無敵状態にしたり、相手を即死させられるほど能力を強化するような呪文
    - categoryがdebuffの場合: 対象の敵を即死させられるほど衰弱させたり、能力を無効化するほどの効果を持つ呪文
- "high"
    - categoryがattackの場合: extremeほどではないが、生命体を即死させるほどの効果を持つ呪文
    - categoryがhealの場合: HPやMPを全回復させるほどの効果を持つ呪文
    - categoryがbuffの場合: 対象の味方が受けるダメージをほとんど無くしたり、相手に致命傷を負わせられるほど力を強化するような呪文
    - categoryがdebuffの場合: 対象の敵が行動不能になるほど衰弱させたり、能力を半減させるほどの効果を持つ呪文
- "medium"
    - categoryがattackの場合: highほどではないが、生命体を重傷を負わせるほどの効果を持つ呪文
    - categoryがhealの場合: HPやMPを半分回復させるほどの効果を持つ呪文
    - categoryがbuffの場合: 対象の味方が受けるダメージを半減させたり、与えるダメージを倍にするほど力を強化するような呪文
    - categoryがdebuffの場合: 対象の敵の能力を少し減らすほどの効果を持つ呪文
- "low"
    - categoryがattackの場合: mediumほどではないが、生命体に軽傷を負わせるほどの効果を持つ呪文
    - categoryがhealの場合: HPやMPを少し回復させるほどの効果を持つ呪文
    - categoryがbuffの場合: 対象の味方が受けるダメージを少し減らしたり、与えるダメージを少し増やすほど力を強化するような呪文
    - categoryがdebuffの場合: 対象の敵の能力を一時的に少し減らすほどの効果を持つ呪文

### coolness
入力された呪文のかっこよさを0~20の21段階で評価してください。加点要因は以下のとおりです。
- 常用されない言葉やフレーズを使用している
- 呪文の内容が独創的である
- 呪文詠唱の最後に、呪文名を叫んでいる


"""
    RESPONSE_SCHEMA = {
        "type": "OBJECT",
        "properties": {
            "category": {
                "type": "STRING",
                "enum": ["attack", "heal", "buff", "debuff"]
            },
            "naturality": {
                "type": "STRING",
                "enum": ["supernatural", "non-natural", "natural"]
            },
            "cost": {
                "type": "STRING",
                "enum": ["extreme", "high", "medium", "low"]
            },
            "coolness": {
                "type": "INTEGER"
            }
        },
        "required": ["category", "naturality", "cost", "coolness"]
    }

    def __init__(self):
        self.evaluator = Evaluator(self.SYSTEM_INSTRUCTION, self.RESPONSE_SCHEMA)
    
    def evaluate(self, spell):
        result = self.evaluator.generate(spell)
        result["spell"] = spell
        return SpellEvaluation.from_dict(result)


class FieldEvaluation:
    def __init__(self, harnessing, aftermath):
        self.harnessing = harnessing
        self.aftermath = aftermath

    @classmethod
    def from_dict(cls, data):
        return cls(
            harnessing=data["harnessing"],
            aftermath=data["aftermath"]
        )

    def to_dict(self):
        return {
            "harnessing": self.harnessing,
            "aftermath": self.aftermath
        }


class FieldEvaluator:
    SYSTEM_INSTRUCTION = """
あなたはロールプレイングゲームの戦闘システムの一部として、ユーザーが入力した呪文詠唱が戦闘を行っているフィールドをどれほど活用しているかを評価します。以下の指示、情報に従って振る舞ってください。 

## フィールドの情報
フィールドの特徴：{feature}

## 入力
以下のように、フィールドの状態とプレイヤーが詠唱した呪文が入力されます。
```
フィールドの状態：草を優しく揺らす程度の風が吹いている。
呪文：風よ、集い吹き荒れ敵を吹き飛ばせ！
```

## 出力
入力を踏まえて、以下のkeyを持つJSONを出力してください。

### harnessing
入力された呪文がフィールドの特徴や状態をどれほど活用しているかを-10~10の21段階で評価してください。フィールドの状況を最大限に活用しているほど高い点数になります。
#### 例
{harnessing_example}

### aftermath
入力された呪文が発動した結果、フィールドがどのような状況になるかを短い文章で出力してください。
#### 例
{aftermath_example}

"""
    RESPONSE_SCHEMA = {
        "type": "OBJECT",
        "properties": {
            "harnessing": {
                "type": "INTEGER"
            },
            "aftermath": {
                "type": "STRING"
            }
        },
        "required": ["harnessing", "aftermath"]
    }

    def __init__(self, id):
        instruction_data = load_field_data(id)["instruction_info"]
        if isinstance(instruction_data["harnessing_example"], list):
            instruction_data["harnessing_example"] = "\n".join(instruction_data["harnessing_example"])
        if isinstance(instruction_data["aftermath_example"], list):
            instruction_data["aftermath_example"] = "\n".join(instruction_data["aftermath_example"])
        system_instruction = self.SYSTEM_INSTRUCTION.format(**instruction_data)
        self.evaluator = Evaluator(system_instruction, self.RESPONSE_SCHEMA)

    def evaluate(self, field_state, spell):
        result = self.evaluator.generate(f"フィールドの状態：{field_state}\n呪文：{spell}")
        return FieldEvaluation.from_dict(result)


class EnemyEvaluation:
    def __init__(self, aiming_weakpoint, enemy_message, enemy_state):
        self.aiming_weakpoint = aiming_weakpoint
        self.enemy_message = enemy_message
        self.enemy_state = enemy_state
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            aiming_weakpoint=data["aiming_weakpoint"],
            enemy_message=data["enemy_message"],
            enemy_state=data["enemy_state"]
        )
    
    def to_dict(self):
        return {
            "aiming_weakpoint": self.aiming_weakpoint,
            "enemy_message": self.enemy_message,
            "enemy_state": self.enemy_state
        }


class EnemyEvaluator:
    SYSTEM_INSTRUCTION = """
あなたはロールプレイングゲームの戦闘システムの一部として、ユーザーが入力した呪文がモンスターに与える影響を評価します。以下の指示、情報に従って振る舞ってください。

## モンスターの情報
モンスターの特徴：{feature}
モンスターの長所：{strongpoint}
モンスターの弱点：{weakpoint}
モンスターの性格：{character}

## 入力
モンスターの状態とプレイヤーが詠唱した呪文が入力されます。例えば、以下のような形式です。
```
モンスターの状態：モンスターはプレイヤーに向かって立ちはだかっている。
呪文：風よ、集い吹き荒れ敵を吹き飛ばせ！
```

## 出力
入力を踏まえて、以下のkeyを持つJSONを出力してください。

### aiming_weakpoint
入力された呪文がモンスターの状態や弱点を利用できているか、-10~10の21段階で評価してください。弱点を突いているほど高い点数に、相手の長所をついているほど低い点数になります。また、モンスターの状態として、特定の箇所が傷ついている場合、その箇所を狙う呪文が詠唱された場合は高い点数になります。
#### 例
{aiming_weakpoint_example}

### enemy_message
攻撃を受けたモンスターがプレイヤーに向かって発するセリフを出力してください。
このメッセージは、aiming_weakpointの評価を中心にしつつ、モンスターの状態も踏まえてください。これを通じて、プレイヤーにモンスターの長所や弱点を示唆することが目的です。
#### 例
{enemy_message_example}

### enemy_state
攻撃を受けた後のモンスターの状態を短い文章で出力してください。
"""

    RESPONSE_SCHEMA = {
        "type": "OBJECT",
        "properties": {
            "aiming_weakpoint": {
                "type": "INTEGER"
            },
            "enemy_message": {
                "type": "STRING"
            },
            "enemy_state": {
                "type": "STRING"
            }
        },
        "required": ["aiming_weakpoint", "enemy_message", "enemy_state"]
    }

    def __init__(self, id):
        instruction_data = load_enemy_data(id)["instruction_info"]
        if isinstance(instruction_data["aiming_weakpoint_example"], list):
            instruction_data["aiming_weakpoint_example"] = "\n".join(instruction_data["aiming_weakpoint_example"])
        if isinstance(instruction_data["enemy_message_example"], list):
            instruction_data["enemy_message_example"] = "\n".join(instruction_data["enemy_message_example"])
        system_instruction = self.SYSTEM_INSTRUCTION.format(**instruction_data)
        self.evaluator = Evaluator(system_instruction, self.RESPONSE_SCHEMA)

    def evaluate(self, enemy_state, spell):
        result = self.evaluator.generate(f"モンスターの状態：{enemy_state}\n呪文：{spell}")
        return EnemyEvaluation.from_dict(result)

class AttackEvaluator:
    def __init__(self, field_id, enemy_id):
        self.spell_evaluator = SpellEvaluator()
        self.field_evaluator = FieldEvaluator(field_id)
        self.enemy_evaluator = EnemyEvaluator(enemy_id)

    def evaluate_spell(self, spell):
        result = self.spell_evaluator.evaluate(spell)
        return result

    def evaluate_field(self, field_state, spell):
        result = self.field_evaluator.evaluate(field_state, spell)
        return result

    def evaluate_enemy(self, enemy_state, spell):
        result = self.enemy_evaluator.evaluate(enemy_state, spell)
        return result
    
    def evaluate(self, spell, field_state, enemy_state):
        spell_result = self.evaluate_spell(spell)
        field_result = self.evaluate_field(field_state, spell)
        enemy_result = self.evaluate_enemy(enemy_state, spell)
        return spell_result, field_result, enemy_result