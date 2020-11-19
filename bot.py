import json
import logging
import os
import datetime as dt
import requests
from time import sleep

from collections import OrderedDict

import telebot
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar

info = OrderedDict()
edit_record_flag = False
LSTEP = {'y': 'год', 'm': 'месяц', 'd': 'день'}
PARAMS = ["ФИО", "Дата рождения", "Пол", "Мобильный телефон"]
COLUMNS = ["chat_id", "name", "birth_date", "gender", "mobile_phone"]

with open("config.json") as json_file:
    config = json.load(json_file)
    bot = telebot.TeleBot(config["TOKEN"])
    logging.info(f"telebot with TOKEN = {config['TOKEN']} has been created")


class MyStyleCalendar(DetailedTelegramCalendar):
    # previous and next buttons style. they are emoji now!
    prev_button = "⬅"
    next_button = "➡"
    # you do not want empty cells when month and year are being selected
    empty_month_button = ""
    empty_year_button = ""


def create_inline_keyboard_button(text, callback_data):
    button = types.InlineKeyboardButton(text=text, callback_data=callback_data)
    return button


def get_start_message():
    msg = (
            "Этот чат поможет Вам записаться на курс!\n"
            + "Введите следующие команды:\n"
            + "1. /register - для записи на курс\n"
            + "2. /links - для получения дополнительных ссылок\n"
            + "3. /images - для получения фотографии с собакой\n"
    )

    return msg


@bot.message_handler(commands=["start"])
def start_message(message):
    chat_id = message.chat.id
    logging.info("/start command")

    msg_to_user = get_start_message()
    bot.send_message(chat_id, msg_to_user, parse_mode="HTML")


@bot.message_handler(commands=["register"])
def register_window(message):
    chat_id = message.chat.id
    logging.info("/register command")

    info[str(chat_id)] = []

    msg_to_user = (
        "Для записи на курс, заполните следующую информацию."
    )
    bot.send_message(chat_id, msg_to_user)
    sleep(1)
    ask_name(chat_id)


@bot.message_handler(commands=["links"])
def links_window(message):
    chat_id = message.chat.id
    logging.info("/links command")

    msg_to_user = (
        "Вам может быть инетресно:\n"
        "1. <a href='http://www.google.com/'>Google search</a>\n"
        "2. <a href='https://www.yandex.ru/'>Яндекс Поиск</a>\n"
        "3. <a href='https://www.apple.com/ru/iphone/'>iPhone</a>\n"
    )
    bot.send_message(chat_id, msg_to_user, parse_mode="HTML")


def get_dog_url():
    contents = requests.get('https://random.dog/woof.json').json()
    url = contents['url']
    return url


@bot.message_handler(commands=["images"])
def images_window(message):
    chat_id = message.chat.id
    logging.info("/images command")

    url = get_dog_url()
    bot.send_photo(chat_id=chat_id, photo=url)


# ................................Name.........................................
def ask_name(chat_id):
    msg_to_user = "Введите Ваши ФИО:"

    msg = bot.send_message(chat_id, msg_to_user)
    bot.register_next_step_handler(msg, name_response)


def name_response(message):
    chat_id = message.chat.id
    name = message.text
    global edit_record_flag
    logging.info("user name for application")

    if not edit_record_flag:
        info[str(chat_id)].append(name)
        ask_birth_date(chat_id)
    else:
        info[str(chat_id)][0] = name
        edit_record_flag = False
        ask_summary(chat_id)


# ................................Date of birth................................
def ask_birth_date(chat_id):
    msg_to_user = "Выберите Вашу дату рождения:"

    bot.send_message(chat_id, msg_to_user)
    calendar, step = MyStyleCalendar(max_date=dt.datetime.now().date()).build()
    bot.send_message(chat_id, f"Выберите {LSTEP[step]}", reply_markup=calendar)


@bot.callback_query_handler(func=MyStyleCalendar.func())
def birth_date_response(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    global edit_record_flag

    result, key, step = MyStyleCalendar().process(call.data)
    if not result and key:
        bot.edit_message_text(
            f"Выберите {LSTEP[step]}",
            chat_id,
            msg_id,
            reply_markup=key
        )
    elif result:
        bot.edit_message_text(
            f"Вы выбрали <b>{result}</b>",
            chat_id,
            msg_id,
            parse_mode="HTML"
        )
        logging.info("user date of birth for application")

        if not edit_record_flag:
            info[str(chat_id)].append(result.strftime("%Y-%m-%d"))
            ask_gender(chat_id)
        else:
            info[str(chat_id)][1] = result.strftime("%Y-%m-%d")
            edit_record_flag = False
            ask_summary(chat_id)


# ............................. Ask Gender.....................................
def ask_gender(chat_id):
    msg_to_user = "Выберите Ваш пол:"

    markup = types.InlineKeyboardMarkup()
    btn = create_inline_keyboard_button("Мужской", "Мужской")
    markup.add(btn)
    btn = create_inline_keyboard_button("Женский", "Женский")
    markup.add(btn)

    bot.send_message(chat_id, text=msg_to_user, reply_markup=markup)


@bot.callback_query_handler(
    func=lambda call: call.data in ["Мужской", "Женский"]
)
def gender_response(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    global edit_record_flag
    logging.info("user gender for application")

    # bot.send_message(call.message.chat.id, call.data)
    bot.edit_message_reply_markup(chat_id, msg_id)
    bot.send_message(
        chat_id,
        f"Вы выбрали: <b>{call.data}</b>",
        parse_mode="HTML"
    )

    if not edit_record_flag:
        info[str(chat_id)].append(call.data)
        ask_phone(chat_id)
    else:
        info[str(chat_id)][2] = call.data
        edit_record_flag = False
        ask_summary(chat_id)


# ..................................Phone...................................
def ask_phone(chat_id):
    msg_to_user = "Введите номер телефона:"

    msg = bot.send_message(chat_id, msg_to_user)
    bot.register_next_step_handler(msg, phone_response)


def phone_response(message):
    chat_id = message.chat.id
    phone_number = message.text
    global edit_record_flag
    logging.info("user phone for application")

    if not edit_record_flag:
        info[str(chat_id)].append(phone_number)
        ask_summary(chat_id)
    else:
        info[str(chat_id)][3] = phone_number
        edit_record_flag = False
        ask_summary(chat_id)


# ....................................Summary..................................
def ask_summary(chat_id):
    msg_to_user = get_summary(chat_id)

    markup = types.InlineKeyboardMarkup()
    btn = create_inline_keyboard_button("Все верно", "Correct")
    markup.add(btn)
    btn = create_inline_keyboard_button("Изменить", "Edit")
    markup.add(btn)

    bot.send_message(chat_id, text=msg_to_user, reply_markup=markup)


def get_summary(chat_id):
    text = "Проверьте правильность заполнения.\n"

    for i, (param, value) in enumerate(zip(PARAMS, info[str(chat_id)]), 1):
        text += f"{i}. {param}: {value}\n"

    return text


@bot.callback_query_handler(
    func=lambda call: call.data in ["Correct", "Edit"]
)
def summary_response(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    logging.info("user summary for application")

    if call.data == "Correct":
        msg_to_user = "<b>Заявка успешно заполнена!</b>"
        bot.send_message(chat_id, msg_to_user, parse_mode="HTML")
        save_record(chat_id)
        info.pop(str(chat_id))
    else:  # Edit
        msg_to_user = "В каком поле ошибка? (1, 2, 3, 4)"
        msg = bot.send_message(chat_id, msg_to_user)
        bot.register_next_step_handler(msg, edit_record)

    bot.edit_message_reply_markup(chat_id, msg_id)


# ..................................Edit Record................................
def edit_record(message):
    """
    Change the certain field (1, 2, 3, 4) of the application form
    if user has made a mistake.
    """
    chat_id = message.chat.id
    num_record = message.text
    global edit_record_flag

    if not num_record.isnumeric():
        logging.info("The field must be a number.")

        msg_to_user = "Поле должно быть числом (1, 2, 3, 4)"
        msg = bot.send_message(chat_id, msg_to_user)
        bot.register_next_step_handler(msg, edit_record)

    elif int(num_record) not in [1, 2, 3, 4]:
        logging.info("The field must take the next values (1, 2, 3, 4).")

        msg_to_user = "Поле должно быть числом (1, 2, 3, 4)"
        msg = bot.send_message(chat_id, msg_to_user)
        bot.register_next_step_handler(msg, edit_record)
    else:
        edit_record_flag = True

        if num_record == "1":
            ask_name(chat_id)
        elif num_record == "2":
            ask_birth_date(chat_id)
        elif num_record == "3":
            ask_gender(chat_id)
        else:
            ask_phone(chat_id)


# ...................................Echo......................................
@bot.message_handler(content_types=['text'])
def echo_text(message):
    chat_id = message.chat.id
    global edit_record_flag

    if edit_record_flag:
        msg_to_user = "<b>Вы не ответили на текущий вопрос!</b>"
    else:
        msg_to_user = get_start_message()

    bot.send_message(chat_id, msg_to_user, parse_mode="HTML")


def create_output_file(dir_name="data", file_name="results", mode="a+"):
    """
    Create output file with filled applications.

    Parameters:
    -----------
    dir_name : str
        Name of the directory to be created.
    file_name : str
        Name of the file to be created in the directory.
    mode : str
        Write mode.

    Returns:
    --------
    fd : file object
        A file object which is supposed to be used for read and write data.
    """
    path = os.getcwd()
    dir_path = path + '/' + dir_name
    file_path = dir_path + '/' + file_name + ".txt"

    fd = None

    try:
        os.mkdir(dir_path)
    except FileExistsError:
        logging.warning(f"Directory {dir_path} has already existed")
    except OSError:
        logging.error(f"Creation of the directory {dir_path} failed")
        Exception(f"Creation of the directory {dir_path} failed")
    else:
        logging.info(f"Successfully created the directory {dir_path}")

    try:
        fd = open(file_path, mode)
    except IOError:
        logging.error(f"There is no file named {file_path}")
    else:
        logging.info(f"Successfully created the file {file_path}")

    return fd


def check_write_mode(write_mode):
    """
    Check whether the write mode correct or not.

    Parameter:
    ----------
    write_mode : str
        Write mode.

    Returns:
    --------
    bool
        True if the write mode is correct, False otherwise.
    """
    if write_mode not in ["w+", "a+"]:
        return False
    else:
        return True


def save_record(chat_id):
    if not check_write_mode(config["write_mode"]):
        err_msg = "Only [w+, a+] write mode can be used."
        logging.error(err_msg)
        Exception(err_msg)

    fd = create_output_file(
        config["dir_name"],
        config["file_name"],
        config["write_mode"]
    )

    file_path = config["dir_name"] + '/' + config["file_name"] + ".txt"
    if os.stat(file_path).st_size == 0:
        fd.write(','.join(COLUMNS) + '\n')

    # Fill the output file with data
    if len(info[str(chat_id)]) == len(PARAMS):
        fd.write(str(chat_id) + ',' + ','.join(info[str(chat_id)]) + '\n')

    fd.close()


if __name__ == "__main__":
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        filename='bot.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        datefmt='%d-%m-%y %H:%M:%S'
    )

    # run telebot.
    bot.polling()
