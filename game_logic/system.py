import os
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, Part


PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "teak-flash-436008-q2")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "asia-northeast1")
MODEL = os.environ.get("GOOGLE_CLOUD_VERTEX_MODEL", "gemini-1.5-flash-001")

GENERATION_CONFIG = {
    "max_output_tokens": 8192,
    "temperature": 1,
    "top_p": 0.95,
    # "response_mime_type": "application/json",
    # "response_schema": {
    #     "type": "OBJECT",
    #     "properties": {
    #         "adaptability": {"type": "NUMBER"},
    #         "weakness": {"type": "NUMBER"},
    #         "coolness": {"type": "NUMBER"},
    #         "enemy_msg": {"type": "STRING"},
    #     },
    # },
}

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


SYSTEM_INSTRUCTION = """あなたはロールプレイングゲームの戦闘システムです。以下の指示、情報に従って振る舞ってください。 
## 入力
プレイヤーが詠唱した呪文と、現在プレイヤーが戦っているモンスターの情報が与えられます。例えば以下のような形式です。
```
モンスター：ストーンゴーレム。土を固めてできた2mほどの人形。固くて物理的な衝撃に強いが、関節部分は比較的やわらかい。背中の核で周囲の環境から魔素を吸収して駆動する。
呪文：風よ、集い吹き荒れ敵を吹き飛ばせ！
```

## 出力
入力を踏まえて、以下に示す3つの観点の得点と呪文を喰らったモンスターのセリフを出力してください。例えば以下のようなものです。
```
一般的な自然法則との適合性：3
モンスターの弱点の考慮：2
かっこよさ：4
モンスターのセリフ：私の体を壊せる風などない！
```

## ダメージ評価の観点
### 観点1: 一般的な自然法則との適合性
ゲーム内世界では、地球上で成り立つ一般的な自然法則が成り立ちます。例えば、重力があり、物質は原子によって成り立ちます。水は土の形を変え、草木は燃えます。呪文の内容と、このような一般的な自然法則との適合性を1から10の10段階で評価してください。最も適合している場合は10です。例えば、「風よ、集いて人形となり、敵を殴れ」という呪文は、質量のない風を質量のある人形にしようとしている点で、自然法則との適合性が低いと判断できます。

### 観点2: モンスターの弱点の考慮 入力として与えられたモンスターの情報と自然法則を踏まえ、モンスターの弱点を突く呪文詠唱ができているかを1~10の10段階で評価してください。弱点を突けているほど高い点数になります。例えば前述のストーンゴーレムに対しては、水をぶつけるような呪文や、ゴーレムの核を攻撃する呪文は、7以上の得点になるでしょう。

### 観点3: かっこよさ プレイヤーが入力した呪文のかっこよさを1~10の10段階で評価してください。いわゆる厨二病的なかっこよさをかんじられるほど10に近い点にしてください。"""


def generate():
    vertexai.init(project=PROJECT, location=LOCATION)
    model = GenerativeModel(MODEL, system_instruction=[SYSTEM_INSTRUCTION])
    chat = model.start_chat()
    print(
        chat.send_message(
            [
                """
             モンスター：魔王。とても強い。仰々しくて尊大な口調。光に弱い。
             呪文：永久不滅な空の輝きよ、我が手に集い、敵を貫け！
             """
            ],
            generation_config=GENERATION_CONFIG,
            safety_settings=SAFETY_SETTING,
        )
    )


generate()
