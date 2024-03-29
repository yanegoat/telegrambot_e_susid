import telebot
from telebot import types

from app.config import config, logger
from app.db.db import Database

bot = telebot.TeleBot(config.bot_token)

db = Database(logger)


@bot.message_handler(commands=['start', 'register'])
def send_welcome(message):
    logger.info(f"Registering user {message.from_user.id} with username {message.from_user.username}")
    db.register_user(message.from_user.id, message.from_user.username)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Join a Group', 'Create a Group')
    bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Join a Group')
def join_group(message):
    logger.info("Joining group")
    groups = db.get_groups()
    if groups:
        markup = types.InlineKeyboardMarkup()
        for group_id, group_name in groups:
            markup.add(types.InlineKeyboardButton(group_name, callback_data=f'join_{group_id}'))
        bot.send_message(message.chat.id, "Select a group:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "No groups available. Consider creating one!")


@bot.message_handler(func=lambda message: message.text == 'Create a Group')
def request_group_name(message):
    logger.info("Requesting group name")
    sent = bot.send_message(message.chat.id, "Enter the name for your new group:")
    bot.register_next_step_handler(sent, create_group)


# Callback query handler for joining groups
@bot.callback_query_handler(func=lambda call: call.data.startswith('join_'))
def handle_join_group(call):
    logger.info(f"Joining group {call.data}")
    group_id = int(call.data.split('_')[1])
    db.update_user_group(call.from_user.id, group_id)
    bot.answer_callback_query(call.id, "Joined group successfully!")


@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in allowed_users:
        bot.send_message(message.chat.id,
                         '''Привіт, я бот який допоможе тобі та твоїм друзям бути гідними сусідами, а не щурами. Якщо ти гідний сусід, то я тобі допоможу:)''')
    else:
        bot.send_message(message.chat.id, "Вибач, але ти не маєш доступу до цього бота...")


@bot.message_handler(commands=['start'])
def handle_start(message):
    send_split_the_check_button(message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Поділити чек")
def handle_split_check(message):
    request_photo(message.chat.id)


@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    # Store the photo file ID and prompt for the sum
    user_data[chat_id] = {'photo': message.photo[-1].file_id}
    bot.send_message(chat_id, "Тепер введи суму чеку:)")


@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    # Check if we are expecting a sum from this user
    if chat_id in user_data and 'photo' in user_data[chat_id]:
        user_data[chat_id]['sum'] = message.text
        for user_id in RECIPIENT_USER_IDS:
            bot.send_photo(user_id, user_data[chat_id]['photo'], caption=f"Sum: {user_data[chat_id]['sum']}")
        del user_data[chat_id]  # Clear the stored data for this user
        send_split_the_check_button(chat_id)  # Show the button again for further actions
    else:
        # If the message is not recognized as part of the flow, show the button again
        send_split_the_check_button(chat_id)


def create_group(message):
    logger.info(f"Creating group {message.text}")
    group_name = message.text
    group_id = db.add_group(group_name, message.from_user.id)
    # Here you can also update the user's group_id in the users table if needed
    bot.send_message(message.chat.id, f"Group '{group_name}' created successfully!")
    db.update_user_group(message.from_user.id, group_id)


def send_split_the_check_button(chat_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton("Поділити чек"))
    bot.send_message(chat_id, "Ну і що будемо робити?", reply_markup=markup)


def request_photo(chat_id):
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(chat_id, "Відправ мені фото чеку будь-ласка:))", reply_markup=markup)
