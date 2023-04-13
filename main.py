import logging
import os
import telegram
from telegram.ext import Application, MessageHandler, filters, ConversationHandler, CommandHandler, ContextTypes, \
    Updater
from telegram import File, Update, ReplyKeyboardRemove, InlineKeyboardButton, KeyboardButton
from config import TOKEN
import requests
from markups.markup_profile import markup_profile
from markups.markup_with_choice_and_auth import markup_with_choice_and_auth
from markups.markup_choice import markup_choice
from markups.markup import markup
from markups.markup_with_choice import markup_with_choice
from markups.markup_wth_choice_and_reg import markup_with_choice_and_reg
from misc.check_password_syms import check_password_syms
from song_downloader import download_song
from telegram import ReplyKeyboardMarkup
from data import db_session
from data.users import User
from data.songs import Song
from data.videos import Video
from werkzeug.security import generate_password_hash, check_password_hash
from user_media_db_funcs.add_song_to_user import add_song_to_user_in_db
from user_media_db_funcs.add_vid_to_user import add_vid_to_user_in_db
from user_media_db_funcs.get_all_user_songs import get_all_user_songs
from user_media_db_funcs.get_all_user_vids import get_all_user_vids
from default_answers import ans1, ans2

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# запуск бд
db_session.global_init("db/database.db")


async def start(update, context):
    user_id = update.message.from_user.id
    db_sess = db_session.create_session()
    if db_sess.query(User.user_id).all():
        if user_id in db_sess.query(User.user_id).all()[0]:
            await update.message.reply_text(
                ans1, reply_markup=markup_with_choice_and_auth, parse_mode="HTML")
            return 1
    await update.message.reply_text(
        ans1, reply_markup=markup_with_choice_and_reg, parse_mode='HTML')
    return 1


async def first_response(update, context):
    chat_id = update.message.chat_id
    # await context.bot.send_message(chat_id=chat_id, text="hi")
    answer1 = update.message.text
    if "песня" in answer1.lower() or "видео" in answer1.lower():
        await update.message.reply_text(
            f"Отправьте <b>Youtube-ссылку</b> на видео с песней или видео, которую(ое) хотитие скачать :)",
            reply_markup=markup
            , parse_mode="HTML")
        if "песня" in answer1.lower():
            return 2
        elif "видео" in answer1.lower():
            return 3
    else:
        await update.message.reply_text(ans1, reply_markup=markup_with_choice, parse_mode="HTML")
        return 1


async def second_response(update, context):
    video_url = update.message.text
    chat_id = update.message.chat_id
    useri = update.message.from_user
    user_id = update.message.from_user.id
    try:
        status = download_song(video_url, useri.id)
        if status and status != -1:
            # добавление песни
            add_song_to_user_in_db(video_url, user_id)
            await update.message.reply_audio(audio=open(status, 'rb'), reply_markup=markup, parse_mode="HTML")
            os.remove(status)
        else:
            await update.message.reply_text(f"Не получилось скачать {video_url}", reply_markup=markup,
                                            parse_mode="HTML")
    except Exception:
        update.message.reply_text(f"Не получилось скачать {video_url}", reply_markup=markup, parse_mode="HTML")

    if status != -1:
        # file_info = conte
        await context.bot.send_message(chat_id=chat_id, text="Круто, песня скачалась :)",
                                       reply_markup=markup_with_choice, parse_mode="HTML")
        await update.message.reply_text(ans1, reply_markup=markup_with_choice, parse_mode="HTML")
        return 1
    else:
        await context.bot.send_message(chat_id=chat_id, text="Жаль, песня не скачалась :(",
                                       reply_markup=markup_with_choice, parse_mode="HTML")
        await update.message.reply_text(ans1, reply_markup=markup_with_choice, parse_mode="HTML")
        return 1


async def third_response(update, context):
    video_url = update.message.text
    chat_id = update.message.chat_id
    useri = update.message.from_user
    user_id = update.message.from_user.id
    try:
        status = download_song(video_url, useri.id, mp4=True)
        if status:
            # добавляем видео
            add_vid_to_user_in_db(video_url, user_id)
            await update.message.reply_video(video=open(status, 'rb'), reply_markup=markup, parse_mode="HTML")
            os.remove(status)
        else:
            await update.message.reply_text(f"Не получилось скачать {video_url}", reply_markup=markup,
                                            parse_mode="HTML")
    except Exception:
        await update.message.reply_text(f"Не получилось скачать {video_url}", reply_markup=markup, parse_mode="HTML")

    if status != -1:
        await update.message.reply_text("Круто, видео скачалось :)",
                                        reply_markup=markup, parse_mode="HTML"
                                        )
        await update.message.reply_text(ans1, reply_markup=markup_with_choice, parse_mode="HTML")
        return 1
    else:
        await update.message.reply_text("Жаль, видео не скачалось :(",
                                        reply_markup=markup, parse_mode="HTML"
                                        )
        await update.message.reply_text(ans1, reply_markup=markup_with_choice, parse_mode="HTML")
        return 1


async def stop(update, context):
    await update.message.reply_text("Жаль, что вы не хоте продолжать со мной работать :(\n", reply_markup=markup
                                    , parse_mode="HTML")
    return 1


async def registrate(update, context):
    await update.message.reply_text("<b>Регистрация!</b>\n"
                                    "Введите ваше имя!", reply_markup=markup, parse_mode="HTML")
    return 4


async def get_name(update, context):
    context.user_data['username'] = update.message.text
    chat_id = update.message.chat_id
    await update.message.reply_text("Придумайте и введите ваш пароль!", reply_markup=markup, parse_mode="HTML")
    await context.bot.send_message(chat_id=chat_id, text="В пароле должно быть <em>не менее 8 символов</em>",
                                   parse_mode="HTML")
    await context.bot.send_message(chat_id=chat_id, text="В пароле должны быть <em>цифры, заглавные и маленькие "
                                                         "буквы</em>", parse_mode="HTML")
    await context.bot.send_message(chat_id=chat_id, text="В пароле <em>не должно быть русских букв</em>",
                                   parse_mode="HTML")
    return 5


async def get_password(update, context):
    password = update.message.text
    is_good_passw = check_password_syms(password)
    chat_id = update.message.chat_id
    if is_good_passw:
        context.user_data['user_hashed_password'] = generate_password_hash(update.message.text)
        await update.message.reply_text("<b>Вы готовы зарегестрироваться ?</b>", reply_markup=markup_choice,
                                        parse_mode="HTML")
        return 6
    else:
        await context.bot.send_message(chat_id=chat_id, text="<b>Вы придумали плохой пароль!</b>", parse_mode="HTML")
        await context.bot.send_message(chat_id=chat_id, text="Ваша регистрация отменяется!", parse_mode="HTML")
        await update.message.reply_text(ans1, reply_markup=markup_with_choice_and_reg, parse_mode="HTML")
        return 1


async def confirm_reg(update, context):
    chat_id = update.message.chat_id
    user_choice = update.message.text
    context.user_data['user_id'] = update.message.from_user.id
    if "да" in user_choice.lower():
        if "да" in user_choice.lower():
            user = User()
            user.user_id = context.user_data['user_id']
            user.hashed_password = context.user_data['user_hashed_password']
            user.name = context.user_data['username']
            db_sess = db_session.create_session()
            db_sess.add(user)
            db_sess.commit()
            context.user_data.clear()
            await context.bot.send_message(chat_id=chat_id, text="<b>Вы зарегистрировались!</b>", parse_mode="HTML")
            await update.message.reply_text(
                ans1, reply_markup=markup_with_choice_and_auth, parse_mode="HTML")
    else:
        await update.message.reply_text(
            ans1, reply_markup=markup_with_choice_and_reg, parse_mode="HTML")
    return 1


async def profile(update, context):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=chat_id, text="Вы находитесь в своем профиле !", parse_mode="HTML")
    await update.message.reply_text(
        ans2,
        reply_markup=markup_profile, parse_mode="HTML")
    return 7


async def analyze_user_choice(update, context):
    user_choice = update.message.text
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    if "назад" in user_choice.lower():
        await update.message.reply_text(
            ans1, reply_markup=markup_with_choice_and_auth, parse_mode="HTML")
        return 1
    elif "все песни" in user_choice.lower():
        await update.message.reply_text(
            "<b>Ниже перечислены все скачанные вами песни !</b>",
            reply_markup=markup_profile, parse_mode="HTML")
        user_songs = get_all_user_songs(user_id=user_id)
        for song in user_songs:
            await context.bot.send_message(chat_id=chat_id, text=f"{song.link}\n"
                                                                 f"дата загрузки :{song.created_date}\n",
                                           parse_mode="HTML")
        await context.bot.send_message(chat_id=chat_id, text="Вы находитесь в своем профиле !", parse_mode="HTML")
        await update.message.reply_text(ans2,
                                        reply_markup=markup_profile, parse_mode="HTML"
                                        )
        return 7
    elif "все видео" in user_choice.lower():
        await update.message.reply_text(
            "<b>Ниже перечислены все скачанные вами видео !</b>",
            reply_markup=markup_profile, parse_mode="HTML")
        user_vids = get_all_user_vids(user_id=user_id)
        for vid in user_vids:
            await context.bot.send_message(chat_id=chat_id, text=f"{vid.link}\n"
                                                                 f"дата загрузки :{vid.created_date}\n",
                                           parse_mode="HTML")
        await context.bot.send_message(chat_id=chat_id, text="Вы находитесь в своем профиле !", parse_mode="HTML")
        await update.message.reply_text(ans2,
                                        reply_markup=markup_profile, parse_mode="HTML"
                                        )
        return 7
    elif "удалить профиль" in user_choice.lower():
        await context.bot.send_message(chat_id=chat_id, text="<b>Подтвердите свой нынешний пароль!</b>",
                                       reply_markup=markup_profile, parse_mode="HTML"
                                       )
        return 8
    elif "сменить пароль" in user_choice.lower():
        await context.bot.send_message(chat_id=chat_id, text="<b>Подтвердите свой нынешний пароль!</b>",
                                       reply_markup=markup_profile, parse_mode="HTML"
                                       )
        return 10


async def confirm_account_del(update, context):
    password = update.message.text
    db_sess = db_session.create_session()
    user_idx = update.message.from_user.id
    curr_User = db_sess.query(User).filter((User.user_id == user_idx)).first()
    check_password_hash(curr_User.hashed_password, password)
    chat_id = update.message.chat_id
    if check_password_hash(curr_User.hashed_password, password):
        await update.message.reply_text("<b>Вы действительно хотите удалить свол профиль ?</b>",
                                        reply_markup=markup_choice, parse_mode="HTML")
        return 9
    else:
        await context.bot.send_message(chat_id=chat_id, text="<b>Пароли не свопадают!</b>", parse_mode="HTML")
        await context.bot.send_message(chat_id=chat_id, text="Вы находитесь в своем профиле !", parse_mode="HTML")
        await update.message.reply_text(ans2,
                                        reply_markup=markup_profile, parse_mode="HTML"
                                        )
        return 7


async def delete_account(update, context):
    user_choice = update.message.text
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if "да" in user_choice.lower():
        if "да" in user_choice.lower():
            db_sess = db_session.create_session()
            db_sess.query(Song).filter(Song.user_id == user_id).delete()
            db_sess.query(Video).filter(Video.user_id == user_id).delete()
            db_sess.query(User).filter(User.user_id == user_id).delete()
            db_sess.commit()
            await context.bot.send_message(chat_id=chat_id, text="<b>Ваш профиль успешно удален!</b>",
                                           parse_mode="HTML")
            await update.message.reply_text(
                ans1, reply_markup=markup_with_choice_and_reg, parse_mode="HTML")
            return 1
    else:
        await context.bot.send_message(chat_id=chat_id, text="<b>Хорошо, ничего удалять не будем :)</b>",
                                       parse_mode="HTML")
        await update.message.reply_text(
            ans2,
            reply_markup=markup_profile, parse_mode="HTML")
        return 7


async def password_change_diag(update, context):
    password = update.message.text
    db_sess = db_session.create_session()
    user_idx = update.message.from_user.id
    curr_User = db_sess.query(User).filter((User.user_id == user_idx)).first()
    check_password_hash(curr_User.hashed_password, password)
    chat_id = update.message.chat_id
    if check_password_hash(curr_User.hashed_password, password):
        await context.bot.send_message(chat_id=chat_id, text="Отлично! Пароли свопадают!", parse_mode="HTML")
        await update.message.reply_text("<b>Придумайте и Введите новый пароль!</b>",
                                        reply_markup=markup_profile, parse_mode="HTML")
        return 11
    else:
        await context.bot.send_message(chat_id=chat_id, text="<b>Пароли не свопадают!</b>", parse_mode="HTML")
        await context.bot.send_message(chat_id=chat_id, text="Вы находитесь в своем профиле !", parse_mode="HTML")
        await update.message.reply_text(ans2,
                                        reply_markup=markup_profile, parse_mode="HTML"
                                        )
        return 7


async def password_change(update, context):
    new_password = update.message.text
    is_good_passw = check_password_syms(new_password)
    chat_id = update.message.chat_id
    if is_good_passw:
        new_password_hash = generate_password_hash(new_password)
        user_id = update.message.from_user.id
        db_sess = db_session.create_session()
        curr_user = db_sess.query(User).filter((User.user_id == user_id)).first()
        curr_user.hashed_password = new_password_hash
        db_sess.add(curr_user)
        db_sess.commit()
        await context.bot.send_message(chat_id=chat_id, text="<b>Вы успешно сменили пароль!</b>", parse_mode="HTML")
        await context.bot.send_message(chat_id=chat_id, text="Вы находитесь в своем профиле !", parse_mode="HTML")
        await update.message.reply_text(ans2, reply_markup=markup_profile, parse_mode="HTML")
        return 7
    else:
        await context.bot.send_message(chat_id=chat_id, text="<b>Вы придумали плохой пароль!</b>", parse_mode="HTML")
        await context.bot.send_message(chat_id=chat_id, text="Смена пароля отменяется!", parse_mode="HTML")
        await update.message.reply_text(ans2, reply_markup=markup_profile, parse_mode="HTML")
        return 7


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
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_reg)],
            7: [MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_user_choice)],
            8: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_account_del)],
            9: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_account)],
            10: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_change_diag)],
            11: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_change)],
        },

        fallbacks=[CommandHandler('stop', stop),
                   CommandHandler('start', start),
                   CommandHandler('registrate', registrate),
                   CommandHandler('profile', profile)
                   ],
        allow_reentry=True
    )

    application.add_handler(conv_handler)

    # Запускаем приложение.
    application.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
