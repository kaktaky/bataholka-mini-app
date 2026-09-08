import json
from openai import OpenAI

from backend import config

BASE_URL = config.LM_BASE_URL
MODEL = config.LM_MODEL

CATEGORIES = ["ok", "насилие", "наркотики", "оружие", "документы",
              "мошенничество", "интим", "оскорбления", "контакты", "другое"]

SCHEMA = {
    "type": "object",
    "properties": {
        "reason":     {"type": "string"},
        "decision":   {"type": "string", "enum": ["approve", "reject"]},
        "category":   {"type": "string", "enum": CATEGORIES},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["decision", "category", "reason", "confidence"],
    "additionalProperties": False,
}

SYSTEM = """\
Ты модератор доски объявлений. Определи, нарушает ли объявление правила.
Запрещено: оружие, наркотики, поддельные документы, интим-услуги, органы,
услуги насилия, мошеннические схемы, оскорбления, обход площадки через
личные контакты в тексте.

Важно: криминальные объявления почти всегда написаны эвфемизмами и намёками,
а не прямым текстом. Оценивай подразумеваемый смысл, а не буквальный.

Примеры намёков: "закопаю за горами" — сокрытие тела; "белый снег",
"соль", "закладки" — наркотики; "решу вопрос с правами" — поддельные документы.

write to decision when ok approve else reject.

Обычные бытовые объявления не выдумывай подозрительными.
"""

client = OpenAI(base_url=BASE_URL, api_key=config.LM_API_KEY)


def moderate(text: str) -> dict:
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": text.strip()[:2000]}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "moderation",
                "strict": True,
                "schema": SCHEMA,
            },
        },
        temperature=0,
        max_tokens=500,
    )
    res = json.loads(r.choices[0].message.content)
    return res


if __name__ == "__main__":
    for ad in [
        "Продам детскую коляску, состояние отличное, самовывоз",
        "Белый снег высшего качества, закладки по городу, пишите в тг",
    ]:
        print(ad, "->", moderate(ad))
