import telebot
from telebot import types

TOKEN = "6607362953:AAHq51eNlOotBWVC5DCmE0lenRt24w6e1jc"
bot = telebot.TeleBot(TOKEN)

allowed_users = [739212312, 6725692476]

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in allowed_users:
        bot.send_message(message.chat.id, '''Привіт, я бот який допоможе тобі та твоїм друзям бути гідними сусідами, а не щурами. Якщо ти гідний сусід, то я тобі допоможу:)''')
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

bot.polling()



