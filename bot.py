import re
import asyncio
import aiogram
from aiogram.utils import exceptions
from aiogram import Bot, Dispatcher, types
from random import choice
from config import API_TOKEN, WELCOME_MSG, CODE_ADDED_SUCCESS, CODE_ALREADY_EXISTS, NO_CODES_AVAILABLE, \
    RATE_LIMIT_EXCEEDED, NOT_AUTHORIZED, CONFIRM_USAGE_PROMPT, ACTION_CANCELLED, REFERRAL_CODE_MSG, \
    CODE_NOT_FOUND, CODE_DELETED_SUCCESS, INVALID_OR_DUPLICATE_CODE, USED_BUTTON_TEXT, CONFIRM_BUTTON_TEXT, \
    CANCEL_BUTTON_TEXT
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
    await message.answer(WELCOME_MSG)


# Handler for /povo_add command
@dp.message_handler(commands=['povo_add'])
async def add_referral_code_command(message: types.Message):
    user_id = message.from_user.id
    referral_code = message.get_args()

    # Check if the code matches the regex and if the user can add this code
    if re.match(CODE_REGEX, referral_code) and can_add_code(user_id, referral_code):
        if code_exists(referral_code):
            await message.reply(CODE_ALREADY_EXISTS)
        else:
            add_code(referral_code)
            log_user_activity(user_id, 'add', referral_code)  # Log the user's activity
            await message.reply(CODE_ADDED_SUCCESS)
            if message.chat.type == 'supergroup' or message.chat.type == 'group':
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    else:
        await message.reply(INVALID_OR_DUPLICATE_CODE)


@dp.message_handler(commands=['povo_del'])
async def delete_referral_code_command(message: types.Message):
    logger.info(f"/povo_del command received from {message.from_user.id} with arguments {message.get_args()}")
    referral_code = message.get_args()
    codes = [c[1] for c in get_codes()]
    if referral_code in codes:
        referral_id = codes.index(referral_code) + 1  # Assuming `id` values start from 1
        delete_code(referral_id)
        await message.answer(CODE_DELETED_SUCCESS)
    else:
        await message.answer(CODE_NOT_FOUND)


# Handler for /povo command
@dp.message_handler(commands=['povo'])
async def send_referral_code(message: types.Message):
    user_id = message.from_user.id

    if can_get_code(user_id):  # Check if the user can retrieve a code
        codes = get_codes()
        if codes:
            code = choice(codes)
            if code[2] < 10:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton(text=USED_BUTTON_TEXT, callback_data=f"confirmUsage_{code[0]}_{user_id}"))
                sent_message = await message.reply(REFERRAL_CODE_MSG.format(code[1]), reply_markup=keyboard)
                increment_code_usage(code[0])
                log_user_activity(user_id, 'get', code[1])  # Log the user's activity
                await schedule_message_deletion(message.chat.id, sent_message.message_id, 1 * 60 * 60)
            else:
                delete_code(code[0])
                await send_referral_code(message)
        else:
            await message.reply(NO_CODES_AVAILABLE)
    else:
        await message.reply(RATE_LIMIT_EXCEEDED)


# Handlers for the "Used" button press
@dp.callback_query_handler(lambda c: c.data.startswith("confirmUsage"))
async def prompt_confirm_usage(callback_query: types.CallbackQuery):
    _, code_id, request_user_id = callback_query.data.split('_')
    request_user_id = int(request_user_id)

    if callback_query.from_user.id == request_user_id:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text=CONFIRM_BUTTON_TEXT, callback_data=f"confirmYes_{code_id}"),
            types.InlineKeyboardButton(text=CANCEL_BUTTON_TEXT, callback_data=f"confirmNo_{code_id}")
        )
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=CONFIRM_USAGE_PROMPT,
                                    reply_markup=keyboard)
    else:
        await bot.answer_callback_query(callback_query.id, text=NOT_AUTHORIZED)


@dp.callback_query_handler(lambda c: c.data.startswith("confirmYes"))
async def confirm_usage(callback_query: types.CallbackQuery):
    _, code_id = callback_query.data.split('_')
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    # Delete the message
    await bot.delete_message(chat_id, message_id)


@dp.callback_query_handler(lambda c: c.data.startswith("confirmNo"))
async def cancel_usage(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id, text=ACTION_CANCELLED)


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
