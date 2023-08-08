# Standard library imports
import re
import asyncio
import logging
from random import choice
from logging.handlers import RotatingFileHandler

# Third-party package imports
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions

# Local application imports
from config import (
    API_TOKEN, WELCOME_MSG, CODE_ADDED_SUCCESS, CODE_ALREADY_EXISTS, NO_CODES_AVAILABLE,
    RATE_LIMIT_EXCEEDED, NOT_AUTHORIZED, CONFIRM_USAGE_PROMPT, ACTION_CANCELLED, REFERRAL_CODE_MSG,
    CODE_NOT_FOUND, CODE_DELETED_SUCCESS, INVALID_OR_DUPLICATE_CODE, USED_BUTTON_TEXT, CONFIRM_BUTTON_TEXT,
    CANCEL_BUTTON_TEXT
)
from database import (
    add_code, get_codes, delete_code, increment_code_usage, code_exists, can_get_code,
    log_user_activity, can_add_code
)

# Constants
CODE_REGEX = r'^[a-zA-Z0-9]+$'  # Only allows alphanumeric characters

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Set up logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=3)  # 5MB per log file, 3 backup logs
log_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    """
    Handler for the /start command.

    When a user starts a conversation with the bot or sends the /start command, this function responds
    with a welcome message to the user.

    Parameters:
    - message (types.Message): The incoming message object from the user.

    Returns:
    - None: Sends a welcome message to the user.
    """

    # Log the receipt of the /start command from the user
    logger.info(f"/start command received from user: {message.from_user.id} (Username: {message.from_user.username})")

    # Respond to the user with the welcome message
    await message.answer(WELCOME_MSG)


@dp.message_handler(commands=['povo_add'])
async def add_referral_code_command(message: types.Message):
    """
    Handler function for /povo_add command. This function allows users to add their referral codes.

    Args:
        message (types.Message): The incoming message object from the user.
    """

    # Log the receipt of the /povo_add command from a specific user
    logger.info(f"Received /povo_add command from user {message.from_user.id}")

    # Extract user ID and the provided referral code argument from the message
    user_id = message.from_user.id
    referral_code = message.get_args()

    # Validate the format of the referral code using regex
    if re.match(CODE_REGEX, referral_code):
        logger.debug(f"Referral code {referral_code} from user {user_id} passed the regex validation.")

        # Check if the user is eligible to add this particular code
        if can_add_code(user_id, referral_code):
            logger.debug(f"User {user_id} is eligible to add referral code {referral_code}.")

            # Check if the provided referral code already exists in the database
            if code_exists(referral_code):
                logger.warning(f"Referral code {referral_code} from user {user_id} already exists.")
                await message.reply(CODE_ALREADY_EXISTS)
            else:
                # Add the referral code to the database
                add_code(referral_code)
                logger.info(f"Referral code {referral_code} added to the database by user {user_id}.")

                # Log the user's activity for adding the referral code
                log_user_activity(user_id, 'add', referral_code)

                # Send a success response to the user
                await message.reply(CODE_ADDED_SUCCESS)

                # If the chat is a group or supergroup, delete the original command message to keep chat clean
                if message.chat.type == 'supergroup' or message.chat.type == 'group':
                    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                    logger.info(f"Deleted /povo_add command message from user {user_id} in chat {message.chat.id}.")
        else:
            logger.warning(f"User {user_id} tried to add an invalid or duplicate referral code: {referral_code}.")
            await message.reply(INVALID_OR_DUPLICATE_CODE)
    else:
        logger.warning(f"Referral code {referral_code} from user {user_id} failed the regex validation.")
        await message.reply(INVALID_OR_DUPLICATE_CODE)


@dp.message_handler(commands=['povo_del'])
async def delete_referral_code_command(message: types.Message):
    """
    Handler function for /povo_del command. This function allows users to delete a specific referral code.

    Args:
        message (types.Message): The incoming message object from the user.
    """

    # Log the receipt of the /povo_del command from a specific user
    logger.info(f"/povo_del command received from {message.from_user.id} with arguments {message.get_args()}")

    # Extract the provided referral code argument from the message
    referral_code = message.get_args()

    # Retrieve all existing referral codes
    codes = [c[1] for c in get_codes()]

    # Check if the provided referral code exists in the database
    if referral_code in codes:
        referral_id = codes.index(referral_code) + 1  # Assuming `id` values start from 1
        logger.debug(f"Referral code {referral_code} found in database with ID {referral_id}. Preparing to delete.")

        # Delete the referral code from the database
        delete_code(referral_id)
        logger.info(f"Referral code {referral_code} with ID {referral_id} deleted from database.")

        # Send a success response to the user
        await message.answer(CODE_DELETED_SUCCESS)
    else:
        logger.warning(f"User {message.from_user.id} tried to delete non-existent referral code {referral_code}.")

        # Inform the user that the code was not found
        await message.answer(CODE_NOT_FOUND)


@dp.message_handler(commands=['povo'])
async def send_referral_code(message: types.Message):
    """
    Handler function for /povo command. This function provides users with a referral code.

    Args:
        message (types.Message): The incoming message object from the user.
    """

    # Log the receipt of the /povo command from a specific user
    logger.info(f"Received /povo command from user {message.from_user.id}")

    # Extract the user ID from the incoming message
    user_id = message.from_user.id

    # Check if the user is eligible to retrieve a code
    if can_get_code(user_id):
        logger.info(f"User {user_id} is eligible to get a referral code.")

        # Get all available referral codes
        codes = get_codes()

        if codes:
            # Randomly select a referral code from the available codes
            code = choice(codes)

            # Check if the selected code's usage is below the threshold
            if code[2] < 10:
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton(text=USED_BUTTON_TEXT,
                                               callback_data=f"confirmUsage_{code[0]}_{user_id}"))

                # Send the selected referral code to the user
                sent_message = await message.reply(REFERRAL_CODE_MSG.format(code[1]), reply_markup=keyboard)

                # Increment the usage count of the selected code
                increment_code_usage(code[0])

                # Log the user's activity
                log_user_activity(user_id, 'get', code[1])

                # Schedule the sent message for deletion after 1 hour
                await schedule_message_deletion(message.chat.id, sent_message.message_id, 1 * 60 * 60)
            else:
                # If the selected code's usage is above the threshold, delete it and send a new one to the user
                logger.debug(f"Referral code {code[1]} exceeded usage limit. Deleting and retrying.")
                delete_code(code[0])
                await send_referral_code(message)
        else:
            # Inform the user that there are no available referral codes
            logger.warning(f"No referral codes available for user {user_id}.")
            await message.reply(NO_CODES_AVAILABLE)
    else:
        # Inform the user that they have exceeded the rate limits
        logger.warning(f"User {user_id} exceeded rate limits.")
        await message.reply(RATE_LIMIT_EXCEEDED)


@dp.callback_query_handler(lambda c: c.data.startswith("confirmUsage"))
async def prompt_confirm_usage(callback_query: types.CallbackQuery):
    """
    Handler function for callback queries that start with "confirmUsage".
    This function prompts the user to confirm the usage of a referral code.

    Args:
        callback_query (types.CallbackQuery): The incoming callback query object from the user.
    """

    # Extract the code_id and request_user_id from the callback data
    _, code_id, request_user_id = callback_query.data.split('_')
    request_user_id = int(request_user_id)

    # Log the receipt of the callback query for confirmation
    logger.info(f"Received confirmUsage callback from user {callback_query.from_user.id} for code {code_id}")

    # Check if the callback query is from the same user who requested the referral code
    if callback_query.from_user.id == request_user_id:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text=CONFIRM_BUTTON_TEXT, callback_data=f"confirmYes_{code_id}"),
            types.InlineKeyboardButton(text=CANCEL_BUTTON_TEXT, callback_data=f"confirmNo_{code_id}")
        )

        # Edit the message to prompt the user for confirmation
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=CONFIRM_USAGE_PROMPT,
                                    reply_markup=keyboard)
    else:
        # If the callback query is not from the same user, inform them that they are not authorized
        logger.warning(f"Unauthorized access attempt by user {callback_query.from_user.id} for code {code_id}")
        await bot.answer_callback_query(callback_query.id, text=NOT_AUTHORIZED)


@dp.callback_query_handler(lambda c: c.data.startswith("confirmYes"))
async def confirm_usage(callback_query: types.CallbackQuery):
    """
    Handler function for callback queries that start with "confirmYes".
    This function confirms the usage of a referral code and deletes the confirmation message.

    Args:
        callback_query (types.CallbackQuery): The incoming callback query object from the user.
    """

    # Extract the code_id from the callback data
    _, code_id = callback_query.data.split('_')
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id

    # Log the receipt of the callback query for confirmation
    logger.info(f"Received confirmYes callback from user {callback_query.from_user.id} for code {code_id}")

    # Delete the confirmation message after the usage has been confirmed
    await bot.delete_message(chat_id, message_id)
    logger.info(f"Deleted confirmation message in chat {chat_id} for code {code_id}")


@dp.callback_query_handler(lambda c: c.data.startswith("confirmNo"))
async def cancel_usage(callback_query: types.CallbackQuery):
    """
    Handler function for callback queries that start with "confirmNo".
    This function answers the callback query with a cancellation message.

    Args:
        callback_query (types.CallbackQuery): The incoming callback query object from the user.
    """

    # Log the receipt of the callback query indicating the user's decision to cancel
    logger.info(f"Received confirmNo callback from user {callback_query.from_user.id}. Action is cancelled.")

    # Answer the callback query, notifying the user of the cancellation
    await bot.answer_callback_query(callback_query.id, text=ACTION_CANCELLED)
    logger.info(f"Answered callback query for user {callback_query.from_user.id} with cancellation message.")


async def schedule_message_deletion(chat_id: int, message_id: int, delay: int):
    """
    Schedule the deletion of a specific message after a given delay.

    Args:
        chat_id (int): The ID of the chat where the message is located.
        message_id (int): The ID of the message to be deleted.
        delay (int): The time (in seconds) after which the message should be deleted.
    """

    # Log the initialization of the scheduled deletion
    logger.info(f"Scheduling deletion of message {message_id} in chat {chat_id} after {delay} seconds.")

    try:
        await asyncio.sleep(delay)

        # Attempt to delete the message
        await bot.delete_message(chat_id, message_id)
        logger.info(f"Successfully deleted message {message_id} in chat {chat_id} after the scheduled delay.")

    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        # Handle the case where the message has already been deleted
        logger.warning(f"Failed to delete message {message_id} in chat {chat_id} as it was not found.")
        pass


@dp.message_handler(commands=['list'])
async def list_codes_command(message: types.Message):
    """
    Handler for the /list command. Lists all referral codes stored in the database.

    Args:
        message (types.Message): The incoming Telegram message object.
    """

    # Log the receipt of the /list command
    logger.info(f"/list command received from {message.from_user.id}")

    # Fetch all codes from the database
    codes = get_codes()
    logger.info(f"Fetched {len(codes)} codes from the database.")

    # Check if there are any codes
    if codes:
        # Begin crafting the response message
        response = "Here are all the referral codes:\n"

        # Iterate over all codes and add them to the response message
        for code in codes:
            response += f"ID: {code[0]}, Code: {code[1]}, Usage count: {code[2]}\n"

        # Send the response message
        await message.answer(response)
        logger.info(f"Sent list of codes to {message.from_user.id}")
    else:
        # Inform the user that there are no codes
        await message.answer("No referral codes in the database.")
        logger.warning(f"No codes found in the database.")


if __name__ == '__main__':
    """
    Main execution block. If this script is run directly (not imported),
    it initiates the bot's polling process to actively check for and respond to incoming messages.
    """

    # Import necessary modules and components for bot execution
    from aiogram import executor

    # Log the start of the bot's execution
    logger.info("Starting the bot's polling process...")

    # Start the bot's polling process to check for incoming messages
    # `skip_updates=True` skips any pending updates on startup (e.g., missed messages while bot was off)
    executor.start_polling(dp, skip_updates=True)

    # Log the successful startup of the bot
    logger.info("Bot started successfully and is now polling for messages.")

