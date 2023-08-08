import re
import asyncio
import aiogram
from aiogram.utils import exceptions
from aiogram import Bot, Dispatcher, types
from random import choice
from config import API_TOKEN
from database import add_code, get_codes, delete_code, increment_code_usage, code_exists, can_get_code, \
    log_user_activity, can_add_code
import logging

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

CODE_REGEX = r'^[a-zA-Z0-9]+$'  # Only allows alphanumeric characters


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Handler for /start command
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    logger.info(f"/start command received from {message.from_user.id}")
    await message.answer(
        "Welcome! To send your Povo referral code, use the /povo_add command followed by your code. Remember, "
        "the code should contain only Latin letters and Arabic numerals.")


# Handler for /povo_add command
@dp.message_handler(commands=['povo_add'])
def add_referral_code_command(message: types.Message):
    user_id = message.from_user.id
    referral_code = message.get_args()

    # Check if the code matches the regex and if the user can add this code
    if re.match(CODE_REGEX, referral_code) and can_add_code(user_id, referral_code):
        if code_exists(referral_code):
            await message.reply(
                "This referral code already exists. If you continue to duplicate your code, you may be suspended from "
                "using this bot.")
        else:
            add_code(referral_code)
            log_user_activity(user_id, 'add', referral_code)  # Log the user's activity
            await message.reply("Referral code added successfully!")
            if message.chat.type == 'supergroup' or message.chat.type == 'group':
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    else:
        await message.reply("Invalid referral code or you've already added this code.")


@dp.message_handler(commands=['povo_del'])
async def delete_referral_code_command(message: types.Message):
    logger.info(f"/povo_del command received from {message.from_user.id} with arguments {message.get_args()}")
    referral_code = message.get_args()
    codes = [c[1] for c in get_codes()]
    if referral_code in codes:
        referral_id = codes.index(referral_code) + 1  # Assuming `id` values start from 1
        delete_code(referral_id)
        await message.answer("Referral code deleted successfully!")
    else:
        await message.answer("Referral code not found.")


# Handler for /povo command
@dp.message_handler(commands=['povo'])
async def send_referral_code(message: types.Message):
    user_id = message.from_user.id

    if can_get_code(user_id):  # Check if the user can retrieve a code
        codes = get_codes()
        if codes:
            code = choice(codes)
            if code[2] < 10:  # Check if code usage is less than 10
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(text="Used ✅", callback_data=code[0]))
                sent_message = await message.reply(f"Here's your referral code: {code[1]}", reply_markup=keyboard)
                increment_code_usage(code[0])
                await schedule_message_deletion(message.chat.id, sent_message.message_id, 1 * 60 * 60)
                log_user_activity(user_id, 'get', code[1])  # Log the user's activity
            else:
                delete_code(code[0])
                await send_referral_code(message)
        else:
            await message.reply("No referral codes available at the moment.")
    else:
        await message.reply("You can't retrieve a referral code more than once in an hour.")


# Handler for the "Used" button press
@dp.callback_query_handler(lambda c: True)
async def button_used(callback_query: types.CallbackQuery):
    logger.info(f"Button used by {callback_query.from_user.id} on message {callback_query.message.message_id}")
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    if callback_query.message.reply_to_message is not None and callback_query.from_user.id == callback_query.message.reply_to_message.from_user.id:
        # Delete the message
        await bot.delete_message(chat_id, message_id)

    else:
        # Ignore button press from other users
        await bot.answer_callback_query(callback_query.id, text="You are not authorized to use this button.")


# Function to schedule message deletion after a specified time
async def schedule_message_deletion(chat_id: int, message_id: int, delay: int):
    try:
        await asyncio.sleep(delay)
        await bot.delete_message(chat_id, message_id)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        # Handle the case where the message has already been deleted
        pass


# Handler for /list command
@dp.message_handler(commands=['list'])
async def list_codes_command(message: types.Message):
    logger.info(f"/list command received from {message.from_user.id}")
    # Fetch all codes from the database
    codes = get_codes()

    # Check if there are any codes
    if codes:
        # Begin crafting the response message
        response = "Here are all the referral codes:\n"

        # Iterate over all codes and add them to the response message
        for code in codes:
            response += f"ID: {code[0]}, Code: {code[1]}, Usage count: {code[2]}\n"

        # Send the response message
        await message.answer(response)
    else:
        await message.answer("No referral codes in the database.")


# Start polling
if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)