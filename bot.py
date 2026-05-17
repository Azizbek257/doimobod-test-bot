import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# 1. BOT SOZLAMALARI (TOKEN VA KANAL ID)
BOT_TOKEN = "7722744158:AAHwscR-u_M5gX-uLqYcWc76iG899M70Kno"  # Sizning bot tokeningiz
CHANNEL_ID = "-1002364733353"  # Sizning telegram kanalingiz ID-si
ADMIN_ID = 6363653198  # Sizning (ustozning) telegram ID-ingiz

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher obyektlarini yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Bazani vaqtincha xotirada saqlash
active_tests = {}  # {test_kod: "to_g_ri_javoblar"}
student_results = {}

# --- USTOZ QISMI (ADMIN) ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "🌟 **Assalomu alaykum, Ustoz!**\n"
            "Doimobod EDU test tekshirish tizimiga xush kelibsiz.\n\n"
            "Yangi test kalitlarini kiritish uchun masalan:\n"
            "`/yangi 1234*abcd...` ko'rinishida yuboring.\n"
            "(1234 - test kodi, abcd... - to'g'ri javoblar)"
        )
    else:
        await message.answer(
            "👋 **Assalomu alaykum, talaba!**\n"
            "Test topshirish botiga xush kelibsiz.\n\n"
            "Javoblaringizni tekshirish uchun quyidagi formatda yuboring:\n"
            "`TestKodi*Ism Familiya*Javoblar` (Masalan: `1234*Ali Valiyev*abcd...`)\n\n"
            "⚠️ *Eslatma: Javoblarni kichik harflar bilan, probelsiz yozing.*"
        )

@dp.message(Command("yangi"))
async def add_test_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        data = message.text.split(" ", 1)[1]
        test_code, answers = data.split("*")
        test_code = test_code.strip()
        answers = answers.strip().lower()
        
        active_tests[test_code] = answers
        await message.answer(f"✅ **Yangi test muvaffaqiyatli saqlandi!**\n🔑 KOD: `{test_code}`\n📊 Savollar soni: {len(answers)} ta.")
    except Exception:
        await message.answer("❌ **Xatolik!** Format noto'g'ri. Quyidagicha yozing:\n`/yangi Kod*javoblar` (Masalan: `/yangi 1234*abcde`)")

# --- TALABALAR QISMI ---
@dp.message(F.text.contains("*"))
async def check_test_handler(message: types.Message):
    try:
        parts = message.text.split("*")
        if len(parts) < 3:
            await message.answer("❌ **Format noto'g'ri!**\nIltimos, `TestKodi*Ism Familiya*Javoblaringiz` shaklida yuboring.")
            return
            
        test_code = parts[0].strip()
        student_name = parts[1].strip()
        student_answers = parts[2].strip().lower()
        
        if test_code not in active_tests:
            await message.answer("❌ **Kechirasiz, bunday kodli test tizimda mavjud emas!**\nIltimos, kodni qayta tekshiring.")
            return
            
        correct_answers = active_tests[test_code]
        correct_count = 0
        total_questions = len(correct_answers)
        
        for i in range(min(len(student_answers), total_questions)):
            if student_answers[i] == correct_answers[i]:
                correct_count += 1
                
        percentage = (correct_count / total_questions) * 100
        
        result_msg = (
            f"📊 **Sizning Natijangiz:**\n\n"
            f"👤 O'quvchi: **{student_name}**\n"
            f"🔑 Test kodi: `{test_code}`\n"
            f"✅ To'g'ri javoblar: {correct_count} ta\n"
            f"❌ Noto'g'ri javoblar: {total_questions - correct_count} ta\n"
            f"📈 Foiz: {percentage:.1f}%\n"
        )
        await message.answer(result_msg)
        
        # KANALGA NATIJANI YUBORISH
        channel_msg = (
            f"📢 **Yangi Natija (Test: {test_code})**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 O'quvchi: **{student_name}**\n"
            f"✅ Natija: {correct_count}/{total_questions} ta\n"
            f"📈 Ko'rsatkich: {percentage:.1f}%\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📍 @Doimobod_EDU"
        )
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=channel_msg)
        except Exception as e:
            logging.error(f"Kanalga yuborishda xatolik: {e}")
            
    except Exception as e:
        await message.answer("❌ **Xatolik yuz berdi!** Ma'lumotlarni qayta tekshiring.")

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
