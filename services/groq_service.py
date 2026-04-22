# ============================================================
# services/groq_service.py - Groq API orqali quiz yaratish
# ============================================================

import json
import logging
import httpx
from config import GROQ_API_KEYS, GROQ_MODEL, QUIZ_BATCH_SIZE

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

QUIZ_GENERATION_PROMPT = f"""
Siz Advanced English Grammar Quiz yaratuvchi IELTS o'qituvchisiz. O'rta va yuqori darajadagi savollar yarating.

MUHIM TALABLAR:
1. Aynan {QUIZ_BATCH_SIZE} ta savol yarating - HECH QACHON KAMROQ YOKI KO'PROQ EMAS
2. Har bir savolda FAQAT 3 ta variant bo'lsin
3. Faqat BITTA to'g'ri javob bo'lsin
4. Savollar QIYIN va AMALIY bo'lsin (sodda emas!)
5. Har bir explanation BATAFSIL, TUSHUNTIRIB BERILSIN va MISOLLAR BILAN TUSHUNTIRING

SAVOLLAR MAVZULARI (har bir mavzudan 1-2 ta savol):
- Present Simple vs Continuous vs Perfect (murakkab holatlar)
- Past Simple vs Continuous vs Perfect (murakkab holatlar)
- Future tenses (Simple, Continuous, Perfect, Going to)
- Conditional sentences (If clauses - Type 1, 2, 3)
- Modal verbs (can/could/may/might/must/should/would/will)
- Passive voice (turli zamanlarda)
- Reported speech (Direct to Indirect)
- Articles (a/an/the - murakkab qoidalar)
- Prepositions (in/on/at/by/with va boshqalar)
- Phrasal verbs (common va uncommon)
- Relative clauses (who/which/that/where)
- Gerunds vs Infinitives

EXPLANATION TALABLARI - BATAFSIL VA TUSHUNTIRIB BERILSIN:
1. NIMA UCHUN TO'G'RI JAVOB TO'G'RI:
   - Qaysi grammar qoidasi ishlatiladi
   - Qanday ma'noni bildiradi
   - Misol bilan tushuntiring

2. NIMA UCHUN BOSHQA VARIANTLAR NOTO'G'RI:
   - Har bir noto'g'ri variant uchun alohida tushuntiring
   - Qaysi qoidani buzadi
   - Qanday xato ma'noni bildiradi

3. QOIDANI ANIQ AYTING:
   - Grammar qoidasining nomini ayting
   - Qoidaning asosiy qismi nima ekanligini tushuntiring

4. MISOLLAR BILAN TUSHUNTIRING:
   - Shunga o'xshash misollar keltiring
   - Har bir misol o'zbek tilida tarjimasi bilan

MISOL FORMAT:
[
  {{
    "question": "By the time you arrive, I ___ dinner.",
    "options": ["will finish", "will have finished", "am finishing"],
    "correct_answer": "will have finished",
    "explanation": "1. 'Will have finished' to'g'ri javob, chunki bu Future Perfect zamoni. Bu gapning ma'nosi: 'Siz kelgan paytda men taomni tugatgan bo'lishaman' degan ma'noni bildiradi. 'By the time' iborasi bilan Future Perfect ishlatiladi. Misol: 'By 5 PM, I will have finished my work' (Soat 5 ga kelib, men ishimni tugatgan bo'lishaman).\\n\\n2. 'Will finish' noto'g'ri, chunki bu Future Simple. Bu shakl 'Siz kelgan paytda men taomni tutatyapman' degan ma'noni bildiradi, lekin biz 'tugatgan bo'lishaman' degan ma'noni istaymiz.\\n\\n3. 'Am finishing' noto'g'ri, chunki bu Present Continuous. Bu shakl hozir davom etayotgan harakatni bildiradi, lekin biz kelajakdagi voqea haqida gapirmoqchimiz.\\n\\nQOIDA: 'By the time' + Future Perfect = kelajakdagi biror voqea tugagan paytda boshqa bir voqea haqida gapirish. Misol: 'By next year, she will have lived here for 10 years' (Keyingi yil, u bu yerda 10 yil yasagan bo'ladi).",
    "tense_or_topic": "Future Perfect"
  }}
]

FAQAT JSON ARRAY QAYTARING - BOSHQA HECH NARSA YOZMANG!
"""


async def generate_quiz_questions() -> list[dict] | None:
    for api_key_index, api_key in enumerate(GROQ_API_KEYS):
        try:
            logger.info(f"Quiz yaratish uchun API key #{api_key_index + 1} ishlatilmoqda...")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": """Siz IELTS o'qituvchisi va Advanced English Grammar Quiz yaratuvchi AI tizimсiz. 
Sizning vazifangiz:
1. FAQAT JSON formatda javob berish - boshqa hech narsa yozmang
2. Har bir savol QIYIN va AMALIY bo'lsin
3. Har bir explanation BATAFSIL, TUSHUNTIRIB BERILSIN va MISOLLAR BILAN TUSHUNTIRING
4. Noto'g'ri variantlarni alohida tushuntiring
5. Grammar qoidalarini ANIQ AYTING
6. Talablar qat'iy bajarilsin - hech qachon kamroq yoki ko'proq savol yozmang""",
                    },
                    {
                        "role": "user",
                        "content": QUIZ_GENERATION_PROMPT,
                    },
                ],
                "temperature": 0.8,
                "max_tokens": 6000,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(GROQ_API_URL, headers=headers, json=payload)
                response.raise_for_status()

            data = response.json()
            raw_content = data["choices"][0]["message"]["content"].strip()

            if raw_content.startswith("```"):
                lines = raw_content.split("\n")
                raw_content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

            quizzes = json.loads(raw_content)

            validated = []
            for q in quizzes:
                if all(k in q for k in ["question", "options", "correct_answer", "explanation", "tense_or_topic"]):
                    if len(q["options"]) == 3 and q["correct_answer"] in q["options"]:
                        validated.append(q)

            logger.info(f"Groq AI {len(validated)} ta savol yaratdi (API key #{api_key_index + 1})")
            return validated

        except httpx.HTTPStatusError as e:
            logger.warning(f"API key #{api_key_index + 1} HTTP xatosi: {e.response.status_code}")
            if api_key_index < len(GROQ_API_KEYS) - 1:
                logger.info(f"Keyingi API key bilan qayta urinilmoqda...")
                continue
            else:
                logger.error(f"Barcha API keylar ishlamadi")
                return None
        except json.JSONDecodeError as e:
            logger.warning(f"API key #{api_key_index + 1} JSON xatosi: {e}")
            if api_key_index < len(GROQ_API_KEYS) - 1:
                logger.info(f"Keyingi API key bilan qayta urinilmoqda...")
                continue
            else:
                logger.error(f"Barcha API keylar ishlamadi")
                return None
        except Exception as e:
            logger.warning(f"API key #{api_key_index + 1} da xato: {e}")
            if api_key_index < len(GROQ_API_KEYS) - 1:
                logger.info(f"Keyingi API key bilan qayta urinilmoqda...")
                continue
            else:
                logger.error(f"Barcha API keylar ishlamadi")
                return None

    return None
