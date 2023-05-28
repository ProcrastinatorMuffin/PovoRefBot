import re
from aiogram import Bot, Dispatcher, types
from random import choice
from config import API_TOKEN
from database import add_code, get_codes, delete_code, increment_code_usage

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

CODE_REGEX = r'^[a-zA-Z0-9]+$'  # Only allows alphanumeric characters


# Handler for /start command
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Welcome! Please send your Povo referral code. Remember, the code should contain only "
                         "Latin letters and Arabic numerals.")


# Handler for /stop command
@dp.message_handler(commands=['stop'])
async def stop_command(message: types.Message):
    await message.answer("Stopping bot...")


# Handler for /povo_add command
@dp.message_handler(commands=['povo_add'])
async def add_referral_code_command(message: types.Message):
    referral_code = message.get_args()
    if re.match(CODE_REGEX, referral_code):
        add_code(referral_code)
        await message.answer("Referral code added successfully!")
    else:
        await message.answer("Invalid referral code. The code should contain only Latin letters and Arabic numerals.")


# Handler for private chat referral code submission
@dp.message_handler(content_types=types.ContentType.TEXT, chat_type=types.ChatType.PRIVATE)
async def add_referral_code(message: types.Message):
    if re.match(CODE_REGEX, message.text):
        add_code(message.text)
        await message.answer("Referral code added successfully!")
    else:
        await message.answer("Invalid referral code. The code should contain only Latin letters and Arabic numerals.")


# Handler for /povo command
@dp.message_handler(commands=['povo'])
async def send_referral_code(message: types.Message):
    # Get all codes from the database
    codes = get_codes()

    if codes:
        # Select a random code
        code = choice(codes)
        if code[2] < 10:  # Check if code usage is less than 10
            await message.answer(f"Here's your referral code: {code[1]}")
            increment_code_usage(code[0])
        else:
            delete_code(code[0])
            return await send_referral_code(message)
    else:
        await message.answer("No referral codes available at the moment.")


# Start polling
if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
