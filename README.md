# 🤖 English Learning Telegram Bot

Python + aiogram 3 + Groq AI yordamida yozilgan ingliz tili o'rgatuvchi bot.

---

## 📁 Loyiha tuzilmasi

```
telegram_bot/
├── app.py                    # Asosiy kirish nuqtasi
├── config.py                 # API kalitlar va sozlamalar
├── requirements.txt          # Kutubxonalar
│
├── handlers/
│   ├── __init__.py
│   ├── start_handler.py      # /start va asosiy menyu
│   ├── quiz_handler.py       # Grammar quiz bo'limi
│   └── vocabulary_handler.py # Vocabulary bo'limi
│
├── keyboards/
│   ├── __init__.py
│   ├── reply_keyboards.py    # Reply klaviaturalar
│   └── inline_keyboards.py   # Inline klaviaturalar
│
├── services/
│   ├── __init__.py
│   ├── json_service.py       # JSON fayl operatsiyalari
│   └── groq_service.py       # Groq AI integratsiyasi
│
└── data/
    ├── users.json            # Foydalanuvchilar
    ├── quizzes.json          # Grammar savollar
    ├── user_progress.json    # Foydalanuvchi progressi
    └── vocabulary.json       # So'zlar bazasi
```

---

## ⚙️ Sozlash

### 1. API kalitlarini olish

**Telegram Bot Token:**
1. Telegramda [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting
4. Token ni nusxalab oling

**Groq API Key:**
1. [https://console.groq.com](https://console.groq.com) ga boring
2. Ro'yxatdan o'ting (bepul)
3. API Keys bo'limidan yangi kalit yarating

### 2. config.py ni to'ldirish

```python
BOT_TOKEN = "7123456789:AAF..."   # @BotFather dan
GROQ_API_KEY = "gsk_..."          # console.groq.com dan
```

---

## 🚀 Ishga tushirish

### Python versiyasi: 3.11+

```bash
# 1. Loyihani klonlash yoki yuklab olish
cd telegram_bot

# 2. Virtual muhit yaratish (ixtiyoriy, lekin tavsiya etiladi)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 4. API kalitlarini config.py ga kiritish
# (yuqoridagi sozlash bo'limiga qarang)

# 5. Botni ishga tushirish
python app.py
```

### Serverda ishga tushirish (background):

```bash
# nohup orqali
nohup python app.py &

# yoki screen orqali
screen -S bot
python app.py
# Ctrl+A, D - screendan chiqish
```

---

## 📖 Bot funksiyalari

### 📝 Quiz bo'limi
- Grammar savollar AI tomonidan avtomatik yaratiladi
- Har bir savol 3 ta variant bilan chiqadi
- To'g'ri/noto'g'ri javob bilan batafsil tushuntirish beriladi
- Savollar tugasa yangilari avtomatik yuklanadi

### 📚 Vocabulary bo'limi
- **So'z qo'shish:** `apple - olma` formatida so'z qo'shiladi
- **Boshlash:** Barcha so'zlardan quiz o'ynaladi
- Hamma foydalanuvchi qo'shgan so'zlar umumiy bazada saqlanadi

---

## 🔧 Muammolar

| Muammo | Yechim |
|--------|--------|
| `Unauthorized` xatosi | BOT_TOKEN ni tekshiring |
| Quiz yaratilmaydi | GROQ_API_KEY ni tekshiring |
| `ModuleNotFoundError` | `pip install -r requirements.txt` qayta ishlating |
| Bot javob bermaydi | Internetni tekshiring |
