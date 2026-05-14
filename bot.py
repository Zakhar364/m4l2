from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import *
import schedule
import threading
import time
from config import *

bot = TeleBot(API_TOKEN)

def gen_markup(id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=id))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    prize_id = call.data
    user_id = call.message.chat.id

    # Проверяем количество уже полученных призов
    winners_count = manager.count_prize_winners(prize_id)
    
    if winners_count >= 3:
        bot.send_message(user_id, "❌ Мне жаль, но уже 3 пользователя получили этот приз!")
        return
    
    # Добавляем пользователя как победителя
    if manager.add_winner(user_id, prize_id):
        # Отправляем расшифрованное изображение
        img = manager.get_prize_img(prize_id)
        with open(f'img/{img}', 'rb') as photo:
            bot.send_photo(user_id, photo, caption="🎉 Поздравляем! Ты получил приз!")
    else:
        bot.send_message(user_id, "⚠️ Ты уже получал этот приз!")


def send_message():
    prize_id, img = manager.get_random_prize()[:2]
    manager.mark_prize_used(prize_id)
    hide_img(img)
    for user in manager.get_users():
        with open(f'hidden_img/{img}', 'rb') as photo:
            bot.send_photo(user, photo, reply_markup=gen_markup(id = prize_id))
        

def shedule_thread():
    schedule.every().minute.do(send_message) # Здесь ты можешь задать периодичность отправки картинок
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегестрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждый час тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'

Только три первых пользователя получат картинку!)""")


@bot.message_handler(commands=['rating'])
def handle_rating(message):
    winners = manager.get_winners()
    
    if not winners:
        bot.send_message(message.chat.id, "📊 Таблица рейтинга пуста. Победителей пока нет!")
        return
    
    # Формируем таблицу
    rating_text = "📊 <b>Таблица рейтинга</b>\n\n"
    rating_text += "<code>" + f"{'№':<3} {'Пользователь':<20} {'Приз ID':<10} {'Время':<19}\n" + "-" * 52 + "</code>\n"
    
    for idx, (username, prize_id, win_time) in enumerate(winners, 1):
        username = username or "Unknown"
        rating_text += f"<code>{idx:<3} {username:<20} {prize_id:<10} {win_time:<19}</code>\n"
    
    bot.send_message(message.chat.id, rating_text, parse_mode="HTML")
        


def polling_thread():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    polling_thread = threading.Thread(target=polling_thread)
    polling_shedule  = threading.Thread(target=shedule_thread)

    polling_thread.start()
    polling_shedule.start()
  
