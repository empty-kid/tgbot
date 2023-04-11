import logging
import os

import telegram
from telegram.ext import Application, MessageHandler, filters, ConversationHandler, CommandHandler, ContextTypes
from telegram import File, Update, ReplyKeyboardRemove, InlineKeyboardButton, KeyboardButton
from config import TOKEN
import requests
from song_downloader import download_song
from telegram import ReplyKeyboardMarkup

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)

reply_keyboard_with_choice = [[KeyboardButton("/start"),
                               KeyboardButton("/stop")],
                              [KeyboardButton("Песня"),
                               KeyboardButton("Видео")]
                              ]
reply_keyboard = [[KeyboardButton("/start"),
                   KeyboardButton("/stop")]]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
markup_with_choice = ReplyKeyboardMarkup(reply_keyboard_with_choice, one_time_keyboard=False)


async def start(update, context):
    await update.message.reply_text(
        "Перечисление команд бота:\n"
        "/stop - окончить диалог досрочно\n"
        "/start - начать диалог\n"
        f"Что скачать (песню или видео) ?", reply_markup=markup_with_choice)
    return 1


async def first_response(update, context):
    chat_id = update.message.chat_id
    # await context.bot.send_message(chat_id=chat_id, text="hi")
    answer1 = update.message.text
    if "песня" in answer1.lower() or "видео" in answer1.lower():
        await update.message.reply_text(
            f"Отправьте ссылку на видео с песней или видео, которую(ое) хотитие скачать :)", reply_markup=markup)
        if "песня" in answer1.lower():
            return 2
        elif "видео" in answer1.lower():
            return 3
    else:
        await update.message.reply_text("Перечисление команд бота:\n"
                                        "/stop - окончить диалог досрочно\n"
                                        "/start - начать диалог\n"
                                        f"Что скачать (песню или видео) ?", reply_markup=markup_with_choice)
        return 1


async def second_response(update, context):
    video_url = update.message.text
    chat_id = update.message.chat_id
    user = update.message.from_user

    try:
        status = download_song(video_url, user.id)
        if status:
            await update.message.reply_audio(audio=open(status, 'rb'), reply_markup=markup)
            os.remove(status)
        else:
            await update.message.reply_text(f"Не получилось скачать {video_url}", reply_markup=markup)
    except Exception:
        update.message.reply_text(f"Не получилось скачать {video_url}", reply_markup=markup)

    if status != -1:
        # file_info = conte
        await context.bot.send_message(chat_id=chat_id, text="Круто, песня скачалась :)",
                                       reply_markup=markup_with_choice)
        await update.message.reply_text("Перечисление команд бота:\n"
                                        "/stop - окончить диалог досрочно\n"
                                        "/start - начать диалог\n"
                                        f"Что скачать (песню или видео) ?", reply_markup=markup_with_choice)
        return 1
    else:
        await context.bot.send_message(chat_id=chat_id, text="Жаль, песня не скачалась :(",
                                       reply_markup=markup_with_choice)
        await update.message.reply_text("Перечисление команд бота:\n"
                                        "/stop - окончить диалог досрочно\n"
                                        "/start - начать диалог\n"
                                        f"Что скачать (песню или видео) ?", reply_markup=markup_with_choice)
        return 1


async def third_response(update, context):
    video_url = update.message.text
    chat_id = update.message.chat_id
    user = update.message.from_user

    try:
        status = download_song(video_url, user.id, mp4=True)
        if status:
            await update.message.reply_video(video=open(status, 'rb'), reply_markup=markup)
            os.remove(status)
        else:
            await update.message.reply_text(f"Не получилось скачать {video_url}", reply_markup=markup)
    except Exception:
        await update.message.reply_text(f"Не получилось скачать {video_url}", reply_markup=markup)

    if status != -1:
        await update.message.reply_text("Круто, видео скачалось :)",
                                        reply_markup=markup
                                        )
        await update.message.reply_text("Перечисление команд бота:\n"
                                        "/stop - окончить диалог досрочно\n"
                                        "/start - начать диалог\n"
                                        f"Что скачать (песню или видео) ?", reply_markup=markup_with_choice)
        return 1
    else:
        await update.message.reply_text("Жаль, видео не скачалось :(",
                                        reply_markup=markup
                                        )
        await update.message.reply_text("Перечисление команд бота:\n"
                                        "/stop - окончить диалог досрочно\n"
                                        "/start - начать диалог\n"
                                        f"Что скачать (песню или видео) ?", reply_markup=markup_with_choice)
        return 1


async def stop(update, context):
    await update.message.reply_text("Жаль, что вы не хоте продолжать со мной работать :(\n", reply_markup=markup
                                    )
    return 1


def main():
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        # В данном случае — команда /start. Она задаёт первый вопрос.
        entry_points=[CommandHandler('start', start)],

        # Состояние внутри диалога.
        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
            # Функция читает ответ на второй вопрос и завершает диалог.
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, third_response)],
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        },

        fallbacks=[CommandHandler('stop', stop),
                   CommandHandler('start', start),
                   ],
        allow_reentry=True
    )
    application.add_handler(conv_handler)

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
