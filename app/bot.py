import random
import time

import telebot
from telebot import types

from app.config import config, logger
from app.db.db import Database

bot = telebot.TeleBot(config.bot_token)

db = Database(logger)

saved_payer_id = []
class Joker:
    def __init__(self):
        self.list = ['Щоб Данек тобі в думу насрав',
                     'Щоб твої квіти зав’яли',
                     'Пішов ти нахуй',
                     'Піська не встайот, бо я не лягаю спати',
                     'Мамку єбав)',
                     'Папку єбав)',
                     'Надрочив тобі на обличчя поки ти спав, солоденький',
                     'Нахуй нє?',
                     'Кажеца Кот знов обригався',
                     'Щоб твоє життя пішло в таку ж сраку, як музика Грішані',
                     'Пукнув на тебе киця',
                     'Обсірав тобі ліжко, люблю',
                     'Цукерочка ти моя обдристана)']

    def random(self):
        return random.choice(self.list)


joker = Joker()

# @bot.message_handler(commands=['start', 'register'])
# def send_welcome(message):
#     logger.info(f"Registering user {message.from_user.id} with username {message.from_user.username}")
#     db.register_user(message.from_user.id, message.from_user.username)
#     msg =
#     markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
#     markup.add('Вступити в групу', 'Створити групу')
#     bot.send_message(message.chat.id,
#                      "Привіт, я бот який допоможе тобі та твоїм друзям бути гідними сусідами, а не щурами. Якщо ти гідний сусід, то я тобі допоможу:)")
#     bot.send_message(message.chat.id, "Щоб почати, вступи в групу твоїх сусідів або створи її:", reply_markup=markup)

@bot.message_handler(commands=['start', 'register'])
def send_welcome(message):
    logger.info(f"Registering user {message.from_user.id} with username {message.from_user.username}")
    bot.send_message(message.chat.id,
                     "Привіт, я бот який допоможе тобі та твоїм друзям бути гідними сусідами, а не щурами. Якщо ти гідний сусід, то я тобі допоможу:)")
    msg = bot.send_message(message.chat.id, "Напиши мені номер своєї основної картки, щоб в майбутньому я міг повертати твої гроші:")
    bot.register_next_step_handler(msg, process_card_number_step, message.from_user.id, message.from_user.username)

def process_card_number_step(message, telegram_id, username):
    card_number = message.text
    # Perform any necessary validation on card_number here
    db.register_user(telegram_id, username, card_number)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Вступити в групу', 'Створити групу')
    bot.send_message(message.chat.id, "Щоб почати, вступи в групу твоїх сусідів або створи її:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'Вступити в групу')
def request_group_code(message):
    logger.info("Joining group")
    bot.reply_to(message, 'Напишіть код для вступу в групу.')
    bot.register_next_step_handler(message, join_group)


def join_group(message):
    logger.info(f"Joining group with code {message.text}")
    join_code = message.text
    telegram_id = message.from_user.id
    username = message.from_user.username
    joined = db.join_group(telegram_id, username, join_code)

    if joined:
        bot.reply_to(message, 'Вітаємо! Ви успішно вступили в групу!')
        send_main_menu(message)
    else:
        bot.reply_to(message, 'Помилка при вступі в групу. Перевірте код та спробуйте ще раз.')


@bot.message_handler(func=lambda message: message.text == 'Створити групу')
def create_group(message):
    logger.info("Creating group")
    result = db.create_group(message.from_user.id, message.from_user.username)
    if result is None:
        bot.reply_to(message, "Упс, халепа... Айтішники дураки, спробуй пізніше(")
    else:
        join_code, group_id = result
        bot.reply_to(message, f"Групу створено\! Тицяй на код, та відправляй своему хоумі: `{join_code}`",
                     parse_mode='MarkdownV2')
        # Assuming update_user_group is correctly implemented for the new schema
        db.update_user_group(message.from_user.id, group_id)
        send_main_menu(message)


def send_main_menu(message):
    time.sleep(1.5)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    # Add menu options
    markup.add('Поділити чек', 'Профіль', 'Прікол')
    bot.send_message(message.chat.id, "Ну і що будемо робити?:", reply_markup=markup)


@bot.message_handler(commands=['menu'])
def handle_start(message):
    send_main_menu(message)


@bot.message_handler(func=lambda message: message.text == "Поділити чек")
def handle_split_check(message):
    global saved_payer_id
    payer_id = db.get_user_id(message.from_user.id)
    logger.info(f"Got payer id: {payer_id}")
    saved_payer_id.append(payer_id)
    logger.info(f"Saved payer id: {saved_payer_id}")
    ask_photo(message)





@bot.message_handler(content_types=['photo'])
def handle_split_check_photo(message):
    global file_id
    file_id = message.photo[-1].file_id
    select_users(message)


@bot.message_handler(func=lambda message: message.text == "Прікол")
def handle_split_check_2(message):
    susids = db.get_users_in_group(message.from_user.id)
    for telegram_id, user_id in susids:
        bot.send_message(telegram_id, joker.random())
    send_main_menu(message)


@bot.message_handler(func=lambda message: message.text == "Профіль")
def handle_split_check_3(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Щурячі борги', 'Мої борги', 'Моя картка', 'Повернутись')
    bot.send_message(message.chat.id, "Що хочеш подивитись?", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Щурячі борги")
def shuryachi_borgi(message):
    telegram_id = message.from_user.id
    payer_id = db.get_user_id(telegram_id)
    debts = db.get_debts(payer_id)
    # username = db.get_username({debt[2] for debt in debts})
    if not debts:
        bot.send_message(telegram_id, "Наразі ви не маєте боржників")
    else:
        for debt in debts:
            user_id = debt[1]
            username = db.get_username_t(user_id)
            logger.info(f"Username: {username}")
            if username is None:
                username = "Unknown User"
            message_text = f"Борг №{debt[0]}:\n"
            message_text += f"Вам все ще винен @{username}: {debt[2]} грн\n"
            message_text += f"Дата: {debt[3].date()}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Сплачено', callback_data=f'paid_{debt[0]}_{username}'),
                       types.InlineKeyboardButton('Все ще винен', callback_data=f'still_owes_{debt[0]}_{username}'))
            bot.send_message(telegram_id, message_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('paid_'))
def handle_paid(call):
    debt_id = call.data.split('_')[1]
    username = call.data.split('_')[2]
    db.clear_debts(debt_id)
    bot.answer_callback_query(call.id, f"Борг №{debt_id} від {username} відмічено як сплачений")

@bot.callback_query_handler(func=lambda call: call.data.startswith('still_owes_'))
def handle_still_owes(call):
    debt_id = call.data.split('_')[1]
    username = call.data.split('_')[2]
    bot.answer_callback_query(call.id, f"Борг №{debt_id} від {username} все ще актуальний")


@bot.message_handler(func=lambda message: message.text == "Мої борги")
def my_debts(message):
    telegram_id = message.from_user.id
    user_id = db.get_user_id(telegram_id)
    debts = db.get_my_debts(user_id)
    if not debts:
        bot.send_message(telegram_id, "Наразі ви не маєте боргів")
    else:
        for debt in debts:
            user_id = debt[3]
            username = db.get_username_t(user_id)
            if username is None:
                username = "Unknown User"
            card_number = db.get_card_number(user_id)
            if card_number is None:
                card_number = "Unknown Card"
            message_text = f"Борг №{debt[0]}:\n"
            message_text += f"Ви винні: {debt[1]} грн, вашому сусіду @{username}\n"
            message_text += f"Дата: {debt[2].date()}"
            bot.send_message(telegram_id, message_text)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('Сплатив', callback_data=f'pay_{debt[0]}_{username}_{debt[3]}_{debt[1]}_{debt[2].date()}'),
                       types.InlineKeyboardButton('Сплачу пізніше', callback_data=f'paylater_{debt[0]}_{username}'))
            bot.send_message(telegram_id, f"Сплати на цю картку, будь ласка: `{card_number}`\n", parse_mode='MarkdownV2', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_pay(call):
    debt_id = call.data.split('_')[1]
    username = call.data.split('_')[2]
    payer_id = call.data.split('_')[3]
    amount = call.data.split('_')[4]
    datee = call.data.split('_')[5]
    telegram_id = db.get_telegram_id(payer_id)
    my_user_id = db.get_id(debt_id)
    my_user_name = db.get_username_t(my_user_id)
    message_text = f"Привіт, @{username}!\n"
    message_text += f"Користувач @{my_user_name} сплатив борг №{debt_id}\n"
    message_text += f"Сума боргу: {amount} грн, станом на {datee}\n"
    message_text += "Перевір будь ласка свою картку, та підтверди оплату в своєму профілі"
    bot.send_message(telegram_id, message_text)

@bot.callback_query_handler(func=lambda call: call.data.startswith('paylater_'))
def handle_pay_later(call):
    debt_id = call.data.split('_')[1]
    username = call.data.split('_')[2]
    bot.answer_callback_query(call.id, f"Не затягуй з оплатою боргу №{debt_id} твому сусіду {username}!")


@bot.message_handler(func=lambda message: message.text == "Моя картка")
def my_card(message):
    telegram_id = message.from_user.id
    user_id = db.get_user_id(telegram_id)
    card_number = db.get_card_number(user_id)
    if card_number is None:
        card_number = "Unknown Card"
    bot.send_message(telegram_id, f"Твоя картка: {card_number}")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Змінити картку', 'Повернутись')
    bot.send_message(message.chat.id, "Хочеш змінити?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Змінити картку")
def change_card(message):
    telegram_id = message.from_user.id
    msg = bot.send_message(telegram_id, "Введи новий номер своєї картки:")
    bot.register_next_step_handler(msg, process_card_number_step_2, telegram_id)

def process_card_number_step_2(message, telegram_id):
    card_number = message.text
    db.update_card_number(telegram_id, card_number)
    bot.send_message(telegram_id, f"Твоя нова картка: {card_number}")
    send_main_menu(message)

@bot.message_handler(func=lambda message: message.text == "Повернутись")
def return_to_main_menu(message):
    send_main_menu(message)


def select_users(message):
    logger.info("Selecting users")
    telegram_id = message.from_user.id
    users = db.get_users_in_group(telegram_id)
    markup = types.InlineKeyboardMarkup()
    for user_id, username in users:
        markup.add(types.InlineKeyboardButton(username, callback_data=f'user_{user_id}_{username}'))
    markup.add(types.InlineKeyboardButton("Щури вибрані", callback_data='done'))
    bot.send_message(message.chat.id, "З ким будемо ділити:", reply_markup=markup)

def ask_photo(message):
    bot.send_message(message.chat.id, "Відправ мені фото чеку будь-ласка:))")


# Global structure to track user selections for simplicity; consider a more robust approach for production
user_selections = []
file_id = None


@bot.callback_query_handler(func=lambda call: call.data.startswith('user_'))
def handle_user_selection(call):
    selected_user_id = call.data.split('_')[1]
    selected_user_name = call.data.split('_')[2]
    if selected_user_id not in user_selections:
        user_selections.append(selected_user_id)
        bot.answer_callback_query(call.id, f"User {selected_user_name} selected.")
    else:
        user_selections.remove(selected_user_id)
        bot.answer_callback_query(call.id, f"User {selected_user_name} un-selected.")
    print(user_selections)
@bot.callback_query_handler(func=lambda call: call.data == 'done')
def handle_calculation(call):
    personal_spendings = {}
    user_ids = list(user_selections)  # Make a copy of the user_selections list

    def process_next_user(message=None):
        logger.info(f"Processing next user")
        if message is not None:
            # This is not the first user, so we process the previous user's spending
            previous_user_id = user_ids[0]
            personal_spendings[previous_user_id] = float(message.text)
            user_ids.pop(0)  # Remove the previous user from the list

        if user_ids:  # If there are still users left
            next_user_id = user_ids[0]
            next_username = db.get_username(next_user_id)
            if next_username:
                msg = bot.send_message(call.message.chat.id, f"Введи персональну витрату цього гівнюка {next_username}")
                bot.register_next_step_handler(msg, process_next_user)
            else:
                bot.send_message(call.message.chat.id, "Гівнюк не знайдений(")

        else:
            # All users have been processed, so we ask for the total spending amount
            sum_spending_msg = bot.send_message(call.message.chat.id, "Ну і скільки ти витратив загалом на цих дурнів?")
            bot.register_next_step_handler(sum_spending_msg, process_total_spending,
                                           personal_spendings)  # Pass personal_spendings here
    # Start the process with the first user
    process_next_user()

def process_total_spending(message, personal_spendings):
    sum_spending = float(message.text)
    personal_sum = sum_spending / len(personal_spendings)

    for user_id, spending in personal_spendings.items():
        spending += personal_sum
        if db.get_user_id(message.from_user.id) == saved_payer_id[0]:
            continue

        if file_id:
            bot.send_photo(user_id, file_id, caption=f"Не знаю нащо ти вписався в цю схемку, але тепер ти винний  {spending}")
        else:
            bot.send_message(user_id, f"Не знаю нащо ти вписався в цю схемку, але тепер ти винний: {spending}")
        insert_spending(user_id, spending)
    saved_payer_id.clear()
    send_main_menu(message)

def insert_spending(user_id, spending):
    logger.info(f"Inserting spending for user {user_id}")
    payer_id = saved_payer_id[0]
    telegram_id = user_id
    group_id = db.get_group_id(telegram_id)
    user_idd = db.get_user_id(telegram_id)
    amount = spending
    description = "Борг за чек"
    if payer_id == user_idd:
        return
    db.upsert_spending(user_idd, group_id, amount, description, payer_id)




