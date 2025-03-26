import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from database import Database
import httpx

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройка прокси для OpenAI
proxies = {
    "http": os.getenv('HTTP_PROXY'),
    "https": os.getenv('HTTPS_PROXY')
}

# Инициализация клиентов
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    http_client=httpx.Client(proxies=proxies)
)
db = Database()

# Базовая информация о компании
COMPANY_INFO = """
KnyazService — это надёжный партнёр в мире Telegram-маркетинга, с более чем 5-летним опытом в сфере автоматизированной рекламы. Сервис помогает компаниям и частным лицам продвигать свои товары и услуги через интеллектуальную рассылку сообщений в Telegram-чаты, охватывая десятки тематик и направлений.

Основные возможности:
- Автоматическая рассылка сообщений в Telegram-чаты без ручного труда
- Индивидуальный подбор чатов под каждое объявление
- Круглосуточная рассылка по расписанию (каждый час)
- Premium-аккаунты для стабильной работы
- Автоответ от аккаунта-рассыльщика
- Реальные отчёты о рассылке в режиме реального времени
- Поддержка интеграций с внешними системами (CRM и др.)
- Аналитика и эффективность
- Персонализация сообщений
- Работа с отзывами

Тематики чатов:
- Реклама
- США (товары, работа, недвижимость)
- Услуги
- Товары
- Майнинг
- Вакансии
- Бизнес
- Блогеры
- SMM
- Табачные изделия
- Арбитраж трафика
- Беттинг
- Чаты ЖК
- Строительство
- Перевозки
- Авто
- Теневые услуги
- Эскорт
- Юридические услуги и ООО
- Кредиты
- Клиентские базы
- Недвижимость
- Аренда
- Фриланс
- Нетворкинг
- Барахолки

Тарифы на рассылку:
- 1 неделя — 2900 рублей
- 2 недели — 5600 рублей
- 1 месяц — 9900 рублей
- 2 месяца — 16900 рублей
- 4 месяца — 27900 рублей
- 6 месяцев — 39000 рублей
- 1 год — 55000 рублей

Оплата возможна в рублях и криптовалюте.
Старт рассылки — в течение 3 часов после оплаты.

Дополнительные условия:
- Рассылка осуществляется только в релевантные по тематике чаты, подобранные вручную
- В случае блокировки — повторная отправка в этот чат не выполняется
- Сервис может корректировать содержание объявления для соответствия требованиям Telegram и конкретных чатов
- Логи рассылки хранятся 2 недели, сообщения удаляются через 72 часа после завершения кампании
- Ссылки на чаты доступны только в логах в личном кабинете
- Компания открыта к индивидуальным предложениям для оптовых клиентов
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_message = (
        "Привет! Я бот-помощник нашей компании. "
        "Я могу ответить на вопросы о наших товарах, "
        "условиях доставки, скидках и оформлении заказа. "
        "Как я могу вам помочь?"
    )
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик входящих сообщений"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    message = update.message.text

    # Получаем историю сообщений
    recent_messages = db.get_recent_messages(user_id)
    
    # Формируем контекст для OpenAI
    conversation_history = ""
    for msg, resp, _ in reversed(recent_messages):
        conversation_history += f"User: {msg}\nAssistant: {resp}\n"

    # Формируем промпт
    prompt = f"""
    {COMPANY_INFO}

    История диалога:
    {conversation_history}

    Текущий вопрос пользователя: {message}

    Пожалуйста, ответьте на вопрос пользователя, используя информацию о компании.
    """

    try:
        # Получаем ответ от OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Вы - дружелюбный помощник компании, который отвечает на вопросы клиентов."},
                {"role": "user", "content": prompt}
            ]
        )
        
        bot_response = response.choices[0].message.content

        # Сохраняем сообщение и ответ в базу данных
        db.save_message(user_id, username, message, bot_response)

        # Отправляем ответ пользователю
        await update.message.reply_text(bot_response)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже."
        )

def main():
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
