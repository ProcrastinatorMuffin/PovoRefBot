import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read API_TOKEN from environment variables
API_TOKEN = os.getenv('API_TOKEN')
DB_NAME = 'referral_codes.db'

# General Bot Responses
WELCOME_MSG = "Привет! Отправь мне свой реферальный код командой /add. Используй /povo, чтобы получить случайный " \
              "реферальный код."
CODE_ADDED_SUCCESS = "Ваш реферальный код успешно добавлен!"
CODE_ALREADY_EXISTS = "Такой реферальный код уже существует!"
NO_CODES_AVAILABLE = "В данный момент реферальные коды отсутствуют."
RATE_LIMIT_EXCEEDED = "Воспользуйтесь кодом, который вы запросили ранее."
NOT_AUTHORIZED = "У вас недостаточно прав для использования этой команды."
CONFIRM_USAGE_PROMPT = "Вы уверены, что хотите пометить этот код как использованный? Сообщение с кодом будет " \
                       "безвозвратно удалено."
ACTION_CANCELLED = "Действие отменено."
REFERRAL_CODE_MSG = "Вот ваш реферальный код: {}"
CODE_NOT_FOUND = "Реферальный код не найден."
CODE_DELETED_SUCCESS = "Реферальный код успешно удален!"
INVALID_OR_DUPLICATE_CODE = "Реферальный код недействителен или уже был добавлен ранее"

# Inline Keyboard Buttons (keeping these the same as they contain universal symbols)
USED_BUTTON_TEXT = "Я использовал(а) код ✅"
CONFIRM_BUTTON_TEXT = "Да ✅"
CANCEL_BUTTON_TEXT = "Нет ❌"

