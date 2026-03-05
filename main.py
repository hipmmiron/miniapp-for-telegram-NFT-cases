import asyncio
import json
import subprocess
import aiosqlite
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import WebAppInfo, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command

# --- КОНФИГ (Твой токен и ссылка) ---
TOKEN = "8628901391:AAFHVQplTDUvhKmK-Ara5AOcDghTz2eRJoI"
WEB_APP_URL = "https://hipmmiron.github.io/miniapp-for-telegram-NFT-cases/"
DB_NAME = ".db"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ФУНКЦИЯ АВТОДЕПЛОЯ (Тот самый "Автокомит") ---
def auto_deploy():
    try:
        print("🚀 Синхронизация с GitHub...")
        # Добавляем всё, что ты там наменял в HTML
        subprocess.run(["git", "add", "."], check=True)
        
        # Проверяем, есть ли реально изменения, чтобы не плодить пустые коммиты
        status = subprocess.check_output(["git", "status", "--porcelain"]).decode()
        if status:
            subprocess.run(["git", "commit", "-m", "pro-update: expensive style & logic"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ GitHub обновлен! Твой S23 Ultra увидит новый дизайн через минуту.")
        else:
            print("💤 Изменений в файлах не найдено, пропускаю пуш.")
    except Exception as e:
        print(f"⚠️ Гит капризничает: {e}")
        print("Продолжаю запуск бота без деплоя...")

# --- БАЗА ДАННЫХ ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 1000
            )
        """)
        await db.commit()

async def get_user_balance(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row: return row[0]
            await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()
            return 1000

async def update_balance(user_id: int, amount: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

# --- ХЕНДЛЕРЫ ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    balance = await get_user_balance(message.from_user.id)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🌌 ОТКРЫТЬ КЕЙСЫ (PRO)", web_app=WebAppInfo(url=WEB_APP_URL))],
        [types.InlineKeyboardButton(text="💎 ПОПОЛНИТЬ (7 ⭐)", callback_data="buy")]
    ])
    await message.answer(
        f"🌌 **Nebula NFT Casino**\n\nТвой баланс: `{balance} 🪙`",
        reply_markup=kb, 
        parse_mode="Markdown"
    )

@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    data = json.loads(message.web_app_data.data)
    cost = data.get('cost', 0)
    prize = data.get('prize', '💩')
    
    balance = await get_user_balance(message.from_user.id)
    if balance >= cost:
        await update_balance(message.from_user.id, -cost)
        bonus = 5000 if prize == "🍑" else 0
        if bonus: await update_balance(message.from_user.id, bonus)
        
        await message.answer(
            f"🎰 **Результат прокрутки:**\nСписано: `{cost} 🪙`\nВыпало: {prize}\n" + 
            (f"🔥 **JACKPOT:** `{bonus} 🪙`!" if bonus else ""),
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Баланс пуст. Звезды сами себя не купят.")

# --- ЗАПУСК ---
async def main():
    # 1. Сначала пушим изменения на GitHub
    auto_deploy()
    # 2. Инициализируем БД
    await init_db()
    # 3. Запускаем бота
    print(f"Бот Nebula в сети: https://t.me/nebula_NFT_cases_bot")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Выключаюсь...")