import telebot
from telebot import types
import re
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PORT = "5432"
USER = "postgres"
PASSWORD = "admin"
DATABASE = "tele_bot_e_susid"
HOST = "localhost"

# create connection string
conn = psycopg2.connect(host=HOST, port=PORT, user=USER,
                        database=DATABASE, password=PASSWORD)
print("Connection established")


def init_table():
    cursor = conn.cursor()
    create_tables_commands = [
        """
        CREATE TABLE IF NOT EXISTS groups (
            group_id SERIAL PRIMARY KEY,
            group_name VARCHAR(255) UNIQUE NOT NULL,
            telegram_id BIGINT UNIQUE NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(255),
            group_id INTEGER,
            FOREIGN KEY (group_id) REFERENCES groups (group_id)
);
        """,
        """
        CREATE TABLE IF NOT EXISTS costs (
            cost_id SERIAL PRIMARY KEY,
            amount DECIMAL NOT NULL,
            description TEXT,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        """
    ]
    # Execute each table creation command
    for command in create_tables_commands:
        cursor.execute(command)
    print("Table created successfully")
    conn.commit()
    cursor.close()


TOKEN = "6607362953:AAHq51eNlOotBWVC5DCmE0lenRt24w6e1jc"
bot = telebot.TeleBot(TOKEN)

def update_user_group(telegram_id, group_id):
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET group_id = %s WHERE telegram_id = %s;', (group_id, telegram_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating user group: {e}")
        conn.rollback()
def register_user(telegram_id, username):
    logger.info(f"Registering user {telegram_id} with username {username}")
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO users (telegram_id, username) VALUES (%s, %s) ON CONFLICT (telegram_id) DO NOTHING;''',
            (telegram_id, username))
        conn.commit()
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        conn.rollback()


def get_groups():
    logger.info("Fetching groups")
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT group_id, group_name FROM groups;')
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching groups: {e}")
        return None


def add_group(group_name, telegram_id):
    logger.info(f"Adding group {group_name} with telegram_id {telegram_id}")
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO groups (group_name, telegram_id) VALUES (%s, %s) RETURNING group_id;',
                       (group_name, telegram_id))
        group_id = cursor.fetchone()[0]
        update_user_group(telegram_id, group_id)
        conn.commit()
        return group_id
    except Exception as e:
        logger.error(f"Error adding group: {e}")
        conn.rollback()
        return None


@bot.message_handler(commands=['start', 'register'])
def send_welcome(message):
    logger.info(f"Registering user {message.from_user.id} with username {message.from_user.username}")
    register_user(message.from_user.id, message.from_user.username)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Join a Group', 'Create a Group')
    bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == 'Join a Group')
def join_group(message):
    logger.info("Joining group")
    groups = get_groups()
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


def create_group(message):
    logger.info(f"Creating group {message.text}")
    group_name = message.text
    group_id = add_group(group_name, message.from_user.id)
    # Here you can also update the user's group_id in the users table if needed
    bot.send_message(message.chat.id, f"Group '{group_name}' created successfully!")
    update_user_group(message.from_user.id, group_id)


# Callback query handler for joining groups
@bot.callback_query_handler(func=lambda call: call.data.startswith('join_'))
def handle_join_group(call):
    logger.info(f"Joining group {call.data}")
    cursor = conn.cursor()
    group_id = int(call.data.split('_')[1])
    # Update the user's group_id in the users table here
    cursor.execute('UPDATE users SET group_id = %s WHERE telegram_id = %s;', (group_id, call.from_user.id))
    conn.commit()
    bot.answer_callback_query(call.id, "Joined group successfully!")


@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in allowed_users:
        bot.send_message(message.chat.id,
                         '''Привіт, я бот який допоможе тобі та твоїм друзям бути гідними сусідами, а не щурами. Якщо ти гідний сусід, то я тобі допоможу:)''')
    else:
        bot.send_message(message.chat.id, "Вибач, але ти не маєш доступу до цього бота...")


RECIPIENT_USER_IDS = [739212312, 6725692476]  # Replace with actual user IDs

# A dictionary to keep track of the user state and data
user_data = {}

chat_id = RECIPIENT_USER_IDS[0]


@bot.message_handler(commands=['start'])
def handle_start(message):
    send_split_the_check_button(message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Поділити чек")
def handle_split_check(message):
    request_photo(message.chat.id)


def send_split_the_check_button(chat_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add(types.KeyboardButton("Поділити чек"))
    bot.send_message(chat_id, "Ну і що будемо робити?", reply_markup=markup)


def request_photo(chat_id):
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(chat_id, "Відправ мені фото чеку будь-ласка:))", reply_markup=markup)


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


# bot.polling()

if __name__ == "__main__":
    logger.info("Starting bot...")
    init_table()
    bot.polling()
