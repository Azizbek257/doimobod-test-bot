import logging
import asyncio
import io
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# --- TOKEN VA ADMIN ---
TOKEN = "7759885145:AAFS1wbyM4lX6gWqMvG674g9mS-C6g379Yg"
ADMIN_ID = 5410190204  # Sizning Telegram ID'ngiz

# --- AIOGRAM INITIALIZATION (XATOSIZ VERSIYA) ---
bot = Bot(token=TOKEN, default_req_options=Bot.Properties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# --- O'ZGARUVCHILARNI XOTIRADA SAQLASH ---
# Haqiqiy loyihada bular bazada turadi, hozircha operativ xotirada
CURRENT_TITUL = ""      # Masalan: "ABCDACBA..."
STUDENT_RESULTS = {}    # {user_id: {"name": "...", "score": 15, "total": 30}}

# --- STATES (FSM) ---
class AdminStates(StatesGroup):
    waiting_for_titul = State()

class StudentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_answers = State()

# --- ADMIN BUYRUQLARI ---
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Siz admin emassiz!")
        return
    
    text = (
        "<b>Doimobod EDU - Admin Panel</b>\n\n"
        "1. /set_titul - Yangi kalit (titul) kiritish\n"
        "2. /get_results - Natijalarni fayl qilib yuklab olish\n"
        "3. /clear_results - Natijalar bazasini tozalash\n\n"
        f"Hozirgi faol kalit: <code>{CURRENT_TITUL if CURRENT_TITUL else 'Kiritilmagan'}</code>"
    )
    await message.reply(text)

@dp.message(Command("set_titul"))
async def set_titul_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.reply("Yangi kalitlarni shunday formatda yuboring (Masalan: ABCDACBA...):")
    await state.set_state(AdminStates.waiting_for_titul)

@dp.message(AdminStates.waiting_for_titul)
async def set_titul_save(message: types.Message, state: FSMContext):
    global CURRENT_TITUL
    CURRENT_TITUL = message.text.strip().upper()
    await state.clear()
    await message.reply(f"Kalit muvaffaqiyatli saqlandi!\nJami savollar soni: {len(CURRENT_TITUL)} ta.")

@dp.message(Command("get_results"))
async def get_results_file(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    
    if not STUDENT_RESULTS:
        await message.reply("Hozircha hech kim test topshirmadi.")
        return
    
    # Oddiy CSV/TXT formatda fayl yaratish (Excel tushunadigan format)
    output = io.StringIO()
    output.write("Ism;To'g'ri javoblar;Jami savollar\n")
    
    for res in STUDENT_RESULTS.values():
        output.write(f"{res['name']};{res['score']};{res['total']}\n")
    
    # Faylni telegramga yuborish
    file_data = output.getvalue().encode('utf-8')
    output.close()
    
    document = types.BufferedInputFile(file_data, filename="natijalar.csv")
    await message.reply_document(document, caption="Doimobod EDU test natijalari")

@dp.message(Command("clear_results"))
async def clear_results_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    global STUDENT_RESULTS
    STUDENT_RESULTS.clear()
    await message.reply("Barcha natijalar o'chirib tashlandi!")


# --- TALABALAR BUYRUQLARI ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.reply("Doimobod EDU test tekshirish botiga xush kelibsiz!\n\nIltimos, ism va familiyangizni kiriting:")
    await state.set_state(StudentStates.waiting_for_name)

@dp.message(StudentStates.waiting_for_name)
async def get_student_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(student_name=name)
    await message.reply(f"Rahmat, {name}.\n\nEndi javoblaringizni ketma-ket yuboring (Masalan: ABCD...):")
    await state.set_state(StudentStates.waiting_for_answers)

@dp.message(StudentStates.waiting_for_answers)
async def check_answers(message: types.Message, state: FSMContext):
    global STUDENT_RESULTS
    if not CURRENT_TITUL:
        await message.reply("Xatolik: Admin hali kalitlarni kiritgani yo'q! Keyinroq urinib ko'ring.")
        await state.clear()
        return
        
    student_answers = message.text.strip().upper()
    user_data = await state.get_data()
    name = user_data.get("student_name")
    
    # Tekshirish logikasi
    correct_count = 0
    total_questions = len(CURRENT_TITUL)
    
    # Talaba kam yoki ko'p javob yuborgan bo'lsa ham solishtirish
    for i in range(min(len(student_answers), total_questions)):
        if student_answers[i] == CURRENT_TITUL[i]:
            correct_count += 1
            
    # Natijani saqlash
    STUDENT_RESULTS[message.from_user.id] = {
        "name": name,
        "score": correct_count,
        "total": total_questions
    }
    
    await state.clear()
    
    # Talabaga javobini qaytarish
    await message.reply(
        f"<b>Sizning natijangiz:</b>\n\n"
        f"👤 O'quvchi: {name}\n"
        f"✅ To'g'ri javoblar: {correct_count} ta\n"
        f"📊 Umumiy savollar: {total_questions} ta\n"
        f"📈 Foiz: {round((correct_count/total_questions)*100, 1)}%"
    )
    
    # Adminga ham xabar yuborish
    try:
        await bot.send_message(
            ADMIN_ID, 
            f"🔔 <b>Yangi natija:</b>\n\n"
            f"👤 {name} test topshirdi.\n"
            f"🎯 Natija: {correct_count}/{total_questions}"
        )
    except Exception:
        pass

# --- MAIN ---
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

